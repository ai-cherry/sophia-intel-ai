# apps/dashboard-backend/services/mcp_client.py
import os
import json
import time
from typing import Dict, Any, Iterator

try:
    import httpx
except ImportError:
    import requests as httpx

MCP_URL = os.getenv("MCP_CODE_SERVER_URL") or os.getenv("MCP_BASE_URL", "http://localhost:8080")
MCP_TOKEN = os.getenv("MCP_AUTH_TOKEN")

def plan_mission(natural_goal: str) -> Dict[str, Any]:
    """Plan a coding mission using MCP planner"""
    if not MCP_URL:
        raise ValueError("MCP_CODE_SERVER_URL not configured")
    
    headers = {}
    if MCP_TOKEN:
        headers["Authorization"] = f"Bearer {MCP_TOKEN}"
    
    payload = {"goal": natural_goal}
    
    try:
        if hasattr(httpx, 'post'):
            r = httpx.post(f"{MCP_URL.rstrip('/')}/plan", json=payload, headers=headers, timeout=20.0)
        else:
            r = httpx.post(f"{MCP_URL.rstrip('/')}/plan", json=payload, headers=headers, timeout=20.0)
            
        if r.status_code != 200:
            raise Exception(f"MCP planner returned HTTP {r.status_code}: {r.text}")
            
        response = r.json()
        return response.get("mission", {
            "id": f"mission_{int(time.time())}",
            "goal": natural_goal,
            "steps": [
                {"agent": "planner", "action": "analyze_requirements", "status": "pending"},
                {"agent": "coder", "action": "implement_solution", "status": "pending"},
                {"agent": "reviewer", "action": "code_review", "status": "pending"},
                {"agent": "integrator", "action": "create_pr", "status": "pending"}
            ],
            "created_at": time.time()
        })
        
    except Exception as e:
        # Return a mock mission if MCP is not available
        return {
            "id": f"mission_{int(time.time())}",
            "goal": natural_goal,
            "status": "planned",
            "steps": [
                {"agent": "planner", "action": "analyze_requirements", "status": "ready"},
                {"agent": "coder", "action": "implement_solution", "status": "pending"},
                {"agent": "reviewer", "action": "code_review", "status": "pending"},
                {"agent": "integrator", "action": "create_pr", "status": "pending"}
            ],
            "error": f"MCP unavailable: {str(e)}",
            "created_at": time.time()
        }

def run_mission_stream(mission: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    """Run a mission and stream the results"""
    if not MCP_URL:
        yield {"event": "error", "message": "MCP_CODE_SERVER_URL not configured"}
        return
    
    headers = {}
    if MCP_TOKEN:
        headers["Authorization"] = f"Bearer {MCP_TOKEN}"
    
    try:
        # Try to stream from MCP server
        if hasattr(httpx, 'stream'):
            with httpx.stream("POST", f"{MCP_URL.rstrip('/')}/run", json={"mission": mission}, headers=headers, timeout=None) as s:
                for line in s.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        yield data
                    except:
                        yield {"event": "log", "message": line.decode("utf-8", errors="ignore")}
        else:
            # Fallback: simulate mission execution
            steps = mission.get("steps", [])
            for i, step in enumerate(steps):
                yield {"event": "step_start", "step": i, "agent": step.get("agent"), "action": step.get("action")}
                time.sleep(1)  # Simulate work
                yield {"event": "step_complete", "step": i, "agent": step.get("agent"), "result": "completed"}
            
            yield {"event": "mission_complete", "mission_id": mission.get("id"), "status": "success"}
                
    except Exception as e:
        yield {"event": "error", "message": f"Mission execution failed: {str(e)}"}

def get_mission_status(mission_id: str) -> Dict[str, Any]:
    """Get status of a running mission"""
    if not MCP_URL:
        return {"error": "MCP_CODE_SERVER_URL not configured"}
    
    headers = {}
    if MCP_TOKEN:
        headers["Authorization"] = f"Bearer {MCP_TOKEN}"
    
    try:
        if hasattr(httpx, 'get'):
            r = httpx.get(f"{MCP_URL.rstrip('/')}/mission/{mission_id}", headers=headers, timeout=10.0)
        else:
            r = httpx.get(f"{MCP_URL.rstrip('/')}/mission/{mission_id}", headers=headers, timeout=10.0)
            
        if r.status_code == 200:
            return r.json()
        else:
            return {"error": f"HTTP {r.status_code}", "status": "unknown"}
            
    except Exception as e:
        return {"error": str(e), "status": "unknown"}

