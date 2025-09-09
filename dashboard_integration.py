#!/usr/bin/env python3
"""
Sophia AI Dashboard Integration Service

This service bridges the gap between different dashboard components and ensures
proper data flow between them. It resolves circular dependencies and provides
a unified interface for all dashboards.
"""

import argparse
import logging
from datetime import datetime
from typing import Any, Dict

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("dashboard_integration.log"),
    ],
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sophia AI Dashboard Integration",
    description="Unified dashboard data integration service",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DEFAULT_TIMEOUT = 10  # seconds
DEFAULT_CACHE_TTL = 60  # seconds
DASHBOARD_URLS = {
    "main": "http://localhost:8501",
    "business": "http://localhost:8502",
    "monitoring": "http://localhost:3001",
}
API_URLS = {
    "sophia": "http://localhost:8000",
}

# In-memory cache
dashboard_data_cache = {}


# Models
class HealthStatus(BaseModel):
    status: str
    timestamp: str
    components: Dict[str, str]
    services: Dict[str, str]


class DashboardMetrics(BaseModel):
    component: str
    metrics: Dict[str, Any]
    timestamp: str


# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with links to all dashboards"""
    html_content = """
    <html>
        <head>
            <title>Sophia AI Dashboards</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #2a6496; }
                .dashboard-list { display: flex; flex-wrap: wrap; }
                .dashboard-card { 
                    border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 10px;
                    width: 200px; background-color: #f8f9fa;
                }
                .dashboard-card h3 { margin-top: 0; }
                .dashboard-link { 
                    display: inline-block; background-color: #2a6496; color: white;
                    padding: 8px 16px; border-radius: 4px; text-decoration: none; margin-top: 10px;
                }
                .dashboard-link:hover { background-color: #1a4c80; }
            </style>
        </head>
        <body>
            <h1>Sophia AI Unified Dashboard Hub</h1>
            <p>Welcome to the Sophia AI Platform dashboard hub. Select a dashboard to view:</p>

            <div class="dashboard-list">
                <div class="dashboard-card">
                    <h3>🏠 Main Dashboard</h3>
                    <p>Platform overview and high-level metrics</p>
                    <a href="/redirect/main" class="dashboard-link">Open</a>
                </div>



                <div class="dashboard-card">
                    <h3>📊 Business Dashboard</h3>
                    <p>Business metrics and executive information</p>
                    <a href="/redirect/business" class="dashboard-link">Open</a>
                </div>

                <div class="dashboard-card">
                    <h3>📈 Monitoring</h3>
                    <p>System monitoring and infrastructure metrics</p>
                    <a href="/redirect/monitoring" class="dashboard-link">Open</a>
                </div>
            </div>

            <div style="margin-top: 30px;">
                <h2>API Status</h2>
                <ul>
                    <li><a href="/health">System Health</a></li>
                    <li><a href="/api/dashboard/unified">Unified Dashboard Data</a></li>
                </ul>
            </div>
        </body>
    </html>
    """
    return html_content


@app.get("/redirect/{dashboard}")
async def redirect_to_dashboard(dashboard: str):
    """Redirect to the specified dashboard"""
    if dashboard in DASHBOARD_URLS:
        return RedirectResponse(url=DASHBOARD_URLS[dashboard])
    raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard}' not found")


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    components = {}
    services = {}

    # Check component health
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
        # Check Sophia API
        try:
            async with session.get(f"{API_URLS['sophia']}/health") as response:
                if response.status == 200:
                    components["sophia_api"] = "healthy"
                else:
                    components["sophia_api"] = "degraded"
        except Exception:components["sophia_api"] = "unhealthy"

        # Artemis removed

        # Check dashboards
        for name, url in DASHBOARD_URLS.items():
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        services[f"{name}_dashboard"] = "healthy"
                    else:
                        services[f"{name}_dashboard"] = "degraded"
            except Exception:services[f"{name}_dashboard"] = "unhealthy"

    return HealthStatus(
        status=(
            "healthy"
            if all(v == "healthy" for v in components.values())
            else "degraded"
        ),
        timestamp=datetime.now().isoformat(),
        components=components,
        services=services,
    )


@app.get("/api/dashboard/unified")
async def unified_dashboard_data():
    """Unified dashboard data endpoint that aggregates data from all sources"""
    # Check if we have valid cached data
    cache_key = "unified_dashboard_data"
    now = datetime.now().timestamp()

    if cache_key in dashboard_data_cache:
        cache_entry = dashboard_data_cache[cache_key]
        if now - cache_entry["timestamp"] < DEFAULT_CACHE_TTL:
            logger.debug("Returning cached unified dashboard data")
            return cache_entry["data"]

    # Collect data from various sources
    data = {
        "timestamp": datetime.now().isoformat(),
        "components": {},
    }

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
    ) as session:
        # Fetch Sophia API data
        try:
            async with session.get(f"{API_URLS['sophia']}/health") as response:
                if response.status == 200:
                    sophia_data = await response.json()
                    data["components"]["sophia"] = {
                        "status": sophia_data.get("status", "unknown"),
                        "uptime": sophia_data.get("uptime", 0),
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch Sophia API data: {e}")
            data["components"]["sophia"] = {"status": "error", "error": str(e)}

        # Fetch Artemis data
        try:
            async with session.get(f"{API_URLS['artemis']}/status") as response:
                if response.status == 200:
                    artemis_data = await response.json()
                    data["components"]["artemis"] = {
                        "status": artemis_data.get("status", "unknown"),
                        "agents": artemis_data.get("agents", {}),
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch Artemis data: {e}")
            data["components"]["artemis"] = {"status": "error", "error": str(e)}

    # Cache the data
    dashboard_data_cache[cache_key] = {
        "timestamp": now,
        "data": data,
    }

    return data


@app.post("/api/dashboard/metrics")
async def update_metrics(metrics: DashboardMetrics):
    """Update dashboard metrics from any component"""
    component = metrics.component
    timestamp = metrics.timestamp

    logger.info(f"Received metrics update from {component}")

    # Store in cache
    cache_key = f"metrics_{component}"
    dashboard_data_cache[cache_key] = {
        "timestamp": datetime.now().timestamp(),
        "data": metrics.dict(),
    }

    return {"status": "success", "message": f"Updated metrics for {component}"}


@app.get("/api/dashboard/{component}/metrics")
async def get_component_metrics(component: str):
    """Get metrics for a specific component"""
    cache_key = f"metrics_{component}"

    if cache_key in dashboard_data_cache:
        cache_entry = dashboard_data_cache[cache_key]
        return cache_entry["data"]

    raise HTTPException(
        status_code=404, detail=f"No metrics found for component '{component}'"
    )


def main():
    """Run the dashboard integration service"""
    parser = argparse.ArgumentParser(
        description="Sophia AI Dashboard Integration Service"
    )
    parser.add_argument(
        "--host", type=str, default="${BIND_IP}", help="Host to bind to"
    )
    parser.add_argument("--port", type=int, default=8505, help="Port to bind to")
    args = parser.parse_args()

    logger.info(f"Starting dashboard integration service on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
