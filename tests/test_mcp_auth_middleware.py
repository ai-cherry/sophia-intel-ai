import os
import pytest
from fastapi.testclient import TestClient


def _with_env(env: dict):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            old = {k: os.getenv(k) for k in env}
            try:
                for k, v in env.items():
                    if v is None and k in os.environ:
                        del os.environ[k]
                    elif v is not None:
                        os.environ[k] = v
                return fn(*args, **kwargs)
            finally:
                for k, v in old.items():
                    if v is None and k in os.environ:
                        del os.environ[k]
                    elif v is not None:
                        os.environ[k] = v
        return wrapper
    return decorator


@_with_env({"MCP_TOKEN": "secret", "MCP_DEV_BYPASS": "false"})
def test_mcp_fs_requires_bearer():
    from mcp.filesystem.server import app
    client = TestClient(app)
    # No auth
    r = client.post("/repo/list", json={"root": ".", "limit": 1})
    assert r.status_code == 401
    # With auth
    r = client.post(
        "/repo/list",
        headers={"Authorization": "Bearer secret"},
        json={"root": ".", "limit": 1},
    )
    # Either 200 or 400 if invalid path — but not 401
    assert r.status_code in (200, 400)

