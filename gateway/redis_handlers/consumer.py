import json
import asyncio
import aioredis
import logging
from ..websocket_manager import ConnectionManager
from ..config import settings

logger = logging.getLogger(__name__)

class RedisConsumer:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.should_stop = False
    
    async def start_consuming(self):
        """Start consuming messages from Redis response queue"""
        redis = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        try:
            while not self.should_stop:
                try:
                    # Try to get message from response queue with timeout
                    result = await redis.blpop(
                        "queue_agent_judgement_stream",
                        "queue_agent_judgement_final",
                        timeout=5
                    )
                    
                    if result:
                        queue_name, msg_data = result
                        await self.process_message(json.loads(msg_data))
                    else:
                        # No message received, continue polling
                        await asyncio.sleep(0.1)
                
                except Exception as e:
                    logger.error(f"Error processing Redis message: {str(e)}")
                    await asyncio.sleep(1)  # Wait before retry
        
        finally:
            await redis.close()
    
    async def process_message(self, message: dict):
        """Process received message and send to appropriate WebSocket client"""
        try:
            session_id = message.get("session_id")
            if not session_id:
                logger.error("Received message without session_id")
                return
            
            # Forward message to WebSocket client
            await self.manager.send_message(session_id, message)
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def stop(self):
        """Stop the consumer"""
        self.should_stop = True 