"""
Real API Gateway with Portkey Integration
Production-ready routing with fallback chains - NO MOCKS
"""

import os
import httpx
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

logger = logging.getLogger(__name__)

class Provider(Enum):
    """Supported API providers."""
    PORTKEY = "portkey"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    XAI = "xai"

@dataclass
class ModelConfig:
    """Model configuration with routing preferences."""
    provider: Provider
    model_name: str
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: float = 30.0
    fallback_providers: List[Provider] = None

class RealAPIGateway:
    """Production API Gateway with real provider integrations."""
    
    def __init__(self):
        self.validate_environment()
        self.setup_providers()
        self.setup_model_routing()
    
    def validate_environment(self):
        """Validate all required API keys are present."""
        required_keys = {
            "PORTKEY_API_KEY": "Portkey Gateway",
            "OPENAI_API_KEY": "OpenAI",
            "ANTHROPIC_API_KEY": "Anthropic",
            "OPENROUTER_API_KEY": "OpenRouter"
        }
        
        missing_keys = []
        for key, name in required_keys.items():
            if not os.getenv(key):
                missing_keys.append(f"{key} ({name})")
        
        if missing_keys:
            raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
        
        # Validate no dummy keys
        for key, name in required_keys.items():
            value = os.getenv(key)
            if value and ("dummy" in value.lower() or "test" in value.lower()):
                raise ValueError(f"Dummy API key detected for {name}: {key}")
        
        logger.info("✅ All API keys validated successfully")

    def setup_providers(self):
        """Setup provider configurations with Portkey as primary gateway."""
        # Portkey configuration with virtual keys and OpenRouter/Together AI integration
        portkey_config = {
            "retry": {
                "attempts": 3,
                "on_status_codes": [429, 500, 502, 503, 504]
            },
            "cache": {
                "enabled": True,
                "ttl": 3600
            },
            "fallbacks": [
                {"provider": "openrouter"},
                {"provider": "together"}
            ]
        }
        
        self.providers = {
            Provider.PORTKEY: {
                "base_url": "https://api.portkey.ai/v1",
                "headers": {
                    "x-portkey-api-key": os.getenv("PORTKEY_API_KEY"),
                    "x-portkey-config": json.dumps(portkey_config),
                    "content-type": "application/json"
                },
                "config": portkey_config
            },
            Provider.OPENAI: {
                "base_url": "https://api.openai.com/v1",
                "headers": {
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                    "Content-Type": "application/json"
                }
            },
            Provider.ANTHROPIC: {
                "base_url": "https://api.anthropic.com/v1",
                "headers": {
                    "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }
            },
            Provider.OPENROUTER: {
                "base_url": "https://openrouter.ai/api/v1",
                "headers": {
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "HTTP-Referer": "https://sophia-intel-ai.com",
                    "X-Title": "Sophia Intel AI",
                    "Content-Type": "application/json"
                }
            },
            Provider.GROQ: {
                "base_url": "https://api.groq.com/openai/v1",
                "headers": {
                    "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                    "Content-Type": "application/json"
                }
            }
        }

    def setup_model_routing(self):
        """Setup intelligent model routing with fallbacks."""
        self.model_configs = {
            # Strategic Planning - High quality, slower
            "strategic": ModelConfig(
                provider=Provider.PORTKEY,
                model_name="gpt-4",
                max_tokens=4000,
                temperature=0.3,
                fallback_providers=[Provider.ANTHROPIC, Provider.OPENAI]
            ),
            
            # Development - Balanced performance
            "development": ModelConfig(
                provider=Provider.OPENAI,
                model_name="gpt-4",
                max_tokens=4000,
                temperature=0.2,
                fallback_providers=[Provider.OPENROUTER, Provider.ANTHROPIC]
            ),
            
            # Fast responses - Speed optimized
            "fast": ModelConfig(
                provider=Provider.GROQ,
                model_name="llama3-8b-8192",
                max_tokens=2000,
                temperature=0.7,
                fallback_providers=[Provider.OPENROUTER, Provider.OPENAI]
            ),
            
            # Analysis - High reasoning capability
            "analysis": ModelConfig(
                provider=Provider.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0.1,
                fallback_providers=[Provider.OPENAI, Provider.OPENROUTER]
            ),
            
            # Code generation - Specialized
            "coding": ModelConfig(
                provider=Provider.OPENAI,
                model_name="gpt-4",
                max_tokens=4000,
                temperature=0.2,
                fallback_providers=[Provider.OPENROUTER, Provider.ANTHROPIC]
            )
        }

    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            model_type: str = "development",
                            stream: bool = False,
                            **kwargs) -> Dict[str, Any]:
        """Execute chat completion with real API providers and fallback chain."""
        
        config = self.model_configs.get(model_type, self.model_configs["development"])
        
        # Try primary provider first
        try:
            return await self._call_provider(config.provider, config, messages, stream, **kwargs)
        except Exception as primary_error:
            logger.warning(f"Primary provider {config.provider.value} failed: {primary_error}")
            
            # Try fallback providers
            if config.fallback_providers:
                for fallback_provider in config.fallback_providers:
                    try:
                        logger.info(f"Trying fallback provider: {fallback_provider.value}")
                        fallback_config = ModelConfig(
                            provider=fallback_provider,
                            model_name=self._get_fallback_model(fallback_provider),
                            max_tokens=config.max_tokens,
                            temperature=config.temperature
                        )
                        return await self._call_provider(fallback_provider, fallback_config, messages, stream, **kwargs)
                    except Exception as fallback_error:
                        logger.warning(f"Fallback provider {fallback_provider.value} failed: {fallback_error}")
                        continue
            
            # If all providers failed, raise original error
            if os.getenv("FAIL_ON_MOCK_FALLBACK", "false").lower() == "true":
                raise Exception(f"All providers failed. Primary error: {primary_error}")
            else:
                raise primary_error

    def _get_fallback_model(self, provider: Provider) -> str:
        """Get appropriate model for fallback provider."""
        model_map = {
            Provider.OPENAI: "gpt-4",
            Provider.ANTHROPIC: "claude-3-sonnet-20240229",
            Provider.OPENROUTER: "openai/gpt-4",
            Provider.GROQ: "llama3-8b-8192",
            Provider.DEEPSEEK: "deepseek-chat",
            Provider.XAI: "grok-beta"
        }
        return model_map.get(provider, "gpt-3.5-turbo")

    async def _call_provider(self, 
                           provider: Provider, 
                           config: ModelConfig, 
                           messages: List[Dict[str, str]], 
                           stream: bool = False,
                           **kwargs) -> Dict[str, Any]:
        """Make actual API call to provider."""
        
        provider_config = self.providers[provider]
        
        # Prepare request payload based on provider
        if provider == Provider.ANTHROPIC:
            payload = {
                "model": config.model_name,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "messages": messages,
                "stream": stream
            }
            endpoint = "/messages"
        else:
            # OpenAI-compatible format
            payload = {
                "model": config.model_name,
                "messages": messages,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "stream": stream
            }
            endpoint = "/chat/completions"
        
        # Add any additional parameters
        payload.update(kwargs)
        
        # Make the API call
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            logger.info(f"Calling {provider.value} with model {config.model_name}")
            
            response = await client.post(
                f"{provider_config['base_url']}{endpoint}",
                headers=provider_config["headers"],
                json=payload
            )
            
            if response.status_code != 200:
                error_details = response.text if response.text else "Unknown error"
                raise httpx.HTTPStatusError(
                    f"Provider {provider.value} returned {response.status_code}: {error_details}",
                    request=response.request,
                    response=response
                )
            
            result = response.json()
            
            # Normalize response format across providers
            if provider == Provider.ANTHROPIC:
                # Convert Anthropic format to OpenAI format
                content = result.get("content", [])
                if content and len(content) > 0:
                    text_content = content[0].get("text", "")
                    return {
                        "choices": [{
                            "message": {
                                "role": "assistant",
                                "content": text_content
                            },
                            "finish_reason": "stop"
                        }],
                        "usage": result.get("usage", {}),
                        "model": config.model_name,
                        "provider": provider.value
                    }
                else:
                    raise ValueError("Invalid response from Anthropic API")
            else:
                # OpenAI-compatible format
                result["provider"] = provider.value
                return result

    async def get_available_models(self, provider: Provider = None) -> Dict[str, List[str]]:
        """Get available models from providers."""
        if provider:
            providers = [provider]
        else:
            providers = [Provider.OPENAI, Provider.ANTHROPIC, Provider.OPENROUTER]
        
        models = {}
        
        for prov in providers:
            try:
                provider_config = self.providers[prov]
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    if prov == Provider.ANTHROPIC:
                        # Anthropic doesn't have a models endpoint, return known models
                        models[prov.value] = [
                            "claude-3-sonnet-20240229",
                            "claude-3-haiku-20240307",
                            "claude-3-opus-20240229"
                        ]
                    else:
                        # OpenAI-compatible models endpoint
                        response = await client.get(
                            f"{provider_config['base_url']}/models",
                            headers=provider_config["headers"]
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            model_names = [model["id"] for model in data.get("data", [])]
                            models[prov.value] = model_names
                        else:
                            logger.warning(f"Failed to get models from {prov.value}")
                            models[prov.value] = []
                            
            except Exception as e:
                logger.error(f"Error getting models from {prov.value}: {e}")
                models[prov.value] = []
        
        return models

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all configured providers."""
        health_status = {}
        
        for provider in self.providers:
            try:
                if provider == Provider.ANTHROPIC:
                    # Test with minimal request
                    result = await self.chat_completion(
                        messages=[{"role": "user", "content": "Hi"}],
                        model_type="analysis"
                    )
                    health_status[provider.value] = {
                        "status": "healthy",
                        "response_received": bool(result)
                    }
                else:
                    # Test models endpoint for OpenAI-compatible providers
                    models = await self.get_available_models(provider)
                    health_status[provider.value] = {
                        "status": "healthy" if models.get(provider.value) else "unhealthy",
                        "model_count": len(models.get(provider.value, []))
                    }
                    
            except Exception as e:
                health_status[provider.value] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Overall health
        healthy_count = sum(1 for status in health_status.values() if status["status"] == "healthy")
        total_count = len(health_status)
        
        return {
            "overall_status": "healthy" if healthy_count > 0 else "unhealthy",
            "healthy_providers": healthy_count,
            "total_providers": total_count,
            "providers": health_status
        }

# Global instance
_gateway = None

def get_api_gateway() -> RealAPIGateway:
    """Get or create the global API gateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = RealAPIGateway()
    return _gateway