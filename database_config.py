"""
SOPHIA V4 Database Configuration
Centralized database configuration for all MCP servers and main application
"""

import os

# Neon Database Configuration
NEON_PROJECT_ID = "rough-union-72390895"
NEON_ORG_ID = "org-hidden-boat-28633291"
NEON_API_TOKEN = os.getenv('NEON_API_TOKEN')

# Main production endpoint
NEON_MAIN_ENDPOINT = "ep-rough-dew-af6w48m3.c-2.us-west-2.aws.neon.tech"
NEON_MAIN_BRANCH = "br-green-firefly-afykrx78"

# Database connection strings
def get_database_url(database_name="neondb", endpoint=None):
    """
    Get database URL for Neon PostgreSQL
    Format: postgresql://[user[:password]@][netloc][:port][/dbname]
    """
    if endpoint is None:
        endpoint = NEON_MAIN_ENDPOINT
    
    # Neon uses passwordless access for this project
    return f"postgresql://neondb_owner@{endpoint}/{database_name}?sslmode=require"

# MCP Server Database Configurations
MCP_DATABASES = {
    "code_index": get_database_url("sophia_code_index"),
    "code_gen": get_database_url("sophia_code_gen"),
    "ci_cd": get_database_url("sophia_ci_cd"),
    "arch_optimize": get_database_url("sophia_arch_optimize"),
    "security": get_database_url("sophia_security"),
    "analytics": get_database_url("sophia_analytics")
}

# Redis Configuration for AI Swarm Coordination
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# API Keys Configuration
API_KEYS = {
    'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
    'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN'),
    'MEM0_API_KEY': os.getenv('MEM0_API_KEY'),
    'N8N_API_KEY': os.getenv('N8N_API_KEY'),
    'NEON_API_TOKEN': os.getenv('NEON_API_TOKEN')
}

# Deployment Configuration
DEPLOYMENT_CONFIG = {
    'fly_app_name': 'sophia-v4-main',
    'mcp_servers': {
        'code-index-mcp': {'port': 5000, 'fly_app': 'sophia-code-index'},
        'code-gen-mcp': {'port': 5001, 'fly_app': 'sophia-code-gen'},
        'ci-cd-mcp': {'port': 5002, 'fly_app': 'sophia-ci-cd'},
        'arch-optimize-mcp': {'port': 5003, 'fly_app': 'sophia-arch-optimize'},
        'security-mcp': {'port': 5004, 'fly_app': 'sophia-security'},
        'analytics-mcp': {'port': 5005, 'fly_app': 'sophia-analytics'}
    }
}

# Environment Variables for Deployment
ENVIRONMENT_VARS = {
    'NEON_PROJECT_ID': NEON_PROJECT_ID,
    'NEON_ORG_ID': NEON_ORG_ID,
    'NEON_MAIN_ENDPOINT': NEON_MAIN_ENDPOINT,
    'NEON_MAIN_BRANCH': NEON_MAIN_BRANCH,
    'DATABASE_URL': get_database_url(),
    'REDIS_URL': REDIS_URL
}

