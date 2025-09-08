"""
Clean feature flag system - no mocks, just disable features
"""

import os
from typing import Dict, List, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class FeatureFlags:
    """Control which features are available based on API keys"""

    def __init__(self):
        # Check what's actually available
        self.features = {
            # AI Chat Features
            'chat_gpt': bool(os.getenv('OPENAI_API_KEY')),
            'chat_claude': bool(os.getenv('ANTHROPIC_API_KEY')),
            'chat_grok': bool(os.getenv('GROK_API_KEY')),

            # Integration Features
            'github_integration': bool(os.getenv('GITHUB_TOKEN')),
            'hubspot_crm': bool(os.getenv('HUBSPOT_API_KEY')),
            'gong_calls': bool(os.getenv('GONG_ACCESS_KEY')),
            'slack_integration': bool(os.getenv('SLACK_BOT_TOKEN')),
            'notion_integration': bool(os.getenv('NOTION_API_KEY')),

            # Database Features
            'vector_search': bool(os.getenv('QDRANT_URL')),
            'redis_cache': bool(os.getenv('REDIS_URL')),
            'postgres_db': bool(os.getenv('DATABASE_URL')),

            # Core features always enabled
            'basic_chat': True,
            'knowledge_base': True,
            'user_management': True,
            'file_upload': True,
            'health_checks': True,
        }

        # Log feature status on startup
        enabled_count = sum(1 for v in self.features.values() if v)
        total_count = len(self.features)
        logger.info(f"Feature flags initialized: {enabled_count}/{total_count} features enabled")

        # Log missing critical features
        missing_critical = self.get_missing_critical_apis()
        if missing_critical:
            logger.warning(f"Missing critical API keys: {', '.join(missing_critical)}")

    def is_enabled(self, feature: str) -> bool:
        """Check if feature is enabled"""
        return self.features.get(feature, False)

    def get_enabled_features(self) -> List[str]:
        """Get list of enabled features"""
        return [k for k, v in self.features.items() if v]

    def get_disabled_features(self) -> List[str]:
        """Get list of disabled features"""
        return [k for k, v in self.features.items() if not v]

    def get_missing_apis(self) -> List[str]:
        """Get list of missing API keys"""
        missing = []

        api_map = {
            'chat_gpt': 'OpenAI API key',
            'chat_claude': 'Anthropic API key',
            'chat_grok': 'Grok API key',
            'github_integration': 'GitHub token',
            'hubspot_crm': 'HubSpot API key',
            'gong_calls': 'Gong access key',
            'slack_integration': 'Slack bot token',
            'notion_integration': 'Notion API key',
            'vector_search': 'Qdrant URL',
            'redis_cache': 'Redis URL',
            'postgres_db': 'Database URL'
        }

        for feature, name in api_map.items():
            if not self.features[feature]:
                missing.append(name)

        return missing

    def get_missing_critical_apis(self) -> List[str]:
        """Get list of missing critical API keys"""
        critical_features = ['postgres_db', 'chat_gpt', 'github_integration']
        missing = []

        api_map = {
            'postgres_db': 'Database URL',
            'chat_gpt': 'OpenAI API key',
            'github_integration': 'GitHub token'
        }

        for feature in critical_features:
            if not self.features[feature]:
                missing.append(api_map[feature])

        return missing

    def get_feature_status(self) -> Dict:
        """Get comprehensive feature status"""
        return {
            'enabled': self.get_enabled_features(),
            'disabled': self.get_disabled_features(),
            'missing_apis': self.get_missing_apis(),
            'missing_critical': self.get_missing_critical_apis(),
            'total_features': len(self.features),
            'enabled_count': len(self.get_enabled_features())
        }

def require_feature(feature_name: str):
    """Decorator to check if feature is enabled"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            flags = FeatureFlags()
            if not flags.is_enabled(feature_name):
                return {
                    'error': f'Feature {feature_name} is not available',
                    'reason': 'Missing API key or configuration',
                    'solution': 'Add required API key to .env file',
                    'setup_guide': 'Run: ./scripts/setup_free_api_keys.sh'
                }
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def get_available_models() -> List[Dict]:
    """Get list of available AI models based on API keys"""
    flags = FeatureFlags()
    models = []

    if flags.is_enabled('chat_gpt'):
        models.extend([
            {'id': 'gpt-4', 'name': 'GPT-4', 'provider': 'openai', 'available': True},
            {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo', 'provider': 'openai', 'available': True}
        ])

    if flags.is_enabled('chat_claude'):
        models.extend([
            {'id': 'claude-3-opus', 'name': 'Claude 3 Opus', 'provider': 'anthropic', 'available': True},
            {'id': 'claude-3-sonnet', 'name': 'Claude 3 Sonnet', 'provider': 'anthropic', 'available': True}
        ])

    if flags.is_enabled('chat_grok'):
        models.append(
            {'id': 'grok-beta', 'name': 'Grok Beta', 'provider': 'xai', 'available': True}
        )

    # Always include local fallback
    models.append({
        'id': 'local', 
        'name': 'Local Assistant', 
        'provider': 'sophia', 
        'available': True,
        'description': 'Rule-based responses when AI APIs unavailable'
    })

    return models

# Global instance for easy access
feature_flags = FeatureFlags()
