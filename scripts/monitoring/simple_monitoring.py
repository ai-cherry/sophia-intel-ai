#!/usr/bin/env python3
"""
Simple Sophia AI Monitoring Script
No complex dependencies, just basic health checks and logging
"""
import datetime
import json
import time
import requests
# Simple configuration
ENDPOINTS = [
    "http://www.sophia-intel.ai/health",
    "http://www.sophia-intel.ai/",
    "http://api.sophia-intel.ai/health",
]
LOG_FILE = "/tmp/sophia_monitoring.log"
CHECK_INTERVAL = 300  # 5 minutes
def log_message(message, level="INFO"):
    """Simple logging function"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {level}: {message}"
    print(log_entry)
    # Append to log file
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")
def check_endpoint(url, timeout=10):
    """Simple endpoint health check"""
    try:
        response = requests.get(url, timeout=timeout)
        status = "UP" if response.status_code == 200 else "DOWN"
        response_time = response.elapsed.total_seconds()
        return {
            "url": url,
            "status": status,
            "status_code": response.status_code,
            "response_time": response_time,
            "timestamp": datetime.datetime.now().isoformat(),
        }
    except requests.exceptions.RequestException as e:
        return {
            "url": url,
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat(),
        }
def run_health_checks():
    """Run health checks on all endpoints"""
    log_message("Starting health checks...")
    results = []
    for endpoint in ENDPOINTS:
        result = check_endpoint(endpoint)
        results.append(result)
        if result["status"] == "UP":
            log_message(f"✅ {endpoint} - OK ({result.get('response_time', 0):.2f}s)")
        else:
            log_message(f"❌ {endpoint} - {result['status']}", "ERROR")
    return results
def save_status_report(results):
    """Save simple status report"""
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "summary": {
            "total_endpoints": len(results),
            "healthy_endpoints": len([r for r in results if r["status"] == "UP"]),
            "unhealthy_endpoints": len([r for r in results if r["status"] != "UP"]),
        },
        "endpoints": results,
    }
    # Save to simple JSON file
    status_file = "/tmp/sophia_status.json"
    with open(status_file, "w") as f:
        json.dump(report, f, indent=2)
    log_message(f"Status report saved to {status_file}")
    return report
def main():
    """Main monitoring function"""
    log_message("🚀 Starting Sophia AI Simple Monitoring")
    log_message(f"Monitoring {len(ENDPOINTS)} endpoints every {CHECK_INTERVAL} seconds")
    try:
        while True:
            # Run health checks
            results = run_health_checks()
            # Save status report
            report = save_status_report(results)
            # Simple alerting - log if any endpoints are down
            unhealthy = report["summary"]["unhealthy_endpoints"]
            if unhealthy > 0:
                log_message(
                    f"⚠️  ALERT: {unhealthy} endpoints are unhealthy!", "WARNING"
                )
            else:
                log_message("✅ All endpoints healthy")
            # Wait for next check
            log_message(f"Next check in {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        log_message("Monitoring stopped by user")
    except Exception as e:
        log_message(f"Monitoring error: {e}", "ERROR")
if __name__ == "__main__":
    main()
