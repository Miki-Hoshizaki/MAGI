"""
Task dispatcher for handling gateway requests and distributing them to agents.
"""
from typing import List, Dict, Any
from celery import shared_task, chord
from celery.utils.log import get_task_logger
from django.conf import settings
from apps.agents.models import Agent
from utils.redis_channels import RedisChannels
from utils.redis_client import redis_client
from .agent_tasks import process_agent_task

logger = get_task_logger(__name__)

@shared_task(name="tasks.dispatch_gateway_request", queue="gateway_requests")
def dispatch_gateway_request(session_id: str, request_data: Dict[str, Any]) -> None:
    """
    Dispatch a gateway request to multiple agents for processing.
    
    Args:
        session_id: The unique session identifier
        request_data: The request data to be processed
    """
    try:
        logger.info(f"Dispatching gateway request for session {session_id}")
        
        # Get active agents
        agents = Agent.objects.filter(is_active=True)
        if not agents.exists():
            raise ValueError("No active agents available")
        
        # Create agent tasks
        header = [
            process_agent_task.s(session_id, request_data, str(agent.id))
            for agent in agents
        ]
        
        # Create callback task to collect results
        callback = collect_results.s(session_id)
        
        # Execute the chord
        chord(header)(callback)
        
        logger.info(f"Successfully dispatched request to {len(agents)} agents for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error dispatching gateway request: {str(e)}")
        # Publish error to result stream
        redis_client.xadd(
            RedisChannels.result_stream(session_id),
            {
                'status': 'error',
                'error': str(e)
            },
            maxlen=1000
        )
        raise

@shared_task(name="tasks.collect_results")
def collect_results(agent_results: List[Dict[str, Any]], session_id: str) -> None:
    """
    Collect and aggregate results from multiple agents.
    
    Args:
        agent_results: List of results from individual agents
        session_id: The unique session identifier
    """
    try:
        logger.info(f"Collecting results for session {session_id}")
        
        # Calculate weighted votes
        votes = {}
        for result in agent_results:
            vote = result.get('vote')
            weight = result.get('weight', 1.0)
            confidence = result.get('confidence', 1.0)
            
            if vote not in votes:
                votes[vote] = 0
            votes[vote] += weight * confidence
        
        # Find the winning vote
        winning_vote = max(votes.items(), key=lambda x: x[1])[0]
        
        # Prepare final result
        final_result = {
            'status': 'completed',
            'agent_results': agent_results,
            'aggregated_result': {
                'winning_vote': winning_vote,
                'vote_distribution': votes
            }
        }
        
        # Publish final result to result stream
        redis_client.xadd(
            RedisChannels.result_stream(session_id),
            final_result,
            maxlen=1000
        )
        
        logger.info(f"Successfully published aggregated results for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error collecting results: {str(e)}")
        redis_client.xadd(
            RedisChannels.result_stream(session_id),
            {
                'status': 'error',
                'error': str(e)
            },
            maxlen=1000
        )
        raise
