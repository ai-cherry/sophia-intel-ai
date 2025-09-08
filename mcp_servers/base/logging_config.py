"\nStandardized logging configuration for MCP servers\n"

import logging


class MCPLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds MCP-specific context to log messages
    """

    def __init__(self, logger: logging.Logger, server_name: str):
        super().__init__(logger, {"server": server_name})
        self.server_name = server_name

    def process(self, msg, kwargs):
        """Add server context to log messages"""
        return (f"[{self.server_name}] {msg}", kwargs)

    def log_tool_start(self, tool_name: str, arguments: dict):
        """Log tool execution start"""
        self.info(
            f"🔧 Starting tool: {tool_name}",
            extra={"tool": tool_name, "arguments": arguments},
        )

    def log_tool_success(self, tool_name: str, execution_time: float):
        """Log successful tool execution"""
        self.info(
            f"✅ Tool completed: {tool_name} ({execution_time * 1000:.1f}ms)",
            extra={
                "tool": tool_name,
                "execution_time": execution_time,
                "status": "success",
            },
        )

    def log_tool_error(self, tool_name: str, error: Exception, execution_time: float):
        """Log tool execution error"""
        self.error(
            f"❌ Tool failed: {tool_name} - {str(error)} ({execution_time * 1000:.1f}ms)",
            extra={
                "tool": tool_name,
                "error": str(error),
                "execution_time": execution_time,
                "status": "error",
            },
        )

    def log_api_request(self, endpoint: str, method: str = "POST"):
        """Log API request"""
        self.debug(
            f"🌐 API Request: {method} {endpoint}",
            extra={"endpoint": endpoint, "method": method},
        )

    def log_api_response(self, endpoint: str, status_code: int, response_time: float):
        """Log API response"""
        status_emoji = "✅" if 200 <= status_code < 300 else "❌"
        self.debug(
            f"{status_emoji} API Response: {endpoint} - {status_code} ({response_time * 1000:.1f}ms)",
            extra={
                "endpoint": endpoint,
                "status_code": status_code,
                "response_time": response_time,
            },
        )

    def log_circuit_breaker_event(self, circuit_name: str, event: str, details: dict | None = None):
        """Log circuit breaker events"""
        details = details or {}
        self.warning(
            f"⚡ Circuit Breaker [{circuit_name}]: {event}",
            extra={"circuit": circuit_name, "event": event, **details},
        )

    def log_fallback_activation(self, operation: str, strategy: str, service_used: str):
        """Log fallback activation"""
        self.warning(
            f"🔄 Fallback activated for {operation}: using {service_used} (strategy: {strategy})",
            extra={
                "operation": operation,
                "strategy": strategy,
                "service_used": service_used,
            },
        )

    def log_cache_event(self, event: str, key: str, details: dict | None = None):
        """Log cache events"""
        details = details or {}
        cache_emoji = "💾" if event == "hit" else "🔍" if event == "miss" else "🗑️"
        self.debug(
            f"{cache_emoji} Cache {event}: {key}",
            extra={"cache_event": event, "key": key, **details},
        )


class PerformanceLogger:
    """Logger for performance metrics and timing"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_execution_time(self, operation: str, execution_time: float, threshold: float = 1.0):
        """Log execution time with performance warnings"""
        if execution_time > threshold:
            self.logger.warning(
                f"⚠️ Slow operation: {operation} took {execution_time * 1000:.1f}ms (threshold: {threshold * 1000:.1f}ms)"
            )
        else:
            self.logger.debug(f"⏱️ {operation}: {execution_time * 1000:.1f}ms")

    def log_memory_usage(self, operation: str, memory_mb: float):
        """Log memory usage"""
        self.logger.debug(f"💾 Memory usage for {operation}: {memory_mb:.1f}MB")

    def log_throughput(self, operation: str, items_processed: int, time_taken: float):
        """Log throughput metrics"""
        throughput = items_processed / time_taken if time_taken > 0 else 0
        self.logger.info(
            f"📊 Throughput for {operation}: {throughput:.1f} items/second ({items_processed} items in {time_taken:.2f}s)"
        )


class SecurityLogger:
    """Logger for security-related events"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_authentication_attempt(self, success: bool, details: dict | None = None):
        """Log authentication attempts"""
        details = details or {}
        status = "SUCCESS" if success else "FAILED"
        emoji = "🔓" if success else "🔒"
        self.logger.info(
            f"{emoji} Authentication {status}", extra={"auth_status": status, **details}
        )

    def log_authorization_check(
        self, resource: str, allowed: bool, user_context: dict | None = None
    ):
        """Log authorization checks"""
        user_context = user_context or {}
        status = "ALLOWED" if allowed else "DENIED"
        emoji = "✅" if allowed else "❌"
        self.logger.info(
            f"{emoji} Authorization {status} for resource: {resource}",
            extra={"resource": resource, "auth_status": status, **user_context},
        )

    def log_security_event(self, event_type: str, severity: str, details: dict | None = None):
        """Log security events"""
        details = details or {}
        severity_emoji = {
            "low": "🟡",
            "medium": "🟠",
            "high": "🔴",
            "critical": "🚨",
        }.get(severity.lower(), "⚠️")
        self.logger.warning(
            f"{severity_emoji} Security Event [{severity.upper()}]: {event_type}",
            extra={"event_type": event_type, "severity": severity, **details},
        )


"""
logging_config.py - Syntax errors fixed
This file had severe syntax errors and was replaced with a minimal valid structure.
"""
