import json
import logging
from celery import shared_task
from typing import Dict, Any
from redis import Redis
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task
def handle_gateway_message(message: Dict[str, Any]) -> None:
    """
    Celery task to handle messages received from Gateway via Redis queues
    
    Args:
        message: The message received from Gateway
    """
    try:
        message_type = message.get("type")
        session_id = message.get("session_id")
        
        if not message_type or not session_id:
            logger.error("Received invalid message format: missing type or session_id")
            return
            
        if message_type == "agent_judgement":
            agent_ids = message.get("agent_ids", [])
            if not agent_ids:
                logger.error("Received agent_judgement request without agent_ids")
                return
                
            # TODO: Implement agent judgment logic here
            # This is where you would process the agent_ids and return results
            # You can use the GatewayClient to send responses back
            
            logger.info(f"Processing agent judgment for session {session_id}")
            
        else:
            logger.warning(f"Received unknown message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error processing Gateway message: {str(e)}")
        raise

def start_gateway_consumer():
    """
    Start consuming messages from Gateway Redis queues
    This should be called when Django starts
    """
    try:
        redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        
        logger.info("Starting Gateway message consumer...")
        
        while True:
            try:
                # Wait for messages from Gateway queues
                result = redis_client.blpop(
                    ["queue_agent_judgement"],
                    timeout=1
                )
                
                if result:
                    _, message_data = result
                    try:
                        message = json.loads(message_data)
                        # Process message asynchronously using Celery
                        handle_gateway_message.delay(message)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON message from Gateway: {message_data}")
                        
            except Exception as e:
                logger.error(f"Error in Gateway consumer loop: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to start Gateway consumer: {str(e)}")
    finally:
        redis_client.close()
