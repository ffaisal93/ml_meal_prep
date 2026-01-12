"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    openai_api_key: str
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cache_ttl_seconds: int = 3600
    rate_limit_enabled: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

