from __future__ import annotations

import os
from fastapi import Header, HTTPException


async def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """Simple RBAC: if ADMIN_API_KEY is set, require matching X-Admin-Key header.

    In local/dev when ADMIN_API_KEY is unset, allow writes by default.
    """
    expected = os.getenv("ADMIN_API_KEY")
    if not expected:
        return  # open in dev
    if not x_admin_key or x_admin_key != expected:
        raise HTTPException(status_code=403, detail="admin required")

