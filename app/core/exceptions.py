"""
Custom Exceptions and Guardrail Reporting

This module provides structured exception handling and guardrail violation reporting
to improve error propagation and troubleshooting across the agent framework.
"""

import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification"""
    CONFIGURATION = "configuration"
    REASONING = "reasoning"
    TOOL_EXECUTION = "tool_execution"
    MEMORY = "memory"
    COMMUNICATION = "communication"
    SECURITY = "security"
    RATE_LIMIT = "rate_limit"
    MODEL = "model"
    VALIDATION = "validation"
    SYSTEM = "system"


class GuardrailType(str, Enum):
    """Types of guardrail violations"""
    INPUT_VALIDATION = "input_validation"
    OUTPUT_VALIDATION = "output_validation"
    CONTENT_FILTER = "content_filter"
    RATE_LIMIT = "rate_limit"
    COST_LIMIT = "cost_limit"
    SECURITY_POLICY = "security_policy"
    DATA_PRIVACY = "data_privacy"
    ETHICAL_GUIDELINES = "ethical_guidelines"


class ErrorContext(BaseModel):
    """Context information for errors"""
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: Optional[str] = None
    service_name: Optional[str] = None
    operation: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GuardrailViolation(BaseModel):
    """Detailed guardrail violation report"""
    violation_type: GuardrailType
    severity: ErrorSeverity
    description: str
    violated_rule: Optional[str] = None
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    suggested_action: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Optional[ErrorContext] = None


# Base Exception Classes

class SophiaBaseException(Exception):
    """Base exception for all Sophia AI errors"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.cause = cause
        self.traceback = traceback.format_exc()
        
        # Log the error
        self._log_error()
    
    def _log_error(self):
        """Log the error with appropriate level"""
        log_message = f"{self.category}: {self.message}"
        
        if self.context:
            log_message += f" | Context: {self.context.dict()}"
        
        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif self.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for serialization"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.category,
            "severity": self.severity,
            "context": self.context.dict() if self.context else None,
            "cause": str(self.cause) if self.cause else None,
            "traceback": self.traceback
        }


# Configuration Errors

class ConfigurationError(SophiaBaseException):
    """Configuration-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            **kwargs
        )


class InvalidConfigError(ConfigurationError):
    """Invalid configuration values"""
    pass


class MissingConfigError(ConfigurationError):
    """Missing required configuration"""
    pass


# Reasoning Errors

class ReasoningError(SophiaBaseException):
    """Reasoning engine errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.REASONING,
            **kwargs
        )


class MaxStepsExceededError(ReasoningError):
    """Maximum reasoning steps exceeded"""
    
    def __init__(self, max_steps: int, **kwargs):
        super().__init__(
            message=f"Maximum reasoning steps ({max_steps}) exceeded",
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class ReasoningLoopError(ReasoningError):
    """Detected infinite loop in reasoning"""
    
    def __init__(self, **kwargs):
        super().__init__(
            message="Infinite loop detected in reasoning process",
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


# Tool Execution Errors

class ToolExecutionError(SophiaBaseException):
    """Tool execution errors"""
    
    def __init__(self, tool_name: str, message: str, **kwargs):
        super().__init__(
            message=f"Tool '{tool_name}' execution failed: {message}",
            category=ErrorCategory.TOOL_EXECUTION,
            **kwargs
        )
        self.tool_name = tool_name


class ToolNotFoundError(ToolExecutionError):
    """Tool not found in registry"""
    
    def __init__(self, tool_name: str, **kwargs):
        super().__init__(
            tool_name=tool_name,
            message=f"Tool '{tool_name}' not found in registry",
            **kwargs
        )


class ToolValidationError(ToolExecutionError):
    """Tool parameter validation failed"""
    
    def __init__(self, tool_name: str, validation_error: str, **kwargs):
        super().__init__(
            tool_name=tool_name,
            message=f"Validation failed: {validation_error}",
            **kwargs
        )


class ToolTimeoutError(ToolExecutionError):
    """Tool execution timeout"""
    
    def __init__(self, tool_name: str, timeout: int, **kwargs):
        super().__init__(
            tool_name=tool_name,
            message=f"Execution exceeded timeout of {timeout}s",
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


# Model Errors

class ModelError(SophiaBaseException):
    """Model-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.MODEL,
            **kwargs
        )


class ModelUnavailableError(ModelError):
    """Model service unavailable"""
    
    def __init__(self, model_name: str, **kwargs):
        super().__init__(
            message=f"Model '{model_name}' is unavailable",
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class ModelQuotaExceededError(ModelError):
    """Model quota or rate limit exceeded"""
    
    def __init__(self, model_name: str, **kwargs):
        super().__init__(
            message=f"Quota exceeded for model '{model_name}'",
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


# Security Errors

class SecurityError(SophiaBaseException):
    """Security-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            **kwargs
        )


class AuthenticationError(SecurityError):
    """Authentication failure"""
    pass


class AuthorizationError(SecurityError):
    """Authorization failure"""
    pass


class SecretExposureError(SecurityError):
    """Potential secret or key exposure detected"""
    
    def __init__(self, **kwargs):
        super().__init__(
            message="Potential secret exposure detected",
            **kwargs
        )


# Guardrail Errors

class GuardrailError(SophiaBaseException):
    """Guardrail violation errors"""
    
    def __init__(
        self,
        violation: GuardrailViolation,
        **kwargs
    ):
        super().__init__(
            message=f"Guardrail violation: {violation.description}",
            category=ErrorCategory.VALIDATION,
            severity=violation.severity,
            **kwargs
        )
        self.violation = violation


class InputGuardrailError(GuardrailError):
    """Input validation guardrail violation"""
    pass


class OutputGuardrailError(GuardrailError):
    """Output validation guardrail violation"""
    pass


class ContentFilterError(GuardrailError):
    """Content filter guardrail violation"""
    pass


class CostLimitError(GuardrailError):
    """Cost limit guardrail violation"""
    
    def __init__(self, current_cost: float, limit: float, **kwargs):
        violation = GuardrailViolation(
            violation_type=GuardrailType.COST_LIMIT,
            severity=ErrorSeverity.HIGH,
            description=f"Cost limit exceeded: ${current_cost:.2f} > ${limit:.2f}",
            suggested_action="Reduce request frequency or optimize prompts"
        )
        super().__init__(violation=violation, **kwargs)


# Rate Limiting Errors

class RateLimitError(SophiaBaseException):
    """Rate limit exceeded"""
    
    def __init__(
        self,
        limit_type: str,
        current_rate: int,
        max_rate: int,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        message = f"Rate limit exceeded: {current_rate}/{max_rate} {limit_type}"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        
        super().__init__(
            message=message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.retry_after = retry_after


# Error Handler and Reporter

class ErrorHandler:
    """Centralized error handling and reporting"""
    
    def __init__(self):
        self.error_history: list[SophiaBaseException] = []
        self.guardrail_violations: list[GuardrailViolation] = []
        self.error_callbacks: list[Callable] = []
    
    def handle_error(self, error: Exception, context: Optional[ErrorContext] = None) -> SophiaBaseException:
        """Handle and wrap generic exceptions"""
        if isinstance(error, SophiaBaseException):
            sophia_error = error
        else:
            # Wrap in base exception
            sophia_error = SophiaBaseException(
                message=str(error),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                context=context,
                cause=error
            )
        
        # Record error
        self.error_history.append(sophia_error)
        
        # Execute callbacks
        for callback in self.error_callbacks:
            try:
                callback(sophia_error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
        
        return sophia_error
    
    def report_guardrail_violation(
        self,
        violation: GuardrailViolation,
        raise_error: bool = True
    ) -> Optional[GuardrailError]:
        """Report a guardrail violation"""
        # Record violation
        self.guardrail_violations.append(violation)
        
        # Log violation
        logger.warning(f"Guardrail violation: {violation.dict()}")
        
        # Raise error if requested
        if raise_error:
            error = GuardrailError(violation=violation)
            self.error_history.append(error)
            raise error
        
        return None
    
    def add_error_callback(self, callback: Callable):
        """Add callback for error notifications"""
        self.error_callbacks.append(callback)
    
    def get_error_statistics(self) -> dict:
        """Get error statistics"""
        stats = {
            "total_errors": len(self.error_history),
            "errors_by_category": {},
            "errors_by_severity": {},
            "guardrail_violations": len(self.guardrail_violations),
            "violations_by_type": {}
        }
        
        # Count by category
        for error in self.error_history:
            category = error.category
            stats["errors_by_category"][category] = stats["errors_by_category"].get(category, 0) + 1
            
            severity = error.severity
            stats["errors_by_severity"][severity] = stats["errors_by_severity"].get(severity, 0) + 1
        
        # Count violations
        for violation in self.guardrail_violations:
            vtype = violation.violation_type
            stats["violations_by_type"][vtype] = stats["violations_by_type"].get(vtype, 0) + 1
        
        return stats
    
    def clear_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.guardrail_violations.clear()


# Global error handler
global_error_handler = ErrorHandler()


# Decorator for error handling
def handle_errors(
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    reraise: bool = True
):
    """Decorator for automatic error handling"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    operation=func.__name__,
                    metadata={"args": str(args), "kwargs": str(kwargs)}
                )
                error = global_error_handler.handle_error(e, context)
                if reraise:
                    raise error
                return None
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    operation=func.__name__,
                    metadata={"args": str(args), "kwargs": str(kwargs)}
                )
                error = global_error_handler.handle_error(e, context)
                if reraise:
                    raise error
                return None
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator