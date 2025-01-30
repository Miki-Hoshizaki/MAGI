import pytest
from fastapi.testclient import TestClient
from fastapi import WebSocket
from unittest.mock import AsyncMock, patch, MagicMock
from websocket_manager import ConnectionManager
import json

class MockWebSocket:
    def __init__(self):
        self.accept = AsyncMock()
        self.close = AsyncMock()
        self.send_json = AsyncMock()
        self.receive_json = AsyncMock()

@pytest.fixture
async def connection_manager():
    manager = ConnectionManager()
    # Mock redis client
    manager.redis_client = MagicMock()
    return manager

@pytest.mark.asyncio
async def test_disconnect_all(connection_manager):
    # Setup test data
    mock_ws1 = MockWebSocket()
    mock_ws2 = MockWebSocket()
    
    # Connect two mock websockets
    await connection_manager.connect("session1", mock_ws1)
    await connection_manager.connect("session2", mock_ws2)
    
    # Verify connections are stored
    assert len(connection_manager.active_connections) == 2
    
    # Call disconnect_all
    await connection_manager.disconnect_all()
    
    # Verify all connections are closed
    assert len(connection_manager.active_connections) == 0
    mock_ws1.close.assert_called_once()
    mock_ws2.close.assert_called_once()

@pytest.mark.asyncio
async def test_broadcast(connection_manager):
    # Setup test data
    mock_ws1 = MockWebSocket()
    mock_ws2 = MockWebSocket()
    test_message = {
        "type": "agent_judgement",
        "agent_ids": ["agent1", "agent2"],
        "content": "Test broadcast message"
    }
    
    # Connect two mock websockets
    await connection_manager.connect("session1", mock_ws1)
    await connection_manager.connect("session2", mock_ws2)
    
    # Broadcast message
    await connection_manager.broadcast(test_message)
    
    # Verify message was sent to all connections
    mock_ws1.send_json.assert_called_once_with(test_message)
    mock_ws2.send_json.assert_called_once_with(test_message)

@pytest.mark.asyncio
async def test_broadcast_with_disconnected_client(connection_manager):
    # Setup test data
    mock_ws1 = MockWebSocket()
    mock_ws2 = MockWebSocket()
    test_message = {
        "type": "agent_judgement",
        "agent_ids": ["agent1"],
        "content": "Test broadcast with disconnection"
    }
    
    # Make one client raise an exception when sending
    mock_ws2.send_json.side_effect = Exception("Connection lost")
    
    # Connect two mock websockets
    await connection_manager.connect("session1", mock_ws1)
    await connection_manager.connect("session2", mock_ws2)
    
    # Broadcast message
    await connection_manager.broadcast(test_message)
    
    # Verify message was sent to the working connection
    mock_ws1.send_json.assert_called_once_with(test_message)
    # Verify the failed connection was removed
    assert len(connection_manager.active_connections) == 1
    assert "session2" not in connection_manager.active_connections
