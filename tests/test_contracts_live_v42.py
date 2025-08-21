# tests/test_contracts_live_v42.py
import os, json, requests, pytest

RUN = os.getenv("RUN_CONTRACT_TESTS", "0") == "1"
pytestmark = pytest.mark.skipif(not RUN, reason="Set RUN_CONTRACT_TESTS=1 to run live endpoint checks")

CODE_URL     = os.getenv("CODE_URL", "https://sophia-code.fly.dev").rstrip("/")
CONTEXT_URL  = os.getenv("CONTEXT_URL", "https://sophia-context-v42.fly.dev").rstrip("/")
RESEARCH_URL = os.getenv("RESEARCH_URL", "https://sophia-research.fly.dev").rstrip("/")

SERVICES = [
    ("code", CODE_URL),
    ("context", CONTEXT_URL),
    ("research", RESEARCH_URL),
]

def _get_json(url: str):
    r = requests.get(url, timeout=15)
    return r.status_code, (r.json() if "application/json" in r.headers.get("content-type","") else {}), r.text

@pytest.mark.parametrize("name,base", SERVICES)
def test_healthz_shape(name, base):
    code, js, _ = _get_json(f"{base}/healthz")
    assert code == 200, f"/healthz not 200 for {name}: {code}"
    assert isinstance(js, dict), f"/healthz not JSON for {name}"
    assert js.get("service","").startswith(f"sophia-{name}"), f"service mismatch for {name}: {js}"
    # v4.2 target is 'ok' — accept 'healthy' temporarily to ease migration
    assert js.get("status") in {"ok", "healthy"}, f"status must be ok|healthy: {js}"
    assert js.get("version") == "4.2.0", f"version must be 4.2.0: {js}"

def test_context_search_example():
    code, js, _ = _get_json(f"{CONTEXT_URL}/healthz")
    assert code == 200
    r = requests.post(f"{CONTEXT_URL}/context/search",
                      json={"query": "AgentManager create_swarm", "k": 3}, timeout=20)
    assert r.status_code in (200, 501, 400), f"unexpected status: {r.status_code}"
    # If implemented, expect JSON shape with matches list
    if r.status_code == 200:
        body = r.json()
        assert "matches" in body and isinstance(body["matches"], list)

def test_research_search_example():
    code, js, _ = _get_json(f"{RESEARCH_URL}/healthz")
    assert code == 200
    r = requests.post(f"{RESEARCH_URL}/search",
                      json={"query": "AI orchestration platforms", "max_sources": 3}, timeout=30)
    assert r.status_code in (200, 501, 400), f"unexpected status: {r.status_code}"
    if r.status_code == 200:
        body = r.json()
        assert isinstance(body.get("results", []), list)

