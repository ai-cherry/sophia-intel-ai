"""
SOPHIA MCP Client Library
Enhanced integration between SOPHIA and MCP servers for contextualized coding memory
"""

from .sophia_client import SophiaMCPClient
from .session_manager import SophiaSessionManager
from .context_tools import ContextAwareToolWrapper

__all__ = [
    'SophiaMCPClient',
    'SophiaSessionManager', 
    'ContextAwareToolWrapper'
]

__version__ = '1.0.0'