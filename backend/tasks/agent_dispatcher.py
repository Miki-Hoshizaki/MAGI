from celery import shared_task
from typing import Dict, List
import json
import redis
import logging
from datetime import datetime
from collections import defaultdict

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
        
        # Extract request data
        request_id = message.get('request_id')
        agents_data = message.get('agents', [])
        if not agents_data:
            raise ValueError("No agents provided in message")

        # Create subtasks for each agent
        for agent_data in agents_data:
            agent_id = agent_data.get('agent_id')
            if not agent_id:
                continue
                
            # Queue agent-specific task
            agent_task.delay(
                session_id=session_id,
                request_id=request_id,
                agent_id=agent_id,
                agent_data=agent_data,
                message=message
            )
        
        return {
            "status": "success",
            "message": f"Dispatched to {len(agents_data)} agents",
            "session_id": session_id,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error processing request for session {session_id}: {str(e)}")
        # Publish error message back to Gateway
        error_message = {
            "type": "agent_judgement_response",
            "session_id": session_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        redis_client.publish(f"gateway:responses:{session_id}", json.dumps(error_message))
        raise

@shared_task(name='tasks.agent_task')
def agent_task(session_id: str, request_id: str, agent_id: str, agent_data: Dict, message: Dict):
    """
    Individual agent task that processes the request using LLM and publishes results
    
    Args:
        session_id: Session identifier
        request_id: Request identifier
        agent_id: Agent identifier
        agent_data: Agent configuration data
        message: Original request message
    """
    try:
        logger.info(f"Agent {agent_id} processing request for session {session_id}")
        
        # Get agent from database
        from apps.agents.models import Agent
        try:
            agent = Agent.objects.get(id=agent_id)
        except Agent.DoesNotExist:
            raise ValueError(f"Agent {agent_id} not found in database")
        
        # Get user request from message
        user_request = message.get('request', '')
        logger.info(f"message: {message}")
        if not user_request:
            raise ValueError("No user request provided in message")
            
        # Prepare prompts
        system_prompt = agent.system_prompt
        user_prompt = agent.user_prompt_template.format_map(defaultdict(str, {"user_request": user_request}))
        
        # Initialize LLM client based on agent's model and provider
        llm_model = agent.llm_model
        provider = llm_model.provider
        
        if provider.provider_type == 'openai':
            from llm.providers.openai_provider import OpenAIProvider
            llm_client = OpenAIProvider(
                api_key=provider.api_key,
                model=llm_model.model_name,
                base_url=provider.base_url,
                **agent.get_llm_parameters()
            )
        elif provider.provider_type == 'anthropic':
            from llm.providers.anthropic_provider import AnthropicProvider
            llm_client = AnthropicProvider(
                api_key=provider.api_key,
                model=llm_model.model_name,
                base_url=provider.base_url,
                **agent.get_llm_parameters()
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider.provider_type}")
        
        # Stream intermediate status
        intermediate_result = {
            "type": "agent_response",
            "session_id": session_id,
            "status": "processing",
            "request_id": request_id,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        redis_client.publish(f"gateway:responses:{session_id}", json.dumps(intermediate_result))
        
        # Stream LLM response
        llm_params = agent.get_llm_parameters()
        
        # Create event loop for async operations
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run stream_chat in the event loop
            async def process_stream():
                async for chunk in llm_client.stream_chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    **llm_params
                ):
                    response = {
                        "type": "agent_response",
                        "session_id": session_id,
                        "status": "streaming",
                        "request_id": request_id,
                        "agent_id": agent_id,
                        "content": chunk,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    redis_client.publish(f"gateway:responses:{session_id}", json.dumps(response))
                    
            loop.run_until_complete(process_stream())
        finally:
            loop.close()
        
        # Send completion message
        final_result = {
            "type": "agent_response",
            "session_id": session_id,
            "status": "completed",
            "request_id": request_id,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        redis_client.publish(f"gateway:responses:{session_id}", json.dumps(final_result))
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "session_id": session_id,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in agent {agent_id} for session {session_id}: {str(e)}")
        error_message = {
            "type": "agent_response",
            "session_id": session_id,
            "status": "error",
            "request_id": request_id,
            "agent_id": agent_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        redis_client.publish(f"gateway:responses:{session_id}", json.dumps(error_message))
        raise