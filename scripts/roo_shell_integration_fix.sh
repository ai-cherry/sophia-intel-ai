#!/usr/bin/env bash
# Roo Shell Integration Fix - Based on Official Documentation
# Addresses known VSCode 1.98+ shell integration issues

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Roo Shell Integration Fix (Official Documentation Based) ===${NC}"
echo -e "${YELLOW}Implementing fixes from Roo official troubleshooting guide...${NC}"
echo

# Check VSCode version for known issues
echo -e "${YELLOW}Step 1: Checking VSCode version...${NC}"
if command -v code &>/dev/null; then
    VSCODE_VERSION=$(code --version | head -n1)
    echo "VSCode Version: $VSCODE_VERSION"
    
    # Extract version number for comparison
    VERSION_NUM=$(echo "$VSCODE_VERSION" | grep -oE '[0-9]+\.[0-9]+' | head -1)
    MAJOR=$(echo "$VERSION_NUM" | cut -d'.' -f1)
    MINOR=$(echo "$VERSION_NUM" | cut -d'.' -f2)
    
    if [[ $MAJOR -gt 1 ]] || [[ $MAJOR -eq 1 && $MINOR -gt 98 ]]; then
        echo -e "${YELLOW}⚠ VSCode version > 1.98 detected - applying known workarounds${NC}"
        VSCODE_198_PLUS=true
    else
        echo -e "${GREEN}✓ VSCode version compatible${NC}"
        VSCODE_198_PLUS=false
    fi
else
    echo -e "${RED}❌ VSCode not found in PATH${NC}"
    VSCODE_198_PLUS=false
fi

# Apply official Roo settings based on documentation
echo -e "${YELLOW}Step 2: Applying official Roo terminal settings...${NC}"

# Create optimized settings based on official documentation
cat > .vscode/settings.json << 'EOF'
{
    "python.interpreter": "/workspaces/sophia-intel/venv/bin/python",
    "python.defaultInterpreterPath": "/workspaces/sophia-intel/venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.terminal.activateEnvInCurrentTerminal": true,
    "terminal.integrated.defaultProfile.linux": "bash",
    "terminal.integrated.cwd": "/workspaces/sophia-intel",
    "terminal.integrated.shellIntegration.enabled": true,
    "terminal.integrated.shellIntegration.decorationsEnabled": "both",
    "terminal.integrated.shellIntegration.history": 100,
    "terminal.integrated.shellIntegration.suggestEnabled": true,
    "terminal.integrated.inheritEnv": true,
    "terminal.integrated.env.linux": {
        "PYTHONPATH": "/workspaces/sophia-intel:/workspaces/sophia-intel/venv/lib/python3.11/site-packages",
        "VIRTUAL_ENV": "/workspaces/sophia-intel/venv",
        "PATH": "/workspaces/sophia-intel/venv/bin:${env:PATH}"
    },
    "terminal.integrated.profiles.linux": {
        "bash": {
            "path": "bash",
            "args": ["-l"],
            "env": {
                "PYTHONPATH": "/workspaces/sophia-intel:/workspaces/sophia-intel/venv/lib/python3.11/site-packages",
                "VIRTUAL_ENV": "/workspaces/sophia-intel/venv",
                "PATH": "/workspaces/sophia-intel/venv/bin:${env:PATH}"
            }
        }
    },
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 1000,
    "workbench.startupEditor": "none",
    "python.analysis.extraPaths": [
        "/workspaces/sophia-intel",
        "/workspaces/sophia-intel/venv/lib/python3.11/site-packages"
    ],
    "python.analysis.autoImportCompletions": true,
    "roo-cline.terminalShellIntegration": false,
    "roo-cline.useIntegratedTerminal": true,
    "roo-cline.pythonPath": "/workspaces/sophia-intel/venv/bin/python",
    "roo-cline.workspaceRoot": "/workspaces/sophia-intel"
}
EOF

echo -e "${GREEN}✓ Applied official Roo terminal settings${NC}"

# Handle VSCode 1.98+ specific issues
if [[ "$VSCODE_198_PLUS" == "true" ]]; then
    echo -e "${YELLOW}Step 3: Applying VSCode 1.98+ workarounds...${NC}"
    
    # Add terminal command delay for VSCode 1.98+ issues
    echo -e "Additional settings for VSCode 1.98+:"
    echo -e "- Terminal Command Delay: 50ms (or try 0ms if 50ms doesn't work)"
    echo -e "- These settings need to be configured in Roo Code settings UI"
    echo -e "- Navigate to Roo settings → Terminal group → Terminal command delay"
    echo
fi

# Manual shell integration setup for bash in Codespaces
echo -e "${YELLOW}Step 4: Ensuring shell integration hooks...${NC}"

# Check if shell integration is already in bashrc
if ! grep -q "code --locate-shell-integration-path" ~/.bashrc 2>/dev/null; then
    echo "Adding shell integration to ~/.bashrc..."
    echo '' >> ~/.bashrc
    echo '# VSCode shell integration' >> ~/.bashrc
    echo '[[ "$TERM_PROGRAM" == "vscode" ]] && . "$(code --locate-shell-integration-path bash)"' >> ~/.bashrc
    echo -e "${GREEN}✓ Shell integration added to ~/.bashrc${NC}"
else
    echo -e "${GREEN}✓ Shell integration already present in ~/.bashrc${NC}"
fi

# Create a comprehensive validation script
echo -e "${YELLOW}Step 5: Creating enhanced validation script...${NC}"

cat > validate_shell_integration.py << 'EOF'
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
EOF

chmod +x validate_shell_integration.py

echo -e "${GREEN}Shell integration fix completed!${NC}"
echo
echo -e "${YELLOW}Manual Steps Required:${NC}"
echo -e "1. ${BLUE}Configure Roo Terminal Settings${NC}:"
echo -e "   • Click ⚙️ icon in Roo sidebar top-right"
echo -e "   • Select 'Terminal' group from left menu"
echo -e "   • ${BLUE}UNCHECK${NC} 'Disable terminal shell integration' (enable VSCode integration)"
echo -e "   • Set 'Terminal command delay' to 50ms (or try 0ms if 50ms fails)"
echo -e "   • Click 'Apply' and restart all terminals"
echo
echo -e "2. ${BLUE}Reload VSCode${NC}: Ctrl+Shift+P → 'Developer: Reload Window'"
echo
echo -e "3. ${BLUE}Test Integration${NC}: python validate_shell_integration.py"
echo
echo -e "${YELLOW}If Issues Persist:${NC}"
echo -e "• Try enabling 'Disable terminal shell integration' (use Roo's inline terminal)"
echo -e "• Check F12 Developer Console for errors"
echo -e "• Consider VSCode version downgrade to 1.98 if using newer version"
echo
echo -e "${GREEN}Integration fix based on official Roo documentation complete!${NC}"