#!/usr/bin/env python3
"""
Script to standardize LAMBDA_CLOUD_API_KEY to LAMBDA_CLOUD_API_KEY across the entire codebase
"""
import os
import re
import glob
from pathlib import Path

def find_files_to_update():
    """Find all files that might contain LAMBDA_CLOUD_API_KEY references"""
    patterns = [
        "**/*.py", "**/*.yml", "**/*.yaml", "**/*.env*", 
        "**/*.md", "**/*.sh", "**/*.ts", "**/*.js", "**/*.json"
    ]
    
    files_to_check = set()
    for pattern in patterns:
        files_to_check.update(glob.glob(pattern, recursive=True))
    
    # Filter out files we don't want to modify
    exclude_patterns = [
        ".git/", "__pycache__/", "node_modules/", ".pytest_cache/",
        "venv/", "env/", ".venv/", "dist/", "build/"
    ]
    
    files_to_update = []
    for file_path in files_to_check:
        if any(exclude in file_path for exclude in exclude_patterns):
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'LAMBDA_CLOUD_API_KEY' in content:
                    files_to_update.append(file_path)
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
    
    return files_to_update

def update_file(file_path):
    """Update a single file to replace LAMBDA_CLOUD_API_KEY with LAMBDA_CLOUD_API_KEY"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace LAMBDA_CLOUD_API_KEY with LAMBDA_CLOUD_API_KEY
        content = content.replace('LAMBDA_CLOUD_API_KEY', 'LAMBDA_CLOUD_API_KEY')
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    print("🔍 Finding files with LAMBDA_CLOUD_API_KEY references...")
    files_to_update = find_files_to_update()
    
    if not files_to_update:
        print("✅ No files found with LAMBDA_CLOUD_API_KEY references")
        return
    
    print(f"📝 Found {len(files_to_update)} files to update:")
    for file_path in files_to_update:
        print(f"  - {file_path}")
    
    print("\n🔄 Updating files...")
    updated_count = 0
    
    for file_path in files_to_update:
        if update_file(file_path):
            print(f"✅ Updated: {file_path}")
            updated_count += 1
        else:
            print(f"⚠️  No changes needed: {file_path}")
    
    print(f"\n🎉 Standardization complete! Updated {updated_count} files.")
    print("All LAMBDA_CLOUD_API_KEY references have been changed to LAMBDA_CLOUD_API_KEY")

if __name__ == "__main__":
    main()
