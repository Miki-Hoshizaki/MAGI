import pytest
import time
import hashlib
from utils.auth import verify_appid_token, generate_session_id
from config import settings

def test_verify_appid_token_valid():
    """Test token verification with valid credentials"""
    appid = "test_app"
    current_minute = int(time.time() // 60)
    raw_str = f"{appid}{settings.FIXED_SECRET}{current_minute}"
    token = hashlib.sha256(raw_str.encode()).hexdigest()[:10]
    
    assert verify_appid_token(appid, token) is True

def test_verify_appid_token_invalid():
    """Test token verification with invalid token"""
    appid = "test_app"
    token = "invalid_token"
    
    assert verify_appid_token(appid, token) is False

def test_verify_appid_token_empty():
    """Test token verification with empty credentials"""
    assert verify_appid_token("", "") is False
    assert verify_appid_token("test_app", "") is False
    assert verify_appid_token("", "token") is False

def test_verify_appid_token_time_drift():
    """Test token verification with previous minute"""
    appid = "test_app"
    previous_minute = int(time.time() // 60) - 1
    raw_str = f"{appid}{settings.FIXED_SECRET}{previous_minute}"
    token = hashlib.sha256(raw_str.encode()).hexdigest()[:10]
    
    assert verify_appid_token(appid, token) is True

def test_generate_session_id():
    """Test session ID generation"""
    appid = "test_app"
    session_id = generate_session_id(appid)
    assert isinstance(session_id, str)
    assert len(session_id) > 0

@pytest.mark.asyncio
async def test_verify_appid_token():
    """Test async token verification"""
    appid = "test_app"
    current_minute = int(time.time() // 60)
    raw_str = f"{appid}{settings.FIXED_SECRET}{current_minute}"
    token = hashlib.sha256(raw_str.encode()).hexdigest()[:10]
    
    result = verify_appid_token(appid, token)
    assert result is True 