import redis.asyncio as redis
from .settings import settings


class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )

    async def set_room_metadata(self, room_id: str, name: str, language: str, created_at: str, updated_at: str):
        """Сохраняет метаданные комнаты в Redis"""
        await self.client.hset(
            f"room:{room_id}:info",
            mapping={
                "room_id": room_id,
                "name": name,
                "language": language,
                "created_at": created_at,
                "updated_at": updated_at
            }
        )
        await self.client.expire(f"room:{room_id}:info", 3600)

    async def get_room_metadata(self, room_id: str) -> dict | None:
        """Получает метаданные комнаты из Redis"""
        return await self.client.hgetall(f"room:{room_id}:info")

    async def activate_room(self, room_id: str):
        """Активирует комнату (первый участник зашел)"""
        await self.client.sadd("active_rooms", room_id)

    async def deactivate_room(self, room_id: str):
        """Деактивирует комнату (последний участник вышел)"""
        await self.client.srem("active_rooms", room_id)

    async def get_active_rooms_info(self) -> list[dict]:
        """Возвращает список активных комнат с метаданными"""
        room_ids = await self.client.smembers("active_rooms")
        if not room_ids:
            return []

        rooms = []
        for room_id in room_ids:
            info = await self.client.hgetall(f"room:{room_id}:info")
            if info:
                rooms.append(info)
        return rooms

    async def add_participant(self, room_id: str, user_id: str):
        """Добавляет участника в комнату и активирует если первый"""
        count_before = await self.client.scard(f"room:{room_id}:users")
        await self.client.sadd(f"room:{room_id}:users", user_id)
        await self.client.expire(f"room:{room_id}:users", 3600)

        if count_before == 0:
            await self.activate_room(room_id)

    async def remove_participant(self, room_id: str, user_id: str):
        """Удаляет участника, если комната пуста — деактивирует"""
        await self.client.srem(f"room:{room_id}:users", user_id)

        count = await self.client.scard(f"room:{room_id}:users")
        if count == 0:
            await self.deactivate_room(room_id)
            await self.client.delete(f"room:{room_id}:users")
            # await self.client.delete(f"room:{room_id}:code")

    async def get_participant_count(self, room_id: str) -> int:
        """Количество участников в комнате"""
        return await self.client.scard(f"room:{room_id}:users")

    async def set_code(self, room_id: str, code: str):
        """Сохраняет код активной комнаты"""
        await self.client.setex(f"room:{room_id}:code", 3600, code)

    async def get_code(self, room_id: str) -> str | None:
        """Получает код активной комнаты"""
        return await self.client.get(f"room:{room_id}:code")

    async def delete_code(self, room_id: str):
        """Удаляет код комнаты"""
        await self.client.delete(f"room:{room_id}:code")