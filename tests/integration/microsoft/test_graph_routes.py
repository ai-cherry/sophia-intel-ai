import os
import pytest
import httpx

pytestmark = pytest.mark.integration


def _api_base() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8000")


def _server_up(base: str) -> bool:
    try:
        with httpx.Client(timeout=2.0) as c:
            r = c.get(f"{base}/health")
            return r.status_code == 200
    except Exception:
        return False


def _has_ms_env() -> bool:
    return bool(
        (os.getenv("MS_TENANT_ID") or os.getenv("MICROSOFT_TENANT_ID"))
        and (os.getenv("MS_CLIENT_ID") or os.getenv("MICROSOFT_CLIENT_ID"))
        and (os.getenv("MS_CLIENT_SECRET") or os.getenv("MICROSOFT_SECRET_KEY"))
    )


def test_graph_routes_smoke():
    if not _has_ms_env():
        pytest.skip("Microsoft Graph env not configured")

    base = _api_base()
    if not _server_up(base):
        pytest.skip("API server not running")

    with httpx.Client(timeout=5.0) as c:
        r = c.get(f"{base}/api/microsoft/users?top=1")
        assert r.status_code == 200
        r = c.get(f"{base}/api/microsoft/teams?top=1")
        assert r.status_code == 200
        r = c.get(f"{base}/api/microsoft/drive-root")
        assert r.status_code == 200

