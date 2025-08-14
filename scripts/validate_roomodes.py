#!/usr/bin/env python3
"""
SOPHIA .roomodes Validator & Cache Buster
Validates .roomodes file and forces Roo extension to reload when changes are detected.
"""

import os
import sys
import yaml
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

class RooModesValidator:
    def __init__(self, roomodes_path: str = ".roomodes"):
        self.roomodes_path = Path(roomodes_path)
        self.cache_file = Path(".roomodes.checksum")
        
    def validate_yaml_syntax(self) -> Dict[str, Any]:
        """Validate YAML syntax and return parsed data."""
        try:
            with open(self.roomodes_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for non-ASCII characters that might cause issues
            if not content.isascii():
                non_ascii_chars = [c for c in content if not c.isascii()]
                print(f"⚠️  Warning: Non-ASCII characters found: {set(non_ascii_chars)}")
            
            data = yaml.safe_load(content)
            print("✅ YAML syntax is valid")
            return data
            
        except yaml.YAMLError as e:
            print(f"❌ YAML syntax error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            sys.exit(1)
    
    def validate_schema(self, data: Dict[str, Any]) -> None:
        """Validate the .roomodes schema structure."""
        required_top_level = ['customModes']
        for field in required_top_level:
            if field not in data:
                print(f"❌ Missing top-level field: {field}")
                sys.exit(1)
        
        if not isinstance(data['customModes'], list):
            print("❌ customModes must be a list")
            sys.exit(1)
        
        if len(data['customModes']) == 0:
            print("❌ customModes list is empty")
            sys.exit(1)
        
        required_mode_fields = ['slug', 'name', 'description', 'roleDefinition', 'groups', 'systemPrompt', 'rules']
        
        for i, mode in enumerate(data['customModes']):
            mode_name = mode.get('name', f'Mode {i+1}')
            
            # Check required fields
            for field in required_mode_fields:
                if field not in mode:
                    print(f"❌ Mode '{mode_name}' missing required field: {field}")
                    sys.exit(1)
            
            # Validate groups structure
            if not isinstance(mode['groups'], list):
                print(f"❌ Mode '{mode_name}': groups must be a list")
                sys.exit(1)
            
            for j, group in enumerate(mode['groups']):
                if not isinstance(group, str):
                    print(f"❌ Mode '{mode_name}': group {j+1} must be a string")
                    sys.exit(1)
            
            # Validate slug format
            slug = mode['slug']
            if not isinstance(slug, str) or not slug.islower() or not slug.replace('_', '').isalnum():
                print(f"❌ Mode '{mode_name}': slug '{slug}' must be lowercase alphanumeric with underscores")
                sys.exit(1)
        
        print(f"✅ Schema validation passed for {len(data['customModes'])} modes")
    
    def get_file_checksum(self) -> str:
        """Get MD5 checksum of the .roomodes file."""
        with open(self.roomodes_path, 'rb') as f:
            content = f.read()
        return hashlib.md5(content).hexdigest()
    
    def get_cached_checksum(self) -> Optional[str]:
        """Get the last known checksum from cache."""
        try:
            if self.cache_file.exists():
                return self.cache_file.read_text().strip()
        except Exception:
            pass
        return None
    
    def update_checksum_cache(self, checksum: str) -> None:
        """Update the cached checksum."""
        self.cache_file.write_text(checksum)
    
    def create_roo_reload_scripts(self) -> None:
        """Create scripts to force Roo extension reload."""
        
        # VSCode reload script
        vscode_reload_script = """#!/bin/bash
# Auto-generated Roo extension reload script
echo "🔄 Forcing Roo extension reload..."

# Method 1: Kill and restart code-server (Codespaces)
if [ "${CODESPACES:-false}" = "true" ]; then
    echo "📍 Codespaces environment detected"
    pkill -f "code-server" 2>/dev/null || true
    sleep 2
    echo "✅ Code-server restarted, page will reload automatically"
else
    echo "📍 Local VSCode environment"
    echo "Please run: Ctrl+Shift+P → 'Developer: Reload Window'"
fi

# Method 2: Clear extension cache directories
ROO_CACHE_DIRS=(
    ~/.vscode-remote/data/User/globalStorage/rooveterinaryinc.roo-cline
    ~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline
    ~/.vscode/extensions/rooveterinaryinc.roo-cline*/data
)

for cache_dir in "${ROO_CACHE_DIRS[@]}"; do
    if [ -d "$cache_dir" ]; then
        echo "🧹 Clearing cache: $cache_dir"
        rm -rf "$cache_dir"/* 2>/dev/null || true
    fi
done

echo "✅ Roo extension cache cleared"
echo "🔄 Extension should reload automatically with new modes"
"""
        
        Path("scripts/roo_force_reload.sh").write_text(vscode_reload_script)
        os.chmod("scripts/roo_force_reload.sh", 0o755)
        
        # Create a timestamp file to track reloads
        reload_log = f"# Roo Extension Reload Log\n"
        reload_log += f"Last reload: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
        reload_log += f"Reason: .roomodes file change detected\n"
        reload_log += f"File checksum: {self.get_file_checksum()}\n"
        
        Path(".roo_reload_log").write_text(reload_log)
    
    def validate(self, auto_reload: bool = False) -> Dict[str, Any]:
        """Main validation function."""
        print("🔍 Validating .roomodes file...")
        
        if not self.roomodes_path.exists():
            print(f"❌ File not found: {self.roomodes_path}")
            sys.exit(1)
        
        # Check file encoding
        try:
            with open(self.roomodes_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print("✅ File encoding is valid UTF-8")
        except UnicodeDecodeError as e:
            print(f"❌ File encoding error: {e}")
            sys.exit(1)
        
        # Validate YAML and schema
        data = self.validate_yaml_syntax()
        self.validate_schema(data)
        
        # Check if file has changed
        current_checksum = self.get_file_checksum()
        cached_checksum = self.get_cached_checksum()
        
        if current_checksum != cached_checksum:
            print(f"🔄 File changes detected (checksum: {current_checksum[:8]}...)")
            self.update_checksum_cache(current_checksum)
            
            if auto_reload:
                print("🚀 Auto-reload enabled, creating reload scripts...")
                self.create_roo_reload_scripts()
                print("✅ Reload scripts created in scripts/roo_force_reload.sh")
                print("🔄 Run the script to force Roo extension reload")
        else:
            print("✅ No changes detected since last validation")
        
        # Print mode summary
        modes = data['customModes']
        print(f"\n📊 Mode Summary ({len(modes)} modes):")
        for mode in modes:
            groups = mode['groups']
            print(f"  • {mode['name']} ({mode['slug']}) → groups: {', '.join(groups)}")
        
        return data

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate .roomodes file and manage Roo extension cache")
    parser.add_argument("--auto-reload", action="store_true", 
                       help="Automatically create reload scripts when changes detected")
    parser.add_argument("--file", default=".roomodes", 
                       help="Path to .roomodes file (default: .roomodes)")
    parser.add_argument("--json", action="store_true", 
                       help="Output validation results as JSON")
    
    args = parser.parse_args()
    
    try:
        validator = RooModesValidator(args.file)
        data = validator.validate(auto_reload=args.auto_reload)
        
        if args.json:
            result = {
                "valid": True,
                "modes": len(data['customModes']),
                "mode_names": [m['name'] for m in data['customModes']],
                "checksum": validator.get_file_checksum()
            }
            print(json.dumps(result, indent=2))
        else:
            print("\n✅ All validations passed!")
            
    except SystemExit as e:
        if args.json:
            error_result = {
                "valid": False,
                "error": "Validation failed",
                "exit_code": e.code
            }
            print(json.dumps(error_result, indent=2))
        sys.exit(e.code)

if __name__ == "__main__":
    main()