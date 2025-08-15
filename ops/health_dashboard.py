#!/usr/bin/env python3
"""
Sophia Intel Health Dashboard
Real-time web dashboard for platform monitoring
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ops.monitoring import SophiaIntelMonitor


class HealthDashboard:
    """Flask-based health dashboard"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.latest_health_data = {}
        self.health_history = []
        self.monitor = None
        self.monitoring_thread = None
        self.running = False
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/health')
        def get_health():
            """Get current health status"""
            return jsonify(self.latest_health_data)
        
        @self.app.route('/api/health/history')
        def get_health_history():
            """Get health history"""
            hours = request.args.get('hours', 24, type=int)
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            filtered_history = [
                entry for entry in self.health_history
                if datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')) > cutoff_time
            ]
            
            return jsonify(filtered_history)
        
        @self.app.route('/api/components')
        def get_components():
            """Get component status summary"""
            if not self.latest_health_data:
                return jsonify({"error": "No health data available"})
            
            components = self.latest_health_data.get('components', {})
            summary = []
            
            for name, data in components.items():
                summary.append({
                    "name": name,
                    "status": data['status'],
                    "response_time": data.get('response_time_ms'),
                    "last_check": data['last_check'],
                    "error": data.get('error_message')
                })
            
            return jsonify(summary)
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get system metrics"""
            if not self.latest_health_data:
                return jsonify({"error": "No metrics available"})
            
            return jsonify(self.latest_health_data.get('system_metrics', {}))
        
        @self.app.route('/api/alerts')
        def get_alerts():
            """Get current alerts"""
            alerts = []
            
            if not self.latest_health_data:
                return jsonify(alerts)
            
            components = self.latest_health_data.get('components', {})
            sys_metrics = self.latest_health_data.get('system_metrics', {})
            
            # Component alerts
            for name, data in components.items():
                if data['status'] == 'unhealthy':
                    alerts.append({
                        "type": "critical",
                        "component": name,
                        "message": f"{name} is unhealthy: {data.get('error_message', 'Unknown error')}",
                        "timestamp": data['last_check']
                    })
                elif data['status'] == 'degraded':
                    alerts.append({
                        "type": "warning",
                        "component": name,
                        "message": f"{name} performance degraded: {data.get('error_message', 'Performance issues')}",
                        "timestamp": data['last_check']
                    })
            
            # System alerts
            if sys_metrics.get('cpu_percent', 0) > 90:
                alerts.append({
                    "type": "critical",
                    "component": "system",
                    "message": f"High CPU usage: {sys_metrics['cpu_percent']:.1f}%",
                    "timestamp": sys_metrics['timestamp']
                })
            elif sys_metrics.get('cpu_percent', 0) > 80:
                alerts.append({
                    "type": "warning",
                    "component": "system",
                    "message": f"Elevated CPU usage: {sys_metrics['cpu_percent']:.1f}%",
                    "timestamp": sys_metrics['timestamp']
                })
            
            if sys_metrics.get('memory_percent', 0) > 90:
                alerts.append({
                    "type": "critical",
                    "component": "system",
                    "message": f"High memory usage: {sys_metrics['memory_percent']:.1f}%",
                    "timestamp": sys_metrics['timestamp']
                })
            elif sys_metrics.get('memory_percent', 0) > 80:
                alerts.append({
                    "type": "warning",
                    "component": "system",
                    "message": f"Elevated memory usage: {sys_metrics['memory_percent']:.1f}%",
                    "timestamp": sys_metrics['timestamp']
                })
            
            return jsonify(alerts)
    
    async def run_monitoring_loop(self):
        """Background monitoring loop"""
        async with SophiaIntelMonitor() as monitor:
            self.monitor = monitor
            
            while self.running:
                try:
                    # Run health check
                    health_data = await monitor.run_comprehensive_health_check()
                    
                    # Update latest data
                    self.latest_health_data = health_data
                    
                    # Add to history (keep last 1000 entries)
                    self.health_history.append(health_data)
                    if len(self.health_history) > 1000:
                        self.health_history.pop(0)
                    
                    print(f"✅ Health check completed at {health_data['timestamp']}")
                    
                except Exception as e:
                    print(f"❌ Monitoring error: {e}")
                
                # Wait 60 seconds between checks
                for _ in range(60):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
    
    def start_monitoring(self):
        """Start background monitoring"""
        self.running = True
        
        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_monitoring_loop())
        
        self.monitoring_thread = threading.Thread(target=run_async_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
    
    def create_dashboard_template(self):
        """Create HTML template for dashboard"""
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        
        dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sophia Intel Health Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f1419;
            color: #ffffff;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .header h1 {
            font-size: 2rem;
            font-weight: 600;
        }
        
        .header .subtitle {
            opacity: 0.9;
            margin-top: 0.5rem;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: #1a1f2e;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            border: 1px solid #2d3748;
        }
        
        .card h3 {
            color: #e2e8f0;
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #2d3748;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #a0aec0;
        }
        
        .metric-value {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .status-healthy { color: #48bb78; }
        .status-degraded { color: #ed8936; }
        .status-unhealthy { color: #f56565; }
        .status-unknown { color: #a0aec0; }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #2d3748;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }
        
        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
        }
        
        .progress-low { background: #48bb78; }
        .progress-medium { background: #ed8936; }
        .progress-high { background: #f56565; }
        
        .component-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .component {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: #2d3748;
            border-radius: 8px;
        }
        
        .component-name {
            font-weight: 500;
        }
        
        .component-status {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .alert {
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .alert-critical {
            background: rgba(245, 101, 101, 0.1);
            border-color: #f56565;
        }
        
        .alert-warning {
            background: rgba(237, 137, 54, 0.1);
            border-color: #ed8936;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #a0aec0;
        }
        
        .refresh-indicator {
            position: fixed;
            top: 1rem;
            right: 1rem;
            background: #4a5568;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.875rem;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Sophia Intel Health Dashboard</h1>
        <div class="subtitle">Real-time platform monitoring and health status</div>
    </div>
    
    <div class="refresh-indicator" id="refreshIndicator">
        <span id="refreshStatus">Loading...</span>
    </div>
    
    <div class="container">
        <div class="grid">
            <!-- System Metrics -->
            <div class="card">
                <h3>📊 System Metrics</h3>
                <div id="systemMetrics" class="loading">Loading system metrics...</div>
            </div>
            
            <!-- Health Summary -->
            <div class="card">
                <h3>🎯 Health Summary</h3>
                <div id="healthSummary" class="loading">Loading health summary...</div>
            </div>
            
            <!-- Alerts -->
            <div class="card">
                <h3>🚨 Active Alerts</h3>
                <div id="alerts" class="loading">Loading alerts...</div>
            </div>
        </div>
        
        <!-- Components -->
        <div class="card">
            <h3>🔧 Component Status</h3>
            <div id="components" class="loading">Loading components...</div>
        </div>
    </div>
    
    <script>
        let refreshInterval;
        
        function updateRefreshIndicator(status) {
            const indicator = document.getElementById('refreshStatus');
            indicator.textContent = status;
            
            if (status === 'Refreshing...') {
                indicator.classList.add('pulse');
            } else {
                indicator.classList.remove('pulse');
            }
        }
        
        function formatBytes(bytes) {
            const sizes = ['B', 'KB', 'MB', 'GB'];
            if (bytes === 0) return '0 B';
            const i = Math.floor(Math.log(bytes) / Math.log(1024));
            return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
        }
        
        function getProgressClass(value) {
            if (value < 60) return 'progress-low';
            if (value < 80) return 'progress-medium';
            return 'progress-high';
        }
        
        function getStatusClass(status) {
            return `status-${status}`;
        }
        
        async function fetchData(endpoint) {
            try {
                const response = await fetch(`/api/${endpoint}`);
                return await response.json();
            } catch (error) {
                console.error(`Error fetching ${endpoint}:`, error);
                return null;
            }
        }
        
        async function updateSystemMetrics() {
            const metrics = await fetchData('metrics');
            const container = document.getElementById('systemMetrics');
            
            if (!metrics) {
                container.innerHTML = '<div class="loading">Failed to load metrics</div>';
                return;
            }
            
            container.innerHTML = `
                <div class="metric">
                    <span class="metric-label">CPU Usage</span>
                    <span class="metric-value">${metrics.cpu_percent.toFixed(1)}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill ${getProgressClass(metrics.cpu_percent)}" 
                         style="width: ${metrics.cpu_percent}%"></div>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Memory Usage</span>
                    <span class="metric-value">${metrics.memory_percent.toFixed(1)}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill ${getProgressClass(metrics.memory_percent)}" 
                         style="width: ${metrics.memory_percent}%"></div>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Disk Usage</span>
                    <span class="metric-value">${metrics.disk_percent.toFixed(1)}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill ${getProgressClass(metrics.disk_percent)}" 
                         style="width: ${metrics.disk_percent}%"></div>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Processes</span>
                    <span class="metric-value">${metrics.process_count}</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Uptime</span>
                    <span class="metric-value">${(metrics.uptime_seconds / 3600).toFixed(1)}h</span>
                </div>
            `;
        }
        
        async function updateHealthSummary() {
            const health = await fetchData('health');
            const container = document.getElementById('healthSummary');
            
            if (!health || !health.summary) {
                container.innerHTML = '<div class="loading">Failed to load health data</div>';
                return;
            }
            
            const summary = health.summary;
            
            container.innerHTML = `
                <div class="metric">
                    <span class="metric-label">Overall Score</span>
                    <span class="metric-value">${summary.overall_health_score.toFixed(1)}%</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">✅ Healthy</span>
                    <span class="metric-value status-healthy">${summary.healthy}</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">⚠️ Degraded</span>
                    <span class="metric-value status-degraded">${summary.degraded}</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">❌ Unhealthy</span>
                    <span class="metric-value status-unhealthy">${summary.unhealthy}</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">❓ Unknown</span>
                    <span class="metric-value status-unknown">${summary.unknown}</span>
                </div>
            `;
        }
        
        async function updateAlerts() {
            const alerts = await fetchData('alerts');
            const container = document.getElementById('alerts');
            
            if (!alerts) {
                container.innerHTML = '<div class="loading">Failed to load alerts</div>';
                return;
            }
            
            if (alerts.length === 0) {
                container.innerHTML = '<div style="text-align: center; color: #48bb78;">✅ No active alerts</div>';
                return;
            }
            
            container.innerHTML = alerts.map(alert => `
                <div class="alert alert-${alert.type}">
                    <strong>${alert.component}</strong><br>
                    ${alert.message}
                    <div style="font-size: 0.875rem; opacity: 0.8; margin-top: 0.5rem;">
                        ${new Date(alert.timestamp).toLocaleString()}
                    </div>
                </div>
            `).join('');
        }
        
        async function updateComponents() {
            const components = await fetchData('components');
            const container = document.getElementById('components');
            
            if (!components) {
                container.innerHTML = '<div class="loading">Failed to load components</div>';
                return;
            }
            
            container.innerHTML = `
                <div class="component-list">
                    ${components.map(comp => `
                        <div class="component">
                            <div>
                                <div class="component-name">${comp.name}</div>
                                ${comp.response_time ? `<div style="font-size: 0.875rem; color: #a0aec0;">${comp.response_time.toFixed(0)}ms</div>` : ''}
                                ${comp.error ? `<div style="font-size: 0.875rem; color: #f56565;">${comp.error}</div>` : ''}
                            </div>
                            <div class="component-status ${getStatusClass(comp.status)}">
                                ${comp.status.toUpperCase()}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        async function refreshDashboard() {
            updateRefreshIndicator('Refreshing...');
            
            await Promise.all([
                updateSystemMetrics(),
                updateHealthSummary(),
                updateAlerts(),
                updateComponents()
            ]);
            
            updateRefreshIndicator(`Last updated: ${new Date().toLocaleTimeString()}`);
        }
        
        // Initial load
        refreshDashboard();
        
        // Auto-refresh every 30 seconds
        refreshInterval = setInterval(refreshDashboard, 30000);
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        });
    </script>
</body>
</html>"""
        
        with open(template_dir / "dashboard.html", 'w') as f:
            f.write(dashboard_html)
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the dashboard"""
        # Create template
        self.create_dashboard_template()
        
        # Start monitoring
        self.start_monitoring()
        
        try:
            print(f"🚀 Starting Sophia Intel Health Dashboard on http://{host}:{port}")
            self.app.run(host=host, port=port, debug=debug, threaded=True)
        finally:
            self.stop_monitoring()


def main():
    """Main dashboard runner"""
    dashboard = HealthDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()

