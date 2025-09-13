from __future__ import annotations

import logging
import re


class RedactAuthFilter(logging.Filter):
    """Filter that redacts Authorization headers and API keys from logs."""

    _auth_re = re.compile(r"(Authorization:\s*)([^\r\n]+)", re.IGNORECASE)
    _bearer_re = re.compile(r"Bearer\s+[A-Za-z0-9\-_.=:+/]+", re.IGNORECASE)
    _jwt_re = re.compile(r"eyJ[\w\-_.]+\.[\w\-_.]+\.[\w\-_.]+")
    _key_re = re.compile(r"(api_?key=)([^&\s]+)", re.IGNORECASE)

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        try:
            msg = str(record.getMessage())
            msg = self._auth_re.sub(r"\1[REDACTED]", msg)
            msg = self._bearer_re.sub("Bearer [REDACTED]", msg)
            msg = self._jwt_re.sub("[REDACTED_JWT]", msg)
            msg = self._key_re.sub(r"\1[REDACTED]", msg)
            record.msg = msg
        except Exception:
            pass
        return True


def install_redaction() -> None:
    filt = RedactAuthFilter()
    for name in ("uvicorn", "uvicorn.access", "httpx", "fastapi", "root"):
        logger = logging.getLogger(name)
        logger.addFilter(filt)
