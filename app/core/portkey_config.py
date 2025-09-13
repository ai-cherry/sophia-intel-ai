"""
Centralized Portkey Configuration Manager
Handles all LLM routing through Portkey with proper virtual keys and fallback mechanisms
"""
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any
from portkey_ai import Portkey
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class ModelProvider(Enum):
    """Supported model providers through Portkey"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    PERPLEXITY = "perplexity"
    GROQ = "groq"
    MISTRAL = "mistral"
    GEMINI = "gemini"
    XAI = "xai"
    TOGETHER = "together"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    OPENROUTER = "openrouter"
class AgentRole(Enum):
    """Agent roles for optimal model selection"""
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    CODING = "coding"
    RESEARCH = "research"
    STRATEGIC = "strategic"
    TACTICAL = "tactical"
    EMPATHETIC = "empathetic"
    TECHNICAL = "technical"
    REALTIME = "realtime"
    COST_SENSITIVE = "cost_sensitive"
@dataclass
class ProviderConfig:
    """Configuration for each provider"""
    virtual_key: str
    models: list[str]
    fallback_providers: list[str]
    max_tokens: int = 4096
    temperature: float = 0.7
    retry_count: int = 3
class PortkeyManager:
    """Singleton manager for all Portkey operations"""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    def __init__(self):
        if self._initialized:
            return
        # Require PORTKEY_API_KEY from environment or secure vault
        self.api_key = os.getenv("PORTKEY_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "PORTKEY_API_KEY is not set. Configure it in ./.env.master and start via ./sophia"
            )
        self.base_url = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
        # Initialize provider configurations with actual virtual keys
        self.providers = {
            ModelProvider.OPENAI: ProviderConfig(
                virtual_key=os.getenv("OPENAI_VK", "openai-vk-190a60"),
                models=["gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"],
                fallback_providers=[ModelProvider.ANTHROPIC, ModelProvider.OPENROUTER],
            ),
            ModelProvider.ANTHROPIC: ProviderConfig(
                virtual_key=os.getenv("ANTHROPIC_VK", "anthropic-vk-b42804"),
                models=[
                    "claude-opus-4.1",
                    "claude-sonnet-4",
                    "claude-3-opus-20240229",
                    "claude-3-haiku-20240307",
                ],
                fallback_providers=[ModelProvider.OPENAI, ModelProvider.OPENROUTER],
            ),
            ModelProvider.DEEPSEEK: ProviderConfig(
                virtual_key=os.getenv("DEEPSEEK_VK", "deepseek-vk-24102f"),
                models=[
                    "deepseek-reasoner-v3.1",
                    "deepseek-chat-v3.1",
                    "deepseek-r1",
                    "deepseek-coder",
                ],
                fallback_providers=[ModelProvider.OPENAI, ModelProvider.MISTRAL],
            ),
            ModelProvider.PERPLEXITY: ProviderConfig(
                virtual_key=os.getenv("PERPLEXITY_VK", "perplexity-vk-56c172"),
                models=["sonar-pro", "sonar", "sonar-reasoning"],
                fallback_providers=[ModelProvider.OPENAI, ModelProvider.ANTHROPIC],
            ),
            ModelProvider.GROQ: ProviderConfig(
                virtual_key=os.getenv("GROQ_VK", "groq-vk-6b9b52"),
                models=["llama-3.1-70b-versatile", "llama-3.1-8b-instant"],
                fallback_providers=[ModelProvider.TOGETHER, ModelProvider.OPENROUTER],
            ),
            ModelProvider.MISTRAL: ProviderConfig(
                virtual_key=os.getenv("MISTRAL_VK", "mistral-vk-f92861"),
                models=["mistral-large", "mistral-medium"],
                fallback_providers=[ModelProvider.GROQ, ModelProvider.TOGETHER],
            ),
            ModelProvider.GEMINI: ProviderConfig(
                virtual_key=os.getenv("GEMINI_VK", "gemini-vk-3d6108"),
                models=["gemini-1.5-flash", "gemini-1.5-pro"],
                fallback_providers=[ModelProvider.OPENAI, ModelProvider.ANTHROPIC],
            ),
            ModelProvider.XAI: ProviderConfig(
                virtual_key=os.getenv("XAI_VK", "xai-vk-e65d0f"),
                models=["grok-2", "grok-2-mini", "grok-vision-2"],
                fallback_providers=[ModelProvider.OPENAI, ModelProvider.ANTHROPIC],
            ),
            ModelProvider.TOGETHER: ProviderConfig(
                virtual_key=os.getenv("TOGETHER_VK", "together-ai-670469"),
                models=[
                    "meta-llama/Llama-3.2-3B-Instruct-Turbo",
                    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                ],
                fallback_providers=[ModelProvider.GROQ, ModelProvider.OPENROUTER],
            ),
            ModelProvider.COHERE: ProviderConfig(
                virtual_key=os.getenv("COHERE_VK", "cohere-vk-496fa9"),
                models=["command-r-plus", "command-r"],
                fallback_providers=[ModelProvider.OPENAI, ModelProvider.ANTHROPIC],
            ),
            ModelProvider.HUGGINGFACE: ProviderConfig(
                virtual_key=os.getenv("HUGGINGFACE_VK", "huggingface-vk-28240e"),
                models=["meta-llama/Llama-3-70b", "mistralai/Mixtral-8x7B"],
                fallback_providers=[ModelProvider.TOGETHER, ModelProvider.GROQ],
            ),
            ModelProvider.OPENROUTER: ProviderConfig(
                virtual_key=os.getenv("OPENROUTER_VK", "vkj-openrouter-cc4151"),
                models=["auto"],  # OpenRouter auto-selects best model
                fallback_providers=[],  # OpenRouter is the final fallback
            ),
        }
        # Role to provider mapping for optimal performance
        self.role_mappings = {
            AgentRole.CREATIVE: [
                ModelProvider.OPENAI,
                ModelProvider.ANTHROPIC,
                ModelProvider.GEMINI,
            ],
            AgentRole.ANALYTICAL: [
                ModelProvider.DEEPSEEK,
                ModelProvider.ANTHROPIC,
                ModelProvider.OPENAI,
            ],
            AgentRole.CODING: [
                ModelProvider.DEEPSEEK,
                ModelProvider.OPENAI,
                ModelProvider.ANTHROPIC,
            ],
            AgentRole.RESEARCH: [
                ModelProvider.PERPLEXITY,
                ModelProvider.OPENAI,
                ModelProvider.ANTHROPIC,
            ],
            AgentRole.STRATEGIC: [
                ModelProvider.ANTHROPIC,
                ModelProvider.OPENAI,
                ModelProvider.GEMINI,
            ],
            AgentRole.TACTICAL: [
                ModelProvider.GROQ,
                ModelProvider.MISTRAL,
                ModelProvider.TOGETHER,
            ],
            AgentRole.EMPATHETIC: [
                ModelProvider.ANTHROPIC,
                ModelProvider.OPENAI,
                ModelProvider.COHERE,
            ],
            AgentRole.TECHNICAL: [
                ModelProvider.DEEPSEEK,
                ModelProvider.MISTRAL,
                ModelProvider.GROQ,
            ],
            AgentRole.REALTIME: [
                ModelProvider.PERPLEXITY,
                ModelProvider.GROQ,
                ModelProvider.OPENAI,
            ],
            AgentRole.COST_SENSITIVE: [
                ModelProvider.MISTRAL,
                ModelProvider.TOGETHER,
                ModelProvider.GROQ,
            ],
        }
        # Initialize Portkey client
        self.client = None
        self._initialize_client()
        self._initialized = True
    def _initialize_client(self):
        """Initialize the Portkey client with proper configuration"""
        try:
            self.client = Portkey(
                api_key=self.api_key,
                base_url=self.base_url,
                config={
                    "retry": {"attempts": 3, "on_status_codes": [429, 500, 502, 503]},
                    "cache": {"mode": "semantic", "max_age": 3600},
                },
            )
            logger.info("Portkey client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Portkey client: {e}")
            raise
    def get_client_for_role(self, role: AgentRole, **kwargs) -> Portkey:
        """Get a configured Portkey client for a specific agent role"""
        providers = self.role_mappings.get(role, [ModelProvider.OPENAI])
        primary_provider = providers[0]
        config = self.providers[primary_provider]
        # Build fallback configuration
        fallback_configs = []
        for fallback_provider in config.fallback_providers:
            fallback_config = self.providers.get(fallback_provider)
            if fallback_config:
                fallback_configs.append(
                    {
                        "virtual_key": fallback_config.virtual_key,
                        "model": (
                            fallback_config.models[0]
                            if fallback_config.models
                            else "auto"
                        ),
                    }
                )
        # Create client with role-specific configuration
        return Portkey(
            api_key=self.api_key,
            virtual_key=config.virtual_key,
            config={
                "model": config.models[0] if config.models else "auto",
                "max_tokens": kwargs.get("max_tokens", config.max_tokens),
                "temperature": kwargs.get("temperature", config.temperature),
                "fallbacks": fallback_configs,
                "retry": {
                    "attempts": config.retry_count,
                    "on_status_codes": [429, 500, 502, 503],
                },
                "cache": {"mode": "semantic", "max_age": 3600},
                "metadata": {
                    "role": role.value,
                    "primary_provider": primary_provider.value,
                },
            },
        )
    def get_client_for_provider(self, provider: ModelProvider, **kwargs) -> Portkey:
        """Get a configured Portkey client for a specific provider"""
        config = self.providers[provider]
        # Build fallback configuration
        fallback_configs = []
        for fallback_provider in config.fallback_providers:
            fallback_config = self.providers.get(fallback_provider)
            if fallback_config:
                fallback_configs.append(
                    {
                        "virtual_key": fallback_config.virtual_key,
                        "model": (
                            fallback_config.models[0]
                            if fallback_config.models
                            else "auto"
                        ),
                    }
                )
        return Portkey(
            api_key=self.api_key,
            virtual_key=config.virtual_key,
            config={
                "model": kwargs.get(
                    "model", config.models[0] if config.models else "auto"
                ),
                "max_tokens": kwargs.get("max_tokens", config.max_tokens),
                "temperature": kwargs.get("temperature", config.temperature),
                "fallbacks": fallback_configs,
                "retry": {
                    "attempts": config.retry_count,
                    "on_status_codes": [429, 500, 502, 503],
                },
                "metadata": {"provider": provider.value},
            },
        )
    def test_connection(self, provider: ModelProvider) -> bool:
        """Test connection to a specific provider"""
        try:
            client = self.get_client_for_provider(provider)
            client.chat.completions.create(
                messages=[{"role": "user", "content": "Test connection"}], max_tokens=10
            )
            logger.info(f"✓ {provider.value} connection successful")
            return True
        except Exception as e:
            logger.error(f"✗ {provider.value} connection failed: {e}")
            return False
    def test_all_connections(self) -> dict[str, bool]:
        """Test all provider connections"""
        results = {}
        for provider in ModelProvider:
            results[provider.value] = self.test_connection(provider)
        return results
    def get_provider_status(self) -> dict[str, Any]:
        """Get status of all providers"""
        status = {}
        for provider, config in self.providers.items():
            status[provider.value] = {
                "virtual_key": config.virtual_key[:10]
                + "...",  # Partial key for security
                "models": config.models,
                "fallback_providers": [p.value for p in config.fallback_providers],
                "configured": bool(config.virtual_key),
            }
        return status
# Singleton instance
portkey_manager = PortkeyManager()
