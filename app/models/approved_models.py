from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class ApprovedModels:
    models_by_provider: dict[str, set[str]]
    aliases: dict[str, str]
    def is_approved(self, provider: str, model: str) -> bool:
        p = (provider or "").strip().lower()
        m = (model or "").strip()
        # Normalize known alias forms (e.g., anthropic/claude-4.1-sonnet vs anthropic/claude-sonnet-4.1)
        key = f"{p}/{m}"
        if key in self.aliases:
            m = self.aliases[key].split("/", 1)[1]
        # Allow fully-qualified or provider-agnostic checks
        if p in self.models_by_provider and m in self.models_by_provider[p]:
            return True
        # Sometimes callers pass fully-qualified model in 'model' and omit provider
        for prov, models in self.models_by_provider.items():
            if m in models:
                return True
            # Handle callers using fully qualified id in 'model'
            if f"{prov}/{m}" in {
                f"{pp}/{mm}" for pp, ms in self.models_by_provider.items() for mm in ms
            }:
                return True
        return False
# Centralized approved model list (expand only with owner approval)
APPROVED = ApprovedModels(
    models_by_provider={
        # OpenRouter-hosted families
        "openrouter": {
            "openrouter/sonoma-sky-alpha",
            "deepseek/deepseek-coder",
            "deepseek/deepseek-chat-v3.1",
            "qwen/qwq-32b-preview",
            "meta-llama/llama-3.3-70b-instruct",
            "mistralai/mistral-large-2411",
            "google/gemini-2.0-flash",
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "amazon/nova-pro-v1",
            "google/gemini-flash-1.5-8b",
            "google/gemini-pro-1.5",
            "moonshotai/kimi-k2-0905",
            "qwen/qwen-2.5-coder-32b-instruct",
        },
        # Qwen
        "qwen": {
            "qwen3-max",
            "qwen3-coder",
            "qwen3-30b-a3b-thinking-2507",
            "qwq-32b-preview",
            "qwen-2.5-coder-32b-instruct",
        },
        # Moonshot
        "moonshotai": {
            "kimi-k2-0905",
        },
        # DeepSeek
        "deepseek": {
            "deepseek-chat-v3-0324",
            "deepseek-chat-v3.1",
            "deepseek-coder",
        },
        # X.AI (Grok)
        "x-ai": {
            "grok-code-fast-1",
        },
        # OpenAI
        "openai": {
            "gpt-4.1-mini",
            "gpt-5-mini",
            "gpt-5",
            "gpt-4o",
            "gpt-4o-mini",
            "text-embedding-3-large",
        },
        # Anthropic
        "anthropic": {
            "claude-4.1-opus",
            "claude-4.1-sonnet",
            "claude-3-opus-20240229",
            "claude-3.5-sonnet-20241022",
            "claude-3-haiku",
        },
        # Groq (fast lint/checks) – model id to be set explicitly by owner
        "groq": {
            # Add explicit ids as approved when selected, e.g., "llama-3.1-8b-instant"
        },
    },
    aliases={
        # Normalize common naming variants to canonical forms
        "anthropic/claude-opus-4.1": "anthropic/claude-4.1-opus",
        "anthropic/claude-sonnet-4": "anthropic/claude-4.1-sonnet",
        "deepseek/deepseek-chat-v3-1": "deepseek/deepseek-chat-v3.1",
        # OpenRouter fully-qualified ids mapping to provider-native ids
        "openrouter/qwen/qwen3-coder": "qwen/qwen3-coder",
        "openrouter/deepseek/deepseek-chat-v3-0324": "deepseek/deepseek-chat-v3-0324",
    },
)
def is_model_approved(provider: str, model: str) -> bool:
    return APPROVED.is_approved(provider, model)
def list_approved() -> dict[str, set[str]]:
    return APPROVED.models_by_provider
