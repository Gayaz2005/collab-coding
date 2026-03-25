from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str
    language: str
    created_at: datetime
    updated_at: datetime


class RoomCreate(BaseModel):
    name: str
    language: str = 'python'


class CodeUpdate(BaseModel):
    code: str
