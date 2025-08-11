import os
import json
import subprocess
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


def load_from_esc(env_name: str, token: str = None) -> Dict[str, Any]:
    """
    Loads configuration from Pulumi ESC using the ESC CLI.
    
    Args:
        env_name: The ESC environment name (e.g., "sophia/dev")
        token: Optional ESC token (defaults to ESC_TOKEN env var)
    
    Returns:
        Dictionary of environment variables from ESC
    """
    print(f"Loading configuration from Pulumi ESC environment: {env_name}")
    
    # Set token if provided
    env = os.environ.copy()
    if token:
        env["ESC_TOKEN"] = token
    elif os.getenv("ESC_TOKEN"):
        env["ESC_TOKEN"] = os.getenv("ESC_TOKEN")
    else:
        print("Warning: No ESC_TOKEN found, ESC operations may fail")
        return {}
    
    try:
        # Use esc CLI to get environment
        result = subprocess.run(
            ["esc", "env", "get", env_name, "--format", "json"],
            capture_output=True,
            text=True,
            env=env,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"ESC command failed: {result.stderr}")
            return {}
        
        # Parse JSON response
        esc_data = json.loads(result.stdout)
        
        # Extract environment variables section
        env_vars = esc_data.get("environmentVariables", {})
        
        print(f"Loaded {len(env_vars)} variables from ESC")
        return env_vars
        
    except subprocess.TimeoutExpired:
        print("ESC command timed out")
        return {}
    except json.JSONDecodeError as e:
        print(f"Failed to parse ESC response: {e}")
        return {}
    except FileNotFoundError:
        print("ESC CLI not found. Please install Pulumi ESC")
        return {}
    except Exception as e:
        print(f"Unexpected error loading from ESC: {e}")
        return {}


def load_from_env() -> Dict[str, Any]:
    """
    Loads configuration directly from environment variables.
    """
    print("Loading configuration from environment variables.")
    return {
        key: os.getenv(key)
        for key in [
            "GH_FINE_GRAINED_TOKEN",
            "GH_CLASSIC_PAT_TOKEN",
            "PULUMI_ACCESS_TOKEN",
            "QDRANT_URL",
            "QDRANT_API_KEY",
            "DATABASE_URL",
            "OPENROUTER_API_KEY",
            "PORTKEY_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "DEEPSEEK_API_KEY",
        ]
    }


def load_config(prefer_esc: bool = True) -> AppConfig:
    """
    Loads configuration with precedence: ESC → ENV → file
    
    Args:
        prefer_esc: Whether to prefer ESC over environment variables
    
    Returns:
        AppConfig object with merged configuration
    """
    raw_config = {}
    
    # Step 1: Try loading from ESC if available
    esc_env = os.getenv("ESC_ENV")
    esc_token = os.getenv("ESC_TOKEN")
    
    if prefer_esc and esc_env:
        try:
            esc_config = load_from_esc(esc_env, esc_token)
            if esc_config:
                raw_config.update(esc_config)
                print(f"✓ Loaded config from ESC environment: {esc_env}")
        except Exception as e:
            print(f"Warning: Could not load from ESC: {e}")
    
    # Step 2: Override/supplement with environment variables
    env_config = load_from_env()
    for key, value in env_config.items():
        if value is not None:  # Only override with non-None values
            raw_config[key] = value
    
    # Step 3: Log configuration sources (never log values!)
    config_sources = []
    if esc_env and any(k in raw_config for k in ["PULUMI_ACCESS_TOKEN", "QDRANT_API_KEY"]):
        config_sources.append(f"ESC ({esc_env})")
    if any(os.getenv(k) for k in ["GH_FINE_GRAINED_TOKEN", "OPENROUTER_API_KEY"]):
        config_sources.append("Environment")
    
    if config_sources:
        print(f"Configuration sources: {', '.join(config_sources)}")

    # Determine GitHub token
    if raw_config.get("GH_FINE_GRAINED_TOKEN"):
        github_token = raw_config["GH_FINE_GRAINED_TOKEN"]
        token_type = "fine_grained"
    elif raw_config.get("GH_CLASSIC_PAT_TOKEN"):
        github_token = raw_config["GH_CLASSIC_PAT_TOKEN"]
        token_type = "classic_pat"
    else:
        raise ValueError(
            "No GitHub token found (GH_FINE_GRAINED_TOKEN or GH_CLASSIC_PAT_TOKEN)."
        )

    # Extract LLM keys
    llm_keys = {
        "openrouter": raw_config.get("OPENROUTER_API_KEY"),
        "portkey": raw_config.get("PORTKEY_API_KEY"),
        "anthropic": raw_config.get("ANTHROPIC_API_KEY"),
        "openai": raw_config.get("OPENAI_API_KEY"),
        "deepseek": raw_config.get("DEEPSEEK_API_KEY"),
    }

    # Handle missing Pulumi config gracefully
    pulumi_token = raw_config.get("PULUMI_ACCESS_TOKEN")
    if not pulumi_token:
        print("WARNING: PULUMI_ACCESS_TOKEN not set, Pulumi operations will be disabled")
    
    # Handle missing Qdrant config gracefully
    qdrant_url = raw_config.get("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = raw_config.get("QDRANT_API_KEY")
    if not qdrant_api_key:
        print("WARNING: QDRANT_API_KEY not set, Qdrant operations may fail")
    
    return AppConfig(
        github=GitHubConfig(token=github_token, token_type=token_type),
        pulumi=PulumiConfig(access_token=pulumi_token),
        qdrant=QdrantConfig(
            url=qdrant_url, api_key=qdrant_api_key
        ),
        database_url=raw_config.get("DATABASE_URL"),
        llm_keys={k: v for k, v in llm_keys.items() if v is not None},
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
