import subprocess
import os
from app.indexing.indexer import index_file

def get_changed_files():
    """Get list of changed files using git diff"""
    result = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], capture_output=True, text=True)
    return result.stdout.splitlines()

def incremental_index():
    """Reindex only changed files"""
    changed_files = get_changed_files()
    for file_path in changed_files:
        if os.path.exists(file_path):
            index_file(file_path)
            print(f"Reindexed: {file_path}")

if __name__ == "__main__":
    incremental_index()