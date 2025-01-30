import pytest
import json
import asyncio
from unittest.mock import MagicMock, patch
from ..redis_handlers.producer import send_to_redis
from ..redis_handlers.consumer import RedisConsumer
from ..websocket_manager import ConnectionManager

@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    async def mock_connect(*args, **kwargs):
        return MagicMock()
    return mock_connect

@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket connection manager"""
    manager = ConnectionManager()
    manager.send_message = MagicMock()
    return manager

@pytest.mark.asyncio
async def test_send_to_redis(mock_redis):
    """Test sending message to Redis"""
    with patch('aioredis.from_url', mock_redis):
        message = {
            "type": "agent_judgement",
            "session_id": "test-session",
            "agent_ids": ["agent1"],
            "data": {"test": "data"}
        }
        
        # Mock Redis connection
        redis_mock = await mock_redis()
        redis_mock.lpush = MagicMock()
        
        # Test sending message
        await send_to_redis(message)
        
        # Verify Redis lpush was called with correct arguments
        redis_mock.lpush.assert_called_once_with(
            "queue_agent_judgement",
            json.dumps(message)
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
    
    # Test processing message
    await consumer.process_message(message)
    
    # Verify message was forwarded to WebSocket
    mock_websocket_manager.send_message.assert_called_once_with(
        "test-session",
        message
    )

@pytest.mark.asyncio
async def test_redis_consumer_invalid_message(mock_websocket_manager):
    """Test Redis consumer handling invalid message"""
    consumer = RedisConsumer(mock_websocket_manager)
    
    # Message without session_id
    message = {
        "type": "agent_judgement_stream",
        "data": {"thinking": "step 1"}
    }
    
    # Test processing invalid message
    await consumer.process_message(message)
    
    # Verify no message was forwarded
    mock_websocket_manager.send_message.assert_not_called()

@pytest.mark.asyncio
async def test_redis_consumer_start_consuming(mock_redis, mock_websocket_manager):
    """Test Redis consumer main loop"""
    consumer = RedisConsumer(mock_websocket_manager)
    
    # Mock Redis connection and blpop response
    redis_mock = await mock_redis()
    redis_mock.blpop = MagicMock()
    redis_mock.blpop.return_value = (
        "queue_agent_judgement_stream",
        json.dumps({
            "session_id": "test-session",
            "type": "agent_judgement_stream",
            "data": {"thinking": "step 1"}
        })
    )
    
    with patch('aioredis.from_url', mock_redis):
        # Start consumer and let it process one message
        consumer_task = asyncio.create_task(consumer.start_consuming())
        await asyncio.sleep(0.1)  # Give it time to process
        consumer.stop()  # Stop the consumer
        await consumer_task  # Wait for it to finish
        
        # Verify Redis blpop was called
        redis_mock.blpop.assert_called_with(
            "queue_agent_judgement_stream",
            "queue_agent_judgement_final",
            timeout=5
        ) 