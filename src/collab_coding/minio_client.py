import io
import asyncio
import logging
from minio import Minio
from minio.versioningconfig import VersioningConfig
from .settings import settings

logger = logging.getLogger(__name__)


class MinioClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket_and_versioning()

    def _ensure_bucket_and_versioning(self):
        """Создает bucket и включает версионирование"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Бакет '{self.bucket}' создан")
            
            config = self.client.get_bucket_versioning(self.bucket)
            if config.status != "Enabled":
                self.client.set_bucket_versioning(
                    self.bucket, 
                    VersioningConfig("Enabled")
                )
                logger.info(f"Версионирование включено для бакета '{self.bucket}'")
        except Exception as e:
            logger.error(f"Ошибка инициализации MinIO: {e}")
            raise

    async def save_code(self, room_id: str, code: str) -> str | None:
        """Сохраняет код в MinIO. Возвращает version_id"""
        path = f"rooms/{room_id}/code.py"
        data = code.encode("utf-8")
        
        try:
            result = await asyncio.to_thread(
                self.client.put_object,
                self.bucket,
                path,
                io.BytesIO(data),
                len(data),
                content_type="text/plain"
            )
            logger.debug(f"Код сохранен в MinIO: комната={room_id}, версия={result.version_id}")
            return result.version_id
        except Exception as e:
            logger.error(f"Ошибка сохранения кода в MinIO: комната={room_id}, ошибка={e}")
            return None

    async def get_code(self, room_id: str, version_id: str = None) -> tuple[str | None, str | None]:
        """Получает код из MinIO. Возвращает (код, version_id)"""
        path = f"rooms/{room_id}/code.py"
        
        try:
            response = await asyncio.to_thread(
                self.client.get_object,
                self.bucket,
                path,
                version_id=version_id
            )
            data = await asyncio.to_thread(response.read)
            version = response.getheader("x-amz-version-id")
            response.close()
            response.release_conn()
            
            logger.debug(f"Код загружен из MinIO: комната={room_id}, версия={version}")
            return data.decode("utf-8"), version
        except Exception as e:
            logger.warning(f"Код не найден в MinIO: комната={room_id}, ошибка={e}")
            return None, None

    async def get_code_versions(self, room_id: str) -> list[dict]:
        """Получает список всех версий кода комнаты"""
        path = f"rooms/{room_id}/code.py"
        versions = []
        
        try:
            objects = await asyncio.to_thread(
                self.client.list_objects,
                self.bucket,
                prefix=path,
                include_version=True
            )
            for obj in objects:
                versions.append({
                    "version_id": obj.version_id,
                    "last_modified": obj.last_modified.isoformat(),
                    "size": obj.size,
                    "is_latest": obj.is_latest
                })
            logger.debug(f"Найдено {len(versions)} версий для комнаты {room_id}")
            return versions
        except Exception as e:
            logger.error(f"Ошибка получения версий кода: комната={room_id}, ошибка={e}")
            return []