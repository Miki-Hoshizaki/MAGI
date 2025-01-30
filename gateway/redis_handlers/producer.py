import json
import redis.asyncio as redis
import logging
from config import settings

logger = logging.getLogger(__name__)

async def get_redis_connection():
    """Get Redis connection from pool"""
    return redis.from_url(
        settings.get_redis_url(),
        encoding="utf-8",
        decode_responses=True
    )

async def send_to_redis(message: dict):
    """Send message to appropriate Redis queue based on message type"""
    try:
        message_type = message.get("type", "default")
        queue_name = f"queue_{message_type}"
        
        redis_client = await get_redis_connection()
        try:
            await redis_client.lpush(queue_name, json.dumps(message))
            logger.info(f"Message sent to Redis queue {queue_name}")
        finally:
            await redis_client.close()
    
    except Exception as e:
        logger.error(f"Error sending message to Redis: {str(e)}")
        raise 