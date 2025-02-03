from django.core.management.base import BaseCommand
import redis
import json
import logging
import os
from tasks.agent_dispatcher import process_request
from utils.redis_channels import RedisChannels
from config.celery import app

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs the Redis consumer for gateway requests'

    def handle(self, *args, **options):
        # Print Celery configuration
        self.stdout.write("\nCelery Configuration:")
        self.stdout.write("-" * 50)
        self.stdout.write(f"Broker URL: {app.conf.broker_url}")
        self.stdout.write(f"Result Backend: {app.conf.result_backend}")
        self.stdout.write(f"Task Default Queue: {app.conf.task_default_queue}")
        self.stdout.write(f"Task Serializer: {app.conf.task_serializer}")
        self.stdout.write(f"Accept Content: {app.conf.accept_content}")
        self.stdout.write("-" * 50 + "\n")
        
        # Get Redis URL from environment variable or use default
        redis_url = os.getenv('GATEWAY_REDIS_URL', 'redis://localhost:6379/0')
        self.stdout.write(f'Connecting to Redis at: {redis_url}')
        
        redis_client = redis.from_url(redis_url)
        pubsub = redis_client.pubsub()
        
        # Subscribe to gateway request pattern
        pattern = "gateway:requests:*"
        self.stdout.write(self.style.SUCCESS(f'Subscribing to pattern: {pattern}'))
        pubsub.psubscribe(pattern)
        
        try:
            for message in pubsub.listen():
                if message['type'] == 'pmessage':
                    try:
                        # Extract session_id from channel name
                        channel = message['channel'].decode()
                        session_id = channel.split(':')[-1]
                        
                        # Parse message data
                        data = json.loads(message['data'].decode())
                        self.stdout.write(f'Received message on channel {channel}')
                        # self.stdout.write(f'Message data: {json.dumps(data, indent=2)}')
                        
                        # Queue celery task
                        process_request.delay(
                            session_id=session_id,
                            message=data
                        )
                        
                        self.stdout.write(f'Queued task for session {session_id}')
                        
                    except json.JSONDecodeError as e:
                        logger.error(f'Failed to decode message: {e}')
                    except Exception as e:
                        logger.error(f'Error processing message: {e}')
                        raise e
                        
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Shutting down consumer...'))
            pubsub.punsubscribe()
            pubsub.close()
