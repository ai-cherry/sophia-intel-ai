"""PORTKEY-ONLY LLM GATEWAY - THE SINGLE SOURCE OF TRUTH"""

import os
from typing import Any, Dict, Optional
from portkey_ai import Portkey

class LLMGateway:
    """ALL LLM calls go through Portkey. NO EXCEPTIONS."""
    
    _instance: Optional['LLMGateway'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # ONLY Portkey configuration
        self.client = Portkey(
            api_key=os.getenv("PORTKEY_API_KEY"),
            virtual_keys={
                "openrouter": os.getenv("OPENROUTER_VK"),
                "together": os.getenv("TOGETHER_VK"),
                "aimlapi": os.getenv("AIMLAPI_VK")
            },
            config={
                "retry": {"attempts": 3},
                "cache": {"ttl": 3600},
                "fallback": {
                    "models": [
                        "claude-opus-4.1",
                        "gpt-4o",
                        "meta/llama-maverick-4"
                    ]
                }
            }
        )
        
        self._initialized = True
    
    async def chat(self, messages: list, model: str = "auto", **kwargs) -> Any:
        """All chat completions through Portkey"""
        return await self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
    
    async def embed(self, text: str, model: str = "text-embedding-3-large") -> list:
        """All embeddings through Portkey"""
        return await self.client.embeddings.create(
            model=model,
            input=text
        )

# SINGLETON INSTANCE
gateway = LLMGateway()
