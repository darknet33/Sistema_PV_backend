from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws import manager

router = APIRouter()


@router.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    if room not in {"productos", "ventas", "compras", "dashboard", "reportes"}:
        await websocket.close(code=4000, reason="Sala no válida")
        return

    await manager.connect(websocket, room)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, room)
