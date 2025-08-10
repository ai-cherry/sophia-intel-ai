import os
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class GitHubConfig:
    token: str
    token_type: str

@dataclass
class PulumiConfig:
    access_token: str

@dataclass
class QdrantConfig:
    url: str
    api_key: str

@dataclass
class AppConfig:
    github: GitHubConfig
    pulumi: PulumiConfig
    qdrant: QdrantConfig
    database_url: Optional[str]
    llm_keys: Dict[str, str]

def load_from_esc(env_name: str) -> Dict[str, Any]:
    """
    Loads configuration from Pulumi ESC.
    This is a placeholder implementation. In a real scenario, this would
    involve the Pulumi ESC SDK to fetch secrets.
    """
    print(f"Attempting to load configuration from Pulumi ESC environment: {env_name}")
    # In a real implementation, you'd use the Pulumi ESC SDK here.
    # For now, we simulate by reading the same environment variables.
    return {
        "GH_FINE_GRAINED_TOKEN": os.getenv("GH_FINE_GRAINED_TOKEN"),
        "GH_CLASSIC_PAT_TOKEN": os.getenv("GH_CLASSIC_PAT_TOKEN"),
        "PULUMI_ACCESS_TOKEN": os.getenv("PULUMI_ACCESS_TOKEN"),
        "QDRANT_URL": os.getenv("QDRANT_URL"),
        "QDRANT_API_KEY": os.getenv("QDRANT_API_KEY"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
        "PORTKEY_API_KEY": os.getenv("PORTKEY_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
    }

def load_from_env() -> Dict[str, Any]:
    """
    Loads configuration directly from environment variables.
    """
    print("Loading configuration from environment variables.")
    return {key: os.getenv(key) for key in [
        "GH_FINE_GRAINED_TOKEN", "GH_CLASSIC_PAT_TOKEN", "PULUMI_ACCESS_TOKEN",
        "QDRANT_URL", "QDRANT_API_KEY", "DATABASE_URL", "OPENROUTER_API_KEY",
        "PORTKEY_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"
    ]}

def load_config(prefer_esc: bool = True) -> AppConfig:
    """
    Loads configuration, preferring Pulumi ESC if available and requested.
    """
    esc_token = os.getenv("ESC_TOKEN")
    esc_env = os.getenv("ESC_ENV")

    if prefer_esc and esc_token and esc_env:
        try:
            raw_config = load_from_esc(esc_env)
        except Exception as e:
            print(f"Could not load from ESC, falling back to environment variables: {e}")
            raw_config = load_from_env()
    else:
        raw_config = load_from_env()

    # Determine GitHub token
    if raw_config.get("GH_FINE_GRAINED_TOKEN"):
        github_token = raw_config["GH_FINE_GRAINED_TOKEN"]
        token_type = "fine_grained"
    elif raw_config.get("GH_CLASSIC_PAT_TOKEN"):
        github_token = raw_config["GH_CLASSIC_PAT_TOKEN"]
        token_type = "classic_pat"
    else:
        raise ValueError("No GitHub token found (GH_FINE_GRAINED_TOKEN or GH_CLASSIC_PAT_TOKEN).")

    # Extract LLM keys
    llm_keys = {
        "openrouter": raw_config.get("OPENROUTER_API_KEY"),
        "portkey": raw_config.get("PORTKEY_API_KEY"),
        "anthropic": raw_config.get("ANTHROPIC_API_KEY"),
        "openai": raw_config.get("OPENAI_API_KEY"),
        "deepseek": raw_config.get("DEEPSEEK_API_KEY"),
    }

    return AppConfig(
        github=GitHubConfig(token=github_token, token_type=token_type),
        pulumi=PulumiConfig(access_token=raw_config.get("PULUMI_ACCESS_TOKEN")),
        qdrant=QdrantConfig(url=raw_config.get("QDRANT_URL"), api_key=raw_config.get("QDRANT_API_KEY")),
        database_url=raw_config.get("DATABASE_URL"),
        llm_keys={k: v for k, v in llm_keys.items() if v is not None}
    )

if __name__ == "__main__":
    # Example usage:
    # Set environment variables for testing
    # os.environ["GH_FINE_GRAINED_TOKEN"] = "test_gh_token"
    # os.environ["PULUMI_ACCESS_TOKEN"] = "test_pulumi_token"
    # os.environ["QDRANT_URL"] = "http://localhost:6333"
    # os.environ["QDRANT_API_KEY"] = "test_qdrant_key"
    # os.environ["OPENROUTER_API_KEY"] = "test_openrouter_key"

    try:
        config = load_config(prefer_esc=False)
        import json
        print(json.dumps(config, default=lambda o: o.__dict__, indent=2))
    except (ValueError, KeyError) as e:
        print(f"Configuration error: {e}")