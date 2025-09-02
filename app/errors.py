class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message: str, status_code: int = 400, error_code: str = "internal_error"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)

class ValidationError(APIError):
    """Raised when input validation fails"""
    def __init__(self, message: str, status_code: 400, error_code: "validation_error"):
        super().__init__(message, status_code, error_code)

class RateLimitExceeded(APIError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded", status_code: int = 429, error_code: str = "rate_limit_exceeded"):
        super().__init__(message, status_code, error_code)

class ServiceUnavailable(APIError):
    """Raised when a service is unavailable"""
    def __init__(self, message: str = "Service unavailable", status_code: int = 503, error_code: str = "service_unavailable"):
        super().__init__(message, status_code, error_code)