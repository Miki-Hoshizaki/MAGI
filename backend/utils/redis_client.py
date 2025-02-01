import redis
import json
import logging
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

class RedisClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'client'):
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            redis_db = getattr(settings, 'REDIS_DB', 0)
            redis_password = getattr(settings, 'REDIS_PASSWORD', None)
            
            self.client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True
            )
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a Redis channel"""
        try:
            result = self.client.publish(channel, json.dumps(message))
            return result > 0
        except Exception as e:
            logger.error(f"Error publishing to Redis channel {channel}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[str]:
        """Get a value from Redis"""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {str(e)}")
            return None
    
    def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set a value in Redis with optional expiration"""
        try:
            return self.client.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking existence of key {key} in Redis: {str(e)}")
            return False
    
    def publish_agent_result(self, session_id: str, result: Dict[str, Any]) -> bool:
        """Publish an agent result to the appropriate channel"""
        channel = f"backend:responses:{session_id}"
        return self.publish(channel, result)
    
    def close(self):
        """Close the Redis connection"""
        try:
            self.client.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")

# Global Redis client instance
redis_client = RedisClient() 