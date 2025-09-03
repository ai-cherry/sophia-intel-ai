"""
Enhanced Environment configuration loader for Sophia Intel AI.
Supports loading from .env files, Pulumi ESC with hierarchical environments,
caching, refresh mechanisms, and comprehensive validation.

Following ADR-006: Configuration Management Standardization
"""

import hashlib
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Union

from dotenv import load_dotenv

from app.core.ai_logger import logger as ai_logger
from app.core.circuit_breaker import with_circuit_breaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnvConfig:
    """Complete environment configuration for all services following ADR-006."""

    # =============================================================================
    # ENVIRONMENT METADATA
    # =============================================================================
    environment_name: str = "dev"
    environment_type: str = "development"  # development, staging, production
    domain: str = "localhost"
    region: str = "local"
    loaded_from: str = ""  # Track source: esc, env_file, environment
    loaded_at: datetime = field(default_factory=datetime.now)
    config_hash: str = ""

    # =============================================================================
    # LLM PROVIDER CONFIGURATION
    # =============================================================================

    # Primary Gateway (Portkey)
    openai_base_url: str = "https://api.portkey.ai/v1"
    openai_api_key: str = ""
    portkey_api_key: str = ""
    portkey_base_url: str = "https://api.portkey.ai/v1"

    # Portkey Virtual Keys
    portkey_openrouter_vk: str = ""
    portkey_anthropic_vk: str = ""
    portkey_together_vk: str = ""
    portkey_xai_vk: str = ""

    # Direct Provider APIs
    agno_api_key: str = ""
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    together_api_key: str = ""
    deepseek_api_key: str = ""
    xai_api_key: str = ""
    perplexity_api_key: str = ""
    gemini_api_key: str = ""
    mistral_api_key: str = ""
    cohere_api_key: str = ""

    # =============================================================================
    # MEMORY AND VECTOR STORE CONFIGURATION
    # =============================================================================
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: str = ""
    weaviate_batch_size: int = 100
    weaviate_timeout: int = 30

    # MEM0 Integration
    mem0_api_key: str = ""
    mem0_account_name: str = ""
    mem0_account_id: str = ""

    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================

    # PostgreSQL (Neon)
    postgres_url: str = ""
    neon_api_key: str = ""
    neon_rest_api_endpoint: str = ""
    neon_project_id: str = ""
    neon_branch_id: str = ""
    neon_password: str = ""
    postgres_password: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_username: str = "default"
    redis_password: str = ""
    redis_user_key: str = ""
    redis_account_key: str = ""

    # =============================================================================
    # INFRASTRUCTURE CONFIGURATION
    # =============================================================================
    pulumi_access_token: str = ""
    fly_api_token: str = ""
    lambda_api_key: str = ""
    lambda_cloud_endpoint: str = "https://cloud.lambdalabs.com/api/v1"
    docker_pat: str = ""
    github_token: str = ""

    # =============================================================================
    # SEARCH AND DATA APIs
    # =============================================================================
    huggingface_api_token: str = ""
    exa_api_key: str = ""
    brave_api_key: str = ""
    serper_api_key: str = ""
    tavily_api_key: str = ""
    newsdata_api_key: str = ""

    # =============================================================================
    # OBSERVABILITY AND MONITORING
    # =============================================================================
    langfuse_api_key: str = ""
    langchain_api_key: str = ""
    helicone_api_key: str = ""
    arize_api_key: str = ""
    arize_space_id: str = ""
    dd_api_key: str = ""

    # =============================================================================
    # SECURITY CONFIGURATION
    # =============================================================================
    jwt_secret: str = ""
    api_secret_key: str = ""
    encryption_key: str = ""
    neon_auth_jwks_url: str = ""

    # =============================================================================
    # SERVICE URLs
    # =============================================================================
    unified_api_url: str = "http://localhost:8003"
    agno_bridge_url: str = "http://localhost:7777"
    frontend_url: str = "http://localhost:3333"
    mcp_server_url: str = "http://localhost:8004"
    vector_store_url: str = "http://localhost:8005"

    # =============================================================================
    # APPLICATION CONFIGURATION
    # =============================================================================
    playground_port: int = 7777
    playground_host: str = "127.0.0.1"
    agent_ui_port: int = 3333
    agent_ui_host: str = "127.0.0.1"
    local_dev_mode: bool = True

    # =============================================================================
    # FEATURE FLAGS
    # =============================================================================
    enable_streaming: bool = True
    enable_memory: bool = True
    enable_teams: bool = True
    enable_workflows: bool = True
    enable_apps: bool = True
    enable_evaluation_gates: bool = True
    enable_runner_gate: bool = True
    enable_safety_checks: bool = True
    enable_runner_writes: bool = True
    enable_git_writes: bool = True
    enable_file_writes: bool = True
    debug_mode: bool = False
    verbose_logging: bool = False

    # =============================================================================
    # PERFORMANCE AND COST CONTROLS
    # =============================================================================
    max_workers: int = 10
    timeout_seconds: int = 120
    max_retries: int = 3
    batch_size: int = 10
    parallel_requests: int = 5
    daily_budget_usd: float = 100.0
    max_tokens_per_request: int = 4096
    max_requests_per_minute: int = 60
    api_rate_limit: int = 100
    api_rate_window: int = 60

    # =============================================================================
    # MODEL CONFIGURATION
    # =============================================================================
    # Orchestrator model (restricted to GPT-5)
    orchestrator_model: str = "openai/gpt-5"

    # Agent swarm allowed models
    agent_swarm_models: str = "x-ai/grok-code-fast-1,google/gemini-2.5-flash,google/gemini-2.5-pro,deepseek/deepseek-chat-v3-0324,deepseek/deepseek-chat-v3.1,qwen/qwen3-30b-a3b,qwen/qwen3-coder,openai/gpt-5,deepseek/deepseek-r1-0528:free,openai/gpt-4o-mini,z-ai/glm-4.5"

    # Legacy model tiers (deprecated)
    default_fast_models: str = "groq/llama-3.2-90b-text-preview,openai/gpt-4o-mini"
    default_balanced_models: str = "openai/gpt-4o,anthropic/claude-3.5-sonnet"
    default_heavy_models: str = "anthropic/claude-3.5-sonnet,qwen/qwen-2.5-coder-32b-instruct,openai/gpt-4o"

    # Embedding models (Together AI via Portkey)
    embedding_primary_model: str = "togethercomputer/m2-bert-80M-8k-retrieval"
    embedding_fallback_models: str = "BAAI/bge-large-en-v1.5,BAAI/bge-base-en-v1.5"
    embedding_cache_enabled: bool = True
    embedding_cache_ttl: int = 3600
    embedding_similarity_threshold: float = 0.95
    embedding_batch_size: int = 32

    # Legacy embedding tiers (deprecated)
    embed_model_tier_s: str = "voyage-3-large"
    embed_model_tier_a: str = "cohere/embed-multilingual-v3.0"
    embed_model_tier_b: str = "BAAI/bge-base-en-v1.5"


class PulumiESCClient:
    """Enhanced Pulumi ESC client with caching and error handling."""

    def __init__(self):
        self.cache: dict[str, dict] = {}
        self.cache_ttl = 300  # 5 minutes
        self.cache_timestamps: dict[str, datetime] = {}

    def is_available(self) -> bool:
        """Check if Pulumi ESC CLI is available."""
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

    def open_environment(self, environment: str, force_refresh: bool = False) -> Optional[dict]:
        """
        Open a Pulumi ESC environment with caching.
        
        Args:
            environment: Environment name (e.g., "dev", "staging", "prod")
            force_refresh: Force refresh of cached data
            
        Returns:
            Environment configuration dictionary or None if failed
        """
        # Check cache first
        if not force_refresh and self._is_cached(environment):
            logger.info(f"Using cached ESC environment: {environment}")
            return self.cache[environment]

        try:
            logger.info(f"Loading ESC environment: {environment}")
            result = subprocess.run(
                ["esc", "env", "open", environment, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                env_data = json.loads(result.stdout)

                # Cache the result
                self.cache[environment] = env_data
                self.cache_timestamps[environment] = datetime.now()

                logger.info(f"Successfully loaded ESC environment: {environment}")
                return env_data
            else:
                logger.error(f"Failed to load ESC environment {environment}: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout loading ESC environment: {environment}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from ESC environment {environment}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading ESC environment {environment}: {e}")
            return None

    def _is_cached(self, environment: str) -> bool:
        """Check if environment data is cached and not expired."""
        if environment not in self.cache or environment not in self.cache_timestamps:
            return False

        cache_age = datetime.now() - self.cache_timestamps[environment]
        return cache_age < timedelta(seconds=self.cache_ttl)

    def refresh_cache(self, environment: str) -> bool:
        """Refresh cached environment data."""
        result = self.open_environment(environment, force_refresh=True)
        return result is not None

    def list_environments(self) -> list[str]:
        """List available ESC environments."""
        try:
            result = subprocess.run(
                ["esc", "env", "ls", "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                environments = json.loads(result.stdout)
                return [env["name"] for env in environments]
            else:
                logger.error(f"Failed to list ESC environments: {result.stderr}")
                return []

        except Exception as e:
            logger.error(f"Error listing ESC environments: {e}")
            return []


class EnhancedEnvLoader:
    """
    Enhanced environment loader with Pulumi ESC integration, caching,
    and comprehensive validation following ADR-006.
    """

    def __init__(self, env_file: Optional[str] = None, environment: Optional[str] = None):
        """
        Initialize enhanced environment loader.
        
        Args:
            env_file: Path to .env file (optional)
            environment: ESC environment name (optional, auto-detected if None)
        """
        self.env_file = env_file or ".env.local"
        self.config = EnvConfig()
        self.esc_client = PulumiESCClient()
        self.environment = environment or self._detect_environment()
        self.fallback_files = [
            ".env.local",
            ".env.complete",
            ".env",
            "agent-ui/.env.local"
        ]

    def _detect_environment(self) -> str:
        """Auto-detect environment from various sources."""
        # Priority order: ENV var > hostname > git branch > default

        # Check environment variables
        if env := os.getenv("SOPHIA_ENVIRONMENT"):
            return env
        if env := os.getenv("ENVIRONMENT"):
            return env
        if env := os.getenv("NODE_ENV"):
            if env == "production":
                return "prod"
            elif env == "staging":
                return "staging"
            else:
                return "dev"

        # Check hostname patterns
        hostname = os.getenv("HOSTNAME", "")
        if "prod" in hostname or "production" in hostname:
            return "prod"
        elif "staging" in hostname or "stage" in hostname:
            return "staging"

        # Check if running on Fly.io
        if os.getenv("FLY_APP_NAME"):
            app_name = os.getenv("FLY_APP_NAME", "")
            if "prod" in app_name:
                return "prod"
            elif "staging" in app_name or "stage" in app_name:
                return "staging"

        # Default to development
        return "dev"

    def load_configuration(self, force_refresh: bool = False) -> EnvConfig:
        """
        Load configuration with intelligent source selection and fallback.
        
        Args:
            force_refresh: Force refresh of cached ESC data
            
        Returns:
            Loaded and validated configuration
        """
        logger.info(f"Loading configuration for environment: {self.environment}")

        # Strategy 1: Try Pulumi ESC first (production preferred approach)
        if self._should_use_esc():
            if self._load_from_esc(force_refresh):
                logger.info("Successfully loaded configuration from Pulumi ESC")
                self.config.loaded_from = f"esc:{self.environment}"
                self.config.loaded_at = datetime.now()
                return self.config
            else:
                logger.warning("Failed to load from ESC, falling back to .env files")

        # Strategy 2: Fallback to .env files
        if self._load_from_env_files():
            logger.info("Successfully loaded configuration from .env files")
            self.config.loaded_from = "env_files"
            self.config.loaded_at = datetime.now()
        else:
            # Strategy 3: Load from existing environment variables
            logger.warning("Failed to load from files, using environment variables")
            self._load_from_environment_vars()
            self.config.loaded_from = "environment_vars"
            self.config.loaded_at = datetime.now()

        return self.config

    def _should_use_esc(self) -> bool:
        """Determine if ESC should be used based on environment and availability."""
        # Force ESC usage with environment variable
        if os.getenv("USE_PULUMI_ESC", "").lower() == "true":
            return True

        # Use ESC for non-development environments if available
        if self.environment in ["staging", "prod"] and self.esc_client.is_available():
            return True

        # Use ESC for development if explicitly configured and available
        if self.environment == "dev" and self.esc_client.is_available():
            # Check if ESC environment exists
            environments = self.esc_client.list_environments()
            return self.environment in environments

        return False

    def _load_from_esc(self, force_refresh: bool = False) -> bool:
        """Load configuration from Pulumi ESC."""
        try:
            env_data = self.esc_client.open_environment(self.environment, force_refresh)
            if not env_data:
                return False

            # Extract environment variables from ESC response
            env_vars = env_data.get("environmentVariables", {})

            # Set environment variables from ESC
            for key, value in env_vars.items():
                os.environ[key] = str(value)

            # Update config from loaded environment variables
            self._update_config_from_env()

            # Set environment metadata
            self.config.environment_name = self.environment
            self._set_environment_metadata(env_data)

            return True

        except Exception as e:
            logger.error(f"Error loading from ESC: {e}")
            return False

    def _load_from_env_files(self) -> bool:
        """Load configuration from .env files with fallback chain."""
        loaded = False

        for env_file in self.fallback_files:
            env_path = Path(env_file)
            if env_path.exists():
                try:
                    load_dotenv(env_path, override=True)
                    logger.info(f"Loaded environment from: {env_file}")
                    loaded = True
                    break
                except Exception as e:
                    logger.warning(f"Failed to load {env_file}: {e}")
                    continue

        if loaded:
            self._update_config_from_env()
            self.config.environment_name = self.environment

        return loaded

    def _load_from_environment_vars(self) -> None:
        """Load configuration from existing environment variables as fallback."""
        logger.info("Loading configuration from environment variables")
        self._update_config_from_env()
        self.config.environment_name = self.environment

    @with_circuit_breaker("external_api")
    def _update_config_from_env(self) -> None:
        """Update config object from environment variables with comprehensive mapping."""

        # Environment metadata
        self.config.environment_name = os.getenv("ENVIRONMENT", self.config.environment_name)
        self.config.environment_type = os.getenv("ENV_TYPE", self.config.environment_type)
        self.config.domain = os.getenv("DOMAIN", self.config.domain)
        self.config.region = os.getenv("REGION", self.config.region)

        # LLM Provider Configuration
        self.config.openai_base_url = os.getenv("OPENAI_BASE_URL", self.config.openai_base_url)
        self.config.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.config.portkey_api_key = os.getenv("PORTKEY_API_KEY", "")
        self.config.portkey_base_url = os.getenv("PORTKEY_BASE_URL", self.config.portkey_base_url)

        # Portkey Virtual Keys
        self.config.portkey_openrouter_vk = os.getenv("PORTKEY_OPENROUTER_VK", "")
        self.config.portkey_anthropic_vk = os.getenv("PORTKEY_ANTHROPIC_VK", "")
        self.config.portkey_together_vk = os.getenv("PORTKEY_TOGETHER_VK", "")
        self.config.portkey_xai_vk = os.getenv("PORTKEY_XAI_VK", "")

        # Direct Provider APIs
        self.config.agno_api_key = os.getenv("AGNO_API_KEY", "")
        self.config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.config.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.config.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.config.together_api_key = os.getenv("TOGETHER_API_KEY", "")
        self.config.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.config.xai_api_key = os.getenv("XAI_API_KEY", "")
        self.config.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY", "")
        self.config.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.config.mistral_api_key = os.getenv("MISTRAL_API_KEY", "")
        self.config.cohere_api_key = os.getenv("COHERE_API_KEY", "")

        # Memory and Vector Store
        self.config.weaviate_url = os.getenv("WEAVIATE_URL", self.config.weaviate_url)
        self.config.weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "")
        self.config.weaviate_batch_size = int(os.getenv("WEAVIATE_BATCH_SIZE", "100"))
        self.config.weaviate_timeout = int(os.getenv("WEAVIATE_TIMEOUT", "30"))

        # MEM0
        self.config.mem0_api_key = os.getenv("MEM0_API_KEY", "")
        self.config.mem0_account_name = os.getenv("MEM0_ACCOUNT_NAME", "")
        self.config.mem0_account_id = os.getenv("MEM0_ACCOUNT_ID", "")

        # Database Configuration
        self.config.postgres_url = os.getenv("POSTGRES_URL", "")
        self.config.neon_api_key = os.getenv("NEON_API_KEY", "")
        self.config.neon_rest_api_endpoint = os.getenv("NEON_REST_API_ENDPOINT", "")
        self.config.neon_project_id = os.getenv("NEON_PROJECT_ID", "")
        self.config.neon_branch_id = os.getenv("NEON_BRANCH_ID", "")
        self.config.neon_password = os.getenv("NEON_PASSWORD", "")
        self.config.postgres_password = os.getenv("POSTGRES_PASSWORD", "")

        # Redis
        self.config.redis_url = os.getenv("REDIS_URL", self.config.redis_url)
        self.config.redis_host = os.getenv("REDIS_HOST", self.config.redis_host)
        self.config.redis_port = int(os.getenv("REDIS_PORT", str(self.config.redis_port)))
        self.config.redis_username = os.getenv("REDIS_USERNAME", self.config.redis_username)
        self.config.redis_password = os.getenv("REDIS_PASSWORD", "")
        self.config.redis_user_key = os.getenv("REDIS_USER_KEY", "")
        self.config.redis_account_key = os.getenv("REDIS_ACCOUNT_KEY", "")

        # Infrastructure
        self.config.pulumi_access_token = os.getenv("PULUMI_ACCESS_TOKEN", "")
        self.config.fly_api_token = os.getenv("FLY_API_TOKEN", "")
        self.config.lambda_api_key = os.getenv("LAMBDA_API_KEY", "")
        self.config.lambda_cloud_endpoint = os.getenv("LAMBDA_CLOUD_ENDPOINT", self.config.lambda_cloud_endpoint)
        self.config.docker_pat = os.getenv("DOCKER_PAT", "")
        self.config.github_token = os.getenv("GITHUB_TOKEN", "")

        # Search and Data APIs
        self.config.huggingface_api_token = os.getenv("HUGGINGFACE_API_TOKEN", "")
        self.config.exa_api_key = os.getenv("EXA_API_KEY", "")
        self.config.brave_api_key = os.getenv("BRAVE_API_KEY", "")
        self.config.serper_api_key = os.getenv("SERPER_API_KEY", "")
        self.config.tavily_api_key = os.getenv("TAVILY_API_KEY", "")
        self.config.newsdata_api_key = os.getenv("NEWSDATA_API_KEY", "")

        # Observability
        self.config.langfuse_api_key = os.getenv("LANGFUSE_API_KEY", "")
        self.config.langchain_api_key = os.getenv("LANGCHAIN_API_KEY", "")
        self.config.helicone_api_key = os.getenv("HELICONE_API_KEY", "")
        self.config.arize_api_key = os.getenv("ARIZE_API_KEY", "")
        self.config.arize_space_id = os.getenv("ARIZE_SPACE_ID", "")
        self.config.dd_api_key = os.getenv("DD_API_KEY", "")

        # Security
        self.config.jwt_secret = os.getenv("JWT_SECRET", "")
        self.config.api_secret_key = os.getenv("API_SECRET_KEY", "")
        self.config.encryption_key = os.getenv("ENCRYPTION_KEY", "")
        self.config.neon_auth_jwks_url = os.getenv("NEON_AUTH_JWKS_URL", "")

        # Service URLs
        self.config.unified_api_url = os.getenv("UNIFIED_API_URL", self.config.unified_api_url)
        self.config.agno_bridge_url = os.getenv("AGNO_BRIDGE_URL", self.config.agno_bridge_url)
        self.config.frontend_url = os.getenv("FRONTEND_URL", self.config.frontend_url)
        self.config.mcp_server_url = os.getenv("MCP_SERVER_URL", self.config.mcp_server_url)
        self.config.vector_store_url = os.getenv("VECTOR_STORE_URL", self.config.vector_store_url)

        # Application
        self.config.playground_port = int(os.getenv("PLAYGROUND_PORT", str(self.config.playground_port)))
        self.config.playground_host = os.getenv("PLAYGROUND_HOST", self.config.playground_host)
        self.config.agent_ui_port = int(os.getenv("AGENT_UI_PORT", str(self.config.agent_ui_port)))
        self.config.agent_ui_host = os.getenv("AGENT_UI_HOST", self.config.agent_ui_host)
        self.config.local_dev_mode = os.getenv("LOCAL_DEV_MODE", "true").lower() == "true"

        # Feature Flags
        self.config.enable_streaming = os.getenv("ENABLE_STREAMING", "true").lower() == "true"
        self.config.enable_memory = os.getenv("ENABLE_MEMORY", "true").lower() == "true"
        self.config.enable_teams = os.getenv("ENABLE_TEAMS", "true").lower() == "true"
        self.config.enable_workflows = os.getenv("ENABLE_WORKFLOWS", "true").lower() == "true"
        self.config.enable_apps = os.getenv("ENABLE_APPS", "true").lower() == "true"
        self.config.enable_evaluation_gates = os.getenv("ENABLE_EVALUATION_GATES", "true").lower() == "true"
        self.config.enable_runner_gate = os.getenv("ENABLE_RUNNER_GATE", "true").lower() == "true"
        self.config.enable_safety_checks = os.getenv("ENABLE_SAFETY_CHECKS", "true").lower() == "true"
        self.config.enable_runner_writes = os.getenv("ENABLE_RUNNER_WRITES", "true").lower() == "true"
        self.config.enable_git_writes = os.getenv("ENABLE_GIT_WRITES", "true").lower() == "true"
        self.config.enable_file_writes = os.getenv("ENABLE_FILE_WRITES", "true").lower() == "true"
        self.config.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        self.config.verbose_logging = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"

        # Performance and Cost Controls
        self.config.max_workers = int(os.getenv("MAX_WORKERS", str(self.config.max_workers)))
        self.config.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", str(self.config.timeout_seconds)))
        self.config.max_retries = int(os.getenv("MAX_RETRIES", str(self.config.max_retries)))
        self.config.batch_size = int(os.getenv("BATCH_SIZE", str(self.config.batch_size)))
        self.config.parallel_requests = int(os.getenv("PARALLEL_REQUESTS", str(self.config.parallel_requests)))
        self.config.daily_budget_usd = float(os.getenv("DAILY_BUDGET_USD", str(self.config.daily_budget_usd)))
        self.config.max_tokens_per_request = int(os.getenv("MAX_TOKENS_PER_REQUEST", str(self.config.max_tokens_per_request)))
        self.config.max_requests_per_minute = int(os.getenv("MAX_REQUESTS_PER_MINUTE", str(self.config.max_requests_per_minute)))
        self.config.api_rate_limit = int(os.getenv("API_RATE_LIMIT", str(self.config.api_rate_limit)))
        self.config.api_rate_window = int(os.getenv("API_RATE_WINDOW", str(self.config.api_rate_window)))

        # Model Configuration
        self.config.orchestrator_model = os.getenv("ORCHESTRATOR_MODEL", self.config.orchestrator_model)
        self.config.agent_swarm_models = os.getenv("AGENT_SWARM_MODELS", self.config.agent_swarm_models)
        self.config.default_fast_models = os.getenv("DEFAULT_FAST_MODELS", self.config.default_fast_models)
        self.config.default_balanced_models = os.getenv("DEFAULT_BALANCED_MODELS", self.config.default_balanced_models)
        self.config.default_heavy_models = os.getenv("DEFAULT_HEAVY_MODELS", self.config.default_heavy_models)

        # Embedding Configuration
        self.config.embedding_primary_model = os.getenv("EMBEDDING_PRIMARY_MODEL", self.config.embedding_primary_model)
        self.config.embedding_fallback_models = os.getenv("EMBEDDING_FALLBACK_MODELS", self.config.embedding_fallback_models)
        self.config.embedding_cache_enabled = os.getenv("EMBEDDING_CACHE_ENABLED", "true").lower() == "true"
        self.config.embedding_cache_ttl = int(os.getenv("EMBEDDING_CACHE_TTL", str(self.config.embedding_cache_ttl)))
        self.config.embedding_similarity_threshold = float(os.getenv("EMBEDDING_SIMILARITY_THRESHOLD", str(self.config.embedding_similarity_threshold)))
        self.config.embedding_batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", str(self.config.embedding_batch_size)))

        # Legacy embedding tiers
        self.config.embed_model_tier_s = os.getenv("EMBED_MODEL_TIER_S", self.config.embed_model_tier_s)
        self.config.embed_model_tier_a = os.getenv("EMBED_MODEL_TIER_A", self.config.embed_model_tier_a)
        self.config.embed_model_tier_b = os.getenv("EMBED_MODEL_TIER_B", self.config.embed_model_tier_b)

        # Generate config hash for change detection
        config_str = json.dumps(self.__dict__, default=str, sort_keys=True)
        self.config.config_hash = hashlib.md5(config_str.encode()).hexdigest()[:16]

    def _set_environment_metadata(self, env_data: dict) -> None:
        """Set environment metadata from ESC data."""
        values = env_data.get("values", {})
        if "environment" in values:
            env_config = values["environment"]
            if isinstance(env_config, dict):
                self.config.environment_type = env_config.get("type", self.config.environment_type)
                self.config.domain = env_config.get("domain", self.config.domain)
                self.config.region = env_config.get("region", self.config.region)

    def validate_configuration(self) -> dict[str, Any]:
        """
        Comprehensive configuration validation with detailed diagnostics.
        
        Returns:
            Validation results with status and recommendations
        """
        validation = {
            "overall_status": "unknown",
            "ready_for_production": False,
            "critical_issues": [],
            "warnings": [],
            "recommendations": [],
            "component_status": {}
        }

        # LLM Gateway Validation
        gateway_status = self._validate_llm_gateway()
        validation["component_status"]["llm_gateway"] = gateway_status

        # Provider Validation
        providers_status = self._validate_providers()
        validation["component_status"]["providers"] = providers_status

        # Database Validation
        database_status = self._validate_databases()
        validation["component_status"]["databases"] = database_status

        # Infrastructure Validation
        infra_status = self._validate_infrastructure()
        validation["component_status"]["infrastructure"] = infra_status

        # Security Validation
        security_status = self._validate_security()
        validation["component_status"]["security"] = security_status

        # Determine overall status
        all_critical = all(
            status.get("status") == "healthy"
            for status in [gateway_status, providers_status, database_status]
        )

        if all_critical:
            validation["overall_status"] = "healthy"
            validation["ready_for_production"] = security_status.get("status") == "healthy"
        else:
            validation["overall_status"] = "degraded"
            validation["ready_for_production"] = False

        # Collect issues and recommendations
        for component, status in validation["component_status"].items():
            validation["critical_issues"].extend(status.get("critical_issues", []))
            validation["warnings"].extend(status.get("warnings", []))
            validation["recommendations"].extend(status.get("recommendations", []))

        return validation

    @with_circuit_breaker("external_api")
    def _validate_llm_gateway(self) -> dict[str, Any]:
        """Validate LLM gateway configuration."""
        status = {
            "status": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }

        # Check primary gateway
        if not self.config.openai_api_key and not self.config.portkey_api_key:
            status["critical_issues"].append("No LLM gateway API key configured")
            status["status"] = "unhealthy"
        elif self.config.portkey_api_key:
            status["status"] = "healthy"
            status["recommendations"].append("Using Portkey gateway - excellent choice for production")
        else:
            status["status"] = "degraded"
            status["warnings"].append("Using direct OpenAI API instead of Portkey gateway")

        return status

    @with_circuit_breaker("external_api")
    def _validate_providers(self) -> dict[str, Any]:
        """Validate LLM provider configuration."""
        status = {
            "status": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }

        providers = [
            self.config.anthropic_api_key,
            self.config.openrouter_api_key,
            self.config.groq_api_key,
            self.config.together_api_key
        ]

        active_providers = sum(1 for key in providers if key)

        if active_providers == 0:
            status["critical_issues"].append("No LLM provider API keys configured")
            status["status"] = "unhealthy"
        elif active_providers == 1:
            status["status"] = "degraded"
            status["warnings"].append("Only one LLM provider configured - consider adding fallbacks")
        else:
            status["status"] = "healthy"
            status["recommendations"].append(f"Good provider redundancy with {active_providers} providers")

        return status

    def _validate_databases(self) -> dict[str, Any]:
        """Validate database configuration."""
        status = {
            "status": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }

        issues = 0

        # Check PostgreSQL
        if not self.config.postgres_url:
            status["warnings"].append("No PostgreSQL connection configured")
            issues += 1

        # Check Redis
        if not self.config.redis_url:
            status["warnings"].append("No Redis connection configured")
            issues += 1

        # Check Weaviate
        if not self.config.weaviate_url:
            status["critical_issues"].append("No Weaviate vector database configured")
            issues += 1

        if issues == 0:
            status["status"] = "healthy"
        elif issues <= 2:
            status["status"] = "degraded"
        else:
            status["status"] = "unhealthy"

        return status

    def _validate_infrastructure(self) -> dict[str, Any]:
        """Validate infrastructure configuration."""
        status = {
            "status": "healthy",
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }

        if self.config.environment_name == "prod":
            if not self.config.fly_api_token:
                status["warnings"].append("No Fly.io API token for production deployment")
            if not self.config.pulumi_access_token:
                status["warnings"].append("No Pulumi access token for infrastructure management")

        return status

    def _validate_security(self) -> dict[str, Any]:
        """Validate security configuration."""
        status = {
            "status": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }

        issues = 0

        # Check JWT secret
        if not self.config.jwt_secret:
            status["critical_issues"].append("No JWT secret configured")
            issues += 1
        elif len(self.config.jwt_secret) < 32:
            status["warnings"].append("JWT secret is too short (< 32 characters)")

        # Check API secret
        if not self.config.api_secret_key:
            status["warnings"].append("No API secret key configured")

        # Production-specific security checks
        if self.config.environment_name == "prod":
            if self.config.debug_mode:
                status["critical_issues"].append("Debug mode enabled in production")
                issues += 1
            if self.config.verbose_logging:
                status["warnings"].append("Verbose logging enabled in production")

        status["status"] = "unhealthy" if issues > 0 else "healthy"
        return status

    def refresh_configuration(self) -> bool:
        """Refresh configuration from source."""
        try:
            old_hash = self.config.config_hash
            self.load_configuration(force_refresh=True)
            new_hash = self.config.config_hash

            if old_hash != new_hash:
                logger.info("Configuration refreshed - changes detected")
                return True
            else:
                logger.info("Configuration refreshed - no changes")
                return False

        except Exception as e:
            logger.error(f"Failed to refresh configuration: {e}")
            return False

    def get_config(self) -> EnvConfig:
        """Get the loaded configuration."""
        return self.config

    def print_status(self, detailed: bool = False) -> None:
        """Print comprehensive configuration status."""
        validation = self.validate_configuration()

        logger.info("\n" + "="*80)
        logger.info("🔧 SOPHIA INTEL AI - ENVIRONMENT CONFIGURATION STATUS")
        logger.info("="*80)

        # Environment info
        logger.info(f"\n📋 Environment: {self.config.environment_name} ({self.config.environment_type})")
        logger.info(f"📂 Loaded from: {self.config.loaded_from}")
        logger.info(f"⏰ Loaded at: {self.config.loaded_at.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🆔 Config hash: {self.config.config_hash}")

        # Overall status
        status_icon = "🟢" if validation["overall_status"] == "healthy" else "🟡" if validation["overall_status"] == "degraded" else "🔴"
        logger.info(f"\n{status_icon} Overall Status: {validation['overall_status'].upper()}")
        logger.info(f"🚀 Production Ready: {'YES' if validation['ready_for_production'] else 'NO'}")

        # Component status
        logger.info("\n📊 Component Status:")
        for component, status in validation["component_status"].items():
            status_icon = "🟢" if status["status"] == "healthy" else "🟡" if status["status"] == "degraded" else "🔴"
            logger.info(f"  {status_icon} {component.replace('_', ' ').title()}: {status['status']}")

        # Issues and warnings
        if validation["critical_issues"]:
            logger.info(f"\n❌ Critical Issues ({len(validation['critical_issues'])}):")
            for issue in validation["critical_issues"]:
                logger.info(f"  • {issue}")

        if validation["warnings"]:
            logger.info(f"\n⚠️  Warnings ({len(validation['warnings'])}):")
            for warning in validation["warnings"]:
                logger.info(f"  • {warning}")

        if validation["recommendations"]:
            logger.info(f"\n💡 Recommendations ({len(validation['recommendations'])}):")
            for rec in validation["recommendations"]:
                logger.info(f"  • {rec}")

        if detailed:
            self._print_detailed_config()

        logger.info("="*80)

    def _print_detailed_config(self) -> None:
        """Print detailed configuration for debugging."""
        logger.info("\n🔍 Detailed Configuration:")
        logger.info("  • Service URLs:")
        logger.info(f"    - API: {self.config.unified_api_url}")
        logger.info(f"    - Bridge: {self.config.agno_bridge_url}")
        logger.info(f"    - Frontend: {self.config.frontend_url}")
        logger.info("  • Databases:")
        logger.info(f"    - Weaviate: {self.config.weaviate_url}")
        logger.info(f"    - Redis: {self.config.redis_host}:{self.config.redis_port}")
        logger.info("  • Models:")
        logger.info(f"    - Fast: {self.config.default_fast_models}")
        logger.info(f"    - Balanced: {self.config.default_balanced_models}")
        logger.info("  • Limits:")
        logger.info(f"    - Budget: ${self.config.daily_budget_usd}/day")
        logger.info(f"    - Tokens: {self.config.max_tokens_per_request}")
        logger.info(f"    - Rate: {self.config.api_rate_limit}/min")


# =============================================================================
# GLOBAL CONFIGURATION MANAGEMENT
# =============================================================================

# Global singleton instance
_env_loader: Optional[EnhancedEnvLoader] = None

def get_env_config(environment: Optional[str] = None, force_refresh: bool = False) -> EnvConfig:
    """
    Get the global environment configuration with caching.
    
    Args:
        environment: Override environment detection
        force_refresh: Force refresh of configuration
        
    Returns:
        EnvConfig object with all settings
    """
    global _env_loader

    if _env_loader is None or force_refresh:
        _env_loader = EnhancedEnvLoader(environment=environment)
        _env_loader.load_configuration(force_refresh=force_refresh)

    return _env_loader.get_config()

def validate_environment(environment: Optional[str] = None) -> dict[str, Any]:
    """
    Validate environment configuration with detailed diagnostics.
    
    Args:
        environment: Override environment detection
        
    Returns:
        Comprehensive validation results
    """
    config = get_env_config(environment)
    loader = EnhancedEnvLoader(environment=environment)
    loader.config = config
    return loader.validate_configuration()

def print_env_status(detailed: bool = False, environment: Optional[str] = None) -> None:
    """
    Print environment configuration status.
    
    Args:
        detailed: Include detailed configuration information
        environment: Override environment detection
    """
    config = get_env_config(environment)
    loader = EnhancedEnvLoader(environment=environment)
    loader.config = config
    loader.print_status(detailed=detailed)

def refresh_env_config() -> bool:
    """
    Refresh global environment configuration.
    
    Returns:
        True if configuration changed, False otherwise
    """
    global _env_loader
    if _env_loader:
        return _env_loader.refresh_configuration()
    return False

def get_service_manifest() -> dict[str, Any]:
    """
    Generate a service manifest with all configuration needed by clients.
    
    Returns:
        JSON-serializable manifest with service URLs, models, and settings
    """
    config = get_env_config()

    # Parse model lists
    agent_models = [m.strip() for m in config.agent_swarm_models.split(',')]
    embedding_fallbacks = [m.strip() for m in config.embedding_fallback_models.split(',')]

    manifest = {
        "environment": {
            "name": config.environment_name,
            "type": config.environment_type,
            "domain": config.domain,
            "region": config.region,
            "loaded_from": config.loaded_from,
            "loaded_at": config.loaded_at.isoformat(),
            "config_hash": config.config_hash
        },
        "services": {
            "unified_api": {
                "url": config.unified_api_url,
                "health": f"{config.unified_api_url}/healthz",
                "docs": f"{config.unified_api_url}/docs"
            },
            "frontend": {
                "url": config.frontend_url
            },
            "mcp_server": {
                "url": config.mcp_server_url
            },
            "vector_store": {
                "url": config.vector_store_url
            },
            "weaviate": {
                "url": config.weaviate_url
            },
            "redis": {
                "host": config.redis_host,
                "port": config.redis_port
            }
        },
        "models": {
            "orchestrator": {
                "model": config.orchestrator_model,
                "description": "Primary orchestrator model (GPT-5)"
            },
            "agent_swarm": {
                "allowed_models": agent_models,
                "description": "Models available for agent swarm selection"
            },
            "embeddings": {
                "primary": config.embedding_primary_model,
                "fallbacks": embedding_fallbacks,
                "cache": {
                    "enabled": config.embedding_cache_enabled,
                    "ttl_seconds": config.embedding_cache_ttl,
                    "similarity_threshold": config.embedding_similarity_threshold
                },
                "batch_size": config.embedding_batch_size
            }
        },
        "features": {
            "streaming": config.enable_streaming,
            "memory": config.enable_memory,
            "teams": config.enable_teams,
            "workflows": config.enable_workflows,
            "apps": config.enable_apps,
            "evaluation_gates": config.enable_evaluation_gates,
            "safety_checks": config.enable_safety_checks
        },
        "limits": {
            "daily_budget_usd": config.daily_budget_usd,
            "max_tokens_per_request": config.max_tokens_per_request,
            "max_requests_per_minute": config.max_requests_per_minute,
            "api_rate_limit": config.api_rate_limit,
            "api_rate_window": config.api_rate_window
        },
        "ports": {
            "api": 8003,
            "frontend": 3000,
            "mcp": 8004,
            "vector_store": 8005
        },
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

    return manifest

async def check_service_health() -> dict[str, Any]:
    """
    Check health status of all configured services.
    
    Returns:
        Health status for each service
    """
    import asyncio

    import aiohttp

    config = get_env_config()
    health_status = {}

    services_to_check = [
        ("unified_api", f"{config.unified_api_url}/healthz"),
        ("weaviate", f"{config.weaviate_url}/v1/.well-known/ready"),
    ]

    async def check_service(name: str, url: str) -> tuple[str, dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        return name, {"status": "healthy", "latency_ms": 0}
                    else:
                        return name, {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except asyncio.TimeoutError:
            return name, {"status": "timeout", "error": "Request timed out"}
        except Exception as e:
            return name, {"status": "error", "error": str(e)}

    # Check services in parallel
    tasks = [check_service(name, url) for name, url in services_to_check]
    results = await asyncio.gather(*tasks)

    for name, status in results:
        health_status[name] = status

    # Check Redis separately (different protocol)
    try:
        import redis
        r = redis.Redis(host=config.redis_host, port=config.redis_port,
                       password=config.redis_password, socket_timeout=5)
        r.ping()
        health_status["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["redis"] = {"status": "error", "error": str(e)}

    return health_status


if __name__ == "__main__":
    # Enhanced CLI for testing and diagnostics
    import argparse

    parser = argparse.ArgumentParser(description="Sophia Intel AI Environment Configuration")
    parser.add_argument("--environment", "-e", choices=["dev", "staging", "prod"],
                       help="Override environment detection")
    parser.add_argument("--detailed", "-d", action="store_true",
                       help="Show detailed configuration")
    parser.add_argument("--validate", "-v", action="store_true",
                       help="Run validation only")
    parser.add_argument("--refresh", "-r", action="store_true",
                       help="Force refresh configuration")

    args = parser.parse_args()

    logger.info("🚀 Sophia Intel AI - Environment Configuration Loader")
    logger.info("Following ADR-006: Configuration Management Standardization")

    try:
        if args.validate:
            validation = validate_environment(args.environment)
            logger.info(f"\nValidation Status: {validation['overall_status']}")
            logger.info(f"Production Ready: {validation['ready_for_production']}")
        else:
            config = get_env_config(args.environment, args.refresh)
            print_env_status(args.detailed, args.environment)

            logger.info("\n✅ Configuration loaded successfully!")
            logger.info(f"Environment: {config.environment_name}")
            logger.info(f"Loaded from: {config.loaded_from}")

    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        logger.info(f"\n❌ Configuration loading failed: {e}")
        exit(1)
