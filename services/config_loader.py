import os
from dataclasses import dataclass, field
from typing import List, Optional

# Assuming a simple ESC loader for now
# In a real scenario, this would involve the Pulumi ESC SDK
def load_from_esc(env_name: str):
    """
    Loads configuration from Pulumi ESC.
    This is a placeholder implementation.
    """
    print(f"Attempting to load configuration from Pulumi ESC environment: {env_name}")
    # Placeholder: In a real implementation, you would use the Pulumi ESC SDK
    # to fetch the configuration. For now, we'll simulate it by reading
    # environment variables that *would* have been set by ESC.
    return {
        "github": {
            "mode": "app",
            "app_id": os.getenv("GITHUB_APP_ID"),
            "private_key_pem": os.getenv("GITHUB_APP_PRIVATE_KEY_PEM"),
            "fine_grained_token_present": os.getenv("GH_FINE_GRAINED_TOKEN") is not None,
        },
        "pulumi": {"access_token": os.getenv("PULUMI_ACCESS_TOKEN")},
        "qdrant": {"url": os.getenv("QDRANT_URL"), "api_key": os.getenv("QDRANT_API_KEY")},
        "db": {"database_url": os.getenv("DATABASE_URL")},
        "llm": {
            "router": "openrouter",
            "fallbacks": ["portkey", "direct"]
        },
        "approvals": {
            "allowed_users": [os.getenv("GH_USERNAME")] if os.getenv("GH_USERNAME") else []
        }
    }


def load_from_env():
    """
    Loads configuration from environment variables.
    """
    print("Loading configuration from environment variables.")
    return {
        "github": {
            "mode": "pat",
            "username": os.getenv("GH_USERNAME"),
            "fine_grained_token": os.getenv("GH_FINE_GRAINED_TOKEN"),
        },
        "pulumi": {"access_token": os.getenv("PULUMI_ACCESS_TOKEN")},
        "qdrant": {"url": os.getenv("QDRANT_URL"), "api_key": os.getenv("QDRANT_API_KEY")},
        "db": {"database_url": os.getenv("DATABASE_URL")},
        "llm": {
            "router": "openrouter",
            "fallbacks": ["portkey", "direct"]
        },
        "approvals": {
            "allowed_users": [os.getenv("GH_USERNAME")] if os.getenv("GH_USERNAME") else []
        }
    }


def load_config(prefer_esc: bool = True):
    """
    Loads configuration, preferring Pulumi ESC if available and requested.
    """
    esc_token = os.getenv("ESC_TOKEN")
    esc_env = os.getenv("ESC_ENV")

    if prefer_esc and esc_token and esc_env:
        try:
            return load_from_esc(esc_env)
        except Exception as e:
            print(f"Could not load from ESC, falling back to environment variables: {e}")
            return load_from_env()
    else:
        return load_from_env()

if __name__ == "__main__":
    config = load_config()
    import json
    print(json.dumps(config, indent=2))