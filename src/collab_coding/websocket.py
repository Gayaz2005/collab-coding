from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        # {room_id: {websocket1, websocket2, ...}}
        self.active_connections: dict[str, set[WebSocket]] = {}
    
    async def connect(self, room_id: str, websocket: WebSocket):
        """Новое подключение к комнате"""
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)
        
        print(f"Подключился к комнате {room_id}. Всего: {len(self.active_connections[room_id])}")
    
    def disconnect(self, room_id: str, websocket: WebSocket):
        """Отключение от комнаты"""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
                print(f"Комната {room_id} пуста, удалена")
            else:
                print(f"Отключился из комнаты {room_id}. Осталось: {len(self.active_connections[room_id])}")
    
    async def broadcast(self, room_id: str, message: str, sender: WebSocket):
        """Отправить всем в комнате кроме отправителя"""
        if room_id not in self.active_connections:
            return
        
        for connection in self.active_connections[room_id]:
            if connection != sender:
                try:
                    await connection.send_text(message)
                except:
                    pass  # клиент отключился, почистится позже
    
    async def broadcast_to_all(self, room_id: str, message: str):
        """Отправить всем в комнате (включая отправителя)"""
        if room_id not in self.active_connections:
            return
        
        for connection in self.active_connections[room_id]:
            try:
                await connection.send_text(message)
            except:
                pass
    
    def get_room_count(self, room_id: str) -> int:
        """Сколько человек в комнате"""
        return len(self.active_connections.get(room_id, set()))