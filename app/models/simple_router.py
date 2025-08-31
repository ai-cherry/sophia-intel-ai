"""
Simplified model router for agent system.
Uses direct OpenAI client integration.
"""

from typing import Dict, Any, Optional
import os
from openai import OpenAI, AsyncOpenAI

# Role→Model mappings 
ROLE_MODELS = {
    "planner": "gpt-4",
    "critic": "gpt-4", 
    "judge": "gpt-4",
    "coderA": "gpt-4",
    "coderB": "gpt-4",
    "generator": "gpt-4",
    "fast": "gpt-3.5-turbo",
    "balanced": "gpt-4",
    "heavy": "gpt-4"
}

# Role parameters
ROLE_PARAMS = {
    "planner": {"temperature": 0.3, "max_tokens": 2000},
    "critic": {"temperature": 0.1, "max_tokens": 1500}, 
    "judge": {"temperature": 0.2, "max_tokens": 1500},
    "generator": {"temperature": 0.7, "max_tokens": 3000},
    "fast": {"temperature": 0.7, "max_tokens": 1000},
    "balanced": {"temperature": 0.7, "max_tokens": 2000},
    "heavy": {"temperature": 0.7, "max_tokens": 4000}
}


class SimpleOpenAIChat:
    """Simplified OpenAI chat wrapper."""
    
    def __init__(self, model: str = "gpt-4", **kwargs):
        self.model = model
        self.params = kwargs
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy-key"))
        
    def invoke(self, messages, **kwargs):
        """Simple invoke method."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **{**self.params, **kwargs}
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Mock response for: {messages[-1].get('content', 'unknown')[:50]}..."


def agno_chat_model(model_id: str, **params) -> SimpleOpenAIChat:
    """Create a chat model instance."""
    return SimpleOpenAIChat(model=model_id, **params)