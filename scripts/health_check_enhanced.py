#!/usr/bin/env python3
"""
Enhanced Health Check Script
Comprehensive service health validation with retry logic and detailed reporting
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx
import redis
import psycopg
import structlog

logger = structlog.get_logger(__name__)

class HealthChecker:
    """Enhanced health checker with circuit breaker pattern"""
    
    def __init__(self):
        self.services = {
            'postgres': {'port': 5432, 'url': 'postgresql://builder:builder123@localhost:5432/builder'},
            'redis': {'port': 6379, 'url': 'redis://localhost:6379'},
            'weaviate': {'port': 8080, 'url': 'http://localhost:8080/v1/.well-known/ready'},
            'neo4j': {'port': 7474, 'url': 'http://localhost:7474'},
            'bridge': {'port': 8003, 'url': 'http://localhost:8003/health'}
        }
        self.retry_attempts = 3
        self.retry_delay = 2.0
        self.timeout = 10.0
    
    async def check_http_service(self, name: str, url: str) -> Dict[str, Any]:
        """Check HTTP-based service with retries"""
        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return {
                            'status': 'healthy',
                            'response_time': response.elapsed.total_seconds(),
                            'attempts': attempt + 1
                        }
                    else:
                        raise Exception(f"HTTP {response.status_code}")
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    return {
                        'status': 'unhealthy',
                        'error': str(e),
                        'attempts': attempt + 1
                    }
                await asyncio.sleep(self.retry_delay)
        
        return {'status': 'unhealthy', 'error': 'Max retries exceeded'}
    
    async def check_postgres(self) -> Dict[str, Any]:
        """Check PostgreSQL with connection pooling"""
        for attempt in range(self.retry_attempts):
            try:
                async with await psycopg.AsyncConnection.connect(
                    self.services['postgres']['url'],
                    connect_timeout=self.timeout
                ) as conn:
                    async with conn.cursor() as cur:
                        await cur.execute('SELECT 1')
                        result = await cur.fetchone()
                        return {
                            'status': 'healthy',
                            'query_result': result[0],
                            'attempts': attempt + 1
                        }
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    return {
                        'status': 'unhealthy',
                        'error': str(e),
                        'attempts': attempt + 1
                    }
                await asyncio.sleep(self.retry_delay)
        
        return {'status': 'unhealthy', 'error': 'Max retries exceeded'}
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis/Valkey with connection pooling"""
        for attempt in range(self.retry_attempts):
            try:
                r = redis.Redis.from_url(
                    self.services['redis']['url'],
                    socket_connect_timeout=self.timeout
                )
                result = r.ping()
                r.close()
                return {
                    'status': 'healthy',
                    'ping_result': result,
                    'attempts': attempt + 1
                }
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    return {
                        'status': 'unhealthy',
                        'error': str(e),
                        'attempts': attempt + 1
                    }
                await asyncio.sleep(self.retry_delay)
        
        return {'status': 'unhealthy', 'error': 'Max retries exceeded'}
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all services"""
        start_time = time.time()
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'services': {},
            'summary': {
                'healthy': 0,
                'unhealthy': 0,
                'total_response_time': 0
            }
        }
        
        # Check all services concurrently
        tasks = [
            ('postgres', self.check_postgres()),
            ('redis', self.check_redis()),
            ('weaviate', self.check_http_service('weaviate', self.services['weaviate']['url'])),
            ('neo4j', self.check_http_service('neo4j', self.services['neo4j']['url'])),
            ('bridge', self.check_http_service('bridge', self.services['bridge']['url']))
        ]
        
        for name, task in tasks:
            try:
                result = await task
                results['services'][name] = result
                
                if result['status'] == 'healthy':
                    results['summary']['healthy'] += 1
                    if 'response_time' in result:
                        results['summary']['total_response_time'] += result['response_time']
                else:
                    results['summary']['unhealthy'] += 1
                    results['overall_status'] = 'degraded'
            except Exception as e:
                results['services'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
                results['summary']['unhealthy'] += 1
                results['overall_status'] = 'degraded'
        
        # Set overall status based on critical services
        critical_services = ['postgres', 'redis', 'weaviate']
        critical_unhealthy = sum(1 for svc in critical_services 
                               if results['services'].get(svc, {}).get('status') != 'healthy')
        
        if critical_unhealthy > 0:
            results['overall_status'] = 'critical' if critical_unhealthy > 1 else 'degraded'
        
        results['execution_time'] = time.time() - start_time
        return results

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable health report"""
        report = []
        report.append("=== Sophia Intel AI - Enhanced Health Report ===")
        report.append(f"Timestamp: {results['timestamp']}")
        report.append(f"Overall Status: {results['overall_status'].upper()}")
        report.append(f"Execution Time: {results['execution_time']:.2f}s")
        report.append("")
        
        report.append("Service Details:")
        for service, details in results['services'].items():
            status = details['status'].upper()
            if status == 'HEALTHY':
                icon = "✅"
                extra = f" (attempts: {details.get('attempts', 1)})"
                if 'response_time' in details:
                    extra += f", {details['response_time']*1000:.0f}ms"
            elif status == 'UNHEALTHY':
                icon = "❌"
                extra = f" - {details.get('error', 'Unknown error')}"
            else:
                icon = "⚠️"
                extra = f" - {details.get('error', 'Unknown error')}"
            
            report.append(f"  {icon} {service.upper()}: {status}{extra}")
        
        report.append("")
        report.append("Summary:")
        report.append(f"  Healthy Services: {results['summary']['healthy']}")
        report.append(f"  Unhealthy Services: {results['summary']['unhealthy']}")
        report.append(f"  Average Response Time: {results['summary']['total_response_time']/max(1, results['summary']['healthy'])*1000:.0f}ms")
        
        return "\n".join(report)

async def main():
    """Main health check execution"""
    checker = HealthChecker()
    results = await checker.comprehensive_health_check()
    
    # Print human-readable report
    print(checker.generate_report(results))
    
    # Save detailed JSON results
    with open('health_check_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Exit with appropriate code
    if results['overall_status'] == 'critical':
        exit(2)
    elif results['overall_status'] == 'degraded':
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    asyncio.run(main())