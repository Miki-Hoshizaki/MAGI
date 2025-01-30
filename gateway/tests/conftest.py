import pytest
import os

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