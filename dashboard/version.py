"""
Version endpoint for SOPHIA Dashboard
Proves which code version is actually running in production
"""

import os
import time
from flask import Blueprint

version_bp = Blueprint("version", __name__)

def json_no_cache(payload, status=200, schema=None):
    """Return JSON response with no-cache headers"""
    from flask import jsonify
    resp = jsonify(payload)
    resp.status_code = status
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    if schema:
        resp.headers['X-Response-Schema'] = schema
    return resp

@version_bp.route("/api/version", methods=["GET"])
def version():
    """Version endpoint to verify deployment"""
    return json_no_cache({
        "schema": "v2",  # bump when response shape changes
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "built_at": os.getenv("BUILD_TIME", str(int(time.time()))),
        "app_version": "4.1.0",
        "response_format": "new_answer_envelope",
        "ts": time.time()
    }, schema="v2")

