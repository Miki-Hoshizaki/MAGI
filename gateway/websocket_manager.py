from typing import Dict, Optional
from fastapi import WebSocket
import json
import logging
from .redis_handlers.producer import send_to_redis

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept connection and store it"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"New connection established: {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"Connection closed: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """Send message to a specific client"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {str(e)}")
                await self.disconnect(session_id)
    
    async def handle_message(self, session_id: str, message: dict):
        """Handle incoming message from client"""
        try:
            message_type = message.get("type")
            if not message_type:
                await self.send_message(session_id, {
                    "error": "Missing message type"
                })
                return
            
            if message_type == "agent_judgement":
                agent_ids = message.get("agent_ids")
                if not agent_ids:
                    await self.send_message(session_id, {
                        "error": "Missing agent_ids for agent_judgement"
                    })
                    return
                
                # Add session_id to message before sending to Redis
                message["session_id"] = session_id
                await send_to_redis(message)
            
            elif message_type == "unregister":
                # Handle unregister message (reserved for future use)
                pass
            
            else:
                await self.send_message(session_id, {
                    "error": f"Unsupported message type: {message_type}"
                })
        
        except Exception as e:
            logger.error(f"Error handling message from {session_id}: {str(e)}")
            await self.send_message(session_id, {
                "error": "Internal server error"
            }) 