"""Centralized configuration backed by repo `.env.master`.

This module is silent and idempotent; it relies on `app.core.env.load_env_once()`
to populate environment variables exactly once from the repository `.env.master`.
"""

import os
from typing import Optional, Dict, Any
from app.core.env import load_env_once

class Config:
    """Single source of truth for all configuration (env-driven)."""

    # Environment detection
    ENV = os.getenv("SOPHIA_ENV", "local")

    _loaded = False

    @classmethod
    def load_env(cls):
        """Load environment once from repo `.env.master` (silent)."""
        if cls._loaded:
            return
        load_env_once()
        cls._loaded = True
    
    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get config value with fallback"""
        cls.load_env()
        return os.getenv(key, default)
    
    @classmethod
    def get_required(cls, key: str) -> str:
        """Get required config or raise error"""
        value = cls.get(key)
        if not value:
            raise ValueError(f"Required config {key} not set")
        return value
    
    @classmethod
    def get_portkey_config(cls) -> Dict[str, Any]:
        """Get Portkey configuration"""
        cls.load_env()
        return {
            "api_key": cls.get("PORTKEY_API_KEY"),
            "base_url": cls.get("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
            "virtual_keys": {
                "openrouter": cls.get("OPENROUTER_VK"),
                "together": cls.get("TOGETHER_VK"),
                "aimlapi": cls.get("AIMLAPI_VK"),
            },
            "headers": {
                "x-portkey-retry": "3",
                "x-portkey-cache": "semantic",
            }
        }
    
    @classmethod
    def get_business_config(cls) -> Dict[str, Any]:
        """Get business integration configs"""
        cls.load_env()
        return {
            "hubspot": {
                "api_key": cls.get("HUBSPOT_API_KEY"),
                "access_token": cls.get("HUBSPOT_ACCESS_TOKEN"),
                "app_id": cls.get("HUBSPOT_APP_ID"),
            },
            "salesforce": {
                "client_id": cls.get("SALESFORCE_CLIENT_ID"),
                "client_secret": cls.get("SALESFORCE_CLIENT_SECRET"),
                "username": cls.get("SALESFORCE_USERNAME"),
                "password": cls.get("SALESFORCE_PASSWORD"),
                "security_token": cls.get("SALESFORCE_SECURITY_TOKEN"),
                "domain": cls.get("SALESFORCE_DOMAIN", "https://na139.salesforce.com"),
            },
            "gong": {
                "access_key": cls.get("GONG_ACCESS_KEY"),
                "client_secret": cls.get("GONG_CLIENT_SECRET"),
            },
            "slack": {
                "bot_token": cls.get("SLACK_BOT_TOKEN"),
                "app_token": cls.get("SLACK_APP_TOKEN"),
                "user_token": cls.get("SLACK_USER_TOKEN"),
                "signing_secret": cls.get("SLACK_SIGNING_SECRET"),
            },
            "airtable": {
                "pat": cls.get("AIRTABLE_PAT") or cls.get("AIRTABLE_API_KEY"),
                "base_id": cls.get("AIRTABLE_BASE_ID"),
            }
        }
    
    @classmethod
    def get_database_urls(cls) -> Dict[str, str]:
        """Get database connection strings"""
        cls.load_env()
        return {
            "neon": cls.get("NEON_DATABASE_URL"),
            "redis": cls.get("REDIS_URL", "redis://localhost:6379"),
            "weaviate": cls.get("WEAVIATE_URL", "http://localhost:8080"),
            "qdrant": cls.get("QDRANT_URL", "http://localhost:6333"),
            "milvus": cls.get("MILVUS_URL", "http://localhost:19530"),
        }
    
    @classmethod
    def is_cloud_deployment(cls) -> bool:
        """Check if running in cloud"""
        return cls.ENV in ["staging", "production"] or bool(os.getenv("FLY_APP_NAME") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

# Auto-load on import (silent)
Config.load_env()
