"""
Configuration management using Pydantic Settings
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_password: Optional[str] = None
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    
    # Recommendation Settings
    embedding_dimension: int = 128
    max_recommendations: int = 50
    cache_ttl_seconds: int = 3600
    
    # Data Configuration
    data_file_path: str = "data/new_orders.csv"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
