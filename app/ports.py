"""
Centralized Portkey client management for slim-agno.
All LLM and embedding calls route through Portkey gateway with observability.
Enhanced with role-based routing, caching, and quality gates.
"""

import os
from typing import List, Dict, Any, Optional, Literal
from openai import OpenAI, AsyncOpenAI
from app import settings
from app.portkey_config import (
    PortkeyGateway, Role, ObservabilityHeaders,
    LoadBalanceStrategy, FallbackStrategy, ABTestStrategy,
    MODEL_RECOMMENDATIONS
)

# ============================================
# Enhanced Gateway Instance
# ============================================

# Initialize the enhanced Portkey gateway
gateway = PortkeyGateway()

# Legacy clients for backward compatibility
CHAT = gateway.chat_client
ASYNC_CHAT = gateway.async_chat_client
EMBED = gateway.embed_client
ASYNC_EMBED = gateway.async_embed_client

def chat(
    messages: List[Dict[str, str]], 
    model: str = "openai/gpt-4o",
    system: Optional[str] = None,
    temperature: float = 0.7,
    role: Optional[Role] = None,
    swarm: Optional[str] = None,
    ticket_id: Optional[str] = None,
    use_fallback: bool = False,
    **kwargs
) -> str:
    """
    Enhanced synchronous chat completion via Portkey → OpenRouter.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: OpenRouter model ID (e.g., "openai/gpt-4o", "anthropic/claude-3.5-sonnet")
        system: Optional system message to prepend
        temperature: Sampling temperature (auto-adjusted by role)
        role: Agent role for tracking and optimization
        swarm: Swarm identifier for observability
        ticket_id: Task/ticket identifier
        use_fallback: Enable automatic fallback on failure
        **kwargs: Additional parameters for the completion
    
    Returns:
        The assistant's response content
    """
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)
    
    # Use fallback strategy if requested
    routing_strategy = None
    if use_fallback:
        routing_strategy = FallbackStrategy([
            {"virtual_key": "@openrouter-prod-vk", "override_params": {"model": model}},
            {"virtual_key": "@openrouter-prod-vk", "override_params": {"model": "openai/gpt-4o"}},
            {"virtual_key": "@openrouter-prod-vk", "override_params": {"model": "anthropic/claude-3.5-sonnet"}}
        ])
    
    # Use enhanced gateway with observability
    return gateway.chat(
        messages=msgs,
        model=model,
        temperature=temperature,
        role=role,
        swarm=swarm,
        ticket_id=ticket_id,
        routing_strategy=routing_strategy,
        **kwargs
    )

async def async_chat(
    messages: List[Dict[str, str]], 
    model: str = "openai/gpt-4o",
    system: Optional[str] = None,
    temperature: float = 0.7,
    role: Optional[Role] = None,
    swarm: Optional[str] = None,
    ticket_id: Optional[str] = None,
    stream: bool = False,
    use_fallback: bool = False,
    **kwargs
):
    """
    Enhanced asynchronous chat completion via Portkey → OpenRouter.
    Supports streaming and automatic fallback.
    """
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)
    
    # Use fallback strategy if requested
    routing_strategy = None
    if use_fallback:
        routing_strategy = FallbackStrategy([
            {"virtual_key": "@openrouter-prod-vk", "override_params": {"model": model}},
            {"virtual_key": "@openrouter-prod-vk", "override_params": {"model": "openai/gpt-4o"}},
            {"virtual_key": "@openrouter-prod-vk", "override_params": {"model": "anthropic/claude-3.5-sonnet"}}
        ])
    
    # Use enhanced gateway
    return await gateway.achat(
        messages=msgs,
        model=model,
        temperature=temperature,
        role=role,
        swarm=swarm,
        ticket_id=ticket_id,
        routing_strategy=routing_strategy,
        stream=stream,
        **kwargs
    )

def chat_with_tools(
    messages: List[Dict[str, str]],
    tools: List[Dict[str, Any]],
    model: str = "openai/gpt-4o",
    tool_choice: str = "auto",
    **kwargs
) -> Any:
    """
    Chat completion with tool calling support.
    
    Args:
        messages: Conversation history
        tools: List of tool definitions (OpenAI format)
        model: OpenRouter model ID
        tool_choice: How to choose tools ("auto", "none", or specific tool)
        **kwargs: Additional parameters
    
    Returns:
        Full response object (includes tool calls if any)
    """
    response = CHAT.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        extra_headers={
            "HTTP-Referer": settings.HTTP_REFERER,
            "X-Title": settings.X_TITLE,
        },
        **kwargs
    )
    return response

# ============================================
# Role-based Model Selection
# ============================================

def get_model_for_role(role: Role, pool: Literal["fast", "heavy", "balanced"] = "balanced") -> str:
    """Get recommended model for a given role."""
    if role in MODEL_RECOMMENDATIONS:
        rec = MODEL_RECOMMENDATIONS[role]
        if role == Role.GENERATOR:
            return rec[pool][0] if pool in rec else rec["balanced"][0]
        return rec["default"]
    return Models.GPT4O  # Default fallback

def get_temperature_for_role(role: Role) -> float:
    """Get optimal temperature for a given role."""
    if role in MODEL_RECOMMENDATIONS:
        return MODEL_RECOMMENDATIONS[role].get("temperature", 0.7)
    return 0.7

def embed_texts(
    texts: List[str], 
    model: Optional[str] = None,
    use_cache: bool = True
) -> List[List[float]]:
    """
    Generate embeddings via Portkey → Together AI with caching.
    
    Args:
        texts: List of text strings to embed
        model: Optional model override (defaults to EMBED_MODEL)
        use_cache: Whether to use caching for embeddings
    
    Returns:
        List of embedding vectors
    """
    model = model or settings.EMBED_MODEL or settings.TOGETHER_EMBED_MODEL
    
    # Use enhanced gateway with caching
    if use_cache:
        from app.memory.embed_router import embed_with_cache
        return embed_with_cache(texts, model)
    else:
        return gateway.embed(texts, model)

async def async_embed_texts(
    texts: List[str], 
    model: Optional[str] = None,
    batch_size: int = 100
) -> List[List[float]]:
    """
    Asynchronously generate embeddings via Portkey → Together AI with batching.
    
    Args:
        texts: List of text strings to embed
        model: Optional model override
        batch_size: Batch size for large embedding requests
    
    Returns:
        List of embedding vectors
    """
    model = model or settings.EMBED_MODEL or settings.TOGETHER_EMBED_MODEL
    
    # Use enhanced gateway with batching
    return await gateway.aembed(texts, model, batch_size)

# ============================================
# Model Name Constants (OpenRouter format)
# ============================================

class Models:
    """Common OpenRouter model identifiers."""
    
    # Generalist models
    GPT4O = "openai/gpt-4o"
    GPT4O_MINI = "openai/gpt-4o-mini"
    CLAUDE_35_SONNET = "anthropic/claude-3.5-sonnet"
    CLAUDE_35_HAIKU = "anthropic/claude-3.5-haiku"
    GEMINI_20_FLASH = "google/gemini-2.0-flash-exp:free"
    GEMINI_15_PRO = "google/gemini-1.5-pro"
    
    # Coding specialists
    QWEN_CODER_32B = "qwen/qwen-2.5-coder-32b-instruct"
    DEEPSEEK_CODER = "deepseek/deepseek-coder"
    DEEPSEEK_CHAT = "deepseek/deepseek-chat"
    
    # Fast/cheap models
    LLAMA_31_8B = "meta-llama/llama-3.1-8b-instruct"
    MISTRAL_7B = "mistralai/mistral-7b-instruct"
    
    # Embedding models (Together AI)
    EMBED_M2_BERT_8K = "togethercomputer/m2-bert-80M-8k-retrieval"
    EMBED_M2_BERT_32K = "togethercomputer/m2-bert-80M-32k-retrieval"

# ============================================
# Quick Utilities
# ============================================

def available_models() -> Dict[str, str]:
    """Return a dictionary of available models by category."""
    return {
        "generalist": [Models.GPT4O, Models.CLAUDE_35_SONNET, Models.GEMINI_15_PRO],
        "coding": [Models.QWEN_CODER_32B, Models.DEEPSEEK_CODER],
        "fast": [Models.GPT4O_MINI, Models.LLAMA_31_8B, Models.MISTRAL_7B],
        "embedding": [Models.EMBED_M2_BERT_8K, Models.EMBED_M2_BERT_32K],
    }

def test_connection():
    """Quick test to verify Portkey connections are working."""
    try:
        # Test chat
        chat_result = chat(
            [{"role": "user", "content": "Say 'Portkey chat OK' in 3 words"}],
            model=Models.GPT4O_MINI
        )
        print(f"✅ Chat: {chat_result}")
        
        # Test embeddings
        vecs = embed_texts(["Portkey embeddings test"])
        print(f"✅ Embeddings: Got vector of dimension {len(vecs[0])}")
        
        return True
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False