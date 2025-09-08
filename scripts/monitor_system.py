#!/usr/bin/env python3
"""
System Monitor Background Script
SOLO DEVELOPER USE ONLY - NOT FOR DISTRIBUTION

Monitors system resources, API endpoints, and service health.
Sends alerts if thresholds are exceeded.
"""

import os
import json
import time
import logging
import argparse
import datetime
import requests
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/system_monitor.log',
    filemode='a'
)
logger = logging.getLogger('system_monitor')

# Constants
CPU_THRESHOLD = 80.0        # Alert if CPU usage exceeds this percentage
MEMORY_THRESHOLD = 80.0     # Alert if memory usage exceeds this percentage
DISK_THRESHOLD = 85.0       # Alert if disk usage exceeds this percentage
API_TIMEOUT = 5             # Timeout for API health checks (seconds)
COST_THRESHOLD = 0.55       # $ per million tokens
RETENTION_DAYS = 7          # How long to keep monitoring data

def check_system_resources() -> Dict[str, Any]:
    """
    Check system CPU, memory, and disk usage
    """
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "alert": cpu_percent > CPU_THRESHOLD
            },
            "memory": {
                "total_gb": memory.total / (1024**3),
                "used_gb": memory.used / (1024**3),
                "percent": memory_percent,
                "alert": memory_percent > MEMORY_THRESHOLD
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3),
                "percent": disk_percent,
                "alert": disk_percent > DISK_THRESHOLD
            }
        }

        # Log alerts
        if result["cpu"]["alert"]:
            logger.warning(f"CPU usage alert: {cpu_percent}% (threshold: {CPU_THRESHOLD}%)")
        if result["memory"]["alert"]:
            logger.warning(f"Memory usage alert: {memory_percent}% (threshold: {MEMORY_THRESHOLD}%)")
        if result["disk"]["alert"]:
            logger.warning(f"Disk usage alert: {disk_percent}% (threshold: {DISK_THRESHOLD}%)")

        return result
    except Exception as e:
        logger.error(f"Error checking system resources: {e}")
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e),
            "cpu": {"percent": 0, "alert": False},
            "memory": {"percent": 0, "alert": False},
            "disk": {"percent": 0, "alert": False}
        }

def check_api_health() -> Dict[str, Any]:
    """
    Check health of API endpoints
    """
    endpoints = [
        {"name": "MCP Server", "url": "http://localhost:8000/health", "expected_status": 200},
        {"name": "OpenRouter", "url": "https://openrouter.ai/api/v1/auth/key", "expected_status": 200},
        {"name": "Portkey", "url": "https://api.portkey.ai/v1/health", "expected_status": 200},
        {"name": "Memory System", "url": "http://localhost:6333/health", "expected_status": 200},  # Qdrant
    ]

    results = {
        "timestamp": datetime.datetime.now().isoformat(),
        "endpoints": []
    }

    any_alert = False

    for endpoint in endpoints:
        try:
            headers = {}
            if "openrouter.ai" in endpoint["url"] and os.getenv("OPENROUTER_API_KEY"):
                headers["Authorization"] = f"Bearer {os.getenv('OPENROUTER_API_KEY')}"
            elif "portkey.ai" in endpoint["url"] and os.getenv("PORTKEY_API_KEY"):
                headers["x-portkey-api-key"] = os.getenv("PORTKEY_API_KEY")

            response = requests.get(endpoint["url"], headers=headers, timeout=API_TIMEOUT)
            status = "UP" if response.status_code == endpoint["expected_status"] else "DOWN"
            latency = response.elapsed.total_seconds() * 1000  # ms

            is_alert = status == "DOWN"

            if is_alert:
                any_alert = True
                logger.warning(f"API alert: {endpoint['name']} is {status} (status: {response.status_code})")

            results["endpoints"].append({
                "name": endpoint["name"],
                "status": status,
                "latency_ms": latency,
                "status_code": response.status_code,
                "alert": is_alert
            })
        except Exception as e:
            any_alert = True
            logger.warning(f"API alert: {endpoint['name']} is DOWN (error: {e})")

            results["endpoints"].append({
                "name": endpoint["name"],
                "status": "DOWN",
                "latency_ms": 0,
                "error": str(e),
                "alert": True
            })

    results["alert"] = any_alert
    return results

def check_processes() -> Dict[str, Any]:
    """
    Check for essential processes
    """
    processes = [
        {"name": "python", "pattern": "mcp_server.py", "critical": True},
        {"name": "streamlit", "pattern": "dashboard.py", "critical": False},
    ]

    results = {
        "timestamp": datetime.datetime.now().isoformat(),
        "processes": []
    }

    any_alert = False

    for proc in processes:
        try:
            # Use pgrep to find process
            cmd = f"pgrep -f '{proc['pattern']}'"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)

            is_running = result.returncode == 0
            is_alert = proc["critical"] and not is_running

            if is_alert:
                any_alert = True
                logger.warning(f"Process alert: {proc['name']} ({proc['pattern']}) is not running")

            results["processes"].append({
                "name": proc["name"],
                "pattern": proc["pattern"],
                "running": is_running,
                "critical": proc["critical"],
                "alert": is_alert
            })
        except Exception as e:
            logger.error(f"Error checking process {proc['name']}: {e}")
            any_alert = True if proc["critical"] else any_alert

            results["processes"].append({
                "name": proc["name"],
                "pattern": proc["pattern"],
                "running": False,
                "error": str(e),
                "critical": proc["critical"],
                "alert": proc["critical"]
            })

    results["alert"] = any_alert
    return results

def check_costs() -> Dict[str, Any]:
    """
    Check API costs and usage
    """
    # Try to load cached model rankings
    cache_dir = Path("cache")
    rankings_file = cache_dir / "model_rankings.json"

    if not rankings_file.exists():
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "error": "No model rankings data available",
            "alert": False
        }

    try:
        with open(rankings_file, "r") as f:
            models = json.load(f)

        # Find current models in use
        config_file = Path(".continue/config.json")
        if not config_file.exists():
            return {
                "timestamp": datetime.datetime.now().isoformat(),
                "error": "Continue config not found",
                "alert": False
            }

        with open(config_file, "r") as f:
            config = json.load(f)

        active_models = []
        for model in config.get("models", []):
            if model.get("provider") == "openrouter":
                model_id = model.get("model")
                # Find this model in rankings
                model_data = next((m for m in models if m.get("id") == model_id), None)
                if model_data:
                    active_models.append({
                        "name": model.get("title"),
                        "model_id": model_id,
                        "cost_per_million": model_data.get("cost_per_million", 0),
                        "above_threshold": model_data.get("cost_per_million", 0) > COST_THRESHOLD * 1000000
                    })

        # Check if any models are above threshold
        above_threshold = any(m["above_threshold"] for m in active_models)
        if above_threshold:
            logger.warning(f"Cost alert: Some models exceed cost threshold (${COST_THRESHOLD}/1M tokens)")

        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "active_models": active_models,
            "cost_threshold": COST_THRESHOLD,
            "alert": above_threshold
        }
    except Exception as e:
        logger.error(f"Error checking costs: {e}")
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e),
            "alert": False
        }

def save_metrics(system_data: Dict[str, Any], api_data: Dict[str, Any], 
                process_data: Dict[str, Any], cost_data: Dict[str, Any]):
    """
    Save metrics to file for dashboard to read
    """
    metrics_dir = Path("metrics")
    metrics_dir.mkdir(exist_ok=True)

    # Generate timestamp for filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Combine all data
    combined_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "system": system_data,
        "api": api_data,
        "processes": process_data,
        "costs": cost_data,
        "alert": (
            system_data.get("cpu", {}).get("alert", False) or
            system_data.get("memory", {}).get("alert", False) or
            system_data.get("disk", {}).get("alert", False) or
            api_data.get("alert", False) or
            process_data.get("alert", False) or
            cost_data.get("alert", False)
        )
    }

    # Save to file
    with open(metrics_dir / f"monitor_{timestamp}.json", "w") as f:
        json.dump(combined_data, f, indent=2)

    # Also save to latest.json for dashboard to read easily
    with open(metrics_dir / "latest.json", "w") as f:
        json.dump(combined_data, f, indent=2)

    # Clean up old metrics
    cleanup_old_metrics(metrics_dir)

def cleanup_old_metrics(metrics_dir: Path):
    """
    Clean up metrics files older than RETENTION_DAYS
    """
    retention_seconds = RETENTION_DAYS * 24 * 60 * 60
    current_time = time.time()

    for file in metrics_dir.glob("monitor_*.json"):
        if file.name == "latest.json":
            continue

        file_age = current_time - file.stat().st_mtime
        if file_age > retention_seconds:
            try:
                file.unlink()
                logger.debug(f"Deleted old metrics file: {file.name}")
            except Exception as e:
                logger.error(f"Error deleting old metrics file {file.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Monitor system resources and API health")
    parser.add_argument("--no-save", action="store_true", help="Don't save metrics to file")
    args = parser.parse_args()

    logger.info("Starting system monitoring")

    # Run checks
    system_data = check_system_resources()
    api_data = check_api_health()
    process_data = check_processes()
    cost_data = check_costs()

    # Save metrics unless disabled
    if not args.no_save:
        save_metrics(system_data, api_data, process_data, cost_data)

    # Log summary
    alerts = []
    if system_data.get("cpu", {}).get("alert", False):
        alerts.append(f"CPU: {system_data['cpu']['percent']}%")
    if system_data.get("memory", {}).get("alert", False):
        alerts.append(f"Memory: {system_data['memory']['percent']}%")
    if system_data.get("disk", {}).get("alert", False):
        alerts.append(f"Disk: {system_data['disk']['percent']}%")

    api_alerts = sum(1 for endpoint in api_data.get("endpoints", []) if endpoint.get("alert", False))
    if api_alerts > 0:
        alerts.append(f"API: {api_alerts} endpoints down")

    process_alerts = sum(1 for proc in process_data.get("processes", []) if proc.get("alert", False))
    if process_alerts > 0:
        alerts.append(f"Processes: {process_alerts} critical processes down")

    if cost_data.get("alert", False):
        alerts.append("Costs: Model costs above threshold")

    if alerts:
        logger.warning(f"Monitoring alerts: {', '.join(alerts)}")
    else:
        logger.info("Monitoring completed: All systems healthy")

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    main()
