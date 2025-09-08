#!/usr/bin/env python3
"""
Configuration for RAG Memory Services
Provides environment-aware configuration with sensible defaults
"""

from pydantic import BaseSettings, Field
from typing import Optional
import os

class MemoryConfig(BaseSettings):
    """Memory service configuration with environment variable support"""
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", env="MEMORY_REDIS_HOST")
    redis_port: int = Field(default=6379, env="MEMORY_REDIS_PORT")
    redis_db: int = Field(default=0, env="MEMORY_REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="MEMORY_REDIS_PASSWORD")
    redis_timeout: int = Field(default=5, env="MEMORY_REDIS_TIMEOUT")
    redis_ttl: int = Field(default=86400, env="MEMORY_REDIS_TTL")  # 24 hours
    
    # Weaviate Configuration
    weaviate_url: str = Field(default="http://localhost:8080", env="MEMORY_WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(default=None, env="MEMORY_WEAVIATE_API_KEY")
    weaviate_timeout: int = Field(default=10, env="MEMORY_WEAVIATE_TIMEOUT")
    
    # Service Configuration
    enable_redis: bool = Field(default=True, env="MEMORY_ENABLE_REDIS")
    enable_weaviate: bool = Field(default=True, env="MEMORY_ENABLE_WEAVIATE")
    enable_persistence: bool = Field(default=True, env="MEMORY_ENABLE_PERSISTENCE")
    
    # Memory Limits
    max_memory_entries: int = Field(default=10000, env="MEMORY_MAX_ENTRIES")
    max_entry_size: int = Field(default=100000, env="MEMORY_MAX_ENTRY_SIZE")  # 100KB
    cache_ttl: int = Field(default=3600, env="MEMORY_CACHE_TTL")  # 1 hour
    
    # Search Configuration
    default_search_limit: int = Field(default=10, env="MEMORY_DEFAULT_SEARCH_LIMIT")
    max_search_limit: int = Field(default=100, env="MEMORY_MAX_SEARCH_LIMIT")
    search_timeout: int = Field(default=30, env="MEMORY_SEARCH_TIMEOUT")
    
    # Security Configuration
    enable_auth: bool = Field(default=False, env="MEMORY_ENABLE_AUTH")
    api_key: Optional[str] = Field(default=None, env="MEMORY_API_KEY")
    rate_limit_enabled: bool = Field(default=True, env="MEMORY_RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="MEMORY_RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="MEMORY_RATE_LIMIT_PERIOD")  # seconds
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="MEMORY_LOG_LEVEL")
    log_format: str = Field(default="json", env="MEMORY_LOG_FORMAT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def validate_config(self) -> bool:
        """Validate configuration settings"""
        if self.max_search_limit < self.default_search_limit:
            raise ValueError("max_search_limit must be >= default_search_limit")
        
        if self.rate_limit_requests < 1:
            raise ValueError("rate_limit_requests must be positive")
        
        if self.rate_limit_period < 1:
            raise ValueError("rate_limit_period must be positive")
        
        return True

# Singleton instance
_config = None

def get_config() -> MemoryConfig:
    """Get or create configuration singleton"""
    global _config
    if _config is None:
        _config = MemoryConfig()
        _config.validate_config()
    return _config