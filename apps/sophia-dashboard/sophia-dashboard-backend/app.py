import os
import json
import time
import sys
from flask import Flask, jsonify, Response, request, send_from_directory
from flask_cors import CORS

# Add services to path
sys.path.insert(0, os.path.dirname(__file__))

from services.health import check_all_components
from services.mcp_client import plan_mission, run_mission_stream
from services.models import get_allowed_models_filtered

app = Flask(__name__, static_folder="static", static_url_path="/")
CORS(app)

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

