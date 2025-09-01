"""
Unified Sophia Intel AI Server
Main entry point for the consolidated agent system with real APIs.
NO MOCKS - Production ready deployment.

Following ADR-006: Configuration Management Standardization
- Uses enhanced EnvLoader with Pulumi ESC integration
- Single source of truth for all environment configuration
- Proper secret management and validation
"""

import uvicorn
import sys
import logging
from pathlib import Path

# Import enhanced configuration system following ADR-006
from app.config.env_loader import get_env_config, validate_environment, print_env_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

def main():
    """Main entry point with enhanced configuration management."""
    
    print("🚀 Starting Unified Sophia Intel AI Server...")
    print("=" * 80)
    print("✅ ADR-006: Configuration Management Standardization")
    print("✅ Enhanced EnvLoader with Pulumi ESC support")
    print("✅ Real API integrations - NO MOCKS")
    print("✅ Production-ready endpoints")
    print("✅ Agent UI integration")
    print("✅ MCP protocol support")
    print("=" * 80)
    
    # Load and validate configuration
    try:
        config = get_env_config()
        logger.info(f"✅ Configuration loaded from: {config.loaded_from}")
        
        # Validate environment
        validation = validate_environment()
        if not validation.get("ready_for_production", False) and config.environment_name == "prod":
            logger.warning("⚠️  Production environment has configuration issues!")
            for issue in validation.get("critical_issues", []):
                logger.error(f"❌ {issue}")
        
        # Print status in development mode
        if config.local_dev_mode:
            print_env_status(detailed=True)
            
    except Exception as e:
        logger.error(f"❌ Configuration loading failed: {e}")
        print(f"\n❌ Failed to load configuration: {e}")
        print("Please check your environment configuration or Pulumi ESC setup")
        return 1
    
    # Import the unified server (after config is loaded)
    try:
        from app.api.unified_server import app, server_config
        
        # Use configuration values
        host = config.playground_host if config.environment_name == "dev" else "0.0.0.0"
        port = server_config.PORT
        
        # Development mode configuration
        reload = config.debug_mode and config.local_dev_mode
        log_level = "debug" if config.debug_mode else "info"
        
        print(f"\n🌐 Server Configuration:")
        print(f"  • Environment: {config.environment_name} ({config.environment_type})")
        print(f"  • Host: {host}")
        print(f"  • Port: {port}")
        print(f"  • Debug: {'ENABLED' if config.debug_mode else 'DISABLED'}")
        print(f"  • Reload: {'ENABLED' if reload else 'DISABLED'}")
        print(f"  • Log Level: {log_level.upper()}")
        print("=" * 80)
        
        # Run server with enhanced configuration
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            reload=reload,
            workers=1 if reload else config.max_workers,
            timeout_keep_alive=config.timeout_seconds,
            access_log=config.verbose_logging
        )
        
    except ImportError as e:
        logger.error(f"❌ Failed to import unified server: {e}")
        print(f"\n❌ Failed to import unified server: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        print(f"\n❌ Server startup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)