from fastapi import WebSocket, WebSocketDisconnect
import logging
from .redis_client import RedisClient
from .minio_client import MinioClient
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}
        self.redis = RedisClient()
        self.minio = MinioClient()

    async def connect(self, room_id: str, websocket: WebSocket, room_name: str, room_language: str):
        """Подключение к комнате"""
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)

        participant_id = f"user_{id(websocket)}"
        await self.redis.add_participant(room_id, participant_id)

        logger.info(f"Подключился к комнате {room_id}. Всего: {len(self.active_connections[room_id])}")

    async def disconnect(self, room_id: str, websocket: WebSocket):
        """Отключение от комнаты"""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)

            participant_id = f"user_{id(websocket)}"
            await self.redis.remove_participant(room_id, participant_id)

            if not self.active_connections[room_id]:
                code = await self.redis.get_code(room_id)
                if code:
                    await self.minio.save_code(room_id, code)
                await self.redis.delete_code(room_id)
                
                del self.active_connections[room_id]
                logger.info(f"Комната {room_id} пуста, код архивирован")
            else:
                logger.info(f"Отключился из комнаты {room_id}. Осталось: {len(self.active_connections[room_id])}")

    async def broadcast(self, room_id: str, message: str, sender: WebSocket):
        """Отправить всем в комнате кроме отправителя"""
        if room_id not in self.active_connections:
            return

        await self.redis.set_code(room_id, message)

        for connection in self.active_connections[room_id]:
            if connection != sender:
                try:
                    await connection.send_text(message)
                except:
                    pass

    