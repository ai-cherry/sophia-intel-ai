"""
Centralized Portkey client management for slim-agno.
All LLM and embedding calls route through Portkey gateway.
"""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI, AsyncOpenAI
from app import settings

# ============================================
# Chat/Completion Client (Portkey → OpenRouter)
# ============================================

CHAT = OpenAI(
    base_url=settings.OPENAI_BASE_URL,  # https://api.portkey.ai/v1
    api_key=settings.OPENAI_API_KEY,    # Portkey VK for OpenRouter
)

ASYNC_CHAT = AsyncOpenAI(
    base_url=settings.OPENAI_BASE_URL,
    api_key=settings.OPENAI_API_KEY,
)

def chat(
    messages: List[Dict[str, str]], 
    model: str = "openai/gpt-4o",
    system: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
) -> str:
    """
    Synchronous chat completion via Portkey → OpenRouter.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: OpenRouter model ID (e.g., "openai/gpt-4o", "anthropic/claude-3.5-sonnet")
        system: Optional system message to prepend
        temperature: Sampling temperature
        **kwargs: Additional parameters for the completion
    
    Returns:
        The assistant's response content
    """
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)
    
    response = CHAT.chat.completions.create(
        model=model,
        messages=msgs,
        temperature=temperature,
        extra_headers={
            "HTTP-Referer": settings.HTTP_REFERER,
            "X-Title": settings.X_TITLE,
        },
        **kwargs
    )
    return response.choices[0].message.content

async def async_chat(
    messages: List[Dict[str, str]], 
    model: str = "openai/gpt-4o",
    system: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
) -> str:
    """
    Asynchronous chat completion via Portkey → OpenRouter.
    """
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)
    
    response = await ASYNC_CHAT.chat.completions.create(
        model=model,
        messages=msgs,
        temperature=temperature,
        extra_headers={
            "HTTP-Referer": settings.HTTP_REFERER,
            "X-Title": settings.X_TITLE,
        },
        **kwargs
    )
    return response.choices[0].message.content

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
# Embeddings Client (Portkey → Together AI)
# ============================================

EMBED = OpenAI(
    base_url=settings.EMBED_BASE_URL,  # https://api.portkey.ai/v1
    api_key=settings.EMBED_API_KEY or settings.TOGETHER_API_KEY,  # Portkey VK for Together
)

ASYNC_EMBED = AsyncOpenAI(
    base_url=settings.EMBED_BASE_URL,
    api_key=settings.EMBED_API_KEY or settings.TOGETHER_API_KEY,
)

def embed_texts(
    texts: List[str], 
    model: Optional[str] = None
) -> List[List[float]]:
    """
    Generate embeddings via Portkey → Together AI.
    
    Args:
        texts: List of text strings to embed
        model: Optional model override (defaults to EMBED_MODEL)
    
    Returns:
        List of embedding vectors
    """
    model = model or settings.EMBED_MODEL or settings.TOGETHER_EMBED_MODEL
    
    response = EMBED.embeddings.create(
        model=model,
        input=texts
    )
    return [item.embedding for item in response.data]

async def async_embed_texts(
    texts: List[str], 
    model: Optional[str] = None
) -> List[List[float]]:
    """
    Asynchronously generate embeddings via Portkey → Together AI.
    """
    model = model or settings.EMBED_MODEL or settings.TOGETHER_EMBED_MODEL
    
    response = await ASYNC_EMBED.embeddings.create(
        model=model,
        input=texts
    )
    return [item.embedding for item in response.data]

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