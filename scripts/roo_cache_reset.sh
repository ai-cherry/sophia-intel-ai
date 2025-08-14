#!/usr/bin/env bash
# Comprehensive Roo Cache & Environment Reset Script
# Addresses shell integration and workspace cache misalignment issues

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Comprehensive Roo Cache & Environment Reset ===${NC}"
echo -e "${YELLOW}Addressing shell/workspace cache misalignment issues...${NC}"
echo

# Kill any hanging processes first
echo -e "${YELLOW}Step 1: Cleaning up processes...${NC}"
pkill -f "code --list-extensions" 2>/dev/null || true

# Check current Python environment alignment
echo -e "${YELLOW}Step 2: Verifying Python environment...${NC}"
echo "Current Python: $(which python)"
echo "Expected Python: /workspaces/sophia-intel/venv/bin/python"

if [[ "$(which python)" != "/workspaces/sophia-intel/venv/bin/python" ]]; then
    echo -e "${RED}❌ Python environment misaligned${NC}"
    echo "Activating virtual environment..."
    source /workspaces/sophia-intel/venv/bin/activate
    echo "After activation: $(which python)"
else
    echo -e "${GREEN}✓ Python environment aligned${NC}"
fi

# Clear VSCode extension caches (Codespaces specific)
echo -e "${YELLOW}Step 3: Clearing VSCode extension caches...${NC}"

# Primary Roo extension cache locations in Codespaces
ROO_CACHE_PATHS=(
    ~/.vscode-remote/data/User/globalStorage/rooveterinaryinc.roo-cline
    ~/.vscode-remote/extensions/rooveterinaryinc.roo-cline*/data
    ~/.vscode-remote/extensions/rooveterinaryinc.roo-cline*/out
    ~/.vscode-remote/extensions/rooveterinaryinc.roo-cline*/cache
    ~/vscode-remote/data/User/globalStorage/rooveterinaryinc.roo-cline
)

for cache_path in "${ROO_CACHE_PATHS[@]}"; do
    if [ -d "$cache_path" ] || [ -f "$cache_path" ]; then
        echo "Clearing cache: $cache_path"
        rm -rf "$cache_path" 2>/dev/null || true
    fi
done

# Clear shell integration cache
echo -e "${YELLOW}Step 4: Clearing shell integration cache...${NC}"
rm -rf ~/.vscode-remote/data/User/workspaceStorage/*/vscode.shellintegration* 2>/dev/null || true
rm -rf ~/.vscode-remote/data/CachedExtensions/* 2>/dev/null || true

# Clear workspace-specific VSCode cache
echo -e "${YELLOW}Step 5: Clearing workspace cache...${NC}"
WORKSPACE_HASH=$(echo "/workspaces/sophia-intel" | sha1sum | cut -d' ' -f1)
rm -rf ~/.vscode-remote/data/User/workspaceStorage/$WORKSPACE_HASH* 2>/dev/null || true

# Clear any .roo directory in workspace
if [ -d .roo ]; then
    echo "Backing up and clearing .roo directory..."
    mv .roo .roo.backup.$(date +%Y%m%d%H%M%S) 2>/dev/null || true
fi

# Reset terminal profile integration
echo -e "${YELLOW}Step 6: Resetting terminal integration...${NC}"
unset VSCODE_INJECTION
export TERM_PROGRAM_VERSION=""
export VSCODE_SHELL_INTEGRATION=""

# Verify .roomodes file is still intact
echo -e "${YELLOW}Step 7: Verifying .roomodes file integrity...${NC}"
if [ -f .roomodes ]; then
    echo "File exists: $(ls -la .roomodes)"
    echo "File type: $(file .roomodes)"
    echo "Modified: $(stat -c %y .roomodes)"
    
    # Quick YAML validation
    if python -c "import yaml; yaml.safe_load(open('.roomodes'))" 2>/dev/null; then
        echo -e "${GREEN}✓ .roomodes YAML is valid${NC}"
        MODES_COUNT=$(python -c "import yaml; print(len(yaml.safe_load(open('.roomodes'))['customModes']))")
        echo -e "${GREEN}✓ Found $MODES_COUNT custom modes${NC}"
    else
        echo -e "${RED}❌ .roomodes YAML validation failed${NC}"
    fi
else
    echo -e "${RED}❌ .roomodes file missing${NC}"
    exit 1
fi

# Update VSCode settings to force proper environment
echo -e "${YELLOW}Step 8: Updating VSCode settings...${NC}"
cat > .vscode/settings.json.new << 'EOF'
{
    "python.interpreter": "/workspaces/sophia-intel/venv/bin/python",
    "python.defaultInterpreterPath": "/workspaces/sophia-intel/venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.terminal.activateEnvInCurrentTerminal": true,
    "terminal.integrated.defaultProfile.linux": "bash",
    "terminal.integrated.cwd": "/workspaces/sophia-intel",
    "terminal.integrated.shellIntegration.enabled": false,
    "terminal.integrated.shellIntegration.decorationsEnabled": "never",
    "terminal.integrated.env.linux": {
        "PYTHONPATH": "/workspaces/sophia-intel:/workspaces/sophia-intel/venv/lib/python3.11/site-packages",
        "VIRTUAL_ENV": "/workspaces/sophia-intel/venv",
        "PATH": "/workspaces/sophia-intel/venv/bin:${env:PATH}"
    },
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 1000,
    "workbench.startupEditor": "none",
    "python.analysis.extraPaths": [
        "/workspaces/sophia-intel",
        "/workspaces/sophia-intel/venv/lib/python3.11/site-packages"
    ],
    "roo-cline.terminalShellIntegration": false,
    "roo-cline.useIntegratedTerminal": true,
    "roo-cline.pythonPath": "/workspaces/sophia-intel/venv/bin/python",
    "roo-cline.workspaceRoot": "/workspaces/sophia-intel"
}
EOF

mv .vscode/settings.json.new .vscode/settings.json

echo -e "${YELLOW}Step 9: Creating environment validation script...${NC}"
cat > validate_roo_env.py << 'EOF'
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
EOF

chmod +x validate_roo_env.py

echo -e "${GREEN}Cache reset completed!${NC}"
echo
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. ${BLUE}Reload VSCode window${NC}: Ctrl+Shift+P → 'Developer: Reload Window'"
echo -e "2. ${BLUE}Wait for extension to fully load${NC} (check status bar)"
echo -e "3. ${BLUE}Run validation${NC}: python validate_roo_env.py"
echo -e "4. ${BLUE}Test custom modes${NC} in Roo sidebar"
echo
echo -e "${YELLOW}If issues persist:${NC}"
echo -e "- Try disabling then re-enabling the Roo extension"
echo -e "- Check VSCode Developer Console (F12) for errors"
echo -e "- Consider restarting the Codespace completely"
echo
echo -e "${GREEN}Environment reset complete!${NC}"