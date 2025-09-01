#!/usr/bin/env python3
"""
Dead Code Elimination Script for Sophia Intel AI
Safely removes orphaned files and unused imports identified in the architectural audit.
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import json
import subprocess
from typing import List, Set, Dict

# Files identified as completely orphaned (never imported)
ORPHANED_FILES = [
    "app/playground.py",
    "app/server_shim.py", 
    "app/api/code_generator_server.py",
    "app/api/gateway.py",
    "app/models/router.py",
    "app/gpu/lambda_executor.py",
    "app/rag/basic_rag.py",
    "app/agno_v2/playground.py",
    "app/agno_v2/playground_with_env.py",
    "app/config/local_dev_config.py",
    "app/ports.py",
    "app/settings.py",
]

# Duplicate implementations to remove
DUPLICATE_FILES = [
    "app/memory/embed_together.py",  # Duplicate of embedding_pipeline.py
    "app/memory/weaviate_store.py",  # Duplicate of hybrid_search.py  
    "app/api/memory_endpoints.py",   # Merged into unified_server.py
]

# Files with highest unused import counts
HIGH_UNUSED_IMPORTS = [
    "app/swarms/consciousness_tracking.py",
    "app/memory/graph_rag.py",
    "app/models/portkey_dynamic_client.py",
    "app/memory/hybrid_search.py",
    "app/memory/embedding_pipeline.py",
    "app/swarms/memory_enhanced_swarm.py",
]


class DeadCodeEliminator:
    """Safely removes dead code from the codebase."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.backup_dir = Path("backup_dead_code") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.removed_files: List[str] = []
        self.cleaned_imports: List[str] = []
        self.errors: List[str] = []
        
    def run(self):
        """Execute the dead code elimination process."""
        print("🧹 Sophia Intel AI - Dead Code Elimination")
        print("=" * 50)
        
        if self.dry_run:
            print("🔍 Running in DRY RUN mode (no changes will be made)")
        else:
            print("⚠️  Running in LIVE mode (files will be modified)")
            self._create_backup_directory()
        
        # Step 1: Remove orphaned files
        print("\n📂 Step 1: Removing orphaned files...")
        self._remove_orphaned_files()
        
        # Step 2: Remove duplicate files
        print("\n📂 Step 2: Removing duplicate implementations...")
        self._remove_duplicate_files()
        
        # Step 3: Clean unused imports
        print("\n🔧 Step 3: Cleaning unused imports...")
        self._clean_unused_imports()
        
        # Step 4: Generate report
        print("\n📊 Step 4: Generating report...")
        self._generate_report()
        
    def _create_backup_directory(self):
        """Create backup directory for removed files."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created backup directory: {self.backup_dir}")
        
    def _remove_orphaned_files(self):
        """Remove files that are never imported."""
        for filepath in ORPHANED_FILES:
            self._remove_file(filepath, "orphaned")
            
    def _remove_duplicate_files(self):
        """Remove duplicate implementations."""
        for filepath in DUPLICATE_FILES:
            self._remove_file(filepath, "duplicate")
            
    def _remove_file(self, filepath: str, reason: str):
        """Remove a single file with backup."""
        file_path = Path(filepath)
        
        if not file_path.exists():
            print(f"  ⏭️  Skipping {filepath} (doesn't exist)")
            return
            
        try:
            # Get file size for reporting
            file_size = file_path.stat().st_size
            line_count = len(file_path.read_text().splitlines())
            
            if not self.dry_run:
                # Backup the file
                backup_path = self.backup_dir / reason / filepath
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_path)
                
                # Remove the file
                file_path.unlink()
                
            self.removed_files.append({
                "path": filepath,
                "reason": reason,
                "lines": line_count,
                "size": file_size
            })
            
            print(f"  ✅ Removed {filepath} ({line_count} lines, {reason})")
            
        except Exception as e:
            self.errors.append(f"Failed to remove {filepath}: {e}")
            print(f"  ❌ Error removing {filepath}: {e}")
            
    def _clean_unused_imports(self):
        """Clean unused imports using autoflake."""
        try:
            # Check if autoflake is installed
            result = subprocess.run(
                ["which", "autoflake"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("  ⚠️  autoflake not installed. Install with: pip install autoflake")
                return
                
            # Clean high-priority files first
            for filepath in HIGH_UNUSED_IMPORTS:
                if Path(filepath).exists():
                    self._clean_file_imports(filepath)
                    
            # Then clean all Python files
            if not self.dry_run:
                print("  🔄 Cleaning all Python files...")
                cmd = [
                    "autoflake",
                    "--remove-all-unused-imports",
                    "--remove-unused-variables",
                    "--in-place",
                    "--recursive",
                    "app/"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print("  ✅ Successfully cleaned all unused imports")
                else:
                    print(f"  ⚠️  Warning: {result.stderr}")
                    
        except Exception as e:
            self.errors.append(f"Import cleaning failed: {e}")
            print(f"  ❌ Error cleaning imports: {e}")
            
    def _clean_file_imports(self, filepath: str):
        """Clean imports in a single file."""
        if self.dry_run:
            print(f"  🔍 Would clean imports in {filepath}")
        else:
            cmd = [
                "autoflake",
                "--remove-all-unused-imports",
                "--remove-unused-variables", 
                "--in-place",
                filepath
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.cleaned_imports.append(filepath)
                print(f"  ✅ Cleaned imports in {filepath}")
            else:
                print(f"  ⚠️  Failed to clean {filepath}")
                
    def _generate_report(self):
        """Generate elimination report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "removed_files": self.removed_files,
            "cleaned_imports": self.cleaned_imports,
            "errors": self.errors,
            "summary": {
                "files_removed": len(self.removed_files),
                "total_lines_removed": sum(f["lines"] for f in self.removed_files),
                "total_bytes_removed": sum(f["size"] for f in self.removed_files),
                "imports_cleaned": len(self.cleaned_imports)
            }
        }
        
        # Save report
        report_path = Path("dead_code_elimination_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        # Print summary
        print("\n" + "=" * 50)
        print("📊 ELIMINATION SUMMARY")
        print("=" * 50)
        print(f"Files removed: {report['summary']['files_removed']}")
        print(f"Lines removed: {report['summary']['total_lines_removed']:,}")
        print(f"Bytes removed: {report['summary']['total_bytes_removed']:,}")
        print(f"Files with imports cleaned: {report['summary']['imports_cleaned']}")
        
        if self.errors:
            print(f"\n⚠️  Errors encountered: {len(self.errors)}")
            for error in self.errors[:5]:
                print(f"  - {error}")
                
        print(f"\n📄 Full report saved to: {report_path}")
        
        if not self.dry_run and self.removed_files:
            print(f"📁 Backed up files to: {self.backup_dir}")
            

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Eliminate dead code from Sophia Intel AI codebase"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in live mode (actually remove files)"
    )
    parser.add_argument(
        "--no-imports",
        action="store_true",
        help="Skip import cleaning"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    # Safety check
    if args.live and not args.force:
        print("⚠️  WARNING: This will permanently modify files!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            sys.exit(0)
    
    eliminator = DeadCodeEliminator(dry_run=not args.live)
    eliminator.run()
    

if __name__ == "__main__":
    main()