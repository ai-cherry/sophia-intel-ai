#!/usr/bin/env python3
"""
Fix Dependencies Script
Identifies and fixes problematic dependencies in pyproject.toml
"""
import re
from pathlib import Path
def fix_dependencies():
    """Fix all problematic dependencies"""
    pyproject_file = Path("pyproject.toml")
    if not pyproject_file.exists():
        print("❌ pyproject.toml not found")
        return False
    with open(pyproject_file) as f:
        content = f.read()
    # List of problematic dependencies to comment out
    problematic_deps = [
        "circomlib",
        "n8n-python",
        "resemble-ai",
        "temporal-sdk",
        "elevenlabs",
        "py-ecc",
    ]
    print("🔧 Fixing problematic dependencies...")
    for dep in problematic_deps:
        # Find lines with this dependency
        pattern = rf'^(\s*)"({dep}[^"]*)",(.*)$'
        replacement = r'\1# "\2",\3 # Temporarily disabled - not available in PyPI'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        print(f"✅ Commented out {dep}")
    # Fix version constraints for available packages
    version_fixes = {
        "qdrant-client>=1.15.1": "qdrant-client>=1.10.1",  # Use available version
        "numpy>=2.0.0": "numpy>=1.26.0",  # Use stable version
        "torch>=2.4.0": "torch>=2.3.0",  # Use available version
        "transformers>=4.43.0": "transformers>=4.40.0",  # Use available version
        "anthropic>=0.30.0": "anthropic>=0.25.0",  # Use available version
        "openai>=1.35.0": "openai>=1.30.0",  # Use available version
    }
    for old_version, new_version in version_fixes.items():
        if old_version in content:
            content = content.replace(old_version, new_version)
            print(f"✅ Fixed version: {old_version} → {new_version}")
    # Write fixed content
    with open(pyproject_file, "w") as f:
        f.write(content)
    print("✅ Dependencies fixed successfully")
    return True
if __name__ == "__main__":
    fix_dependencies()
