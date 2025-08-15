#!/usr/bin/env python3
"""
Sophia Intel Production Monitoring System
Comprehensive monitoring for all platform components
"""

import asyncio
import json
import os
import sys
import time
import psutil
import docker
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
import requests
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status for a component"""
    name: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    last_check: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemMetrics:
    """System-level metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    uptime_seconds: float
    timestamp: str


class SophiaIntelMonitor:
    """Comprehensive monitoring system for Sophia Intel platform"""
    
    def __init__(self):
        self.docker_client = None
        self.session = None
        self.monitoring_results = {}
        
        # Component endpoints
        self.endpoints = {
            "airbyte_server": "http://localhost:8000/api/v1/health",
            "airbyte_webapp": "http://localhost:8080",
            "minio": "http://localhost:9000/minio/health/live",
            "qdrant": os.getenv('QDRANT_URL', 'https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io'),
            "neon_postgres": None,  # Will be checked via connection
            "redis": None  # Will be checked via connection
        }
        
        # Expected Docker containers
        self.expected_containers = [
            "airbyte-airbyte-server-1",
            "airbyte-airbyte-worker-1",
            "airbyte-airbyte-webapp-1",
            "airbyte-airbyte-temporal-1",
            "airbyte-airbyte-db-1",
            "airbyte-minio-1"
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.docker_client:
            self.docker_client.close()
    
    async def check_http_endpoint(self, name: str, url: str, expected_status: int = 200) -> ComponentHealth:
        """Check HTTP endpoint health"""
        start_time = time.time()
        
        try:
            async with self.session.get(url) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == expected_status:
                    return ComponentHealth(
                        name=name,
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        last_check=datetime.utcnow().isoformat(),
                        metadata={"status_code": response.status, "url": url}
                    )
                else:
                    return ComponentHealth(
                        name=name,
                        status=HealthStatus.DEGRADED,
                        response_time_ms=response_time,
                        last_check=datetime.utcnow().isoformat(),
                        error_message=f"Unexpected status code: {response.status}",
                        metadata={"status_code": response.status, "url": url}
                    )
                    
        except asyncio.TimeoutError:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow().isoformat(),
                error_message="Request timeout",
                metadata={"url": url}
            )
        except Exception as e:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow().isoformat(),
                error_message=str(e),
                metadata={"url": url}
            )
    
    def check_docker_containers(self) -> List[ComponentHealth]:
        """Check Docker container health"""
        container_health = []
        
        if not self.docker_client:
            return [ComponentHealth(
                name="docker_client",
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow().isoformat(),
                error_message="Docker client not available"
            )]
        
        try:
            containers = self.docker_client.containers.list(all=True)
            container_map = {c.name: c for c in containers}
            
            for expected_name in self.expected_containers:
                if expected_name in container_map:
                    container = container_map[expected_name]
                    
                    # Determine health status
                    if container.status == "running":
                        # Check if container has health check
                        health_status = container.attrs.get("State", {}).get("Health", {}).get("Status")
                        
                        if health_status == "healthy":
                            status = HealthStatus.HEALTHY
                        elif health_status == "unhealthy":
                            status = HealthStatus.UNHEALTHY
                        elif health_status == "starting":
                            status = HealthStatus.DEGRADED
                        else:
                            # No health check, assume healthy if running
                            status = HealthStatus.HEALTHY
                    elif container.status in ["created", "restarting"]:
                        status = HealthStatus.DEGRADED
                    else:
                        status = HealthStatus.UNHEALTHY
                    
                    container_health.append(ComponentHealth(
                        name=expected_name,
                        status=status,
                        last_check=datetime.utcnow().isoformat(),
                        metadata={
                            "container_status": container.status,
                            "health_status": health_status,
                            "image": container.image.tags[0] if container.image.tags else "unknown",
                            "created": container.attrs.get("Created", "unknown")
                        }
                    ))
                else:
                    container_health.append(ComponentHealth(
                        name=expected_name,
                        status=HealthStatus.UNHEALTHY,
                        last_check=datetime.utcnow().isoformat(),
                        error_message="Container not found"
                    ))
            
        except Exception as e:
            container_health.append(ComponentHealth(
                name="docker_containers",
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow().isoformat(),
                error_message=f"Docker check failed: {e}"
            ))
        
        return container_health
    
    async def check_database_connections(self) -> List[ComponentHealth]:
        """Check database connections"""
        db_health = []
        
        # Check Neon PostgreSQL
        try:
            import asyncpg
            
            neon_host = os.getenv('NEON_HOST', 'ep-rough-voice-a5xp7uy8.us-east-2.aws.neon.tech')
            neon_database = os.getenv('NEON_DATABASE', 'neondb')
            neon_username = os.getenv('NEON_USERNAME', 'neondb_owner')
            neon_password = os.getenv('NEON_PASSWORD', 'npg_xxxxxxxxx')
            
            start_time = time.time()
            
            try:
                conn = await asyncpg.connect(
                    host=neon_host,
                    database=neon_database,
                    user=neon_username,
                    password=neon_password,
                    ssl='require'
                )
                
                # Simple query to test connection
                result = await conn.fetchval('SELECT 1')
                await conn.close()
                
                response_time = (time.time() - start_time) * 1000
                
                db_health.append(ComponentHealth(
                    name="neon_postgres",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    last_check=datetime.utcnow().isoformat(),
                    metadata={"host": neon_host, "database": neon_database}
                ))
                
            except Exception as e:
                db_health.append(ComponentHealth(
                    name="neon_postgres",
                    status=HealthStatus.UNHEALTHY,
                    last_check=datetime.utcnow().isoformat(),
                    error_message=str(e),
                    metadata={"host": neon_host, "database": neon_database}
                ))
                
        except ImportError:
            db_health.append(ComponentHealth(
                name="neon_postgres",
                status=HealthStatus.UNKNOWN,
                last_check=datetime.utcnow().isoformat(),
                error_message="asyncpg not available"
            ))
        
        # Check Redis (if configured)
        redis_host = os.getenv('REDIS_HOST')
        if redis_host:
            try:
                import redis.asyncio as redis
                
                redis_port = int(os.getenv('REDIS_PORT', '6379'))
                redis_password = os.getenv('REDIS_PASSWORD')
                
                start_time = time.time()
                
                try:
                    r = redis.Redis(
                        host=redis_host,
                        port=redis_port,
                        password=redis_password,
                        ssl=True if 'upstash' in redis_host else False
                    )
                    
                    await r.ping()
                    await r.close()
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    db_health.append(ComponentHealth(
                        name="redis",
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        last_check=datetime.utcnow().isoformat(),
                        metadata={"host": redis_host, "port": redis_port}
                    ))
                    
                except Exception as e:
                    db_health.append(ComponentHealth(
                        name="redis",
                        status=HealthStatus.UNHEALTHY,
                        last_check=datetime.utcnow().isoformat(),
                        error_message=str(e),
                        metadata={"host": redis_host, "port": redis_port}
                    ))
                    
            except ImportError:
                db_health.append(ComponentHealth(
                    name="redis",
                    status=HealthStatus.UNKNOWN,
                    last_check=datetime.utcnow().isoformat(),
                    error_message="redis not available"
                ))
        
        return db_health
    
    async def check_qdrant_vector_db(self) -> ComponentHealth:
        """Check Qdrant vector database"""
        qdrant_url = os.getenv('QDRANT_URL')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if not qdrant_url:
            return ComponentHealth(
                name="qdrant",
                status=HealthStatus.UNKNOWN,
                last_check=datetime.utcnow().isoformat(),
                error_message="Qdrant URL not configured"
            )
        
        try:
            headers = {}
            if qdrant_api_key:
                headers['api-key'] = qdrant_api_key
            
            start_time = time.time()
            
            # Check cluster info endpoint
            health_url = f"{qdrant_url.rstrip('/')}/cluster"
            
            async with self.session.get(health_url, headers=headers) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return ComponentHealth(
                        name="qdrant",
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        last_check=datetime.utcnow().isoformat(),
                        metadata={
                            "url": qdrant_url,
                            "cluster_info": data.get("result", {})
                        }
                    )
                else:
                    return ComponentHealth(
                        name="qdrant",
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=response_time,
                        last_check=datetime.utcnow().isoformat(),
                        error_message=f"HTTP {response.status}",
                        metadata={"url": qdrant_url}
                    )
                    
        except Exception as e:
            return ComponentHealth(
                name="qdrant",
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow().isoformat(),
                error_message=str(e),
                metadata={"url": qdrant_url}
            )
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_io,
                process_count=process_count,
                uptime_seconds=uptime_seconds,
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_io={},
                process_count=0,
                uptime_seconds=0.0,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def check_mcp_servers(self) -> List[ComponentHealth]:
        """Check MCP server health"""
        mcp_health = []
        
        # Check if MCP server processes are running
        mcp_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'mcp_server' in cmdline or 'code_mcp' in cmdline:
                    mcp_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if mcp_processes:
            mcp_health.append(ComponentHealth(
                name="mcp_servers",
                status=HealthStatus.HEALTHY,
                last_check=datetime.utcnow().isoformat(),
                metadata={
                    "process_count": len(mcp_processes),
                    "processes": mcp_processes
                }
            ))
        else:
            mcp_health.append(ComponentHealth(
                name="mcp_servers",
                status=HealthStatus.UNKNOWN,
                last_check=datetime.utcnow().isoformat(),
                error_message="No MCP server processes found"
            ))
        
        return mcp_health
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check of all components"""
        logger.info("🔍 Starting comprehensive health check...")
        
        health_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": asdict(self.get_system_metrics()),
            "components": {},
            "summary": {
                "total_components": 0,
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0,
                "unknown": 0
            }
        }
        
        all_components = []
        
        # Check HTTP endpoints
        for name, url in self.endpoints.items():
            if url:
                component = await self.check_http_endpoint(name, url)
                all_components.append(component)
        
        # Check Docker containers
        container_health = self.check_docker_containers()
        all_components.extend(container_health)
        
        # Check databases
        db_health = await self.check_database_connections()
        all_components.extend(db_health)
        
        # Check Qdrant
        qdrant_health = await self.check_qdrant_vector_db()
        all_components.append(qdrant_health)
        
        # Check MCP servers
        mcp_health = await self.check_mcp_servers()
        all_components.extend(mcp_health)
        
        # Process results
        for component in all_components:
            # Convert enum to string for JSON serialization
            component_dict = asdict(component)
            component_dict['status'] = component.status.value
            health_results["components"][component.name] = component_dict
            
            # Update summary
            health_results["summary"]["total_components"] += 1
            if component.status == HealthStatus.HEALTHY:
                health_results["summary"]["healthy"] += 1
            elif component.status == HealthStatus.DEGRADED:
                health_results["summary"]["degraded"] += 1
            elif component.status == HealthStatus.UNHEALTHY:
                health_results["summary"]["unhealthy"] += 1
            else:
                health_results["summary"]["unknown"] += 1
        
        # Calculate overall health score
        total = health_results["summary"]["total_components"]
        if total > 0:
            healthy_score = (health_results["summary"]["healthy"] / total) * 100
            degraded_score = (health_results["summary"]["degraded"] / total) * 50
            health_results["summary"]["overall_health_score"] = healthy_score + degraded_score
        else:
            health_results["summary"]["overall_health_score"] = 0
        
        logger.info("✅ Health check completed")
        return health_results
    
    async def generate_monitoring_report(self) -> str:
        """Generate comprehensive monitoring report"""
        health_data = await self.run_comprehensive_health_check()
        
        report = f"""# Sophia Intel Platform Health Report

## 📊 Executive Summary

**Report Generated**: {health_data['timestamp']}  
**Overall Health Score**: {health_data['summary']['overall_health_score']:.1f}%  

### Component Status Summary
- ✅ **Healthy**: {health_data['summary']['healthy']} components
- ⚠️ **Degraded**: {health_data['summary']['degraded']} components  
- ❌ **Unhealthy**: {health_data['summary']['unhealthy']} components
- ❓ **Unknown**: {health_data['summary']['unknown']} components

**Total Components Monitored**: {health_data['summary']['total_components']}

## 🖥️ System Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **CPU Usage** | {health_data['system_metrics']['cpu_percent']:.1f}% | {'🟢' if health_data['system_metrics']['cpu_percent'] < 80 else '🟡' if health_data['system_metrics']['cpu_percent'] < 95 else '🔴'} |
| **Memory Usage** | {health_data['system_metrics']['memory_percent']:.1f}% | {'🟢' if health_data['system_metrics']['memory_percent'] < 80 else '🟡' if health_data['system_metrics']['memory_percent'] < 95 else '🔴'} |
| **Disk Usage** | {health_data['system_metrics']['disk_percent']:.1f}% | {'🟢' if health_data['system_metrics']['disk_percent'] < 80 else '🟡' if health_data['system_metrics']['disk_percent'] < 95 else '🔴'} |
| **Process Count** | {health_data['system_metrics']['process_count']} | 🟢 |
| **System Uptime** | {health_data['system_metrics']['uptime_seconds'] / 3600:.1f} hours | 🟢 |

## 🔧 Component Health Details

"""
        
        # Group components by category
        categories = {
            "Infrastructure": ["airbyte-airbyte-server-1", "airbyte-airbyte-worker-1", "airbyte-airbyte-webapp-1", 
                             "airbyte-airbyte-temporal-1", "airbyte-airbyte-db-1", "airbyte-minio-1"],
            "Data Services": ["neon_postgres", "qdrant", "redis"],
            "Application Services": ["airbyte_server", "airbyte_webapp", "minio"],
            "AI Services": ["mcp_servers"]
        }
        
        for category, component_names in categories.items():
            report += f"### {category}\n\n"
            
            for comp_name in component_names:
                if comp_name in health_data['components']:
                    comp = health_data['components'][comp_name]
                    status_icon = {
                        'healthy': '✅',
                        'degraded': '⚠️',
                        'unhealthy': '❌',
                        'unknown': '❓'
                    }.get(comp['status'], '❓')
                    
                    response_time = f" ({comp['response_time_ms']:.0f}ms)" if comp['response_time_ms'] else ""
                    error_msg = f" - {comp['error_message']}" if comp['error_message'] else ""
                    
                    report += f"- {status_icon} **{comp['name']}**: {comp['status']}{response_time}{error_msg}\n"
            
            report += "\n"
        
        # Add recommendations
        report += """## 🎯 Recommendations

"""
        
        unhealthy_components = [name for name, comp in health_data['components'].items() 
                              if comp['status'] == 'unhealthy']
        
        if unhealthy_components:
            report += "### 🚨 Critical Issues\n\n"
            for comp_name in unhealthy_components:
                comp = health_data['components'][comp_name]
                report += f"- **{comp_name}**: {comp.get('error_message', 'Unknown error')}\n"
            report += "\n"
        
        degraded_components = [name for name, comp in health_data['components'].items() 
                             if comp['status'] == 'degraded']
        
        if degraded_components:
            report += "### ⚠️ Performance Issues\n\n"
            for comp_name in degraded_components:
                comp = health_data['components'][comp_name]
                report += f"- **{comp_name}**: {comp.get('error_message', 'Performance degraded')}\n"
            report += "\n"
        
        # System recommendations
        sys_metrics = health_data['system_metrics']
        if sys_metrics['cpu_percent'] > 80:
            report += "- 🔴 **High CPU Usage**: Consider scaling or optimizing processes\n"
        if sys_metrics['memory_percent'] > 80:
            report += "- 🔴 **High Memory Usage**: Monitor for memory leaks or scale resources\n"
        if sys_metrics['disk_percent'] > 80:
            report += "- 🔴 **High Disk Usage**: Clean up logs or expand storage\n"
        
        report += f"""
## 📈 Monitoring Data

Full monitoring data saved to: `monitoring_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json`

---
*Generated by Sophia Intel Monitoring System*  
*Next check recommended in 15 minutes*
"""
        
        return report


async def main():
    """Main monitoring execution"""
    logger.info("🚀 Sophia Intel Platform Monitor")
    
    async with SophiaIntelMonitor() as monitor:
        # Run health check
        health_results = await monitor.run_comprehensive_health_check()
        
        # Generate report
        report = await monitor.generate_monitoring_report()
        
        # Save results
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON data
        json_file = Path(__file__).parent.parent / f"monitoring_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(health_results, f, indent=2)
        
        # Save report
        report_file = Path(__file__).parent.parent / f"MONITORING_REPORT_{timestamp}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Print summary
        print("\n" + "="*80)
        print("🔍 SOPHIA INTEL PLATFORM HEALTH CHECK")
        print("="*80)
        
        summary = health_results['summary']
        print(f"Overall Health Score: {summary['overall_health_score']:.1f}%")
        print(f"Components: {summary['healthy']}✅ {summary['degraded']}⚠️ {summary['unhealthy']}❌ {summary['unknown']}❓")
        
        sys_metrics = health_results['system_metrics']
        print(f"System: CPU {sys_metrics['cpu_percent']:.1f}% | Memory {sys_metrics['memory_percent']:.1f}% | Disk {sys_metrics['disk_percent']:.1f}%")
        
        print(f"\n📄 Detailed report: {report_file}")
        print(f"📊 Raw data: {json_file}")
        
        # Return appropriate exit code
        if summary['unhealthy'] > 0:
            print("❌ Critical issues detected!")
            return 1
        elif summary['degraded'] > 0:
            print("⚠️ Performance issues detected")
            return 1
        else:
            print("✅ All systems operational")
            return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

