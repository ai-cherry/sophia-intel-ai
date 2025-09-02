"""
Simplified model router for agent system.
Uses direct OpenAI client integration.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv('.env.local')

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

        # Get real API key, fail if not available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "dummy-key":
            raise ValueError("OPENAI_API_KEY environment variable must be set with a valid API key")

        self.client = OpenAI(api_key=api_key)

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
            # Log the error and re-raise - no mock fallbacks allowed
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"OpenAI API call failed: {e}")
            raise Exception(f"OpenAI API call failed: {e}") from e


def agno_chat_model(model_id: str, **params) -> SimpleOpenAIChat:
    """Create a chat model instance."""
    return SimpleOpenAIChat(model=model_id, **params)
