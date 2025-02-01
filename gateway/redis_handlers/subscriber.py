import json
import logging
import asyncio
import redis.asyncio as redis
from typing import Optional, Dict
from websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)

class RedisSubscriber:
    def __init__(self, connection_manager: ConnectionManager, redis_url: str = "redis://localhost:6379"):
        self.connection_manager = connection_manager
        self.redis_url = redis_url
        self.pubsub: Optional[redis.client.PubSub] = None
        self.is_running = False
        
    async def connect(self):
        """Establish Redis connection and subscribe to channels"""
        try:
            self.redis = redis.from_url(self.redis_url)
            self.pubsub = self.redis.pubsub()
            # Subscribe to all backend response channels
            await self.pubsub.psubscribe("backend:responses:*")
            logger.info("Successfully subscribed to backend response channels")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {str(e)}")
            raise
    
    async def start(self):
        """Start listening for messages"""
        self.is_running = True
        try:
            while self.is_running:
                if not self.pubsub:
                    await self.connect()
                
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    await self.handle_message(message)
                
                await asyncio.sleep(0.01)  # Prevent CPU overload
                
        except Exception as e:
            logger.error(f"Error in message loop: {str(e)}")
            self.is_running = False
            raise
        finally:
            await self.cleanup()
    
    async def stop(self):
        """Stop the subscriber"""
        self.is_running = False
        await self.cleanup()
    
    async def cleanup(self):
        """Clean up Redis connections"""
        if self.pubsub:
            await self.pubsub.punsubscribe()
            await self.pubsub.close()
        if hasattr(self, 'redis'):
            await self.redis.close()
    
    async def handle_message(self, message: Dict):
        """Handle incoming Redis message"""
        try:
            if message["type"] != "pmessage":
                return
            
            # Parse the message data
            data = json.loads(message["data"])
            session_id = data.get("session_id")
            
            if not session_id:
                logger.error("Received message without session_id")
                return
            
            # Forward message to appropriate WebSocket client
            await self.connection_manager.send_message(session_id, data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding message: {str(e)}")
        except Exception as e:
            logger.error(f"Error handling Redis message: {str(e)}")

async def start_subscriber(connection_manager: ConnectionManager):
    """Helper function to start the subscriber"""
    subscriber = RedisSubscriber(connection_manager)
    await subscriber.connect()
    return subscriber 