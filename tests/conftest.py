"""Pytest configuration and fixtures"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Create test client"""
    from backend.main import app
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Create async test client"""
    from backend.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

