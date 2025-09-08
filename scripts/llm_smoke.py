from __future__ import annotations

import argparse
import asyncio
import json
import os

import httpx

from app.core.portkey_manager import PortkeyManager


async def run_portkey(
    provider: str,
    model: str,
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.0,
):
    pm = PortkeyManager()
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": prompt},
    ]
    resp = await pm.execute_manual(
        provider=provider,
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    # Print minimal JSON summary
    out = {
        "provider": provider,
        "model": model,
        "text": resp.choices[0].message.content[:400],
        "usage": getattr(resp, "usage", None)
        and {
            k: getattr(resp.usage, k, None)
            for k in ("prompt_tokens", "completion_tokens", "total_tokens")
        },
    }
    print(json.dumps(out, ensure_ascii=False))


async def run_openrouter_direct(
    model: str, prompt: str, max_tokens: int = 256, temperature: float = 0.0
):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        out = {
            "provider": "openrouter-direct",
            "model": model,
            "text": data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")[:400],
            "raw_status": r.status_code,
        }
        print(json.dumps(out, ensure_ascii=False))


async def run_groq_direct(
    model: str, prompt: str, max_tokens: int = 256, temperature: float = 0.0
):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        out = {
            "provider": "groq-direct",
            "model": model,
            "text": data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")[:400],
            "raw_status": r.status_code,
        }
        print(json.dumps(out, ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser(description="LLM smoke test (manual, no fallbacks)")
    ap.add_argument(
        "--provider",
        help="Portkey provider key (e.g., openai, anthropic, groq, openrouter, xai)",
    )
    ap.add_argument(
        "--transport",
        default="portkey",
        choices=["portkey", "openrouter-direct", "groq-direct"],
        help="Transport to use",
    )
    ap.add_argument(
        "--model", required=True, help="Exact model id for provider/transport"
    )
    ap.add_argument("--prompt", required=False, default="Say 'ready' if online.")
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--temperature", type=float, default=0.0)
    args = ap.parse_args()

    if args.transport == "portkey":
        if not args.provider:
            raise SystemExit("--provider is required for portkey transport")
        asyncio.run(
            run_portkey(
                args.provider,
                args.model,
                args.prompt,
                args.max_tokens,
                args.temperature,
            )
        )
    elif args.transport == "openrouter-direct":
        asyncio.run(
            run_openrouter_direct(
                args.model, args.prompt, args.max_tokens, args.temperature
            )
        )
    elif args.transport == "groq-direct":
        asyncio.run(
            run_groq_direct(args.model, args.prompt, args.max_tokens, args.temperature)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
