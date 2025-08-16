#!/usr/bin/env python3
"""
SOPHIA Intel Backup and Recovery System
Automated backups for databases, configurations, and critical data
"""

import asyncio
import aiohttp
import json
import os
import shutil
import subprocess
import tarfile
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring/logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """Backup configuration"""
    databases: Dict[str, str]
    directories: List[str]
    retention_days: int
    backup_location: str
    compression: bool
    encryption: bool

@dataclass
class BackupResult:
    """Backup operation result"""
    backup_type: str
    source: str
    destination: str
    size_bytes: int
    duration_seconds: float
    status: str
    error: Optional[str]
    timestamp: datetime

class BackupSystem:
    """Comprehensive backup and recovery system"""
    
    def __init__(self, config_path: str = "monitoring/backup-config.json"):
        self.config = self._load_config(config_path)
        self.backup_results: List[BackupResult] = []
        
    def _load_config(self, config_path: str) -> BackupConfig:
        """Load backup configuration"""
        default_config = {
            "databases": {
                "postgres": os.getenv("DATABASE_URL", ""),
                "redis": os.getenv("REDIS_URL", ""),
                "qdrant": os.getenv("QDRANT_URL", "")
            },
            "directories": [
                "infrastructure/",
                "deployment/",
                "monitoring/",
                ".github/workflows/"
            ],
            "retention_days": 30,
            "backup_location": "backups/",
            "compression": True,
            "encryption": False
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Could not load backup config from {config_path}: {e}")
            
        return BackupConfig(**default_config)
    
    def create_backup_directory(self) -> str:
        """Create timestamped backup directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.config.backup_location, f"sophia_intel_backup_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir
    
    async def backup_database(self, db_name: str, connection_url: str, backup_dir: str) -> BackupResult:
        """Backup a database"""
        start_time = datetime.now()
        
        try:
            if not connection_url:
                return BackupResult(
                    backup_type="database",
                    source=db_name,
                    destination="",
                    size_bytes=0,
                    duration_seconds=0,
                    status="skipped",
                    error="No connection URL provided",
                    timestamp=start_time
                )
            
            backup_file = os.path.join(backup_dir, f"{db_name}_backup.sql")
            
            if db_name == "postgres":
                # PostgreSQL backup
                cmd = ["pg_dump", connection_url, "-f", backup_file]
            elif db_name == "redis":
                # Redis backup (save current state)
                backup_file = os.path.join(backup_dir, f"{db_name}_backup.rdb")
                cmd = ["redis-cli", "--rdb", backup_file]
            else:
                # Generic backup approach
                logger.warning(f"No specific backup method for {db_name}, skipping")
                return BackupResult(
                    backup_type="database",
                    source=db_name,
                    destination="",
                    size_bytes=0,
                    duration_seconds=0,
                    status="skipped",
                    error="No backup method available",
                    timestamp=start_time
                )
            
            # Execute backup command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                file_size = os.path.getsize(backup_file) if os.path.exists(backup_file) else 0
                duration = (datetime.now() - start_time).total_seconds()
                
                return BackupResult(
                    backup_type="database",
                    source=db_name,
                    destination=backup_file,
                    size_bytes=file_size,
                    duration_seconds=duration,
                    status="success",
                    error=None,
                    timestamp=start_time
                )
            else:
                return BackupResult(
                    backup_type="database",
                    source=db_name,
                    destination="",
                    size_bytes=0,
                    duration_seconds=(datetime.now() - start_time).total_seconds(),
                    status="failed",
                    error=stderr.decode() if stderr else "Unknown error",
                    timestamp=start_time
                )
                
        except Exception as e:
            return BackupResult(
                backup_type="database",
                source=db_name,
                destination="",
                size_bytes=0,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                status="error",
                error=str(e),
                timestamp=start_time
            )
    
    def backup_directory(self, directory: str, backup_dir: str) -> BackupResult:
        """Backup a directory"""
        start_time = datetime.now()
        
        try:
            if not os.path.exists(directory):
                return BackupResult(
                    backup_type="directory",
                    source=directory,
                    destination="",
                    size_bytes=0,
                    duration_seconds=0,
                    status="skipped",
                    error="Directory does not exist",
                    timestamp=start_time
                )
            
            # Create archive name
            dir_name = directory.rstrip('/').replace('/', '_')
            archive_name = f"{dir_name}_backup.tar.gz"
            archive_path = os.path.join(backup_dir, archive_name)
            
            # Create compressed archive
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(directory, arcname=os.path.basename(directory.rstrip('/')))
            
            file_size = os.path.getsize(archive_path)
            duration = (datetime.now() - start_time).total_seconds()
            
            return BackupResult(
                backup_type="directory",
                source=directory,
                destination=archive_path,
                size_bytes=file_size,
                duration_seconds=duration,
                status="success",
                error=None,
                timestamp=start_time
            )
            
        except Exception as e:
            return BackupResult(
                backup_type="directory",
                source=directory,
                destination="",
                size_bytes=0,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                status="error",
                error=str(e),
                timestamp=start_time
            )
    
    def backup_configuration(self, backup_dir: str) -> BackupResult:
        """Backup system configuration"""
        start_time = datetime.now()
        
        try:
            config_data = {
                "timestamp": datetime.now().isoformat(),
                "environment_variables": {
                    key: "***REDACTED***" if "key" in key.lower() or "token" in key.lower() or "secret" in key.lower()
                    else value
                    for key, value in os.environ.items()
                    if key.startswith(("SOPHIA_", "RAILWAY_", "PULUMI_", "GITHUB_", "DNSIMPLE_"))
                },
                "system_info": {
                    "python_version": subprocess.check_output(["python3", "--version"]).decode().strip(),
                    "node_version": subprocess.check_output(["node", "--version"]).decode().strip() if shutil.which("node") else "Not installed",
                    "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
                    "git_branch": subprocess.check_output(["git", "branch", "--show-current"]).decode().strip()
                }
            }
            
            config_file = os.path.join(backup_dir, "system_configuration.json")
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            file_size = os.path.getsize(config_file)
            duration = (datetime.now() - start_time).total_seconds()
            
            return BackupResult(
                backup_type="configuration",
                source="system_config",
                destination=config_file,
                size_bytes=file_size,
                duration_seconds=duration,
                status="success",
                error=None,
                timestamp=start_time
            )
            
        except Exception as e:
            return BackupResult(
                backup_type="configuration",
                source="system_config",
                destination="",
                size_bytes=0,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                status="error",
                error=str(e),
                timestamp=start_time
            )
    
    async def run_full_backup(self) -> List[BackupResult]:
        """Run a complete backup of all configured items"""
        logger.info("Starting SOPHIA Intel full backup")
        
        # Create backup directory
        backup_dir = self.create_backup_directory()
        logger.info(f"Backup directory: {backup_dir}")
        
        results = []
        
        # Backup databases
        for db_name, connection_url in self.config.databases.items():
            logger.info(f"Backing up database: {db_name}")
            result = await self.backup_database(db_name, connection_url, backup_dir)
            results.append(result)
            logger.info(f"Database {db_name} backup: {result.status}")
        
        # Backup directories
        for directory in self.config.directories:
            logger.info(f"Backing up directory: {directory}")
            result = self.backup_directory(directory, backup_dir)
            results.append(result)
            logger.info(f"Directory {directory} backup: {result.status}")
        
        # Backup configuration
        logger.info("Backing up system configuration")
        result = self.backup_configuration(backup_dir)
        results.append(result)
        logger.info(f"Configuration backup: {result.status}")
        
        # Create backup manifest
        self.create_backup_manifest(backup_dir, results)
        
        # Clean up old backups
        self.cleanup_old_backups()
        
        self.backup_results.extend(results)
        logger.info("Full backup completed")
        
        return results
    
    def create_backup_manifest(self, backup_dir: str, results: List[BackupResult]):
        """Create a manifest file for the backup"""
        manifest = {
            "backup_timestamp": datetime.now().isoformat(),
            "backup_directory": backup_dir,
            "total_items": len(results),
            "successful_items": len([r for r in results if r.status == "success"]),
            "failed_items": len([r for r in results if r.status in ["failed", "error"]]),
            "skipped_items": len([r for r in results if r.status == "skipped"]),
            "total_size_bytes": sum(r.size_bytes for r in results),
            "items": [
                {
                    "type": r.backup_type,
                    "source": r.source,
                    "destination": r.destination,
                    "size_bytes": r.size_bytes,
                    "status": r.status,
                    "error": r.error
                }
                for r in results
            ]
        }
        
        manifest_file = os.path.join(backup_dir, "backup_manifest.json")
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Backup manifest created: {manifest_file}")
    
    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        if not os.path.exists(self.config.backup_location):
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        
        for item in os.listdir(self.config.backup_location):
            item_path = os.path.join(self.config.backup_location, item)
            if os.path.isdir(item_path):
                # Extract timestamp from directory name
                try:
                    timestamp_str = item.split('_')[-2] + '_' + item.split('_')[-1]
                    item_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if item_date < cutoff_date:
                        shutil.rmtree(item_path)
                        logger.info(f"Removed old backup: {item}")
                        
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse date from backup directory: {item}")
    
    def generate_backup_report(self, results: List[BackupResult]) -> str:
        """Generate human-readable backup report"""
        report = []
        report.append("💾 SOPHIA Intel Backup Report")
        report.append("=" * 35)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append(f"Total Items: {len(results)}")
        report.append(f"Successful: {len([r for r in results if r.status == 'success'])}")
        report.append(f"Failed: {len([r for r in results if r.status in ['failed', 'error']])}")
        report.append(f"Skipped: {len([r for r in results if r.status == 'skipped'])}")
        
        total_size = sum(r.size_bytes for r in results)
        report.append(f"Total Size: {total_size / (1024*1024):.2f} MB")
        report.append("")
        
        # Backup details
        report.append("📋 Backup Details:")
        for result in results:
            status_emoji = "✅" if result.status == "success" else "❌" if result.status in ["failed", "error"] else "⏭️"
            size_mb = result.size_bytes / (1024*1024) if result.size_bytes > 0 else 0
            report.append(f"{status_emoji} {result.backup_type}: {result.source} ({size_mb:.2f} MB)")
            if result.error:
                report.append(f"   Error: {result.error}")
        
        return "\n".join(report)

async def main():
    """Main backup function"""
    backup_system = BackupSystem()
    results = await backup_system.run_full_backup()
    
    # Generate and print report
    report = backup_system.generate_backup_report(results)
    print(report)
    
    # Save report
    os.makedirs("monitoring/reports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"monitoring/reports/backup_report_{timestamp}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    logger.info(f"Backup report saved to {report_file}")

if __name__ == "__main__":
    asyncio.run(main())

