import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock
from redis_handlers.producer import send_to_redis
from redis_handlers.consumer import RedisConsumer
from websocket_manager import ConnectionManager

@pytest.fixture
def mock_redis(mocker):
    """Mock Redis client"""
    mock_client = mocker.AsyncMock()
    
    # Use AsyncMock directly instead of custom coroutine function
    mock_client.blpop = mocker.AsyncMock(return_value=(
        "queue_agent_judgement_stream",
        json.dumps({
            "session_id": "test-session",
            "type": "agent_judgement_stream",
            "data": {"thinking": "step 1"}
        }).encode()
    ))
    
    # Ensure other methods are also AsyncMock
    mock_client.lpush = mocker.AsyncMock()
    mock_client.close = mocker.AsyncMock()
    
    # Use return_value instead of side_effect
    mocker.patch('redis.asyncio.from_url', return_value=mock_client)
    return mock_client

@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket connection manager"""
    manager = ConnectionManager()
    manager.send_message = AsyncMock()  # Switch to AsyncMock
    return manager

@pytest.mark.asyncio
async def test_send_to_redis(mock_redis):
    """Test sending message to Redis"""
    test_message = {
        "type": "test",
        "data": "test_data"
    }
    
    await send_to_redis(test_message)
    
    mock_redis.lpush.assert_awaited_once_with(
        "queue_test",
        json.dumps(test_message)
    )

@pytest.mark.asyncio
async def test_redis_consumer_process_message(mock_websocket_manager):
    """Test Redis consumer message processing"""
    consumer = RedisConsumer(mock_websocket_manager)
    
    message = {
        "session_id": "test-session",
        "type": "agent_judgement_stream",
        "data": {"thinking": "step 1"}
    }
    
    await consumer.process_message(message)
    mock_websocket_manager.send_message.assert_called_once_with(
        "test-session",
        message
    )

@pytest.mark.asyncio
async def test_redis_consumer_invalid_message(mock_websocket_manager):
    """Test Redis consumer handling invalid message"""
    consumer = RedisConsumer(mock_websocket_manager)
    message = {
        "type": "agent_judgement_stream",
        "data": {"thinking": "step 1"}
    }
    await consumer.process_message(message)
    mock_websocket_manager.send_message.assert_not_called()

@pytest.mark.asyncio
async def test_redis_consumer_start_consuming(mock_redis, mock_websocket_manager):
    """Test Redis consumer main loop"""
    consumer = RedisConsumer(mock_websocket_manager)
    
    
    async def run_consumer():
        # Create task
        consumer_task = asyncio.create_task(consumer.consume_messages())
        
        # Wait a short time to let consumer start
        await asyncio.sleep(0.2)
        
        # Stop consumer
        consumer.stop()
        
        # Wait for task completion
        try:
            await asyncio.wait_for(consumer_task, timeout=0.5)
            print("Consumer task completed")
        except asyncio.TimeoutError:
            print("Consumer task timeout")
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                print("Consumer task cancelled")
    
    await asyncio.wait_for(run_consumer(), timeout=2.0)
    
    # Verify blpop was called with all expected queues
    mock_redis.blpop.assert_awaited_with(
        [
            "queue_agent_judgement_stream",
            "queue_agent_judgement_final",
            "queue_broadcast",
            "queue_control",
        ],
        timeout=1
    )