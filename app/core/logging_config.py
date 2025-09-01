"""
Centralized Logging Configuration for Sophia Intel AI
Provides consistent logging across all modules with structured output.
"""

import logging
import logging.config
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import traceback

from app.core.config import settings

# ============================================
# Custom Formatters
# ============================================

class StructuredFormatter(logging.Formatter):
    """JSON structured logging formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
        if hasattr(record, 'trace_id'):
            log_obj['trace_id'] = record.trace_id
        if hasattr(record, 'team_id'):
            log_obj['team_id'] = record.team_id
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_obj)

class ColoredFormatter(logging.Formatter):
    """Colored console formatter for development."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console output."""
        if settings.environment == "development":
            levelname = record.levelname
            record.levelname = f"{self.COLORS.get(levelname, '')}{levelname}{self.COLORS['RESET']}"
            record.msg = f"{self.COLORS.get(levelname, '')}{record.msg}{self.COLORS['RESET']}"
        
        return super().format(record)

# ============================================
# Custom Filters
# ============================================

class RequestIdFilter(logging.Filter):
    """Add request ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request context to record."""
        # Get request ID from context (would be set by middleware)
        import contextvars
        request_id_var = contextvars.ContextVar('request_id', default='no-request')
        record.request_id = request_id_var.get()
        return True

class SensitiveDataFilter(logging.Filter):
    """Filter out sensitive data from logs."""
    
    SENSITIVE_KEYS = [
        'password', 'token', 'api_key', 'secret', 'authorization',
        'credit_card', 'ssn', 'email', 'phone'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive information."""
        message = record.getMessage()
        
        # Redact sensitive keys in message
        for key in self.SENSITIVE_KEYS:
            if key in message.lower():
                # Simple redaction - could be more sophisticated
                import re
                pattern = rf'{key}["\']?\s*[:=]\s*["\']?[\w\-\.]+'
                message = re.sub(pattern, f'{key}=***REDACTED***', message, flags=re.IGNORECASE)
        
        record.msg = message
        record.args = ()  # Clear args to prevent re-formatting
        
        return True

# ============================================
# Logging Configuration
# ============================================

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration dictionary."""
    
    # Ensure logs directory exists
    logs_dir = Path(settings.logs_dir)
    logs_dir.mkdir(exist_ok=True)
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        
        "formatters": {
            "structured": {
                "()": StructuredFormatter
            },
            "colored": {
                "()": ColoredFormatter,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        
        "filters": {
            "request_id": {
                "()": RequestIdFilter
            },
            "sensitive_data": {
                "()": SensitiveDataFilter
            }
        },
        
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "colored" if settings.environment == "development" else "simple",
                "filters": ["request_id", "sensitive_data"],
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "structured",
                "filters": ["request_id", "sensitive_data"],
                "filename": str(logs_dir / "sophia_intel.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "structured",
                "filters": ["request_id"],
                "filename": str(logs_dir / "errors.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        
        "loggers": {
            # App loggers
            "app": {
                "level": settings.log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "app.api": {
                "level": settings.log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "app.swarms": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            "app.memory": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            "app.tasks": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            
            # Third-party loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "openai": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        },
        
        "root": {
            "level": settings.log_level,
            "handlers": ["console", "file"]
        }
    }
    
    # Add Sentry handler if configured
    if hasattr(settings, 'sentry_dsn') and settings.sentry_dsn:
        config["handlers"]["sentry"] = {
            "class": "sentry_sdk.integrations.logging.SentryHandler",
            "level": "ERROR"
        }
        for logger in config["loggers"].values():
            if "error_file" in logger.get("handlers", []):
                logger["handlers"].append("sentry")
    
    return config

# ============================================
# Logger Factory
# ============================================

class LoggerFactory:
    """Factory for creating configured loggers."""
    
    _configured = False
    
    @classmethod
    def configure(cls, config: Optional[Dict[str, Any]] = None) -> None:
        """Configure logging system."""
        if cls._configured:
            return
        
        if config is None:
            config = get_logging_config()
        
        logging.config.dictConfig(config)
        cls._configured = True
        
        # Log configuration complete
        logger = logging.getLogger(__name__)
        logger.info(
            "Logging configured",
            extra={
                "environment": settings.environment,
                "log_level": settings.log_level,
                "logs_dir": str(settings.logs_dir)
            }
        )
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a configured logger."""
        if not cls._configured:
            cls.configure()
        
        return logging.getLogger(name)

# ============================================
# Context Managers
# ============================================

class LogContext:
    """Context manager for adding context to logs."""
    
    def __init__(self, **kwargs):
        """Initialize with context values."""
        self.context = kwargs
        self.token = None
    
    def __enter__(self):
        """Set context variables."""
        import contextvars
        
        # Store context in contextvars
        for key, value in self.context.items():
            var = contextvars.ContextVar(key, default=None)
            self.token = var.set(value)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clear context variables."""
        # Context vars are automatically cleaned up

# ============================================
# Utility Functions
# ============================================

def log_function_call(logger: logging.Logger):
    """Decorator to log function calls."""
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Calling {func.__name__}",
                extra={
                    "function": func.__name__,
                    "args": str(args)[:100],  # Truncate long args
                    "kwargs": str(kwargs)[:100]
                }
            )
            
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    f"Completed {func.__name__}",
                    extra={"function": func.__name__}
                )
                return result
            except Exception as e:
                logger.error(
                    f"Error in {func.__name__}: {e}",
                    extra={"function": func.__name__},
                    exc_info=True
                )
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger.debug(
                f"Calling async {func.__name__}",
                extra={
                    "function": func.__name__,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                logger.debug(
                    f"Completed async {func.__name__}",
                    extra={"function": func.__name__}
                )
                return result
            except Exception as e:
                logger.error(
                    f"Error in async {func.__name__}: {e}",
                    extra={"function": func.__name__},
                    exc_info=True
                )
                raise
        
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    
    return decorator

def setup_logging():
    """Setup logging for the application."""
    LoggerFactory.configure()
    
    # Set third-party log levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logger = LoggerFactory.get_logger(__name__)
    logger.info("Sophia Intel AI logging initialized")

# ============================================
# Export
# ============================================

__all__ = [
    "LoggerFactory",
    "LogContext",
    "setup_logging",
    "log_function_call",
    "StructuredFormatter",
    "ColoredFormatter",
    "RequestIdFilter",
    "SensitiveDataFilter"
]