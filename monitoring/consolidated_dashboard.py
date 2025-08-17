"""
SOPHIA Intel Consolidated Dashboard
Production-ready monitoring dashboard with concurrent health checks,
parameterized service URLs, and enhanced UI with charts and alerting
"""

import asyncio
import aiohttp
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    name: str
    url: str
    status: ServiceStatus
    response_time: float
    last_check: datetime
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemMetrics:
    timestamp: datetime
    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    average_response_time: float
    lambda_servers_active: int
    lambda_servers_total: int


class ConsolidatedDashboard:
    """Consolidated monitoring dashboard for SOPHIA Intel"""

    def __init__(self):
        self.app = FastAPI(
            title="SOPHIA Intel Monitoring Dashboard",
            description="Consolidated monitoring dashboard with real-time health checks",
            version="2.0.0",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Service configuration from environment variables
        self.services = self._load_service_config()

        # Health check configuration
        self.health_check_interval = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
        self.health_check_timeout = int(os.getenv("HEALTH_CHECK_TIMEOUT", "5"))

        # Alerting configuration
        self.alert_thresholds = {
            "unhealthy_services": int(os.getenv("ALERT_UNHEALTHY_THRESHOLD", "2")),
            "response_time": float(os.getenv("ALERT_RESPONSE_TIME_THRESHOLD", "5.0")),
            "lambda_servers_down": int(os.getenv("ALERT_LAMBDA_SERVERS_DOWN", "1")),
        }

        # Data storage
        self.current_health: Dict[str, ServiceHealth] = {}
        self.health_history: List[SystemMetrics] = []
        self.max_history_size = int(os.getenv("MAX_HISTORY_SIZE", "1440"))  # 24 hours at 1-minute intervals

        # Background task control
        self.monitoring_task: Optional[asyncio.Task] = None

        self._setup_routes()

    def _load_service_config(self) -> Dict[str, str]:
        """Load service configuration from environment variables"""
        return {
            "mcp_server": os.getenv("MCP_BASE_URL", "http://localhost:8001"),
            "orchestrator": os.getenv("ORCHESTRATOR_URL", "http://localhost:8000"),
            "api_gateway": os.getenv("API_GATEWAY_URL", "http://localhost:8080"),
            "redis": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "postgres": os.getenv("DATABASE_URL", "postgresql://localhost:5432/sophia_intel"),
            "qdrant": os.getenv("QDRANT_URL", "http://localhost:6333"),
            "airbyte": os.getenv("AIRBYTE_API_URL", "https://api.airbyte.com/v1"),
            "minio": os.getenv("MINIO_ENDPOINT", "http://localhost:9000"),
            "lambda_primary": os.getenv("LAMBDA_PRIMARY_URL", "http://192.222.51.223:8000"),
            "lambda_secondary": os.getenv("LAMBDA_SECONDARY_URL", "http://192.222.50.242:8000"),
        }

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.on_event("startup")
        async def startup_event():
            """Start background monitoring on startup"""
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("SOPHIA Intel Dashboard started with monitoring")

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Stop background monitoring on shutdown"""
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            logger.info("SOPHIA Intel Dashboard stopped")

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            """Main dashboard page"""
            return self._generate_dashboard_html()

        @self.app.get("/api/health")
        async def get_health():
            """Get current health status of all services"""
            return {
                "services": {name: asdict(health) for name, health in self.current_health.items()},
                "summary": self._calculate_summary(),
                "last_updated": datetime.now().isoformat(),
            }

        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get historical metrics for charts"""
            return {
                "history": [asdict(metric) for metric in self.health_history[-100:]],  # Last 100 data points
                "current": self._calculate_current_metrics(),
            }

        @self.app.post("/api/health/refresh")
        async def refresh_health():
            """Manually trigger health check refresh"""
            await self._check_all_services()
            return {"status": "refreshed", "timestamp": datetime.now().isoformat()}

        @self.app.get("/api/services/{service_name}/details")
        async def get_service_details(service_name: str):
            """Get detailed information about a specific service"""
            if service_name not in self.current_health:
                raise HTTPException(status_code=404, detail="Service not found")

            health = self.current_health[service_name]
            return {
                "service": asdict(health),
                "history": [m for m in self.health_history[-50:] if service_name in getattr(m, "service_details", {})],
                "recommendations": self._get_service_recommendations(service_name, health),
            }

        @self.app.post("/api/alerts/test")
        async def test_alert():
            """Test alert system"""
            await self._send_alert("Test Alert", "This is a test alert from SOPHIA Intel Dashboard")
            return {"status": "alert_sent", "timestamp": datetime.now().isoformat()}

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await self._check_all_services()
                await self._update_metrics()
                await self._check_alert_conditions()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Short delay before retrying

    async def _check_all_services(self):
        """Check health of all services concurrently"""
        tasks = []

        for service_name, service_url in self.services.items():
            task = asyncio.create_task(self._check_service_health(service_name, service_url))
            tasks.append(task)

        # Wait for all health checks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update current health status
        for i, result in enumerate(results):
            service_name = list(self.services.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Health check failed for {service_name}: {result}")
                self.current_health[service_name] = ServiceHealth(
                    name=service_name,
                    url=self.services[service_name],
                    status=ServiceStatus.UNKNOWN,
                    response_time=0.0,
                    last_check=datetime.now(),
                    error_message=str(result),
                )
            else:
                self.current_health[service_name] = result

    async def _check_service_health(self, service_name: str, service_url: str) -> ServiceHealth:
        """Check health of a single service"""
        start_time = datetime.now()

        try:
            # Determine health endpoint based on service type
            health_endpoint = self._get_health_endpoint(service_name, service_url)

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.health_check_timeout)) as session:
                async with session.get(health_endpoint) as response:
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()

                    if response.status == 200:
                        try:
                            data = await response.json()
                            status = self._determine_service_status(service_name, data, response_time)

                            return ServiceHealth(
                                name=service_name,
                                url=service_url,
                                status=status,
                                response_time=response_time,
                                last_check=end_time,
                                details=data,
                            )
                        except json.JSONDecodeError:
                            # Service responded but not with JSON
                            return ServiceHealth(
                                name=service_name,
                                url=service_url,
                                status=ServiceStatus.DEGRADED,
                                response_time=response_time,
                                last_check=end_time,
                                error_message="Non-JSON response",
                            )
                    else:
                        return ServiceHealth(
                            name=service_name,
                            url=service_url,
                            status=ServiceStatus.UNHEALTHY,
                            response_time=response_time,
                            last_check=end_time,
                            error_message=f"HTTP {response.status}",
                        )

        except asyncio.TimeoutError:
            return ServiceHealth(
                name=service_name,
                url=service_url,
                status=ServiceStatus.UNHEALTHY,
                response_time=self.health_check_timeout,
                last_check=datetime.now(),
                error_message="Timeout",
            )
        except Exception as e:
            return ServiceHealth(
                name=service_name,
                url=service_url,
                status=ServiceStatus.UNHEALTHY,
                response_time=0.0,
                last_check=datetime.now(),
                error_message=str(e),
            )

    def _get_health_endpoint(self, service_name: str, service_url: str) -> str:
        """Get appropriate health endpoint for service"""
        if service_name in ["redis"]:
            # Redis doesn't have HTTP health endpoint, use ping
            return f"{service_url}/ping"
        elif service_name in ["postgres"]:
            # PostgreSQL doesn't have HTTP health endpoint
            return f"{service_url}/health"  # Assuming a health proxy
        elif service_name.startswith("lambda_"):
            # Lambda Labs inference servers
            return f"{service_url}/health"
        else:
            # Standard health endpoint
            return f"{service_url}/health"

    def _determine_service_status(self, service_name: str, data: Dict[str, Any], response_time: float) -> ServiceStatus:
        """Determine service status based on response data and performance"""
        # Check response time threshold
        if response_time > self.alert_thresholds["response_time"]:
            return ServiceStatus.DEGRADED

        # Check service-specific health indicators
        if service_name.startswith("lambda_"):
            # Lambda Labs server specific checks
            if data.get("status") == "healthy" and data.get("model_loaded", False):
                return ServiceStatus.HEALTHY
            elif data.get("status") == "healthy":
                return ServiceStatus.DEGRADED
            else:
                return ServiceStatus.UNHEALTHY

        # Generic health check
        status = data.get("status", "unknown").lower()
        if status == "healthy":
            return ServiceStatus.HEALTHY
        elif status in ["degraded", "warning"]:
            return ServiceStatus.DEGRADED
        elif status in ["unhealthy", "error"]:
            return ServiceStatus.UNHEALTHY
        else:
            return ServiceStatus.UNKNOWN

    async def _update_metrics(self):
        """Update historical metrics"""
        current_metrics = self._calculate_current_metrics()
        self.health_history.append(current_metrics)

        # Trim history to max size
        if len(self.health_history) > self.max_history_size:
            self.health_history = self.health_history[-self.max_history_size :]

    def _calculate_current_metrics(self) -> SystemMetrics:
        """Calculate current system metrics"""
        total_services = len(self.current_health)
        healthy_count = sum(1 for h in self.current_health.values() if h.status == ServiceStatus.HEALTHY)
        degraded_count = sum(1 for h in self.current_health.values() if h.status == ServiceStatus.DEGRADED)
        unhealthy_count = sum(1 for h in self.current_health.values() if h.status == ServiceStatus.UNHEALTHY)

        # Calculate average response time
        response_times = [h.response_time for h in self.current_health.values() if h.response_time > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

        # Count Lambda Labs servers
        lambda_servers = [h for name, h in self.current_health.items() if name.startswith("lambda_")]
        lambda_active = sum(1 for h in lambda_servers if h.status == ServiceStatus.HEALTHY)
        lambda_total = len(lambda_servers)

        return SystemMetrics(
            timestamp=datetime.now(),
            total_services=total_services,
            healthy_services=healthy_count,
            degraded_services=degraded_count,
            unhealthy_services=unhealthy_count,
            average_response_time=avg_response_time,
            lambda_servers_active=lambda_active,
            lambda_servers_total=lambda_total,
        )

    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics"""
        metrics = self._calculate_current_metrics()

        overall_status = ServiceStatus.HEALTHY
        if metrics.unhealthy_services > 0:
            overall_status = ServiceStatus.UNHEALTHY
        elif metrics.degraded_services > 0:
            overall_status = ServiceStatus.DEGRADED

        return {
            "overall_status": overall_status.value,
            "total_services": metrics.total_services,
            "healthy_services": metrics.healthy_services,
            "degraded_services": metrics.degraded_services,
            "unhealthy_services": metrics.unhealthy_services,
            "average_response_time": round(metrics.average_response_time, 3),
            "lambda_servers": {
                "active": metrics.lambda_servers_active,
                "total": metrics.lambda_servers_total,
                "status": "healthy" if metrics.lambda_servers_active == metrics.lambda_servers_total else "degraded",
            },
        }

    async def _check_alert_conditions(self):
        """Check if any alert conditions are met"""
        metrics = self._calculate_current_metrics()
        alerts = []

        # Check unhealthy services threshold
        if metrics.unhealthy_services >= self.alert_thresholds["unhealthy_services"]:
            alerts.append(f"⚠️ {metrics.unhealthy_services} services are unhealthy")

        # Check response time threshold
        if metrics.average_response_time > self.alert_thresholds["response_time"]:
            alerts.append(
                f"⚠️ Average response time is {metrics.average_response_time:.2f}s (threshold: {self.alert_thresholds['response_time']}s)"
            )

        # Check Lambda Labs servers
        lambda_down = metrics.lambda_servers_total - metrics.lambda_servers_active
        if lambda_down >= self.alert_thresholds["lambda_servers_down"]:
            alerts.append(f"⚠️ {lambda_down} Lambda Labs servers are down")

        # Send alerts if any conditions are met
        if alerts:
            alert_message = "SOPHIA Intel Alert:\n\n" + "\n".join(alerts)
            await self._send_alert("SOPHIA Intel System Alert", alert_message)

    async def _send_alert(self, subject: str, message: str):
        """Send alert via configured channels"""
        try:
            # Slack webhook
            slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
            if slack_webhook:
                await self._send_slack_alert(slack_webhook, subject, message)

            # Email alert
            smtp_host = os.getenv("SMTP_HOST")
            if smtp_host:
                await self._send_email_alert(subject, message)

            logger.info(f"Alert sent: {subject}")

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    async def _send_slack_alert(self, webhook_url: str, subject: str, message: str):
        """Send alert to Slack"""
        payload = {"text": f"*{subject}*\n{message}", "username": "SOPHIA Intel", "icon_emoji": ":warning:"}

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Failed to send Slack alert: {response.status}")

    async def _send_email_alert(self, subject: str, message: str):
        """Send alert via email"""
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        alert_email_to = os.getenv("ALERT_EMAIL_TO")

        if not all([smtp_host, smtp_user, smtp_password, alert_email_to]):
            logger.warning("Email configuration incomplete, skipping email alert")
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = alert_email_to
            msg["Subject"] = subject

            msg.attach(MIMEText(message, "plain"))

            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def _get_service_recommendations(self, service_name: str, health: ServiceHealth) -> List[str]:
        """Get recommendations for service issues"""
        recommendations = []

        if health.status == ServiceStatus.UNHEALTHY:
            recommendations.append("Check service logs for errors")
            recommendations.append("Verify service configuration")
            recommendations.append("Restart the service if necessary")

        if health.response_time > 2.0:
            recommendations.append("Investigate performance bottlenecks")
            recommendations.append("Check resource utilization (CPU, memory)")
            recommendations.append("Consider scaling the service")

        if service_name.startswith("lambda_"):
            if health.status != ServiceStatus.HEALTHY:
                recommendations.append("Check Lambda Labs server status")
                recommendations.append("Verify GPU availability")
                recommendations.append("Check inference model loading")

        return recommendations

    def _generate_dashboard_html(self) -> str:
        """Generate dashboard HTML with embedded JavaScript for real-time updates"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOPHIA Intel - Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 2.5em; }
        .header p { margin: 5px 0 0 0; opacity: 0.9; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status-healthy { border-left: 5px solid #4CAF50; }
        .status-degraded { border-left: 5px solid #FF9800; }
        .status-unhealthy { border-left: 5px solid #F44336; }
        .status-unknown { border-left: 5px solid #9E9E9E; }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
        .metric-value { font-weight: bold; }
        .chart-container { height: 300px; margin: 20px 0; }
        .refresh-btn { background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .refresh-btn:hover { background: #5a6fd8; }
        .alert-section { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 10px 0; }
        .service-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .service-card { padding: 15px; border-radius: 8px; border-left: 4px solid #ddd; }
        .last-updated { text-align: center; color: #666; margin-top: 20px; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 SOPHIA Intel</h1>
        <p>Real-time Monitoring Dashboard</p>
    </div>
    
    <div class="grid">
        <div class="card">
            <h3>System Overview</h3>
            <div id="system-overview">Loading...</div>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
        </div>
        
        <div class="card">
            <h3>Response Time Trends</h3>
            <div class="chart-container">
                <canvas id="responseTimeChart"></canvas>
            </div>
        </div>
        
        <div class="card">
            <h3>Service Health Distribution</h3>
            <div class="chart-container">
                <canvas id="healthDistributionChart"></canvas>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h3>Service Status</h3>
        <div id="services-grid" class="service-grid">Loading...</div>
    </div>
    
    <div class="last-updated" id="last-updated">Last updated: Loading...</div>
    
    <script>
        let responseTimeChart, healthDistributionChart;
        
        async function fetchData() {
            try {
                const [healthResponse, metricsResponse] = await Promise.all([
                    fetch('/api/health'),
                    fetch('/api/metrics')
                ]);
                
                const healthData = await healthResponse.json();
                const metricsData = await metricsResponse.json();
                
                updateSystemOverview(healthData.summary);
                updateServicesGrid(healthData.services);
                updateCharts(metricsData);
                updateLastUpdated(healthData.last_updated);
                
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
        
        function updateSystemOverview(summary) {
            const statusColor = {
                'healthy': '#4CAF50',
                'degraded': '#FF9800', 
                'unhealthy': '#F44336'
            };
            
            document.getElementById('system-overview').innerHTML = `
                <div class="metric">
                    <span>Overall Status:</span>
                    <span class="metric-value" style="color: ${statusColor[summary.overall_status] || '#666'}">
                        ${summary.overall_status.toUpperCase()}
                    </span>
                </div>
                <div class="metric">
                    <span>Total Services:</span>
                    <span class="metric-value">${summary.total_services}</span>
                </div>
                <div class="metric">
                    <span>Healthy:</span>
                    <span class="metric-value" style="color: #4CAF50">${summary.healthy_services}</span>
                </div>
                <div class="metric">
                    <span>Degraded:</span>
                    <span class="metric-value" style="color: #FF9800">${summary.degraded_services}</span>
                </div>
                <div class="metric">
                    <span>Unhealthy:</span>
                    <span class="metric-value" style="color: #F44336">${summary.unhealthy_services}</span>
                </div>
                <div class="metric">
                    <span>Avg Response Time:</span>
                    <span class="metric-value">${summary.average_response_time}s</span>
                </div>
                <div class="metric">
                    <span>Lambda Servers:</span>
                    <span class="metric-value">${summary.lambda_servers.active}/${summary.lambda_servers.total}</span>
                </div>
            `;
        }
        
        function updateServicesGrid(services) {
            const grid = document.getElementById('services-grid');
            grid.innerHTML = Object.entries(services).map(([name, service]) => `
                <div class="service-card status-${service.status}">
                    <h4>${name.replace('_', ' ').toUpperCase()}</h4>
                    <div class="metric">
                        <span>Status:</span>
                        <span class="metric-value">${service.status}</span>
                    </div>
                    <div class="metric">
                        <span>Response Time:</span>
                        <span class="metric-value">${service.response_time.toFixed(3)}s</span>
                    </div>
                    <div class="metric">
                        <span>Last Check:</span>
                        <span class="metric-value">${new Date(service.last_check).toLocaleTimeString()}</span>
                    </div>
                    ${service.error_message ? `<div style="color: #F44336; font-size: 0.9em; margin-top: 5px;">Error: ${service.error_message}</div>` : ''}
                </div>
            `).join('');
        }
        
        function updateCharts(metricsData) {
            const history = metricsData.history.slice(-20); // Last 20 data points
            
            // Response Time Chart
            if (responseTimeChart) {
                responseTimeChart.destroy();
            }
            
            const ctx1 = document.getElementById('responseTimeChart').getContext('2d');
            responseTimeChart = new Chart(ctx1, {
                type: 'line',
                data: {
                    labels: history.map(h => new Date(h.timestamp).toLocaleTimeString()),
                    datasets: [{
                        label: 'Average Response Time (s)',
                        data: history.map(h => h.average_response_time),
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
            
            // Health Distribution Chart
            if (healthDistributionChart) {
                healthDistributionChart.destroy();
            }
            
            const current = metricsData.current;
            const ctx2 = document.getElementById('healthDistributionChart').getContext('2d');
            healthDistributionChart = new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: ['Healthy', 'Degraded', 'Unhealthy'],
                    datasets: [{
                        data: [current.healthy_services, current.degraded_services, current.unhealthy_services],
                        backgroundColor: ['#4CAF50', '#FF9800', '#F44336']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
        
        function updateLastUpdated(timestamp) {
            document.getElementById('last-updated').textContent = 
                `Last updated: ${new Date(timestamp).toLocaleString()}`;
        }
        
        async function refreshData() {
            await fetch('/api/health/refresh', { method: 'POST' });
            await fetchData();
        }
        
        // Initial load and auto-refresh
        fetchData();
        setInterval(fetchData, 30000); // Refresh every 30 seconds
    </script>
</body>
</html>
        """


# Global dashboard instance
dashboard = ConsolidatedDashboard()

if __name__ == "__main__":
    port = int(os.getenv("DASHBOARD_PORT", "8090"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    uvicorn.run(dashboard.app, host="0.0.0.0", port=port, log_level=log_level)
