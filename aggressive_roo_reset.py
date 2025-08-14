#!/usr/bin/env python3
"""
Aggressive Roo Reset Script
Clears all possible cached states and forces complete reload
"""

import os
import json
import shutil
import subprocess
import time
from pathlib import Path

def aggressive_roo_reset():
    """Perform aggressive reset of Roo extension state"""
    
    print("🔥 AGGRESSIVE ROO RESET STARTING 🔥")
    print("=" * 60)
    
    workspace = Path("/workspaces/sophia-intel")
    
    # Step 1: Clear VSCode workspace settings that might interfere
    vscode_settings = workspace / ".vscode" / "settings.json"
    if vscode_settings.exists():
        print("📝 Backing up .vscode/settings.json...")
        shutil.copy(vscode_settings, workspace / "settings_backup.json")
        
        try:
            with open(vscode_settings, 'r') as f:
                settings = json.load(f)
            
            # Remove any Roo-related settings that might conflict
            roo_keys_to_remove = []
            for key in settings:
                if 'roo' in key.lower() or 'mode' in key.lower():
                    roo_keys_to_remove.append(key)
            
            for key in roo_keys_to_remove:
                settings.pop(key, None)
                print(f"  ❌ Removed: {key}")
            
            with open(vscode_settings, 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            print(f"  ⚠️  Warning: Could not clean settings.json: {e}")
    
    # Step 2: Clear any possible Roo cache directories
    possible_cache_dirs = [
        workspace / ".roo" / "cache",
        workspace / ".cache",
        Path.home() / ".cache" / "roo",
        Path.home() / ".roo",
        workspace / "node_modules" / ".cache"
    ]
    
    for cache_dir in possible_cache_dirs:
        if cache_dir.exists():
            print(f"🗑️  Removing cache: {cache_dir}")
            try:
                shutil.rmtree(cache_dir)
                print(f"  ✅ Removed: {cache_dir}")
            except Exception as e:
                print(f"  ⚠️  Could not remove {cache_dir}: {e}")
    
    # Step 3: Create fresh Roo configuration with force flags
    roo_config = {
        "version": "1.0.0",
        "workspace": str(workspace),
        "forceReload": True,
        "clearCache": True,
        "aggressiveMode": True,
        "customModes": {
            "enabled": True,
            "file": ".roomodes",
            "forceReload": True,
            "validateOnStartup": True
        },
        "extension": {
            "forceRefresh": True,
            "clearModeCache": True,
            "reloadInterval": 1000
        },
        "debug": {
            "enabled": True,
            "logLevel": "verbose",
            "logModeLoading": True
        }
    }
    
    roo_config_path = workspace / ".roo" / "config.json"
    roo_config_path.parent.mkdir(exist_ok=True)
    
    with open(roo_config_path, 'w') as f:
        json.dump(roo_config, f, indent=2)
    print(f"✅ Created aggressive Roo config: {roo_config_path}")
    
    # Step 4: Create mode force-load script
    force_load_script = workspace / "force_modes_now.js"
    with open(force_load_script, 'w') as f:
        f.write("""
// Force load custom modes script for VSCode extension
console.log('🚀 FORCING MODE RELOAD...');

// If running in VSCode extension context
if (typeof vscode !== 'undefined') {
    console.log('VSCode context detected, reloading...');
    vscode.commands.executeCommand('workbench.action.reloadWindow');
}

// Browser context fallback
if (typeof window !== 'undefined') {
    console.log('Browser context, forcing reload...');
    window.location.reload(true);
}

// Node.js context
if (typeof process !== 'undefined') {
    console.log('Node.js context detected');
    process.exit(0);
}
        """)
    print(f"✅ Created force load script: {force_load_script}")
    
    # Step 5: Create startup trigger
    startup_trigger = workspace / ".roo" / "force_startup.py"
    with open(startup_trigger, 'w') as f:
        f.write("""
#!/usr/bin/env python3
import json
import os
from pathlib import Path

def trigger_mode_reload():
    print("🔄 TRIGGERING MODE RELOAD...")
    
    # Create trigger file that extensions might watch
    trigger_file = Path("/workspaces/sophia-intel/.roo/reload_trigger")
    trigger_file.write_text(f"RELOAD:{os.getpid()}")
    
    # Update roomodes timestamp to trigger file watcher
    roomodes = Path("/workspaces/sophia-intel/.roomodes")
    if roomodes.exists():
        os.utime(roomodes)
        print("✅ Updated .roomodes timestamp")
    
    print("✅ Reload trigger activated")

if __name__ == "__main__":
    trigger_mode_reload()
        """)
    print(f"✅ Created startup trigger: {startup_trigger}")
    
    # Step 6: Execute the startup trigger
    try:
        subprocess.run(["/workspaces/sophia-intel/venv/bin/python", str(startup_trigger)], 
                      check=True, capture_output=True, text=True)
        print("✅ Startup trigger executed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Startup trigger failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 AGGRESSIVE RESET COMPLETE")
    print("\nMANDATORY NEXT STEPS:")
    print("1. Close ALL VSCode tabs and windows")
    print("2. Completely restart VSCode (not just reload)")
    print("3. Wait 30 seconds for extensions to fully load")
    print("4. Check Roo mode selector")
    print("5. If still failing, restart the entire Codespace")
    print("\n📧 IF MODES STILL DON'T APPEAR:")
    print("   Run: python force_load_modes.py")
    print("   Then manually check F12 Developer Console for errors")
    print("=" * 60)

if __name__ == "__main__":
    aggressive_roo_reset()