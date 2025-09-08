"""
Audit Logging System for Pulumi ESC Secret Management
Comprehensive audit trail with compliance features, search, and reporting.
"""

import asyncio
import gzip
import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuditLevel(str, Enum):
    """Audit logging levels"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"


class AuditAction(str, Enum):
    """Types of auditable actions"""

    SECRET_ACCESS = "secret_access"
    SECRET_CREATE = "secret_create"
    SECRET_UPDATE = "secret_update"
    SECRET_DELETE = "secret_delete"
    SECRET_ROTATION = "secret_rotation"
    CONFIG_LOAD = "config_load"
    CONFIG_REFRESH = "config_refresh"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    ERROR_OCCURRED = "error_occurred"
    CACHE_INVALIDATE = "cache_invalidate"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"


@dataclass
class AuditContext:
    """Context information for audit events"""

    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    environment: Optional[str] = None
    service_name: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None


@dataclass
class AuditEvent:
    """Audit event record"""

    timestamp: datetime
    event_id: str
    level: AuditLevel
    action: AuditAction
    resource: str
    message: str
    context: AuditContext
    data: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_details: Optional[str] = None
    duration_ms: Optional[float] = None
    checksum: Optional[str] = field(init=False, default=None)

    def __post_init__(self):
        """Generate checksum for integrity verification"""
        self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum of event data"""
        data_copy = asdict(self)
        data_copy.pop("checksum", None)  # Remove checksum from calculation

        # Convert to JSON and sort keys for consistent hashing
        json_str = json.dumps(data_copy, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify event integrity using checksum"""
        original_checksum = self.checksum
        self.checksum = None  # Temporarily remove for recalculation

        try:
            calculated_checksum = self._calculate_checksum()
            return original_checksum == calculated_checksum
        finally:
            self.checksum = original_checksum


class AuditFilter(BaseModel):
    """Filter criteria for audit log queries"""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    levels: Optional[List[AuditLevel]] = None
    actions: Optional[List[AuditAction]] = None
    resources: Optional[List[str]] = None
    users: Optional[List[str]] = None
    environments: Optional[List[str]] = None
    success_only: Optional[bool] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    search_term: Optional[str] = None


class AuditStorageBackend(BaseModel):
    """Configuration for audit log storage"""

    backend_type: str  # "file", "database", "s3", "syslog"
    connection_params: Dict[str, Any] = Field(default_factory=dict)
    encryption_enabled: bool = True
    compression_enabled: bool = True
    retention_days: int = 2555  # 7 years for compliance
    max_file_size_mb: int = 100
    rotation_enabled: bool = True


class ESCAuditLogger:
    """Comprehensive audit logging system for ESC operations"""

    def __init__(
        self,
        storage_backends: List[AuditStorageBackend],
        encryption_key: Optional[bytes] = None,
        buffer_size: int = 100,
        flush_interval: int = 60,
        enable_integrity_checks: bool = True,
        compliance_mode: bool = True,
    ):
        self.storage_backends = storage_backends
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.enable_integrity_checks = enable_integrity_checks
        self.compliance_mode = compliance_mode

        # Encryption setup
        if encryption_key:
            self.cipher = Fernet(encryption_key)
        else:
            self.cipher = Fernet(Fernet.generate_key())

        # Event buffer for batch processing
        self.event_buffer: List[AuditEvent] = []
        self._buffer_lock = asyncio.Lock()

        # Background tasks
        self._flush_task: Optional[asyncio.Task] = None
        self._rotation_task: Optional[asyncio.Task] = None
        self._stop_logging = False

        # Statistics
        self.stats = {
            "total_events": 0,
            "events_by_level": {level.value: 0 for level in AuditLevel},
            "events_by_action": {action.value: 0 for action in AuditAction},
            "last_flush": None,
            "integrity_violations": 0,
            "storage_errors": 0,
        }

        # Compliance features
        self.sensitive_patterns = [
            r"password\s*[:=]\s*['\"]?([^'\"\\s]+)",
            r"key\s*[:=]\s*['\"]?([^'\"\\s]+)",
            r"token\s*[:=]\s*['\"]?([^'\"\\s]+)",
            r"secret\s*[:=]\s*['\"]?([^'\"\\s]+)",
        ]

    async def start(self):
        """Start the audit logging system"""
        logger.info("Starting ESC Audit Logger")

        # Start background tasks
        self._flush_task = asyncio.create_task(self._periodic_flush())
        self._rotation_task = asyncio.create_task(self._periodic_rotation())

        # Log system start
        await self.log_event(
            level=AuditLevel.INFO,
            action=AuditAction.SYSTEM_START,
            resource="audit_logger",
            message="ESC Audit Logger started",
            context=AuditContext(service_name="esc_audit_logger"),
        )

    async def stop(self):
        """Stop the audit logging system"""
        logger.info("Stopping ESC Audit Logger")

        # Stop background tasks
        self._stop_logging = True

        if self._flush_task:
            self._flush_task.cancel()
        if self._rotation_task:
            self._rotation_task.cancel()

        # Final flush
        await self.flush_events()

        # Log system stop
        await self.log_event(
            level=AuditLevel.INFO,
            action=AuditAction.SYSTEM_STOP,
            resource="audit_logger",
            message="ESC Audit Logger stopped",
            context=AuditContext(service_name="esc_audit_logger"),
        )

    async def log_event(
        self,
        level: AuditLevel,
        action: AuditAction,
        resource: str,
        message: str,
        context: AuditContext,
        data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_details: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ):
        """Log an audit event"""

        # Generate event ID
        event_id = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(self.event_buffer)}"

        # Create audit event
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_id=event_id,
            level=level,
            action=action,
            resource=self._sanitize_resource_name(resource),
            message=self._sanitize_message(message),
            context=context,
            data=self._sanitize_data(data or {}),
            success=success,
            error_details=error_details,
            duration_ms=duration_ms,
        )

        # Add to buffer
        async with self._buffer_lock:
            self.event_buffer.append(event)

            # Update statistics
            self.stats["total_events"] += 1
            self.stats["events_by_level"][level.value] += 1
            self.stats["events_by_action"][action.value] += 1

            # Immediate flush for critical events
            if (
                level in [AuditLevel.CRITICAL, AuditLevel.SECURITY]
                or not success
                or len(self.event_buffer) >= self.buffer_size
            ):
                await self._flush_buffer()

    def _sanitize_resource_name(self, resource: str) -> str:
        """Sanitize resource name to prevent injection attacks"""
        # Remove potentially dangerous characters
        sanitized = resource.replace("\n", "").replace("\r", "").replace("\t", " ")

        # Mask secret patterns
        import re

        for pattern in self.sensitive_patterns:
            sanitized = re.sub(pattern, r"\1***", sanitized, flags=re.IGNORECASE)

        return sanitized[:255]  # Limit length

    def _sanitize_message(self, message: str) -> str:
        """Sanitize log message"""
        return self._sanitize_resource_name(message)

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data in event payload"""
        sanitized = {}

        for key, value in data.items():
            key_lower = key.lower()

            # Mask sensitive keys
            if any(sensitive in key_lower for sensitive in ["password", "key", "secret", "token"]):
                if isinstance(value, str) and len(value) > 4:
                    sanitized[key] = f"***{value[-4:]}"  # Show last 4 chars
                else:
                    sanitized[key] = "***REDACTED***"
            else:
                # Recursively sanitize nested dictionaries
                if isinstance(value, dict):
                    sanitized[key] = self._sanitize_data(value)
                elif isinstance(value, str):
                    sanitized[key] = self._sanitize_message(value)
                else:
                    sanitized[key] = value

        return sanitized

    async def _periodic_flush(self):
        """Periodic flush of event buffer"""
        while not self._stop_logging:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")

    async def _periodic_rotation(self):
        """Periodic log rotation"""
        while not self._stop_logging:
            try:
                await asyncio.sleep(86400)  # Daily rotation
                await self._rotate_logs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic rotation: {e}")

    async def flush_events(self):
        """Flush events from buffer to storage"""
        async with self._buffer_lock:
            if not self.event_buffer:
                return

            events_to_flush = self.event_buffer.copy()
            await self._flush_buffer()

        # Write to all storage backends
        for backend in self.storage_backends:
            try:
                await self._write_to_backend(backend, events_to_flush)
            except Exception as e:
                logger.error(f"Failed to write to backend {backend.backend_type}: {e}")
                self.stats["storage_errors"] += 1

        self.stats["last_flush"] = datetime.utcnow()

    async def _flush_buffer(self):
        """Internal buffer flush (assumes lock is held)"""
        self.event_buffer.clear()

    async def _write_to_backend(self, backend: AuditStorageBackend, events: List[AuditEvent]):
        """Write events to specific storage backend"""

        if backend.backend_type == "file":
            await self._write_to_file(backend, events)
        elif backend.backend_type == "database":
            await self._write_to_database(backend, events)
        elif backend.backend_type == "syslog":
            await self._write_to_syslog(backend, events)
        else:
            logger.warning(f"Unsupported backend type: {backend.backend_type}")

    async def _write_to_file(self, backend: AuditStorageBackend, events: List[AuditEvent]):
        """Write events to file storage"""
        log_file = Path(backend.connection_params.get("file_path", "audit.log"))
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Prepare log entries
        log_entries = []
        for event in events:
            # Verify integrity if enabled
            if self.enable_integrity_checks and not event.verify_integrity():
                logger.error(f"Integrity check failed for event {event.event_id}")
                self.stats["integrity_violations"] += 1
                continue

            # Convert to JSON
            event_data = asdict(event)
            event_data["timestamp"] = event.timestamp.isoformat()

            # Encrypt if enabled
            if backend.encryption_enabled:
                event_json = json.dumps(event_data)
                encrypted_data = self.cipher.encrypt(event_json.encode()).decode()
                log_entries.append(encrypted_data)
            else:
                log_entries.append(json.dumps(event_data))

        # Write to file
        content = "\n".join(log_entries) + "\n"

        if backend.compression_enabled:
            content = gzip.compress(content.encode()).decode("latin1")

        async with aiofiles.open(log_file, "a") as f:
            await f.write(content)

    async def _write_to_database(self, backend: AuditStorageBackend, events: List[AuditEvent]):
        """Write events to database storage"""
        # Database implementation would go here
        # For now, just log the action
        logger.debug(f"Would write {len(events)} events to database")

    async def _write_to_syslog(self, backend: AuditStorageBackend, events: List[AuditEvent]):
        """Write events to syslog"""
        # Syslog implementation would go here
        logger.debug(f"Would write {len(events)} events to syslog")

    async def _rotate_logs(self):
        """Rotate log files based on size and retention policy"""
        for backend in self.storage_backends:
            if backend.backend_type == "file" and backend.rotation_enabled:
                await self._rotate_file_logs(backend)

    async def _rotate_file_logs(self, backend: AuditStorageBackend):
        """Rotate file-based logs"""
        log_file = Path(backend.connection_params.get("file_path", "audit.log"))

        if not log_file.exists():
            return

        # Check file size
        file_size_mb = log_file.stat().st_size / (1024 * 1024)

        if file_size_mb > backend.max_file_size_mb:
            # Create rotated filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            rotated_file = log_file.parent / f"{log_file.stem}_{timestamp}{log_file.suffix}"

            # Move current log to rotated name
            log_file.rename(rotated_file)

            logger.info(f"Rotated audit log: {log_file} -> {rotated_file}")

            # Compress rotated file if enabled
            if backend.compression_enabled:
                await self._compress_log_file(rotated_file)

    async def _compress_log_file(self, file_path: Path):
        """Compress a log file"""
        compressed_path = file_path.with_suffix(f"{file_path.suffix}.gz")

        async with aiofiles.open(file_path, "rb") as f_in:
            content = await f_in.read()

        compressed_content = gzip.compress(content)

        async with aiofiles.open(compressed_path, "wb") as f_out:
            await f_out.write(compressed_content)

        # Remove original file
        file_path.unlink()
        logger.debug(f"Compressed audit log: {file_path} -> {compressed_path}")

    async def search_events(self, filter_criteria: AuditFilter) -> List[AuditEvent]:
        """Search audit events based on filter criteria"""
        # This would implement event searching across storage backends
        # For now, return empty list with a log message
        logger.info(f"Search request: {filter_criteria}")
        return []

    async def generate_compliance_report(
        self, start_date: datetime, end_date: datetime, report_type: str = "full"
    ) -> Dict[str, Any]:
        """Generate compliance audit report"""

        report = {
            "report_generated": datetime.utcnow().isoformat(),
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "report_type": report_type,
            "statistics": self.get_statistics(),
            "compliance_status": {
                "integrity_checks_enabled": self.enable_integrity_checks,
                "encryption_enabled": any(b.encryption_enabled for b in self.storage_backends),
                "retention_policy": max(b.retention_days for b in self.storage_backends),
                "storage_backends": len(self.storage_backends),
            },
        }

        # Add security analysis
        if report_type in ["full", "security"]:
            report["security_analysis"] = {
                "authentication_events": self.stats["events_by_action"].get("authentication", 0),
                "authorization_events": self.stats["events_by_action"].get("authorization", 0),
                "failed_operations": sum(1 for event in self.event_buffer if not event.success),
                "integrity_violations": self.stats["integrity_violations"],
                "storage_errors": self.stats["storage_errors"],
            }

        return report

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics"""
        return self.stats.copy()

    async def log_secret_access(
        self,
        secret_key: str,
        environment: str,
        context: AuditContext,
        success: bool = True,
        error_details: Optional[str] = None,
    ):
        """Convenience method for logging secret access"""
        await self.log_event(
            level=AuditLevel.SECURITY if success else AuditLevel.ERROR,
            action=AuditAction.SECRET_ACCESS,
            resource=f"{environment}.{secret_key}",
            message=f"Secret access: {secret_key} in {environment}",
            context=context,
            success=success,
            error_details=error_details,
        )

    async def log_secret_rotation(
        self,
        secret_key: str,
        environment: str,
        rotation_id: str,
        context: AuditContext,
        success: bool = True,
        error_details: Optional[str] = None,
    ):
        """Convenience method for logging secret rotation"""
        await self.log_event(
            level=AuditLevel.SECURITY,
            action=AuditAction.SECRET_ROTATION,
            resource=f"{environment}.{secret_key}",
            message=f"Secret rotation: {secret_key} in {environment} (ID: {rotation_id})",
            context=context,
            data={"rotation_id": rotation_id},
            success=success,
            error_details=error_details,
        )

    async def log_config_load(
        self,
        source: str,
        environment: str,
        context: AuditContext,
        entries_loaded: int,
        success: bool = True,
        error_details: Optional[str] = None,
    ):
        """Convenience method for logging configuration loads"""
        await self.log_event(
            level=AuditLevel.INFO if success else AuditLevel.ERROR,
            action=AuditAction.CONFIG_LOAD,
            resource=f"{environment}.config",
            message=f"Configuration loaded from {source}: {entries_loaded} entries",
            context=context,
            data={"source": source, "entries_loaded": entries_loaded},
            success=success,
            error_details=error_details,
        )
