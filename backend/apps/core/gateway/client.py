import json
import logging
import redis
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GatewayClient:
    """Client for communicating with the Gateway service via Redis"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
    
    def send_message(self, session_id: str, message: Dict[str, Any], message_type: str = "agent_judgement_stream") -> None:
        """
        Send a message to a specific session through the Gateway
        
        Args:
            session_id: The target session ID
            message: The message content to send
            message_type: Type of message (default: agent_judgement_stream)
        """
        try:
            # Prepare the message with required fields
            full_message = {
                "type": message_type,
                "session_id": session_id,
                **message
            }
            
            # Send to appropriate Redis queue
            queue_name = f"queue_{message_type}"
            self.redis_client.lpush(queue_name, json.dumps(full_message))
            logger.info(f"Message sent to session {session_id} via {queue_name}")
            
        except Exception as e:
            logger.error(f"Error sending message to Gateway: {str(e)}")
            raise
    
    def send_final_result(self, session_id: str, result: Dict[str, Any]) -> None:
        """
        Send a final result message to a specific session
        
        Args:
            session_id: The target session ID
            result: The final result content
        """
        self.send_message(session_id, result, message_type="agent_judgement_final")
    
    def broadcast(self, message: Dict[str, Any], message_type: str = "broadcast") -> None:
        """
        Broadcast a message to all connected sessions
        
        Args:
            message: The message content to broadcast
            message_type: Type of message (default: broadcast)
        """
        try:
            # Prepare the message with required fields
            full_message = {
                "type": message_type,
                **message
            }
            
            # Send to broadcast queue
            queue_name = "queue_broadcast"
            self.redis_client.lpush(queue_name, json.dumps(full_message))
            logger.info(f"Message broadcasted via {queue_name}")
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {str(e)}")
            raise
    
    def disconnect_all(self) -> None:
        """
        Request to disconnect all active WebSocket connections
        """
        try:
            message = {
                "type": "disconnect_all"
            }
            
            # Send to control queue
            queue_name = "queue_control"
            self.redis_client.lpush(queue_name, json.dumps(message))
            logger.info("Disconnect all request sent")
            
        except Exception as e:
            logger.error(f"Error sending disconnect all request: {str(e)}")
            raise
    
    def close(self) -> None:
        """Close the Redis connection"""
        self.redis_client.close()
