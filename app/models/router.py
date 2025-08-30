from agno import OpenAIChat
from app import settings

MODELS = {
    "planner": "gpt-4o",
    "critic": "gpt-4o-mini",
    "judge": "gpt-4o-mini",
    "coder_a": "claude-3-5-sonnet-20241022",
    "coder_b": "deepseek/deepseek-chat"
}

def chat_model(model_id: str = "gpt-4o") -> OpenAIChat:
    """
    Returns an Agno OpenAIChat configured with Portkey endpoint and attribution headers.
    
    Args:
        model_id: The model identifier to use (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")
    
    Returns:
        Configured OpenAIChat instance
    """
    return OpenAIChat(
        model=model_id,
        base_url=settings.OPENAI_BASE_URL,
        api_key=settings.OPENAI_API_KEY,
        default_headers={
            "HTTP-Referer": settings.HTTP_REFERER,
            "X-Title": settings.X_TITLE
        }
    )