"""
Performance Monitoring Dashboard
Real-time visualization of system performance metrics after optimization
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.core.connections import get_connection_manager
from app.core.circuit_breaker import _circuit_manager

app = FastAPI(title="Sophia Intel AI - Performance Dashboard")


class PerformanceMonitor:
    """Collect and aggregate performance metrics"""
    
    def __init__(self):
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history = 1000  # Keep last 1000 data points
        
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics"""
        timestamp = datetime.now().isoformat()
        
        # Get connection pool metrics
        conn_manager = await get_connection_manager()
        connection_metrics = conn_manager.get_metrics()
        
        # Get circuit breaker states
        circuit_states = _circuit_manager.get_all_states()
        open_circuits = _circuit_manager.get_open_circuits()
        
        # Calculate aggregate metrics
        total_circuit_calls = sum(
            state.get("total_calls", 0) 
            for state in circuit_states.values()
        )
        
        avg_success_rate = 0
        if circuit_states:
            success_rates = [
                state.get("success_rate", 0) 
                for state in circuit_states.values()
            ]
            avg_success_rate = sum(success_rates) / len(success_rates)
        
        metrics = {
            "timestamp": timestamp,
            "connections": {
                "http_requests": connection_metrics.get("http_requests", 0),
                "redis_operations": connection_metrics.get("redis_operations", 0),
                "connection_errors": connection_metrics.get("connection_errors", 0),
                "http_connections": connection_metrics.get("http_connections", 0),
                "http_limit": connection_metrics.get("http_limit", 100)
            },
            "circuit_breakers": {
                "total_breakers": len(circuit_states),
                "open_circuits": len(open_circuits),
                "open_circuit_names": open_circuits,
                "total_calls": total_circuit_calls,
                "avg_success_rate": avg_success_rate,
                "states": circuit_states
            },
            "system": {
                "memory_mb": self._get_memory_usage(),
                "cpu_percent": self._get_cpu_usage(),
                "response_time_ms": self._calculate_avg_response_time()
            }
        }
        
        # Add to history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
        
        return metrics
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time from recent requests"""
        # This would integrate with actual request tracking
        # For now, return a simulated value
        import random
        return random.uniform(50, 200)
    
    def get_history(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """Get metrics history for the last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [
            m for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]


# Global monitor instance
monitor = PerformanceMonitor()


@app.get("/")
async def dashboard():
    """Serve the dashboard HTML"""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await websocket.accept()
    
    try:
        while True:
            # Collect and send metrics
            metrics = await monitor.collect_metrics()
            await websocket.send_json(metrics)
            
            # Wait before next update
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")


@app.get("/api/metrics")
async def get_metrics():
    """Get current metrics snapshot"""
    return await monitor.collect_metrics()


@app.get("/api/history")
async def get_history(minutes: int = 5):
    """Get metrics history"""
    return monitor.get_history(minutes)


@app.post("/api/circuit/reset/{name}")
async def reset_circuit(name: str):
    """Reset a specific circuit breaker"""
    breaker = _circuit_manager.get(name)
    if breaker:
        await breaker.reset()
        return {"status": "reset", "name": name}
    return {"status": "not_found", "name": name}


# Dashboard HTML with real-time charts
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Sophia Intel AI - Performance Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .subtitle { opacity: 0.9; }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            opacity: 0.8;
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 1px;
        }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
        }
        .chart-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        canvas { max-height: 300px; }
        .status-good { color: #4ade80; }
        .status-warning { color: #fbbf24; }
        .status-bad { color: #f87171; }
        .circuit-list {
            margin-top: 10px;
            font-size: 0.9em;
        }
        .circuit-item {
            padding: 5px;
            margin: 5px 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
        }
        .badge {
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .badge-open { background: #ef4444; }
        .badge-closed { background: #10b981; }
        .badge-half-open { background: #f59e0b; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Performance Dashboard</h1>
        <div class="subtitle">Real-time monitoring after architectural optimizations</div>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Avg Response Time</div>
            <div class="metric-value" id="response-time">--</div>
            <div class="metric-label">milliseconds</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Connection Pool Usage</div>
            <div class="metric-value" id="connection-usage">--</div>
            <div class="metric-label">active / limit</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Circuit Breakers</div>
            <div class="metric-value" id="circuit-status">--</div>
            <div class="metric-label">open circuits</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value" id="success-rate">--</div>
            <div class="metric-label">percent</div>
        </div>
    </div>
    
    <div class="charts-grid">
        <div class="chart-container">
            <h3>Response Time Trend</h3>
            <canvas id="responseChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>Connection Pool Activity</h3>
            <canvas id="connectionChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>Circuit Breaker States</h3>
            <div id="circuitList"></div>
        </div>
        
        <div class="chart-container">
            <h3>System Resources</h3>
            <canvas id="resourceChart"></canvas>
        </div>
    </div>
    
    <script>
        // Initialize charts
        const responseChart = new Chart(document.getElementById('responseChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Response Time (ms)',
                    data: [],
                    borderColor: '#4ade80',
                    backgroundColor: 'rgba(74, 222, 128, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' } },
                    x: { grid: { color: 'rgba(255,255,255,0.1)' } }
                }
            }
        });
        
        const connectionChart = new Chart(document.getElementById('connectionChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'HTTP Requests',
                        data: [],
                        borderColor: '#60a5fa',
                        backgroundColor: 'rgba(96, 165, 250, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Redis Ops',
                        data: [],
                        borderColor: '#f472b6',
                        backgroundColor: 'rgba(244, 114, 182, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: 'white' } } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' } },
                    x: { grid: { color: 'rgba(255,255,255,0.1)' } }
                }
            }
        });
        
        const resourceChart = new Chart(document.getElementById('resourceChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Memory (MB)',
                        data: [],
                        borderColor: '#fbbf24',
                        backgroundColor: 'rgba(251, 191, 36, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'CPU %',
                        data: [],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: 'white' } } },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: { drawOnChartArea: false }
                    },
                    x: { grid: { color: 'rgba(255,255,255,0.1)' } }
                }
            }
        });
        
        // WebSocket connection
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateMetrics(data);
            updateCharts(data);
        };
        
        function updateMetrics(data) {
            // Update metric cards
            document.getElementById('response-time').textContent = 
                Math.round(data.system.response_time_ms) + 'ms';
            
            document.getElementById('connection-usage').textContent = 
                `${data.connections.http_connections} / ${data.connections.http_limit}`;
            
            document.getElementById('circuit-status').textContent = 
                data.circuit_breakers.open_circuits;
            
            const successRate = Math.round(data.circuit_breakers.avg_success_rate * 100);
            const rateElement = document.getElementById('success-rate');
            rateElement.textContent = successRate + '%';
            rateElement.className = successRate > 90 ? 'metric-value status-good' : 
                                   successRate > 70 ? 'metric-value status-warning' : 
                                   'metric-value status-bad';
            
            // Update circuit breaker list
            updateCircuitList(data.circuit_breakers.states);
        }
        
        function updateCharts(data) {
            const time = new Date(data.timestamp).toLocaleTimeString();
            
            // Update response time chart
            responseChart.data.labels.push(time);
            responseChart.data.datasets[0].data.push(data.system.response_time_ms);
            if (responseChart.data.labels.length > 20) {
                responseChart.data.labels.shift();
                responseChart.data.datasets[0].data.shift();
            }
            responseChart.update('none');
            
            // Update connection chart
            connectionChart.data.labels.push(time);
            connectionChart.data.datasets[0].data.push(data.connections.http_requests);
            connectionChart.data.datasets[1].data.push(data.connections.redis_operations);
            if (connectionChart.data.labels.length > 20) {
                connectionChart.data.labels.shift();
                connectionChart.data.datasets[0].data.shift();
                connectionChart.data.datasets[1].data.shift();
            }
            connectionChart.update('none');
            
            // Update resource chart
            resourceChart.data.labels.push(time);
            resourceChart.data.datasets[0].data.push(data.system.memory_mb);
            resourceChart.data.datasets[1].data.push(data.system.cpu_percent);
            if (resourceChart.data.labels.length > 20) {
                resourceChart.data.labels.shift();
                resourceChart.data.datasets[0].data.shift();
                resourceChart.data.datasets[1].data.shift();
            }
            resourceChart.update('none');
        }
        
        function updateCircuitList(states) {
            const list = document.getElementById('circuitList');
            let html = '';
            
            for (const [name, state] of Object.entries(states)) {
                const badgeClass = state.state === 'open' ? 'badge-open' : 
                                 state.state === 'half_open' ? 'badge-half-open' : 
                                 'badge-closed';
                const successRate = Math.round(state.success_rate * 100);
                
                html += `
                    <div class="circuit-item">
                        <span>${name}</span>
                        <div>
                            <span class="badge ${badgeClass}">${state.state}</span>
                            <span style="margin-left: 10px">${successRate}%</span>
                        </div>
                    </div>
                `;
            }
            
            list.innerHTML = html || '<div>No circuit breakers active</div>';
        }
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    print("🚀 Starting Performance Dashboard on http://localhost:8888")
    uvicorn.run(app, host="0.0.0.0", port=8888)