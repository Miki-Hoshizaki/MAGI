import json
import aioredis
import logging
from ..config import settings

logger = logging.getLogger(__name__)

async def get_redis_connection():
    """Get Redis connection from pool"""
    return await aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )

async def send_to_redis(message: dict):
    """Send message to appropriate Redis queue based on message type"""
    try:
        message_type = message.get("type", "default")
        queue_name = f"queue_{message_type}"
        
        redis = await get_redis_connection()
        try:
            await redis.lpush(queue_name, json.dumps(message))
            logger.info(f"Message sent to Redis queue {queue_name}")
        finally:
            await redis.close()
    
    except Exception as e:
        logger.error(f"Error sending message to Redis: {str(e)}")
        raise 