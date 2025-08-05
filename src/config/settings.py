#!/usr/bin/env python3
"""
config/settings.py - Application configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    # Service endpoints
    focus_time_service_url: str = Field("http://localhost:8001", env="FOCUS_TIME_SERVICE_URL")
    focus_score_service_url: str = Field("http://localhost:8002", env="FOCUS_SCORE_SERVICE_URL")
    
    # OpenAI configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o-mini", env="OPENAI_MODEL") 
    
    # Performance settings
    http_timeout: int = Field(30, env="HTTP_TIMEOUT")
    max_concurrent_requests: int = Field(10, env="MAX_CONCURRENT_REQUESTS")
    cache_ttl_seconds: int = Field(60, env="CACHE_TTL_SECONDS")
    
    # Retry configuration
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay: float = Field(1.0, env="RETRY_DELAY")
    
    # File processing
    max_file_size_mb: int = Field(10, env="MAX_FILE_SIZE_MB")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


# Global settings instance
settings = Settings()
