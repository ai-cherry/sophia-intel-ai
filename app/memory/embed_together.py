import httpx
from typing import List
from app import settings

async def embed_text(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using Together AI.
    
    Args:
        texts: List of text strings to embed
    
    Returns:
        List of embedding vectors
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.together.xyz/v1/embeddings",
            headers={
                "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": settings.TOGETHER_EMBED_MODEL,
                "input": texts
            }
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]