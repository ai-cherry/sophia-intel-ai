#!/usr/bin/env python3
"""Validate Roo environment after cache reset"""
import json
import os
import sys
import yaml
from pathlib import Path

def main():
    print("=== Roo Environment Validation ===")
    
    # Check workspace
    workspace = Path("/workspaces/sophia-intel")
    if not workspace.exists():
        print("❌ Workspace path not found")
        return False
    
    print(f"✓ Workspace: {workspace}")
    
    # Check Python environment
    python_path = sys.executable
    expected_python = "/workspaces/sophia-intel/venv/bin/python"
    
    if python_path == expected_python:
        print(f"✓ Python environment: {python_path}")
    else:
        print(f"⚠ Python environment mismatch:")
        print(f"  Current: {python_path}")
        print(f"  Expected: {expected_python}")
    
    # Check .roomodes
    roomodes_path = workspace / ".roomodes"
    if roomodes_path.exists():
        print(f"✓ .roomodes exists: {roomodes_path}")
        try:
            with open(roomodes_path) as f:
                data = yaml.safe_load(f)
            modes = data.get('customModes', [])
            print(f"✓ Found {len(modes)} custom modes:")
            for mode in modes:
                print(f"  - {mode.get('name', 'Unknown')} ({mode.get('slug', 'no-slug')})")
        except Exception as e:
            print(f"❌ .roomodes validation failed: {e}")
            return False
    else:
        print(f"❌ .roomodes not found")
        return False
    
    # Check VSCode settings
    vscode_settings = workspace / ".vscode" / "settings.json"
    if vscode_settings.exists():
        print(f"✓ VSCode settings exist")
        try:
            with open(vscode_settings) as f:
                settings = json.load(f)
            
            python_interpreter = settings.get("python.interpreter")
            if python_interpreter == expected_python:
                print(f"✓ VSCode Python interpreter aligned")
            else:
                print(f"⚠ VSCode Python interpreter mismatch: {python_interpreter}")
            
            shell_integration = settings.get("terminal.integrated.shellIntegration.enabled")
            if shell_integration is False:
                print("✓ Shell integration disabled (recommended for troubleshooting)")
            else:
                print(f"⚠ Shell integration enabled: {shell_integration}")
                
        except Exception as e:
            print(f"⚠ VSCode settings validation failed: {e}")
    
    print("\n=== Environment Ready for Testing ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
