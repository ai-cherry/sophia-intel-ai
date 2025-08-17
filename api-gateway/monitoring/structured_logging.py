"""
Structured logging configuration for SOPHIA Intel
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
import structlog
import os

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        # Add user ID if available
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_structured_logging():
    """
    Set up structured logging for the application
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    # Configure specific loggers
    loggers_to_configure = [
        "sophia_intel",
        "orchestrator",
        "agents",
        "api",
        "monitoring"
    ]
    
    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level))
        logger.propagate = True

def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance
    """
    return structlog.get_logger(name)

class LoggerMixin:
    """
    Mixin class to add structured logging to any class
    """
    
    @property
    def logger(self) -> structlog.BoundLogger:
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
    
    def log_info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, error: Exception = None, **kwargs):
        """Log error message with context"""
        if error:
            kwargs['error'] = str(error)
            kwargs['error_type'] = type(error).__name__
        self.logger.error(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.debug(message, **kwargs)

def log_request_start(request_id: str, method: str, path: str, user_id: str = None):
    """
    Log the start of a request
    """
    logger = get_logger("api.request")
    logger.info(
        "Request started",
        request_id=request_id,
        method=method,
        path=path,
        user_id=user_id
    )

def log_request_end(request_id: str, status_code: int, duration: float):
    """
    Log the end of a request
    """
    logger = get_logger("api.request")
    logger.info(
        "Request completed",
        request_id=request_id,
        status_code=status_code,
        duration_ms=round(duration * 1000, 2)
    )

def log_orchestrator_task(task_id: str, task_type: str, status: str, duration: float = None, **kwargs):
    """
    Log orchestrator task events
    """
    logger = get_logger("orchestrator.task")
    log_data = {
        "task_id": task_id,
        "task_type": task_type,
        "status": status,
        **kwargs
    }
    
    if duration is not None:
        log_data["duration_ms"] = round(duration * 1000, 2)
    
    logger.info(f"Orchestrator task {status}", **log_data)

def log_ai_model_request(model: str, prompt_length: int, response_length: int = None, duration: float = None, **kwargs):
    """
    Log AI model requests
    """
    logger = get_logger("ai.model")
    log_data = {
        "model": model,
        "prompt_length": prompt_length,
        **kwargs
    }
    
    if response_length is not None:
        log_data["response_length"] = response_length
    
    if duration is not None:
        log_data["duration_ms"] = round(duration * 1000, 2)
    
    logger.info("AI model request", **log_data)

def log_security_event(event_type: str, severity: str, details: Dict[str, Any]):
    """
    Log security-related events
    """
    logger = get_logger("security")
    logger.warning(
        f"Security event: {event_type}",
        event_type=event_type,
        severity=severity,
        **details
    )

