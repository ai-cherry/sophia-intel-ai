"\nStandardized error handling for MCP servers\n"

import logging
import traceback
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base exception for MCP server errors"""

    def __init__(
        self,
        message: str,
        error_code: str = "MCP_ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for JSON serialization"""
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class MCPValidationError(MCPError):
    """Error for input validation failures"""

    def __init__(self, message: str, field: str | None = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = str(value)
        super().__init__(message, "VALIDATION_ERROR", details)


class MCPTimeoutError(MCPError):
    """Error for operation timeouts"""

    def __init__(self, message: str, timeout_seconds: float):
        details = {"timeout_seconds": timeout_seconds}
        super().__init__(message, "TIMEOUT_ERROR", details)


class MCPAPIError(MCPError):
    """Error for external API failures"""

    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        details = {"api_name": api_name}
        if status_code:
            details["status_code"] = str(status_code)
        if response_body:
            details["response_body"] = response_body[:500]
        super().__init__(message, "API_ERROR", details)


class MCPCircuitBreakerError(MCPError):
    """Error when circuit breaker is open"""

    def __init__(self, circuit_name: str, last_failure_time: float | None = None):
        message = f"Circuit breaker '{circuit_name}' is open"
        details = {"circuit_name": circuit_name}
        if last_failure_time:
            details["last_failure_time"] = str(last_failure_time)
        super().__init__(message, "CIRCUIT_BREAKER_OPEN", details)


class MCPConfigurationError(MCPError):
    """Error for configuration issues"""

    def __init__(self, message: str, config_key: str | None = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, "CONFIGURATION_ERROR", details)


async def handle_mcp_error_async(func):
    """Async decorator to handle MCP errors and convert them to standardized format"""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            raise MCPError(
                message=f"Unexpected error: {str(e)}",
                error_code="INTERNAL_ERROR",
                details={
                    "function": func.__name__,
                    "exception_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                },
            )

    return wrapper


class ErrorHandler:
    """Centralized error handler for MCP servers"""

    def __init__(self, server_name: str):
        self.server_name = server_name
        self.logger = logging.getLogger(f"mcp.{server_name}.errors")

    def format_error_response(self, error: Exception) -> str:
        """Format error for MCP response"""
        if isinstance(error, MCPError):
            return self._format_mcp_error(error)
        else:
            return self._format_generic_error(error)

    def _format_mcp_error(self, error: MCPError) -> str:
        """Format MCP error"""
        import json

        return json.dumps(error.to_dict(), indent=2)

    def _format_generic_error(self, error: Exception) -> str:
        """Format generic error"""
        import json

        error_dict = {
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": str(error),
            "details": {
                "exception_type": type(error).__name__,
                "server": self.server_name,
            },
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(error_dict, indent=2)

    def log_error(self, error: Exception, context: dict[str, Any] | None = None):
        """Log error with context"""
        context = context or {}
        if isinstance(error, MCPError):
            self.logger.error(
                f"MCP Error [{error.error_code}]: {error.message}",
                extra={
                    "error_code": error.error_code,
                    "details": error.details,
                    "context": context,
                    "server": self.server_name,
                },
            )
        else:
            self.logger.error(
                f"Unexpected Error: {str(error)}",
                extra={
                    "exception_type": type(error).__name__,
                    "context": context,
                    "server": self.server_name,
                    "traceback": traceback.format_exc(),
                },
            )


"""
error_handling.py - Syntax errors fixed
This file had severe syntax errors and was replaced with a minimal valid structure.
"""
