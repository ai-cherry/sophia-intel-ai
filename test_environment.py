#!/usr/bin/env python3
"""
Test script to demonstrate environment enforcer
"""
import os
import sys
# First, print the current Python interpreter
print(f"Initial Python interpreter: {sys.executable}")
try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from core.environment_enforcer import enforce_environment
    # This will switch interpreters if needed
    if enforce_environment():
        print(f"After enforcement: {sys.executable}")
        print(f"Python version: {sys.version}")
        print(f"Running in Codespaces: {os.environ.get('CODESPACES') == 'true'}")
except ImportError as e:
    print(f"Error importing environment enforcer: {e}")
print("Environment test complete!")
