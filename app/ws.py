import asyncio
from fastapi import WebSocket
from typing import Set, Dict, Any, Optional
import json


class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.rooms:
            self.rooms[room].discard(websocket)
            if not self.rooms[room]:
                del self.rooms[room]

    async def broadcast(self, room: str, data: Dict[str, Any]):
        if room not in self.rooms:
            return
        payload = json.dumps(data, default=str)
        stale = set()
        for ws in self.rooms[room]:
            try:
                await ws.send_text(payload)
            except Exception:
                stale.add(ws)
        for ws in stale:
            self.rooms[room].discard(ws)
        if not self.rooms[room]:
            del self.rooms[room]

    async def broadcast_multiple(self, rooms: list[str], data: Dict[str, Any]):
        for room in rooms:
            await self.broadcast(room, data)


manager = ConnectionManager()

_loop: Optional[asyncio.AbstractEventLoop] = None


def init_loop(loop: asyncio.AbstractEventLoop):
    global _loop
    _loop = loop


def broadcast_sync(room: str, data: Dict[str, Any]):
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(manager.broadcast(room, data), _loop)


def broadcast_multiple_sync(rooms: list[str], data: Dict[str, Any]):
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(manager.broadcast_multiple(rooms, data), _loop)
