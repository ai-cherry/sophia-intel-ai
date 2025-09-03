"""
Structured Logging with Correlation IDs
Provides JSON-formatted logging with distributed tracing support
"""
from typing import Optional

import json
import logging
import sys
import traceback
import uuid
from contextvars import ContextVar
from datetime import datetime
from functools import wraps

# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
session_id_var: ContextVar[str] = ContextVar('session_id', default='')

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_var.get() or str(uuid.uuid4()),
            "request_id": request_id_var.get(),
            "session_id": session_id_var.get(),
            "service": "ai-orchestra",
            "environment": self._get_environment(),
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
            "process_name": record.processName,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Add component-specific fields
        if hasattr(record, 'component'):
            log_data['component'] = record.component

        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation

        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms

        return json.dumps(log_data)

    def _get_environment(self) -> str:
        """Get current environment"""
        import os
        return os.getenv('ENVIRONMENT', 'development')

class StructuredLogger:
    """
    Structured logger with correlation ID support
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize structured logger
        
        Args:
            name: Logger name
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Remove existing handlers
        self.logger.handlers = []

        # Create console handler with structured formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)

        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False

    def with_context(
        self,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Set logging context
        
        Args:
            correlation_id: Correlation ID for distributed tracing
            request_id: Request ID
            session_id: Session ID
        """
        if correlation_id:
            correlation_id_var.set(correlation_id)
        if request_id:
            request_id_var.set(request_id)
        if session_id:
            session_id_var.set(session_id)
        return self

    def _log(self, level: int, message: str, **kwargs):
        """Internal log method"""
        extra_fields = kwargs.pop('extra', {})

        # Add component and operation if provided
        component = kwargs.pop('component', None)
        operation = kwargs.pop('operation', None)
        duration_ms = kwargs.pop('duration_ms', None)

        extra = {'extra_fields': extra_fields}
        if component:
            extra['component'] = component
        if operation:
            extra['operation'] = operation
        if duration_ms is not None:
            extra['duration_ms'] = duration_ms

        self.logger.log(level, message, extra=extra, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)

    def log_operation(
        self,
        operation: str,
        component: str,
        start_time: float,
        success: bool = True,
        **kwargs
    ):
        """
        Log an operation with timing
        
        Args:
            operation: Operation name
            component: Component name
            start_time: Operation start time
            success: Whether operation succeeded
            **kwargs: Additional fields
        """
        import time
        duration_ms = (time.time() - start_time) * 1000

        level = logging.INFO if success else logging.ERROR
        message = f"{operation} {'completed' if success else 'failed'}"

        self._log(
            level,
            message,
            component=component,
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            extra=kwargs
        )

def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)

# Correlation ID middleware for FastAPI
def correlation_id_middleware(func):
    """Decorator to inject correlation ID"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Generate or extract correlation ID
        correlation_id = kwargs.get('correlation_id') or str(uuid.uuid4())
        correlation_id_var.set(correlation_id)

        # Call the wrapped function
        result = await func(*args, **kwargs)

        return result
    return wrapper

# Request logging middleware
class RequestLoggingMiddleware:
    """Middleware for request/response logging"""

    def __init__(self, app, logger: StructuredLogger):
        self.app = app
        self.logger = logger

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Generate correlation ID
            correlation_id = str(uuid.uuid4())
            correlation_id_var.set(correlation_id)

            # Log request
            self.logger.info(
                "Request received",
                component="middleware",
                operation="request",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "query_string": scope["query_string"].decode(),
                    "headers": dict(scope["headers"])
                }
            )

            # Track response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    self.logger.info(
                        "Response sent",
                        component="middleware",
                        operation="response",
                        extra={
                            "status": message["status"],
                            "headers": dict(message.get("headers", []))
                        }
                    )
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

# Performance logging decorator
def log_performance(component: str, operation: str):
    """Decorator to log function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import time
            logger = get_logger(func.__module__)
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                logger.log_operation(
                    operation=operation,
                    component=component,
                    start_time=start_time,
                    success=True
                )
                return result
            except Exception as e:
                logger.log_operation(
                    operation=operation,
                    component=component,
                    start_time=start_time,
                    success=False,
                    error=str(e)
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            logger = get_logger(func.__module__)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                logger.log_operation(
                    operation=operation,
                    component=component,
                    start_time=start_time,
                    success=True
                )
                return result
            except Exception as e:
                logger.log_operation(
                    operation=operation,
                    component=component,
                    start_time=start_time,
                    success=False,
                    error=str(e)
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# Export
__all__ = [
    'StructuredLogger',
    'StructuredFormatter',
    'get_logger',
    'correlation_id_middleware',
    'RequestLoggingMiddleware',
    'log_performance',
    'correlation_id_var',
    'request_id_var',
    'session_id_var'
]
