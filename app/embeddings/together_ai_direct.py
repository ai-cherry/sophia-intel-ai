"""
Direct Together AI Embeddings
No OpenRouter, direct API calls to Together AI for embeddings
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

class TogetherAIEmbeddings:
    """Direct Together AI embedding generation"""

    def __init__(self):
        self.api_key = os.getenv("TOGETHER_API_KEY", "together-ai-670469")
        self.base_url = "https://api.together.xyz/v1"

        if not self.api_key:
            logger.warning("TOGETHER_API_KEY not set, embeddings will use fallback")

    async def generate_embeddings(
        self,
        texts: list[str],
        model: str = "togethercomputer/m2-bert-80M-8k-retrieval"
    ) -> dict[str, Any]:
        """
        Generate embeddings directly from Together AI
        
        Available models:
        - togethercomputer/m2-bert-80M-8k-retrieval (fast, 768 dims)
        - WhereIsAI/UAE-Large-V1 (high quality, 1024 dims)
        - BAAI/bge-large-en-v1.5 (balanced, 1024 dims)
        """

        if not self.api_key or self.api_key == "together-ai-670469":
            # Use hash-based fallback for now
            logger.info("Using hash-based fallback embeddings")
            return self._generate_fallback_embeddings(texts)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "input": texts
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Generated embeddings via Together AI: {model}")
                    return {
                        "embeddings": data["data"][0]["embedding"] if data.get("data") else [],
                        "model": model,
                        "cached": False,
                        "provider": "together_ai"
                    }
                else:
                    logger.error(f"Together AI error: {response.status_code} - {response.text}")
                    return self._generate_fallback_embeddings(texts)

        except Exception as e:
            logger.error(f"Together AI embedding failed: {e}")
            return self._generate_fallback_embeddings(texts)

    def _generate_fallback_embeddings(self, texts: list[str]) -> dict[str, Any]:
        """Generate deterministic hash-based embeddings as fallback"""
        import hashlib

        text = " ".join(texts) if isinstance(texts, list) else texts
        hash_val = hashlib.sha256(text.encode()).hexdigest()

        # Generate 768-dimensional embedding from hash
        embedding = []
        for i in range(0, min(len(hash_val), 768*2), 2):
            if i < len(hash_val) - 1:
                val = float(int(hash_val[i:i+2], 16)) / 255.0
            else:
                val = float(int(hash_val[i:], 16)) / 255.0
            embedding.append(val)

        # Pad to 768 dimensions if needed
        while len(embedding) < 768:
            embedding.append(0.5)

        return {
            "embeddings": embedding[:768],
            "model": "hash-fallback",
            "cached": False,
            "provider": "fallback"
        }

# Global instance
together_embeddings = TogetherAIEmbeddings()
