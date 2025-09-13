#!/usr/bin/env python3
"""
Grok CLI - Simple, provider-aware CLI for xAI Grok.

Defaults to OpenRouter model `x-ai/grok-code-fast-1` if `OPENROUTER_API_KEY` is set.
If `XAI_API_KEY` (or `GROK_API_KEY`) is set and no OpenRouter key, uses `grok-2-latest` directly.

Reads credentials from ~/.config/sophia/env (via app.core.env.load_env_once).
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from builder_cli.lib.env import load_central_env
from app.core.env import load_env_once
from app.llm.multi_transport import MultiTransportLLM


def infer_provider() -> str:
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"
    if os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY"):
        return "xai"
    return "openrouter"  # prefer OpenRouter; will error if missing


def default_model_for(provider: str) -> str:
    if provider == "xai":
        return "grok-2-latest"
    return "x-ai/grok-code-fast-1"


def build_messages(prompt: str, system: Optional[str]) -> list[dict[str, str]]:
    msgs: list[dict[str, str]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return msgs


def read_input(prompt: Optional[str], file: Optional[str]) -> str:
    data = []
    if prompt:
        data.append(prompt)
    if file:
        p = Path(file)
        if not p.exists():
            print(f"Error: file not found: {file}", file=sys.stderr)
            sys.exit(2)
        data.append(p.read_text())
    if not data:
        print("Error: provide --prompt or --file", file=sys.stderr)
        sys.exit(2)
    return "\n\n".join(data)


def main() -> None:
    # Load central unified env first (e.g., .env.local.unified or ~/.config/sophia/env),
    # then project/local fallbacks.
    try:
        load_central_env()
    except Exception:
        pass
    load_env_once()
    ap = argparse.ArgumentParser(description="Grok CLI (xAI via OpenRouter or direct)")
    ap.add_argument("--prompt", "-p", help="Prompt text")
    ap.add_argument("--file", "-f", help="Read prompt from file")
    ap.add_argument("--system", "-s", help="System instruction")
    ap.add_argument("--provider", choices=["openrouter", "xai"], default=None)
    ap.add_argument("--model", help="Model ID override")
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--dry-run", action="store_true", help="Print plan; skip network call")
    ap.add_argument("--json", action="store_true", help="Output raw JSON response")

    args = ap.parse_args()

    provider = args.provider or infer_provider()
    model = args.model or default_model_for(provider)
    prompt = read_input(args.prompt, args.file)
    messages = build_messages(prompt, args.system)

    if args.dry_run:
        print("Grok CLI dry-run:")
        print(f"  provider: {provider}")
        print(f"  model:    {model}")
        print(f"  temp:     {args.temperature}")
        print(f"  max_tok:  {args.max_tokens}")
        preview = (prompt[:160] + ("…" if len(prompt) > 160 else ""))
        print(f"  prompt:   {preview}")
        sys.exit(0)

    llm = MultiTransportLLM()
    # If Portkey VK for xai/openrouter is set, MultiTransport will use it automatically
    try:
        resp = asyncio_run_complete(
            llm, provider, model, messages, args.max_tokens, args.temperature
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        import json as _json
        print(_json.dumps(resp.raw, indent=2))
    else:
        print(resp.text)


def asyncio_run_complete(llm: MultiTransportLLM, provider: str, model: str,
                         messages: list[dict[str, str]], max_tokens: int, temperature: float):
    import asyncio
    async def _go():
        return await llm.complete(
            provider=provider,
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    try:
        return asyncio.run(_go())
    except RuntimeError:
        raise


if __name__ == "__main__":
    main()
