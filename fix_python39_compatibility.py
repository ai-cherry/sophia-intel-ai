#!/usr/bin/env python3
"""
Fix Python 3.9 compatibility issues by replacing type union syntax (|) with Optional/Union
"""

import os
import re
from pathlib import Path

def fix_union_syntax(content: str) -> str:
    """Fix type union syntax for Python 3.9 compatibility"""
    
    # First, ensure imports are added if needed
    has_optional = "from typing import" in content and "Optional" in content
    has_union = "from typing import" in content and "Union" in content
    
    # Pattern to match type hints with | None
    pattern = r'(\w+)\s*:\s*(\w+(?:\[[\w\[\], ]+\])?)\s*\|\s*None'
    
    # Replace with Optional[type]
    def replace_with_optional(match):
        var_name = match.group(1)
        type_name = match.group(2)
        return f"{var_name}: Optional[{type_name}]"
    
    modified = re.sub(pattern, replace_with_optional, content)
    
    # Add imports if we made changes and they're not already there
    if modified != content:
        if not has_optional and "Optional[" in modified:
            # Find the typing import line and add Optional
            import_pattern = r'(from typing import .*?)(\n)'
            
            def add_optional(match):
                imports = match.group(1)
                if "Optional" not in imports:
                    # Add Optional to existing imports
                    if imports.endswith(")"):
                        return imports[:-1] + ", Optional)" + match.group(2)
                    else:
                        return imports + ", Optional" + match.group(2)
                return match.group(0)
            
            modified = re.sub(import_pattern, add_optional, modified, count=1)
            
            # If no typing import exists, add one
            if "from typing import" not in modified:
                # Add after other imports or at the top
                lines = modified.split('\n')
                import_added = False
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        # Found imports section
                        continue
                    elif import_added:
                        break
                    elif i > 0 and not line.strip() and not import_added:
                        # Empty line after imports, add here
                        lines.insert(i, 'from typing import Optional')
                        import_added = True
                        break
                
                if not import_added:
                    # Add at the beginning after docstring if present
                    for i, line in enumerate(lines):
                        if i > 0 and not line.startswith('"""') and not line.startswith("'''"):
                            lines.insert(i, 'from typing import Optional')
                            lines.insert(i+1, '')
                            break
                
                modified = '\n'.join(lines)
    
    return modified

def process_file(filepath: Path) -> bool:
    """Process a single Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified = fix_union_syntax(content)
        
        if modified != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified)
            print(f"✅ Fixed: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    """Fix all Python files in the app directory"""
    app_dir = Path("app")
    
    if not app_dir.exists():
        print("❌ 'app' directory not found")
        return
    
    fixed_count = 0
    total_count = 0
    
    for py_file in app_dir.rglob("*.py"):
        total_count += 1
        if process_file(py_file):
            fixed_count += 1
    
    print(f"\n📊 Summary: Fixed {fixed_count} out of {total_count} files")

if __name__ == "__main__":
    main()