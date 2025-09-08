#!/usr/bin/env python3
"""
Docker Monitoring Dashboard

A simple Flask-based web dashboard to monitor Docker containers
running within the dev container environment.
"""

import threading
import time

from container_manager import DockerManager
from flask import Flask, jsonify, render_template

app = Flask(__name__)
manager = DockerManager()
containers_cache = []
last_update = 0
update_lock = threading.Lock()

# Update container data every 5 seconds
UPDATE_INTERVAL = 5


def update_container_data():
    """Background thread to update container information."""
    global containers_cache, last_update
    while True:
        try:
            containers = manager.list_containers(all_containers=True)

            # Add stats for running containers
            for container in containers:
                if container.get("State") == "running":
                    try:
                        stats = manager.container_stats(container["ID"])
                        container["Stats"] = stats
                    except Exception as e:
                        container["Stats"] = {"Error": str(e)}

            with update_lock:
                containers_cache = containers
                last_update = time.time()

        except Exception as e:
            print(f"Error updating container data: {e}")

        time.sleep(UPDATE_INTERVAL)


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("dashboard.html")


@app.route("/api/containers")
def get_containers():
    """API endpoint to get container data."""
    with update_lock:
        return jsonify({"containers": containers_cache, "last_update": last_update})


@app.route("/api/container/<container_id>/logs")
def get_container_logs(container_id):
    """API endpoint to get logs for a specific container."""
    try:
        logs = manager.get_logs(container_id, tail=100)
        return jsonify({"logs": logs.split("\n")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/container/<container_id>/stop", methods=["POST"])
def stop_container(container_id):
    """API endpoint to stop a container."""
    try:
        result = manager.stop_container(container_id)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/container/<container_id>/remove", methods=["POST"])
def remove_container(container_id):
    """API endpoint to remove a container."""
    try:
        result = manager.remove_container(container_id)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main():
    """Start the Flask application and the background update thread."""
    # Start background update thread
    update_thread = threading.Thread(target=update_container_data)
    update_thread.daemon = True
    update_thread.start()

    # Start Flask app
    app.run(host="${BIND_IP}", port=8080, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
