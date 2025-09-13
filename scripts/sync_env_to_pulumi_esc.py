#!/usr/bin/env python3
"""
Sync Environment Variables to Pulumi ESC
Syncs .env.local credentials to Pulumi ESC for secure secret management
"""
import subprocess
import sys
from pathlib import Path
from typing import Any
import yaml
from dotenv import load_dotenv
# Color codes for terminal output
COLORS = {
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "BLUE": "\033[94m",
    "MAGENTA": "\033[95m",
    "CYAN": "\033[96m",
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
}
def print_colored(message: str, color: str = "RESET", bold: bool = False):
    """Print colored message to terminal"""
    color_code = COLORS.get(color, COLORS["RESET"])
    if bold:
        color_code = COLORS["BOLD"] + color_code
    print(f"{color_code}{message}{COLORS['RESET']}")
def load_env_file(env_path: Path) -> dict[str, str]:
    """Load environment variables from .env file"""
    if not env_path.exists():
        print_colored(f"❌ Environment file not found: {env_path}", "RED")
        return {}
    load_dotenv(env_path)
    # Read all environment variables
    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars
def check_pulumi_login():
    """Check if Pulumi is logged in"""
    try:
        result = subprocess.run(["pulumi", "whoami"], capture_output=True, text=True)
        if result.returncode == 0:
            print_colored(f"✅ Logged in to Pulumi as: {result.stdout.strip()}", "GREEN")
            return True
        else:
            print_colored("❌ Not logged in to Pulumi", "RED")
            print_colored("Run: pulumi login", "YELLOW")
            return False
    except FileNotFoundError:
        print_colored("❌ Pulumi CLI not found. Please install Pulumi first.", "RED")
        print_colored("Visit: https://www.pulumi.com/docs/install/", "YELLOW")
        return False
def create_esc_environment(env_name: str, config: dict[str, Any]):
    """Create or update Pulumi ESC environment"""
    print_colored(f"\n🔄 Creating/updating ESC environment: {env_name}", "CYAN", bold=True)
    # Convert config to YAML
    yaml_config = yaml.dump(config, default_flow_style=False)
    # Use pulumi env init or set
    try:
        # Try to create the environment
        result = subprocess.run(["pulumi", "env", "init", env_name], capture_output=True, text=True)
        if result.returncode == 0:
            print_colored(f"✅ Created environment: {env_name}", "GREEN")
        elif "already exists" in result.stderr:
            print_colored(f"ℹ️  Environment already exists: {env_name}", "YELLOW")
        # Set the environment values
        result = subprocess.run(
            ["pulumi", "env", "set", env_name, "--file", "-"],
            input=yaml_config,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print_colored("✅ Updated environment configuration", "GREEN")
        else:
            print_colored(f"❌ Failed to update environment: {result.stderr}", "RED")
    except Exception as e:
        print_colored(f"❌ Error managing ESC environment: {e}", "RED")
def sync_integrations_to_esc(env_vars: dict[str, str]):
    """Sync integration credentials to Pulumi ESC"""
    # Map environment variables to ESC structure
    esc_config = {
        "values": {
            "integrations": {
                "lattice": {
                    "apiKey": {"fn::secret": env_vars.get("LATTICE_API_KEY", "")},
                    "apiUrl": env_vars.get("LATTICE_API_URL", "https://api.latticehq.com/v1"),
                },
                "slack": {
                    "appId": env_vars.get("SLACK_APP_ID", ""),
                    "clientId": env_vars.get("SLACK_CLIENT_ID", ""),
                    "clientSecret": {"fn::secret": env_vars.get("SLACK_CLIENT_SECRET", "")},
                    "userToken": {"fn::secret": env_vars.get("SLACK_USER_TOKEN", "")},
                },
                "gong": {
                    "accessKey": env_vars.get("GONG_ACCESS_KEY", ""),
                    "clientSecret": {"fn::secret": env_vars.get("GONG_CLIENT_SECRET", "")},
                },
                "linear": {"apiKey": {"fn::secret": env_vars.get("LINEAR_API_KEY", "")}},
                "asana": {"patToken": {"fn::secret": env_vars.get("ASANA_API_TOKEN", "")}},
                "hubspot": {
                    "accessToken": {"fn::secret": env_vars.get("HUBSPOT_ACCESS_TOKEN", "")}
                },
                "looker": {
                    "clientId": env_vars.get("LOOKER_CLIENT_ID", ""),
                    "clientSecret": {"fn::secret": env_vars.get("LOOKER_CLIENT_SECRET", "")},
                },
                "airtable": {
                    "apiKey": {"fn::secret": env_vars.get("AIRTABLE_API_KEY", "")},
                    "baseId": env_vars.get("AIRTABLE_BASE_ID", ""),
                },
                "notion": {"apiKey": {"fn::secret": env_vars.get("NOTION_API_KEY", "")}},
                "elevenlabs": {"apiKey": {"fn::secret": env_vars.get("ELEVENLABS_API_KEY", "")}},
            },
            "ai": {
                "openai": {"apiKey": {"fn::secret": env_vars.get("OPENAI_API_KEY", "")}},
                "anthropic": {"apiKey": {"fn::secret": env_vars.get("ANTHROPIC_API_KEY", "")}},
                # No direct Google Gemini; use gateways (OpenRouter/AIMLAPI/Together/HF)
                "mistral": {"apiKey": {"fn::secret": env_vars.get("MISTRAL_API_KEY", "")}},
                "xai": {"apiKey": {"fn::secret": env_vars.get("XAI_API_KEY", "")}},
            },
            "database": {
                "postgres": {"url": {"fn::secret": env_vars.get("POSTGRES_URL", "")}},
                "redis": {"url": {"fn::secret": env_vars.get("REDIS_URL", "")}},
            },
            "security": {
                "jwtSecret": {"fn::secret": env_vars.get("JWT_SECRET", "")},
                "apiSecret": {"fn::secret": env_vars.get("API_SECRET_KEY", "")},
            },
        },
        "exports": {
            "environmentVariables": {
                "LATTICE_API_KEY": "${integrations.lattice.apiKey}",
                "SLACK_USER_TOKEN": "${integrations.slack.userToken}",
                "LINEAR_API_KEY": "${integrations.linear.apiKey}",
                "NOTION_API_KEY": "${integrations.notion.apiKey}",
            }
        },
    }
    return esc_config
def main():
    """Main function to sync environment variables to Pulumi ESC"""
    print_colored("\n" + "=" * 60, "CYAN")
    print_colored("🚀 Sophia Intel AI - Environment Sync to Pulumi ESC", "CYAN", bold=True)
    print_colored("=" * 60 + "\n", "CYAN")
    # Check Pulumi login
    if not check_pulumi_login():
        sys.exit(1)
    # Load environment variables
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env.local"
    print_colored(f"\n📂 Loading environment from: {env_path}", "BLUE")
    env_vars = load_env_file(env_path)
    if not env_vars:
        print_colored("❌ No environment variables found", "RED")
        sys.exit(1)
    print_colored(f"✅ Loaded {len(env_vars)} environment variables", "GREEN")
    # Count integration credentials
    integration_keys = [
        "LATTICE_API_KEY",
        "SLACK_USER_TOKEN",
        "LINEAR_API_KEY",
        "GONG_ACCESS_KEY",
        "ASANA_API_TOKEN",
        "HUBSPOT_ACCESS_TOKEN",
        "LOOKER_CLIENT_SECRET",
        "AIRTABLE_API_KEY",
        "NOTION_API_KEY",
    ]
    found_integrations = [k for k in integration_keys if k in env_vars]
    print_colored(f"\n🔗 Found {len(found_integrations)} integration credentials:", "MAGENTA")
    for key in found_integrations:
        masked_value = env_vars[key][:10] + "..." if len(env_vars[key]) > 10 else "***"
        print_colored(f"  • {key}: {masked_value}", "YELLOW")
    # Generate ESC configuration
    esc_config = sync_integrations_to_esc(env_vars)
    # Create/update ESC environments
    environments = ["sophia-intel-ai/dev", "sophia-intel-ai/staging"]
    for env_name in environments:
        create_esc_environment(env_name, esc_config)
    print_colored("\n" + "=" * 60, "GREEN")
    print_colored("✅ Environment sync complete!", "GREEN", bold=True)
    print_colored("=" * 60 + "\n", "GREEN")
    print_colored("📝 Next steps:", "CYAN", bold=True)
    print_colored("  1. Use in Pulumi stacks: environment: ['sophia-intel-ai/dev']", "YELLOW")
    print_colored("  2. Access secrets: pulumi env open sophia-intel-ai/dev", "YELLOW")
    print_colored("  3. List environments: pulumi env ls", "YELLOW")
    print_colored(
        "\n💡 All integration credentials are now securely stored in Pulumi ESC!\n", "GREEN"
    )
if __name__ == "__main__":
    main()
