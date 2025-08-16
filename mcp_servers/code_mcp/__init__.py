"""
MCP Code Server Package
Dedicated coding agent with GitHub integration
"""

from .config import code_mcp_settings, get_github_headers, validate_repository_access

__version__ = "1.0.0"
__all__ = ["code_mcp_settings", "validate_repository_access", "get_github_headers"]
