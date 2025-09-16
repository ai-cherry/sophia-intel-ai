from fastapi.testclient import TestClient
from app.api.main import app


def test_factory_agent_crud():
    client = TestClient(app)

    # Create agent
    r = client.post(
        "/api/factory/agents",
        json={"name": "Test Agent", "role": "planner", "config": {"temperature": 0.2}},
    )
    assert r.status_code == 201
    agent = r.json()
    agent_id = agent["id"]

    # Get agent
    r = client.get(f"/api/factory/agents/{agent_id}")
    assert r.status_code == 200

    # Update agent
    r = client.put(f"/api/factory/agents/{agent_id}", json={"published": True})
    assert r.status_code == 200
    assert r.json()["published"] is True

    # Publish (bumps version)
    r = client.post(f"/api/factory/agents/{agent_id}/publish")
    assert r.status_code == 200
    assert r.json()["version"] >= 2

    # Delete
    r = client.delete(f"/api/factory/agents/{agent_id}")
    assert r.status_code == 204


def test_factory_swarm_crud():
    client = TestClient(app)

    # Create swarm
    r = client.post(
        "/api/factory/swarms",
        json={"name": "Test Swarm", "description": "demo", "agent_ids": []},
    )
    assert r.status_code == 201
    swarm = r.json()
    swarm_id = swarm["id"]

    # Update swarm
    r = client.put(f"/api/factory/swarms/{swarm_id}", json={"published": True})
    assert r.status_code == 200

    # Publish
    r = client.post(f"/api/factory/swarms/{swarm_id}/publish")
    assert r.status_code == 200
    assert r.json()["published"] is True

    # Delete
    r = client.delete(f"/api/factory/swarms/{swarm_id}")
    assert r.status_code == 204

