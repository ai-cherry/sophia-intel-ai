"""
SOPHIA v4.1.0 Production Dashboard
Real-time monitoring and ChatOps interface
"""

import os
import asyncio
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
SOPHIA_SERVICES = {
    "code": os.getenv("SOPHIA_CODE_URL", "https://sophia-code.fly.dev"),
    "context": os.getenv("SOPHIA_CONTEXT_URL", "https://sophia-context.fly.dev"),
    "memory": os.getenv("SOPHIA_MEMORY_URL", "https://sophia-memory.fly.dev"),
    "research": os.getenv("SOPHIA_RESEARCH_URL", "https://sophia-research.fly.dev"),
    "business": os.getenv("SOPHIA_BUSINESS_URL", "https://sophia-business.fly.dev")
}

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/healthz')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "4.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": len(SOPHIA_SERVICES)
    })

@app.route('/api/services/status')
async def services_status():
    """Get status of all SOPHIA services"""
    status = {}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for service_name, service_url in SOPHIA_SERVICES.items():
            try:
                response = await client.get(f"{service_url}/healthz")
                if response.status_code == 200:
                    data = response.json()
                    status[service_name] = {
                        "status": "healthy",
                        "url": service_url,
                        "response_time": data.get("response_time_ms", 0),
                        "version": data.get("version", "unknown")
                    }
                else:
                    status[service_name] = {
                        "status": "unhealthy",
                        "url": service_url,
                        "error": f"HTTP {response.status_code}"
                    }
            except Exception as e:
                status[service_name] = {
                    "status": "error", 
                    "url": service_url,
                    "error": str(e)
                }
    
    return jsonify(status)

@app.route('/api/chat', methods=['POST'])
async def chat():
    """ChatOps interface endpoint"""
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        
        if not user_input:
            return jsonify({"error": "Message is required"}), 400
        
        # For demo purposes, simulate ChatOps response
        response = {
            "message": user_input,
            "intent": "demo",
            "response": f"SOPHIA v4.1.0 received: '{user_input}'. In production, this would be processed by the ChatOps router.",
            "timestamp": datetime.utcnow().isoformat(),
            "sources": [
                {"type": "system", "name": "SOPHIA Core", "status": "active"},
                {"type": "integration", "name": "GitHub", "status": "connected"},
                {"type": "integration", "name": "Fly.io", "status": "connected"}
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrations')
def integrations():
    """Get integration status"""
    integrations = {
        "github": {
            "name": "GitHub",
            "status": "connected" if os.getenv("GITHUB_TOKEN") else "not_configured",
            "description": "Repository management and CI/CD"
        },
        "fly": {
            "name": "Fly.io",
            "status": "connected" if os.getenv("FLY_API_TOKEN") else "not_configured", 
            "description": "Cloud deployment and scaling"
        },
        "gong": {
            "name": "Gong.io",
            "status": "connected" if os.getenv("GONG_API_KEY") else "not_configured",
            "description": "Sales call analysis and insights"
        },
        "asana": {
            "name": "Asana",
            "status": "connected" if os.getenv("ASANA_ACCESS_TOKEN") else "not_configured",
            "description": "Task and project management"
        },
        "linear": {
            "name": "Linear",
            "status": "connected" if os.getenv("LINEAR_API_KEY") else "not_configured",
            "description": "Issue tracking and development"
        },
        "notion": {
            "name": "Notion",
            "status": "connected" if os.getenv("NOTION_API_KEY") else "not_configured",
            "description": "Knowledge base and documentation"
        }
    }
    
    return jsonify(integrations)

@app.route('/api/metrics')
def metrics():
    """Prometheus-style metrics endpoint"""
    metrics = f"""# HELP sophia_dashboard_requests_total Total dashboard requests
# TYPE sophia_dashboard_requests_total counter
sophia_dashboard_requests_total 1

# HELP sophia_services_count Number of SOPHIA services
# TYPE sophia_services_count gauge
sophia_services_count {len(SOPHIA_SERVICES)}

# HELP sophia_version_info Version information
# TYPE sophia_version_info gauge
sophia_version_info{{version="4.1.0"}} 1
"""
    return Response(metrics, mimetype='text/plain')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

