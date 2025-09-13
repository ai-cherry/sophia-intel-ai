#!/usr/bin/env python3
"""
Health Monitor and Auto-Recovery System for Sophia Intel AI
Provides continuous monitoring and automatic recovery for all services
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
import psutil
import redis.asyncio as redis
from pydantic import BaseModel, Field

# Service Configuration
class ServiceConfig(BaseModel):
    """Configuration for a monitored service"""
    name: str
    port: int
    health_endpoint: str = "/health"
    process_name: Optional[str] = None
    restart_command: Optional[str] = None
    max_restarts: int = 3
    restart_delay: int = 5
    memory_limit_mb: int = 2048
    cpu_limit_percent: int = 80


class HealthStatus(BaseModel):
    """Health status for a service"""
    service: str
    healthy: bool
    response_time_ms: Optional[float] = None
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    last_check: datetime = Field(default_factory=datetime.now)
    consecutive_failures: int = 0
    restart_count: int = 0
    error: Optional[str] = None


class HealthMonitor:
    """Monitors and recovers services automatically"""
    
    def __init__(self, environment: str = "local"):
        self.environment = environment
        self.redis_client: Optional[redis.Redis] = None
        self.services = self._load_service_config()
        self.status: Dict[str, HealthStatus] = {}
        self.running = False
        
    def _load_service_config(self) -> List[ServiceConfig]:
        """Load service configuration based on environment"""
        base_services = [
            ServiceConfig(
                name="Bridge API",
                port=8003,
                process_name="uvicorn",
                restart_command="cd /app && uvicorn bridge.api:app --host 0.0.0.0 --port 8003"
            ),
            ServiceConfig(
                name="MCP Memory",
                port=8081,
                process_name="python.*memory_server",
                restart_command="cd /app && python -m mcp.memory_server"
            ),
            ServiceConfig(
                name="MCP Filesystem",
                port=8082,
                process_name="python.*filesystem",
                restart_command="cd /app && python -m mcp.filesystem"
            ),
            ServiceConfig(
                name="MCP Git",
                port=8084,
                process_name="python.*git_server",
                restart_command="cd /app && python -m mcp.git_server"
            ),
        ]
        
        if self.environment == "local":
            base_services.extend([
                ServiceConfig(
                    name="Agent UI",
                    port=3000,
                    health_endpoint="/",
                    process_name="node.*next",
                    restart_command="cd /app/sophia-intel-app && npm run start"
                ),
                ServiceConfig(
                    name="Redis",
                    port=6379,
                    health_endpoint="",  # Use custom check
                    process_name="redis-server",
                    restart_command="redis-server --daemonize yes"
                ),
                ServiceConfig(
                    name="PostgreSQL",
                    port=5432,
                    health_endpoint="",  # Use custom check
                    process_name="postgres",
                    restart_command="brew services restart postgresql@16"
                ),
            ])
        
        return base_services
    
    async def connect_redis(self):
        """Connect to Redis for storing health metrics"""
        try:
            self.redis_client = redis.Redis(
                host="localhost",
                port=6379,
                db=3,  # Use DB 3 for health metrics
                decode_responses=True
            )
            await self.redis_client.ping()
            print("✅ Connected to Redis for health metrics")
        except Exception as e:
            print(f"⚠️  Redis not available for metrics: {e}")
            self.redis_client = None
    
    async def check_http_health(self, service: ServiceConfig) -> Tuple[bool, float, Optional[str]]:
        """Check HTTP health endpoint"""
        url = f"http://localhost:{service.port}{service.health_endpoint}"
        
        try:
            start = time.time()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                elapsed = (time.time() - start) * 1000  # Convert to ms
                
                if response.status_code == 200:
                    return True, elapsed, None
                else:
                    return False, elapsed, f"HTTP {response.status_code}"
        except Exception as e:
            return False, 0, str(e)
    
    async def check_redis_health(self) -> Tuple[bool, float, Optional[str]]:
        """Check Redis health"""
        try:
            start = time.time()
            test_client = redis.Redis(host="localhost", port=6379)
            await test_client.ping()
            elapsed = (time.time() - start) * 1000
            await test_client.aclose()
            return True, elapsed, None
        except Exception as e:
            return False, 0, str(e)
    
    async def check_postgres_health(self) -> Tuple[bool, float, Optional[str]]:
        """Check PostgreSQL health"""
        try:
            start = time.time()
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5432"],
                capture_output=True,
                timeout=5
            )
            elapsed = (time.time() - start) * 1000
            
            if result.returncode == 0:
                return True, elapsed, None
            else:
                return False, elapsed, result.stderr.decode()
        except Exception as e:
            return False, 0, str(e)
    
    def get_process_stats(self, process_name: str) -> Tuple[Optional[float], Optional[float]]:
        """Get memory and CPU usage for a process"""
        try:
            for proc in psutil.process_iter(['name', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    # Check if process matches
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if process_name in cmdline or proc.info['name'] == process_name:
                        memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                        cpu_percent = proc.cpu_percent(interval=0.1)
                        return memory_mb, cpu_percent
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return None, None
    
    async def check_service(self, service: ServiceConfig) -> HealthStatus:
        """Check health of a single service"""
        # Get previous status
        prev_status = self.status.get(service.name, HealthStatus(service=service.name, healthy=True))
        
        # Special handling for Redis and PostgreSQL
        if service.name == "Redis":
            healthy, response_time, error = await self.check_redis_health()
        elif service.name == "PostgreSQL":
            healthy, response_time, error = await self.check_postgres_health()
        else:
            healthy, response_time, error = await self.check_http_health(service)
        
        # Get process stats if available
        memory_mb, cpu_percent = None, None
        if service.process_name:
            memory_mb, cpu_percent = self.get_process_stats(service.process_name)
        
        # Update status
        status = HealthStatus(
            service=service.name,
            healthy=healthy,
            response_time_ms=response_time if healthy else None,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            consecutive_failures=0 if healthy else prev_status.consecutive_failures + 1,
            restart_count=prev_status.restart_count,
            error=error
        )
        
        # Check resource limits
        if memory_mb and memory_mb > service.memory_limit_mb:
            status.healthy = False
            status.error = f"Memory limit exceeded: {memory_mb:.1f}MB > {service.memory_limit_mb}MB"
        
        if cpu_percent and cpu_percent > service.cpu_limit_percent:
            status.healthy = False
            status.error = f"CPU limit exceeded: {cpu_percent:.1f}% > {service.cpu_limit_percent}%"
        
        return status
    
    async def restart_service(self, service: ServiceConfig) -> bool:
        """Restart a failed service"""
        if not service.restart_command:
            print(f"❌ No restart command for {service.name}")
            return False
        
        print(f"🔄 Restarting {service.name}...")
        
        try:
            # Kill existing process if needed
            if service.process_name:
                subprocess.run(f"pkill -f '{service.process_name}'", shell=True)
                await asyncio.sleep(2)
            
            # Start service
            subprocess.Popen(
                service.restart_command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for service to start
            await asyncio.sleep(service.restart_delay)
            
            # Verify it's running
            status = await self.check_service(service)
            if status.healthy:
                print(f"✅ {service.name} restarted successfully")
                return True
            else:
                print(f"❌ {service.name} failed to restart")
                return False
                
        except Exception as e:
            print(f"❌ Error restarting {service.name}: {e}")
            return False
    
    async def store_metrics(self, status: HealthStatus):
        """Store health metrics in Redis"""
        if not self.redis_client:
            return
        
        try:
            # Store current status
            key = f"health:{status.service}:current"
            await self.redis_client.hset(
                key,
                mapping={
                    "healthy": "1" if status.healthy else "0",
                    "response_time_ms": status.response_time_ms or 0,
                    "memory_mb": status.memory_mb or 0,
                    "cpu_percent": status.cpu_percent or 0,
                    "consecutive_failures": status.consecutive_failures,
                    "restart_count": status.restart_count,
                    "last_check": status.last_check.isoformat(),
                    "error": status.error or ""
                }
            )
            
            # Store time series data (keep 24 hours)
            ts_key = f"health:{status.service}:timeseries"
            ts_data = json.dumps({
                "timestamp": status.last_check.isoformat(),
                "healthy": status.healthy,
                "response_time_ms": status.response_time_ms,
                "memory_mb": status.memory_mb,
                "cpu_percent": status.cpu_percent
            })
            
            await self.redis_client.zadd(
                ts_key,
                {ts_data: status.last_check.timestamp()}
            )
            
            # Remove old entries (older than 24 hours)
            cutoff = (datetime.now() - timedelta(days=1)).timestamp()
            await self.redis_client.zremrangebyscore(ts_key, 0, cutoff)
            
        except Exception as e:
            print(f"⚠️  Failed to store metrics: {e}")
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        print("🏥 Starting health monitoring...")
        
        while self.running:
            for service_config in self.services:
                try:
                    # Check service health
                    status = await self.check_service(service_config)
                    self.status[service_config.name] = status
                    
                    # Store metrics
                    await self.store_metrics(status)
                    
                    # Handle unhealthy services
                    if not status.healthy:
                        print(f"⚠️  {service_config.name} is unhealthy: {status.error}")
                        
                        # Auto-restart if configured
                        if (status.consecutive_failures >= 3 and 
                            status.restart_count < service_config.max_restarts):
                            
                            success = await self.restart_service(service_config)
                            if success:
                                status.restart_count += 1
                                status.consecutive_failures = 0
                                self.status[service_config.name] = status
                    else:
                        # Reset consecutive failures on success
                        if status.consecutive_failures > 0:
                            print(f"✅ {service_config.name} recovered")
                
                except Exception as e:
                    print(f"❌ Error monitoring {service_config.name}: {e}")
            
            # Wait before next check
            await asyncio.sleep(10)
    
    async def start(self):
        """Start monitoring"""
        self.running = True
        await self.connect_redis()
        await self.monitor_loop()
    
    async def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.redis_client:
            await self.redis_client.close()
    
    def print_status(self):
        """Print current status table"""
        print("\n" + "="*80)
        print(f"Health Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        for service_name, status in self.status.items():
            health = "✅" if status.healthy else "❌"
            response = f"{status.response_time_ms:.1f}ms" if status.response_time_ms else "N/A"
            memory = f"{status.memory_mb:.1f}MB" if status.memory_mb else "N/A"
            cpu = f"{status.cpu_percent:.1f}%" if status.cpu_percent else "N/A"
            
            print(f"{health} {service_name:20} | Response: {response:10} | Memory: {memory:10} | CPU: {cpu:8}")
            if status.error:
                print(f"   └─ Error: {status.error}")
        
        print("="*80)


async def main():
    """Main entry point"""
    # Determine environment
    environment = os.getenv("DEPLOYMENT_ENV", "local")
    
    # Create monitor
    monitor = HealthMonitor(environment=environment)
    
    # Handle shutdown
    import signal
    
    def shutdown(sig, frame):
        print("\n🛑 Stopping health monitor...")
        asyncio.create_task(monitor.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    # Start monitoring
    try:
        # Print initial status
        print(f"🏥 Health Monitor for Sophia Intel AI")
        print(f"Environment: {environment}")
        print(f"Monitoring {len(monitor.services)} services")
        print("Press Ctrl+C to stop\n")
        
        # Run monitor with periodic status prints
        monitor_task = asyncio.create_task(monitor.start())
        
        while True:
            await asyncio.sleep(30)
            monitor.print_status()
            
    except KeyboardInterrupt:
        await monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())