#!/usr/bin/env python3

"""
Dummy server for testing MAGI Gateway communication.
This server listens to Redis channels and responds to client messages.
"""

import asyncio
import json
import logging
import signal
import time
import uuid
from redis.asyncio import Redis
from typing import Optional
from termcolor import colored

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DummyServer:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[Redis] = None
        self._running = False
        self._stop_event = asyncio.Event()
        
    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = Redis.from_url(self.redis_url)
            print(colored("✅ Connected to Redis", "green"))
            
    async def process_message(self, channel: str, message: str):
        """Process received message and send response"""
        try:
            data = json.loads(message)
            session_id = data.get("session_id")
            
            # Print received message
            print(colored("\n📥 Received message on channel: " + channel, "yellow"))
            print(colored(json.dumps(data, indent=2), "cyan"))
            
            # Prepare response based on message type
            if data.get("type") == "agent_judgement":
                response = {
                    "type": "agent_judgement_response",
                    "session_id": session_id,
                    "status": "success",
                    "request_id": data.get("context", {}).get("request_id"),
                    "results": [
                        {
                            "agent_id": agent["agent_id"],
                            "status": "processed",
                            "processing_time": 0.5,
                            "response": {
                                "accepted": True,
                                "score_normalized": agent["judgement"]["score"] * 1.1,  # Adjust score for testing
                                "confidence": agent["judgement"]["metadata"]["confidence"]
                            }
                        }
                        for agent in data.get("agents", [])
                    ],
                    "timestamp": time.time()
                }
                
                # Send response back through Redis
                response_channel = f"gateway:responses:{session_id}"
                await self.redis_client.publish(response_channel, json.dumps(response))
                
                # Print sent response
                print(colored("\n📤 Sent response on channel: " + response_channel, "green"))
                print(colored(json.dumps(response, indent=2), "cyan"))
        except Exception as e:
            logger.error(f"Error processing message: {e}")
                
    async def subscribe_to_channels(self):
        """Subscribe to relevant Redis channels"""
        try:
            # Create a new connection for pubsub
            pubsub = self.redis_client.pubsub()
            
            # Subscribe to all gateway request channels
            pattern = "gateway:requests:*"
            print(colored(f"🔔 Subscribing to pattern: {pattern}", "yellow"))
            
            await pubsub.psubscribe(pattern)
            
            # Listen for messages
            while not self._stop_event.is_set():
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    await self.process_message(
                        message["channel"].decode(),
                        message["data"].decode()
                    )
                await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Error in subscription: {e}")
            raise
        finally:
            await pubsub.close()
            
    def stop(self):
        """Stop the server"""
        self._stop_event.set()
        self._running = False
        
async def main():
    # Create server instance
    server = DummyServer()
    
    # Handle Ctrl+C
    def signal_handler():
        print(colored("\n\n👋 Stopping server...", "yellow"))
        server.stop()
    
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)
    
    try:
        # Connect to Redis
        await server.connect()
        
        # Start subscription
        print(colored("🚀 Starting dummy server...", "green"))
        await server.subscribe_to_channels()
        
    except Exception as e:
        print(colored(f"\n❌ Error: {e}", "red"))
    finally:
        if server.redis_client:
            await server.redis_client.close()
            print(colored("\n👋 Connection closed", "yellow"))

if __name__ == "__main__":
    print(colored("\n🎯 MAGI Gateway Dummy Server", "cyan", attrs=["bold"]))
    print(colored("=" * 50, "cyan"))
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(colored("\n👋 Server stopped by user", "yellow"))
