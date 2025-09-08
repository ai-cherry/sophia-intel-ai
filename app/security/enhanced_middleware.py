from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import APIError, RateLimitExceeded, ServiceUnavailable, ValidationError


def setup_error_handling(app: FastAPI):
    @app.exception_handler(APIError)
    async def api_exception_handler(request: Request, exc: APIError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "message": exc.message},
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "message": exc.message},
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "message": exc.message},
        )

    @app.exception_handler(ServiceUnavailable)
    async def service_unavailable_exception_handler(request: Request, exc: ServiceUnavailable):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "message": exc.message},
        )

    return app
