from agno import OpenAIChat
from app import settings

# Model mappings for OpenRouter model IDs
MODELS = {
    "planner": "openai/gpt-4o",
    "critic": "openai/gpt-4o-mini", 
    "judge": "openai/gpt-4o-mini",
    "coder_a": "anthropic/claude-3.5-sonnet",
    "coder_b": "deepseek/deepseek-coder"
}

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