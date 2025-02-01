"""
Agent task implementation for processing user requests.
"""
from typing import Dict, Any
from celery import shared_task, current_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from apps.agents.models import Agent, AgentRun
from utils.redis_channels import RedisChannels
from utils.redis_client import redis_client

logger = get_task_logger(__name__)

@shared_task(name="tasks.process_agent_task")
def process_agent_task(session_id: str, request_data: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
    """
    Process a user request using a specific agent.
    
    Args:
        session_id: The unique session identifier
        request_data: The request data to be processed
        agent_id: The UUID of the agent to use
        
    Returns:
        Dict[str, Any]: The processing result
    """
    try:
        # Get the agent
        agent = Agent.objects.get(id=agent_id)
        
        # Create agent run record
        agent_run = AgentRun.objects.create(
            agent=agent,
            session_id=session_id,
            request_data=request_data
        )
        
        logger.info(f"Processing agent task for session {session_id} with agent {agent.name}")
        
        # Format the prompt using agent's template
        formatted_prompt = agent.format_prompt(request_data.get('user_request', ''))
        
        # Get LLM parameters
        llm_params = agent.get_llm_parameters()
        
        # Call LLM provider
        llm_model = agent.llm_model
        llm_provider = llm_model.provider
        
        # TODO: Implement actual LLM provider call
        intermediate_result = {
            'raw_response': f"Processing request with {llm_provider.name}",
            'tokens': 100,
            'processing_time': 1.5
        }
        
        # Stream intermediate result
        redis_client.xadd(
            RedisChannels.agent_task_stream(session_id),
            {
                'status': 'progress',
                'agent_id': str(agent.id),
                'agent_name': agent.name,
                'data': intermediate_result
            },
            maxlen=1000
        )
        
        # Process the intermediate result
        final_result = {
            'agent_id': str(agent.id),
            'agent_name': agent.name,
            'vote': process_intermediate_result(intermediate_result),
            'confidence': calculate_confidence(intermediate_result),
            'weight': agent.weight
        }
        
        # Update agent run record
        agent_run.response_data = final_result
        agent_run.completed_at = timezone.now()
        agent_run.save()
        
        logger.info(f"Agent {agent.name} completed processing for session {session_id}")
        return final_result
        
    except Agent.DoesNotExist:
        error_msg = f"Agent {agent_id} not found"
        logger.error(error_msg)
        redis_client.xadd(
            RedisChannels.agent_task_stream(session_id),
            {
                'status': 'error',
                'agent_id': agent_id,
                'error': error_msg
            },
            maxlen=1000
        )
        raise
        
    except Exception as e:
        error_msg = f"Error in agent task: {str(e)}"
        logger.error(error_msg)
        
        if 'agent_run' in locals():
            agent_run.error = error_msg
            agent_run.completed_at = timezone.now()
            agent_run.save()
            
        redis_client.xadd(
            RedisChannels.agent_task_stream(session_id),
            {
                'status': 'error',
                'agent_id': agent_id,
                'error': error_msg
            },
            maxlen=1000
        )
        raise

def process_intermediate_result(result: Dict[str, Any]) -> str:
    """
    Process the intermediate result to generate a final vote.
    Implement your own processing logic here.
    
    Args:
        result: The intermediate result from LLM provider
        
    Returns:
        str: The final vote
    """
    # TODO: Implement your result processing logic
    return "approved"  # placeholder

def calculate_confidence(result: Dict[str, Any]) -> float:
    """
    Calculate confidence score for the result.
    Implement your own confidence calculation logic here.
    
    Args:
        result: The intermediate result from LLM provider
        
    Returns:
        float: Confidence score between 0 and 1
    """
    # TODO: Implement your confidence calculation logic
    return 0.85  # placeholder
