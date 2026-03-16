from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from .storage import RoomStorage
from .models import Room, RoomResponse
from .websocket import ConnectionManager
from .executor import CodeExecutor

app = FastAPI(title="Collab Coding")
app.mount("/static", StaticFiles(directory="src/collab_coding/static"), name="static")
manager = ConnectionManager()
storage = RoomStorage()
executor = CodeExecutor()

@app.get("/")
async def root():
    """Отдаем HTML страницу"""
    return FileResponse("src/collab_coding/static/index.html")


@app.get("/api")
async def api_root():
    """Информация о API"""
    return {
        "message": "Collab Coding API",
        "version": "0.1.0",
        "rooms_count": len(storage.list_rooms())
    }


@app.post("/rooms", response_model=RoomResponse)
async def create_room(name: str = "New Room"):
    """Создать новую комнату"""
    room = storage.create_room(name)
    return room


@app.get("/rooms", response_model=list[RoomResponse])
async def list_rooms():
    """Получить список всех комнат"""
    return storage.list_rooms()


@app.get("/rooms/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str):
    """Получить комнату по ID"""
    room = storage.get(room_id)
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Room {room_id} not found"
        )
    return room


@app.delete("/rooms/{room_id}")
async def delete_room(room_id: str):
    """Удалить комнату"""
    deleted = storage.delete(room_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Room {room_id} not found"
        )
    return {"message": f"Room {room_id} deleted"}


@app.get("/rooms/{room_id}/code")
async def get_code(room_id: str):
    """Получить только код комнаты"""
    room = storage.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"code": room.code}


@app.put("/rooms/{room_id}/code")
async def update_code(room_id: str, code: str):
    """Обновить код в комнате"""
    room = storage.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room.code = code
    return {
        "message": "Code updated",
        "room_id": room_id,
        "code_length": len(code)
    }


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    room = storage.get(room_id)
    if not room:
        await websocket.close(code=1000, reason="Room not found")
        return
    
    await manager.connect(room_id, websocket)
    await websocket.send_text(room.code)
    
    try:
        while True:
            code = await websocket.receive_text()
            storage.update_code(room_id, code)
            await manager.broadcast(room_id, code, websocket)
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)


@app.post("/rooms/{room_id}/run")
async def run_room_code(room_id: str):
    room = storage.get(room_id)
    if not room:
        raise HTTPException(404, "Room not found")
    
    result = await executor.execute_code(room.code)
    return {"room_id": room_id, **result}


if __name__ == "__main__":
    uvicorn.run(
        "src.collab_coding.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )