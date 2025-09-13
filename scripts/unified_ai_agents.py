#!/usr/bin/env python3
"""
Unified AI Agents CLI
Single entrypoint for Grok, Claude Coder, and Codex using a shared environment.
"""
import argparse
import asyncio
import os
from pathlib import Path
from typing import Dict, Tuple
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
from app.llm.multi_transport import MultiTransportLLM
from app.llm.provider_router import EnhancedProviderRouter
def load_env() -> None:
    # Preferred: secure env file mounted from host (read-only)
    secure_env = os.getenv("AGENT_ENV_FILE") or os.getenv("_ENV_FILE")
    if load_dotenv and secure_env and Path(secure_env).exists():
        load_dotenv(dotenv_path=secure_env, override=True)
        return
    # Fallback: .env in repo root (for local quick tests only)
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    if load_dotenv and env_path.exists():
        load_dotenv(dotenv_path=env_path)
def pick_model(agent: str, mode: str, keys: Dict[str, str]) -> Tuple[str, str]:
    """Return (provider, model) based on agent/mode and available keys.
    Preference order: openrouter (broad coverage) -> provider-native.
    """
    has_or = bool(keys.get("openrouter"))
    agent = agent.lower()
    mode = mode.lower()
    if agent == "grok":
        if mode == "code":
            return ("openrouter" if has_or else "xai", "x-ai/grok-code-fast-1")
        else:
            return ("openrouter" if has_or else "xai", "x-ai/grok-4")
    if agent == "claude":
        # Prefer Sonnet-4 style identifiers which exist in repo configs
        model = "anthropic/claude-sonnet-4"
        return ("openrouter" if has_or else "anthropic", model)
    if agent == "codex":
        # Use a strong coder model via OpenRouter as a stand-in
        if mode == "code":
            return ("openrouter" if has_or else "together", "qwen/qwen3-coder")
        else:
            # Balanced chat fallback
            return (
                "openrouter" if has_or else "anthropic",
                "anthropic/claude-3.5-sonnet-20241022",
            )
    # Default fallback
    return (
        "openrouter" if has_or else "anthropic",
        "anthropic/claude-3.5-sonnet-20241022",
    )
def summarize_env(llm: MultiTransportLLM) -> str:
    lines = []
    lines.append("Environment summary:")
    for k in [
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "XAI_API_KEY",
        "PORTKEY_API_KEY",
    ]:
        present = "set" if os.getenv(k) else "missing"
        lines.append(f"  - {k}: {present}")
    # MCP
    port = os.getenv("MCP_MEMORY_PORT", "8001")
    lines.append(f"  - MCP memory port: {port}")
    return "\n".join(lines)
async def run_task(
    agent: str,
    mode: str,
    task: str,
    dry_run: bool = False,
    provider_override: str | None = None,
    task_type: str | None = None,
    model_override: str | None = None,
) -> None:
    llm = MultiTransportLLM()
    router = EnhancedProviderRouter()
    # Resolve task type
    tt = task_type or ("generation" if mode == "code" else "planning")
    # Dry-run: show route selection only
    if dry_run:
        r = router._route_for(tt)
        provider = provider_override or r.provider
        model = model_override or r.model
        print(
            f"Agent: {agent}\nMode: {mode}\nTask-Type: {tt}\nProvider: {provider}\nModel: {model}"
        )
        print(summarize_env(llm))
        return
    messages = [
        {"role": "system", "content": f"You are a helpful {agent} {mode} assistant."},
        {"role": "user", "content": task},
    ]
    try:
        text = await router.complete(
            task_type=tt,
            messages=messages,
            provider_override=provider_override,
            model_override=model_override,
        )
        print("\n==== Result ====")
        print(text)
    except Exception as e:
        print(f"Error executing request: {e}")
def main():
    load_env()
    parser = argparse.ArgumentParser(description="Unified AI Agents CLI")
    parser.add_argument(
        "--agent", choices=["grok", "claude", "codex"], required=False, default="grok"
    )
    parser.add_argument("--mode", choices=["chat", "code"], default="chat")
    parser.add_argument("--task", type=str, help="Task instruction text")
    parser.add_argument(
        "--file", type=str, help="Optional file path for context", default=None
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print configuration without calling LLM"
    )
    parser.add_argument(
        "--whoami", action="store_true", help="Show environment and routing info"
    )
    parser.add_argument(
        "--provider",
        choices=["xai", "openrouter", "anthropic", "openai", "groq", "aimlapi"],
        help="Force provider override",
    )
    parser.add_argument(
        "--model", type=str, help="Force model override (e.g., x-ai/grok-code-fast-1)"
    )
    parser.add_argument(
        "--task-type",
        choices=["planning", "generation", "validation", "indexing", "vision"],
        help="Task type for router selection",
    )
    args = parser.parse_args()
    if args.whoami:
        llm = MultiTransportLLM()
        print(summarize_env(llm))
        return
    if not args.task and not args.dry_run:
        print("--task is required unless --dry-run or --whoami is used")
        return
    asyncio.run(
        run_task(
            args.agent,
            args.mode,
            args.task or "",
            args.dry_run,
            args.provider,
            args.task_type,
            args.model,
        )
    )
if __name__ == "__main__":
    main()
