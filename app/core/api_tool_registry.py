from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class APITool:
    """Metadata describing an external API tool/integration."""

    name: str
    provider: str
    category: str  # voice|search|llm|routing|stt|embedding|infra
    api_key_env: Optional[str]
    rate_limit_per_min: Optional[int] = None
    cost_per_call: Optional[float] = None
    capabilities: Optional[List[str]] = None
    notes: Optional[str] = None


class APIToolRegistry:
    """Central registry for known external API tools.

    This provides a single source of truth for:
    - env var names
    - capabilities
    - coarse rate limits and cost hints (for routing/monitoring)
    """

    tools: Dict[str, APITool] = {
        # Voice
        "elevenlabs": APITool(
            name="ElevenLabs",
            provider="elevenlabs",
            category="voice",
            api_key_env="ELEVENLABS_API_KEY",
            rate_limit_per_min=100,
            cost_per_call=None,
            capabilities=["tts", "voice_profiles"],
            notes="Used by voice_integration for TTS",
        ),

        # STT
        "whisper": APITool(
            name="OpenAI Whisper",
            provider="openai",
            category="stt",
            api_key_env="OPENAI_API_KEY",
            capabilities=["stt"],
        ),

        # LLM routing
        "portkey": APITool(
            name="Portkey",
            provider="portkey",
            category="routing",
            api_key_env="PORTKEY_API_KEY",
            capabilities=["multi-provider", "fallbacks", "caching"],
        ),

        # Search providers (optional integrations)
        "tavily": APITool(
            name="Tavily Search",
            provider="tavily",
            category="search",
            api_key_env="TAVILY_API_KEY",
            rate_limit_per_min=60,
            cost_per_call=0.01,
            capabilities=["web_search", "news"],
        ),
        "exa": APITool(
            name="Exa",
            provider="exa",
            category="search",
            api_key_env="EXA_API_KEY",
            capabilities=["neural_search"],
        ),
        "brave": APITool(
            name="Brave Search",
            provider="brave",
            category="search",
            api_key_env="BRAVE_API_KEY",
            capabilities=["web_search"],
        ),
        # Voice/STT alternatives
        "deepgram": APITool(
            name="Deepgram",
            provider="deepgram",
            category="stt",
            api_key_env="DEEPGRAM_API_KEY",
            capabilities=["realtime_stt", "batch_stt"],
        ),
    }

    @classmethod
    def get(cls, key: str) -> Optional[APITool]:
        return cls.tools.get(key)

    @classmethod
    def list(cls) -> List[APITool]:
        return list(cls.tools.values())

