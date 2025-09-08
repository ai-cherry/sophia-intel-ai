#!/usr/bin/env python3
"""
Telemetry endpoint for SOPHIA system monitoring.
Exposes budget status, circuit breaker state, and routing metrics.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agno_core.adapters.budget import BudgetManager
from agno_core.adapters.circuit_breaker import CircuitBreaker
from agno_core.adapters.telemetry import Telemetry
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:3001"])

# Initialize components
budget_manager = BudgetManager()
circuit_breaker = CircuitBreaker()
telemetry = Telemetry(echo_stdout=False)  # Disable stdout logging

# Background thread for simulating telemetry events (remove in production)
def simulate_events():
    """Simulate telemetry events for testing"""
    while True:
        time.sleep(5)
        # Simulate route decision event
        telemetry.emit({
            "type": "route_decision",
            "data": {
                "primary": "gpt-4-turbo",
                "fallbacks": ["claude-3", "gpt-3.5"],
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Simulate budget usage
        budget_manager.add_usage("gpt-4-turbo", 0.01)  # Add 1 cent usage

# Start simulation in background (for demo purposes)
threading.Thread(target=simulate_events, daemon=True).start()

@app.route('/api/telemetry/snapshot', methods=['GET'])
def telemetry_snapshot():
    """Get current telemetry snapshot"""
    events = telemetry.snapshot()
    
    return jsonify({
        "success": True,
        "data": {
            "events": events,
            "timestamp": datetime.now().isoformat(),
            "event_count": len(events)
        }
    })

@app.route('/api/telemetry/budgets', methods=['GET'])
def budget_status():
    """Get current budget status for all VKs"""
    budgets = {}
    
    # Get all configured VKs from the loaded limits
    for vk_name, limit in budget_manager.limits.items():
        usage = budget_manager.get_usage(vk_name)
        status = budget_manager.check_status(vk_name)
        
        budgets[vk_name] = {
            "status": status,
            "usage_usd": usage,
            "soft_cap_usd": limit.soft_cap_usd,
            "hard_cap_usd": limit.hard_cap_usd,
            "soft_cap_percentage": (usage / limit.soft_cap_usd * 100) if limit.soft_cap_usd > 0 else 0,
            "hard_cap_percentage": (usage / limit.hard_cap_usd * 100) if limit.hard_cap_usd > 0 else 0
        }
    
    # Add some test data if no budgets configured
    if not budgets:
        test_vks = ["gpt-4-turbo", "claude-3-opus", "gpt-3.5-turbo"]
        for vk in test_vks:
            usage = budget_manager.get_usage(vk)
            budgets[vk] = {
                "status": "allow",
                "usage_usd": usage,
                "soft_cap_usd": 10.0,
                "hard_cap_usd": 50.0,
                "soft_cap_percentage": usage / 10.0 * 100,
                "hard_cap_percentage": usage / 50.0 * 100
            }
    
    return jsonify({
        "success": True,
        "data": {
            "budgets": budgets,
            "timestamp": datetime.now().isoformat()
        }
    })

@app.route('/api/telemetry/circuits', methods=['GET'])
def circuit_status():
    """Get circuit breaker status for all VKs"""
    circuits = {}
    
    # Check common VKs (expand this based on your config)
    vk_list = ["gpt-4-turbo", "gpt-4", "claude-3-opus", "claude-3-sonnet", 
               "gpt-3.5-turbo", "mistral-large"]
    
    for vk in vk_list:
        is_open = circuit_breaker.is_open(vk)
        state = circuit_breaker._state.get(vk)
        failures = state.failures if state else 0
        open_until = state.open_until if state else 0
        
        circuits[vk] = {
            "state": "open" if is_open else "closed",
            "failures": failures,
            "open_until": datetime.fromtimestamp(open_until).isoformat() if open_until > 0 else None,
            "threshold": circuit_breaker.failure_threshold,
            "cooldown_seconds": circuit_breaker.cooldown_seconds
        }
    
    return jsonify({
        "success": True,
        "data": {
            "circuits": circuits,
            "timestamp": datetime.now().isoformat()
        }
    })

@app.route('/api/telemetry/metrics', methods=['GET'])
def routing_metrics():
    """Get aggregated routing metrics from telemetry"""
    events = telemetry.snapshot()
    
    # Aggregate metrics
    metrics = {
        "total_routes": 0,
        "cb_blocks": 0,
        "budget_blocks": 0,
        "route_distribution": {},
        "fallback_usage": 0
    }
    
    for event in events:
        event_type = event.get("type")
        if event_type == "route_decision":
            metrics["total_routes"] += 1
            data = event.get("data", {})
            primary = data.get("primary")
            if primary:
                metrics["route_distribution"][primary] = \
                    metrics["route_distribution"].get(primary, 0) + 1
            if data.get("fallbacks"):
                metrics["fallback_usage"] += 1
        elif event_type == "cb_open":
            metrics["cb_blocks"] += 1
        elif event_type == "budget_blocked":
            metrics["budget_blocks"] += 1
    
    return jsonify({
        "success": True,
        "data": {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    })

@app.route('/api/telemetry/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "success": True,
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/telemetry/simulate/failure/<vk>', methods=['POST'])
def simulate_failure(vk):
    """Simulate a failure for testing circuit breaker"""
    circuit_breaker.on_error(vk)  # Use the correct method name
    telemetry.emit({
        "type": "simulated_failure",
        "data": {
            "vk": vk,
            "timestamp": datetime.now().isoformat()
        }
    })
    state = circuit_breaker._state.get(vk)
    failures = state.failures if state else 0
    return jsonify({
        "success": True,
        "message": f"Simulated failure for {vk}",
        "failures": failures,
        "is_open": circuit_breaker.is_open(vk)
    })

@app.route('/api/telemetry/simulate/spend/<vk>/<amount>', methods=['POST'])
def simulate_spend(vk, amount):
    """Simulate budget spend for testing"""
    amount_usd = float(amount)
    budget_manager.add_usage(vk, amount_usd)
    telemetry.emit({
        "type": "simulated_spend",
        "data": {
            "vk": vk,
            "amount_usd": amount_usd,
            "timestamp": datetime.now().isoformat()
        }
    })
    return jsonify({
        "success": True,
        "message": f"Added ${amount_usd} to {vk}",
        "current_usage": budget_manager.get_usage(vk),
        "status": budget_manager.check_status(vk)
    })

if __name__ == '__main__':
    print("🚀 Starting SOPHIA Telemetry Service on http://localhost:5003")
    print("📊 Available endpoints:")
    print("  - GET /api/telemetry/snapshot - Recent telemetry events")
    print("  - GET /api/telemetry/budgets - Budget usage and limits")
    print("  - GET /api/telemetry/circuits - Circuit breaker states")
    print("  - GET /api/telemetry/metrics - Aggregated routing metrics")
    print("  - GET /api/telemetry/health - Health check")
    print("  - POST /api/telemetry/simulate/failure/<vk> - Simulate failure")
    print("  - POST /api/telemetry/simulate/spend/<vk>/<amount> - Simulate spend")
    
    app.run(host='0.0.0.0', port=5003, debug=False)  # Changed port to 5003 and disable debug