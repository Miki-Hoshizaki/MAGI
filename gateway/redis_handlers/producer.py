import json
import logging
import redis.asyncio as redis
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RedisProducer:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis = None
    
    async def connect(self):
        """Establish Redis connection"""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url)
    
    async def publish_request(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Publish a request message to Redis"""
        try:
            if not self.redis:
                await self.connect()
            
            # Add session_id to message if not present
            if "session_id" not in message:
                message["session_id"] = session_id
            
            # Publish to the gateway requests channel
            channel = f"gateway:requests:{session_id}"
            result = await self.redis.publish(channel, json.dumps(message))
            
            logger.info(f"Published message for session {session_id}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Error publishing message for session {session_id}: {str(e)}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()

# Global producer instance
producer = RedisProducer()

async def send_to_redis(message: Dict[str, Any]) -> bool:
    """Helper function to send a message to Redis"""
    session_id = message.get("session_id")
    if not session_id:
        logger.error("Message missing session_id")
        return False
    
    return await producer.publish_request(session_id, message) 