from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from .database import get_db, init_db
from .storage import RoomStorage
from .models import RoomCreate, RoomResponse, CodeUpdate
from .websocket import ConnectionManager
from .executor import CodeExecutor
from .redis_client import RedisClient
from .minio_client import MinioClient

app = FastAPI(title="Collab Coding")
app.mount("/static", StaticFiles(directory="src/collab_coding/static"), name="static")

manager = ConnectionManager()
executor = CodeExecutor()
redis_client = RedisClient()
minio_client = MinioClient()


@app.get("/")
async def root():
    """Отдаем HTML страницу"""
    return FileResponse("src/collab_coding/static/index.html")

@app.on_event("startup")
async def startup():
    """Создает таблицы при запуске"""
    await init_db()

@app.get("/api")
async def api_root():
    """Информация о API"""
    return {
        "message": "Collab Coding API",
        "version": "0.1.0",
    }


@app.post("/rooms", response_model=RoomResponse)
async def create_room(
    room_data: RoomCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новую комнату"""
    storage = RoomStorage(db)
    room = await storage.create_room(room_data)

    await redis_client.set_room_metadata(
        str(room.uuid),
        room.name,
        room.language,
        room.created_at.isoformat(),
        room.updated_at.isoformat()
    )
    return room


@app.get("/rooms")
async def list_rooms():
    """Получить список активных комнат"""
    rooms = await redis_client.get_active_rooms_info()

    result = []
    for room in rooms:
        participants = await redis_client.get_participant_count(room["room_id"])
        result.append({
            "id": room["room_id"],
            "name": room["name"],
            "language": room["language"],
            "created_at": room["created_at"],
            "updated_at": room["updated_at"],
            "participants": participants
        })
    return result

@app.get("/rooms/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Получить комнату по ID"""
    storage = RoomStorage(db)
    room = await storage.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@app.delete("/rooms/{room_id}")
async def delete_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Удалить комнату"""
    storage = RoomStorage(db)
    if not await storage.delete(room_id):
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Room deleted"}


@app.get("/rooms/{room_id}/code")
async def get_code(
    room_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Получить код комнаты (из Redis или MinIO)"""
    storage = RoomStorage(db)
    room = await storage.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    code = await redis_client.get_code(str(room_id))
    if code is None:
        code = await minio_client.get_code(str(room_id))

    return {"code": code or ""}


@app.put("/rooms/{room_id}/code")
async def update_code(
    room_id: UUID,
    update: CodeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить код в комнате (сохраняется в Redis)"""
    storage = RoomStorage(db)

    room = await storage.update_code(room_id, update.code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    await redis_client.set_code(str(room_id), update.code)

    return {
        "message": "Code updated",
        "room_id": str(room_id),
        "code_length": len(update.code)
    }


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    storage = RoomStorage(db)
    room = await storage.get(room_id)
    if not room:
        await websocket.close(code=1000, reason="Room not found")
        return

    await manager.connect(str(room_id), websocket, room.name, room.language)

    code = await redis_client.get_code(str(room_id))
    if code is None:
        code_tuple = await minio_client.get_code(str(room_id))
        code = code_tuple[0] if code_tuple else ""
    await websocket.send_text(code or "")

    try:
        while True:
            code = await websocket.receive_text()
            await redis_client.set_code(str(room_id), code)
            await manager.broadcast(str(room_id), code, websocket)
    except WebSocketDisconnect:
        await manager.disconnect(str(room_id), websocket)


@app.post("/rooms/{room_id}/run")
async def run_room_code(
    room_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    room = await RoomStorage(db).get(room_id)
    if not room:
        raise HTTPException(404, "Room not found")

    code = await redis_client.get_code(str(room_id))
    if code is None:
        code, _ = await minio_client.get_code(str(room_id))

    result = await executor.execute_code(code or "")
    return {"room_id": str(room_id), **result}


if __name__ == "__main__":
    uvicorn.run(
        "src.collab_coding.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
