import docker
import tempfile
import os
import asyncio
import re
from docker.errors import APIError


class CodeExecutor:
    def __init__(self):
        self.client = docker.from_env()
        self.image = "nsjail:latest"

    async def execute_code(self, code: str) -> dict:
        return await asyncio.to_thread(self._execute_sync, code)

    def _filter_nsjail_logs(self, logs: str) -> str:
        """Убирает логи nsjail, оставляет только вывод кода"""
        if not logs:
            return ""

        lines = logs.split('\n')
        output = []

        for line in lines:
            if line and not re.match(r'^\[\w\]\[\d{4}-\d{2}-\d{2}', line):
                output.append(line)

        return '\n'.join(output).strip()

    def _execute_sync(self, code: str) -> dict:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            f.flush()
            host_path = f.name

        try:
            container = self.client.containers.run(
                image=self.image,
                command=["--", "/usr/local/bin/python", "/snekbox/script.py"],
                detach=True,
                mem_limit="256m",
                network_disabled=True,
                volumes={host_path: {'bind': '/snekbox/script.py', 'mode': 'ro'}},
                remove=False
            )

            try:
                container.wait(timeout=6)
            except APIError as e:
                container.kill()
                return {'error': 'Execution timeout (6s)'}

            logs = container.logs(stdout=True, stderr=True)
            container.remove()

            if isinstance(logs, bytes):
                logs = logs.decode('utf-8', errors='ignore')

            clean_output = self._filter_nsjail_logs(logs)

            return {
                'output': clean_output if clean_output else 'No output',
                'success': True
            }

        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
        finally:
            try:
                os.unlink(host_path)
            except:
                pass
