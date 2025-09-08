#!/usr/bin/env python3
"""Grok Agent - Wrapper for unified AI agent CLI"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from unified_ai_agents import main

# Inject grok as the agent
sys.argv.insert(1, "--agent")
sys.argv.insert(2, "grok")

if __name__ == "__main__":
    sys.exit(main())