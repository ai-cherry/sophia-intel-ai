import os
import sys

def mask_secret(secret):
    if secret is None:
        return "Not Set"
    return f"***{secret[-4:]}"

def check_env_vars():
    """
    Verifies the presence of required environment variables.
    """
    print("--- Environment Variable Smoke Check ---")

    required_vars = {
        "GitHub": ["GH_FINE_GRAINED_TOKEN", "GH_CLASSIC_PAT_TOKEN"],
        "Pulumi": ["PULUMI_ACCESS_TOKEN"],
        "Qdrant": ["QDRANT_URL", "QDRANT_API_KEY"],
        "Database": ["DATABASE_URL"],
        "LLM": [
            "OPENROUTER_API_KEY", "PORTKEY_API_KEY", "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY",
            "DEEPSEEK_API_KEY", "QWEN_API_KEY", "LLAMA_API_KEY",
            "MISTRAL_API_KEY", "COHERE_API_KEY", "HUGGINGFACE_API_TOKEN",
            "AGNO_API_KEY", "LANGGRAPH_API_KEY", "LANGSMITH_API_KEY"
        ]
    }

    all_ok = True
    missing_vars = []

    github_token_present = any(os.getenv(var) for var in required_vars["GitHub"])
    if not github_token_present:
        print("❌ GitHub: At least one of GH_FINE_GRAINED_TOKEN or GH_CLASSIC_PAT_TOKEN must be set.")
        all_ok = False
        missing_vars.extend(required_vars["GitHub"])
    else:
        print("✅ GitHub: Token is present.")
        for var in required_vars["GitHub"]:
            print(f"  - {var}: {mask_secret(os.getenv(var))}")


    for category, variables in required_vars.items():
        if category == "GitHub":
            continue

        print(f"\n--- {category} ---")
        for var in variables:
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: {mask_secret(value)}")
            else:
                # Only fail for required, not optional ones
                if var in ["PULUMI_ACCESS_TOKEN", "QDRANT_URL", "QDRANT_API_KEY"]:
                     print(f"❌ {var}: Not set.")
                     all_ok = False
                     missing_vars.append(var)
                else:
                    print(f"⚪️ {var}: Not set (optional).")


    print("\n--- Summary ---")
    if all_ok:
        print("✅ All critical environment variables are present.")
        sys.exit(0)
    else:
        print(f"❌ Missing critical environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

if __name__ == "__main__":
    check_env_vars()