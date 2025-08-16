"""
SOPHIA MCP Client Library
Enhanced integration between SOPHIA and MCP servers for contextualized coding memory
"""

from .context_tools import ContextAwareToolWrapper
from .session_manager import SophiaSessionManager
from .sophia_client import SophiaMCPClient

__all__ = ["SophiaMCPClient", "SophiaSessionManager", "ContextAwareToolWrapper"]

__version__ = "1.0.0"
