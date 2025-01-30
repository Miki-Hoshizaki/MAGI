import sys
import os
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def mock_redis(mocker):
    """Mock Redis client for testing"""
    mock_redis = mocker.MagicMock()
    mocker.patch('redis.asyncio.from_url', return_value=mock_redis)
    return mock_redis

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["FIXED_SECRET"] = "test_secret_key"
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"
    os.environ["REDIS_DB"] = "0"
    os.environ["DEBUG"] = "true"
    yield
    # Clean up is handled by pytest 