import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import json
import time
import asyncio
import hashlib
from main import app
from config import settings
from utils.auth import verify_appid_token, generate_session_id
from httpx import AsyncClient

def generate_test_token(appid: str) -> str:
    """Generate a valid token for testing"""
    current_minute = int(time.time() // 60)
    raw_str = f"{appid}{settings.FIXED_SECRET}{current_minute}"
    return hashlib.sha256(raw_str.encode()).hexdigest()[:10]

@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)

@pytest.fixture
def valid_appid():
    return "test_app_123"

@pytest.fixture
def valid_token(valid_appid):
    return generate_test_token(valid_appid)

@pytest.mark.asyncio
async def test_websocket_connection_success(client, valid_appid, valid_token):
    """Test successful WebSocket connection with valid credentials"""
    with client.websocket_connect(
        f"/ws?appid={valid_appid}&token={valid_token}"
    ) as websocket:
        data = websocket.receive_json()
        assert "session_id" in data
        
        # Send ping
        websocket.send_json({"type": "ping"})
        
        # Wait for pong
        response = websocket.receive_json()
        assert response.get("type") == "pong"

@pytest.mark.asyncio
async def test_websocket_connection_invalid_token(client, valid_appid):
    """Test WebSocket connection with invalid token"""
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/ws?appid={valid_appid}&token=invalid_token",
            timeout=5.0
        ) as websocket:
            websocket._timeout = 5.0
            websocket.receive_json()

@pytest.mark.asyncio
async def test_websocket_send_agent_judgement(client, valid_appid, valid_token):
    """Test sending agent judgement message"""
    with client.websocket_connect(
        f"/ws?appid={valid_appid}&token={valid_token}",
        timeout=5.0
    ) as websocket:
        websocket._timeout = 5.0
        # Wait for connection confirmation message
        data = websocket.receive_json()
        assert "session_id" in data
        
        # Send message
        message = {
            "type": "agent_judgement",
            "agent_ids": ["agent1", "agent2"],
            "data": {"user_input": "test input"}
        }
        websocket.send_json(message)
        
        # Wait for response
        response = websocket.receive_json()
        assert "error" not in response
        
        # Actively close connection
        websocket.close()

@pytest.mark.asyncio
async def test_websocket_invalid_message_type(client, valid_appid, valid_token):
    """Test sending message with invalid type"""
    with client.websocket_connect(
        f"/ws?appid={valid_appid}&token={valid_token}"
    ) as websocket:
        # Wait for connection confirmation message
        data = websocket.receive_json()
        assert "session_id" in data
        
        # Send invalid message type
        message = {
            "type": "invalid_type",
            "data": {"test": "data"}
        }
        websocket.send_json(message)
        
        # Wait for error response
        response = websocket.receive_json()
        assert "error" in response
        assert "Unsupported message type" in response["error"]
        
        # Actively close connection
        websocket.close()

@pytest.mark.asyncio
async def test_websocket_invalid_json(client, valid_appid, valid_token):
    """Test sending invalid JSON"""
    with client.websocket_connect(
        f"/ws?appid={valid_appid}&token={valid_token}"
    ) as websocket:
        # Wait for connection confirmation message
        data = websocket.receive_json()
        assert "session_id" in data
        
        # Send invalid JSON
        websocket.send_text("invalid json")
        
        # Wait for error response
        response = websocket.receive_json()
        assert "error" in response
        assert "Invalid JSON format" in response["error"]
        
        # Actively close connection
        websocket.close()

@pytest.mark.asyncio
async def test_websocket_endpoint(client, valid_appid, valid_token):
    """Test basic WebSocket endpoint functionality"""
    with client.websocket_connect(
        f"/ws?appid={valid_appid}&token={valid_token}"
    ) as websocket:
        # Wait for connection confirmation
        data = websocket.receive_json()
        assert "session_id" in data
        
        # Send test message
        websocket.send_json({"type": "test", "message": "hello"})
        
        # Wait for response
        response = websocket.receive_json()
        assert response.get("type") == "test_response" 