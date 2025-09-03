"""
Infrastructure Models Module

Custom model implementations for routing and fallback logic.
"""

from .portkey_router import AllModelsFailedException, ModelError, PortkeyRouterModel

__all__ = [
    'PortkeyRouterModel',
    'ModelError',
    'AllModelsFailedException'
]
