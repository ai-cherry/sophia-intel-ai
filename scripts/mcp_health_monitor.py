#!/usr/bin/env python3
"""
MCP Health Monitor - Continuous monitoring and auto-recovery for MCP servers
Production-ready with metrics collection and automatic deduplication
"""

import json
import time
import psutil
import requests
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import signal
import sys

# Setup logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "mcp_health_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MCPHealthMonitor")

# MCP Server Configuration
MCP_SERVERS = {
    "memory": {
        "port": 8081,
        "name": "Memory Server",
        "module": "mcp.memory_server:app",
        "pid_file": ".pids/mcp-memory.pid",
        "log_file": "logs/mcp-memory.log",
        "health_endpoint": "/health",
        "restart_threshold": 3,
        "restart_count": 0
    },
    "filesystem": {
        "port": 8082,
        "name": "Filesystem Server", 
        "module": "mcp.filesystem.server:app",
        "pid_file": ".pids/mcp-filesystem.pid",
        "log_file": "logs/mcp-filesystem.log",
        "health_endpoint": "/health",
        "restart_threshold": 3,
        "restart_count": 0
    },
    "git": {
        "port": 8084,
        "name": "Git Server",
        "module": "mcp.git.server:app",
        "pid_file": ".pids/mcp-git.pid",
        "log_file": "logs/mcp-git.log",
        "health_endpoint": "/health",
        "restart_threshold": 3,
        "restart_count": 0
    }
}

# Metrics storage
METRICS_FILE = LOG_DIR / "mcp_health_metrics.json"

class MCPHealthMonitor:
    """Production-ready MCP health monitoring with auto-recovery"""
    
    def __init__(self):
        self.running = True
        self.metrics = self._load_metrics()
        self.check_interval = 30  # seconds
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
    def _handle_shutdown(self, signum, frame):
        """Graceful shutdown handler"""
        logger.info("Received shutdown signal, stopping monitor...")
        self.running = False
        self._save_metrics()
        sys.exit(0)
        
    def _load_metrics(self) -> Dict:
        """Load existing metrics or create new"""
        if METRICS_FILE.exists():
            try:
                with open(METRICS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metrics: {e}")
        
        return {
            "start_time": datetime.now().isoformat(),
            "checks_performed": 0,
            "restarts": {},
            "uptime": {},
            "last_check": None
        }
    
    def _save_metrics(self):
        """Save metrics to file"""
        try:
            self.metrics["last_check"] = datetime.now().isoformat()
            with open(METRICS_FILE, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def _find_duplicate_processes(self, port: int) -> List[int]:
        """Find duplicate processes on the same port"""
        duplicates = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if process is using the port
                for conn in proc.connections(kind='inet'):
                    if conn.laddr.port == port and proc.pid not in duplicates:
                        duplicates.append(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return duplicates
    
    def _kill_duplicates(self, server_name: str, port: int, keep_pid: Optional[int] = None):
        """Kill duplicate processes except the one we want to keep"""
        duplicates = self._find_duplicate_processes(port)
        
        if len(duplicates) > 1:
            logger.warning(f"Found {len(duplicates)} processes on port {port}")
            for pid in duplicates:
                if pid != keep_pid:
                    try:
                        logger.info(f"Killing duplicate process {pid} for {server_name}")
                        psutil.Process(pid).terminate()
                        time.sleep(1)
                        if psutil.pid_exists(pid):
                            psutil.Process(pid).kill()
                    except Exception as e:
                        logger.error(f"Failed to kill process {pid}: {e}")
    
    def _check_health(self, server_key: str, config: Dict) -> Tuple[bool, str]:
        """Check health of a single MCP server"""
        try:
            url = f"http://localhost:{config['port']}{config['health_endpoint']}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                # Check response content
                try:
                    data = response.json()
                    if data.get("status") == "healthy" or "healthy" in str(data):
                        return True, "healthy"
                except:
                    # If not JSON, check text
                    if "healthy" in response.text.lower():
                        return True, "healthy"
                
                return False, f"unhealthy response: {response.text[:100]}"
            else:
                return False, f"status code {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "connection refused"
        except requests.exceptions.Timeout:
            return False, "timeout"
        except Exception as e:
            return False, str(e)
    
    def _get_pid_from_file(self, pid_file: str) -> Optional[int]:
        """Get PID from pid file"""
        pid_path = Path(pid_file)
        if pid_path.exists():
            try:
                with open(pid_path, 'r') as f:
                    return int(f.read().strip())
            except:
                pass
        return None
    
    def _restart_server(self, server_key: str, config: Dict) -> bool:
        """Restart a failed MCP server"""
        logger.warning(f"Attempting to restart {config['name']}")
        
        # First, clean up any existing processes
        self._kill_duplicates(config['name'], config['port'])
        time.sleep(2)
        
        # Increment restart count
        config['restart_count'] += 1
        if server_key not in self.metrics['restarts']:
            self.metrics['restarts'][server_key] = []
        self.metrics['restarts'][server_key].append(datetime.now().isoformat())
        
        # Check if we've exceeded restart threshold
        if config['restart_count'] >= config['restart_threshold']:
            logger.error(f"{config['name']} has exceeded restart threshold ({config['restart_threshold']})")
            return False
        
        # Create pid directory if needed
        Path(".pids").mkdir(exist_ok=True)
        
        # Start the server
        try:
            cmd = [
                "python3", "-m", "uvicorn", config['module'],
                "--host", "0.0.0.0", 
                "--port", str(config['port'])
            ]
            
            # Start process in background
            log_path = Path(config['log_file'])
            log_path.parent.mkdir(exist_ok=True)
            
            with open(log_path, 'a') as log_file:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            
            # Save PID
            with open(config['pid_file'], 'w') as f:
                f.write(str(process.pid))
            
            # Wait for server to start
            time.sleep(3)
            
            # Verify it's running
            is_healthy, status = self._check_health(server_key, config)
            if is_healthy:
                logger.info(f"Successfully restarted {config['name']}")
                config['restart_count'] = 0  # Reset on successful restart
                return True
            else:
                logger.error(f"Failed to restart {config['name']}: {status}")
                return False
                
        except Exception as e:
            logger.error(f"Exception while restarting {config['name']}: {e}")
            return False
    
    def _update_uptime(self, server_key: str, is_up: bool):
        """Update server uptime metrics"""
        if server_key not in self.metrics['uptime']:
            self.metrics['uptime'][server_key] = {
                "total_checks": 0,
                "successful_checks": 0,
                "uptime_percentage": 0.0,
                "last_down": None,
                "last_up": None
            }
        
        stats = self.metrics['uptime'][server_key]
        stats['total_checks'] += 1
        
        if is_up:
            stats['successful_checks'] += 1
            stats['last_up'] = datetime.now().isoformat()
        else:
            stats['last_down'] = datetime.now().isoformat()
        
        stats['uptime_percentage'] = (stats['successful_checks'] / stats['total_checks']) * 100
    
    def check_all_servers(self):
        """Check health of all MCP servers"""
        logger.info("Performing health check on all MCP servers")
        self.metrics['checks_performed'] += 1
        
        status_summary = []
        all_healthy = True
        
        for server_key, config in MCP_SERVERS.items():
            # Kill any duplicates first
            self._kill_duplicates(config['name'], config['port'])
            
            # Check health
            is_healthy, status = self._check_health(server_key, config)
            
            # Update metrics
            self._update_uptime(server_key, is_healthy)
            
            if is_healthy:
                logger.info(f"✅ {config['name']} on port {config['port']}: {status}")
                status_summary.append(f"✅ {config['name']}: healthy")
            else:
                logger.warning(f"❌ {config['name']} on port {config['port']}: {status}")
                status_summary.append(f"❌ {config['name']}: {status}")
                all_healthy = False
                
                # Attempt restart
                if self._restart_server(server_key, config):
                    status_summary[-1] = f"🔄 {config['name']}: restarted successfully"
                else:
                    status_summary[-1] = f"🚨 {config['name']}: restart failed"
        
        # Save metrics after each check
        self._save_metrics()
        
        # Create dashboard-ready status file
        dashboard_status = {
            "timestamp": datetime.now().isoformat(),
            "all_healthy": all_healthy,
            "servers": status_summary,
            "metrics": {
                "checks_performed": self.metrics['checks_performed'],
                "uptime": self.metrics['uptime']
            }
        }
        
        with open(LOG_DIR / "mcp_status.json", 'w') as f:
            json.dump(dashboard_status, f, indent=2)
        
        return all_healthy
    
    def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        logger.info("Starting continuous MCP health monitoring")
        logger.info(f"Check interval: {self.check_interval} seconds")
        
        while self.running:
            try:
                self.check_all_servers()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Brief pause before retrying
        
        logger.info("MCP health monitoring stopped")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Health Monitor")
    parser.add_argument("--once", action="store_true", help="Run single check and exit")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon process")
    
    args = parser.parse_args()
    
    monitor = MCPHealthMonitor()
    
    if args.interval:
        monitor.check_interval = args.interval
    
    if args.once:
        # Single check mode
        all_healthy = monitor.check_all_servers()
        sys.exit(0 if all_healthy else 1)
    elif args.daemon:
        # Daemon mode - detach from terminal
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process
                print(f"Started MCP health monitor daemon (PID: {pid})")
                sys.exit(0)
        except OSError as e:
            logger.error(f"Failed to create daemon: {e}")
            sys.exit(1)
        
        # Child process continues
        monitor.run_continuous_monitoring()
    else:
        # Normal mode
        monitor.run_continuous_monitoring()

if __name__ == "__main__":
    import os
    main()