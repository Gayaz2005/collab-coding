from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4, UUID
from datetime import datetime, timezone

from .models import RoomResponse, RoomCreate
from .models_db import Rooms as RoomsDB


class RoomStorage:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_room(self, data: RoomCreate) -> RoomResponse:
        room = RoomsDB(
            uuid=uuid4(),
            name=data.name,
            language=data.language,
        )
        self.db.add(room)
        await self.db.flush()
        return RoomResponse(
            uuid=room.uuid,
            name=room.name,
            language=room.language,
            created_at=room.created_at,
            updated_at=room.updated_at
        )

    async def update_code(self, room_id: UUID, code: str) -> RoomResponse | None:
        """Обновляет время изменения кода в БД"""
        result = await self.db.execute(
            select(RoomsDB).where(RoomsDB.uuid == room_id)
        )
        room = result.scalar_one_or_none()
        if not room:
            return None
        
        room.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        
        return RoomResponse(
            uuid=room.uuid,
            name=room.name,
            language=room.language,
            created_at=room.created_at,
            updated_at=room.updated_at
        )

    async def get(self, room_id: UUID) -> RoomResponse | None:
        result = await self.db.execute(
            select(RoomsDB).where(RoomsDB.uuid == room_id)
        )
        room = result.scalar_one_or_none()
        if not room:
            return None
        
        return RoomResponse(
            uuid=room.uuid,
            name=room.name,
            language=room.language,
            created_at=room.created_at,
            updated_at=room.updated_at
        )

    async def delete(self, room_id: UUID) -> bool:
        result = await self.db.execute(
            select(RoomsDB).where(RoomsDB.uuid == room_id)
        )
        room = result.scalar_one_or_none()
        if not room:
            return False
        
        await self.db.delete(room)
        await self.db.flush()
        return True
    
    
