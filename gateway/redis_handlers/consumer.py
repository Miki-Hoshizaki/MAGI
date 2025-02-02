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
        message_type = message.get("type")
        
        # Handle system control messages
        if message_type == "disconnected_all":
            await self.websocket_manager.disconnect_all()
            return
        elif message_type == "broadcast":
            broadcast_message = message.get("message")
            if broadcast_message:
                await self.websocket_manager.broadcast(broadcast_message)
            else:
                logger.warning("Received broadcast message without content")
            return
            
        # Handle regular messages
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
            if not self.redis_client:
                await self.connect()

            # Subscribe to both system messages and response messages
            pubsub = self.redis_client.pubsub()
            ret = await pubsub.psubscribe("gateway:system:*", "gateway:responses:*")
            
            self._running = True
            logger.info("Consumer started successfully")
            
            while self._running:
                if self._stop_event.is_set():
                    break
                    
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message is None:
                    await asyncio.sleep(0.1)
                    continue
                
                try:
                    channel = message.get("channel", b"").decode()
                    data = message.get("data", b"").decode()
                    
                    if not data:
                        continue
                        
                    message_data = json.loads(data)
                    await self.process_message(message_data)
                    
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode message: {message}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}")
        finally:
            self._running = False
            if pubsub:
                await pubsub.punsubscribe()
                await pubsub.close()
    
    def stop(self):
        """Stop the consumer"""
        logger.debug("Stopping consumer...")
        self._running = False
        self._stop_event.set()