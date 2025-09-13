#!/usr/bin/env python3
"""
DeepSeek CLI - Handy CLI for DeepSeek via OpenRouter or direct API.

Defaults to OpenRouter model `deepseek/deepseek-chat-v3.1` if `OPENROUTER_API_KEY` is set.
If `DEEPSEEK_API_KEY` is set and no OpenRouter key, uses `deepseek-chat` directly.

Environment: expects repo-local .env.master loaded by ./sophia. If run standalone,
will attempt a silent load via agents.load_env.load_master_env (no prompts).
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from typing import Optional

try:
    # Optional: load repo-local .env.master when run standalone
    from agents.load_env import load_master_env  # type: ignore
    try:
        load_master_env()
    except Exception:
        pass
except Exception:
    pass
from app.llm.multi_transport import MultiTransportLLM


def infer_provider() -> str:
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    return "openrouter"  # prefer OpenRouter; will error if missing


def default_model_for(provider: str, reasoning: bool) -> str:
    if provider == "deepseek":
        return "deepseek-reasoner" if reasoning else "deepseek-chat"
    # OpenRouter IDs
    return "deepseek/deepseek-r1" if reasoning else "deepseek/deepseek-chat-v3.1"


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
    # Environment is expected to be inherited from ./sophia start.
    # If run standalone, the optional import above attempted a silent load.
    ap = argparse.ArgumentParser(description="DeepSeek CLI (via OpenRouter or direct)")
    ap.add_argument("--prompt", "-p", help="Prompt text")
    ap.add_argument("--file", "-f", help="Read prompt from file")
    ap.add_argument("--system", "-s", help="System instruction")
    ap.add_argument("--provider", choices=["openrouter", "deepseek"], default=None)
    ap.add_argument("--model", help="Model ID override")
    ap.add_argument("--reasoning", "--r1", action="store_true", help="Use reasoning model (DeepSeek-R1)")
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--dry-run", action="store_true", help="Print plan; skip network call")
    ap.add_argument("--json", action="store_true", help="Output raw JSON response")

    args = ap.parse_args()

    provider = args.provider or infer_provider()
    model = args.model or default_model_for(provider, args.reasoning)
    prompt = read_input(args.prompt, args.file)
    messages = build_messages(prompt, args.system)

    if args.dry_run:
        print("DeepSeek CLI dry-run:")
        print(f"  provider: {provider}")
        print(f"  model:    {model}")
        print(f"  temp:     {args.temperature}")
        print(f"  max_tok:  {args.max_tokens}")
        preview = (prompt[:160] + ("…" if len(prompt) > 160 else ""))
        print(f"  prompt:   {preview}")
        sys.exit(0)

    llm = MultiTransportLLM()
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
