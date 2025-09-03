#!/usr/bin/env python3
"""
Fix all broken import statements that have the pattern:
from app.core.ai_logger import logger
from app.core.circuit_breaker import with_circuit_breaker
"""

import os
import re
from pathlib import Path

def fix_broken_imports(file_path):
    """Fix broken imports in a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match the broken import
    pattern = r'from app\.core\.circuit_breaker import \(\s*from app\.core\.ai_logger import logger\s*\n\s*with_circuit_breaker,?\s*\)'
    
    # Replacement
    replacement = 'from app.core.ai_logger import logger\nfrom app.core.circuit_breaker import with_circuit_breaker'
    
    # Check if pattern exists
    if re.search(pattern, content):
        # Replace the pattern
        fixed_content = re.sub(pattern, replacement, content)
        
        with open(file_path, 'w') as f:
            f.write(fixed_content)
        
        return True
    return False

def main():
    """Find and fix all Python files with broken imports"""
    root_dir = Path('/Users/lynnmusil/sophia-intel-ai')
    fixed_files = []
    
    # Find all Python files
    for py_file in root_dir.glob('**/*.py'):
        # Skip venv and __pycache__
        if 'venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        try:
            if fix_broken_imports(py_file):
                fixed_files.append(py_file)
                print(f"✅ Fixed: {py_file}")
        except Exception as e:
            print(f"❌ Error fixing {py_file}: {e}")
    
    print(f"\n🎯 Total files fixed: {len(fixed_files)}")
    
    if fixed_files:
        print("\n📝 Fixed files:")
        for f in fixed_files:
            print(f"  - {f.relative_to(root_dir)}")

if __name__ == "__main__":
    main()