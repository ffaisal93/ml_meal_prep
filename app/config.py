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
    port: Optional[int] = None  # Railway uses PORT (uppercase)
    cache_ttl_seconds: int = 3600
    rate_limit_enabled: bool = False
    
    @property
    def effective_port(self) -> int:
        """Get the effective port (Railway's PORT or api_port)"""
        return self.port or self.api_port
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

