import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self, msg_queue: asyncio.Queue):
        self.active_connections: list[WebSocket] = []
        self.msg_queue = msg_queue

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

    async def run(self) -> None:
        while True:
            msg = await self.msg_queue.get()
            await self.broadcast(json.dumps(msg))
