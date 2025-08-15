import os
import json
import time
import sys
from flask import Flask, jsonify, Response, request, send_from_directory
from flask_cors import CORS
from functools import wraps

# Add services to path
sys.path.insert(0, os.path.dirname(__file__))

from services.health import check_all_components
from services.mcp_client import plan_mission, run_mission_stream
from services.models import get_allowed_models_filtered
from services.airbyte import list_workspaces, list_connections, trigger_sync, get_job_status, list_jobs

app = Flask(__name__, static_folder="static", static_url_path="/")
CORS(app)

# API Token for protected operations
API_TOKEN = os.getenv("DASHBOARD_API_TOKEN")

def requires_token(f):
    """Decorator to require API token for mutating operations"""
    @wraps(f)
    def _wrapped(*args, **kwargs):
        if not API_TOKEN:
            return f(*args, **kwargs)  # Allow if not set (dev mode)
        if request.headers.get("X-Auth-Token") != API_TOKEN:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return _wrapped

@app.route("/api/health")
def api_health():
    """Health check endpoint - never hangs, always returns within timeout"""
    try:
        result = check_all_components()
        status_code = 200 if result["status"] != "error" else 503
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "elapsed_ms": 0,
            "components": {},
            "timestamp": time.time()
        }), 500

@app.route("/api/models/allowlist")
def api_models():
    """Get OpenRouter approved model allow-list"""
    try:
        data = get_allowed_models_filtered()
        return jsonify(data)
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "models": [],
            "total_approved": 20,
            "available_count": 0
        }), 500

@app.route("/api/swarm/plan", methods=["POST"])
def api_swarm_plan():
    """Plan a new swarm mission"""
    try:
        payload = request.get_json(force=True)
        nl = payload.get("goal", "").strip()
        if not nl:
            return jsonify({"error": "missing 'goal'"}), 400
        
        mission = plan_mission(nl)
        return jsonify({"mission": mission})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/swarm/run", methods=["POST"])
def api_swarm_run():
    """Run a swarm mission with Server-Sent Events streaming"""
    try:
        mission = request.get_json(force=True).get("mission")
        if not mission:
            return jsonify({"error": "missing 'mission'"}), 400

        def sse():
            """Server-Sent Events generator"""
            try:
                for evt in run_mission_stream(mission):
                    yield f"data: {json.dumps(evt)}\n\n"
                    time.sleep(0.02)  # Small delay for smooth streaming
                yield "event: done\ndata: {}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

        return Response(sse(), mimetype="text/event-stream")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/swarm/jobs")
def api_swarm_jobs():
    """List recent swarm jobs"""
    # Mock data for now - in production would read from database
    return jsonify({
        "jobs": [
            {
                "id": "job_001",
                "goal": "Build user authentication system",
                "status": "completed",
                "created_at": time.time() - 3600,
                "completed_at": time.time() - 3300
            },
            {
                "id": "job_002", 
                "goal": "Add payment integration",
                "status": "running",
                "created_at": time.time() - 1800
            }
        ]
    })

# Airbyte Pipeline Management Endpoints

@app.route("/api/pipelines/workspaces")
def api_airbyte_workspaces():
    """List Airbyte workspaces"""
    return jsonify(list_workspaces())

@app.route("/api/pipelines/connections")
def api_airbyte_connections():
    """List Airbyte connections"""
    workspace_id = request.args.get("workspaceId") or os.getenv("AIRBYTE_WORKSPACE_ID")
    return jsonify(list_connections(workspace_id))

@app.route("/api/pipelines/sync", methods=["POST"])
@requires_token
def api_airbyte_sync():
    """Trigger a manual sync for a connection"""
    try:
        connection_id = request.json.get("connectionId")
        if not connection_id:
            return jsonify({"error": "missing connectionId"}), 400
        
        data = trigger_sync(connection_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/pipelines/jobs/<int:job_id>")
def api_airbyte_job(job_id: int):
    """Get status of a specific Airbyte job"""
    return jsonify(get_job_status(job_id))

@app.route("/api/pipelines/jobs")
def api_airbyte_jobs():
    """List recent Airbyte jobs"""
    connection_id = request.args.get("connectionId")
    limit = int(request.args.get("limit", "10"))
    return jsonify(list_jobs(connection_id, limit))

# Serve frontend build
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Serve React frontend from static folder"""
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_ENV") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)

