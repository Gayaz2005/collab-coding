from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import WebSocket
from pydantic import BaseModel


@dataclass
class Room:
    name: str
    id: UUID = field(default_factory=uuid4)
    code: str = '# Write your Python code here\n\nprint("Hello, World!")'
    language: str = 'python'
    created_at: datetime = field(default_factory=datetime.now)
    participant_count: int = 0

class RoomResponse(BaseModel):
    id: UUID
    name: str
    code: str
    language: str
    created_at: datetime
    participant_count: int

    class Config:
        from_attributes = True

