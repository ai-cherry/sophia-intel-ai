from __future__ import annotations

import uuid
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestIDMiddleware:
    """Attach a correlation/request ID to each request and response headers.

    - Reads incoming X-Request-ID if present, otherwise generates a UUID4.
    - Stores it on scope['state'].correlation_id for handlers to use.
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        self.app = app
        self.header_name = header_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                # Ensure header present
                rid = scope.setdefault("request_id", str(uuid.uuid4()))
                headers.append((self.header_name.encode(), rid.encode()))
                message["headers"] = headers
            await send(message)

        # Get existing header if present via scope extensions (depends on server)
        rid = None
        for key, value in scope.get("headers", []):
            if key.decode().lower() == self.header_name.lower():
                rid = value.decode()
                break
        scope["request_id"] = rid or str(uuid.uuid4())
        await self.app(scope, receive, send_wrapper)

