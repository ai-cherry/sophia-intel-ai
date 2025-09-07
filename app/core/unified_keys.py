"""
Unified API Keys Configuration
Central location for all API keys - both Portkey virtual keys and direct keys
This ensures all orchestrators and agents can access the keys
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class KeyType(Enum):
    """Types of API keys"""

    PORTKEY_VIRTUAL = "portkey_virtual"
    DIRECT_API = "direct_api"
    VECTOR_DB = "vector_db"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class APIKeyConfig:
    """Configuration for an API key"""

    key: str
    type: KeyType
    provider: str
    models: Optional[list] = None
    base_url: Optional[str] = None
    description: Optional[str] = None


class UnifiedKeysManager:
    """Singleton manager for all API keys"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Main Portkey configuration
        self.portkey_api_key = os.getenv("PORTKEY_API_KEY", "hPxFZGd8AN269n4bznDf2/Onbi8I")
        self.portkey_base_url = "https://api.portkey.ai/v1"

        # Portkey Virtual Keys (exact names from dashboard)
        self.portkey_virtual_keys = {
            "OPENAI-VK": APIKeyConfig(
                key=os.getenv("OPENAI_VK", "openai-vk-190a60"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="openai",
                models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                description="OpenAI models via Portkey",
            ),
            "ANTHROPIC-VK": APIKeyConfig(
                key=os.getenv("ANTHROPIC_VK", "anthropic-vk-b42804"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="anthropic",
                models=[
                    "claude-3-haiku-20240307",
                    "claude-3-sonnet-20240229",
                    "claude-3-opus-20240229",
                ],
                description="Anthropic Claude models via Portkey",
            ),
            "DEEPSEEK-VK": APIKeyConfig(
                key=os.getenv("DEEPSEEK_VK", "deepseek-vk-24102f"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="deepseek",
                models=["deepseek-chat", "deepseek-coder"],
                description="DeepSeek models via Portkey",
            ),
            "OPENROUTER-VK": APIKeyConfig(
                key=os.getenv("OPENROUTER_VK", "vkj-openrouter-cc4151"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="openrouter",
                models=["auto"],
                description="OpenRouter auto-routing via Portkey",
            ),
            "PERPLEXITY-VK": APIKeyConfig(
                key=os.getenv("PERPLEXITY_VK", "perplexity-vk-56c172"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="perplexity",
                models=["sonar-pro", "sonar", "sonar-reasoning"],
                description="Perplexity online models via Portkey",
            ),
            "GROQ-VK": APIKeyConfig(
                key=os.getenv("GROQ_VK", "groq-vk-6b9b52"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="groq",
                models=["llama-3.1-70b-versatile", "llama-3.1-8b-instant"],
                description="Groq fast inference via Portkey",
            ),
            "MISTRAL-VK": APIKeyConfig(
                key=os.getenv("MISTRAL_VK", "mistral-vk-f92861"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="mistral",
                models=["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"],
                description="Mistral AI models via Portkey",
            ),
            "XAI-VK": APIKeyConfig(
                key=os.getenv("XAI_VK", "xai-vk-e65d0f"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="xai",
                models=["grok-2", "grok-2-mini", "grok-vision-2"],
                description="X.AI Grok via Portkey",
            ),
            "TOGETHER-VK": APIKeyConfig(
                key=os.getenv("TOGETHER_VK", "together-ai-670469"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="together",
                models=[
                    "meta-llama/Llama-3.2-3B-Instruct-Turbo",
                    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                ],
                description="Together AI models via Portkey",
            ),
            "COHERE-VK": APIKeyConfig(
                key=os.getenv("COHERE_VK", "cohere-vk-496fa9"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="cohere",
                models=["command-r", "command-r-plus"],
                description="Cohere models via Portkey",
            ),
            "GEMINI-VK": APIKeyConfig(
                key=os.getenv("GEMINI_VK", "gemini-vk-3d6108"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="gemini",
                models=["gemini-1.5-flash", "gemini-1.5-pro"],
                description="Google Gemini via Portkey",
            ),
            "HUGGINGFACE-VK": APIKeyConfig(
                key=os.getenv("HUGGINGFACE_VK", "huggingface-vk-28240e"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="huggingface",
                models=["microsoft/Phi-3-mini-4k-instruct"],
                description="HuggingFace models via Portkey",
            ),
            "QDRANT-VK": APIKeyConfig(
                key=os.getenv("QDRANT_VK", "qdrant-vk-d2b62a"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="qdrant",
                description="Qdrant vector DB via Portkey",
            ),
            "MILVUS-VK": APIKeyConfig(
                key=os.getenv("MILVUS_VK", "milvus-vk-34fa02"),
                type=KeyType.PORTKEY_VIRTUAL,
                provider="milvus",
                description="Milvus vector DB via Portkey",
            ),
        }

        # Direct API Keys
        self.direct_api_keys = {
            "OPENAI": APIKeyConfig(
                key=os.getenv(
                    "OPENAI_API_KEY",
                    "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",
                ),
                type=KeyType.DIRECT_API,
                provider="openai",
                base_url="https://api.openai.com/v1",
                models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"],
            ),
            "ANTHROPIC": APIKeyConfig(
                key=os.getenv(
                    "ANTHROPIC_API_KEY",
                    "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",
                ),
                type=KeyType.DIRECT_API,
                provider="anthropic",
                models=[
                    "claude-3-haiku-20240307",
                    "claude-3-sonnet-20240229",
                    "claude-3-opus-20240229",
                ],
            ),
            "DEEPSEEK": APIKeyConfig(
                key=os.getenv("DEEPSEEK_API_KEY", "sk-c8a5f1725d7b4f96b29a3d041848cb74"),
                type=KeyType.DIRECT_API,
                provider="deepseek",
                base_url="https://api.deepseek.com/v1",
                models=["deepseek-chat", "deepseek-coder"],
            ),
            "OPENROUTER": APIKeyConfig(
                key=os.getenv(
                    "OPENROUTER_API_KEY",
                    "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",
                ),
                type=KeyType.DIRECT_API,
                provider="openrouter",
                base_url="https://openrouter.ai/api/v1",
                models=["auto", "openai/gpt-3.5-turbo", "anthropic/claude-3-haiku"],
            ),
            "PERPLEXITY": APIKeyConfig(
                key=os.getenv(
                    "PERPLEXITY_API_KEY", "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"
                ),
                type=KeyType.DIRECT_API,
                provider="perplexity",
                base_url="https://api.perplexity.ai",
                models=["sonar-pro", "sonar", "sonar-reasoning"],
            ),
            "GROQ": APIKeyConfig(
                key=os.getenv(
                    "GROQ_API_KEY", "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"
                ),
                type=KeyType.DIRECT_API,
                provider="groq",
                models=["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            ),
            "MISTRAL": APIKeyConfig(
                key=os.getenv("MISTRAL_API_KEY", "jCGVZEeBzppPH0pPVL0vxRCPnZuWL90i"),
                type=KeyType.DIRECT_API,
                provider="mistral",
                models=["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"],
            ),
            "TOGETHER_AI": APIKeyConfig(
                key=os.getenv(
                    "TOGETHER_AI_API_KEY", "tgp_v1_HE_uluFh-fELZDmEP9xKZXuSBT4a8EHd6s9CmSe5WWo"
                ),
                type=KeyType.DIRECT_API,
                provider="together",
                base_url="https://api.together.xyz/v1",
                models=[
                    "meta-llama/Llama-3.2-3B-Instruct-Turbo",
                    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                ],
            ),
            "HUGGINGFACE": APIKeyConfig(
                key=os.getenv("HUGGINGFACE_API_TOKEN", "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"),
                type=KeyType.DIRECT_API,
                provider="huggingface",
                base_url="https://api-inference.huggingface.co",
                models=["microsoft/Phi-3-mini-4k-instruct", "meta-llama/Llama-2-7b-chat-hf"],
            ),
            "GEMINI": APIKeyConfig(
                key=os.getenv("GEMINI_API_KEY", "AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"),
                type=KeyType.DIRECT_API,
                provider="gemini",
                models=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"],
            ),
            "LLAMA": APIKeyConfig(
                key=os.getenv(
                    "LLAMA_API_KEY", "llx-MfsEhU0wHNL7PcRN4YEFM3eWcPQggq7edEr52IdnvkHZPPYj"
                ),
                type=KeyType.DIRECT_API,
                provider="llama",
                base_url="https://api.llama-api.com",
                models=["llama-13b-chat", "llama-70b-chat"],
            ),
            "AIMLAPI": APIKeyConfig(
                key=os.getenv("AIMLAPI_API_KEY", "562d964ac0b54357874b01de33cb91e9"),
                type=KeyType.DIRECT_API,
                provider="aimlapi",
                base_url="https://api.aimlapi.com/v1",
                models=[
                    "openai/gpt-5-2025-08-07",
                    "openai/gpt-5-mini-2025-08-07",
                    "openai/gpt-5-nano-2025-08-07",
                    "x-ai/grok-4-07-09",
                    "x-ai/grok-3-beta",
                    "x-ai/grok-3-mini-beta",
                    "openai/o4-mini-2025-04-16",
                    "openai/o3-2025-04-16",
                    "openai/o3-pro",
                    "zhipu/glm-4.5",
                    "zhipu/glm-4.5-air",
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-oss-120b",
                    "gpt-oss-20b",
                ],
                description="Access to 300+ models including GPT-5, Grok-4, O-series, and more",
            ),
            "COHERE": APIKeyConfig(
                key=os.getenv("COHERE_API_KEY", "your_cohere_api_key_here"),  # Need real key
                type=KeyType.DIRECT_API,
                provider="cohere",
                models=["command-r", "command-r-plus"],
            ),
        }

        # Vector Database Keys
        self.vector_db_keys = {
            "QDRANT": APIKeyConfig(
                key=os.getenv(
                    "QDRANT_API_KEY",
                    "ccabdaed-b564-4157-8846-b8f227c7f29b|hRnj-WYa5pxZlPuu2S2LmrX2LziBOdChyLP5Hq578N-HIi16EZIshA",
                ),
                type=KeyType.VECTOR_DB,
                provider="qdrant",
                base_url="https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io",
                description="Qdrant vector database",
            ),
            "WEAVIATE": APIKeyConfig(
                key=os.getenv("WEAVIATE_API_KEY", "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf"),
                type=KeyType.VECTOR_DB,
                provider="weaviate",
                base_url="https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud",
                description="Weaviate vector database",
            ),
            "REDIS": APIKeyConfig(
                key=os.getenv(
                    "REDIS_USER_KEY", "S666q3cr9wmzpetc6iud02iqv26774azveodh2pfadrd7pgq8l7"
                ),
                type=KeyType.VECTOR_DB,
                provider="redis",
                base_url="redis-15014.fcrce172.us-east-1-1.ec2.redns.redis-cloud.com:15014",
                description="Redis cache and vector storage",
            ),
            "MEM0": APIKeyConfig(
                key=os.getenv("MEM0_API_KEY", "m0-migu5eMnfwT41nhTgVHsCnSAifVtOf3WIFz2vmQc"),
                type=KeyType.VECTOR_DB,
                provider="mem0",
                base_url="https://api.mem0.ai",
                description="Mem0 memory system",
            ),
        }

        # Infrastructure Keys
        self.infrastructure_keys = {
            "NEON": APIKeyConfig(
                key=os.getenv(
                    "NEON_API_TOKEN",
                    "napi_r3gsuacduzw44nqdqav1u0hr2uv4bb2if48r8627jkxo7e4b2sxn92wsgf6zlxby",
                ),
                type=KeyType.INFRASTRUCTURE,
                provider="neon",
                base_url="https://app-sparkling-wildflower-99699121.dpl.myneon.app",
                description="Neon PostgreSQL database",
            ),
            "NEO4J": APIKeyConfig(
                key=os.getenv("NEO4J_CLIENT_ID", "jPSJvG4itnj6DHbdUwm9dBTjeimb9wXv"),
                type=KeyType.INFRASTRUCTURE,
                provider="neo4j",
                description="Neo4j graph database",
            ),
            "N8N": APIKeyConfig(
                key=os.getenv(
                    "N8N_API_KEY",
                    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzN2Y4NTVkMi01ODIwLTQ2ZmMtYjlhMS1kMjdlN2ZhMGQ3MDIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUwMjgyMjU5LCJleHAiOjE3NTgwMDYwMDB9.5uLdSTZdIwlSld3WpVGC0TVm97vvzXs3y44FNeRm3N8",
                ),
                type=KeyType.INFRASTRUCTURE,
                provider="n8n",
                description="n8n workflow automation",
            ),
            "PULUMI": APIKeyConfig(
                key=os.getenv(
                    "PULUMI_ACCESS_TOKEN", "pul-f60e05d69c13efa7a73abea7a7bf09c668fbc2dc"
                ),
                type=KeyType.INFRASTRUCTURE,
                provider="pulumi",
                description="Pulumi infrastructure as code",
            ),
            "AGNO": APIKeyConfig(
                key=os.getenv("AGNO_API_KEY", "phi-0cnOaV2N-MKID0LJTszPjAdj7XhunqMQFG4IwLPG9dI"),
                type=KeyType.INFRASTRUCTURE,
                provider="agno",
                description="Agno/PhiData framework",
            ),
            "CONTINUE": APIKeyConfig(
                key=os.getenv(
                    "CONTINUE_API_KEY",
                    "con-483f8da98573b95f77c07381f7ccf1ff5e070acf7eac9bea929f64250e9f1dd2",
                ),
                type=KeyType.INFRASTRUCTURE,
                provider="continue",
                description="Continue.dev integration",
            ),
        }

        self._initialized = True

    def get_portkey_virtual_key(self, provider: str) -> Optional[str]:
        """Get Portkey virtual key for a provider"""
        for _key_name, config in self.portkey_virtual_keys.items():
            if config.provider == provider.lower():
                return config.key
        return None

    def get_direct_api_key(self, provider: str) -> Optional[str]:
        """Get direct API key for a provider"""
        for _key_name, config in self.direct_api_keys.items():
            if config.provider == provider.lower():
                return config.key
        return None

    def get_all_keys_for_provider(self, provider: str) -> dict[str, Any]:
        """Get all keys (virtual and direct) for a provider"""
        result = {}

        # Check Portkey virtual keys
        vk = self.get_portkey_virtual_key(provider)
        if vk:
            result["portkey_virtual_key"] = vk

        # Check direct API keys
        dk = self.get_direct_api_key(provider)
        if dk:
            result["direct_api_key"] = dk

        # Get additional config
        for config in self.direct_api_keys.values():
            if config.provider == provider.lower():
                result["base_url"] = config.base_url
                result["models"] = config.models
                break

        return result

    def get_working_providers(self) -> dict[str, list]:
        """Get list of working providers based on test results"""
        return {
            "portkey_working": ["openai", "anthropic", "deepseek", "mistral", "together", "cohere"],
            "direct_working": ["openai", "anthropic", "deepseek"],
            "needs_fix": ["groq", "perplexity", "gemini", "huggingface", "openrouter", "xai"],
        }

    def get_provider_status(self) -> dict[str, Any]:
        """Get comprehensive status of all providers"""
        status = {
            "portkey_api_key": self.portkey_api_key[:20] + "..." if self.portkey_api_key else None,
            "total_virtual_keys": len(self.portkey_virtual_keys),
            "total_direct_keys": len(self.direct_api_keys),
            "vector_databases": len(self.vector_db_keys),
            "infrastructure": len(self.infrastructure_keys),
            "working_providers": self.get_working_providers(),
        }
        return status

    def export_env_file(self, filepath: str = ".env"):
        """Export all keys to a .env file"""
        lines = ["# Generated API Keys Configuration\n"]

        # Portkey main key
        lines.append("# Portkey Configuration\n")
        lines.append(f"PORTKEY_API_KEY={self.portkey_api_key}\n")
        lines.append(f"PORTKEY_BASE_URL={self.portkey_base_url}\n\n")

        # Virtual keys
        lines.append("# Portkey Virtual Keys\n")
        for name, config in self.portkey_virtual_keys.items():
            env_name = name.replace("-", "_").replace("VK", "VK")
            lines.append(f"{env_name}={config.key}\n")

        # Direct API keys
        lines.append("\n# Direct API Keys\n")
        for name, config in self.direct_api_keys.items():
            lines.append(f"{name}_API_KEY={config.key}\n")

        # Vector DB keys
        lines.append("\n# Vector Database Keys\n")
        for name, config in self.vector_db_keys.items():
            lines.append(f"{name}_API_KEY={config.key}\n")
            if config.base_url:
                lines.append(f"{name}_URL={config.base_url}\n")

        # Infrastructure keys
        lines.append("\n# Infrastructure Keys\n")
        for name, config in self.infrastructure_keys.items():
            lines.append(f"{name}_API_KEY={config.key}\n")

        with open(filepath, "w") as f:
            f.writelines(lines)

        return filepath


# Singleton instance
unified_keys = UnifiedKeysManager()
