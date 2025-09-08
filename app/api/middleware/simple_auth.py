"""
Simple API Key Authentication Middleware
Pragmatic approach - good enough security without over-engineering
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException, Request

from backend.config.secrets import get_api_key

logger = logging.getLogger(__name__)

# Public endpoints that don't require API key
PUBLIC_ENDPOINTS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/",
    "/favicon.ico",
}


async def verify_api_key(
    request: Request, x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[str]:
    """
    Dead simple API key check - good enough for now

    Strategy:
    - Public endpoints: Always allow
    - Sensitive endpoints: Require valid API key
    - Invalid key: Log warning and block
    """

    # Check if this is a public endpoint
    path = request.url.path
    if path in PUBLIC_ENDPOINTS:
        return None  # No auth required

    # Check for API key
    expected_key = get_api_key()

    if not x_api_key:
        logger.warning(f"Missing API key for {path} from {request.client.host}")
        raise HTTPException(
            status_code=401, detail="API key required. Include X-API-Key header."
        )

    if x_api_key != expected_key:
        logger.warning(f"Invalid API key for {path} from {request.client.host}")
        raise HTTPException(status_code=403, detail="Invalid API key")

    logger.debug(f"Valid API key for {path}")
    return x_api_key


async def optional_api_key(
    request: Request, x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[str]:
    """
    Optional API key check - for endpoints that work better with auth
    but don't strictly require it
    """

    path = request.url.path
    if path in PUBLIC_ENDPOINTS:
        return None

    expected_key = get_api_key()

    if x_api_key and x_api_key == expected_key:
        logger.debug(f"Valid API key provided for {path}")
        return x_api_key
    elif x_api_key:
        logger.warning(f"Invalid API key provided for {path}")

    return None


def is_authenticated(api_key: Optional[str]) -> bool:
    """Check if the provided API key is valid"""
    if not api_key:
        return False
    return api_key == get_api_key()


# Convenience function for manual checks
def require_api_key(api_key: Optional[str], endpoint: str = "unknown") -> None:
    """Manually check API key and raise exception if invalid"""
    if not is_authenticated(api_key):
        logger.warning(f"API key check failed for {endpoint}")
        raise HTTPException(status_code=403, detail="Valid API key required")
