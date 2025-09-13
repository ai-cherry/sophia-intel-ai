"""
Multi-transport LLM client supporting direct providers and aggregators.
Manual-only mode: no automatic fallbacks or model selection.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any
import httpx
@dataclass
class LLMResponse:
    text: str
    usage: dict[str, int]
    model: str
    provider: str
    raw: Any = None
class MultiTransportLLM:
    """
    Manual LLM client supporting multiple transports.
    No automatic fallback - requires explicit provider/model selection.
    """
    def __init__(self):
        # Load all available keys
        self.keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "together": os.getenv("TOGETHER_AI_API_KEY"),
            "groq": os.getenv("GROQ_API_KEY"),
            "xai": os.getenv("XAI_API_KEY"),
            "deepseek": os.getenv("DEEPSEEK_API_KEY"),
            "perplexity": os.getenv("PERPLEXITY_API_KEY"),
            "aimlapi": os.getenv("AIMLAPI_API_KEY"),
            "portkey": os.getenv("PORTKEY_API_KEY"),
        }
        # Compatibility: allow GROK_API_KEY as alias for XAI_API_KEY
        if not self.keys.get("xai"):
            alias = os.getenv("GROK_API_KEY")
            if alias:
                self.keys["xai"] = alias
        # Portkey virtual keys
        self.portkey_vks = {
            "perplexity": os.getenv("PORTKEY_VK_PERPLEXITY"),
            "groq": os.getenv("PORTKEY_VK_GROQ"),
            "anthropic": os.getenv("PORTKEY_VK_ANTHROPIC"),
            "deepseek": os.getenv("PORTKEY_VK_DEEPSEEK"),
            "openai": os.getenv("PORTKEY_VK_OPENAI"),
            "xai": os.getenv("PORTKEY_VK_XAI"),
            "openrouter": os.getenv("PORTKEY_VK_OPENROUTER"),
            "together": os.getenv("PORTKEY_VK_TOGETHER"),
        }
    async def complete(
        self,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int = 256,
        temperature: float = 0.0,
        transport: str | None = None,
    ) -> LLMResponse:
        """
        Execute completion with explicit provider/model.
        Args:
            provider: Provider name (openai, anthropic, openrouter, etc.)
            model: Exact model ID for that provider
            messages: Chat messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            transport: Optional transport override (portkey, direct, etc.)
        Returns:
            LLMResponse with text and metadata
        Raises:
            RuntimeError: If provider/model combination is invalid or keys missing
        """
        # Determine transport
        if transport is None:
            # Check if we can use Portkey for this provider
            if provider in self.portkey_vks and self.portkey_vks[provider]:
                transport = "portkey"
            else:
                transport = "direct"
        if transport == "portkey":
            return await self._complete_portkey(
                provider, model, messages, max_tokens, temperature
            )
        elif transport == "direct":
            return await self._complete_direct(
                provider, model, messages, max_tokens, temperature
            )
        else:
            raise ValueError(f"Unknown transport: {transport}")
    async def _complete_portkey(
        self,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Complete via Portkey using virtual keys."""
        if not self.keys.get("portkey"):
            raise RuntimeError("PORTKEY_API_KEY not set")
        vk = self.portkey_vks.get(provider)
        if not vk:
            raise RuntimeError(f"No Portkey virtual key for provider: {provider}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.portkey.ai/v1/chat/completions",
                headers={
                    "x-portkey-api-key": self.keys["portkey"],
                    "x-portkey-virtual-key": vk,
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model=model,
                provider=f"portkey/{provider}",
                raw=data,
            )
    async def _complete_direct(
        self,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Complete via direct provider APIs."""
        if provider == "openai":
            return await self._complete_openai(model, messages, max_tokens, temperature)
        elif provider == "anthropic":
            return await self._complete_anthropic(
                model, messages, max_tokens, temperature
            )
        elif provider == "openrouter":
            return await self._complete_openrouter(
                model, messages, max_tokens, temperature
            )
        elif provider == "together":
            return await self._complete_together(
                model, messages, max_tokens, temperature
            )
        elif provider == "groq":
            return await self._complete_groq(model, messages, max_tokens, temperature)
        elif provider == "xai":
            return await self._complete_xai(model, messages, max_tokens, temperature)
        elif provider == "deepseek":
            return await self._complete_deepseek(
                model, messages, max_tokens, temperature
            )
        elif provider == "perplexity":
            return await self._complete_perplexity(
                model, messages, max_tokens, temperature
            )
        elif provider == "aimlapi":
            return await self._complete_aimlapi(
                model, messages, max_tokens, temperature
            )
        else:
            raise ValueError(f"Unknown provider for direct transport: {provider}")
    async def _complete_openai(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """OpenAI direct completion."""
        if not self.keys.get("openai"):
            raise RuntimeError("OPENAI_API_KEY not set")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.keys['openai']}"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model=model,
                provider="openai",
                raw=data,
            )
    async def _complete_anthropic(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Anthropic direct completion."""
        if not self.keys.get("anthropic"):
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        # Convert messages to Anthropic format
        system_message = None
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)
        async with httpx.AsyncClient() as client:
            request_body = {
                "model": model,
                "messages": user_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if system_message:
                request_body["system"] = system_message
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.keys["anthropic"],
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=request_body,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            # Extract text from Anthropic's response format
            text = ""
            if "content" in data:
                for block in data["content"]:
                    if block.get("type") == "text":
                        text += block.get("text", "")
            return LLMResponse(
                text=text,
                usage={
                    "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                    "output_tokens": data.get("usage", {}).get("output_tokens", 0),
                },
                model=model,
                provider="anthropic",
                raw=data,
            )
    async def _complete_openrouter(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """OpenRouter completion."""
        if not self.keys.get("openrouter"):
            raise RuntimeError("OPENROUTER_API_KEY not set")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.keys['openrouter']}",
                    "HTTP-Referer": "https://github.com/sophia-intel-ai",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model=model,
                provider="openrouter",
                raw=data,
            )
    async def _complete_together(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Together AI completion."""
        if not self.keys.get("together"):
            raise RuntimeError("TOGETHER_AI_API_KEY not set")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.keys['together']}"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model=model,
                provider="together",
                raw=data,
            )
    async def _complete_groq(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Groq completion."""
        if not self.keys.get("groq"):
            raise RuntimeError("GROQ_API_KEY not set")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.keys['groq']}"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model=model,
                provider="groq",
                raw=data,
            )
    async def _complete_xai(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """X.AI (Grok) completion."""
        if not self.keys.get("xai"):
            raise RuntimeError("XAI_API_KEY not set")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.keys['xai']}"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model=model,
                provider="xai",
                raw=data,
            )
    async def _complete_deepseek(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """DeepSeek completion."""
        if not self.keys.get("deepseek"):
            raise RuntimeError("DEEPSEEK_API_KEY not set")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.keys['deepseek']}"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model=model,
                provider="deepseek",
                raw=data,
            )
    async def _complete_perplexity(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Perplexity completion."""
        if not self.keys.get("perplexity"):
            raise RuntimeError("PERPLEXITY_API_KEY not set")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {self.keys['perplexity']}"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model=model,
                provider="perplexity",
                raw=data,
            )
    async def _complete_aimlapi(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """AIMLAPI completion (OpenRouter-like)."""
        if not self.keys.get("aimlapi"):
            raise RuntimeError("AIMLAPI_API_KEY not set")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.aimlapi.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.keys['aimlapi']}"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model=model,
                provider="aimlapi",
                raw=data,
            )
