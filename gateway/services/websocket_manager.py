from fastapi import WebSocket
import json
import redis
import asyncio
from typing import Dict
from ..config import settings

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(
                json.dumps(message)
            )
            
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_text(json.dumps(message))
            
    async def handle_message(self, client_id: str, message: dict):
        """Handle received WebSocket message"""
        message_type = message.get("type")
        
        if message_type == "ping":
            await self.send_personal_message({"type": "pong"}, client_id)
        else:
            # TODO: handle other message types
            pass
