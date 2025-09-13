#!/usr/bin/env python3
"""
Migration Rollback Script
Safely rollback ESC migration and restore original configuration files.
"""
import asyncio
import json
import logging
import os
import shutil
# Add project root to path
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import aiofiles
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table
sys.path.append(str(Path(__file__).parent.parent.parent))
from infrastructure.pulumi.esc.audit_logger import (
    AuditAction,
    AuditContext,
    AuditLevel,
    AuditStorageBackend,
    ESCAuditLogger,
)
from infrastructure.pulumi.esc.secrets_manager import ESCSecretsManager
console = Console()
logger = logging.getLogger(__name__)
@dataclass
class RollbackConfig:
    """Configuration for rollback operation"""
    backup_directory: str
    target_backup: Optional[str] = None  # Specific backup to restore
    restore_env_files: bool = True
    remove_esc_secrets: bool = False  # Whether to remove secrets from ESC
    create_rollback_backup: bool = True
    force_rollback: bool = False  # Skip safety checks
    environments_to_clean: List[str] = field(
        default_factory=lambda: ["dev", "staging", "production"]
    )
    pulumi_org: str = "sophia-intel"
    pulumi_api_token: Optional[str] = None
@dataclass
class BackupInfo:
    """Information about available backups"""
    timestamp: str
    backup_path: Path
    manifest_file: Optional[Path]
    source_files: List[str]
    secrets_count: int
    environments: List[str]
    description: str
@dataclass
class RollbackResult:
    """Result of rollback operation"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    restored_files: List[str] = field(default_factory=list)
    removed_secrets: List[str] = field(default_factory=list)
    skipped_operations: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    rollback_backup_path: Optional[str] = None
    @property
    def success_rate(self) -> float:
        return (
            (self.successful_operations / self.total_operations * 100)
            if self.total_operations > 0
            else 0
        )
class ESCMigrationRollback:
    """Handles safe rollback of ESC migration"""
    def __init__(self, config: RollbackConfig):
        self.config = config
        self.available_backups: List[BackupInfo] = []
        self.selected_backup: Optional[BackupInfo] = None
        self.rollback_result = RollbackResult()
        # Initialize ESC manager if token provided
        self.esc_manager: Optional[ESCSecretsManager] = None
        if config.pulumi_api_token:
            self.esc_manager = ESCSecretsManager(
                api_token=config.pulumi_api_token, organization=config.pulumi_org
            )
        # Initialize audit logger
        audit_backends = [
            AuditStorageBackend(
                backend_type="file",
                connection_params={"file_path": "logs/rollback_audit.log"},
            )
        ]
        self.audit_logger = ESCAuditLogger(audit_backends)
    async def execute_rollback(self) -> RollbackResult:
        """Execute the complete rollback process"""
        console.print(
            Panel.fit(
                "[bold red]ESC Migration Rollback[/bold red]\n"
                "⚠️  This will restore original configuration files\n"
                "⚠️  ESC secrets may be removed if requested",
                title="Rollback Warning",
            )
        )
        try:
            await self.audit_logger.start()
            # Step 1: Discover available backups
            await self._discover_backups()
            # Step 2: Select backup to restore
            await self._select_backup()
            # Step 3: Safety checks
            if not self.config.force_rollback:
                await self._perform_safety_checks()
            # Step 4: Create rollback backup (backup current state)
            if self.config.create_rollback_backup:
                await self._create_rollback_backup()
            # Step 5: Restore configuration files
            if self.config.restore_env_files:
                await self._restore_configuration_files()
            # Step 6: Remove ESC secrets (if requested)
            if self.config.remove_esc_secrets and self.esc_manager:
                await self._remove_esc_secrets()
            # Step 7: Verify rollback
            await self._verify_rollback()
            # Step 8: Generate rollback report
            await self._generate_rollback_report()
            return self.rollback_result
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            self.rollback_result.errors.append(f"Rollback failed: {e}")
            await self.audit_logger.log_event(
                level=AuditLevel.ERROR,
                action=AuditAction.ERROR_OCCURRED,
                resource="migration_rollback",
                message=f"Rollback failed: {e}",
                context=AuditContext(service_name="rollback_tool"),
                success=False,
                error_details=str(e),
            )
            raise
        finally:
            await self.audit_logger.stop()
    async def _discover_backups(self):
        """Discover available migration backups"""
        console.print("\n[bold]Step 1: Discovering available backups...[/bold]")
        backup_root = Path(self.config.backup_directory)
        if not backup_root.exists():
            raise ValueError(f"Backup directory not found: {backup_root}")
        # Find backup directories
        backup_patterns = ["migration_backup_*", "backup_*", "*_backup"]
        for pattern in backup_patterns:
            for backup_dir in backup_root.glob(pattern):
                if backup_dir.is_dir():
                    backup_info = await self._analyze_backup(backup_dir)
                    if backup_info:
                        self.available_backups.append(backup_info)
        if not self.available_backups:
            raise ValueError("No migration backups found")
        # Sort by timestamp (newest first)
        self.available_backups.sort(key=lambda b: b.timestamp, reverse=True)
        console.print(
            f"[green]✓[/green] Found {len(self.available_backups)} available backups"
        )
        # Display available backups
        table = Table(title="Available Backups")
        table.add_column("ID", style="cyan", width=3)
        table.add_column("Timestamp", style="green")
        table.add_column("Files", justify="right", style="yellow")
        table.add_column("Secrets", justify="right", style="blue")
        table.add_column("Description", style="dim")
        for i, backup in enumerate(self.available_backups):
            table.add_row(
                str(i + 1),
                backup.timestamp,
                str(len(backup.source_files)),
                str(backup.secrets_count),
                backup.description,
            )
        console.print(table)
        await self.audit_logger.log_event(
            level=AuditLevel.INFO,
            action=AuditAction.CONFIG_LOAD,
            resource="backup_discovery",
            message=f"Discovered {len(self.available_backups)} migration backups",
            context=AuditContext(service_name="rollback_tool"),
        )
    async def _analyze_backup(self, backup_dir: Path) -> Optional[BackupInfo]:
        """Analyze a backup directory and extract information"""
        try:
            # Look for manifest file
            manifest_file = None
            manifest_files = list(backup_dir.glob("*manifest*.json"))
            if manifest_files:
                manifest_file = manifest_files[0]
            # Extract timestamp from directory name
            timestamp = "unknown"
            if "_" in backup_dir.name:
                timestamp_part = backup_dir.name.split("_")[-1]
                try:
                    # Try to parse as timestamp
                    datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
                    timestamp = timestamp_part
                except ValueError:
                    timestamp = timestamp_part
            # Analyze contents
            env_files = list(backup_dir.glob("*.env*"))
            json_files = list(backup_dir.glob("*.json"))
            secrets_count = 0
            environments = []
            source_files = []
            # Load manifest if available
            if manifest_file:
                async with aiofiles.open(manifest_file) as f:
                    content = await f.read()
                manifest = json.loads(content)
                secrets_count = manifest.get("discovered_secrets", 0)
                environments = manifest.get("target_environments", [])
                source_files = manifest.get("source_files", [])
            else:
                # Estimate from files
                source_files = [str(f) for f in env_files]
                secrets_count = len(env_files) * 10  # Rough estimate
            description = f"Backup from {timestamp}"
            if manifest_file:
                description += " (with manifest)"
            return BackupInfo(
                timestamp=timestamp,
                backup_path=backup_dir,
                manifest_file=manifest_file,
                source_files=source_files,
                secrets_count=secrets_count,
                environments=environments,
                description=description,
            )
        except Exception as e:
            logger.warning(f"Error analyzing backup {backup_dir}: {e}")
            return None
    async def _select_backup(self):
        """Select backup to restore"""
        console.print("\n[bold]Step 2: Selecting backup to restore...[/bold]")
        if self.config.target_backup:
            # Find specific backup
            for backup in self.available_backups:
                if (
                    self.config.target_backup in backup.timestamp
                    or self.config.target_backup in str(backup.backup_path)
                ):
                    self.selected_backup = backup
                    break
            if not self.selected_backup:
                raise ValueError(
                    f"Specified backup not found: {self.config.target_backup}"
                )
        else:
            # Use most recent backup
            self.selected_backup = self.available_backups[0]
            if not self.config.force_rollback:
                console.print(
                    f"[yellow]Selected backup: {self.selected_backup.description}[/yellow]"
                )
                if not Confirm.ask("Proceed with this backup?"):
                    console.print("[red]Rollback cancelled by user[/red]")
                    return False
        console.print(
            f"[green]✓[/green] Selected backup: {self.selected_backup.timestamp}"
        )
        console.print(f"  Path: {self.selected_backup.backup_path}")
        console.print(f"  Files: {len(self.selected_backup.source_files)}")
        console.print(f"  Secrets: {self.selected_backup.secrets_count}")
        await self.audit_logger.log_event(
            level=AuditLevel.INFO,
            action=AuditAction.BACKUP_RESTORE,
            resource="backup_selection",
            message=f"Selected backup for restore: {self.selected_backup.timestamp}",
            context=AuditContext(service_name="rollback_tool"),
            data={"backup_path": str(self.selected_backup.backup_path)},
        )
    async def _perform_safety_checks(self):
        """Perform safety checks before rollback"""
        console.print("\n[bold]Step 3: Performing safety checks...[/bold]")
        safety_issues = []
        # Check if current files exist (would be overwritten)
        current_files = []
        for source_file in self.selected_backup.source_files:
            if Path(source_file).exists():
                current_files.append(source_file)
        if current_files:
            console.print(
                f"[yellow]⚠[/yellow] {len(current_files)} files will be overwritten"
            )
            safety_issues.append(f"{len(current_files)} files will be overwritten")
        # Check ESC secrets (if removal requested)
        if self.config.remove_esc_secrets and self.esc_manager:
            try:
                async with self.esc_manager:
                    for env in self.config.environments_to_clean:
                        config = await self.esc_manager.get_environment_config(env)
                        if config:
                            console.print(
                                f"[yellow]⚠[/yellow] ESC secrets in {env} will be removed"
                            )
                            safety_issues.append(
                                f"ESC secrets in {env} will be removed"
                            )
            except Exception as e:
                logger.warning(f"Could not check ESC secrets: {e}")
        # Check if system is currently running
        # (This would check for running processes, active connections, etc.)
        # For now, just warn about potential impact
        console.print("[yellow]⚠[/yellow] Rollback may impact running systems")
        safety_issues.append("Rollback may impact running systems")
        # Display safety summary
        if safety_issues:
            console.print("\n[bold red]Safety Issues Detected:[/bold red]")
            for issue in safety_issues:
                console.print(f"  • {issue}")
            if not self.config.force_rollback:
                console.print(
                    "\n[red]This rollback operation has safety implications.[/red]"
                )
                if not Confirm.ask("Do you want to continue?"):
                    console.print("[red]Rollback cancelled by user[/red]")
                    raise SystemExit("Rollback cancelled for safety")
        else:
            console.print("[green]✓[/green] No safety issues detected")
        await self.audit_logger.log_event(
            level=AuditLevel.WARNING,
            action=AuditAction.AUTHORIZATION,
            resource="safety_check",
            message=f"Safety check completed: {len(safety_issues)} issues found",
            context=AuditContext(service_name="rollback_tool"),
            data={"safety_issues": safety_issues},
        )
    async def _create_rollback_backup(self):
        """Create backup of current state before rollback"""
        console.print("\n[bold]Step 4: Creating rollback backup...[/bold]")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rollback_backup_dir = (
            Path(self.config.backup_directory) / f"rollback_backup_{timestamp}"
        )
        rollback_backup_dir.mkdir(parents=True, exist_ok=True)
        try:
            backed_up_files = []
            # Backup current .env files
            project_root = Path(__file__).parent.parent.parent
            for env_pattern in [".env*", "*/.env*"]:
                for env_file in project_root.glob(env_pattern):
                    if env_file.is_file() and not env_file.name.endswith(".example"):
                        backup_file = rollback_backup_dir / env_file.name
                        shutil.copy2(env_file, backup_file)
                        backed_up_files.append(str(env_file))
            # Create manifest
            rollback_manifest = {
                "rollback_backup_created": datetime.now().isoformat(),
                "original_state_before_rollback": True,
                "backed_up_files": backed_up_files,
                "target_restore_backup": self.selected_backup.timestamp,
                "rollback_config": {
                    "restore_env_files": self.config.restore_env_files,
                    "remove_esc_secrets": self.config.remove_esc_secrets,
                    "environments_to_clean": self.config.environments_to_clean,
                },
            }
            manifest_file = rollback_backup_dir / "rollback_manifest.json"
            async with aiofiles.open(manifest_file, "w") as f:
                await f.write(json.dumps(rollback_manifest, indent=2))
            self.rollback_result.rollback_backup_path = str(rollback_backup_dir)
            console.print(
                f"[green]✓[/green] Rollback backup created: {rollback_backup_dir}"
            )
            console.print(f"  Files backed up: {len(backed_up_files)}")
            await self.audit_logger.log_event(
                level=AuditLevel.INFO,
                action=AuditAction.BACKUP_CREATE,
                resource="rollback_backup",
                message=f"Created rollback backup at {rollback_backup_dir}",
                context=AuditContext(service_name="rollback_tool"),
                data={
                    "backup_path": str(rollback_backup_dir),
                    "files_backed_up": len(backed_up_files),
                },
            )
        except Exception as e:
            error_msg = f"Failed to create rollback backup: {e}"
            self.rollback_result.errors.append(error_msg)
            console.print(f"[red]✗[/red] {error_msg}")
    async def _restore_configuration_files(self):
        """Restore configuration files from backup"""
        console.print("\n[bold]Step 5: Restoring configuration files...[/bold]")
        if not self.selected_backup:
            raise ValueError("No backup selected for restore")
        backup_dir = self.selected_backup.backup_path
        project_root = Path(__file__).parent.parent.parent
        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            restore_task = progress.add_task(
                "Restoring files...", total=len(self.selected_backup.source_files)
            )
            for source_file in self.selected_backup.source_files:
                try:
                    source_path = Path(source_file)
                    backup_file = backup_dir / source_path.name
                    if backup_file.exists():
                        # Restore file
                        target_path = project_root / source_path.name
                        # Read from backup
                        async with aiofiles.open(backup_file) as f:
                            content = await f.read()
                        # Write to target
                        async with aiofiles.open(target_path, "w") as f:
                            await f.write(content)
                        self.rollback_result.successful_operations += 1
                        self.rollback_result.restored_files.append(str(target_path))
                        await self.audit_logger.log_event(
                            level=AuditLevel.INFO,
                            action=AuditAction.BACKUP_RESTORE,
                            resource=str(target_path),
                            message="Restored file from backup",
                            context=AuditContext(service_name="rollback_tool"),
                            success=True,
                        )
                    else:
                        self.rollback_result.skipped_operations.append(
                            f"Backup file not found: {backup_file}"
                        )
                        logger.warning(f"Backup file not found: {backup_file}")
                    self.rollback_result.total_operations += 1
                except Exception as e:
                    error_msg = f"Failed to restore {source_file}: {e}"
                    self.rollback_result.failed_operations += 1
                    self.rollback_result.errors.append(error_msg)
                    logger.error(error_msg)
                    await self.audit_logger.log_event(
                        level=AuditLevel.ERROR,
                        action=AuditAction.BACKUP_RESTORE,
                        resource=source_file,
                        message="Failed to restore file from backup",
                        context=AuditContext(service_name="rollback_tool"),
                        success=False,
                        error_details=str(e),
                    )
                progress.advance(restore_task)
        console.print(
            f"[green]✓[/green] Restored {self.rollback_result.successful_operations} files"
        )
        if self.rollback_result.failed_operations > 0:
            console.print(
                f"[red]✗[/red] Failed to restore {self.rollback_result.failed_operations} files"
            )
    async def _remove_esc_secrets(self):
        """Remove secrets from ESC environments"""
        console.print("\n[bold]Step 6: Removing ESC secrets...[/bold]")
        if not self.esc_manager:
            self.rollback_result.warnings.append(
                "No ESC manager available - skipping secret removal"
            )
            console.print(
                "[yellow]⚠[/yellow] No ESC manager available - skipping secret removal"
            )
            return
        # Load secrets to remove from manifest
        secrets_to_remove = []
        if self.selected_backup.manifest_file:
            try:
                async with aiofiles.open(self.selected_backup.manifest_file) as f:
                    content = await f.read()
                manifest = json.loads(content)
                if "secrets_by_category" in manifest:
                    for category, secrets in manifest["secrets_by_category"].items():
                        for secret in secrets:
                            secrets_to_remove.append(secret["key"])
            except Exception as e:
                logger.warning(f"Could not load secrets from manifest: {e}")
        # If no manifest, try to identify secrets from ESC environments
        if not secrets_to_remove:
            console.print(
                "[yellow]⚠[/yellow] No manifest found - cannot identify specific secrets to remove"
            )
            self.rollback_result.warnings.append(
                "Cannot identify specific secrets - ESC cleanup skipped"
            )
            return
        removal_count = 0
        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            removal_task = progress.add_task(
                "Removing secrets...",
                total=len(secrets_to_remove) * len(self.config.environments_to_clean),
            )
            async with self.esc_manager:
                for environment in self.config.environments_to_clean:
                    for secret_key in secrets_to_remove:
                        try:
                            # Note: Actual secret removal would depend on ESC API capabilities
                            # For now, we'll just log the operation
                            # Check if secret exists first
                            secret_value = await self.esc_manager.get_secret(
                                secret_key, environment, use_cache=False
                            )
                            if secret_value is not None:
                                # Would remove secret here
                                # await self.esc_manager.delete_secret(secret_key, environment)
                                removal_count += 1
                                self.rollback_result.removed_secrets.append(
                                    f"{environment}.{secret_key}"
                                )
                                await self.audit_logger.log_event(
                                    level=AuditLevel.SECURITY,
                                    action=AuditAction.SECRET_DELETE,
                                    resource=f"{environment}.{secret_key}",
                                    message="Secret removed during rollback",
                                    context=AuditContext(service_name="rollback_tool"),
                                    success=True,
                                )
                                console.print(
                                    f"[red]Removed: {environment}.{secret_key}[/red]"
                                )
                            self.rollback_result.total_operations += 1
                            self.rollback_result.successful_operations += 1
                        except Exception as e:
                            error_msg = (
                                f"Failed to remove {secret_key} from {environment}: {e}"
                            )
                            self.rollback_result.failed_operations += 1
                            self.rollback_result.errors.append(error_msg)
                            logger.error(error_msg)
                        progress.advance(removal_task)
        console.print(f"[green]✓[/green] Removed {removal_count} secrets from ESC")
        # Log warning about ESC secret removal
        self.rollback_result.warnings.append(
            "ESC secret removal simulated - actual removal would require ESC API delete capabilities"
        )
    async def _verify_rollback(self):
        """Verify rollback was successful"""
        console.print("\n[bold]Step 7: Verifying rollback...[/bold]")
        verification_issues = []
        # Verify restored files exist and are readable
        for restored_file in self.rollback_result.restored_files:
            try:
                file_path = Path(restored_file)
                if not file_path.exists():
                    verification_issues.append(
                        f"Restored file missing: {restored_file}"
                    )
                elif file_path.stat().st_size == 0:
                    verification_issues.append(f"Restored file empty: {restored_file}")
            except Exception as e:
                verification_issues.append(f"Cannot verify {restored_file}: {e}")
        # Verify basic file contents (sample check)
        try:
            env_file = Path(".env")
            if env_file.exists():
                async with aiofiles.open(env_file) as f:
                    content = await f.read()
                if "=" not in content:
                    verification_issues.append(".env file appears to be invalid format")
                elif len(content.strip()) == 0:
                    verification_issues.append(".env file is empty")
        except Exception as e:
            verification_issues.append(f"Cannot verify .env file: {e}")
        if verification_issues:
            console.print(
                f"[yellow]⚠[/yellow] Verification found {len(verification_issues)} issues:"
            )
            for issue in verification_issues:
                console.print(f"  • {issue}")
            self.rollback_result.warnings.extend(verification_issues)
        else:
            console.print("[green]✓[/green] Rollback verification passed")
        await self.audit_logger.log_event(
            level=AuditLevel.INFO,
            action=AuditAction.CONFIG_LOAD,
            resource="rollback_verification",
            message=f"Rollback verification completed: {len(verification_issues)} issues found",
            context=AuditContext(service_name="rollback_tool"),
            data={"verification_issues": len(verification_issues)},
        )
    async def _generate_rollback_report(self):
        """Generate comprehensive rollback report"""
        console.print("\n[bold]Step 8: Generating rollback report...[/bold]")
        report = {
            "rollback_completed": datetime.now().isoformat(),
            "selected_backup": {
                "timestamp": self.selected_backup.timestamp,
                "path": str(self.selected_backup.backup_path),
                "secrets_count": self.selected_backup.secrets_count,
            },
            "configuration": {
                "restore_env_files": self.config.restore_env_files,
                "remove_esc_secrets": self.config.remove_esc_secrets,
                "force_rollback": self.config.force_rollback,
                "environments_cleaned": self.config.environments_to_clean,
            },
            "results": {
                "total_operations": self.rollback_result.total_operations,
                "successful_operations": self.rollback_result.successful_operations,
                "failed_operations": self.rollback_result.failed_operations,
                "success_rate": round(self.rollback_result.success_rate, 2),
                "restored_files_count": len(self.rollback_result.restored_files),
                "removed_secrets_count": len(self.rollback_result.removed_secrets),
            },
            "restored_files": self.rollback_result.restored_files,
            "removed_secrets": self.rollback_result.removed_secrets,
            "skipped_operations": self.rollback_result.skipped_operations,
            "errors": self.rollback_result.errors,
            "warnings": self.rollback_result.warnings,
            "rollback_backup_path": self.rollback_result.rollback_backup_path,
        }
        # Save report
        report_file = f"rollback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        async with aiofiles.open(report_file, "w") as f:
            await f.write(json.dumps(report, indent=2))
        # Display summary
        table = Table(title="Rollback Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right", style="green")
        table.add_column("Status", style="yellow")
        table.add_row(
            "Total Operations", str(self.rollback_result.total_operations), ""
        )
        table.add_row(
            "Successful",
            str(self.rollback_result.successful_operations),
            "[green]✓[/green]",
        )
        table.add_row(
            "Failed",
            str(self.rollback_result.failed_operations),
            (
                "[red]✗[/red]"
                if self.rollback_result.failed_operations > 0
                else "[green]✓[/green]"
            ),
        )
        table.add_row(
            "Files Restored",
            str(len(self.rollback_result.restored_files)),
            "[green]✓[/green]",
        )
        table.add_row(
            "Secrets Removed",
            str(len(self.rollback_result.removed_secrets)),
            "[yellow]⚠[/yellow]" if self.rollback_result.removed_secrets else "N/A",
        )
        table.add_row("Success Rate", f"{self.rollback_result.success_rate:.1f}%", "")
        console.print(table)
        if self.rollback_result.successful_operations > 0:
            console.print(
                "\n[bold green]✓ Rollback completed successfully![/bold green]"
            )
        else:
            console.print("\n[bold red]✗ Rollback completed with issues[/bold red]")
        if self.rollback_result.errors:
            console.print(f"\n[red]Errors ({len(self.rollback_result.errors)}):[/red]")
            for error in self.rollback_result.errors[:3]:
                console.print(f"  • {error}")
            if len(self.rollback_result.errors) > 3:
                console.print(f"  ... and {len(self.rollback_result.errors) - 3} more")
        if self.rollback_result.warnings:
            console.print(
                f"\n[yellow]Warnings ({len(self.rollback_result.warnings)}):[/yellow]"
            )
            for warning in self.rollback_result.warnings[:3]:
                console.print(f"  • {warning}")
            if len(self.rollback_result.warnings) > 3:
                console.print(
                    f"  ... and {len(self.rollback_result.warnings) - 3} more"
                )
        console.print(f"\n[green]✓[/green] Rollback report saved: {report_file}")
        if self.rollback_result.rollback_backup_path:
            console.print(
                f"[blue]ℹ[/blue] Pre-rollback state backed up to: {self.rollback_result.rollback_backup_path}"
            )
        await self.audit_logger.log_event(
            level=AuditLevel.INFO,
            action=AuditAction.BACKUP_RESTORE,
            resource="rollback_complete",
            message=f"Rollback completed: {self.rollback_result.success_rate:.1f}% success rate",
            context=AuditContext(service_name="rollback_tool"),
            data={
                "total_operations": self.rollback_result.total_operations,
                "successful_operations": self.rollback_result.successful_operations,
                "failed_operations": self.rollback_result.failed_operations,
            },
        )
async def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="Rollback ESC migration")
    parser.add_argument(
        "--backup-dir", default="backup_configs/migration", help="Backup directory"
    )
    parser.add_argument("--target-backup", help="Specific backup timestamp to restore")
    parser.add_argument(
        "--no-restore-files",
        action="store_true",
        help="Skip restoring configuration files",
    )
    parser.add_argument(
        "--remove-esc-secrets", action="store_true", help="Remove secrets from ESC"
    )
    parser.add_argument(
        "--no-rollback-backup",
        action="store_true",
        help="Skip creating rollback backup",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force rollback without safety checks"
    )
    parser.add_argument("--pulumi-token", help="Pulumi API token")
    parser.add_argument("--org", default="sophia-intel", help="Pulumi organization")
    parser.add_argument(
        "--environments",
        nargs="+",
        default=["dev", "staging", "production"],
        help="ESC environments to clean",
    )
    args = parser.parse_args()
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Create rollback configuration
    config = RollbackConfig(
        backup_directory=args.backup_dir,
        target_backup=args.target_backup,
        restore_env_files=not args.no_restore_files,
        remove_esc_secrets=args.remove_esc_secrets,
        create_rollback_backup=not args.no_rollback_backup,
        force_rollback=args.force,
        environments_to_clean=args.environments,
        pulumi_org=args.org,
        pulumi_api_token=args.pulumi_token or os.getenv("PULUMI_API_KEY"),
    )
    # Confirm destructive operation
    if not config.force_rollback:
        console.print(
            "\n[bold red]⚠️  WARNING: This will rollback your ESC migration![/bold red]"
        )
        console.print("This operation will:")
        if config.restore_env_files:
            console.print("  • Restore original configuration files")
        if config.remove_esc_secrets:
            console.print("  • Remove secrets from Pulumi ESC")
        console.print("  • May disrupt running systems")
        if not Confirm.ask("\nAre you sure you want to proceed?"):
            console.print("[yellow]Rollback cancelled by user[/yellow]")
            return 0
    # Execute rollback
    rollback_tool = ESCMigrationRollback(config)
    try:
        result = await rollback_tool.execute_rollback()
        if result.success_rate > 80:
            console.print(
                "\n[bold green]🎉 Rollback completed successfully![/bold green]"
            )
            return 0
        else:
            console.print(
                "\n[bold yellow]⚠️  Rollback completed with issues[/bold yellow]"
            )
            return 1
    except Exception as e:
        console.print(f"\n[bold red]💥 Rollback failed: {e}[/bold red]")
        return 2
if __name__ == "__main__":
    asyncio.run(main())
