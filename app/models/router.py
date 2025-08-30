from agno import OpenAIChat
from agno.models.openai import OpenAIChat as AgnoOpenAIChat
from app import settings

# Role→Model mappings using latest OpenRouter models (August 2025)
ROLE_MODELS = {
    # Strategic/Planning roles - Latest models
    "planner": "openai/gpt-5",                      # GPT-5 for advanced planning
    "critic": "anthropic/claude-3.7-sonnet",        # Claude 3.7 with thinking mode
    "judge": "openai/gpt-5",                        # GPT-5 for synthesis/merge
    
    # Code generation specialists - Latest coding models
    "coderA": "x-ai/grok-code-fast-1",             # Grok Code Fast for primary coding
    "coderB": "qwen/qwen3-coder",                  # Qwen3 Coder as alternative
    "coderC": "mistralai/codestral-2501",          # Latest Codestral
    
    # Reasoning and analysis
    "reasoning": "deepseek/deepseek-r1",           # DeepSeek R1 for reasoning
    "analyzer": "google/gemini-2.5-pro",           # Gemini 2.5 Pro for analysis
    "validator": "anthropic/claude-3.7-sonnet:thinking",  # Claude thinking mode
    
    # Fast/cheap alternatives - Free tier models
    "fast": "deepseek/deepseek-chat-v3.1:free",    # Free DeepSeek V3.1
    "research": "google/gemini-2.5-flash",         # Fast Gemini 2.5
    "free": "meta-llama/llama-4-maverick:free",    # Free Llama 4
    
    # Vision-capable models
    "vision": "google/gemini-2.5-flash-image-preview",  # Image generation/analysis
    
    # Legacy mappings for backward compatibility
    "coder_a": "x-ai/grok-code-fast-1",
    "coder_b": "qwen/qwen3-coder",
}

# Role-specific parameters for optimal performance
ROLE_PARAMS = {
    "planner": {"temperature": 0.3, "top_p": 0.9, "max_tokens": 4000},
    "critic": {"temperature": 0.1, "top_p": 0.8, "max_tokens": 3500},
    "judge": {"temperature": 0.2, "top_p": 0.85, "max_tokens": 5000},
    "coderA": {"temperature": 0.4, "top_p": 0.9, "max_tokens": 8000},
    "coderB": {"temperature": 0.4, "top_p": 0.9, "max_tokens": 8000},
    "coderC": {"temperature": 0.5, "top_p": 0.95, "max_tokens": 8000},
    "fast": {"temperature": 0.3, "top_p": 0.85, "max_tokens": 2000},
}

# Backward compatibility
MODELS = ROLE_MODELS

def chat_model(model_id: str = "openai/gpt-4o") -> OpenAIChat:
    """
    Returns an Agno OpenAIChat configured with Portkey endpoint and attribution headers.
    Routes through Portkey → OpenRouter for all chat/completion calls.
    
    Args:
        model_id: OpenRouter model identifier (e.g., "openai/gpt-4o", "anthropic/claude-3.5-sonnet")
    
    Returns:
        Configured OpenAIChat instance
    """
    return OpenAIChat(
        model=model_id,
        base_url=settings.OPENAI_BASE_URL,  # Portkey gateway
        api_key=settings.OPENAI_API_KEY,    # Portkey VK for OpenRouter
        default_headers={
            "HTTP-Referer": settings.HTTP_REFERER,
            "X-Title": settings.X_TITLE
        }
    )

def agno_chat_model(model_id: str, **kwargs) -> AgnoOpenAIChat:
    """
    Create an Agno-specific OpenAIChat model with role parameters.
    
    Args:
        model_id: Model identifier or role key from ROLE_MODELS
        **kwargs: Additional parameters to override
    
    Returns:
        Configured AgnoOpenAIChat instance
    """
    # If model_id is a role key, get the actual model ID
    actual_model = ROLE_MODELS.get(model_id, model_id)
    
    # Get role-specific params if available
    params = ROLE_PARAMS.get(model_id, {}).copy()
    params.update(kwargs)  # Allow overrides
    
    return AgnoOpenAIChat(
        id=actual_model,
        base_url=settings.OPENAI_BASE_URL,
        api_key=settings.OPENAI_API_KEY,
        default_headers={
            "HTTP-Referer": settings.HTTP_REFERER,
            "X-Title": settings.X_TITLE
        },
        **params
    )