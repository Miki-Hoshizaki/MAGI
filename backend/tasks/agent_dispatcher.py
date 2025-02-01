from celery import shared_task
from typing import Dict, List
import json
import redis
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@shared_task(name='tasks.process_request')
def process_request(session_id: str, message: Dict):
    """
    Main task that processes incoming requests from Gateway
    and dispatches them to agent workers
    """
    try:
        logger.info(f"Processing request for session {session_id}")
        
        # Extract agent IDs from message
        agent_ids = message.get('agent_ids', [])
        if not agent_ids:
            raise ValueError("No agent IDs provided in message")

        # Create subtasks for each agent
        for agent_id in agent_ids:
            # Queue agent-specific task
            agent_task.delay(
                session_id=session_id,
                agent_id=agent_id,
                message=message
            )
        
        return {
            "status": "success",
            "message": f"Dispatched to {len(agent_ids)} agents",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error processing request for session {session_id}: {str(e)}")
        # Publish error message back to Gateway
        error_message = {
            "type": "error",
            "session_id": session_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        redis_client.publish(f"backend:responses:{session_id}", json.dumps(error_message))
        raise

@shared_task(name='tasks.agent_task')
def agent_task(session_id: str, agent_id: str, message: Dict):
    """
    Individual agent task that processes the request and publishes results
    """
    try:
        logger.info(f"Agent {agent_id} processing request for session {session_id}")
        
        # TODO: Implement actual agent logic here
        # This is a placeholder that simulates agent processing
        result = {
            "type": "agent_judgement_stream",
            "session_id": session_id,
            "agent_id": agent_id,
            "content": f"Processing by agent {agent_id}",
            "is_final": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish intermediate result
        redis_client.publish(f"backend:responses:{session_id}", json.dumps(result))
        
        # Simulate final result
        final_result = {
            "type": "agent_judgement_final",
            "session_id": session_id,
            "agent_id": agent_id,
            "content": f"Final result from agent {agent_id}",
            "is_final": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish final result
        redis_client.publish(f"backend:responses:{session_id}", json.dumps(final_result))
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in agent {agent_id} for session {session_id}: {str(e)}")
        error_message = {
            "type": "error",
            "session_id": session_id,
            "agent_id": agent_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        redis_client.publish(f"backend:responses:{session_id}", json.dumps(error_message))
        raise 