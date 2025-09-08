#!/usr/bin/env python3
"""Claude Coder Agent - Wrapper for unified AI agent CLI"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from unified_ai_agents import main

# Inject claude as the agent
sys.argv.insert(1, "--agent")
sys.argv.insert(2, "claude")

if __name__ == "__main__":
    sys.exit(main())