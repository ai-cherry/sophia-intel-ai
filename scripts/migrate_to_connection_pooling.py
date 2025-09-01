#!/usr/bin/env python3
"""
Migration script to update synchronous HTTP and Redis calls to use ConnectionManager
Part of the performance optimization initiative from architectural audit
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Tuple, Dict, Set
import argparse
import json

class ConnectionPoolingMigrator:
    """Migrate synchronous calls to use connection pooling"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.files_to_update: List[Tuple[Path, List[str]]] = []
        self.migration_report = {
            "files_analyzed": 0,
            "files_updated": 0,
            "http_calls_migrated": 0,
            "redis_calls_migrated": 0,
            "skipped_files": [],
            "errors": []
        }
    
    def scan_directory(self, directory: Path) -> None:
        """Scan directory for files needing migration"""
        print(f"🔍 Scanning {directory} for synchronous calls...")
        
        for py_file in directory.rglob("*.py"):
            # Skip test files and migrations
            if any(skip in str(py_file) for skip in ["test", "migration", "__pycache__", ".git"]):
                continue
            
            self.migration_report["files_analyzed"] += 1
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                changes_needed = []
                
                # Check for requests library usage
                if re.search(r'\brequests\.(get|post|put|delete|patch)\b', content):
                    changes_needed.append("http")
                    self.migration_report["http_calls_migrated"] += len(
                        re.findall(r'\brequests\.(get|post|put|delete|patch)\b', content)
                    )
                
                # Check for synchronous Redis usage
                if re.search(r'\bredis\.Redis\(|redis\.StrictRedis\(|redis\.from_url\(', content):
                    changes_needed.append("redis")
                    self.migration_report["redis_calls_migrated"] += len(
                        re.findall(r'\bredis\.(Redis|StrictRedis|from_url)\(', content)
                    )
                
                if changes_needed:
                    self.files_to_update.append((py_file, changes_needed))
                    
            except Exception as e:
                self.migration_report["errors"].append(f"{py_file}: {str(e)}")
    
    def migrate_file(self, file_path: Path, changes: List[str]) -> bool:
        """Migrate a single file to use ConnectionManager"""
        print(f"  📝 Migrating {file_path.name}...")
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Check if already uses ConnectionManager
            if "from app.core.connections import" in content:
                print(f"    ⏭️  Already uses ConnectionManager")
                self.migration_report["skipped_files"].append(str(file_path))
                return False
            
            # Add import at the top of the file
            import_added = False
            
            if "http" in changes:
                # Find the right place to add import
                if not import_added:
                    content = self._add_import(content, 
                        "from app.core.connections import http_get, http_post, get_connection_manager")
                    import_added = True
                
                # Replace requests calls
                content = self._replace_http_calls(content)
            
            if "redis" in changes:
                # Add Redis imports if not already added
                if not import_added:
                    content = self._add_import(content,
                        "from app.core.connections import redis_get, redis_set, get_connection_manager")
                    import_added = True
                
                # Replace Redis initialization
                content = self._replace_redis_calls(content)
            
            # Check if any changes were made
            if content != original_content:
                if not self.dry_run:
                    # Backup original file
                    backup_path = file_path.with_suffix('.py.bak')
                    with open(backup_path, 'w') as f:
                        f.write(original_content)
                    
                    # Write updated content
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    print(f"    ✅ Updated {file_path.name}")
                else:
                    print(f"    🔍 Would update {file_path.name}")
                
                self.migration_report["files_updated"] += 1
                return True
            
        except Exception as e:
            self.migration_report["errors"].append(f"{file_path}: {str(e)}")
            print(f"    ❌ Error: {e}")
            return False
        
        return False
    
    def _add_import(self, content: str, import_statement: str) -> str:
        """Add import statement after existing imports"""
        lines = content.splitlines()
        
        # Find the last import line
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith(('import ', 'from ')) and not line.startswith('from __future__'):
                last_import_idx = i
        
        # Insert new import after last import
        if last_import_idx > 0:
            lines.insert(last_import_idx + 1, import_statement)
        else:
            # Add after module docstring
            in_docstring = False
            for i, line in enumerate(lines):
                if line.strip().startswith('"""'):
                    if not in_docstring:
                        in_docstring = True
                    else:
                        lines.insert(i + 1, "")
                        lines.insert(i + 2, import_statement)
                        break
            else:
                # Just add at the beginning
                lines.insert(0, import_statement)
        
        return '\n'.join(lines)
    
    def _replace_http_calls(self, content: str) -> str:
        """Replace requests.get/post with async equivalents"""
        replacements = [
            # Simple GET requests
            (r'requests\.get\((.*?)\)', r'await http_get(\1)'),
            # Simple POST requests  
            (r'requests\.post\((.*?)\)', r'await http_post(\1)'),
            # Response handling
            (r'response = requests\.(get|post)', r'response = await http_\1'),
            # JSON response
            (r'\.json\(\)', ''),  # Our http_get/post already return JSON
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Mark functions as async if they now contain await
        content = self._make_functions_async(content)
        
        return content
    
    def _replace_redis_calls(self, content: str) -> str:
        """Replace Redis client initialization and calls"""
        replacements = [
            # Redis client initialization
            (r'redis\.Redis\([^)]*\)', 'await get_connection_manager().get_redis()'),
            (r'redis\.from_url\([^)]*\)', 'await get_connection_manager().get_redis()'),
            # Redis operations
            (r'redis_client\.get\((.*?)\)', r'await redis_get(\1)'),
            (r'redis_client\.set\((.*?)\)', r'await redis_set(\1)'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Mark functions as async if they now contain await
        content = self._make_functions_async(content)
        
        return content
    
    def _make_functions_async(self, content: str) -> str:
        """Convert functions to async if they contain await"""
        lines = content.splitlines()
        updated_lines = []
        
        for i, line in enumerate(lines):
            # Check if this is a function definition
            if re.match(r'^(\s*)def\s+\w+\(', line):
                # Check if function body contains await
                indent_level = len(re.match(r'^(\s*)', line).group(1))
                has_await = False
                
                for j in range(i + 1, len(lines)):
                    next_line = lines[j]
                    next_indent = len(re.match(r'^(\s*)', next_line).group(1))
                    
                    # Stop if we've left the function
                    if next_indent <= indent_level and next_line.strip():
                        break
                    
                    if 'await ' in next_line:
                        has_await = True
                        break
                
                # Convert to async if needed
                if has_await and not line.strip().startswith('async '):
                    line = re.sub(r'^(\s*)def\s+', r'\1async def ', line)
            
            updated_lines.append(line)
        
        return '\n'.join(updated_lines)
    
    def generate_report(self) -> None:
        """Generate migration report"""
        print("\n" + "=" * 50)
        print("📊 MIGRATION REPORT")
        print("=" * 50)
        
        print(f"Files analyzed: {self.migration_report['files_analyzed']}")
        print(f"Files to update: {len(self.files_to_update)}")
        print(f"Files updated: {self.migration_report['files_updated']}")
        print(f"HTTP calls migrated: {self.migration_report['http_calls_migrated']}")
        print(f"Redis calls migrated: {self.migration_report['redis_calls_migrated']}")
        
        if self.migration_report['skipped_files']:
            print(f"\nSkipped files (already migrated): {len(self.migration_report['skipped_files'])}")
        
        if self.migration_report['errors']:
            print(f"\n⚠️  Errors encountered: {len(self.migration_report['errors'])}")
            for error in self.migration_report['errors'][:5]:
                print(f"  - {error}")
        
        # Save detailed report
        report_path = Path("connection_pooling_migration_report.json")
        with open(report_path, 'w') as f:
            json.dump(self.migration_report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
    
    def run(self, directory: Path) -> None:
        """Run the migration process"""
        print("🚀 Connection Pooling Migration Tool")
        print("=" * 50)
        
        if self.dry_run:
            print("🔍 Running in DRY RUN mode (no changes will be made)")
        else:
            print("⚠️  Running in LIVE mode (files will be modified)")
        
        # Scan for files needing migration
        self.scan_directory(directory)
        
        print(f"\n📋 Found {len(self.files_to_update)} files needing migration")
        
        # Migrate each file
        for file_path, changes in self.files_to_update:
            self.migrate_file(file_path, changes)
        
        # Generate report
        self.generate_report()


def main():
    parser = argparse.ArgumentParser(
        description="Migrate synchronous calls to use ConnectionManager"
    )
    parser.add_argument(
        "--directory",
        default="app",
        help="Directory to scan (default: app)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in live mode (actually modify files)"
    )
    
    args = parser.parse_args()
    
    migrator = ConnectionPoolingMigrator(dry_run=not args.live)
    migrator.run(Path(args.directory))


if __name__ == "__main__":
    main()