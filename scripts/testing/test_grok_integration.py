#!/usr/bin/env python3
"""
Test Grok integration via unified CLI transport.
Usage:
  python3 scripts/test_grok_integration.py --task "Hello" [--provider xai|openrouter]
Requires XAI_API_KEY or OPENROUTER_API_KEY in the environment.
"""
import argparse
import asyncio
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
from app.llm.multi_transport import MultiTransportLLM
def load_env():
    root = Path(__file__).resolve().parents[1]
    env = root / ".env"
    if load_dotenv and env.exists():
        load_dotenv(dotenv_path=env)
async def run(task: str, provider: str | None):
    llm = MultiTransportLLM()
    prov = provider
    model = "x-ai/grok-code-fast-1"
    if not prov:
        prov = (
            "xai"
            if os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
            else "openrouter"
        )
    print(f"Provider: {prov}\nModel: {model}")
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": task},
    ]
    resp = await llm.complete(
        provider=prov, model=model, messages=messages, max_tokens=256, temperature=0.2
    )
    print("\n=== Response ===\n")
    print(resp.text)
def main():
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--provider", choices=["xai", "openrouter"], default=None)
    args = ap.parse_args()
    asyncio.run(run(args.task, args.provider))
if __name__ == "__main__":
    main()
