#!/usr/bin/env python3
"""
🔥 AUTOMATED DOCUMENT CLEANUP - NO PROMPTS 🔥

This script performs REAL document cleanup automatically with:
- Smart cleanup candidate identification
- Comprehensive safety backups
- Real-time progress monitoring  
- Complete operation logging
"""

import asyncio
import aiofiles
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging


class AutoDocumentCleanup:
    """Automated document cleanup with safety and monitoring"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.backup_dir = Path("./cleanup_backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.operations_log = []
        self.files_processed = 0
        self.files_cleaned = 0
        self.space_saved = 0
        self.start_time = datetime.now()
        
        self.logger.info("🔥 AUTOMATED DOCUMENT CLEANUP INITIALIZED")
        self.logger.info(f"📁 Backup directory: {self.backup_dir}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger('AutoDocumentCleanup')
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
            log_file = Path("auto_document_cleanup.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    async def smart_cleanup_discovery(self, target_paths: List[str]) -> Dict[str, List[Path]]:
        """Smart discovery of cleanup candidates with safety checks"""
        
        candidates = {
            'redundant_reports': [],
            'deployment_logs': [],
            'temporary_configs': [], 
            'duplicate_status': [],
            'old_backups': []
        }
        
        # Safety exclusions - NEVER touch these
        protected_patterns = {
            'readme', 'license', 'contributing', 'changelog', 'makefile',
            'dockerfile', 'requirements.txt', 'package.json', 'setup.py',
            'main.py', '__init__.py', '.gitignore', '.env'
        }
        
        self.logger.info("🔍 Smart cleanup discovery starting...")
        
        for target_path in target_paths:
            root = Path(target_path)
            
            if not root.exists():
                continue
            
            for file_path in root.rglob("*"):
                if not file_path.is_file():
                    continue
                
                filename = file_path.name.lower()
                
                # Skip protected files
                if any(pattern in filename for pattern in protected_patterns):
                    continue
                
                # Skip files under 1KB (too small to matter)
                try:
                    if file_path.stat().st_size < 1024:
                        continue
                except:
                    continue
                
                # Smart categorization
                
                # 1. Redundant reports (safe to cleanup)
                if any(pattern in filename for pattern in [
                    'report_', 'status_report', 'deployment_status', 
                    '_summary', 'handoff', 'final_report'
                ]) and filename.endswith('.md'):
                    # But keep recent ones (last 7 days)
                    try:
                        if (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days > 7:
                            candidates['redundant_reports'].append(file_path)
                    except:
                        pass
                
                # 2. Deployment logs (older than 30 days)
                elif any(pattern in filename for pattern in [
                    'deployment_', 'swarm_deployment_', 'cleanup_report_'
                ]) and filename.endswith(('.json', '.log', '.md')):
                    try:
                        if (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days > 30:
                            candidates['deployment_logs'].append(file_path)
                    except:
                        pass
                
                # 3. Temporary configs
                elif any(pattern in filename for pattern in [
                    'temp_', 'tmp_', '.tmp', '_backup'
                ]) and filename.endswith(('.json', '.yaml', '.yml')):
                    candidates['temporary_configs'].append(file_path)
                
                # 4. Duplicate status files
                elif filename in [
                    'status.json', 'progress.json', 'state.json'
                ] and str(file_path.parent) != str(Path.cwd()):  # Keep root ones
                    candidates['duplicate_status'].append(file_path)
                
                # 5. Old backup files  
                elif filename.endswith(('.bak', '.backup', '.old')):
                    candidates['old_backups'].append(file_path)
        
        # Log discovery results
        total_candidates = sum(len(files) for files in candidates.values())
        self.logger.info(f"📊 Smart discovery complete: {total_candidates} cleanup candidates identified")
        
        for category, files in candidates.items():
            if files:
                size_mb = sum(f.stat().st_size for f in files if f.exists()) / 1024 / 1024
                self.logger.info(f"   📋 {category}: {len(files)} files ({size_mb:.1f} MB)")
        
        return candidates
    
    async def create_safety_backup(self, files_to_backup: List[Path]) -> Dict[str, Any]:
        """Create comprehensive backup with metadata"""
        
        if not files_to_backup:
            return {'status': 'no_files_to_backup'}
        
        self.logger.info(f"💾 Creating safety backup for {len(files_to_backup)} files...")
        
        backup_info = {
            'backup_id': self.backup_dir.name,
            'backup_path': str(self.backup_dir),
            'created_at': datetime.now().isoformat(),
            'files_backed_up': [],
            'total_size_bytes': 0,
            'restore_instructions': f"To restore: cp -r {self.backup_dir}/* ./"
        }
        
        for file_path in files_to_backup:
            try:
                if not file_path.exists():
                    continue
                
                # Create backup structure
                try:
                    relative_path = file_path.relative_to(Path.cwd())
                except ValueError:
                    # If file is outside cwd, use absolute path structure
                    relative_path = Path("external") / file_path.name
                
                backup_file_path = self.backup_dir / relative_path
                backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file with metadata
                shutil.copy2(str(file_path), str(backup_file_path))
                
                file_size = file_path.stat().st_size
                backup_info['files_backed_up'].append({
                    'original_path': str(file_path),
                    'backup_path': str(backup_file_path),
                    'size_bytes': file_size,
                    'backup_timestamp': datetime.now().isoformat()
                })
                backup_info['total_size_bytes'] += file_size
                
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to backup {file_path}: {e}")
        
        # Save backup manifest
        manifest_path = self.backup_dir / "backup_manifest.json"
        async with aiofiles.open(manifest_path, 'w') as f:
            await f.write(json.dumps(backup_info, indent=2))
        
        backup_mb = backup_info['total_size_bytes'] / 1024 / 1024
        self.logger.info(f"✅ Safety backup complete: {len(backup_info['files_backed_up'])} files, {backup_mb:.1f} MB")
        
        return backup_info
    
    async def execute_smart_operation(self, category: str, files: List[Path]) -> Dict[str, Any]:
        """Execute smart cleanup operation with real-time monitoring"""
        
        if not files:
            return {'category': category, 'files_processed': 0}
        
        self.logger.info(f"🔥 Processing {category}: {files[0:3]} files...")
        
        # Determine best operation for category
        operation_map = {
            'redundant_reports': 'archive',
            'deployment_logs': 'archive', 
            'temporary_configs': 'delete',
            'duplicate_status': 'archive',
            'old_backups': 'delete'
        }
        
        operation = operation_map.get(category, 'archive')
        
        results = {
            'category': category,
            'operation': operation,
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'space_saved_bytes': 0,
            'errors': [],
            'processed_files': []
        }
        
        # Create archive directory for non-delete operations
        archive_dir = None
        if operation == 'archive':
            archive_dir = Path("./archived_documents") / datetime.now().strftime("%Y-%m-%d") / category
            archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Process files with real-time logging
        for i, file_path in enumerate(files):
            try:
                if not file_path.exists():
                    continue
                
                self.files_processed += 1
                results['files_processed'] += 1
                
                file_size = file_path.stat().st_size
                
                if operation == 'archive':
                    # Move to organized archive
                    archive_file = archive_dir / file_path.name
                    
                    # Handle name conflicts
                    counter = 1
                    while archive_file.exists():
                        stem = archive_file.stem
                        suffix = archive_file.suffix
                        archive_file = archive_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.move(str(file_path), str(archive_file))
                    self.logger.info(f"📦 [{i+1}/{len(files)}] Archived: {file_path.name}")
                    
                elif operation == 'delete':
                    # Safe deletion
                    file_path.unlink()
                    self.logger.info(f"🗑️ [{i+1}/{len(files)}] Deleted: {file_path.name}")
                
                results['files_successful'] += 1
                results['space_saved_bytes'] += file_size
                results['processed_files'].append(str(file_path))
                
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
                
                # Progress update every 10 files
                if (i + 1) % 10 == 0:
                    progress = ((i + 1) / len(files)) * 100
                    self.logger.info(f"📈 {category} progress: {progress:.0f}% ({i+1}/{len(files)})")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to {operation} {file_path}: {e}")
                results['files_failed'] += 1
                results['errors'].append(str(e))
        
        # Final category summary
        success_rate = (results['files_successful'] / results['files_processed']) * 100 if results['files_processed'] > 0 else 0
        space_mb = results['space_saved_bytes'] / 1024 / 1024
        
        self.logger.info(f"✅ {category} complete: {results['files_successful']}/{results['files_processed']} files ({success_rate:.0f}% success, {space_mb:.1f} MB saved)")
        
        return results
    
    async def generate_real_time_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive real-time cleanup report"""
        
        execution_time = (datetime.now() - self.start_time).total_seconds()
        
        report = {
            'cleanup_execution': {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'execution_time_seconds': execution_time,
                'status': 'completed'
            },
            'performance_metrics': {
                'total_files_processed': self.files_processed,
                'total_files_cleaned': self.files_cleaned,
                'total_space_saved_bytes': self.space_saved,
                'total_space_saved_mb': round(self.space_saved / 1024 / 1024, 2),
                'processing_rate_files_per_second': round(self.files_processed / execution_time, 2) if execution_time > 0 else 0,
                'space_recovery_rate_mb_per_second': round((self.space_saved / 1024 / 1024) / execution_time, 2) if execution_time > 0 else 0
            },
            'operations_by_category': {},
            'safety_info': {
                'backup_location': str(self.backup_dir),
                'rollback_available': self.backup_dir.exists(),
                'operations_logged': len(self.operations_log)
            },
            'detailed_log': self.operations_log
        }
        
        # Aggregate results by category
        for result in results:
            if result.get('files_processed', 0) > 0:
                category = result['category']
                report['operations_by_category'][category] = {
                    'operation_type': result.get('operation', 'unknown'),
                    'files_processed': result['files_processed'],
                    'files_successful': result['files_successful'],
                    'files_failed': result['files_failed'],
                    'space_saved_mb': round(result['space_saved_bytes'] / 1024 / 1024, 2),
                    'success_rate_percent': round((result['files_successful'] / result['files_processed']) * 100, 1),
                    'error_count': len(result.get('errors', []))
                }
        
        return report
    
    async def execute_automated_cleanup(self, target_paths: List[str]) -> Dict[str, Any]:
        """Execute complete automated cleanup workflow"""
        
        self.logger.info("🚀 STARTING AUTOMATED DOCUMENT CLEANUP")
        self.logger.info("=" * 70)
        
        try:
            # Phase 1: Smart Discovery
            self.logger.info("🔍 Phase 1: Smart Cleanup Discovery")
            candidates = await self.smart_cleanup_discovery(target_paths)
            
            total_candidates = sum(len(files) for files in candidates.values())
            
            if total_candidates == 0:
                self.logger.info("✅ Repository is already clean - no cleanup needed!")
                return {'status': 'clean', 'message': 'No cleanup candidates found'}
            
            # Phase 2: Safety Backup
            self.logger.info("🛡️ Phase 2: Creating Safety Backup")
            all_files = []
            for files in candidates.values():
                all_files.extend(files)
            
            backup_info = await self.create_safety_backup(all_files)
            
            # Phase 3: Execute Smart Operations
            self.logger.info("⚡ Phase 3: Executing Smart Cleanup Operations")
            results = []
            
            for category, files in candidates.items():
                if files:
                    result = await self.execute_smart_operation(category, files)
                    results.append(result)
                    
                    # Brief pause between categories for monitoring
                    await asyncio.sleep(0.5)
            
            # Phase 4: Generate Final Report
            self.logger.info("📊 Phase 4: Generating Cleanup Report")
            final_report = await self.generate_real_time_report(results)
            final_report['backup_info'] = backup_info
            
            # Save report
            report_file = Path(f"auto_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            async with aiofiles.open(report_file, 'w') as f:
                await f.write(json.dumps(final_report, indent=2))
            
            # Final summary
            metrics = final_report['performance_metrics']
            
            self.logger.info("=" * 70)
            self.logger.info("🎉 AUTOMATED CLEANUP COMPLETE!")
            self.logger.info(f"⏱️ Execution time: {final_report['cleanup_execution']['execution_time_seconds']:.1f} seconds")
            self.logger.info(f"📄 Files processed: {metrics['total_files_processed']}")
            self.logger.info(f"🗑️ Files cleaned: {metrics['total_files_cleaned']}")
            self.logger.info(f"💾 Space recovered: {metrics['total_space_saved_mb']} MB")
            self.logger.info(f"⚡ Processing rate: {metrics['processing_rate_files_per_second']:.1f} files/sec")
            self.logger.info(f"🔄 Backup available: {final_report['safety_info']['backup_location']}")
            self.logger.info(f"📊 Report saved: {report_file}")
            
            return final_report
            
        except Exception as e:
            self.logger.error(f"💥 AUTOMATED CLEANUP FAILED: {e}")
            return {'status': 'failed', 'error': str(e)}


async def main():
    """Main automated execution"""
    
    print("🔥" * 60)
    print("🔥  AUTOMATED DOCUMENT CLEANUP - EXECUTING NOW  🔥") 
    print("🔥" * 60)
    print()
    
    # Initialize and execute
    cleanup = AutoDocumentCleanup()
    
    target_paths = ["."]  # Current directory
    results = await cleanup.execute_automated_cleanup(target_paths)
    
    if results.get('status') == 'failed':
        print(f"\n❌ Cleanup failed: {results.get('error')}")
        return 1
    elif results.get('status') == 'clean':
        print(f"\n✅ {results.get('message')}")
        return 0
    
    # Print final summary
    metrics = results.get('performance_metrics', {})
    operations = results.get('operations_by_category', {})
    
    print(f"\n🎯 CLEANUP SUMMARY:")
    print(f"   📄 Files processed: {metrics.get('total_files_processed', 0)}")
    print(f"   🗑️ Files cleaned: {metrics.get('total_files_cleaned', 0)}")
    print(f"   💾 Space recovered: {metrics.get('total_space_saved_mb', 0)} MB")
    print(f"   ⚡ Processing rate: {metrics.get('processing_rate_files_per_second', 0):.1f} files/sec")
    
    print(f"\n📋 OPERATIONS COMPLETED:")
    for category, details in operations.items():
        print(f"   📦 {category}: {details['files_successful']} files ({details['space_saved_mb']} MB)")
    
    print(f"\n🔄 ROLLBACK INFO:")
    print(f"   Backup location: {results.get('safety_info', {}).get('backup_location', 'Unknown')}")
    print(f"   Operations logged: {results.get('safety_info', {}).get('operations_logged', 0)}")
    
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