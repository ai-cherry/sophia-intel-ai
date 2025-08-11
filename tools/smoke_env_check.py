import os
import sys
from services.config_loader import load_config, AppConfig


def mask_secret(secret):
    if secret is None:
        return "Not Set"
    if len(secret) <= 4:
        return "***"
    return f"***{secret[-4:]}"


def check_esc_setup():
    """Check if ESC is configured"""
    esc_env = os.getenv("ESC_ENV")
    esc_token = os.getenv("ESC_TOKEN")
    
    print("--- ESC Configuration ---")
    if esc_env and esc_token:
        print(f"✅ ESC_ENV: {esc_env}")
        print(f"✅ ESC_TOKEN: {mask_secret(esc_token)}")
        return True
    else:
        if not esc_env:
            print("⚠️  ESC_ENV: Not set")
        if not esc_token:
            print("⚠️  ESC_TOKEN: Not set")
        return False


def check_config_loader():
    """
    Verifies that config loader can resolve required values.
    """
    print("\n--- Config Loader Check ---")
    
    try:
        config = load_config()
        
        # Check critical configurations
        checks = {
            "GitHub Token": config.github.token if hasattr(config, 'github') else None,
            "Pulumi Token": config.pulumi.access_token if hasattr(config, 'pulumi') else None,
            "Qdrant URL": config.qdrant.url if hasattr(config, 'qdrant') else None,
            "Qdrant API Key": config.qdrant.api_key if hasattr(config, 'qdrant') else None,
        }
        
        all_ok = True
        for name, value in checks.items():
            if value:
                print(f"✅ {name}: {mask_secret(value)}")
            else:
                print(f"❌ {name}: Not configured")
                all_ok = False
        
        # Check LLM keys
        print("\n--- LLM Keys ---")
        if hasattr(config, 'llm_keys') and config.llm_keys:
            for provider, key in config.llm_keys.items():
                if key:
                    print(f"✅ {provider}: {mask_secret(key)}")
        else:
            print("⚠️  No LLM keys configured")
        
        return all_ok
        
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False


def check_env_vars():
    """
    Fallback check for environment variables if ESC is not configured.
    """
    print("\n--- Direct Environment Variable Check ---")

    required_vars = {
        "GitHub": ["GH_FINE_GRAINED_TOKEN", "GH_CLASSIC_PAT_TOKEN", "GITHUB_PAT"],
        "Pulumi": ["PULUMI_ACCESS_TOKEN"],
        "Qdrant": ["QDRANT_URL", "QDRANT_API_KEY"],
        "LLM": [
            "OPENROUTER_API_KEY",
            "PORTKEY_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "GROQ_API_KEY",
            "DEEPSEEK_API_KEY",
            "MISTRAL_API_KEY",
            "HUGGINGFACE_API_TOKEN",
            "AGNO_API_KEY",
        ],
    }

    all_ok = True
    missing_vars = []

    # Check GitHub tokens
    github_token_present = any(os.getenv(var) for var in required_vars["GitHub"])
    if not github_token_present:
        print("❌ GitHub: No GitHub token found")
        all_ok = False
        missing_vars.extend(required_vars["GitHub"])
    else:
        print("✅ GitHub: Token is present")

    # Check other required vars
    for category, variables in required_vars.items():
        if category == "GitHub":
            continue

        for var in variables:
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: {mask_secret(value)}")
            else:
                # Only fail for critical ones
                if var in ["PULUMI_ACCESS_TOKEN", "QDRANT_URL", "QDRANT_API_KEY"]:
                    print(f"❌ {var}: Not set")
                    all_ok = False
                    missing_vars.append(var)

    return all_ok, missing_vars


def main():
    """
    Main smoke check that verifies configuration through multiple methods.
    """
    print("=== Sophia Configuration Smoke Check ===\n")
    
    # Check ESC setup
    esc_configured = check_esc_setup()
    
    # Try config loader (which will use ESC if available)
    config_ok = check_config_loader()
    
    # If neither ESC nor config loader work, check env vars directly
    if not config_ok and not esc_configured:
        env_ok, missing = check_env_vars()
        
        print("\n--- Summary ---")
        if env_ok:
            print("✅ Environment variables configured (consider using ESC)")
            sys.exit(0)
        else:
            print(f"❌ Missing critical variables: {', '.join(missing)}")
            print("\nTo fix: Run scripts/esc-bootstrap.sh to set up Pulumi ESC")
            sys.exit(1)
    
    print("\n--- Summary ---")
    if config_ok:
        if esc_configured:
            print("✅ All checks passed! Configuration loaded from ESC")
        else:
            print("✅ All checks passed! Configuration loaded from environment")
        sys.exit(0)
    else:
        print("❌ Configuration incomplete")
        if not esc_configured:
            print("   Run scripts/esc-bootstrap.sh to set up Pulumi ESC")
        sys.exit(1)


if __name__ == "__main__":
    main()
