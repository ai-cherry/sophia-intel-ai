"""
Simplified FastAPI server for testing deployment
This version removes complex dependencies to ensure basic functionality works
"""

import os
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Create FastAPI application
app = FastAPI(
    title="Sophia AI Platform",
    description="Simplified deployment test version",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Try to mount static files and templates (graceful fallback if not available)
try:
    if os.path.exists("app/static"):
        app.mount("/static", StaticFiles(directory="app/static"), name="static")
    if os.path.exists("app/templates"):
        templates = Jinja2Templates(directory="app/templates")
    else:
        templates = None
except Exception as e:
    print(f"Warning: Static files/templates not available: {e}")
    templates = None

# Basic health endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint - always returns 200 if service is running"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }

@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check - simplified version"""
    return {
        "ready": True,
        "checks": {
            "basic": True
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with API information"""
    return {
        "name": "Sophia AI Platform API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs",
            "redoc": "/redoc",
            "dashboard": "/dashboard",
            "metrics": "/metrics",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the unified dashboard UI"""
    if templates is None or not os.path.exists("app/templates/hub.html"):
        # Fallback HTML if template not available
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sophia Intel AI - Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }
                .status { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .endpoints { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
                .endpoint { margin: 10px 0; }
                .endpoint a { color: #007bff; text-decoration: none; }
                .endpoint a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Sophia Intel AI Platform</h1>
                    <p>Local deployment is working successfully!</p>
                </div>
                
                <div class="status">
                    <strong>✅ Status:</strong> Server is running and responding correctly
                </div>
                
                <div class="endpoints">
                    <h3>Available Endpoints:</h3>
                    <div class="endpoint">📊 <a href="/health">Health Check</a> - Service status</div>
                    <div class="endpoint">📚 <a href="/docs">API Documentation</a> - Interactive Swagger UI</div>
                    <div class="endpoint">📖 <a href="/redoc">ReDoc</a> - Alternative API docs</div>
                    <div class="endpoint">📈 <a href="/metrics">Metrics</a> - Prometheus metrics</div>
                    <div class="endpoint">🔍 <a href="/">API Info</a> - Root endpoint information</div>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; text-align: center;">
                    <p>Dashboard Template: Simplified fallback version</p>
                    <p>Timestamp: {timestamp}</p>
                </div>
            </div>
        </body>
        </html>
        """.format(timestamp=datetime.utcnow().isoformat())
        
        return HTMLResponse(content=html_content)
    
    try:
        return templates.TemplateResponse("hub.html", {"request": request})
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Dashboard Error</h1><p>Template error: {e}</p>",
            status_code=500
        )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        return JSONResponse({"error": f"Metrics unavailable: {e}"}, status_code=500)

# Simple test endpoints
@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Test successful", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "simple_server:app",
        host=os.getenv("BIND_IP", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info",
    )
