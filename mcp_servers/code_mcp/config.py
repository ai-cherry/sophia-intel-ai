"""
Configuration for MCP Code Server
"""

import os
from typing import Optional
from pydantic import Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings


class CodeMCPSettings(BaseSettings):
    """Settings for MCP Code Server"""
    
    # GitHub Integration
    github_pat: str = Field(..., env="GITHUB_PAT", description="GitHub Personal Access Token")
    github_api_base: str = Field(default="https://api.github.com", description="GitHub API base URL")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8002, description="Server port")
    log_level: str = Field(default="info", description="Log level")
    
    # Repository Configuration
    default_repository: str = Field(default="ai-cherry/sophia-intel", description="Default repository")
    default_branch: str = Field(default="main", description="Default branch")
    
    # Operation Limits
    max_file_size: int = Field(default=1024*1024, description="Maximum file size in bytes")
    max_files_per_operation: int = Field(default=50, description="Maximum files per operation")
    
    # Security
    allowed_repositories: list = Field(
        default=["ai-cherry/sophia-intel"], 
        description="List of allowed repositories"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
code_mcp_settings = CodeMCPSettings()


def validate_repository_access(repository: str) -> bool:
    """Validate if repository access is allowed"""
    return repository in code_mcp_settings.allowed_repositories


def get_github_headers() -> dict:
    """Get GitHub API headers"""
    return {
        "Authorization": f"token {code_mcp_settings.github_pat}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Sophia-Intel-MCP-Code-Server"
    }

