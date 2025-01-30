import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import json
import time
import hashlib
from ..main import app
from ..config import settings
from ..utils.auth import verify_appid_token, generate_session_id

def generate_test_token(appid: str) -> str:
    """Generate a valid token for testing"""
    current_minute = int(time.time() // 60)
    raw_str = f"{appid}{settings.FIXED_SECRET}{current_minute}"
    return hashlib.sha256(raw_str.encode()).hexdigest()[:10]

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def valid_appid():
    return "test_app_123"

@pytest.fixture
def valid_token(valid_appid):
    return generate_test_token(valid_appid)

def test_websocket_connection_success(test_client, valid_appid, valid_token):
    """Test successful WebSocket connection with valid credentials"""
    with test_client.websocket_connect(
        f"/ws?appid={valid_appid}&token={valid_token}"
    ) as websocket:
        # Connection should be established
        assert websocket.can_receive

def test_websocket_connection_invalid_token(test_client, valid_appid):
    """Test WebSocket connection with invalid token"""
    with pytest.raises(Exception):
        with test_client.websocket_connect(
            f"/ws?appid={valid_appid}&token=invalid_token"
        ):
            pass

def test_websocket_send_agent_judgement(test_client, valid_appid, valid_token):
    """Test sending agent judgement message"""
    with test_client.websocket_connect(
        f"/ws?appid={valid_appid}&token={valid_token}"
    ) as websocket:
        message = {
            "type": "agent_judgement",
            "agent_ids": ["agent1", "agent2"],
            "data": {"user_input": "test input"}
        }
        websocket.send_json(message)
        # Should not receive error response
        response = websocket.receive_json()
        assert "error" not in response

def test_websocket_invalid_message_type(test_client, valid_appid, valid_token):
    """Test sending message with invalid type"""
    with test_client.websocket_connect(
        f"/ws?appid={valid_appid}&token={valid_token}"
    ) as websocket:
        message = {
            "type": "invalid_type",
            "data": {"test": "data"}
        }
        websocket.send_json(message)
        response = websocket.receive_json()
        assert "error" in response
        assert "Unsupported message type" in response["error"]

def test_websocket_invalid_json(test_client, valid_appid, valid_token):
    """Test sending invalid JSON"""
    with test_client.websocket_connect(
        f"/ws?appid={valid_appid}&token={valid_token}"
    ) as websocket:
        websocket.send_text("invalid json")
        response = websocket.receive_json()
        assert "error" in response
        assert "Invalid JSON format" in response["error"] 