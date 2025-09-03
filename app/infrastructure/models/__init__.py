"""
Infrastructure Models Module

Custom model implementations for routing and fallback logic.
"""

from .portkey_router import PortkeyRouterModel, ModelError, AllModelsFailedException

__all__ = [
    'PortkeyRouterModel',
    'ModelError', 
    'AllModelsFailedException'
]