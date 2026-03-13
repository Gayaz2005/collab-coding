from typing import Dict, Optional
from .models import Room


class RoomStorage:
    def __init__(self):
        self._rooms: Dict[str, Room] = {}


    def create_room(self, name: str):
        room = Room(name=name)
        self._rooms[str(room.id)] = room
        return room
    

    def get(self, room_id: str) -> Optional[Room]:
        return self._rooms.get(room_id)


    def delete(self, room_id: str) -> bool:
        if room_id in self._rooms:
            del self._rooms[room_id]
            return True
        return False
    

    def list_rooms(self) -> list[Room]:
        return list(self._rooms.values())