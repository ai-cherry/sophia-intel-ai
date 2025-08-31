"""
Unified Sophia Intel AI Server
Main entry point for the consolidated agent system with real APIs.
NO MOCKS - Production ready deployment.
"""

import uvicorn
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Add app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

def main():
    """Main entry point."""
    
    # Import the unified server
    from app.api.unified_server import app, ServerConfig
    
    print("🚀 Starting Unified Sophia Intel AI Server...")
    print("=" * 60)
    print("✅ Real API integrations - NO MOCKS")
    print("✅ Production-ready endpoints")
    print("✅ Agent UI integration")
    print("✅ MCP protocol support")
    print("=" * 60)
    
    # Determine port - use 8003 for unified server
    port = int(os.getenv("UNIFIED_API_PORT", "8003"))
    host = os.getenv("UNIFIED_API_HOST", "0.0.0.0")
    
    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )

if __name__ == "__main__":
    main()