
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
    
    print("\n".join(checks))
    
    if all("✅" in check for check in checks):
        print("\n🎉 ALL CHECKS PASSED - MODES SHOULD BE AVAILABLE")
        print("\nIf modes still don't appear:")
        print("1. Restart VSCode completely")
        print("2. Check F12 Developer Console for errors")
        print("3. Try opening Roo settings and manually refresh")
    else:
        print("\n⚠️  Some checks failed - this may explain missing modes")

if __name__ == "__main__":
    verify_modes()
        