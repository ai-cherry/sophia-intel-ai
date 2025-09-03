#!/usr/bin/env python3
"""
Backend server startup script with proper environment loading
"""
import os
import sys
import asyncio
from pathlib import Path

# Use python-dotenv for robust environment loading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set Python path
sys.path.insert(0, str(Path(__file__).parent))
os.environ['PYTHONPATH'] = str(Path(__file__).parent)
os.environ['AGENT_API_PORT'] = os.getenv('AGENT_API_PORT', '8000')

# Import uvicorn to actually run the server
import uvicorn

print("Starting Unified Server on port 8000...")
print(f"OPENAI_API_KEY set: {'OPENAI_API_KEY' in os.environ}")
print(f"OPENROUTER_API_KEY set: {'OPENROUTER_API_KEY' in os.environ}")
print(f"PORTKEY_API_KEY set: {'PORTKEY_API_KEY' in os.environ}")

if __name__ == "__main__":
    # Actually launch the Uvicorn server
    uvicorn.run(
        "app.api.unified_server:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("LOCAL_DEV_MODE", "false").lower() == "true",
        log_level="info",
        access_log=True,
        loop="asyncio"
    )