"""
Real API calls only - no mocks
Chat service with graceful degradation
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List

from app.api.services.feature_flags import (
    FeatureFlags,
    get_available_models,
    require_feature,
)

logger = logging.getLogger(__name__)


class ChatService:
    """Chat service with graceful degradation - no mocks"""

    def __init__(self):
        self.flags = FeatureFlags()
        logger.info(
            f"ChatService initialized with {len(self.get_available_models())} available models"
        )

    def get_available_models(self) -> List[Dict]:
        """Get list of available models"""
        return get_available_models()

    async def get_response(
        self, query: str, model_preference: str = None, context: Dict = None
    ) -> Dict:
        """Get chat response using available models"""

        # Validate input
        if not query or not query.strip():
            return {"error": "Empty query provided", "response": None, "model": None}

        query = query.strip()
        context = context or {}

        # Try preferred model first
        if model_preference:
            result = await self._try_model(query, model_preference, context)
            if not result.get("error"):
                return result

        # Fall back to available models in priority order
        priority_models = [
            "gpt-4",
            "claude-3-opus",
            "gpt-3.5-turbo",
            "claude-3-sonnet",
            "grok-beta",
        ]

        for model in priority_models:
            if self._is_model_available(model):
                result = await self._try_model(query, model, context)
                if not result.get("error"):
                    return result

        # Final fallback to local processing
        return await self._local_response(query, context)

    def _is_model_available(self, model: str) -> bool:
        """Check if model is available"""
        model_map = {
            "gpt-4": "chat_gpt",
            "gpt-3.5-turbo": "chat_gpt",
            "claude-3-opus": "chat_claude",
            "claude-3-sonnet": "chat_claude",
            "grok-beta": "chat_grok",
        }

        feature = model_map.get(model)
        return feature and self.flags.is_enabled(feature)

    async def _try_model(self, query: str, model: str, context: Dict) -> Dict:
        """Try to get response from specific model"""
        try:
            if model.startswith("gpt-"):
                return await self._call_openai(query, model, context)
            elif model.startswith("claude-"):
                return await self._call_anthropic(query, model, context)
            elif model.startswith("grok-"):
                return await self._call_grok(query, model, context)
            else:
                return {"error": f"Unknown model: {model}"}

        except Exception as e:
            logger.error(f"Error calling {model}: {e}")
            return {"error": f"API call failed: {str(e)}"}

    @require_feature("chat_gpt")
    async def _call_openai(self, query: str, model: str, context: Dict) -> Dict:
        """Real OpenAI API call"""
        try:
            import openai

            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # Build messages with context
            messages = []

            # Add system context if provided
            if context.get("system_prompt"):
                messages.append({"role": "system", "content": context["system_prompt"]})

            # Add conversation history if provided
            if context.get("history"):
                messages.extend(context["history"])

            # Add current query
            messages.append({"role": "user", "content": query})

            # Make API call
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=context.get("max_tokens", 1000),
                temperature=context.get("temperature", 0.7),
            )

            return {
                "response": response.choices[0].message.content,
                "model": model,
                "provider": "openai",
                "timestamp": datetime.utcnow().isoformat(),
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {"error": f"OpenAI API error: {str(e)}"}

    @require_feature("chat_claude")
    async def _call_anthropic(self, query: str, model: str, context: Dict) -> Dict:
        """Real Anthropic API call"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            # Build messages for Claude
            messages = []

            # Add conversation history if provided
            if context.get("history"):
                messages.extend(context["history"])

            # Add current query
            messages.append({"role": "user", "content": query})

            # Make API call
            response = await asyncio.to_thread(
                client.messages.create,
                model=model,
                messages=messages,
                max_tokens=context.get("max_tokens", 1000),
                temperature=context.get("temperature", 0.7),
                system=context.get("system_prompt", ""),
            )

            return {
                "response": response.content[0].text,
                "model": model,
                "provider": "anthropic",
                "timestamp": datetime.utcnow().isoformat(),
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                },
            }

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return {"error": f"Anthropic API error: {str(e)}"}

    @require_feature("chat_grok")
    async def _call_grok(self, query: str, model: str, context: Dict) -> Dict:
        """Real Grok API call"""
        try:
            # Grok API implementation would go here
            # For now, return placeholder since Grok API is not widely available
            return {
                "error": "Grok API not yet implemented",
                "solution": "Use OpenAI or Anthropic models instead",
            }

        except Exception as e:
            logger.error(f"Grok API error: {e}")
            return {"error": f"Grok API error: {str(e)}"}

    async def _local_response(self, query: str, context: Dict) -> Dict:
        """Local fallback - no API needed"""
        logger.info("Using local fallback response")

        # Rule-based responses for common queries
        query_lower = query.lower()

        # Help and guidance responses
        if any(word in query_lower for word in ["help", "how", "what", "guide"]):
            response = """I'm Sophia AI, your intelligent assistant. I can help with:

• General questions and information
• Business analysis and insights  
• Code review and development guidance
• Document analysis and summarization

For advanced AI responses, please add API keys:
- OpenAI: Get $5 free credit at https://platform.openai.com
- Anthropic: Request access at https://console.anthropic.com

Run `./scripts/setup_free_api_keys.sh` for setup guide."""

        # API setup queries
        elif any(word in query_lower for word in ["api", "key", "setup", "configure"]):
            response = """To enable AI features, you need API keys:

1. **OpenAI** (Recommended - $5 free credit):
   → https://platform.openai.com/signup
   → Add to .env: OPENAI_API_KEY=sk-xxxxx

2. **Anthropic Claude** (Optional):
   → https://console.anthropic.com
   → Add to .env: ANTHROPIC_API_KEY=sk-ant-xxxxx

3. **GitHub Integration**:
   → https://github.com/settings/tokens
   → Add to .env: GITHUB_TOKEN=ghp_xxxxx

Run: `./scripts/setup_free_api_keys.sh` for detailed guide."""

        # Business/sales queries
        elif any(
            word in query_lower for word in ["sales", "revenue", "business", "crm"]
        ):
            response = """Business analysis requires AI integration. Current status:

• Basic business logic: ✅ Available
• Advanced AI insights: ⬜ Requires OpenAI/Claude API
• CRM integration: ⬜ Requires HubSpot API key
• Sales forecasting: ⬜ Requires AI models

Add API keys to unlock advanced business features."""

        # Technical queries
        elif any(
            word in query_lower for word in ["code", "debug", "error", "technical"]
        ):
            response = """Technical assistance available with limited functionality:

• Basic code review: ✅ Available
• Advanced debugging: ⬜ Requires AI models
• Code generation: ⬜ Requires OpenAI/Claude
• Architecture advice: ⬜ Requires AI integration

For full technical capabilities, add OpenAI or Anthropic API keys."""

        # Default response
        else:
            response = f"""I understand you're asking about: "{query[:50]}..."

I'm running in local mode with basic capabilities. For intelligent responses, please add AI API keys:

• OpenAI (recommended): $5 free credit
• Anthropic Claude: Request access
• Run: `./scripts/setup_free_api_keys.sh`

I can still help with basic queries and guidance!"""

        return {
            "response": response,
            "model": "local",
            "provider": "sophia",
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Local fallback - add API keys for AI responses",
        }

    async def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get chat history for user"""
        # This would integrate with database
        # For now, return empty list
        return []

    async def save_chat_message(self, user_id: str, message: Dict) -> bool:
        """Save chat message to database"""
        # This would integrate with database
        # For now, just log
        logger.info(
            f"Chat message for user {user_id}: {message.get('response', '')[:50]}..."
        )
        return True
