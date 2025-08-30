"""
Environment configuration loader for Sophia Intel AI.
Supports loading from .env files, Pulumi ESC, or environment variables.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class EnvConfig:
    """Complete environment configuration for all services."""
    
    # Primary Gateway
    openai_base_url: str = "https://api.portkey.ai/v1"
    openai_api_key: str = ""
    portkey_api_key: str = ""
    
    # Provider Keys (via Portkey or direct)
    openrouter_api_key: str = ""
    anthropic_api_key: str = ""
    openai_native_api_key: str = ""
    groq_api_key: str = ""
    together_api_key: str = ""
    deepseek_api_key: str = ""
    perplexity_api_key: str = ""
    google_api_key: str = ""
    mistral_api_key: str = ""
    cohere_api_key: str = ""
    
    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    
    # Azure
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    
    # Vector DB
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: str = ""
    pinecone_api_key: str = ""
    qdrant_api_key: str = ""
    
    # Database
    database_url: str = ""
    redis_url: str = "redis://localhost:6379"
    
    # Observability
    langfuse_api_key: str = ""
    langchain_api_key: str = ""
    helicone_api_key: str = ""
    dd_api_key: str = ""
    
    # Agno
    agno_api_key: str = ""
    agno_telemetry: bool = False
    agno_workspace: str = "sophia-intel"
    
    # GitHub
    github_token: str = ""
    
    # Security
    jwt_secret: str = ""
    encryption_key: str = ""
    
    # External Services
    slack_bot_token: str = ""
    discord_bot_token: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    sendgrid_api_key: str = ""
    
    # Application
    playground_port: int = 7777
    agent_ui_port: int = 3000
    local_dev_mode: bool = True
    enable_writes: bool = True
    
    # Features
    enable_streaming: bool = True
    enable_memory: bool = True
    enable_teams: bool = True
    enable_evaluation_gates: bool = True
    
    # Performance
    max_workers: int = 10
    timeout_seconds: int = 120
    max_retries: int = 3
    
    # Cost Controls
    daily_budget_usd: float = 100.0
    max_tokens_per_request: int = 4096
    max_requests_per_minute: int = 60


class EnvLoader:
    """Loads environment configuration from various sources."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize environment loader.
        
        Args:
            env_file: Path to .env file (optional)
        """
        self.env_file = env_file or ".env"
        self.config = EnvConfig()
        self._pulumi_available = self._check_pulumi_esc()
        
    def _check_pulumi_esc(self) -> bool:
        """Check if Pulumi ESC is available and configured."""
        try:
            result = subprocess.run(
                ["esc", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
            
    def load_from_env_file(self, file_path: Optional[str] = None) -> None:
        """Load configuration from .env file."""
        env_path = Path(file_path or self.env_file)
        
        # Try multiple env file locations
        env_files = [
            env_path,
            Path(".env.complete"),
            Path(".env.local"),
            Path(".env"),
        ]
        
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file, override=True)
                print(f"✅ Loaded environment from: {env_file}")
                break
                
        # Update config from environment
        self._update_config_from_env()
        
    def load_from_pulumi_esc(self, environment: str = "sophia-intel") -> None:
        """
        Load configuration from Pulumi ESC.
        
        Args:
            environment: ESC environment name
        """
        if not self._pulumi_available:
            print("⚠️  Pulumi ESC not available, using .env file")
            self.load_from_env_file()
            return
            
        try:
            # Open ESC environment
            result = subprocess.run(
                ["esc", "env", "open", environment, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                env_data = json.loads(result.stdout)
                
                # Set environment variables from ESC
                if "environmentVariables" in env_data:
                    for key, value in env_data["environmentVariables"].items():
                        os.environ[key] = str(value)
                        
                print(f"✅ Loaded environment from Pulumi ESC: {environment}")
                self._update_config_from_env()
            else:
                print(f"❌ Failed to load from Pulumi ESC: {result.stderr}")
                self.load_from_env_file()
                
        except Exception as e:
            print(f"❌ Error loading from Pulumi ESC: {e}")
            self.load_from_env_file()
            
    def _update_config_from_env(self) -> None:
        """Update config object from environment variables."""
        # Primary Gateway
        self.config.openai_base_url = os.getenv("OPENAI_BASE_URL", self.config.openai_base_url)
        self.config.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.config.portkey_api_key = os.getenv("PORTKEY_API_KEY", "")
        
        # Provider Keys
        self.config.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.config.openai_native_api_key = os.getenv("OPENAI_NATIVE_API_KEY", "")
        self.config.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.config.together_api_key = os.getenv("TOGETHER_API_KEY", "")
        self.config.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.config.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY", "")
        self.config.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.config.mistral_api_key = os.getenv("MISTRAL_API_KEY", "")
        self.config.cohere_api_key = os.getenv("COHERE_API_KEY", "")
        
        # AWS
        self.config.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.config.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.config.aws_region = os.getenv("AWS_REGION", "us-east-1")
        
        # Vector DB
        self.config.weaviate_url = os.getenv("WEAVIATE_URL", self.config.weaviate_url)
        self.config.weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "")
        
        # Database
        self.config.database_url = os.getenv("DATABASE_URL", "")
        self.config.redis_url = os.getenv("REDIS_URL", self.config.redis_url)
        
        # Observability
        self.config.langfuse_api_key = os.getenv("LANGFUSE_API_KEY", "")
        
        # Agno
        self.config.agno_api_key = os.getenv("AGNO_API_KEY", "")
        self.config.agno_telemetry = os.getenv("AGNO_TELEMETRY", "false").lower() == "true"
        
        # Application
        self.config.playground_port = int(os.getenv("PLAYGROUND_PORT", "7777"))
        self.config.local_dev_mode = os.getenv("LOCAL_DEV_MODE", "true").lower() == "true"
        self.config.enable_writes = os.getenv("ENABLE_WRITES", "true").lower() == "true"
        
        # Features
        self.config.enable_streaming = os.getenv("ENABLE_STREAMING", "true").lower() == "true"
        self.config.enable_memory = os.getenv("ENABLE_MEMORY", "true").lower() == "true"
        self.config.enable_teams = os.getenv("ENABLE_TEAMS", "true").lower() == "true"
        
        # Performance
        self.config.max_workers = int(os.getenv("MAX_WORKERS", "10"))
        self.config.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "120"))
        
        # Cost Controls
        self.config.daily_budget_usd = float(os.getenv("DAILY_BUDGET_USD", "100"))
        self.config.max_tokens_per_request = int(os.getenv("MAX_TOKENS_PER_REQUEST", "4096"))
        
    def get_config(self) -> EnvConfig:
        """Get the loaded configuration."""
        return self.config
        
    def validate_config(self) -> Dict[str, bool]:
        """
        Validate that required keys are configured.
        
        Returns:
            Dictionary of validation results
        """
        validation = {
            "gateway_configured": bool(self.config.openai_api_key or self.config.portkey_api_key),
            "has_llm_provider": any([
                self.config.openrouter_api_key,
                self.config.anthropic_api_key,
                self.config.openai_native_api_key,
                self.config.groq_api_key,
            ]),
            "has_vector_db": bool(self.config.weaviate_url),
            "has_observability": any([
                self.config.langfuse_api_key,
                self.config.langchain_api_key,
            ]),
            "agno_configured": bool(self.config.agno_api_key or self.config.local_dev_mode),
        }
        
        validation["ready"] = (
            validation["gateway_configured"] and
            validation["has_llm_provider"]
        )
        
        return validation
        
    def print_status(self) -> None:
        """Print configuration status."""
        validation = self.validate_config()
        
        print("\n" + "="*50)
        print("🔧 ENVIRONMENT CONFIGURATION STATUS")
        print("="*50)
        
        print("\n✅ Configured:")
        if validation["gateway_configured"]:
            print("  • Gateway (Portkey/OpenAI)")
        if validation["has_llm_provider"]:
            print("  • LLM Provider(s)")
        if validation["has_vector_db"]:
            print("  • Vector Database")
        if validation["has_observability"]:
            print("  • Observability")
        if validation["agno_configured"]:
            print("  • Agno")
            
        print("\n⚠️  Missing:")
        if not validation["gateway_configured"]:
            print("  • Gateway API key")
        if not validation["has_llm_provider"]:
            print("  • LLM provider keys")
            
        if validation["ready"]:
            print("\n🎉 System is ready to run!")
        else:
            print("\n❌ Please configure missing keys in .env file")
            
        print("="*50)


# Singleton instance
_env_loader: Optional[EnvLoader] = None

def get_env_config() -> EnvConfig:
    """
    Get the global environment configuration.
    
    Returns:
        EnvConfig object with all settings
    """
    global _env_loader
    
    if _env_loader is None:
        _env_loader = EnvLoader()
        
        # Try Pulumi ESC first, fallback to .env
        if os.getenv("USE_PULUMI_ESC", "false").lower() == "true":
            _env_loader.load_from_pulumi_esc()
        else:
            _env_loader.load_from_env_file()
            
    return _env_loader.get_config()


def validate_environment() -> bool:
    """
    Validate that the environment is properly configured.
    
    Returns:
        True if ready, False otherwise
    """
    config = get_env_config()
    loader = EnvLoader()
    loader.config = config
    validation = loader.validate_config()
    
    loader.print_status()
    
    return validation["ready"]


if __name__ == "__main__":
    # Test the environment loader
    print("Testing environment configuration...")
    
    # Load and validate
    config = get_env_config()
    is_ready = validate_environment()
    
    if is_ready:
        print("\n✅ Environment successfully loaded!")
        print(f"  • Playground port: {config.playground_port}")
        print(f"  • Local dev mode: {config.local_dev_mode}")
        print(f"  • Agno workspace: {config.agno_workspace}")
    else:
        print("\n❌ Environment configuration incomplete")
        print("Please check your .env file or Pulumi ESC setup")