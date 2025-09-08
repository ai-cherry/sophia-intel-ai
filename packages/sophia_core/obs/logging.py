"""
Structured Logging with Redaction

Provides structured JSON logging with automatic redaction of sensitive information
including PII, API keys, and other configurable sensitive patterns.
"""

import json
import logging
import re
import sys
import traceback
from datetime import datetime
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..config.helpers import redact_sensitive_data


class LogLevel(str, Enum):
    """Log levels for structured logging."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogRecord(BaseModel):
    """
    Structured log record with automatic redaction.
    """

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: LogLevel
    message: str
    component: str  # agent, swarm, tool, memory, etc.

    # Context information
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    swarm_id: Optional[str] = None
    task_id: Optional[str] = None

    # Additional fields
    fields: Dict[str, Any] = Field(default_factory=dict)

    # Error information
    error: Optional[str] = None
    error_type: Optional[str] = None
    traceback: Optional[str] = None

    # Performance metrics
    duration_ms: Optional[float] = None
    memory_mb: Optional[float] = None

    def to_dict(self, redact: bool = True) -> Dict[str, Any]:
        """
        Convert log record to dictionary.

        Args:
            redact: Whether to redact sensitive information

        Returns:
            Dict[str, Any]: Log record as dictionary
        """
        record_dict = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "component": self.component,
        }

        # Add optional fields
        if self.session_id:
            record_dict["session_id"] = self.session_id
        if self.agent_id:
            record_dict["agent_id"] = self.agent_id
        if self.swarm_id:
            record_dict["swarm_id"] = self.swarm_id
        if self.task_id:
            record_dict["task_id"] = self.task_id

        # Add error information
        if self.error:
            record_dict["error"] = self.error
        if self.error_type:
            record_dict["error_type"] = self.error_type
        if self.traceback:
            record_dict["traceback"] = self.traceback

        # Add performance metrics
        if self.duration_ms is not None:
            record_dict["duration_ms"] = self.duration_ms
        if self.memory_mb is not None:
            record_dict["memory_mb"] = self.memory_mb

        # Add custom fields
        if self.fields:
            record_dict.update(self.fields)

        # Redact sensitive information
        if redact:
            record_dict = redact_sensitive_data(record_dict)

        return record_dict

    def to_json(self, redact: bool = True) -> str:
        """
        Convert log record to JSON string.

        Args:
            redact: Whether to redact sensitive information

        Returns:
            str: JSON representation of log record
        """
        return json.dumps(self.to_dict(redact), default=str, separators=(",", ":"))


class RedactingFormatter(logging.Formatter):
    """
    Custom formatter that redacts sensitive information and outputs structured JSON.
    """

    def __init__(
        self,
        redact_patterns: Optional[Dict[str, re.Pattern]] = None,
        include_traceback: bool = True,
        redact_enabled: bool = True,
    ):
        """
        Initialize redacting formatter.

        Args:
            redact_patterns: Custom redaction patterns
            include_traceback: Whether to include tracebacks
            redact_enabled: Whether to enable redaction
        """
        super().__init__()
        self.redact_patterns = redact_patterns
        self.include_traceback = include_traceback
        self.redact_enabled = redact_enabled

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON with redaction.

        Args:
            record: Python log record

        Returns:
            str: Formatted JSON string
        """
        # Extract component from logger name
        component = record.name.split(".")[-1] if "." in record.name else record.name

        # Map Python log level to our enum
        level_mapping = {
            logging.DEBUG: LogLevel.DEBUG,
            logging.INFO: LogLevel.INFO,
            logging.WARNING: LogLevel.WARNING,
            logging.ERROR: LogLevel.ERROR,
            logging.CRITICAL: LogLevel.CRITICAL,
        }
        level = level_mapping.get(record.levelno, LogLevel.INFO)

        # Create structured log record
        log_record = LogRecord(
            level=level, message=record.getMessage(), component=component
        )

        # Extract context from record attributes
        if hasattr(record, "session_id"):
            log_record.session_id = record.session_id
        if hasattr(record, "agent_id"):
            log_record.agent_id = record.agent_id
        if hasattr(record, "swarm_id"):
            log_record.swarm_id = record.swarm_id
        if hasattr(record, "task_id"):
            log_record.task_id = record.task_id
        if hasattr(record, "duration_ms"):
            log_record.duration_ms = record.duration_ms
        if hasattr(record, "memory_mb"):
            log_record.memory_mb = record.memory_mb

        # Add custom fields from extra
        custom_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "session_id",
                "agent_id",
                "swarm_id",
                "task_id",
                "duration_ms",
                "memory_mb",
            ]:
                custom_fields[key] = value

        if custom_fields:
            log_record.fields.update(custom_fields)

        # Handle exception information
        if record.exc_info:
            log_record.error_type = record.exc_info[0].__name__
            log_record.error = str(record.exc_info[1])

            if self.include_traceback:
                log_record.traceback = "".join(
                    traceback.format_exception(*record.exc_info)
                )

        # Format as JSON
        return log_record.to_json(redact=self.redact_enabled)


class StructuredLogger:
    """
    Structured logger with automatic redaction and context tracking.
    """

    def __init__(
        self, name: str, level: LogLevel = LogLevel.INFO, redact_enabled: bool = True
    ):
        """
        Initialize structured logger.

        Args:
            name: Logger name
            level: Log level
            redact_enabled: Whether to enable redaction
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.redact_enabled = redact_enabled

        # Set up formatter if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = RedactingFormatter(redact_enabled=redact_enabled)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.setLevel(getattr(logging, level.value))

        # Context stack for automatic field inclusion
        self._context_stack: List[Dict[str, Any]] = []

    def push_context(self, **kwargs) -> None:
        """
        Push context onto stack.

        Args:
            **kwargs: Context fields to add
        """
        self._context_stack.append(kwargs)

    def pop_context(self) -> Dict[str, Any]:
        """
        Pop context from stack.

        Returns:
            Dict[str, Any]: Popped context
        """
        return self._context_stack.pop() if self._context_stack else {}

    def _get_current_context(self) -> Dict[str, Any]:
        """Get current context by merging stack."""
        context = {}
        for ctx in self._context_stack:
            context.update(ctx)
        return context

    def log(
        self,
        level: LogLevel,
        message: str,
        error: Optional[Exception] = None,
        duration_ms: Optional[float] = None,
        **fields,
    ) -> None:
        """
        Log structured message.

        Args:
            level: Log level
            message: Log message
            error: Optional exception
            duration_ms: Optional duration in milliseconds
            **fields: Additional fields
        """
        # Get current context
        context = self._get_current_context()

        # Prepare extra fields
        extra = context.copy()
        extra.update(fields)

        if duration_ms is not None:
            extra["duration_ms"] = duration_ms

        # Log with exception if provided
        exc_info = error is not None

        # Get Python log level
        python_level = getattr(logging, level.value)

        self.logger.log(python_level, message, exc_info=exc_info, extra=extra)

    def debug(self, message: str, **fields) -> None:
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, **fields)

    def info(self, message: str, **fields) -> None:
        """Log info message."""
        self.log(LogLevel.INFO, message, **fields)

    def warning(self, message: str, **fields) -> None:
        """Log warning message."""
        self.log(LogLevel.WARNING, message, **fields)

    def error(self, message: str, error: Optional[Exception] = None, **fields) -> None:
        """Log error message."""
        self.log(LogLevel.ERROR, message, error=error, **fields)

    def critical(
        self, message: str, error: Optional[Exception] = None, **fields
    ) -> None:
        """Log critical message."""
        self.log(LogLevel.CRITICAL, message, error=error, **fields)

    def activity(
        self,
        activity: str,
        component: str,
        status: str = "completed",
        duration_ms: Optional[float] = None,
        **fields,
    ) -> None:
        """
        Log activity with structured format.

        Args:
            activity: Activity name
            component: Component performing activity
            status: Activity status
            duration_ms: Duration in milliseconds
            **fields: Additional fields
        """
        message = f"{component} {activity} {status}"

        activity_fields = {"activity": activity, "activity_status": status, **fields}

        level = LogLevel.ERROR if status == "failed" else LogLevel.INFO
        self.log(level, message, duration_ms=duration_ms, **activity_fields)


# Global logger cache
_loggers: Dict[str, StructuredLogger] = {}


def setup_logging(
    level: LogLevel = LogLevel.INFO,
    log_file: Optional[Path] = None,
    redact_enabled: bool = True,
    json_format: bool = True,
) -> None:
    """
    Set up global logging configuration.

    Args:
        level: Default log level
        log_file: Optional log file path
        redact_enabled: Whether to enable redaction
        json_format: Whether to use JSON format
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.value))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set up formatter
    if json_format:
        formatter = RedactingFormatter(redact_enabled=redact_enabled)
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.info(f"Logging initialized with level {level.value}")


@lru_cache(maxsize=128)
def get_logger(name: str, redact_enabled: bool = True) -> StructuredLogger:
    """
    Get or create structured logger.

    Args:
        name: Logger name
        redact_enabled: Whether to enable redaction

    Returns:
        StructuredLogger: Logger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, redact_enabled=redact_enabled)

    return _loggers[name]


# Convenience functions for common logging patterns


def log_agent_activity(
    agent_id: str,
    activity: str,
    status: str = "completed",
    duration_ms: Optional[float] = None,
    session_id: Optional[str] = None,
    **fields,
) -> None:
    """
    Log agent activity.

    Args:
        agent_id: Agent ID
        activity: Activity name
        status: Activity status
        duration_ms: Duration in milliseconds
        session_id: Optional session ID
        **fields: Additional fields
    """
    logger = get_logger("sophia_core.agents")

    activity_fields = {"agent_id": agent_id, **fields}

    if session_id:
        activity_fields["session_id"] = session_id

    logger.activity(activity, "agent", status, duration_ms, **activity_fields)


def log_swarm_activity(
    swarm_id: str,
    activity: str,
    status: str = "completed",
    duration_ms: Optional[float] = None,
    member_count: Optional[int] = None,
    **fields,
) -> None:
    """
    Log swarm activity.

    Args:
        swarm_id: Swarm ID
        activity: Activity name
        status: Activity status
        duration_ms: Duration in milliseconds
        member_count: Number of swarm members
        **fields: Additional fields
    """
    logger = get_logger("sophia_core.swarms")

    activity_fields = {"swarm_id": swarm_id, **fields}

    if member_count is not None:
        activity_fields["member_count"] = member_count

    logger.activity(activity, "swarm", status, duration_ms, **activity_fields)


def log_tool_execution(
    tool_name: str,
    status: str = "completed",
    duration_ms: Optional[float] = None,
    agent_id: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    result: Optional[Any] = None,
    error: Optional[str] = None,
) -> None:
    """
    Log tool execution.

    Args:
        tool_name: Tool name
        status: Execution status
        duration_ms: Duration in milliseconds
        agent_id: Agent executing tool
        parameters: Tool parameters
        result: Tool result
        error: Error message if failed
    """
    logger = get_logger("sophia_core.tools")

    activity_fields = {"tool_name": tool_name}

    if agent_id:
        activity_fields["agent_id"] = agent_id
    if parameters:
        # Redact parameters that might contain sensitive info
        activity_fields["parameters"] = redact_sensitive_data(parameters)
    if result is not None:
        activity_fields["result_type"] = type(result).__name__
    if error:
        activity_fields["error"] = error

    logger.activity("tool_execution", "tool", status, duration_ms, **activity_fields)


def log_memory_operation(
    operation: str,
    memory_type: str,
    status: str = "completed",
    duration_ms: Optional[float] = None,
    entry_count: Optional[int] = None,
    agent_id: Optional[str] = None,
    **fields,
) -> None:
    """
    Log memory operation.

    Args:
        operation: Memory operation (store, retrieve, delete, etc.)
        memory_type: Type of memory (episodic, semantic, working)
        status: Operation status
        duration_ms: Duration in milliseconds
        entry_count: Number of entries affected
        agent_id: Agent performing operation
        **fields: Additional fields
    """
    logger = get_logger("sophia_core.memory")

    activity_fields = {"memory_type": memory_type, "operation": operation, **fields}

    if entry_count is not None:
        activity_fields["entry_count"] = entry_count
    if agent_id:
        activity_fields["agent_id"] = agent_id

    logger.activity(
        f"memory_{operation}", "memory", status, duration_ms, **activity_fields
    )
