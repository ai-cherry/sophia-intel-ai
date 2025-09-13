"""
Opus 4.1 Chat Router - Portkey-only routing

All runtime LLM calls must route through Portkey with Virtual Keys (VKs).
Direct provider calls (OpenRouter/Anthropic/OpenAI/x.ai) are forbidden.
"""
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from models.roles import verify_permissions
from pydantic import BaseModel, Field
from services.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.core.portkey_manager import PortkeyManager
router = APIRouter(prefix="/api/chat", tags=["opus-chat"])
# Configuration
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")

# Circuit breaker for Portkey
portkey_breaker = CircuitBreaker(
    name="portkey",
    config=CircuitBreakerConfig(
        failure_threshold=3, recovery_timeout=30, expected_exception=httpx.HTTPError
    ),
)

# Portkey manager (central VK routing)
_pk_manager = PortkeyManager()
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
class OpusConfig(BaseModel):
    model: str = Field(
        default="anthropic/claude-opus-4-1-20250805", description="Model identifier"
    )
    provider: str = Field(
        default="portkey", description="Provider family (parsed from model prefix)"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Temperature for response generation"
    )
    max_tokens: int = Field(
        default=4096, ge=1, le=8192, description="Maximum tokens in response"
    )
    requirements: Optional[Dict[str, str]] = Field(
        default=None, description="Task-specific requirements"
    )
class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    config: OpusConfig = Field(
        default_factory=OpusConfig, description="Model configuration"
    )
    stream: bool = Field(default=False, description="Enable streaming response")
class ChatResponse(BaseModel):
    content: str = Field(..., description="Generated response content")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")
    usage: Dict[str, Any] = Field(..., description="Token usage and cost information")
class UsageStats(BaseModel):
    requests_today: int = 0
    tokens_used: int = 0
    cost_today: float = 0.0
    average_response_time: float = 0.0
# In-memory usage tracking (in production, use Redis or database)
usage_stats = UsageStats()
daily_reset_time = datetime.now().date()
def reset_daily_stats():
    """Reset daily statistics if it's a new day"""
    global usage_stats, daily_reset_time
    today = datetime.now().date()
    if today > daily_reset_time:
        usage_stats = UsageStats()
        daily_reset_time = today
def calculate_cost(
    provider: str, model: str, input_tokens: int, output_tokens: int
) -> float:
    """Calculate cost based on provider and model"""
    # Pricing per 1K tokens (approximate)
    pricing = {
        "openrouter": {
            "anthropic/claude-opus-4-1-20250805": {"input": 0.015, "output": 0.075}
        },
        "anthropic": {"claude-opus-4-1-20250805": {"input": 0.015, "output": 0.075}},
        "portkey": {
            "anthropic/claude-opus-4-1-20250805": {
                "input": 0.016,
                "output": 0.080,
            }  # Slightly higher for routing
        },
    }
    model_pricing = pricing.get(provider, {}).get(
        model, {"input": 0.015, "output": 0.075}
    )
    input_cost = (input_tokens / 1000) * model_pricing["input"]
    output_cost = (output_tokens / 1000) * model_pricing["output"]
    return input_cost + output_cost
async def call_openrouter(messages: List[Dict], config: OpusConfig) -> Dict[str, Any]:
    """Direct OpenRouter calls are disabled; route via Portkey."""
    raise HTTPException(status_code=410, detail="Direct OpenRouter calls are disabled; route via Portkey")
async def call_anthropic_direct(messages: List[Dict], config: OpusConfig) -> Dict[str, Any]:
    """Direct Anthropic calls are disabled; route via Portkey."""
    raise HTTPException(status_code=410, detail="Direct Anthropic calls are disabled; route via Portkey")
async def call_portkey(messages: List[Dict], config: OpusConfig) -> Dict[str, Any]:
    """Call model via Portkey Gateway using VK routing."""
    if not PORTKEY_API_KEY:
        raise HTTPException(status_code=500, detail="Portkey API key not configured")

    # Infer provider from model prefix if available (e.g., "anthropic/claude-...")
    provider = config.provider
    if "/" in config.model:
        provider = config.model.split("/", 1)[0]

    # Resolve VK for provider via PortkeyManager (falls back to env)
    vk = _pk_manager.VIRTUAL_KEYS.get(provider) or os.getenv(
        f"PORTKEY_VK_{provider.upper()}", ""
    )

    headers = {
        "Authorization": f"Bearer {PORTKEY_API_KEY}",
        "Content-Type": "application/json",
        "x-portkey-provider": provider,
        "x-portkey-virtual-key": vk,
        "x-portkey-trace-id": f"sophia-{int(time.time())}",
    }
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }
    # Task-specific adjustments
    if config.requirements and config.requirements.get("taskType") == "coding":
        payload["temperature"] = min(config.temperature, 0.3)

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.portkey.ai/v1/chat/completions", headers=headers, json=payload
        )
        response.raise_for_status()
        return response.json()
@router.post("/opus", response_model=ChatResponse)
async def chat_with_opus(
    request: ChatRequest,
    http_request: Request,
    user_permissions: dict = Depends(verify_permissions),
):
    """
    Chat with Claude Opus 4.1 via multiple providers with intelligent routing
    """
    reset_daily_stats()
    start_time = time.time()
    # Verify permissions
    if not user_permissions.get("chat", False):
        raise HTTPException(status_code=403, detail="Chat permission required")
    # Convert messages to API format
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    # Portkey-only execution with circuit breaker
    last_error = None
    try:
        if portkey_breaker.can_execute():
            with portkey_breaker:
                result = await call_portkey(messages, request.config)
        else:
            raise HTTPException(status_code=503, detail="Portkey temporarily unavailable")
    except Exception as e:
        last_error = e
        raise HTTPException(
            status_code=503, detail=f"Provider unavailable via Portkey: {str(last_error)}"
        )
    # Extract response content
    if "choices" in result and result["choices"]:
        content = result["choices"][0]["message"]["content"]
    else:
        raise HTTPException(
            status_code=500, detail="Invalid response format from provider"
        )
    # Calculate metrics
    response_time = time.time() - start_time
    usage_data = result.get("usage", {})
    input_tokens = usage_data.get("prompt_tokens", 0)
    output_tokens = usage_data.get("completion_tokens", 0)
    total_tokens = input_tokens + output_tokens
    # Calculate cost (Portkey as the routing provider)
    provider = "portkey"
    cost = calculate_cost(provider, request.config.model, input_tokens, output_tokens)
    # Update usage stats
    usage_stats.requests_today += 1
    usage_stats.tokens_used += total_tokens
    usage_stats.cost_today += cost
    usage_stats.average_response_time = (
        usage_stats.average_response_time * (usage_stats.requests_today - 1)
        + response_time
    ) / usage_stats.requests_today
    # Prepare response
    response_data = ChatResponse(
        content=content,
        metadata={
            "model": request.config.model,
            "provider": provider,
            "tokens": total_tokens,
            "cost": cost,
            "responseTime": response_time,
        },
        usage={
            "promptTokens": input_tokens,
            "completionTokens": output_tokens,
            "totalTokens": total_tokens,
            "cost": cost,
        },
    )
    return response_data
@router.get("/usage")
async def get_usage_stats(user_permissions: dict = Depends(verify_permissions)):
    """Get current usage statistics"""
    if not user_permissions.get("analytics", False):
        raise HTTPException(status_code=403, detail="Analytics permission required")
    reset_daily_stats()
    return usage_stats
@router.get("/providers/status")
async def get_provider_status():
    """Get status of all providers"""
    return {
        "portkey": {
            "available": portkey_breaker.can_execute(),
            "failures": portkey_breaker.failure_count,
            "last_failure": portkey_breaker.last_failure_time,
        }
    }
@router.post("/test")
async def sophia_opus_integration():
    """Test endpoint for Opus 4.1 integration"""
    sophia_request = ChatRequest(
        messages=[
            ChatMessage(
                role="user",
                content="Hello! Please respond with 'Opus 4.1 integration working perfectly!'",
            )
        ],
        config=OpusConfig(provider="portkey"),
    )
    try:
        # Mock request object
        class MockRequest:
            def __init__(self):
                self.client = type("obj", (object,), {"host": "${LOCALHOST_IP}"})()
        # Mock permissions
        actual_permissions = {"chat": True, "analytics": True}
        response = await chat_with_opus(
            sophia_request, MockRequest(), actual_permissions
        )
        return {
            "status": "success",
            "message": "Opus 4.1 integration test completed",
            "response": (
                response.content[:100] + "..."
                if len(response.content) > 100
                else response.content
            ),
            "provider": response.metadata["provider"],
            "cost": response.metadata["cost"],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Opus 4.1 integration test failed: {str(e)}",
        }
