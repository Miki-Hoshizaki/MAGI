"""
Result pusher service for handling Redis stream messages and pushing to WebSocket clients.
"""
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from redis.exceptions import RedisError
from utils.redis_client import redis_client
from utils.redis_channels import RedisChannels

logger = logging.getLogger(__name__)

class ResultPusher:
    """
    Service for pushing results from Redis streams to WebSocket clients.
    """
    def __init__(self):
        self._active_sessions: Dict[str, WebSocket] = {}
        
    async def register_session(self, session_id: str, websocket: WebSocket) -> None:
        """
        Register a new WebSocket connection for a session.
        
        Args:
            session_id: The unique session identifier
            websocket: The WebSocket connection
        """
        await websocket.accept()
        self._active_sessions[session_id] = websocket
        logger.info(f"Registered WebSocket for session {session_id}")
        
    async def unregister_session(self, session_id: str) -> None:
        """
        Unregister a WebSocket connection.
        
        Args:
            session_id: The unique session identifier
        """
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            logger.info(f"Unregistered WebSocket for session {session_id}")
            
    async def start_result_listener(self, session_id: str) -> None:
        """
        Start listening for results for a specific session.
        
        Args:
            session_id: The unique session identifier
        """
        websocket = self._active_sessions.get(session_id)
        if not websocket:
            logger.error(f"No active WebSocket for session {session_id}")
            return
            
        try:
            # Initialize stream positions
            streams = {
                RedisChannels.result_stream(session_id): '0-0',
                RedisChannels.agent_task_stream(session_id): '0-0'
            }
            
            while session_id in self._active_sessions:
                try:
                    # Read from both streams
                    messages = redis_client.xread(
                        streams,
                        count=1,
                        block=5000
                    )
                    
                    if not messages:
                        continue
                        
                    # Process and send messages
                    for stream_name, stream_messages in messages:
                        stream_name = stream_name.decode('utf-8')
                        for msg_id, msg_data in stream_messages:
                            # Update stream position
                            streams[stream_name] = msg_id.decode('utf-8')
                            
                            # Prepare message for client
                            client_message = {
                                'stream': stream_name,
                                'data': msg_data
                            }
                            
                            # Send to client
                            await websocket.send_json(client_message)
                            
                except RedisError as e:
                    logger.error(f"Redis error in result listener: {str(e)}")
                    await asyncio.sleep(1)  # Back off on error
                    continue
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")
            await self.unregister_session(session_id)
            
        except Exception as e:
            logger.error(f"Error in result listener: {str(e)}")
            await self.unregister_session(session_id)
            
    async def handle_client_connection(self, session_id: str, websocket: WebSocket) -> None:
        """
        Handle a new client WebSocket connection.
        
        Args:
            session_id: The unique session identifier
            websocket: The WebSocket connection
        """
        await self.register_session(session_id, websocket)
        
        try:
            # Start result listener
            await self.start_result_listener(session_id)
            
        except Exception as e:
            logger.error(f"Error handling client connection: {str(e)}")
            await self.unregister_session(session_id)
            
# Global result pusher instance
result_pusher = ResultPusher()
