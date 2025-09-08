from typing import Dict, Any
import asyncio
import os


class WorkingAgent:
    """Agent that actually does something via a hosted API."""

    def __init__(self, name: str, model: str, category: str):
        self.name = name
        self.model = model
        self.category = category
        # Prefer OPENAI_API_KEY if set, else AIMLAPI_KEY for compatibility
        self.api_key = os.getenv("AIMLAPI_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v1")

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with a real API call to a chat/completions style endpoint."""
        import httpx

        prompt = task.get("prompt", "")
        if not self.api_key:
            return {"success": False, "error": "Missing API key"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2048,
                },
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "agent": self.name,
                    "response": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                }
            else:
                return {"success": False, "error": response.text}


# Create concrete implementations aligned with roles in the system
agents = {
    "coder": WorkingAgent("Coder", "deepseek/deepseek-chat-v3-0324", "coding"),
    "architect": WorkingAgent("Architect", "anthropic/claude-opus-4-1-20250805", "reasoning"),
    "reviewer": WorkingAgent("Reviewer", "openai/gpt-5-mini-2025-08-07", "general"),
    "researcher": WorkingAgent("Researcher", "meta/llama-4-scout", "research"),
}

