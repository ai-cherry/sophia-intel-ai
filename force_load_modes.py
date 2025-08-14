#!/usr/bin/env python3
# Force load Roo custom modes
import json
import os
import time
from pathlib import Path

def force_load_modes():
    workspace = Path("/workspaces/sophia-intel")
    roomodes_path = workspace / ".roomodes"
    
    if not roomodes_path.exists():
        print("ERROR: .roomodes file not found")
        return False
        
    # Create temporary config to force mode loading
    temp_config = {
        "forceReload": True,
        "timestamp": int(time.time()),
        "customModes": {
            "file": ".roomodes",
            "format": "yaml",
            "enabled": True,
            "forceLoad": True
        }
    }
    
    temp_config_path = workspace / ".roo" / "force_load.json"
    with open(temp_config_path, 'w') as f:
        json.dump(temp_config, f, indent=2)
        
    print(f"Force load configuration created: {temp_config_path}")
    print("Please restart VSCode to apply changes.")
    return True

if __name__ == "__main__":
    force_load_modes()
