"""
Task dispatcher for handling gateway requests and distributing them to agents.
"""
from typing import List, Dict, Any
from celery import shared_task, chord
from celery.utils.log import get_task_logger
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
        
        # Create agent tasks (default to 3 agents)
        header = [
            process_agent_task.s(session_id, request_data)
            for _ in range(3)
        ]
        
        # Create callback task to collect results
        callback = collect_results.s(session_id)
        
        # Execute the chord
        chord(header)(callback)
        
        logger.info(f"Successfully dispatched request for session {session_id}")
        
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
        
        # Aggregate results (implement your aggregation logic here)
        final_result = {
            'agent_results': agent_results,
            'aggregated_result': aggregate_results(agent_results)
        }
        
        # Publish final result to result stream
        redis_client.xadd(
            RedisChannels.result_stream(session_id),
            {
                'status': 'completed',
                'data': final_result
            },
            maxlen=1000
        )
        
        logger.info(f"Successfully published results for session {session_id}")
        
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

def aggregate_results(agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate results from multiple agents into a final result.
    Implement your own aggregation logic here.
    
    Args:
        agent_results: List of results from individual agents
        
    Returns:
        Dict[str, Any]: The aggregated result
    """
    # TODO: Implement your result aggregation logic
    # This is a simple example that just returns the majority vote
    return {
        'majority_vote': max(
            (result.get('vote') for result in agent_results),
            key=lambda x: sum(1 for r in agent_results if r.get('vote') == x)
        )
    }
