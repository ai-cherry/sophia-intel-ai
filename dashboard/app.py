"""
SOPHIA Dashboard v4.1.0
Real-time monitoring and ChatOps interface with proper answer formatting
"""

import os
import time
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, make_response
from flask_cors import CORS
import requests
from version import version_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def json_no_cache(payload, status=200, schema=None):
    """Return JSON response with no-cache headers"""
    resp = jsonify(payload)
    resp.status_code = status
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    if schema:
        resp.headers['X-Response-Schema'] = schema
    return resp

# Configuration
SOPHIA_SERVICES = {
    "code": os.getenv("SOPHIA_CODE_URL", "https://sophia-code.fly.dev"),
    "context": os.getenv("SOPHIA_CONTEXT_URL", "https://sophia-context.fly.dev"),
    "memory": os.getenv("SOPHIA_MEMORY_URL", "https://sophia-memory.fly.dev"),
    "research": os.getenv("SOPHIA_RESEARCH_URL", "https://sophia-research.fly.dev"),
    "business": os.getenv("SOPHIA_BUSINESS_URL", "https://sophia-business.fly.dev")
}

def format_weather_answer(research: dict) -> dict:
    """
    Convert research JSON into UI-friendly weather answer.
    """
    results = research.get("sources") or []
    if not results:
        return {
            "type": "weather", 
            "text": "I couldn't find live weather data right now.", 
            "sources": [], 
            "ts": research.get("created_at")
        }
    
    # Pick the most relevant 1-3 sources
    top = sorted(results, key=lambda r: r.get("relevance_score", 0), reverse=True)[:3]
    lines = []
    
    for r in top:
        snippet = (r.get("snippet") or "")[:200]
        title = r.get("title") or r.get("url", "Weather Source")
        lines.append(f"• {snippet}")
    
    # Create formatted answer
    answer_text = "🌡️ **Las Vegas Weather Today:**\n\n"
    answer_text += "\n\n".join(lines)
    
    if research.get("summary"):
        answer_text += f"\n\n**Summary:** {research['summary'][:300]}{'...' if len(research.get('summary', '')) > 300 else ''}"
    
    sources = [
        {"title": r.get("title") or "Weather Source", "url": r.get("url", "#")} 
        for r in top
    ]
    
    return {
        "type": "weather", 
        "text": answer_text, 
        "sources": sources, 
        "ts": research.get("created_at")
    }

def format_generic_answer(research: dict, query: str) -> dict:
    """
    Convert research JSON into UI-friendly generic answer.
    """
    results = research.get("sources") or []
    
    if not results:
        return {
            "type": "generic",
            "text": f"I searched for '{query}' but couldn't find specific results right now.",
            "sources": [],
            "ts": research.get("created_at")
        }
    
    # Format the answer
    answer_text = f"**Research Results for '{query}':**\n\n"
    
    if research.get("summary"):
        answer_text += f"{research['summary']}\n\n"
    
    answer_text += f"**Found {len(results)} sources:**\n"
    for i, r in enumerate(results[:5], 1):
        title = r.get("title") or "Source"
        snippet = (r.get("snippet") or "")[:150]
        answer_text += f"{i}. **{title}**\n   {snippet}{'...' if len(r.get('snippet', '')) > 150 else ''}\n\n"
    
    sources = [
        {"title": r.get("title") or f"Source {i+1}", "url": r.get("url", "#")} 
        for i, r in enumerate(results[:5])
    ]
    
    return {
        "type": "generic",
        "text": answer_text,
        "sources": sources,
        "ts": research.get("created_at")
    }

@app.route("/")
def dashboard():
    """Main dashboard page"""
    build_time = os.getenv("BUILD_TIME", str(int(time.time())))
    git_commit = os.getenv("GIT_COMMIT", "unknown")
    
    resp = make_response(render_template("dashboard.html", 
                                       build_time=build_time, 
                                       git_commit=git_commit))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp

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
def services_status():
    """Get status of all SOPHIA services"""
    status = {}
    
    for service_name, service_url in SOPHIA_SERVICES.items():
        try:
            import requests
            response = requests.get(f"{service_url}/healthz", timeout=10)
            if response.status_code == 200:
                status[service_name] = {
                    "status": "healthy", 
                    "url": service_url,
                    "response": response.json()
                }
            else:
                status[service_name] = {
                    "status": "unhealthy", 
                    "url": service_url,
                    "status_code": response.status_code
                }
        except Exception as e:
            status[service_name] = {
                "status": "error", 
                "url": service_url,
                "error": str(e)
            }
    
    return jsonify(status)

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat endpoint with proper answer formatting.
    """
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        
        if not user_input:
            return jsonify({
                "ok": False,
                "error": "Message is required",
                "ts": datetime.utcnow().timestamp()
            }), 400
        
        # Route to appropriate service based on intent
        if any(word in user_input.lower() for word in ['weather', 'research', 'search', 'find']):
            # Route to research service
            try:
                import requests
                research_url = SOPHIA_SERVICES.get("research")
                if research_url:
                    response = requests.post(
                        f"{research_url}/search",
                        json={
                            "query": user_input,
                            "sources": ["serper", "tavily"],
                            "max_results_per_source": 5,
                            "include_content": True,
                            "summarize": True
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    # Handle different response types
                    if response.headers.get('content-type', '').startswith('application/json'):
                        research_result = response.json()
                        
                        # Format answer based on query type
                        if any(word in user_input.lower() for word in ['weather', 'temperature', 'forecast']):
                            answer = format_weather_answer(research_result)
                        else:
                            answer = format_generic_answer(research_result, user_input)
                        
                        # Return properly formatted response
                        return json_no_cache({
                            "ok": True,
                            "query": user_input,
                            "answer": answer,
                            "raw": {"research": research_result},
                            "ts": datetime.utcnow().timestamp()
                        }, schema="v2")
                    else:
                        # If HTML or other format, create error response
                        return jsonify({
                            "ok": False,
                            "query": user_input,
                            "answer": {
                                "type": "error",
                                "text": f"Research service returned non-JSON response. Status: {response.status_code}",
                                "sources": [],
                                "ts": datetime.utcnow().timestamp()
                            },
                            "error": "Service configuration issue",
                            "ts": datetime.utcnow().timestamp()
                        })
                        
            except Exception as e:
                logger.error(f"Research service error: {e}")
                # Fallback response
                return jsonify({
                    "ok": False,
                    "query": user_input,
                    "answer": {
                        "type": "error",
                        "text": f"Research service unavailable. Error: {str(e)}",
                        "sources": [],
                        "ts": datetime.utcnow().timestamp()
                    },
                    "error": str(e),
                    "ts": datetime.utcnow().timestamp()
                })
        
        # Default response for other queries
        return json_no_cache({
            "ok": True,
            "query": user_input,
            "answer": {
                "type": "general",
                "text": f"SOPHIA v4.1.0 received: '{user_input}'. This would be processed by the appropriate service in production.",
                "sources": [
                    {"title": "SOPHIA Core", "url": "https://sophia-dashboard.fly.dev"},
                    {"title": "GitHub", "url": "https://github.com/ai-cherry/sophia-intel"},
                    {"title": "Fly.io", "url": "https://fly.io/apps/sophia-dashboard"}
                ],
                "ts": datetime.utcnow().timestamp()
            },
            "ts": datetime.utcnow().timestamp()
        }, schema="v2")
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "ts": datetime.utcnow().timestamp()
        }), 500

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
        },
        "slack": {
            "name": "Slack",
            "status": "connected" if os.getenv("SLACK_BOT_TOKEN") else "not_configured",
            "description": "Team communication and ChatOps"
        },
        "salesforce": {
            "name": "Salesforce",
            "status": "connected" if os.getenv("SALESFORCE_ACCESS_TOKEN") else "not_configured",
            "description": "CRM and sales automation"
        }
    }
    
    return jsonify(integrations)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

