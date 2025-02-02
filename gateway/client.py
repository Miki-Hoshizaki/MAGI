#!/usr/bin/env python3

"""
Test client for the MAGI Gateway WebSocket interface.
This client connects to the gateway, sends test messages, and waits for responses.
"""

import asyncio
import json
import time
import hashlib
import websockets
import argparse
import signal
from typing import Optional
from urllib.parse import urlencode
import uuid
from termcolor import colored
from datetime import datetime

class GatewayClient:
    def __init__(self, host: str = "localhost", port: int = 8888, appid: str = "b75fce6f-e8af-4207-9c32-f8166afb4520"):
        self.host = host
        self.port = port
        self.appid = appid
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self.running = True
        
    def generate_token(self) -> str:
        """Generate authentication token"""
        current_minute = int(time.time() // 60)
        secret = "magi-gateway-development-secret"  # Gateway's FIXED_SECRET
        raw_str = f"{self.appid}{secret}{current_minute}"
        return hashlib.sha256(raw_str.encode()).hexdigest()[:10]
        
    def get_ws_url(self) -> str:
        """Generate WebSocket URL with authentication parameters"""
        params = {
            "appid": self.appid,
            "token": self.generate_token()
        }
        return f"ws://{self.host}:{self.port}/ws?{urlencode(params)}"
        
    async def connect(self):
        """Connect to the gateway"""
        url = self.get_ws_url()
        print(colored("🔌 Connecting to gateway...", "yellow"))
        print(colored(f"URL: {url}", "cyan"))
        self.ws = await websockets.connect(url)
        
        # Wait for connection confirmation
        response = await self.ws.recv()
        data = json.loads(response)
        if data.get("type") == "connection_established":
            self.session_id = data.get("session_id")
            print(colored("✅ Connected successfully!", "green"))
            print(colored(f"Session ID: {self.session_id}", "cyan"))
        else:
            raise Exception("Failed to establish connection")

    async def ping(self) -> bool:
        """Send ping message and wait for pong"""
        if not self.ws:
            raise Exception("Not connected")
            
        print(colored("\n🏓 Sending ping...", "yellow"))
        await self.ws.send(json.dumps({"type": "ping"}))
        
        response = await self.ws.recv()
        data = json.loads(response)
        if data.get("type") == "pong":
            print(colored("✅ Received pong", "green"))
            return True
        return False
            
    async def send_message(self, message_type: str, content: dict):
        """Send a message to the gateway"""
        if not self.ws:
            raise Exception("Not connected")
            
        message = {
            "type": message_type,
            **content,
            "timestamp": time.time()
        }
        
        print(colored("\n📤 Sending message:", "yellow"))
        print(colored(json.dumps(message, indent=2), "cyan"))
        
        await self.ws.send(json.dumps(message))
        
    async def receive_messages(self):
        """Continuously receive messages until interrupted"""
        if not self.ws:
            raise Exception("Not connected")
            
        while self.running:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                timestamp = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                print(colored(f"\n📥 Received at {timestamp}:", "green"))
                print(colored(json.dumps(data, indent=2), "cyan"))
            except websockets.exceptions.ConnectionClosed:
                print(colored("\n❌ Connection closed", "red"))
                break
            except Exception as e:
                print(colored(f"\n❌ Error receiving message: {e}", "red"))
                break
                
    def stop(self):
        """Stop the client"""
        self.running = False

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MAGI Gateway Test Client")
    parser.add_argument("--host", default="localhost", help="Gateway host")
    parser.add_argument("--port", type=int, default=8888, help="Gateway port")
    parser.add_argument("--appid", default="b75fce6f-e8af-4207-9c32-f8166afb4520", help="Application ID")
    args = parser.parse_args()
    
    # Create client
    client = GatewayClient(args.host, args.port, args.appid)
    
    # Handle Ctrl+C
    def signal_handler():
        print(colored("\n\n👋 Stopping client...", "yellow"))
        client.stop()
    
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)
    
    try:
        # Connect to gateway
        await client.connect()
        
        # Send ping and wait for pong before starting message receiver
        if not await client.ping():
            print(colored("❌ Ping failed, exiting...", "red"))
            return
            
        # Start message receiver
        receiver_task = asyncio.create_task(client.receive_messages())
            
        # Construct agent judgement message
        message = {
            "type": "agent_judgement",
            "request_id": str(uuid.uuid4()),
            "request": '''
            <user_request>
Write a sorting algorithm in Python
</user_request>

<response>
I'll write a Python implementation of the merge sort algorithm, which is an efficient, stable sorting algorithm with O(n log n) time complexity.

```python
def merge_sort(arr):
    # Base case: if array has 1 or fewer elements, it's already sorted
    if len(arr) <= 1:
        return arr
    
    # Split array into two halves
    mid = len(arr) // 2
    left = arr[:mid]
    right = arr[mid:]
    
    # Recursively sort both halves
    left = merge_sort(left)
    right = merge_sort(right)
    
    # Merge the sorted halves
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    # Compare elements from both arrays and merge them in sorted order
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    # Add remaining elements from left array, if any
    result.extend(left[i:])
    # Add remaining elements from right array, if any
    result.extend(right[j:])
    
    return result

# Example usage:
if __name__ == "__main__":
    # Test the sorting algorithm
    test_array = [64, 34, 25, 12, 22, 11, 90]
    sorted_array = merge_sort(test_array)
    print(f"Original array: {test_array}")
    print(f"Sorted array: {sorted_array}")
```

This implementation of merge sort works by:

1. Dividing the input array into two halves recursively until we have single elements
2. Merging these sorted smaller arrays back together in sorted order
3. Continuing this process until we have one fully sorted array

The algorithm is particularly efficient for large datasets and has several advantages:

* Stable sorting (maintains relative order of equal elements)
* Guaranteed O(n log n) time complexity regardless of input
* Works well for linked lists
* Predictable performance

Would you like me to explain any part of the implementation in more detail?
            ''',
            "agents": [
                {
                    "agent_id": "89cbe912-25d0-47b0-97da-b25622bfac0d",
                },
                {
                    "agent_id": "6634d0ec-d700-4a92-9066-4960a0f11927",
                },
                {
                    "agent_id": "d37c1cc8-bcc4-4b73-9f49-a93a30971f2c",
                }
            ],
            "timestamp": time.time()
        }
        
        # Send message
        await client.send_message("agent_judgement", message)
        
        # Keep running until interrupted
        try:
            await receiver_task
        except asyncio.CancelledError:
            pass
            
    except Exception as e:
        print(colored(f"\n❌ Error: {e}", "red"))
    finally:
        if client.ws:
            await client.ws.close()
            print(colored("\n👋 Connection closed", "yellow"))

if __name__ == "__main__":
    print(colored("\n🚀 MAGI Gateway Test Client", "cyan", attrs=["bold"]))
    print(colored("=" * 50, "cyan"))
    asyncio.run(main())
