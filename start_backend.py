#!/usr/bin/env python3
"""
Backend server startup script with proper environment loading
"""
import os
import sys
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                        print(f"Loaded: {key.strip()}")

# Load environment
load_env_file()

# Set Python path
sys.path.insert(0, str(Path(__file__).parent))
os.environ['PYTHONPATH'] = str(Path(__file__).parent)
os.environ['AGENT_API_PORT'] = '8000'

# Import and run the server
from app.api import unified_server

print("Starting Unified Server on port 8000...")
print(f"OPENAI_API_KEY set: {'OPENAI_API_KEY' in os.environ}")
print(f"OPENROUTER_API_KEY set: {'OPENROUTER_API_KEY' in os.environ}")
print(f"PORTKEY_API_KEY set: {'PORTKEY_API_KEY' in os.environ}")