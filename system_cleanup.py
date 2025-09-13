#!/usr/bin/env python3
"""
Sophia Intel AI - System Cleanup
Removes duplicate files, outdated services, and consolidates the architecture
"""

import os
import shutil
import json
import logging
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime

class SystemCleanup:
    def __init__(self, project_root: str = "/Users/lynnmusil/sophia-intel-ai"):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        
        self.files_to_remove = []
        self.directories_to_remove = []
        self.files_removed = 0
        self.dirs_removed = 0
        
    def identify_duplicate_env_files(self) -> List[Path]:
        """Identify duplicate .env files to remove (keeping centralized version)"""
        env_files_to_remove = []
        
        # Now that we have centralized config, remove the old scattered .env files
        patterns = [
            ".env.local",
            ".env.production", 
            ".env.voice",
            ".env.portkey",
            ".env", # The main .env (we keep .env.centralized)
            ".envrc",
            "infra/ports.env",
            "sophia-intel-app/.env.local"
        ]
        
        for pattern in patterns:
            path = self.project_root / pattern
            if path.exists():
                env_files_to_remove.append(path)
                
        return env_files_to_remove
    
    def identify_duplicate_dashboards(self) -> List[Path]:
        """Identify duplicate dashboard and UI implementations"""
        duplicate_dirs = [
            "agent-ui",       # Duplicate of main UI
            "sophia-v2",      # Old version
            "webui",          # Another UI implementation
            "dashboards",     # Multiple dashboard implementations
            "ui",             # Generic UI (we have sophia-intel-app)
            "dashboard.py",   # Single file dashboard
            "demo_advanced_dashboard.py",  # Demo files
            "dashboard_integration.py"
        ]
        
        duplicates = []
        for dir_name in duplicate_dirs:
            path = self.project_root / dir_name
            if path.exists():
                duplicates.append(path)
                
        return duplicates
    
    def identify_duplicate_mcp_implementations(self) -> List[Path]:
        """Identify duplicate MCP server implementations"""
        duplicate_mcp = [
            "mcp_memory_server",    # We have mcp/memory now
            "mcp_servers",          # Old location
            "mcp-bridge",           # Bridge implementation (using unified)
            "mcp-unified",          # We have the main mcp/ now
            "bridge"                # Generic bridge
        ]
        
        duplicates = []
        for dir_name in duplicate_mcp:
            path = self.project_root / dir_name
            if path.exists():
                duplicates.append(path)
                
        return duplicates
    
    def identify_outdated_docs(self) -> List[Path]:
        """Identify outdated documentation files"""
        outdated_docs = [
            "ADVANCED_DASHBOARD_IMPLEMENTATION_PLAN.md",
            "AI_AGENT_INSTRUCTIONS.md",
            "BUILDER_IMPLEMENTATION_PLAN.md", 
            "DEPLOYMENT_PLAN_TO_PRODUCTION.md",
            "IMPROVEMENT_PLAN_PHASE2.md",
            "IMPLEMENTATION_COMPLETE.md",
            "IMPLEMENTATION_SUMMARY.md",
            "LOCAL_DEPLOYMENT_STATUS.md",
            "SOPHIA_COMPLETE_OVERHAUL_PLAN.md",
            "SOPHIA_DASHBOARD_ENHANCEMENT_PROPOSAL.md",
            "VOICE_CODING_IMPLEMENTATION_PLAN.md",
            # Keep essential docs, remove implementation-specific ones that are outdated
        ]
        
        docs_to_remove = []
        for doc_name in outdated_docs:
            path = self.project_root / doc_name
            if path.exists():
                docs_to_remove.append(path)
                
        return docs_to_remove
    
    def identify_test_artifacts(self) -> List[Path]:
        """Identify test files and artifacts that can be cleaned up"""
        test_patterns = [
            "*_test_results*.json",
            "*test_report*.json", 
            "*test_report*.txt",
            "test_*.json",
            "comprehensive_*test*.json",
            "integration_test_report_*.json",
            "scout_*test*.json",
            "swarm_*test*.json"
        ]
        
        test_files = []
        for pattern in test_patterns:
            test_files.extend(self.project_root.glob(pattern))
            
        return test_files
    
    def identify_duplicate_scripts(self) -> List[Path]:
        """Identify duplicate or outdated scripts"""
        duplicate_scripts = [
            "cleanup.sh",
            "aggressive_cleanup.sh", 
            "final_cleanup.sh",
            "cleanup_git.sh",
            "cleanup_duplicates.sh",    # The one we're replacing
            "consolidate_cli.sh",
            "consolidate_mcp.sh",
            "execute_consolidation.py",
            "consolidate_dashboards.py"
        ]
        
        scripts_to_remove = []
        for script_name in duplicate_scripts:
            path = self.project_root / script_name
            if path.exists():
                scripts_to_remove.append(path)
                
        return scripts_to_remove
    
    def identify_old_builders(self) -> List[Path]:
        """Identify old builder implementations"""
        old_builders = [
            "builder_cli",
            "builder-cli", 
            "builder-agno-system",  # Keep this one - it's the latest
            "agno",                 # Old agno implementation
            "codex-launch"          # Old codex launcher
        ]
        
        # Actually keep builder-agno-system, remove the others
        builders_to_remove = []
        for builder in old_builders[:-2]:  # Keep last 2
            path = self.project_root / builder
            if path.exists():
                builders_to_remove.append(path)
                
        return builders_to_remove
    
    def create_removal_plan(self) -> Dict[str, List[Path]]:
        """Create comprehensive removal plan"""
        plan = {
            "duplicate_env_files": self.identify_duplicate_env_files(),
            "duplicate_dashboards": self.identify_duplicate_dashboards(), 
            "duplicate_mcp": self.identify_duplicate_mcp_implementations(),
            "outdated_docs": self.identify_outdated_docs(),
            "test_artifacts": self.identify_test_artifacts(),
            "duplicate_scripts": self.identify_duplicate_scripts(),
            "old_builders": self.identify_old_builders()
        }
        
        return plan
    
    def save_removal_plan(self, plan: Dict[str, List[Path]]) -> None:
        """Save removal plan to file for review"""
        plan_data = {}
        total_files = 0
        
        for category, files in plan.items():
            plan_data[category] = []
            for file_path in files:
                plan_data[category].append({
                    "path": str(file_path),
                    "exists": file_path.exists(),
                    "is_file": file_path.is_file(),
                    "is_dir": file_path.is_dir(),
                    "size_bytes": file_path.stat().st_size if file_path.exists() else 0
                })
                total_files += 1
        
        plan_data["summary"] = {
            "total_items_to_remove": total_files,
            "generated_at": datetime.now().isoformat(),
            "categories": list(plan.keys())
        }
        
        plan_file = self.project_root / "cleanup_plan.json"
        with open(plan_file, 'w') as f:
            json.dump(plan_data, f, indent=2)
            
        self.logger.info(f"Cleanup plan saved to {plan_file}")
        self.logger.info(f"Total items identified for removal: {total_files}")
        
        # Print summary
        for category, files in plan.items():
            if files:
                print(f"\n{category.replace('_', ' ').title()}: {len(files)} items")
                for file_path in files[:3]:  # Show first 3
                    print(f"  - {file_path}")
                if len(files) > 3:
                    print(f"  ... and {len(files) - 3} more")
    
    def execute_cleanup(self, plan: Dict[str, List[Path]], dry_run: bool = True) -> None:
        """Execute the cleanup plan"""
        if dry_run:
            self.logger.info("🔍 DRY RUN - No files will be deleted")
        else:
            self.logger.info("🗑️  EXECUTING CLEANUP - Files will be deleted!")
            
        total_removed = 0
        
        for category, files in plan.items():
            if not files:
                continue
                
            self.logger.info(f"\nProcessing {category}: {len(files)} items")
            
            for file_path in files:
                if not file_path.exists():
                    continue
                    
                try:
                    if dry_run:
                        if file_path.is_file():
                            self.logger.info(f"  Would remove file: {file_path}")
                        else:
                            self.logger.info(f"  Would remove directory: {file_path}")
                    else:
                        if file_path.is_file():
                            file_path.unlink()
                            self.logger.info(f"  ✅ Removed file: {file_path}")
                            self.files_removed += 1
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)
                            self.logger.info(f"  ✅ Removed directory: {file_path}")
                            self.dirs_removed += 1
                            
                    total_removed += 1
                    
                except Exception as e:
                    self.logger.error(f"  ❌ Failed to remove {file_path}: {e}")
        
        if not dry_run:
            self.logger.info(f"\n✅ Cleanup complete!")
            self.logger.info(f"Files removed: {self.files_removed}")
            self.logger.info(f"Directories removed: {self.dirs_removed}")
            
            # Create cleanup report
            report = {
                "cleanup_completed_at": datetime.now().isoformat(),
                "files_removed": self.files_removed,
                "directories_removed": self.dirs_removed,
                "total_items_removed": self.files_removed + self.dirs_removed
            }
            
            report_file = self.project_root / "cleanup_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            self.logger.info(f"Cleanup report saved to {report_file}")
        else:
            self.logger.info(f"\n📋 Dry run complete - {total_removed} items would be removed")
            self.logger.info("Run with dry_run=False to execute cleanup")
    
    def run_cleanup(self, dry_run: bool = True) -> None:
        """Run the complete cleanup process"""
        self.logger.info("🧹 Starting system cleanup analysis...")
        
        # Create removal plan
        plan = self.create_removal_plan()
        
        # Save plan for review
        self.save_removal_plan(plan)
        
        # Execute cleanup
        self.execute_cleanup(plan, dry_run=dry_run)


if __name__ == "__main__":
    import sys
    
    cleanup = SystemCleanup()
    
    # Check for --execute flag
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("🔍 Running in DRY RUN mode (no files will be deleted)")
        print("To actually delete files, run with: python3 system_cleanup.py --execute")
    else:
        print("🗑️  EXECUTING CLEANUP - Files will be deleted!")
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        if confirm.lower() != "yes":
            print("Cleanup cancelled")
            sys.exit(0)
    
    cleanup.run_cleanup(dry_run=dry_run)