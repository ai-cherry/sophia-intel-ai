"""
MCP Code Server Package
Dedicated coding agent with GitHub integration
"""

from .config import code_mcp_settings, validate_repository_access, get_github_headers

__version__ = "1.0.0"
__all__ = ["code_mcp_settings", "validate_repository_access", "get_github_headers"]

