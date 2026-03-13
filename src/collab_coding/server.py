from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from .storage import RoomStorage
from .models import Room, RoomResponse


app = FastAPI(title="Collab Coding")
app.mount("/static", StaticFiles(directory="src/collab_coding/static"), name="static")

storage = RoomStorage()


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


if __name__ == "__main__":
    uvicorn.run(
        "src.collab_coding.server:app",
        reload=True
    )