from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List

import httpx


async def check_openai(client: httpx.AsyncClient) -> Dict[str, Any]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return {"provider": "openai", "skipped": True, "reason": "no key"}
    try:
        r = await client.get(
            "https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {key}"}
        )
        ok = r.status_code < 400
        return {"provider": "openai", "ok": ok, "status": r.status_code}
    except Exception as e:
        return {"provider": "openai", "ok": False, "error": str(e)}


async def check_anthropic(client: httpx.AsyncClient) -> Dict[str, Any]:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return {"provider": "anthropic", "skipped": True, "reason": "no key"}
    try:
        # Anthropic has no simple GET; use models list via beta path is not public. Hit usage to validate auth.
        r = await client.get(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
        )
        ok = r.status_code < 400
        return {"provider": "anthropic", "ok": ok, "status": r.status_code}
    except Exception as e:
        return {"provider": "anthropic", "ok": False, "error": str(e)}


async def check_openrouter(client: httpx.AsyncClient) -> Dict[str, Any]:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return {"provider": "openrouter", "skipped": True, "reason": "no key"}
    try:
        r = await client.get(
            "https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {key}"}
        )
        ok = r.status_code < 400
        return {"provider": "openrouter", "ok": ok, "status": r.status_code}
    except Exception as e:
        return {"provider": "openrouter", "ok": False, "error": str(e)}


async def check_groq(client: httpx.AsyncClient) -> Dict[str, Any]:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return {"provider": "groq", "skipped": True, "reason": "no key"}
    try:
        r = await client.get(
            "https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {key}"}
        )
        ok = r.status_code < 400
        return {"provider": "groq", "ok": ok, "status": r.status_code}
    except Exception as e:
        return {"provider": "groq", "ok": False, "error": str(e)}


async def check_perplexity(client: httpx.AsyncClient) -> Dict[str, Any]:
    key = os.getenv("PERPLEXITY_API_KEY")
    if not key:
        return {"provider": "perplexity", "skipped": True, "reason": "no key"}
    try:
        r = await client.get(
            "https://api.perplexity.ai/models", headers={"Authorization": f"Bearer {key}"}
        )
        ok = r.status_code < 400
        return {"provider": "perplexity", "ok": ok, "status": r.status_code}
    except Exception as e:
        return {"provider": "perplexity", "ok": False, "error": str(e)}


async def check_together(client: httpx.AsyncClient) -> Dict[str, Any]:
    key = os.getenv("TOGETHER_AI_API_KEY")
    if not key:
        return {"provider": "together", "skipped": True, "reason": "no key"}
    try:
        r = await client.get(
            "https://api.together.xyz/v1/models", headers={"Authorization": f"Bearer {key}"}
        )
        ok = r.status_code < 400
        return {"provider": "together", "ok": ok, "status": r.status_code}
    except Exception as e:
        return {"provider": "together", "ok": False, "error": str(e)}


async def check_deepseek(client: httpx.AsyncClient) -> Dict[str, Any]:
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        return {"provider": "deepseek", "skipped": True, "reason": "no key"}
    try:
        r = await client.get(
            "https://api.deepseek.com/models", headers={"Authorization": f"Bearer {key}"}
        )
        ok = r.status_code < 400
        return {"provider": "deepseek", "ok": ok, "status": r.status_code}
    except Exception as e:
        return {"provider": "deepseek", "ok": False, "error": str(e)}


async def check_huggingface(client: httpx.AsyncClient) -> Dict[str, Any]:
    key = os.getenv("HUGGINGFACE_API_TOKEN")
    if not key:
        return {"provider": "huggingface", "skipped": True, "reason": "no token"}
    try:
        r = await client.get(
            "https://huggingface.co/api/whoami-v2", headers={"Authorization": f"Bearer {key}"}
        )
        ok = r.status_code < 400
        return {"provider": "huggingface", "ok": ok, "status": r.status_code}
    except Exception as e:
        return {"provider": "huggingface", "ok": False, "error": str(e)}


async def check_gemini(client: httpx.AsyncClient) -> Dict[str, Any]:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return {"provider": "gemini", "skipped": True, "reason": "no key"}
    try:
        r = await client.get(f"https://generativelanguage.googleapis.com/v1/models?key={key}")
        ok = r.status_code < 400
        return {"provider": "gemini", "ok": ok, "status": r.status_code}
    except Exception as e:
        return {"provider": "gemini", "ok": False, "error": str(e)}


async def check_openxai(client: httpx.AsyncClient) -> Dict[str, Any]:
    key = os.getenv("XAI_API_KEY")
    if not key:
        return {"provider": "xai", "skipped": True, "reason": "no key"}
    try:
        # x.ai largely mirrors OpenAI; try /v1/models
        r = await client.get(
            "https://api.x.ai/v1/models", headers={"Authorization": f"Bearer {key}"}
        )
        ok = r.status_code < 400
        return {"provider": "xai", "ok": ok, "status": r.status_code}
    except Exception as e:
        return {"provider": "xai", "ok": False, "error": str(e)}


async def main() -> None:
    providers = [
        check_openai,
        check_anthropic,
        check_openrouter,
        check_groq,
        check_perplexity,
        check_together,
        check_deepseek,
        check_huggingface,
        check_gemini,
        check_openxai,
    ]

    results: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=8) as client:
        for fn in providers:
            try:
                res = await fn(client)
            except Exception as e:
                res = {"provider": getattr(fn, "__name__", "unknown"), "ok": False, "error": str(e)}
            results.append(res)

    # Print as JSON lines for easy parsing
    import json

    for r in results:
        print(json.dumps(r))


if __name__ == "__main__":
    asyncio.run(main())
