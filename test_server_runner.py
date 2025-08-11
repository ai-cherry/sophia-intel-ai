#!/usr/bin/env python3
"""
Test Server Runner - Runs the enhanced MCP server with test configuration
"""

import sys
import os
import asyncio
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import test configuration
from config.test_config import settings

# Patch the settings in the enhanced server
import mcp_servers.enhanced_unified_server as server_module
server_module.settings = settings

# Replace the memory service with test version
from mcp_servers.test_memory_service import TestMemoryService
server_module.MemoryService = TestMemoryService

# Import the enhanced server
from mcp_servers.enhanced_unified_server import EnhancedUnifiedMCPServer

def run_test_server():
    """Run the enhanced MCP server with test configuration"""
    print("🚀 Starting Enhanced MCP Server in Test Mode")
    print(f"📍 Server will run on http://localhost:{settings.MCP_PORT}")
    print(f"🔧 Environment: {settings.ENVIRONMENT}")
    print("-" * 50)
    
    # Create server instance
    server = EnhancedUnifiedMCPServer()
    
    # Run the server
    uvicorn.run(
        server.app,
        host=settings.API_HOST,
        port=settings.MCP_PORT,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    try:
        run_test_server()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

