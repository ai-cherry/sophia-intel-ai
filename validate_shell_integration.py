#!/usr/bin/env python3
"""
Enhanced shell integration validation based on Roo documentation
"""
import json
import os
import subprocess
import sys
import yaml
from pathlib import Path

def check_vscode_version():
    """Check VSCode version for known issues"""
    try:
        result = subprocess.run(['code', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.strip().split('\n')[0]
            print(f"✓ VSCode Version: {version_line}")
            
            # Check for 1.98+ issues
            try:
                version_parts = version_line.split('.')
                major = int(version_parts[0])
                minor = int(version_parts[1])
                
                if major > 1 or (major == 1 and minor > 98):
                    print("⚠ VSCode 1.98+ detected - may need terminal command delay workaround")
                    return True
            except (ValueError, IndexError):
                pass
                
        return False
    except FileNotFoundError:
        print("❌ VSCode not found in PATH")
        return False

def check_shell_integration():
    """Check if shell integration is properly configured"""
    bashrc_path = Path.home() / '.bashrc'
    
    if bashrc_path.exists():
        with open(bashrc_path, 'r') as f:
            content = f.read()
            
        if 'code --locate-shell-integration-path' in content:
            print("✓ Shell integration hooks found in ~/.bashrc")
            return True
        else:
            print("⚠ Shell integration hooks missing from ~/.bashrc")
            return False
    else:
        print("⚠ ~/.bashrc not found")
        return False

def check_roo_environment():
    """Check Roo-specific environment"""
    print("\n=== Roo Environment Validation ===")
    
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
            print(f"✓ Found {len(modes)} custom modes")
        except Exception as e:
            print(f"❌ .roomodes validation failed: {e}")
            return False
    else:
        print("❌ .roomodes not found")
        return False
    
    return True

def main():
    print("=== Enhanced Shell Integration Validation ===")
    
    vscode_198_plus = check_vscode_version()
    shell_integration_ok = check_shell_integration()
    roo_env_ok = check_roo_environment()
    
    print("\n=== Recommendations ===")
    
    if vscode_198_plus:
        print("📝 VSCode 1.98+ Workarounds:")
        print("   1. Open Roo settings → Terminal group")
        print("   2. Set Terminal Command Delay to 50ms (or try 0ms)")
        print("   3. Restart all terminals after changing settings")
        print("   4. If issues persist, consider downgrading to VSCode 1.98")
    
    if not shell_integration_ok:
        print("📝 Shell Integration:")
        print("   1. Restart VSCode completely")
        print("   2. Open a new terminal (Ctrl+`)")
        print("   3. Check if integration loads automatically")
    
    if roo_env_ok:
        print("📝 Next Steps:")
        print("   1. Reload VSCode window: Ctrl+Shift+P → 'Developer: Reload Window'")
        print("   2. Wait for extension to fully load")
        print("   3. Test custom modes in Roo sidebar")
    
    print("\n=== Troubleshooting Tips ===")
    print("• If commands stall: Reset terminal stats in Roo settings")
    print("• If output is incomplete: Try closing/reopening terminal tab")
    print("• If venv issues persist: Restart entire Codespace")
    print("• For persistent issues: Check F12 Developer Console for errors")
    
    return roo_env_ok and shell_integration_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
