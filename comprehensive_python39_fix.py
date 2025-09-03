#!/usr/bin/env python3
"""
Comprehensive Python 3.9 compatibility fix
Systematically fixes all PEP-604 union operators in the codebase
"""
import os
import re
from pathlib import Path

def fix_python_file(filepath):
    """Fix Python 3.9 compatibility issues in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return False, "Could not read file"
    
    original_content = content
    changes_made = []
    
    # Step 1: Ensure proper imports
    if 'from typing import' in content:
        # Extract existing imports
        import_match = re.search(r'from typing import ([^;\n]+)', content)
        if import_match:
            imports = import_match.group(1)
            import_list = [i.strip() for i in imports.split(',')]
            
            # Check what we need to add
            needs_union = '|' in content and 'Union' not in import_list
            needs_optional = '| None' in content and 'Optional' not in import_list
            
            if needs_union or needs_optional:
                if needs_union and 'Union' not in import_list:
                    import_list.append('Union')
                    changes_made.append("Added Union import")
                if needs_optional and 'Optional' not in import_list:
                    import_list.append('Optional')
                    changes_made.append("Added Optional import")
                
                # Sort and update imports
                import_list = sorted(set(import_list))
                new_imports = ', '.join(import_list)
                content = re.sub(r'from typing import [^;\n]+', f'from typing import {new_imports}', content)
    
    # Step 2: Fix type annotations
    
    # Replace X | None with Optional[X]
    patterns_fixed = 0
    
    # Handle simple types: str | None, int | None, etc.
    pattern = r'\b(\w+)\s*\|\s*None\b'
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, r'Optional[\1]', content)
        patterns_fixed += len(matches)
        changes_made.append(f"Fixed {len(matches)} simple Optional patterns")
    
    # Handle complex types: dict[str, Any] | None
    pattern = r'(dict\[[^\]]+\])\s*\|\s*None'
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, r'Optional[\1]', content)
        patterns_fixed += len(matches)
        changes_made.append(f"Fixed {len(matches)} dict Optional patterns")
    
    # Handle list types: list[str] | None
    pattern = r'(list\[[^\]]+\])\s*\|\s*None'
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, r'Optional[\1]', content)
        patterns_fixed += len(matches)
        changes_made.append(f"Fixed {len(matches)} list Optional patterns")
    
    # Handle asyncio.Task | None
    pattern = r'(asyncio\.Task)\s*\|\s*None'
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, r'Optional[\1]', content)
        patterns_fixed += len(matches)
        changes_made.append(f"Fixed {len(matches)} asyncio.Task Optional patterns")
    
    # Replace X | Y with Union[X, Y] (for non-None cases)
    # Simple types: str | int
    pattern = r'\b(\w+)\s*\|\s*(\w+)\b(?!\s*\|)(?!\s*None)'
    def replace_union(match):
        type1, type2 = match.groups()
        if type2 != 'None':  # Double check it's not None
            return f'Union[{type1}, {type2}]'
        return match.group(0)
    
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, replace_union, content)
        patterns_fixed += len(matches)
        changes_made.append(f"Fixed {len(matches)} Union patterns")
    
    # Handle list[str] | str patterns
    pattern = r'(list\[[^\]]+\])\s*\|\s*(\w+)'
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, r'Union[\1, \2]', content)
        patterns_fixed += len(matches)
        changes_made.append(f"Fixed {len(matches)} list|type patterns")
    
    # Handle str | list[str] patterns
    pattern = r'(\w+)\s*\|\s*(list\[[^\]]+\])'
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, r'Union[\1, \2]', content)
        patterns_fixed += len(matches)
        changes_made.append(f"Fixed {len(matches)} type|list patterns")
    
    # Fix return type annotations: -> X | Y
    pattern = r'->\s*(\w+)\s*\|\s*(\w+)(?=:)'
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, r'-> Union[\1, \2]', content)
        patterns_fixed += len(matches)
        changes_made.append(f"Fixed {len(matches)} return type patterns")
    
    # Fix return type with None: -> X | None
    pattern = r'->\s*([^:]+?)\s*\|\s*None(?=:)'
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, r'-> Optional[\1]', content)
        patterns_fixed += len(matches)
        changes_made.append(f"Fixed {len(matches)} return Optional patterns")
    
    # Write back if changes were made
    if content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made
        except:
            return False, "Could not write file"
    
    return False, []

def main():
    """Fix all Python files in the app directory"""
    app_dir = Path('app')
    
    # Priority files to fix first (from the error messages)
    priority_files = [
        'app/observability/cost_tracker.py',
        'app/observability/health_aggregator.py',
        'app/observability/otel_config.py',
        'app/infrastructure/dependency_injection.py',
        'app/workflows/structured_io.py',
        'app/tasks/indexing.py',
        'app/weaviate/weaviate_client.py',
        'app/swarms/coding/team.py',
        'app/agno_bridge.py',
    ]
    
    fixed_count = 0
    error_count = 0
    
    print("=" * 60)
    print("Python 3.9 Compatibility Fixer")
    print("=" * 60)
    
    # Fix priority files first
    print("\n📌 Fixing priority files...")
    for filepath in priority_files:
        file_path = Path(filepath)
        if file_path.exists():
            success, changes = fix_python_file(file_path)
            if success:
                fixed_count += 1
                print(f"✅ Fixed: {filepath}")
                for change in changes:
                    print(f"   - {change}")
            elif changes:  # Error message
                error_count += 1
                print(f"❌ Error in {filepath}: {changes}")
        else:
            print(f"⚠️  File not found: {filepath}")
    
    # Then fix all other Python files
    print("\n📁 Scanning all Python files in app/...")
    all_files = list(app_dir.rglob('*.py'))
    
    for py_file in all_files:
        # Skip if already processed
        if str(py_file) in priority_files:
            continue
            
        success, changes = fix_python_file(py_file)
        if success:
            fixed_count += 1
            print(f"✅ Fixed: {py_file}")
            for change in changes:
                print(f"   - {change}")
        elif changes:  # Error message
            error_count += 1
            print(f"❌ Error in {py_file}: {changes}")
    
    print("\n" + "=" * 60)
    print(f"📊 Summary:")
    print(f"   Files fixed: {fixed_count}")
    print(f"   Errors: {error_count}")
    print(f"   Total files scanned: {len(all_files)}")
    print("=" * 60)
    
    if fixed_count > 0:
        print("\n✨ Python 3.9 compatibility fixes applied successfully!")
        print("   You should now be able to run the server with Python 3.9")
    else:
        print("\n✅ No Python 3.9 compatibility issues found!")

if __name__ == '__main__':
    main()