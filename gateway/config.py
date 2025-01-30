from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Magi Gateway"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS settings
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", "")
    REDIS_URL: Optional[str] = None  # Allow direct setting of REDIS_URL
    
    def get_redis_url(self) -> str:
        """Get Redis URL, either from REDIS_URL or construct from components"""
        if self.REDIS_URL:
            return self.REDIS_URL
            
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Authentication settings
    FIXED_SECRET: str = os.getenv("FIXED_SECRET", "your-fixed-secret-key")  # Change in production!
    
    # JWT Configurations
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Backend service configurations
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://backend:8000")

    class Config:
        env_file = ".env.test" if os.getenv("TESTING") else ".env"
        case_sensitive = True

settings = Settings()
