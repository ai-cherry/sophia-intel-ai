from __future__ import annotations

from typing import Any, Dict
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def _base_payload(request: Request, message: str, code: str) -> Dict[str, Any]:
    rid = getattr(request, "request_id", None) or request.scope.get("request_id")
    return {"code": code, "message": message, "correlation_id": rid}


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    payload = _base_payload(request, exc.detail if exc.detail else "HTTP error", "http_error")
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    payload = _base_payload(request, "Validation error", "validation_error")
    payload["errors"] = exc.errors()
    return JSONResponse(status_code=422, content=payload)


async def unhandled_exception_handler(request: Request, exc: Exception):
    payload = _base_payload(request, "Internal server error", "internal_error")
    return JSONResponse(status_code=500, content=payload)

