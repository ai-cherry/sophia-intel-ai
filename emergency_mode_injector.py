#!/usr/bin/env python3
"""
Emergency Mode Injector
Direct injection of modes bypassing normal Roo loading mechanisms
"""

import json
import os
import subprocess
import time
from pathlib import Path

def emergency_inject_modes():
    """Emergency injection of SOPHIA modes"""
    
    print("🚨 EMERGENCY MODE INJECTOR ACTIVATED 🚨")
    print("=" * 60)
    
    workspace = Path("/workspaces/sophia-intel")
    
    # Create multiple configuration formats to ensure compatibility
    configs = {
        "roomodes_json": {
            "customModes": [
                {
                    "slug": "architect",
                    "name": "SOPHIA Architect", 
                    "description": "Architecture design, code reviews, refactoring",
                    "groups": ["architect", "code", "debug"],
                    "systemPrompt": "You are the SOPHIA Architect, expert in system architecture and code quality.",
                    "enabled": True
                },
                {
                    "slug": "builder",
                    "name": "SOPHIA Feature Builder",
                    "description": "New feature development, component creation",
                    "groups": ["code", "ask", "architect"],
                    "systemPrompt": "You are the SOPHIA Feature Builder, specialized in implementing new features.",
                    "enabled": True
                },
                {
                    "slug": "tester", 
                    "name": "SOPHIA Test Engineer",
                    "description": "Comprehensive testing, quality assurance",
                    "groups": ["debug", "code", "ask"],
                    "systemPrompt": "You are the SOPHIA Test Engineer, focused on comprehensive testing.",
                    "enabled": True
                },
                {
                    "slug": "operator",
                    "name": "SOPHIA Operator (DevOps/IaC)",
                    "description": "Infrastructure, deployment, monitoring",
                    "groups": ["orchestrator", "code", "architect"],
                    "systemPrompt": "You are the SOPHIA Operator, specialized in DevOps and infrastructure.",
                    "enabled": True
                },
                {
                    "slug": "debugger",
                    "name": "SOPHIA Debugger",
                    "description": "Troubleshooting, error analysis, system diagnostics",
                    "groups": ["debug", "ask", "code"],
                    "systemPrompt": "You are the SOPHIA Debugger, specialized in troubleshooting.",
                    "enabled": True
                }
            ]
        }
    }
    
    # Create JSON version of roomodes
    roomodes_json = workspace / ".roomodes.json"
    with open(roomodes_json, 'w') as f:
        json.dump(configs["roomodes_json"], f, indent=2)
    print(f"✅ Created JSON roomodes: {roomodes_json}")
    
    # Create VSCode-specific configuration
    vscode_dir = workspace / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    
    vscode_roo_config = {
        "roo.customModes.enabled": True,
        "roo.customModes.file": ".roomodes",
        "roo.customModes.alternateFile": ".roomodes.json",
        "roo.extension.forceReload": True,
        "roo.debug.enabled": True,
        "roo.modes.sophia.enabled": True
    }
    
    # Update or create VSCode settings
    vscode_settings_path = vscode_dir / "settings.json"
    if vscode_settings_path.exists():
        with open(vscode_settings_path, 'r') as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                settings = {}
    else:
        settings = {}
    
    settings.update(vscode_roo_config)
    
    with open(vscode_settings_path, 'w') as f:
        json.dump(settings, f, indent=2)
    print(f"✅ Updated VSCode settings: {vscode_settings_path}")
    
    # Create mode manifest file
    mode_manifest = {
        "version": "2.0.0",
        "timestamp": int(time.time()),
        "workspace": str(workspace),
        "modesLoaded": True,
        "modes": [
            {"slug": "architect", "name": "SOPHIA Architect", "loaded": True},
            {"slug": "builder", "name": "SOPHIA Feature Builder", "loaded": True},
            {"slug": "tester", "name": "SOPHIA Test Engineer", "loaded": True},
            {"slug": "operator", "name": "SOPHIA Operator (DevOps/IaC)", "loaded": True},
            {"slug": "debugger", "name": "SOPHIA Debugger", "loaded": True}
        ],
        "emergency_injection": True
    }
    
    manifest_path = workspace / ".roo" / "mode_manifest.json"
    manifest_path.parent.mkdir(exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(mode_manifest, f, indent=2)
    print(f"✅ Created mode manifest: {manifest_path}")
    
    # Create activation script
    activation_script = workspace / "activate_sophia_modes.sh"
    with open(activation_script, 'w') as f:
        f.write("""#!/bin/bash
echo "🎯 ACTIVATING SOPHIA MODES..."

# Set environment variables that extensions might check
export ROO_CUSTOM_MODES_ENABLED=true
export ROO_MODES_FILE=".roomodes"
export SOPHIA_MODES_ACTIVE=true

# Touch files to trigger watchers
touch .roomodes
touch .roomodes.json
touch .roo/config.json

echo "✅ SOPHIA modes environment activated"
echo "Please restart VSCode now..."
        """)
    
    # Make activation script executable
    os.chmod(activation_script, 0o755)
    print(f"✅ Created activation script: {activation_script}")
    
    # Execute activation script
    try:
        result = subprocess.run(['bash', str(activation_script)], 
                              capture_output=True, text=True, check=True)
        print("✅ Activation script executed successfully")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Activation script had issues: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
    
    # Create final verification script
    verify_script = workspace / "verify_modes_loaded.py"
    with open(verify_script, 'w') as f:
        f.write("""
#!/usr/bin/env python3
import json
from pathlib import Path

def verify_modes():
    workspace = Path("/workspaces/sophia-intel")
    
    checks = []
    
    # Check .roomodes exists and is valid
    roomodes = workspace / ".roomodes"
    if roomodes.exists():
        checks.append("✅ .roomodes file exists")
        try:
            content = roomodes.read_text()
            if "SOPHIA" in content:
                checks.append("✅ .roomodes contains SOPHIA modes")
            else:
                checks.append("❌ .roomodes missing SOPHIA content")
        except Exception as e:
            checks.append(f"❌ .roomodes read error: {e}")
    else:
        checks.append("❌ .roomodes file missing")
    
    # Check JSON version
    roomodes_json = workspace / ".roomodes.json"
    if roomodes_json.exists():
        checks.append("✅ .roomodes.json backup exists")
    
    # Check Roo config
    roo_config = workspace / ".roo" / "config.json"
    if roo_config.exists():
        checks.append("✅ Roo config exists")
    
    # Check VSCode settings
    vscode_settings = workspace / ".vscode" / "settings.json"
    if vscode_settings.exists():
        checks.append("✅ VSCode settings exists")
    
    print("\\n".join(checks))
    
    if all("✅" in check for check in checks):
        print("\\n🎉 ALL CHECKS PASSED - MODES SHOULD BE AVAILABLE")
        print("\\nIf modes still don't appear:")
        print("1. Restart VSCode completely")
        print("2. Check F12 Developer Console for errors")
        print("3. Try opening Roo settings and manually refresh")
    else:
        print("\\n⚠️  Some checks failed - this may explain missing modes")

if __name__ == "__main__":
    verify_modes()
        """)
    print(f"✅ Created verification script: {verify_script}")
    
    print("\n" + "=" * 60)
    print("🚨 EMERGENCY INJECTION COMPLETE 🚨")
    print("\nCRITICAL NEXT STEPS:")
    print("1. COMPLETELY CLOSE AND RESTART VSCODE")
    print("2. Wait 60 seconds for full extension loading")
    print("3. Check Roo mode selector")
    print("4. Run: python verify_modes_loaded.py")
    print("\n🔥 IF STILL NO MODES:")
    print("   - Check F12 Developer Console for errors")
    print("   - Try restarting the entire Codespace") 
    print("   - Contact Roo support with this diagnostic data")
    print("=" * 60)

if __name__ == "__main__":
    emergency_inject_modes()