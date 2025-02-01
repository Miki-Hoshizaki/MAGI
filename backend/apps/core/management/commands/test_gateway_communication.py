"""
Django management command to test communication with the gateway.
"""
import json
import uuid
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from redis import Redis
from termcolor import colored
from utils.redis_channels import RedisChannels

class Command(BaseCommand):
    help = 'Test communication with the gateway via Redis'

    def __init__(self):
        super().__init__()
        self.redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
        self.session_id = str(uuid.uuid4())

    def send_test_request(self) -> dict:
        """
        Send a test request to the gateway requests channel.
        
        Returns:
            dict: The request data that was sent
        """
        request_data = {
            "session_id": self.session_id,
            "request_id": str(uuid.uuid4()),
            "type": "test",
            "content": "This is a test request from backend",
            "timestamp": time.time()
        }
        
        # Publish to gateway requests channel
        self.redis_client.publish(
            RedisChannels.GATEWAY_REQUESTS,
            json.dumps(request_data)
        )
        
        return request_data

    def monitor_results(self, timeout: int = 30) -> bool:
        """
        Monitor the results stream for the response.
        
        Args:
            timeout: Maximum time to wait for response in seconds
            
        Returns:
            bool: True if response received, False if timeout
        """
        results_stream = RedisChannels.result_stream(self.session_id)
        start_time = time.time()
        
        self.stdout.write("Monitoring results stream...")
        
        while time.time() - start_time < timeout:
            # Check for new messages in the stream
            response = self.redis_client.xread(
                {results_stream: "0-0"},
                count=1,
                block=1000
            )
            
            if response:
                stream_name, messages = response[0]
                message_id, message_data = messages[0]
                
                # Convert message data from bytes to dict
                message_data = {
                    k.decode('utf-8'): v.decode('utf-8')
                    for k, v in message_data.items()
                }
                
                return message_data
                
        return None

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting gateway communication test..."))
        self.stdout.write(f"Session ID: {self.session_id}")
        
        # Send test request
        self.stdout.write("\nSending test request...")
        request_data = self.send_test_request()
        self.stdout.write(colored("✓ Request sent", "green"))
        self.stdout.write(f"Request data: {json.dumps(request_data, indent=2)}")
        
        # Monitor for response
        self.stdout.write("\nWaiting for response (30s timeout)...")
        response_data = self.monitor_results()
        
        if response_data:
            self.stdout.write(colored("✓ Response received", "green"))
            self.stdout.write(f"Response data: {json.dumps(response_data, indent=2)}")
        else:
            self.stdout.write(colored("✗ No response received (timeout)", "red"))
            
        # Cleanup
        results_stream = RedisChannels.result_stream(self.session_id)
        self.redis_client.delete(results_stream)
        self.stdout.write("\nTest completed.")
