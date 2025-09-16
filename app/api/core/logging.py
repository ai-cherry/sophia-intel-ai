"""Structured logging configuration"""
import logging
import sys

try:
    from pythonjsonlogger import jsonlogger  # type: ignore
except Exception:  # pragma: no cover
    jsonlogger = None  # type: ignore


def setup_logging():
    """Configure JSON structured logging, fallback to basic if unavailable"""
    handler = logging.StreamHandler(sys.stdout)
    if jsonlogger is not None:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    handler.setFormatter(formatter)
    logging.root.handlers = []
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)
    # Reduce noise from libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
