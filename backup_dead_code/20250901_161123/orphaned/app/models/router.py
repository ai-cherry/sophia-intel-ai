from agno import OpenAIChat
from agno.models.openai import OpenAIChat as AgnoOpenAIChat
from app import settings

# Role→Model mappings using OpenAI models for demo
ROLE_MODELS = {
    # Strategic/Planning roles - GPT-4 for complex tasks
    "planner": "gpt-4o-mini",                      # GPT-4o-mini for planning
    "critic": "gpt-4o-mini",                       # GPT-4o-mini for review
    "judge": "gpt-4o-mini",                        # GPT-4o-mini for decisions
    
    # Code generation specialists - GPT models
    "coderA": "gpt-4o-mini",                       # GPT-4o-mini for primary coding
    "coderB": "gpt-4o-mini",                       # GPT-4o-mini as alternative
    "coderC": "gpt-4o-mini",                       # GPT-4o-mini for code
    
    # Reasoning and analysis
    "reasoning": "gpt-4o-mini",                    # GPT-4o-mini for reasoning
    "analyzer": "gpt-4o-mini",                     # GPT-4o-mini for analysis
    "validator": "gpt-4o-mini",                    # GPT-4o-mini for validation
    
    # Fast/cheap alternatives
    "fast": "gpt-3.5-turbo",                      # GPT-3.5 for fast responses
    "research": "gpt-4o-mini",                     # GPT-4o-mini for research
    "free": "gpt-3.5-turbo",                      # GPT-3.5 as free tier
    
    # Vision-capable models
    "vision": "gpt-4o",                           # GPT-4o with vision
    
    # Legacy mappings for backward compatibility
    "coder_a": "gpt-4o-mini",
    "coder_b": "gpt-4o-mini",
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
        **params
    )