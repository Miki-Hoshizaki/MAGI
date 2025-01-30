import json
import asyncio
import logging
from typing import Optional
from redis.asyncio import Redis
from websocket_manager import ConnectionManager
from .producer import get_redis_connection

logger = logging.getLogger(__name__)

class RedisConsumer:
    def __init__(self, websocket_manager: ConnectionManager):
        self.websocket_manager = websocket_manager
        self.redis_client: Optional[Redis] = None
        self._running = False
        self._stop_event = asyncio.Event()
        
    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = await get_redis_connection()
            logger.debug("Connected to Redis")
    
    async def process_message(self, message: dict):
        """Process received message"""
        session_id = message.get("session_id")
        if not session_id:
            logger.warning("Received message without session_id")
            return
            
        await self.websocket_manager.send_message(session_id, message)
        logger.debug(f"Processed message for session {session_id}")
    
    async def consume_messages(self):
        """Start consuming messages from Redis queues"""
        logger.debug("Starting consumer...")
        try:
            await self.connect()
            self._running = True
            self._stop_event.clear()
            
            while self._running:
                try:
                    # Use wait_for to handle blpop, allowing faster response to stop signals
                    result = await asyncio.wait_for(
                        self.redis_client.blpop(
                            ["queue_agent_judgement_stream", "queue_agent_judgement_final"],
                            timeout=1
                        ),
                        timeout=1.5
                    )
                    
                    if result:
                        _, message_data = result
                        try:
                            message = json.loads(message_data)
                            await self.process_message(message)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON message: {message_data}")
                            
                except asyncio.TimeoutError:
                    if not self._running:
                        logger.debug("Consumer stopped due to stop signal")
                        break
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    if not self._running:
                        break
                    
                # Check stop signal
                if self._stop_event.is_set():
                    logger.debug("Stop event detected")
                    break
                    
        except Exception as e:
            logger.error(f"Error consuming Redis messages: {e}")
        finally:
            self._running = False
            if self.redis_client:
                await self.redis_client.close()
                logger.debug("Redis connection closed")
            self._stop_event.set()
    
    def stop(self):
        """Stop the consumer"""
        logger.debug("Stopping consumer...")
        self._running = False
        self._stop_event.set() 