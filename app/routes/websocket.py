from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
from redis import asyncio as aioredis
from ..config import settings

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/feed")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Subscribe to Redis for new briefs
        redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = redis.pubsub()
        await pubsub.subscribe("new_briefs")
        
        # Listen for redis messages and push to websocket
        async def listen_to_redis():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await websocket.send_text(message["data"])

        # Run listener in background
        asyncio.create_task(listen_to_redis())
        
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        await pubsub.unsubscribe("new_briefs")
