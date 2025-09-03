from enum import Enum
import os
from typing import Optional


class KeyProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"


ENV_MAP = {
    KeyProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
    KeyProvider.OPENAI: "OPENAI_API_KEY",
    KeyProvider.QWEN: "QWEN_API_KEY",
    KeyProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
}


def get_key(provider: KeyProvider | str) -> Optional[str]:
    if isinstance(provider, str):
        provider = KeyProvider(provider.lower()) if provider.lower() in [p.value for p in KeyProvider] else None
    if not provider:
        return None
    env_name = ENV_MAP.get(provider)
    return os.getenv(env_name) if env_name else None

