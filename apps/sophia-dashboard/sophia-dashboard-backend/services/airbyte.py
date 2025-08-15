# apps/dashboard-backend/services/airbyte.py
import os
import base64
from typing import Dict, Any, List

try:
    import httpx
except ImportError:
    import requests as httpx

AIRBYTE_API_URL = os.getenv("AIRBYTE_API_URL", "http://localhost:8001")  # OSS API service
AIRBYTE_API_TOKEN = os.getenv("AIRBYTE_API_TOKEN")  # Cloud token OR OSS token
AIRBYTE_BASIC_USER = os.getenv("AIRBYTE_BASIC_USER")
AIRBYTE_BASIC_PASS = os.getenv("AIRBYTE_BASIC_PASS")
AIRBYTE_WORKSPACE_ID = os.getenv("AIRBYTE_WORKSPACE_ID")  # optional: narrow scope

DEFAULT_TIMEOUT = float(os.getenv("AIRBYTE_TIMEOUT_SECONDS", "8.0"))

def _headers() -> Dict[str, str]:
    """Generate headers for Airbyte API requests"""
    h = {"Content-Type": "application/json"}
    
    if AIRBYTE_API_TOKEN:
        h["Authorization"] = f"Bearer {AIRBYTE_API_TOKEN}"
    elif AIRBYTE_BASIC_USER and AIRBYTE_BASIC_PASS:
        creds = base64.b64encode(f"{AIRBYTE_BASIC_USER}:{AIRBYTE_BASIC_PASS}".encode()).decode()
        h["Authorization"] = f"Basic {creds}"
    
    return h

def _post(path: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Make POST request to Airbyte API"""
    url = f"{AIRBYTE_API_URL.rstrip('/')}{path}"
    
    if hasattr(httpx, 'post'):
        r = httpx.post(url, headers=_headers(), json=json_data, timeout=DEFAULT_TIMEOUT)
    else:
        r = httpx.post(url, headers=_headers(), json=json_data, timeout=DEFAULT_TIMEOUT)
    
    r.raise_for_status()
    return r.json()

def _get(path: str) -> Dict[str, Any]:
    """Make GET request to Airbyte API"""
    url = f"{AIRBYTE_API_URL.rstrip('/')}{path}"
    
    if hasattr(httpx, 'get'):
        r = httpx.get(url, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    else:
        r = httpx.get(url, headers=_headers(), timeout=DEFAULT_TIMEOUT)
    
    r.raise_for_status()
    return r.json()

def list_workspaces() -> Dict[str, Any]:
    """List all workspaces"""
    try:
        # OSS: POST /api/v1/workspaces/list  (Cloud similar)
        return _post("/api/v1/workspaces/list", {})
    except Exception as e:
        return {
            "error": str(e),
            "workspaces": [],
            "status": "error"
        }

def list_connections(workspace_id: str = None) -> Dict[str, Any]:
    """List connections in a workspace"""
    try:
        body = {"workspaceId": workspace_id} if workspace_id else {}
        return _post("/api/v1/connections/list", body)
    except Exception as e:
        return {
            "error": str(e),
            "connections": [],
            "status": "error"
        }

def get_connection(connection_id: str) -> Dict[str, Any]:
    """Get details of a specific connection"""
    try:
        return _post("/api/v1/connections/get", {"connectionId": connection_id})
    except Exception as e:
        return {
            "error": str(e),
            "connection": None,
            "status": "error"
        }

def trigger_sync(connection_id: str) -> Dict[str, Any]:
    """Trigger a manual sync for a connection"""
    try:
        return _post("/api/v1/connections/sync", {"connectionId": connection_id})
    except Exception as e:
        return {
            "error": str(e),
            "job": None,
            "status": "error"
        }

def get_job_status(job_id: int) -> Dict[str, Any]:
    """Get status of a sync job"""
    try:
        # OSS: POST /api/v1/jobs/get
        return _post("/api/v1/jobs/get", {"id": job_id})
    except Exception as e:
        return {
            "error": str(e),
            "job": None,
            "status": "error"
        }

def list_jobs(connection_id: str = None, limit: int = 10) -> Dict[str, Any]:
    """List recent jobs"""
    try:
        body = {"limit": limit}
        if connection_id:
            body["connectionId"] = connection_id
        return _post("/api/v1/jobs/list", body)
    except Exception as e:
        return {
            "error": str(e),
            "jobs": [],
            "status": "error"
        }

def get_connection_health(connection_id: str) -> Dict[str, str]:
    """Get health status of a connection"""
    try:
        # Get connection details
        conn_data = get_connection(connection_id)
        if conn_data.get("error"):
            return {"status": "error", "detail": conn_data["error"]}
        
        connection = conn_data.get("connection", {})
        status = connection.get("status", "unknown")
        
        # Get recent jobs to determine health
        jobs_data = list_jobs(connection_id, limit=5)
        if jobs_data.get("error"):
            return {"status": "degraded", "detail": "Cannot fetch job history"}
        
        jobs = jobs_data.get("jobs", [])
        if not jobs:
            return {"status": "unknown", "detail": "No job history"}
        
        # Check latest job status
        latest_job = jobs[0] if jobs else {}
        job_status = latest_job.get("job", {}).get("status", "unknown")
        
        if job_status == "succeeded":
            return {"status": "healthy", "detail": f"Last sync: {job_status}"}
        elif job_status in ["running", "pending"]:
            return {"status": "running", "detail": f"Currently: {job_status}"}
        elif job_status in ["failed", "cancelled"]:
            return {"status": "unhealthy", "detail": f"Last sync: {job_status}"}
        else:
            return {"status": "unknown", "detail": f"Status: {job_status}"}
            
    except Exception as e:
        return {"status": "error", "detail": str(e)}

def check_airbyte_health() -> Dict[str, Any]:
    """Check overall Airbyte system health"""
    try:
        # Try to list workspaces as a health check
        workspaces = list_workspaces()
        if workspaces.get("error"):
            return {
                "status": "unhealthy",
                "detail": workspaces["error"],
                "response_time_ms": 0
            }
        
        # Check if we can list connections
        connections = list_connections(AIRBYTE_WORKSPACE_ID)
        if connections.get("error"):
            return {
                "status": "degraded", 
                "detail": f"Workspaces OK, connections failed: {connections['error']}",
                "response_time_ms": 0
            }
        
        return {
            "status": "healthy",
            "detail": f"API responsive, {len(connections.get('connections', []))} connections",
            "response_time_ms": 0
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "detail": str(e),
            "response_time_ms": 0
        }

