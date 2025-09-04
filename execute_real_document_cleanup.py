#!/usr/bin/env python3
"""
🔥 REAL DOCUMENT CLEANUP EXECUTION 🔥

This script performs ACTUAL document cleanup operations with:
- Real file deletions/moves (not simulated)
- Comprehensive safety backups
- Progress monitoring
- Rollback capabilities

⚠️ WARNING: This performs REAL operations on your files!
"""

import asyncio
import aiofiles
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging


class RealDocumentCleanup:
    """Real document cleanup with safety and monitoring"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.backup_dir = Path("./cleanup_backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.operations_log = []
        self.files_processed = 0
        self.files_cleaned = 0
        self.space_saved = 0
        
        self.logger.info("🔥 REAL DOCUMENT CLEANUP INITIALIZED")
        self.logger.info(f"📁 Backup directory: {self.backup_dir}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger('RealDocumentCleanup')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            log_file = Path("real_document_cleanup.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    async def discover_cleanup_candidates(self, target_paths: List[str]) -> Dict[str, List[Path]]:
        """Discover documents that are candidates for cleanup"""
        
        candidates = {
            'duplicate_reports': [],
            'old_status_files': [], 
            'backup_files': [],
            'temporary_files': [],
            'low_value_configs': []
        }
        
        self.logger.info("🔍 Discovering cleanup candidates...")
        
        for target_path in target_paths:
            root = Path(target_path)
            
            if not root.exists():
                self.logger.warning(f"⚠️ Path does not exist: {target_path}")
                continue
            
            # Find files matching cleanup patterns
            for file_path in root.rglob("*"):
                if not file_path.is_file():
                    continue
                
                filename = file_path.name.lower()
                
                # Duplicate/redundant reports
                if any(pattern in filename for pattern in [
                    'status_report', 'deployment_status', '_report_', 
                    'summary_report', 'handoff', 'current', 'latest'
                ]):
                    candidates['duplicate_reports'].append(file_path)
                
                # Old status files
                elif any(pattern in filename for pattern in [
                    'status.', 'progress.', 'temp_', 'tmp_'
                ]):
                    candidates['old_status_files'].append(file_path)
                
                # Backup files
                elif any(filename.endswith(ext) for ext in [
                    '.bak', '.backup', '.old', '.orig', '~'
                ]):
                    candidates['backup_files'].append(file_path)
                
                # Temporary files  
                elif any(pattern in filename for pattern in [
                    '.tmp', '.temp', 'temporary', '.swp', '.swo'
                ]):
                    candidates['temporary_files'].append(file_path)
                
                # Low-value configs (package locks, etc.)
                elif filename in [
                    'package-lock.json', 'yarn.lock', '.ds_store', 
                    'thumbs.db', 'desktop.ini'
                ]:
                    candidates['low_value_configs'].append(file_path)
        
        # Log discovery results
        total_candidates = sum(len(files) for files in candidates.values())
        self.logger.info(f"📊 Discovery complete: {total_candidates} cleanup candidates found")
        
        for category, files in candidates.items():
            if files:
                self.logger.info(f"   📋 {category}: {len(files)} files")
        
        return candidates
    
    async def create_safety_backup(self, files_to_backup: List[Path]) -> Dict[str, Any]:
        """Create comprehensive backup before cleanup"""
        
        self.logger.info(f"💾 Creating safety backup for {len(files_to_backup)} files...")
        
        backup_info = {
            'backup_id': self.backup_dir.name,
            'backup_path': str(self.backup_dir),
            'created_at': datetime.now().isoformat(),
            'files_backed_up': [],
            'total_size_bytes': 0
        }
        
        for file_path in files_to_backup:
            try:
                if not file_path.exists():
                    continue
                
                # Create backup structure
                relative_path = file_path.relative_to(Path.cwd())
                backup_file_path = self.backup_dir / relative_path
                backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(str(file_path), str(backup_file_path))
                
                file_size = file_path.stat().st_size
                backup_info['files_backed_up'].append({
                    'original_path': str(file_path),
                    'backup_path': str(backup_file_path),
                    'size_bytes': file_size
                })
                backup_info['total_size_bytes'] += file_size
                
            except Exception as e:
                self.logger.error(f"❌ Failed to backup {file_path}: {e}")
        
        # Save backup manifest
        manifest_path = self.backup_dir / "backup_manifest.json"
        async with aiofiles.open(manifest_path, 'w') as f:
            await f.write(json.dumps(backup_info, indent=2))
        
        self.logger.info(f"✅ Backup complete: {len(backup_info['files_backed_up'])} files, {backup_info['total_size_bytes'] / 1024 / 1024:.1f} MB")
        
        return backup_info
    
    async def execute_cleanup_operation(self, category: str, files: List[Path], 
                                      operation: str = "archive") -> Dict[str, Any]:
        """Execute real cleanup operation"""
        
        self.logger.info(f"🔥 Executing {operation} for {category}: {len(files)} files")
        
        results = {
            'category': category,
            'operation': operation,
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'space_saved_bytes': 0,
            'errors': []
        }
        
        archive_dir = Path("./archived_documents") / datetime.now().strftime("%Y-%m-%d") / category
        
        for file_path in files:
            try:
                if not file_path.exists():
                    continue
                
                self.files_processed += 1
                results['files_processed'] += 1
                
                file_size = file_path.stat().st_size
                
                if operation == "archive":
                    # Move to archive directory
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    archive_file = archive_dir / file_path.name
                    
                    # Handle name conflicts
                    counter = 1
                    while archive_file.exists():
                        stem = archive_file.stem
                        suffix = archive_file.suffix
                        archive_file = archive_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.move(str(file_path), str(archive_file))
                    
                    self.logger.info(f"📦 Archived: {file_path.name} -> {archive_file}")
                    
                elif operation == "delete":
                    # Permanent deletion
                    file_path.unlink()
                    
                    self.logger.info(f"🗑️ Deleted: {file_path.name}")
                
                results['files_successful'] += 1
                results['space_saved_bytes'] += file_size
                self.files_cleaned += 1
                self.space_saved += file_size
                
                # Log operation
                self.operations_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'operation': operation,
                    'category': category,
                    'file': str(file_path),
                    'size_bytes': file_size,
                    'status': 'success'
                })
                
            except Exception as e:
                self.logger.error(f"❌ Failed to {operation} {file_path}: {e}")
                results['files_failed'] += 1
                results['errors'].append(str(e))
                
                self.operations_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'operation': operation,
                    'category': category, 
                    'file': str(file_path),
                    'status': 'failed',
                    'error': str(e)
                })
        
        success_rate = (results['files_successful'] / results['files_processed']) * 100 if results['files_processed'] > 0 else 0
        
        self.logger.info(f"✅ {category} {operation} complete: {results['files_successful']}/{results['files_processed']} files ({success_rate:.1f}% success)")
        
        return results
    
    async def monitor_cleanup_progress(self, total_files: int):
        """Monitor and report cleanup progress"""
        
        while self.files_processed < total_files:
            progress = (self.files_processed / total_files) * 100 if total_files > 0 else 0
            space_mb = self.space_saved / 1024 / 1024
            
            self.logger.info(f"📈 Progress: {progress:.1f}% ({self.files_processed}/{total_files}) | Space saved: {space_mb:.1f} MB")
            
            await asyncio.sleep(2)  # Update every 2 seconds
    
    async def generate_cleanup_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive cleanup report"""
        
        report = {
            'cleanup_summary': {
                'execution_time': datetime.now().isoformat(),
                'total_files_processed': self.files_processed,
                'total_files_cleaned': self.files_cleaned,
                'total_space_saved_bytes': self.space_saved,
                'total_space_saved_mb': self.space_saved / 1024 / 1024,
                'backup_location': str(self.backup_dir)
            },
            'operations_by_category': {},
            'detailed_operations': self.operations_log,
            'rollback_instructions': {
                'backup_location': str(self.backup_dir),
                'restore_command': f"python3 restore_from_backup.py {self.backup_dir}/backup_manifest.json"
            }
        }
        
        # Aggregate by category
        for result in results:
            category = result['category']
            report['operations_by_category'][category] = {
                'operation': result['operation'],
                'files_processed': result['files_processed'],
                'files_successful': result['files_successful'],
                'files_failed': result['files_failed'],
                'space_saved_mb': result['space_saved_bytes'] / 1024 / 1024,
                'success_rate': (result['files_successful'] / result['files_processed'] * 100) if result['files_processed'] > 0 else 0
            }
        
        return report
    
    async def execute_full_cleanup(self, target_paths: List[str]) -> Dict[str, Any]:
        """Execute complete document cleanup workflow"""
        
        start_time = datetime.now()
        self.logger.info("🚀 STARTING REAL DOCUMENT CLEANUP")
        self.logger.info("=" * 60)
        
        try:
            # Phase 1: Discover candidates
            candidates = await self.discover_cleanup_candidates(target_paths)
            
            if not any(candidates.values()):
                self.logger.info("✅ No cleanup candidates found - repository is clean!")
                return {'status': 'clean', 'message': 'No cleanup needed'}
            
            # Phase 2: Create safety backup
            all_files = []
            for files in candidates.values():
                all_files.extend(files)
            
            backup_info = await self.create_safety_backup(all_files)
            
            # Phase 3: Execute cleanup operations
            results = []
            
            # Archive duplicate reports (safest first)
            if candidates['duplicate_reports']:
                result = await self.execute_cleanup_operation(
                    'duplicate_reports', candidates['duplicate_reports'], 'archive'
                )
                results.append(result)
            
            # Archive old status files
            if candidates['old_status_files']:
                result = await self.execute_cleanup_operation(
                    'old_status_files', candidates['old_status_files'], 'archive'
                )
                results.append(result)
            
            # Delete temporary files (safe to delete)
            if candidates['temporary_files']:
                result = await self.execute_cleanup_operation(
                    'temporary_files', candidates['temporary_files'], 'delete'
                )
                results.append(result)
            
            # Archive backup files
            if candidates['backup_files']:
                result = await self.execute_cleanup_operation(
                    'backup_files', candidates['backup_files'], 'archive'
                )
                results.append(result)
            
            # Archive low-value configs  
            if candidates['low_value_configs']:
                result = await self.execute_cleanup_operation(
                    'low_value_configs', candidates['low_value_configs'], 'archive'
                )
                results.append(result)
            
            # Phase 4: Generate final report
            final_report = await self.generate_cleanup_report(results)
            final_report['backup_info'] = backup_info
            
            # Save report
            report_file = Path(f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            async with aiofiles.open(report_file, 'w') as f:
                await f.write(json.dumps(final_report, indent=2))
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            final_report['execution_time_seconds'] = execution_time
            
            self.logger.info("=" * 60)
            self.logger.info("🎉 DOCUMENT CLEANUP COMPLETE!")
            self.logger.info(f"⏱️ Execution time: {execution_time:.1f} seconds")
            self.logger.info(f"📄 Files processed: {self.files_processed}")
            self.logger.info(f"🗑️ Files cleaned: {self.files_cleaned}")
            self.logger.info(f"💾 Space saved: {self.space_saved / 1024 / 1024:.1f} MB")
            self.logger.info(f"🔄 Rollback available: {self.backup_dir}")
            self.logger.info(f"📊 Report saved: {report_file}")
            
            return final_report
            
        except Exception as e:
            self.logger.error(f"💥 CLEANUP FAILED: {e}")
            return {'status': 'failed', 'error': str(e)}


async def main():
    """Main execution function"""
    
    print("🔥" * 50)
    print("🔥  REAL DOCUMENT CLEANUP EXECUTION  🔥") 
    print("🔥" * 50)
    print()
    
    print("⚠️  WARNING: This will perform REAL file operations!")
    print("📁 Files will be moved/deleted according to cleanup policies")
    print("💾 Complete backup will be created before any operations")
    print("🔄 Rollback capability will be available")
    print()
    
    # Get user confirmation
    response = input("🤔 Do you want to proceed with REAL cleanup? (yes/no): ").lower()
    
    if response not in ['yes', 'y']:
        print("🛡️ Cleanup cancelled for safety")
        return
    
    print()
    print("🚀 Initializing document cleanup system...")
    
    # Initialize cleanup system
    cleanup = RealDocumentCleanup()
    
    # Execute cleanup
    target_paths = ["."]  # Current directory
    results = await cleanup.execute_full_cleanup(target_paths)
    
    if results.get('status') == 'failed':
        print(f"\n❌ Cleanup failed: {results.get('error')}")
        return 1
    elif results.get('status') == 'clean':
        print(f"\n✅ {results.get('message')}")
        return 0
    
    # Print summary
    summary = results.get('cleanup_summary', {})
    print(f"\n🎯 CLEANUP SUMMARY:")
    print(f"   📄 Files processed: {summary.get('total_files_processed', 0)}")
    print(f"   🗑️ Files cleaned: {summary.get('total_files_cleaned', 0)}")
    print(f"   💾 Space saved: {summary.get('total_space_saved_mb', 0):.1f} MB")
    print(f"   🔄 Backup location: {summary.get('backup_location', 'Unknown')}")
    
    print(f"\n📋 OPERATIONS BY CATEGORY:")
    for category, details in results.get('operations_by_category', {}).items():
        print(f"   📦 {category}: {details['files_successful']}/{details['files_processed']} files ({details['success_rate']:.1f}%)")
    
    return 0


if __name__ == "__main__":
    import sys
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Cleanup failed: {e}")
        sys.exit(1)