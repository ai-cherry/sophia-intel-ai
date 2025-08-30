from typing import List
from openai import AsyncOpenAI
from app import settings

# Create async OpenAI client for embeddings via Portkey
embed_client = AsyncOpenAI(
    base_url=settings.EMBED_BASE_URL,  # Portkey gateway
    api_key=settings.EMBED_API_KEY or settings.TOGETHER_API_KEY,  # Portkey VK for Together AI
)

async def embed_text(texts: List[str], model: str = None) -> List[List[float]]:
    """
    Generate embeddings using Together AI via Portkey gateway.
    
    Args:
        texts: List of text strings to embed
        model: Optional model override (defaults to EMBED_MODEL from settings)
    
    Returns:
        List of embedding vectors
    """
    model = model or settings.EMBED_MODEL or settings.TOGETHER_EMBED_MODEL
    
    # Use OpenAI SDK format via Portkey
    response = await embed_client.embeddings.create(
        model=model,
        input=texts
    )
    
    # Extract embeddings from response
    return [item.embedding for item in response.data]