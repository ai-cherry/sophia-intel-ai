"""
Local Development Configuration
This configuration enables full local development with all tools working.
No external API keys required - uses local models or mock responses for testing.
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class LocalDevConfig:
    """Configuration for local development with all tools enabled."""
    
    # Enable all write operations (BE CAREFUL!)
    ENABLE_RUNNER_WRITES: bool = True
    ENABLE_GIT_WRITES: bool = True
    ENABLE_FILE_WRITES: bool = True
    
    # Safety overrides for development
    SKIP_SAFETY_GATES: bool = False  # Keep gates but allow override
    ALLOW_ALL_PATHS: bool = False  # Keep path validation for safety
    
    # Tool configuration
    TOOLS_ENABLED = {
        "fs.read": True,
        "fs.write": True,
        "fs.list": True,
        "fs.delete": True,  # Careful!
        "git.status": True,
        "git.diff": True,
        "git.add": True,
        "git.commit": True,
        "git.branch": True,
        "git.push": False,  # Keep disabled for safety
        "memory.add": True,
        "memory.search": True,
        "memory.clear": True,
        "code.search": True,
        "code.analyze": True,
        "test.run": True,
        "lint.check": True,
    }
    
    # LLM Configuration for local development
    # Option 1: Use OpenAI-compatible local server (like Ollama, LM Studio, etc.)
    LOCAL_LLM_BASE_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")
    LOCAL_LLM_API_KEY: str = "local-dev-key"  # Not needed for most local servers
    
    # Option 2: Use mock responses for testing
    USE_MOCK_LLM: bool = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
    
    # Models to use (can be local model names)
    MODELS = {
        "planner": os.getenv("LOCAL_PLANNER_MODEL", "llama3.2:latest"),
        "generator": os.getenv("LOCAL_GENERATOR_MODEL", "codellama:latest"),
        "critic": os.getenv("LOCAL_CRITIC_MODEL", "llama3.2:latest"),
        "judge": os.getenv("LOCAL_JUDGE_MODEL", "llama3.2:latest"),
        "runner": os.getenv("LOCAL_RUNNER_MODEL", "llama3.2:latest"),
    }
    
    # Database configuration
    DB_PATH: str = "tmp/supermemory.db"
    ENABLE_DB_LOGGING: bool = True
    
    # Server configuration
    API_PORT: int = 8001
    ENABLE_CORS: bool = True
    CORS_ORIGINS: list = ["*"]  # Allow all in dev
    
    # Debugging
    DEBUG_MODE: bool = True
    LOG_LEVEL: str = "DEBUG"
    TRACE_TOOLS: bool = True
    TRACE_LLM_CALLS: bool = True
    
    @classmethod
    def is_safe_for_production(cls) -> bool:
        """Check if current config is safe for production."""
        config = cls()
        unsafe_settings = []
        
        if config.ENABLE_RUNNER_WRITES:
            unsafe_settings.append("Runner writes enabled")
        if config.ENABLE_GIT_WRITES:
            unsafe_settings.append("Git writes enabled")
        if config.SKIP_SAFETY_GATES:
            unsafe_settings.append("Safety gates skipped")
        if config.ALLOW_ALL_PATHS:
            unsafe_settings.append("Path validation disabled")
        if config.CORS_ORIGINS == ["*"]:
            unsafe_settings.append("CORS allows all origins")
            
        if unsafe_settings:
            print("⚠️ WARNING: Unsafe settings for production:")
            for setting in unsafe_settings:
                print(f"  - {setting}")
            return False
        return True
    
    def get_llm_config(self, role: str = "planner"):
        """Get LLM configuration for a specific role."""
        if self.USE_MOCK_LLM:
            return {
                "base_url": None,
                "api_key": None,
                "model": "mock",
                "mock_mode": True
            }
        else:
            return {
                "base_url": self.LOCAL_LLM_BASE_URL,
                "api_key": self.LOCAL_LLM_API_KEY,
                "model": self.MODELS.get(role, "llama3.2:latest"),
                "mock_mode": False
            }

# Singleton instance
local_config = LocalDevConfig()

# Check safety on import
if not LocalDevConfig.is_safe_for_production():
    print("\n🔧 LOCAL DEVELOPMENT MODE ACTIVE")
    print("📝 All tools and write operations are ENABLED")
    print("⚠️  DO NOT use this configuration in production!\n")