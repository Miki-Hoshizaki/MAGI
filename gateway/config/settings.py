"""
Gateway configuration settings.
"""
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Gateway settings."""
    
    # Application settings
    APP_NAME: str = "MAGI Gateway"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
    ]
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security settings
    FIXED_SECRET: str = "magi-gateway-development-secret"
    
    class Config:
        env_prefix = "MAGI_GATEWAY_"
        case_sensitive = True

# Create settings instance
settings = Settings()
