#!/usr/bin/env python3
"""
Security Monitoring Gates - Phase 1 Implementation
Automated monitoring for security compliance and performance regression detection
"""
import asyncio
import json
import time
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@dataclass
class SecurityCheck:
    """Security check definition"""
    check_id: str
    name: str
    description: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    status: str = "PENDING"
    message: str = ""
    timestamp: Optional[datetime] = None
@dataclass
class PerformanceMetric:
    """Performance metric tracking"""
    metric_name: str
    current_value: float
    baseline_value: float
    threshold_percent: float
    status: str = "PENDING"
    timestamp: Optional[datetime] = None
class SecurityMonitoringGates:
    """
    Security and performance monitoring gates for CI/CD pipeline
    Ensures Phase 1 security fixes don't introduce regressions
    """
    def __init__(self):
        self.security_checks = []
        self.performance_metrics = []
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "phase": "PHASE_1_SECURITY_FIXES",
            "overall_status": "PENDING",
            "security_status": "PENDING",
            "performance_status": "PENDING",
            "checks": [],
            "metrics": [],
            "summary": {}
        }
    async def run_all_gates(self) -> Dict[str, Any]:
        """Run all security and performance monitoring gates"""
        logger.info("🚀 Starting Security Monitoring Gates - Phase 1")
        # Run security compliance checks
        await self._run_security_gates()
        # Run performance regression checks
        await self._run_performance_gates()
        # Generate final report
        self._generate_final_report()
        return self.results
    async def _run_security_gates(self):
        """Run security compliance gates"""
        logger.info("🔒 Running Security Compliance Gates...")
        security_checks = [
            SecurityCheck(
                "PYJWT_VERSION",
                "PyJWT Version Compliance",
                "Verify PyJWT >= 3.0.0 for critical auth fixes",
                "CRITICAL"
            ),
            SecurityCheck(
                "SETUPTOOLS_VERSION", 
                "setuptools Security Constraint",
                "Verify setuptools >= 78.1.1 for CVE-2025-47273",
                "CRITICAL"
            ),
            SecurityCheck(
                "WHEEL_VERSION",
                "wheel Security Constraint", 
                "Verify wheel >= 0.38.1 for CVE-2022-40898",
                "CRITICAL"
            ),
            SecurityCheck(
                "HARDCODED_SECRETS",
                "Hardcoded Secrets Scan",
                "Verify no hardcoded secrets in codebase",
                "HIGH"
            ),
            SecurityCheck(
                "DEPENDENCY_MOCKS",
                "Mock Dependencies Check",
                "Verify no dangerous mock implementations",
                "HIGH"
            ),
            SecurityCheck(
                "ENVIRONMENT_CONFIG",
                "Security Environment Configuration",
                "Verify security environment setup",
                "MEDIUM"
            )
        ]
        for check in security_checks:
            await self._execute_security_check(check)
            self.security_checks.append(check)
    async def _execute_security_check(self, check: SecurityCheck):
        """Execute individual security check"""
        check.timestamp = datetime.utcnow()
        try:
            if check.check_id == "PYJWT_VERSION":
                await self._check_pyjwt_version(check)
            elif check.check_id == "SETUPTOOLS_VERSION":
                await self._check_setuptools_version(check)
            elif check.check_id == "WHEEL_VERSION":
                await self._check_wheel_version(check)
            elif check.check_id == "HARDCODED_SECRETS":
                await self._check_hardcoded_secrets(check)
            elif check.check_id == "DEPENDENCY_MOCKS":
                await self._check_dependency_mocks(check)
            elif check.check_id == "ENVIRONMENT_CONFIG":
                await self._check_environment_config(check)
        except Exception as e:
            check.status = "FAILED"
            check.message = f"Check execution failed: {e}"
            logger.error(f"Security check {check.check_id} failed: {e}")
    async def _check_pyjwt_version(self, check: SecurityCheck):
        """Check PyJWT version compliance"""
        try:
            import jwt
            version = jwt.__version__
            major_version = int(version.split('.')[0])
            if major_version >= 3:
                check.status = "PASSED"
                check.message = f"PyJWT version {version} meets security requirement >=3.0.0"
            else:
                check.status = "FAILED"
                check.message = f"PyJWT version {version} does not meet security requirement >=3.0.0"
        except ImportError:
            check.status = "FAILED"
            check.message = "PyJWT not installed - critical security requirement not met"
            return
    async def _check_setuptools_version(self, check: SecurityCheck):
        """Check setuptools version compliance"""
        try:
            import setuptools
            version = setuptools.__version__
            version_parts = list(map(int, version.split('.')))
            # Check for setuptools >= 78.1.1
            if (version_parts[0] > 78 or 
                (version_parts[0] == 78 and version_parts[1] > 1) or
                (version_parts[0] == 78 and version_parts[1] == 1 and version_parts[2] >= 1)):
                check.status = "PASSED"
                check.message = f"setuptools version {version} meets security requirement >=78.1.1"
            else:
                check.status = "FAILED"
                check.message = f"setuptools version {version} vulnerable to CVE-2025-47273"
        except (ImportError, IndexError, ValueError):
            check.status = "FAILED"
            check.message = "setuptools version check failed"
    async def _check_wheel_version(self, check: SecurityCheck):
        """Check wheel version compliance"""
        try:
            import wheel
            version = wheel.__version__
            version_parts = list(map(int, version.split('.')))
            # Check for wheel >= 0.38.1
            if (version_parts[0] > 0 or
                (version_parts[0] == 0 and version_parts[1] > 38) or
                (version_parts[0] == 0 and version_parts[1] == 38 and version_parts[2] >= 1)):
                check.status = "PASSED"
                check.message = f"wheel version {version} meets security requirement >=0.38.1"
            else:
                check.status = "FAILED"
                check.message = f"wheel version {version} vulnerable to CVE-2022-40898"
        except (ImportError, IndexError, ValueError):
            check.status = "FAILED"
            check.message = "wheel version check failed"
    async def _check_hardcoded_secrets(self, check: SecurityCheck):
        """Check for hardcoded secrets in codebase"""
        import re
        secret_patterns = [
            r'salt\s*=\s*b?[\'"][^\'\"]{8,}[\'"]',  # Hardcoded salt patterns
            r'password\s*=\s*[\'"][^\'\"]{4,}[\'"]',
            r'secret\s*=\s*[\'"][^\'\"]{8,}[\'"]',
            r'api[_-]?key\s*=\s*[\'"][^\'\"]{10,}[\'"]'
        ]
        files_to_check = [
            'orchestration/communication/acp_protocol.py',
            'orchestration/security/guardrails.py',
            'core/clean_architecture/infrastructure.py'
        ]
        violations = []
        for file_path in files_to_check:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        # Filter out obvious test/placeholder values
                        real_secrets = [m for m in matches if not any(
                            word in m.lower() for word in ['test', 'example', 'placeholder', 'dummy']
                        )]
                        if real_secrets:
                            violations.extend([(file_path, pattern, real_secrets)])
        if not violations:
            check.status = "PASSED"
            check.message = "No hardcoded secrets detected in critical files"
        else:
            check.status = "FAILED"
            check.message = f"Hardcoded secrets detected: {len(violations)} violations"
    async def _check_dependency_mocks(self, check: SecurityCheck):
        """Check for dangerous mock implementations"""
        dangerous_patterns = [
            "class MockAsyncPG",
            "class MockConnection", 
            "asyncpg = MockAsyncPG()",
            "BaseModel:"
        ]
        file_path = 'core/clean_architecture/infrastructure.py'
        violations = []
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                for pattern in dangerous_patterns:
                    if pattern in content:
                        violations.append(pattern)
        if not violations:
            check.status = "PASSED"
            check.message = "No dangerous mock implementations detected"
        else:
            check.status = "FAILED"  
            check.message = f"Dangerous mock implementations found: {violations}"
    async def _check_environment_config(self, check: SecurityCheck):
        """Check security environment configuration"""
        if os.path.exists('.env.security'):
            check.status = "PASSED"
            check.message = "Security environment configuration file exists"
        else:
            check.status = "WARNING"
            check.message = "Security environment configuration file not found"
    async def _run_performance_gates(self):
        """Run performance regression gates"""
        logger.info("📊 Running Performance Regression Gates...")
        # Define performance baselines and thresholds
        performance_metrics = [
            PerformanceMetric(
                "startup_time_ms",
                0.0,  # Will be measured
                5000.0,  # 5 second baseline
                10.0  # 10% threshold
            ),
            PerformanceMetric(
                "memory_usage_mb", 
                0.0,  # Will be measured
                512.0,  # 512MB baseline
                15.0  # 15% threshold
            ),
            PerformanceMetric(
                "import_time_ms",
                0.0,  # Will be measured
                100.0,  # 100ms baseline
                20.0  # 20% threshold
            )
        ]
        for metric in performance_metrics:
            await self._measure_performance_metric(metric)
            self.performance_metrics.append(metric)
    async def _measure_performance_metric(self, metric: PerformanceMetric):
        """Measure individual performance metric"""
        metric.timestamp = datetime.utcnow()
        try:
            if metric.metric_name == "startup_time_ms":
                metric.current_value = await self._measure_startup_time()
            elif metric.metric_name == "memory_usage_mb":
                metric.current_value = await self._measure_memory_usage()
            elif metric.metric_name == "import_time_ms":
                metric.current_value = await self._measure_import_time()
            # Check against threshold
            percentage_change = ((metric.current_value - metric.baseline_value) / metric.baseline_value) * 100
            if abs(percentage_change) <= metric.threshold_percent:
                metric.status = "PASSED"
            elif percentage_change > metric.threshold_percent:
                metric.status = "WARNING"
            else:
                metric.status = "PASSED"  # Performance improvement
        except Exception as e:
            metric.status = "FAILED"
            logger.error(f"Performance metric {metric.metric_name} measurement failed: {e}")
    async def _measure_startup_time(self) -> float:
        """Measure application startup time"""
        # Simplified startup time measurement
        start_time = time.time()
        try:
            # Import core modules to simulate startup
            import core.clean_architecture.domain
            import orchestration.communication.acp_protocol
        except ImportError:
            pass
        end_time = time.time()
        return (end_time - start_time) * 1000
    async def _measure_memory_usage(self) -> float:
        """Measure current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return 0.0  # psutil not available
    async def _measure_import_time(self) -> float:
        """Measure core module import time"""
        start_time = time.time()
        try:
            import core.clean_architecture.infrastructure
        except ImportError:
            pass
        end_time = time.time()
        return (end_time - start_time) * 1000
    def _generate_final_report(self):
        """Generate final monitoring report"""
        # Calculate overall status
        security_failures = [c for c in self.security_checks if c.status == "FAILED"]
        performance_failures = [m for m in self.performance_metrics if m.status == "FAILED"]
        if security_failures:
            self.results["security_status"] = "FAILED"
            self.results["overall_status"] = "FAILED"
        elif any(c.status == "WARNING" for c in self.security_checks):
            self.results["security_status"] = "WARNING"
        else:
            self.results["security_status"] = "PASSED"
        if performance_failures:
            self.results["performance_status"] = "FAILED"
            if self.results["overall_status"] != "FAILED":
                self.results["overall_status"] = "FAILED"
        elif any(m.status == "WARNING" for m in self.performance_metrics):
            self.results["performance_status"] = "WARNING"
        else:
            self.results["performance_status"] = "PASSED"
        if self.results["overall_status"] == "PENDING":
            if self.results["security_status"] == "WARNING" or self.results["performance_status"] == "WARNING":
                self.results["overall_status"] = "WARNING"
            else:
                self.results["overall_status"] = "PASSED"
        # Add detailed results
        self.results["checks"] = [asdict(check) for check in self.security_checks]
        self.results["metrics"] = [asdict(metric) for metric in self.performance_metrics]
        # Generate summary
        self.results["summary"] = {
            "total_security_checks": len(self.security_checks),
            "security_checks_passed": len([c for c in self.security_checks if c.status == "PASSED"]),
            "security_checks_failed": len(security_failures),
            "total_performance_metrics": len(self.performance_metrics),
            "performance_metrics_passed": len([m for m in self.performance_metrics if m.status == "PASSED"]),
            "performance_metrics_failed": len(performance_failures),
            "phase_1_security_fixes_validated": len(security_failures) == 0
        }
    def save_results(self, file_path: str = "monitoring_gates_results.json"):
        """Save monitoring results to file"""
        with open(file_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"📄 Monitoring results saved to {file_path}")
async def main():
    """Main execution function"""
    monitor = SecurityMonitoringGates()
    results = await monitor.run_all_gates()
    # Save results
    monitor.save_results()
    # Print summary
    print("\n" + "="*60)
    print("🚀 PHASE 1 SECURITY MONITORING GATES COMPLETE")
    print("="*60)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Security Status: {results['security_status']}")
    print(f"Performance Status: {results['performance_status']}")
    print(f"Security Checks: {results['summary']['security_checks_passed']}/{results['summary']['total_security_checks']} passed")
    print(f"Performance Metrics: {results['summary']['performance_metrics_passed']}/{results['summary']['total_performance_metrics']} passed")
    # Exit with appropriate code
    if results['overall_status'] == "FAILED":
        sys.exit(1)
    elif results['overall_status'] == "WARNING":
        sys.exit(2)  
    else:
        sys.exit(0)
if __name__ == "__main__":
    asyncio.run(main())
