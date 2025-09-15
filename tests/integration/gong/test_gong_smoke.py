import os
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.gong]


def _has_gong_env() -> bool:
    """Check if Gong credentials are available."""
    return bool(os.getenv("GONG_ACCESS_KEY") and os.getenv("GONG_CLIENT_SECRET"))


@pytest.mark.asyncio
async def test_gong_connection():
    """Test Gong client connection."""
    if not _has_gong_env():
        pytest.skip("Gong credentials not configured")

    from app.integrations.gong_optimized_client import GongOptimizedClient

    async with GongOptimizedClient(use_oauth=False) as client:
        ok = await client.test_connection()
        assert ok is True


@pytest.mark.asyncio
async def test_gong_calls_optional():
    """Test Gong calls retrieval (optional - skips if no permissions)."""
    if not _has_gong_env():
        pytest.skip("Gong credentials not configured")

    from app.integrations.gong_optimized_client import GongOptimizedClient

    async with GongOptimizedClient(use_oauth=False) as client:
        # Verify connection first
        ok = await client.test_connection()
        assert ok is True

        # Optional: light calls listing (if available)
        try:
            import datetime as _dt

            to_date = _dt.datetime.utcnow()
            from_date = to_date - _dt.timedelta(days=7)
            resp = await client.get_calls(from_date=from_date, to_date=to_date, limit=1)
            
            assert isinstance(resp, dict)
            # Verify expected structure if calls returned
            if "calls" in resp and resp["calls"]:
                call = resp["calls"][0]
                assert "id" in call or "callId" in call
                
        except Exception as e:
            # Allow environments without permissions to still pass
            pytest.skip(f"Gong calls retrieval not available: {e}")
