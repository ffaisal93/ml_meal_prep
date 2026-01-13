"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    openai_api_key: str
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    port: Optional[int] = None  # Railway uses PORT (uppercase)
    cache_ttl_seconds: int = 3600
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 10  # Requests per minute per IP
    rate_limit_system_max_rps: int = 50  # System-wide max requests per second
    
    # Database configuration
    # Railway automatically provides DATABASE_URL for PostgreSQL services
    # For SQLite, use PERSISTENT_VOLUME_PATH (Railway feature)
    database_url: Optional[str] = Field(None, env="DATABASE_URL")  # Railway provides this automatically
    persistent_volume_path: Optional[str] = Field(None, env="PERSISTENT_VOLUME_PATH")
    db_path: str = "meal_planner.db"  # Default SQLite path
    
    @property
    def effective_port(self) -> int:
        """Get the effective port (Railway's PORT or api_port)"""
        return self.port or self.api_port
    
    @property
    def effective_db_path(self) -> str:
        """Get the effective database path (persistent volume or default)"""
        if self.persistent_volume_path:
            import os
            return os.path.join(self.persistent_volume_path, self.db_path)
        return self.db_path
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

