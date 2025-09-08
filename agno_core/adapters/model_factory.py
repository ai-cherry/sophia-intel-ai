import os
import socket
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml


MODELS_YAML_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "..", "config", "models.yaml")
# Resolve to repo-root/config/models.yaml regardless of caller CWD
MODELS_YAML_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "models.yaml"))


class ConfigError(RuntimeError):
    pass


def _load_models_yaml(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        raise ConfigError(f"models.yaml not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _require_env(keys: List[str]) -> List[str]:
    missing = [k for k in keys if not os.getenv(k)]
    return missing


@dataclass
class PortkeyCallConfig:
    model: str
    virtual_key_env: Optional[str] = None
    virtual_key_envs: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    context_window: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None


class PortkeyClient:
    """Lightweight Portkey adapter placeholder.

    This does not perform network I/O here; it assembles a call spec that the
    runtime can use to hit Portkey's endpoint with the selected virtual key.
    """

    def __init__(self, api_key_env: str, call: PortkeyCallConfig):
        self.api_key_env = api_key_env
        self.call = call
        self._validate_env()

    def _validate_env(self) -> None:
        missing = _require_env([self.api_key_env])
        if missing:
            raise ConfigError(f"Missing required env: {', '.join(missing)}")
        # At least one VK must be present
        vk_envs = []
        if self.call.virtual_key_env:
            vk_envs.append(self.call.virtual_key_env)
        if self.call.virtual_key_envs:
            vk_envs.extend(self.call.virtual_key_envs)
        if not vk_envs:
            raise ConfigError("No virtual key env(s) configured for model call")
        missing_vk = _require_env(list(dict.fromkeys(vk_envs)))
        if missing_vk:
            # Warn rather than hard-fail; factory may handle fallbacks
            raise ConfigError(f"Missing Portkey VK env(s): {', '.join(missing_vk)}")

    def build_call_spec(self) -> Dict[str, Any]:
        spec: Dict[str, Any] = {
            "provider_model": self.call.model,
            "portkey_api_key": os.getenv(self.api_key_env),
        }
        if self.call.virtual_key_env:
            spec["virtual_key"] = os.getenv(self.call.virtual_key_env)
        if self.call.virtual_key_envs:
            spec["virtual_keys"] = [os.getenv(k) for k in self.call.virtual_key_envs if os.getenv(k)]
        params = {}
        if self.call.max_tokens is not None:
            params["max_tokens"] = self.call.max_tokens
        if self.call.temperature is not None:
            params["temperature"] = self.call.temperature
        if self.call.context_window is not None:
            params["context_window"] = self.call.context_window
        if self.call.extra:
            params.update(self.call.extra)
        spec["params"] = params
        return spec


class ModelFactory:
    """Factory that maps logical model types to Portkey call specs via config/models.yaml"""

    # Map provider namespace to expected VK env var
    PROVIDER_TO_VK_ENV = {
        "openai": "PORTKEY_VK_OPENAI",
        "anthropic": "PORTKEY_VK_ANTHROPIC",
        "openrouter": "PORTKEY_VK_OPENROUTER",
        "google": "PORTKEY_VK_GOOGLE",
        "deepseek": "PORTKEY_VK_DEEPSEEK",
        "qwen": "PORTKEY_VK_QWEN",
        "x-ai": "PORTKEY_VK_XAI",
        "meta": "PORTKEY_VK_META",
        "groq": "PORTKEY_VK_GROQ",
        "perplexity": "PORTKEY_VK_PERPLEXITY",
        "together": "PORTKEY_VK_TOGETHER",
        "moonshotai": "PORTKEY_VK_MOONSHOT",
    }

    def __init__(self, models_yaml: str = MODELS_YAML_PATH, portkey_api_env: str = "PORTKEY_API_KEY"):
        self.models_yaml = models_yaml
        self.portkey_api_env = portkey_api_env
        self._cfg = _load_models_yaml(models_yaml)
        if "model_routing" not in self._cfg:
            raise ConfigError("models.yaml: 'model_routing' not found")

    def _build_from_entry(self, entry_key: str, subkey: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None) -> PortkeyClient:
        mr = self._cfg["model_routing"]
        if entry_key not in mr:
            raise ConfigError(f"models.yaml: '{entry_key}' not found under model_routing")
        entry = mr[entry_key]
        extra: Dict[str, Any] = {}
        model_name: Optional[str] = None
        vk_env: Optional[str] = None
        vk_envs: Optional[List[str]] = None

        if entry_key == "specialized" and subkey:
            # specialized.scout / specialized.maverick
            model_name = entry.get(subkey)
            vk_env = entry.get("virtual_key")
        else:
            model_name = entry.get("primary")
            # support both virtual_key and virtual_keys
            if "virtual_key" in entry:
                vk_env = entry["virtual_key"]
            if "virtual_keys" in entry:
                vk_envs = entry["virtual_keys"]

        if not model_name:
            raise ConfigError(f"models.yaml: model for '{entry_key}' not configured")

        cfg = PortkeyCallConfig(
            model=model_name,
            virtual_key_env=vk_env,
            virtual_key_envs=vk_envs,
            extra={},
        )
        # Optional tunables by category
        if entry_key == "fast_operations":
            cfg.max_tokens = 4096
            cfg.temperature = 0.1
        elif entry_key == "coding":
            cfg.max_tokens = 16384
            cfg.temperature = 0.2
        elif entry_key == "reasoning":
            cfg.max_tokens = 8192
            cfg.temperature = 0.7
        elif entry_key == "advanced_context":
            cfg.max_tokens = 32768
            cfg.temperature = 0.5
            cfg.context_window = entry.get("context_window")

        # Apply explicit overrides
        if overrides:
            for k, v in overrides.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
                else:
                    if cfg.extra is None:
                        cfg.extra = {}
                    cfg.extra[k] = v

        return PortkeyClient(self.portkey_api_env, cfg)

    def create(self, logical_type: str, *, subkey: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None) -> PortkeyClient:
        """Create PortkeyClient for a logical model type.

        Examples:
          create('fast_operations')
          create('specialized', subkey='scout')
        """
        return self._build_from_entry(logical_type, subkey=subkey, overrides=overrides)

    def create_for_model(self, provider_model: str, overrides: Optional[Dict[str, Any]] = None) -> PortkeyClient:
        """Create a PortkeyClient for an explicit provider/model string.

        Attempts to infer the correct VK env var from the provider prefix before '/'.
        """
        if "/" not in provider_model:
            raise ConfigError(f"Invalid provider/model: {provider_model}")
        provider = provider_model.split("/", 1)[0]
        vk_env = self.PROVIDER_TO_VK_ENV.get(provider)
        if not vk_env:
            raise ConfigError(f"No VK env mapping for provider '{provider}'")
        cfg = PortkeyCallConfig(model=provider_model, virtual_key_env=vk_env)
        if overrides:
            for k, v in overrides.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
                else:
                    if cfg.extra is None:
                        cfg.extra = {}
                    cfg.extra[k] = v
        return PortkeyClient(self.portkey_api_env, cfg)


def quick_self_test() -> Dict[str, Any]:
    """Non-network smoke: ensures envs present and config parsable.

    Returns a dict of call specs for primary routes for inspection.
    """
    fac = ModelFactory()
    specs = {}
    for logical in ["fast_operations", "reasoning", "advanced_context", "coding", "general"]:
        try:
            specs[logical] = fac.create(logical).build_call_spec()
        except Exception as e:
            specs[logical] = {"error": str(e)}
    # Specialized
    for sub in ["scout", "maverick"]:
        try:
            specs[f"specialized.{sub}"] = fac.create("specialized", subkey=sub).build_call_spec()
        except Exception as e:
            specs[f"specialized.{sub}"] = {"error": str(e)}
    return specs
