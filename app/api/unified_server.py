"""
Compatibility entrypoint for unified API.
Exports the main FastAPI application from app.api.main as `app`.
"""
from app.api.main import app  # noqa: F401

