#!/usr/bin/env python3
"""
Startup Validation Script for Sophia AI
Comprehensive validation of startup process with error detection and recovery
"""
import asyncio
import aiohttp
import json
import logging
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import argparse
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/startup-validator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
@dataclass
class ValidationResult:
    """Validation result for a specific check"""
    name: str
    status: str  # 'pass', 'fail', 'warn', 'skip'
    message: str
    duration_ms: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
@dataclass
class StartupValidationReport:
    """Complete startup validation report"""
    timestamp: datetime
    total_duration_ms: float
    overall_status: str
    passed_checks: int
    failed_checks: int
    warning_checks: int
    skipped_checks: int
    results: List[ValidationResult]
    system_info: Dict[str, Any]
    recommendations: List[str]
class StartupValidator:
    """Comprehensive startup validation system"""
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.start_time = time.time()
        self.timeout_seconds = 600  # 10 minutes
        self.critical_services = [
            'postgresql', 'redis', 'qdrant', 'neo4j'
        ]
        self.optional_services = [
            'backend-api', 'mcp-server', 'lambda-manager', 'frontend'
        ]
    async def validate_environment_variables(self) -> ValidationResult:
        """Validate required environment variables"""
        start_time = time.time()
        required_vars = [
            'DATABASE_URL', 'REDIS_URL', 'QDRANT_URL', 'NEO4J_URL'
        ]
        optional_vars = [
            'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'LAMBDA_LABS_API_KEY',
            'PORTKEY_API_KEY', 'OPENROUTER_API_KEY', 'ESTUARY_API_TOKEN'
        ]
        missing_required = []
        missing_optional = []
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        duration = (time.time() - start_time) * 1000
        if missing_required:
            return ValidationResult(
                name="Environment Variables",
                status="fail",
                message=f"Missing required variables: {', '.join(missing_required)}",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={
                    "missing_required": missing_required,
                    "missing_optional": missing_optional
                }
            )
        elif missing_optional:
            return ValidationResult(
                name="Environment Variables",
                status="warn",
                message=f"Missing optional variables: {', '.join(missing_optional)}",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={
                    "missing_required": missing_required,
                    "missing_optional": missing_optional
                }
            )
        else:
            return ValidationResult(
                name="Environment Variables",
                status="pass",
                message="All environment variables configured",
                duration_ms=duration,
                timestamp=datetime.now()
            )
    async def validate_file_permissions(self) -> ValidationResult:
        """Validate file permissions for scripts and directories"""
        start_time = time.time()
        issues = []
        # Check script permissions
        script_files = [
            'scripts/deploy-lambda.sh',
            'scripts/shutdown-production.sh',
            'scripts/health-monitor.sh',
            'scripts/lambda-init.sh'
        ]
        for script in script_files:
            if Path(script).exists():
                if not os.access(script, os.X_OK):
                    issues.append(f"{script} is not executable")
            else:
                issues.append(f"{script} does not exist")
        # Check directory permissions
        required_dirs = [
            'logs', 'data/uploads', 'data/cache', 'tmp'
        ]
        for directory in required_dirs:
            dir_path = Path(directory)
            if not dir_path.exists():
                issues.append(f"Directory {directory} does not exist")
            elif not os.access(directory, os.W_OK):
                issues.append(f"Directory {directory} is not writable")
        duration = (time.time() - start_time) * 1000
        if issues:
            return ValidationResult(
                name="File Permissions",
                status="fail",
                message=f"Permission issues found: {'; '.join(issues)}",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"issues": issues}
            )
        else:
            return ValidationResult(
                name="File Permissions",
                status="pass",
                message="All file permissions correct",
                duration_ms=duration,
                timestamp=datetime.now()
            )
    async def validate_docker_containers(self) -> ValidationResult:
        """Validate Docker containers are running and healthy"""
        start_time = time.time()
        containers = {
            'sophia-postgres': 'PostgreSQL',
            'sophia-redis': 'Redis',
            'sophia-qdrant': 'Qdrant',
            'sophia-neo4j': 'Neo4j'
        }
        container_status = {}
        issues = []
        for container_name, service_name in containers.items():
            try:
                # Check if container exists and is running
                result = subprocess.run(
                    ['docker', 'inspect', container_name, '--format={{.State.Status}}'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    status = result.stdout.strip()
                    container_status[service_name] = status
                    if status != 'running':
                        issues.append(f"{service_name} container is {status}")
                    else:
                        # Check health status if available
                        health_result = subprocess.run(
                            ['docker', 'inspect', container_name, '--format={{.State.Health.Status}}'],
                            capture_output=True, text=True, timeout=10
                        )
                        if health_result.returncode == 0:
                            health_status = health_result.stdout.strip()
                            if health_status and health_status != '<no value>':
                                container_status[f"{service_name}_health"] = health_status
                                if health_status not in ['healthy', 'starting']:
                                    issues.append(f"{service_name} health check is {health_status}")
                else:
                    container_status[service_name] = 'not_found'
                    issues.append(f"{service_name} container not found")
            except subprocess.TimeoutExpired:
                issues.append(f"{service_name} container check timed out")
            except Exception as e:
                issues.append(f"{service_name} container check failed: {str(e)}")
        duration = (time.time() - start_time) * 1000
        if issues:
            return ValidationResult(
                name="Docker Containers",
                status="fail",
                message=f"Container issues: {'; '.join(issues)}",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"container_status": container_status, "issues": issues}
            )
        else:
            return ValidationResult(
                name="Docker Containers",
                status="pass",
                message="All containers running and healthy",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"container_status": container_status}
            )
    async def validate_database_connections(self) -> ValidationResult:
        """Validate database connections"""
        start_time = time.time()
        connection_results = {}
        issues = []
        # PostgreSQL
        try:
            import psycopg2
            conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            conn.close()
            connection_results['postgresql'] = 'connected'
        except ImportError:
            issues.append("psycopg2 not installed for PostgreSQL")
            connection_results['postgresql'] = 'missing_driver'
        except Exception as e:
            issues.append(f"PostgreSQL connection failed: {str(e)}")
            connection_results['postgresql'] = 'failed'
        # Redis
        try:
            import redis
            r = redis.from_url(os.getenv('REDIS_URL'))
            r.ping()
            connection_results['redis'] = 'connected'
        except ImportError:
            issues.append("redis package not installed")
            connection_results['redis'] = 'missing_driver'
        except Exception as e:
            issues.append(f"Redis connection failed: {str(e)}")
            connection_results['redis'] = 'failed'
        # Qdrant
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    os.getenv('QDRANT_URL') + '/health',
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        connection_results['qdrant'] = 'connected'
                    else:
                        issues.append(f"Qdrant health check failed: HTTP {response.status}")
                        connection_results['qdrant'] = 'unhealthy'
        except Exception as e:
            issues.append(f"Qdrant connection failed: {str(e)}")
            connection_results['qdrant'] = 'failed'
        # Neo4j
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(
                os.getenv('NEO4J_URL'),
                auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'password'))
            )
            with driver.session() as session:
                session.run("RETURN 1")
            driver.close()
            connection_results['neo4j'] = 'connected'
        except ImportError:
            issues.append("neo4j package not installed")
            connection_results['neo4j'] = 'missing_driver'
        except Exception as e:
            issues.append(f"Neo4j connection failed: {str(e)}")
            connection_results['neo4j'] = 'failed'
        duration = (time.time() - start_time) * 1000
        if issues:
            return ValidationResult(
                name="Database Connections",
                status="fail",
                message=f"Database connection issues: {'; '.join(issues)}",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"connections": connection_results, "issues": issues}
            )
        else:
            return ValidationResult(
                name="Database Connections",
                status="pass",
                message="All database connections successful",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"connections": connection_results}
            )
    async def validate_api_endpoints(self) -> ValidationResult:
        """Validate API endpoints are responding"""
        start_time = time.time()
        endpoints = {
            'Backend API': 'http://localhost:8000/health',
            'MCP Server': 'http://localhost:8001/health',
            'Lambda Manager': 'http://localhost:8002/health',
            'Frontend': '${SOPHIA_FRONTEND_ENDPOINT}'
        }
        endpoint_results = {}
        issues = []
        warnings = []
        async with aiohttp.ClientSession() as session:
            for name, url in endpoints.items():
                try:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        endpoint_results[name] = {
                            'status_code': response.status,
                            'response_time_ms': response.headers.get('X-Response-Time', 'unknown')
                        }
                        if response.status == 200:
                            endpoint_results[name]['status'] = 'healthy'
                        else:
                            if name in ['Backend API', 'MCP Server']:
                                issues.append(f"{name} returned HTTP {response.status}")
                            else:
                                warnings.append(f"{name} returned HTTP {response.status}")
                            endpoint_results[name]['status'] = 'unhealthy'
                except asyncio.TimeoutError:
                    if name in ['Backend API', 'MCP Server']:
                        issues.append(f"{name} request timed out")
                    else:
                        warnings.append(f"{name} request timed out")
                    endpoint_results[name] = {'status': 'timeout'}
                except Exception as e:
                    if name in ['Backend API', 'MCP Server']:
                        issues.append(f"{name} connection failed: {str(e)}")
                    else:
                        warnings.append(f"{name} connection failed: {str(e)}")
                    endpoint_results[name] = {'status': 'failed', 'error': str(e)}
        duration = (time.time() - start_time) * 1000
        if issues:
            return ValidationResult(
                name="API Endpoints",
                status="fail",
                message=f"Critical API issues: {'; '.join(issues)}",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"endpoints": endpoint_results, "issues": issues, "warnings": warnings}
            )
        elif warnings:
            return ValidationResult(
                name="API Endpoints",
                status="warn",
                message=f"Optional API warnings: {'; '.join(warnings)}",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"endpoints": endpoint_results, "warnings": warnings}
            )
        else:
            return ValidationResult(
                name="API Endpoints",
                status="pass",
                message="All API endpoints responding",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"endpoints": endpoint_results}
            )
    async def validate_python_environment(self) -> ValidationResult:
        """Validate Python environment and dependencies"""
        start_time = time.time()
        issues = []
        warnings = []
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            issues.append(f"Python version {python_version.major}.{python_version.minor} is too old (minimum 3.8)")
        # Check virtual environment
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            warnings.append("Not running in a virtual environment")
        # Check critical packages
        critical_packages = [
            'fastapi', 'uvicorn', 'pydantic', 'aiohttp', 'redis', 'psycopg2'
        ]
        missing_packages = []
        for package in critical_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        if missing_packages:
            issues.append(f"Missing critical packages: {', '.join(missing_packages)}")
        # Check optional packages
        optional_packages = [
            'langchain', 'anthropic', 'openai', 'qdrant_client', 'neo4j'
        ]
        missing_optional = []
        for package in optional_packages:
            try:
                __import__(package)
            except ImportError:
                missing_optional.append(package)
        if missing_optional:
            warnings.append(f"Missing optional packages: {', '.join(missing_optional)}")
        duration = (time.time() - start_time) * 1000
        if issues:
            return ValidationResult(
                name="Python Environment",
                status="fail",
                message=f"Python environment issues: {'; '.join(issues)}",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"issues": issues, "warnings": warnings}
            )
        elif warnings:
            return ValidationResult(
                name="Python Environment",
                status="warn",
                message=f"Python environment warnings: {'; '.join(warnings)}",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"warnings": warnings}
            )
        else:
            return ValidationResult(
                name="Python Environment",
                status="pass",
                message="Python environment is properly configured",
                duration_ms=duration,
                timestamp=datetime.now()
            )
    async def validate_system_resources(self) -> ValidationResult:
        """Validate system resources (memory, disk, CPU)"""
        start_time = time.time()
        issues = []
        warnings = []
        system_info = {}
        try:
            import psutil
            # Memory check
            memory = psutil.virtual_memory()
            system_info['memory_total_gb'] = round(memory.total / (1024**3), 2)
            system_info['memory_used_percent'] = memory.percent
            if memory.percent > 90:
                issues.append(f"Memory usage critical: {memory.percent}%")
            elif memory.percent > 80:
                warnings.append(f"Memory usage high: {memory.percent}%")
            # Disk check
            disk = psutil.disk_usage('/workspaces')
            system_info['disk_total_gb'] = round(disk.total / (1024**3), 2)
            system_info['disk_used_percent'] = round((disk.used / disk.total) * 100, 1)
            if disk.free < 1024**3:  # Less than 1GB free
                issues.append(f"Disk space critical: {round(disk.free / (1024**3), 2)}GB free")
            elif disk.free < 5 * 1024**3:  # Less than 5GB free
                warnings.append(f"Disk space low: {round(disk.free / (1024**3), 2)}GB free")
            # CPU check
            cpu_percent = psutil.cpu_percent(interval=1)
            system_info['cpu_percent'] = cpu_percent
            system_info['cpu_count'] = psutil.cpu_count()
            if cpu_percent > 95:
                warnings.append(f"CPU usage very high: {cpu_percent}%")
            elif cpu_percent > 80:
                warnings.append(f"CPU usage high: {cpu_percent}%")
        except ImportError:
            warnings.append("psutil not available for system resource monitoring")
        except Exception as e:
            warnings.append(f"System resource check failed: {str(e)}")
        duration = (time.time() - start_time) * 1000
        if issues:
            return ValidationResult(
                name="System Resources",
                status="fail",
                message=f"System resource issues: {'; '.join(issues)}",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"system_info": system_info, "issues": issues, "warnings": warnings}
            )
        elif warnings:
            return ValidationResult(
                name="System Resources",
                status="warn",
                message=f"System resource warnings: {'; '.join(warnings)}",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"system_info": system_info, "warnings": warnings}
            )
        else:
            return ValidationResult(
                name="System Resources",
                status="pass",
                message="System resources are adequate",
                duration_ms=duration,
                timestamp=datetime.now(),
                details={"system_info": system_info}
            )
    async def run_all_validations(self) -> StartupValidationReport:
        """Run all validation checks"""
        logger.info("🔍 Starting comprehensive startup validation...")
        validation_functions = [
            self.validate_environment_variables,
            self.validate_file_permissions,
            self.validate_docker_containers,
            self.validate_database_connections,
            self.validate_python_environment,
            self.validate_system_resources,
            self.validate_api_endpoints
        ]
        for validation_func in validation_functions:
            try:
                result = await validation_func()
                self.results.append(result)
                status_icon = {
                    'pass': '✅',
                    'warn': '⚠️',
                    'fail': '❌',
                    'skip': '⏭️'
                }.get(result.status, '❓')
                logger.info(f"{status_icon} {result.name}: {result.message} ({result.duration_ms:.1f}ms)")
            except Exception as e:
                error_result = ValidationResult(
                    name=validation_func.__name__.replace('validate_', '').replace('_', ' ').title(),
                    status='fail',
                    message=f"Validation error: {str(e)}",
                    duration_ms=0,
                    timestamp=datetime.now(),
                    details={"error": str(e), "traceback": traceback.format_exc()}
                )
                self.results.append(error_result)
                logger.error(f"❌ {error_result.name}: {error_result.message}")
        # Calculate summary statistics
        total_duration = (time.time() - self.start_time) * 1000
        passed = sum(1 for r in self.results if r.status == 'pass')
        failed = sum(1 for r in self.results if r.status == 'fail')
        warnings = sum(1 for r in self.results if r.status == 'warn')
        skipped = sum(1 for r in self.results if r.status == 'skip')
        # Determine overall status
        if failed > 0:
            overall_status = 'fail'
        elif warnings > 0:
            overall_status = 'warn'
        else:
            overall_status = 'pass'
        # Generate recommendations
        recommendations = self.generate_recommendations()
        # Get system info
        system_info = self.get_system_info()
        return StartupValidationReport(
            timestamp=datetime.now(),
            total_duration_ms=total_duration,
            overall_status=overall_status,
            passed_checks=passed,
            failed_checks=failed,
            warning_checks=warnings,
            skipped_checks=skipped,
            results=self.results,
            system_info=system_info,
            recommendations=recommendations
        )
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        for result in self.results:
            if result.status == 'fail':
                if 'Environment Variables' in result.name:
                    recommendations.append("Set missing environment variables in .env file or Codespaces secrets")
                elif 'File Permissions' in result.name:
                    recommendations.append("Run: chmod +x scripts/*.sh to fix script permissions")
                elif 'Docker Containers' in result.name:
                    recommendations.append("Restart failed containers: docker restart <container-name>")
                elif 'Database Connections' in result.name:
                    recommendations.append("Check database containers are running and ports are accessible")
                elif 'Python Environment' in result.name:
                    recommendations.append("Install missing packages: uv pip install <package-name>")
                elif 'API Endpoints' in result.name:
                    recommendations.append("Start missing services or check service logs")
            elif result.status == 'warn':
                if 'System Resources' in result.name:
                    recommendations.append("Monitor system resources and consider scaling if needed")
                elif 'API Endpoints' in result.name:
                    recommendations.append("Optional services can be started later if needed")
        if not recommendations:
            recommendations.append("All validations passed! System is ready for development.")
        return recommendations
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        info = {
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'platform': sys.platform,
            'working_directory': os.getcwd(),
            'environment': os.getenv('ENVIRONMENT', 'unknown')
        }
        try:
            import psutil
            info.update({
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_total_gb': round(psutil.disk_usage('/workspaces').total / (1024**3), 2)
            })
        except ImportError:
            pass
        return info
async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Sophia AI Startup Validator")
    parser.add_argument("--output", "-o", help="Output file for JSON report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--timeout", "-t", type=int, default=600, help="Timeout in seconds")
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    validator = StartupValidator()
    validator.timeout_seconds = args.timeout
    try:
        report = await validator.run_all_validations()
        # Print summary
        status_icon = {
            'pass': '✅',
            'warn': '⚠️',
            'fail': '❌'
        }.get(report.overall_status, '❓')
        print(f"\n{status_icon} Startup Validation Complete!")
        print(f"Overall Status: {report.overall_status.upper()}")
        print(f"Duration: {report.total_duration_ms:.1f}ms")
        print(f"Results: {report.passed_checks} passed, {report.failed_checks} failed, {report.warning_checks} warnings")
        if report.recommendations:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"   {i}. {rec}")
        # Save report
        report_data = asdict(report)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            print(f"\n📄 Detailed report saved to: {args.output}")
        else:
            with open('/tmp/startup-validation-report.json', 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            print(f"\n📄 Detailed report saved to: /tmp/startup-validation-report.json")
        # Exit with appropriate code
        if report.overall_status == 'fail':
            sys.exit(1)
        elif report.overall_status == 'warn':
            sys.exit(2)
        else:
            sys.exit(0)
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}")
        logger.debug(traceback.format_exc())
        sys.exit(3)
if __name__ == "__main__":
    asyncio.run(main())
