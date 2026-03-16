from .models import Room


class RoomStorage:
    def __init__(self):
        self._rooms: dict[str, Room] = {}


    def create_room(self, name: str):
        room = Room(name=name)
        self._rooms[str(room.id)] = room
        return room
    
    def update_code(self, room_id: str, new_code: str) -> Room | None:
        """Обновить код в комнате"""
        room = self._rooms.get(room_id)
        if room:
            room.code = new_code
            print(f"Код обновлен в комнате {room_id}")
        return room

    def get(self, room_id: str) -> Room | None:
        return self._rooms.get(room_id)


    def delete(self, room_id: str) -> bool:
        if room_id in self._rooms:
            del self._rooms[room_id]
            return True
        return False
    

    def list_rooms(self) -> list[Room]:
        return list(self._rooms.values())