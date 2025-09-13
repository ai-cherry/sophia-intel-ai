import asyncio
import types
import pytest
import httpx
@pytest.mark.asyncio
async def test_circuit_breaker_opens_and_half_opens(monkeypatch):
    from services.neural_gateway import main as ng
    gw = ng.NeuralGateway()
    # Prepare a stub http client
    class StubClient:
        def __init__(self):
            self.calls = 0
        async def post(self, url, json=None, timeout=None):
            self.calls += 1
            # First 3 fail -> open circuit; 4th should be blocked; after sleep, succeed
            if self.calls <= 3:
                raise httpx.RequestError("fail")
            # Simulate OK response
            class Resp:
                status_code = 200
                def raise_for_status(self):
                    return None
                def json(self):
                    return {"response": "ok"}
            return Resp()
        async def get(self, url, timeout=None):
            class Resp:
                status_code = 200
            return Resp()
    stub = StubClient()
    # Monkeypatch module global http_client
    ng.http_client = stub
    # Send a request that will fail 3 times and open circuit
    req = ng.ChatRequest(message="hello", stream=False, temperature=0.0, max_tokens=16)
    for _ in range(3):
        with pytest.raises(ng.HTTPException):
            await gw._route_to_neural_engine(req)
    # Now circuit should be open; next call raises immediately
    with pytest.raises(ng.HTTPException) as ei:
        await gw._route_to_neural_engine(req)
    assert "circuit open" in str(ei.value.detail)
    # Fast forward time to half-open window
    gw._cb['neural_engine']['opened_at'] = gw._cb['neural_engine']['opened_at'] - gw._cb_open_seconds - 1
    # Next call should attempt and succeed, closing circuit
    resp = await gw._route_to_neural_engine(req)
    assert resp.get("response") == "ok"
