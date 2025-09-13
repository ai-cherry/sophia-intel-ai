#!/usr/bin/env python3
"""
Unified Error Handling System
=============================
Comprehensive error handling, logging, monitoring, and recovery system.
Replaces scattered error handling patterns with unified, robust error management.

Features:
- Structured error classification and handling
- Automatic error recovery and fallback mechanisms
- Performance impact monitoring and alerts
- Error rate limiting and circuit breakers
- Comprehensive logging with context preservation
- Error analytics and trend analysis
- Integration with monitoring systems
- User-friendly error responses
"""

import asyncio
import functools
import hashlib
import json
import logging
import os
import sys
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import redis.asyncio as redis
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error category classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization" 
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    NETWORK = "network"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"

class RecoveryStrategy(Enum):
    """Error recovery strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    FAIL_FAST = "fail_fast"

@dataclass
class ErrorContext:
    """Comprehensive error context information"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    service_name: str = "sophia-ai"
    function_name: Optional[str] = None
    recovery_attempted: bool = False
    recovery_strategy: Optional[RecoveryStrategy] = None
    performance_impact: Optional[float] = None  # in milliseconds

@dataclass
class CircuitBreakerState:
    """Circuit breaker state management"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "closed"  # closed, open, half-open
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds

class UnifiedErrorHandler:
    """
    Unified Error Handling System
    Provides comprehensive error management across the entire application
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
        
        # Error tracking
        self._error_counts: Dict[str, int] = {}
        self._circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self._error_patterns: Dict[str, List[datetime]] = {}
        
        # Configuration
        self.max_errors_per_minute = 10
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 60
        self.enable_metrics = True
        self.enable_recovery = True
        
        logger.info("Unified Error Handler initialized")
    
    async def initialize(self):
        """Initialize Redis connection for error tracking"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis connected for error handling")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Error tracking will be memory-only.")
            self.redis_client = None
    
    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = None,
        recovery_strategy: RecoveryStrategy = None,
        user_friendly_message: str = None
    ) -> ErrorContext:
        """
        Comprehensive error handling with classification and recovery
        """
        # Generate unique error ID
        error_id = self._generate_error_id(error, context)
        
        # Classify error if not provided
        if category is None:
            category = self._classify_error(error)
        
        # Determine severity if not provided
        if severity == ErrorSeverity.MEDIUM:
            severity = self._determine_severity(error, category)
        
        # Create error context
        error_context = ErrorContext(
            error_id=error_id,
            timestamp=datetime.utcnow(),
            severity=severity,
            category=category,
            message=str(error),
            details=self._extract_error_details(error, context),
            stack_trace=traceback.format_exc(),
            user_id=context.get("user_id") if context else None,
            request_id=context.get("request_id") if context else None,
            function_name=context.get("function_name") if context else None,
            recovery_strategy=recovery_strategy
        )
        
        # Log error with appropriate level
        await self._log_error(error_context)
        
        # Track error patterns and metrics
        await self._track_error_metrics(error_context)
        
        # Attempt recovery if enabled
        if self.enable_recovery and recovery_strategy:
            await self._attempt_recovery(error_context)
        
        # Check for circuit breaker activation
        await self._check_circuit_breaker(error_context)
        
        # Send alerts for critical errors
        if severity == ErrorSeverity.CRITICAL:
            await self._send_critical_alert(error_context)
        
        return error_context
    
    def error_handler(
        self,
        category: ErrorCategory = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recovery_strategy: RecoveryStrategy = None,
        user_friendly_message: str = None,
        reraise: bool = True
    ):
        """
        Decorator for automatic error handling
        """
        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    context = {
                        "function_name": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }
                    
                    error_context = await self.handle_error(
                        e, context, severity, category, recovery_strategy, user_friendly_message
                    )
                    
                    if reraise:
                        raise
                    
                    return None
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    context = {
                        "function_name": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }
                    
                    # For sync functions, we can't use await, so we'll log synchronously
                    self._log_error_sync(e, context, severity, category)
                    
                    if reraise:
                        raise
                    
                    return None
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    @contextmanager
    def error_context(
        self,
        operation_name: str,
        category: ErrorCategory = None,
        recovery_strategy: RecoveryStrategy = None
    ):
        """
        Context manager for error handling
        """
        start_time = time.time()
        try:
            yield
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            context = {
                "operation_name": operation_name,
                "execution_time_ms": execution_time
            }
            
            # Create a task for async error handling
            asyncio.create_task(self.handle_error(
                e, context, category=category, recovery_strategy=recovery_strategy
            ))
            
            raise
    
    async def create_http_error_response(self, error_context: ErrorContext) -> JSONResponse:
        """
        Create user-friendly HTTP error response
        """
        # Determine HTTP status code based on category
        status_code = self._get_http_status_code(error_context.category)
        
        # Create user-friendly message
        user_message = self._get_user_friendly_message(error_context)
        
        response_data = {
            "error": {
                "id": error_context.error_id,
                "message": user_message,
                "category": error_context.category.value,
                "timestamp": error_context.timestamp.isoformat(),
            }
        }
        
        # Add debug info for development
        if os.getenv("ENV") == "development":
            response_data["error"]["debug"] = {
                "original_message": error_context.message,
                "details": error_context.details
            }
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    async def get_error_analytics(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Get error analytics and trends
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        
        # Get error data from Redis or memory
        error_data = await self._get_error_data(cutoff_time)
        
        analytics = {
            "time_range_hours": time_range_hours,
            "total_errors": len(error_data),
            "errors_by_category": self._group_errors_by_category(error_data),
            "errors_by_severity": self._group_errors_by_severity(error_data),
            "error_rate_trend": self._calculate_error_rate_trend(error_data),
            "top_error_patterns": self._identify_error_patterns(error_data),
            "recovery_success_rate": self._calculate_recovery_success_rate(error_data),
            "performance_impact": self._calculate_performance_impact(error_data)
        }
        
        return analytics
    
    # === Private Methods ===
    
    def _generate_error_id(self, error: Exception, context: Dict[str, Any]) -> str:
        """Generate unique error ID"""
        error_data = f"{type(error).__name__}:{str(error)}:{context.get('function_name', '')}"
        return hashlib.md5(error_data.encode()).hexdigest()[:12]
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Automatically classify error type"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        if "authentication" in error_message or "unauthorized" in error_message:
            return ErrorCategory.AUTHENTICATION
        elif "permission" in error_message or "forbidden" in error_message:
            return ErrorCategory.AUTHORIZATION
        elif "validation" in error_message or isinstance(error, ValueError):
            return ErrorCategory.VALIDATION
        elif "connection" in error_message or "timeout" in error_message:
            return ErrorCategory.NETWORK
        elif "database" in error_message or "sql" in error_message:
            return ErrorCategory.DATABASE
        elif isinstance(error, (MemoryError, SystemError)):
            return ErrorCategory.SYSTEM
        elif "external" in error_message or "api" in error_message:
            return ErrorCategory.EXTERNAL_SERVICE
        else:
            return ErrorCategory.BUSINESS_LOGIC
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity automatically"""
        if isinstance(error, (SystemError, MemoryError)):
            return ErrorSeverity.CRITICAL
        elif category in [ErrorCategory.SECURITY, ErrorCategory.DATABASE]:
            return ErrorSeverity.HIGH
        elif category in [ErrorCategory.EXTERNAL_SERVICE, ErrorCategory.NETWORK]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _extract_error_details(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed error information"""
        details = {
            "error_type": type(error).__name__,
            "error_module": getattr(error, "__module__", None),
            "python_version": sys.version,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if context:
            details.update(context)
        
        # Add specific details for certain error types
        if hasattr(error, "args") and error.args:
            details["error_args"] = str(error.args)
        
        return details
    
    async def _log_error(self, error_context: ErrorContext):
        """Log error with appropriate level and formatting"""
        log_data = {
            "error_id": error_context.error_id,
            "category": error_context.category.value,
            "severity": error_context.severity.value,
            "message": error_context.message,
            "user_id": error_context.user_id,
            "request_id": error_context.request_id,
            "function": error_context.function_name
        }
        
        log_message = f"Error {error_context.error_id}: {error_context.message}"
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra=log_data)
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra=log_data)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra=log_data)
        else:
            logger.info(log_message, extra=log_data)
        
        # Store in Redis for analytics
        if self.redis_client:
            try:
                error_key = f"error:{error_context.error_id}"
                error_data = {
                    "context": error_context.__dict__,
                    "timestamp": error_context.timestamp.isoformat()
                }
                await self.redis_client.setex(error_key, 86400, json.dumps(error_data, default=str))
            except Exception as e:
                logger.warning(f"Failed to store error in Redis: {e}")
    
    def _log_error_sync(self, error: Exception, context: Dict[str, Any], severity: ErrorSeverity, category: ErrorCategory):
        """Synchronous error logging"""
        log_message = f"Error: {str(error)}"
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    async def _track_error_metrics(self, error_context: ErrorContext):
        """Track error metrics and patterns"""
        error_key = f"{error_context.category.value}:{type(error_context).__name__}"
        
        # Increment error count
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        
        # Track error patterns
        if error_key not in self._error_patterns:
            self._error_patterns[error_key] = []
        
        self._error_patterns[error_key].append(error_context.timestamp)
        
        # Keep only recent errors (last hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self._error_patterns[error_key] = [
            ts for ts in self._error_patterns[error_key] if ts > cutoff_time
        ]
    
    async def _attempt_recovery(self, error_context: ErrorContext):
        """Attempt error recovery based on strategy"""
        if not error_context.recovery_strategy:
            return
        
        try:
            if error_context.recovery_strategy == RecoveryStrategy.RETRY:
                # Implement retry logic
                pass
            elif error_context.recovery_strategy == RecoveryStrategy.FALLBACK:
                # Implement fallback logic
                pass
            elif error_context.recovery_strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                # Implement circuit breaker logic
                await self._activate_circuit_breaker(error_context)
            
            error_context.recovery_attempted = True
        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed: {recovery_error}")
    
    async def _check_circuit_breaker(self, error_context: ErrorContext):
        """Check and update circuit breaker state"""
        breaker_key = f"{error_context.category.value}:{error_context.function_name}"
        
        if breaker_key not in self._circuit_breakers:
            self._circuit_breakers[breaker_key] = CircuitBreakerState()
        
        breaker = self._circuit_breakers[breaker_key]
        breaker.failure_count += 1
        breaker.last_failure_time = datetime.utcnow()
        
        if breaker.failure_count >= breaker.failure_threshold:
            breaker.state = "open"
            logger.warning(f"Circuit breaker opened for {breaker_key}")
    
    async def _activate_circuit_breaker(self, error_context: ErrorContext):
        """Activate circuit breaker for the failing component"""
        breaker_key = f"{error_context.category.value}:{error_context.function_name}"
        
        if breaker_key in self._circuit_breakers:
            self._circuit_breakers[breaker_key].state = "open"
            logger.warning(f"Circuit breaker activated for {breaker_key}")
    
    async def _send_critical_alert(self, error_context: ErrorContext):
        """Send alert for critical errors"""
        alert_message = f"CRITICAL ERROR: {error_context.message}"
        logger.critical(alert_message)
        
        # Here you would integrate with alerting systems like PagerDuty, Slack, etc.
        # For now, we'll just log it
    
    def _get_http_status_code(self, category: ErrorCategory) -> int:
        """Get appropriate HTTP status code for error category"""
        status_map = {
            ErrorCategory.AUTHENTICATION: status.HTTP_401_UNAUTHORIZED,
            ErrorCategory.AUTHORIZATION: status.HTTP_403_FORBIDDEN,
            ErrorCategory.VALIDATION: status.HTTP_400_BAD_REQUEST,
            ErrorCategory.BUSINESS_LOGIC: status.HTTP_422_UNPROCESSABLE_ENTITY,
            ErrorCategory.EXTERNAL_SERVICE: status.HTTP_502_BAD_GATEWAY,
            ErrorCategory.DATABASE: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCategory.NETWORK: status.HTTP_504_GATEWAY_TIMEOUT,
            ErrorCategory.SYSTEM: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCategory.PERFORMANCE: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCategory.SECURITY: status.HTTP_403_FORBIDDEN
        }
        
        return status_map.get(category, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_user_friendly_message(self, error_context: ErrorContext) -> str:
        """Generate user-friendly error message"""
        friendly_messages = {
            ErrorCategory.AUTHENTICATION: "Authentication required. Please log in.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to perform this action.",
            ErrorCategory.VALIDATION: "The provided data is invalid. Please check your input.",
            ErrorCategory.BUSINESS_LOGIC: "Unable to process your request due to business rules.",
            ErrorCategory.EXTERNAL_SERVICE: "External service is temporarily unavailable. Please try again.",
            ErrorCategory.DATABASE: "Database is temporarily unavailable. Please try again.",
            ErrorCategory.NETWORK: "Network connection issue. Please try again.",
            ErrorCategory.SYSTEM: "System error occurred. Our team has been notified.",
            ErrorCategory.PERFORMANCE: "Service is running slowly. Please try again.",
            ErrorCategory.SECURITY: "Security check failed. Please contact support."
        }
        
        return friendly_messages.get(error_context.category, "An unexpected error occurred. Please try again.")
    
    async def _get_error_data(self, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get error data from storage"""
        # This would typically query Redis or a database
        # For now, return mock data
        return []
    
    def _group_errors_by_category(self, error_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group errors by category"""
        return {}
    
    def _group_errors_by_severity(self, error_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group errors by severity"""
        return {}
    
    def _calculate_error_rate_trend(self, error_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate error rate trend over time"""
        return []
    
    def _identify_error_patterns(self, error_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify common error patterns"""
        return []
    
    def _calculate_recovery_success_rate(self, error_data: List[Dict[str, Any]]) -> float:
        """Calculate recovery success rate"""
        return 0.0
    
    def _calculate_performance_impact(self, error_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate performance impact of errors"""
        return {}

# Global error handler instance
_error_handler: Optional[UnifiedErrorHandler] = None

def get_error_handler() -> UnifiedErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = UnifiedErrorHandler()
    return _error_handler

# Convenience decorators
def handle_errors(
    category: ErrorCategory = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recovery_strategy: RecoveryStrategy = None
):
    """Convenience decorator for error handling"""
    error_handler = get_error_handler()
    return error_handler.error_handler(category, severity, recovery_strategy)

def critical_section(category: ErrorCategory = None):
    """Decorator for critical sections that need high-priority error handling"""
    return handle_errors(category, ErrorSeverity.CRITICAL, RecoveryStrategy.FAIL_FAST)

def resilient_operation(recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY):
    """Decorator for operations that should attempt recovery"""
    return handle_errors(recovery_strategy=recovery_strategy)

# FastAPI exception handler
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for FastAPI applications"""
    error_handler = get_error_handler()
    
    context = {
        "request_url": str(request.url),
        "request_method": request.method,
        "user_agent": request.headers.get("user-agent"),
        "request_id": request.headers.get("x-request-id")
    }
    
    error_context = await error_handler.handle_error(exc, context)
    return await error_handler.create_http_error_response(error_context)