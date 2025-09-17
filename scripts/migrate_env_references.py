#!/usr/bin/env python3
"""
Environment Configuration Migration Script

Migrates all references from legacy .env.template pattern to standardized .env.template pattern.
Part of Phase 1 remediation for repository duplication issues.

Usage:
    python scripts/migrate_env_references.py --dry-run    # Preview changes
    python scripts/migrate_env_references.py --execute   # Apply changes
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import argparse


class EnvMigrator:
    """Migrates environment configuration references across the repository."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.changes: List[Tuple[Path, List[Tuple[int, str, str]]]] = []
        
        # Pattern mappings: old_pattern -> new_pattern
        self.migrations = {
            r'\.env\.example': '.env.template',
            r'env\.example': '.env.template',
            r'\.env\.mcp\.example': '.env.template',
            r'config/production\.env\.example': '.env.template',
        }
        
        # Files to exclude from migration
        self.exclude_patterns = {
            '.git/',
            '__pycache__/',
            '.pytest_cache/',
            '.venv/',
            'node_modules/',
            '.ruff_cache/',
            'dist/',
            'build/',
            '*.pyc',
            '*.pyo',
            '.DS_Store'
        }
        
        # Extensions to process
        self.include_extensions = {'.py', '.sh', '.md', '.yml', '.yaml', '.json', '.txt', '.toml'}
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from processing."""
        path_str = str(file_path)
        
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
                
        return False
    
    def find_files_to_process(self) -> List[Path]:
        """Find all files that need to be processed."""
        files = []
        
        for file_path in self.repo_root.rglob('*'):
            if file_path.is_file() and not self.should_exclude_file(file_path):
                if file_path.suffix in self.include_extensions or file_path.name in {'Makefile', 'Dockerfile'}:
                    files.append(file_path)
        
        return files
    
    def analyze_file(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Analyze a file and return list of (line_num, old_line, new_line) tuples."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Skip binary files
            return []
        except Exception as e:
            print(f"⚠️ Could not read {file_path}: {e}")
            return []
        
        changes = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            new_line = line
            modified = False
            
            for old_pattern, new_pattern in self.migrations.items():
                if re.search(old_pattern, line):
                    new_line = re.sub(old_pattern, new_pattern, new_line)
                    modified = True
            
            if modified and new_line != line:
                changes.append((line_num, line, new_line))
        
        return changes
    
    def scan_repository(self) -> Dict[str, int]:
        """Scan repository for files that need migration."""
        print("🔍 Scanning repository for environment configuration references...")
        
        files_to_process = self.find_files_to_process()
        stats = {
            'files_scanned': 0,
            'files_with_changes': 0,
            'total_changes': 0
        }
        
        for file_path in files_to_process:
            stats['files_scanned'] += 1
            changes = self.analyze_file(file_path)
            
            if changes:
                stats['files_with_changes'] += 1
                stats['total_changes'] += len(changes)
                self.changes.append((file_path, changes))
        
        return stats
    
    def preview_changes(self):
        """Preview all changes that would be made."""
        if not self.changes:
            print("✅ No changes needed - all references already use .env.template pattern")
            return
            
        print(f"\n📋 Preview of {len(self.changes)} files with changes:\n")
        
        for file_path, file_changes in self.changes:
            rel_path = file_path.relative_to(self.repo_root)
            print(f"📄 {rel_path} ({len(file_changes)} changes):")
            
            for line_num, old_line, new_line in file_changes:
                print(f"   Line {line_num}:")
                print(f"     - {old_line.strip()}")
                print(f"     + {new_line.strip()}")
            print()
    
    def apply_changes(self) -> Dict[str, int]:
        """Apply all changes to files."""
        if not self.changes:
            print("✅ No changes to apply")
            return {'files_modified': 0, 'lines_changed': 0}
        
        print(f"🔧 Applying changes to {len(self.changes)} files...")
        
        stats = {'files_modified': 0, 'lines_changed': 0}
        
        for file_path, file_changes in self.changes:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # Apply changes in reverse order to maintain line numbers
                for line_num, old_line, new_line in reversed(file_changes):
                    if lines[line_num - 1] == old_line:
                        lines[line_num - 1] = new_line
                        stats['lines_changed'] += 1
                    else:
                        print(f"⚠️ Line {line_num} in {file_path} has changed, skipping")
                
                # Write back to file
                file_path.write_text('\n'.join(lines), encoding='utf-8')
                stats['files_modified'] += 1
                
                rel_path = file_path.relative_to(self.repo_root)
                print(f"✅ Updated {rel_path}")
                
            except Exception as e:
                print(f"❌ Failed to update {file_path}: {e}")
        
        return stats
    
    def cleanup_deprecated_files(self, dry_run: bool = True) -> List[Path]:
        """Remove deprecated environment files."""
        deprecated_files = [
            '.env.template',
            '.env.template',
            '.env.template',
            'config/production.env.template'
        ]
        
        files_to_remove = []
        for file_name in deprecated_files:
            file_path = self.repo_root / file_name
            if file_path.exists():
                files_to_remove.append(file_path)
        
        if not files_to_remove:
            print("✅ No deprecated environment files found")
            return []
        
        if dry_run:
            print(f"\n🗑️ Would remove {len(files_to_remove)} deprecated files:")
            for file_path in files_to_remove:
                rel_path = file_path.relative_to(self.repo_root)
                print(f"   - {rel_path}")
        else:
            print(f"\n🗑️ Removing {len(files_to_remove)} deprecated files:")
            for file_path in files_to_remove:
                rel_path = file_path.relative_to(self.repo_root)
                try:
                    file_path.unlink()
                    print(f"   ✅ Removed {rel_path}")
                except Exception as e:
                    print(f"   ❌ Failed to remove {rel_path}: {e}")
        
        return files_to_remove
    
    def validate_template_file(self) -> bool:
        """Ensure .env.template exists and is properly configured."""
        template_file = self.repo_root / '.env.template'
        
        if not template_file.exists():
            print("❌ .env.template not found - creating from .env.template if available")
            
            # Try to create from .env.template
            example_file = self.repo_root / '.env.template'
            if example_file.exists():
                template_file.write_text(example_file.read_text())
                print("✅ Created .env.template from .env.template")
            else:
                print("❌ No .env.template found to create template from")
                return False
        
        print("✅ .env.template exists")
        return True


def main():
    parser = argparse.ArgumentParser(description='Migrate environment configuration references')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview changes without applying them')
    parser.add_argument('--execute', action='store_true',
                       help='Apply changes to files')
    parser.add_argument('--cleanup-deprecated', action='store_true',
                       help='Remove deprecated environment files')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print("❌ Must specify either --dry-run or --execute")
        parser.print_help()
        return 1
    
    repo_root = Path(__file__).parent.parent
    migrator = EnvMigrator(repo_root)
    
    print("🔧 Environment Configuration Migration Tool")
    print("=" * 50)
    
    # Validate template file exists
    if not migrator.validate_template_file():
        return 1
    
    # Scan repository
    stats = migrator.scan_repository()
    print(f"\n📊 Scan Results:")
    print(f"   Files scanned: {stats['files_scanned']}")
    print(f"   Files needing changes: {stats['files_with_changes']}")
    print(f"   Total changes: {stats['total_changes']}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be applied")
        migrator.preview_changes()
        migrator.cleanup_deprecated_files(dry_run=True)
        print("\n💡 Run with --execute to apply these changes")
        
    elif args.execute:
        print("\n🚀 EXECUTE MODE - Applying changes")
        
        if stats['files_with_changes'] > 0:
            migrator.preview_changes()
            
            response = input("\n❓ Proceed with applying these changes? (y/N): ")
            if response.lower() != 'y':
                print("❌ Migration cancelled by user")
                return 1
            
            apply_stats = migrator.apply_changes()
            print(f"\n✅ Migration completed:")
            print(f"   Files modified: {apply_stats['files_modified']}")
            print(f"   Lines changed: {apply_stats['lines_changed']}")
        
        if args.cleanup_deprecated:
            migrator.cleanup_deprecated_files(dry_run=False)
    
    print("\n🎯 Next Steps:")
    print("1. Test the system with updated configuration")
    print("2. Update documentation to reference .env.template only")
    print("3. Add .env.template validation to CI/CD pipeline")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
