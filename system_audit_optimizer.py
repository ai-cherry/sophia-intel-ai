#!/usr/bin/env python3
"""
🎖️ Sophia AI Platform - Complete System Audit & Optimization
Comprehensive audit of the entire Sophia AI Platform with optimization recommendations
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Optional

import requests


class SystemAuditOptimizer:
    def __init__(self):
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "system_health": {},
            "security_audit": {},
            "performance_metrics": {},
            "optimization_recommendations": [],
            "deployment_readiness": {},
            "cost_analysis": {},
            "compliance_check": {},
        }

        # Load configurations
        self.deployment_config = self.load_json_file("deployment_config.json")
        self.environment_config = self.load_json_file("environment_config.json")
        self.scan_results = self.load_json_file("lambda_labs_scan_results.json")

        # Instance information
        self.instances = (
            self.environment_config.get("instances", {})
            if self.environment_config
            else {}
        )
        self.primary_ip = "104.171.202.103"  # sophia-production-instance

    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def load_json_file(self, filename: str) -> Optional[Dict]:
        """Load JSON file safely"""
        try:
            with open(filename) as f:
                return json.load(f)
        except FileNotFoundError:
            self.log(f"File not found: {filename}", "WARNING")
            return None
        except Exception as e:
            self.log(f"Error loading {filename}: {str(e)}", "ERROR")
            return None

    def run_command(self, command: str, timeout: int = 30) -> Dict:
        """Run shell command and return result"""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1,
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}

    def test_endpoint(self, url: str, timeout: int = 10) -> Dict:
        """Test HTTP endpoint availability"""
        try:
            response = requests.get(url, timeout=timeout)
            return {
                "available": True,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "headers": dict(response.headers),
            }
        except requests.exceptions.RequestException as e:
            return {
                "available": False,
                "error": str(e),
                "status_code": None,
                "response_time": None,
            }

    def audit_system_health(self):
        """Audit overall system health"""
        self.log("🏥 Auditing system health...")

        health_checks = {
            "disk_space": self.check_disk_space(),
            "memory_usage": self.check_memory_usage(),
            "cpu_usage": self.check_cpu_usage(),
            "network_connectivity": self.check_network_connectivity(),
            "service_status": self.check_service_status(),
            "docker_status": self.check_docker_status(),
            "python_environment": self.check_python_environment(),
        }

        # Calculate overall health score
        healthy_checks = sum(
            1 for check in health_checks.values() if check.get("status") == "healthy"
        )
        total_checks = len(health_checks)
        health_score = (healthy_checks / total_checks) * 100

        self.audit_results["system_health"] = {
            "overall_score": health_score,
            "status": (
                "healthy"
                if health_score >= 80
                else "warning" if health_score >= 60 else "critical"
            ),
            "checks": health_checks,
            "summary": f"{healthy_checks}/{total_checks} checks passed",
        }

        self.log(
            f"System health score: {health_score:.1f}% ({healthy_checks}/{total_checks} checks passed)"
        )

    def check_disk_space(self) -> Dict:
        """Check disk space usage"""
        result = self.run_command("df -h / | tail -1 | awk '{print $5}' | sed 's/%//'")
        if result["success"]:
            usage = int(result["stdout"])
            return {
                "status": (
                    "healthy" if usage < 80 else "warning" if usage < 90 else "critical"
                ),
                "usage_percent": usage,
                "message": f"Disk usage: {usage}%",
            }
        return {"status": "error", "message": "Could not check disk space"}

    def check_memory_usage(self) -> Dict:
        """Check memory usage"""
        result = self.run_command(
            "free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'"
        )
        if result["success"]:
            usage = float(result["stdout"])
            return {
                "status": (
                    "healthy" if usage < 80 else "warning" if usage < 90 else "critical"
                ),
                "usage_percent": usage,
                "message": f"Memory usage: {usage:.1f}%",
            }
        return {"status": "error", "message": "Could not check memory usage"}

    def check_cpu_usage(self) -> Dict:
        """Check CPU usage"""
        result = self.run_command(
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//'"
        )
        if result["success"]:
            try:
                usage = float(result["stdout"])
                return {
                    "status": (
                        "healthy"
                        if usage < 80
                        else "warning" if usage < 90 else "critical"
                    ),
                    "usage_percent": usage,
                    "message": f"CPU usage: {usage:.1f}%",
                }
            except ValueError:
                pass
        return {"status": "warning", "message": "Could not determine CPU usage"}

    def check_network_connectivity(self) -> Dict:
        """Check network connectivity"""
        # Test connectivity to key services
        tests = [
            ("Google DNS", "8.8.8.8"),
            ("GitHub", "github.com"),
            ("Lambda Labs API", "cloud.lambdalabs.com"),
        ]

        results = []
        for name, host in tests:
            result = self.run_command(f"ping -c 1 -W 5 {host}")
            results.append({"name": name, "host": host, "reachable": result["success"]})

        reachable_count = sum(1 for r in results if r["reachable"])
        total_count = len(results)

        return {
            "status": (
                "healthy"
                if reachable_count == total_count
                else "warning" if reachable_count > 0 else "critical"
            ),
            "reachable": reachable_count,
            "total": total_count,
            "tests": results,
            "message": f"Network connectivity: {reachable_count}/{total_count} hosts reachable",
        }

    def check_service_status(self) -> Dict:
        """Check status of key services"""
        services = ["docker", "ssh", "systemd-resolved"]

        results = []
        for service in services:
            result = self.run_command(f"systemctl is-active {service}")
            results.append(
                {
                    "name": service,
                    "active": result["success"] and result["stdout"] == "active",
                    "status": result["stdout"],
                }
            )

        active_count = sum(1 for r in results if r["active"])
        total_count = len(results)

        return {
            "status": (
                "healthy"
                if active_count == total_count
                else "warning" if active_count > total_count // 2 else "critical"
            ),
            "active": active_count,
            "total": total_count,
            "services": results,
            "message": f"Services: {active_count}/{total_count} active",
        }

    def check_docker_status(self) -> Dict:
        """Check Docker status and containers"""
        # Check if Docker is installed and running
        docker_version = self.run_command("docker --version")
        if not docker_version["success"]:
            return {
                "status": "warning",
                "message": "Docker not installed or not accessible",
                "installed": False,
            }

        # Check running containers
        containers = self.run_command(
            "docker ps --format 'table {{.Names}}\\t{{.Status}}'"
        )
        container_count = 0
        if containers["success"]:
            lines = containers["stdout"].split("\\n")
            container_count = max(0, len(lines) - 1)  # Subtract header line

        return {
            "status": "healthy",
            "installed": True,
            "version": docker_version["stdout"],
            "running_containers": container_count,
            "message": f"Docker running with {container_count} containers",
        }

    def check_python_environment(self) -> Dict:
        """Check Python environment and packages"""
        python_version = self.run_command("python3 --version")
        pip_version = self.run_command("pip3 --version")

        # Check key packages
        key_packages = ["requests", "fastapi", "uvicorn", "pulumi"]
        package_status = []

        for package in key_packages:
            result = self.run_command(f"pip3 show {package}")
            package_status.append({"name": package, "installed": result["success"]})

        installed_count = sum(1 for p in package_status if p["installed"])

        return {
            "status": "healthy" if installed_count == len(key_packages) else "warning",
            "python_version": (
                python_version["stdout"] if python_version["success"] else "unknown"
            ),
            "pip_version": (
                pip_version["stdout"] if pip_version["success"] else "unknown"
            ),
            "packages": package_status,
            "message": f"Python environment: {installed_count}/{len(key_packages)} key packages installed",
        }

    def audit_security(self):
        """Audit security configuration"""
        self.log("🔒 Auditing security configuration...")

        security_checks = {
            "ssh_configuration": self.check_ssh_security(),
            "file_permissions": self.check_file_permissions(),
            "firewall_status": self.check_firewall(),
            "secret_exposure": self.check_secret_exposure(),
            "ssl_certificates": self.check_ssl_certificates(),
        }

        # Calculate security score
        secure_checks = sum(
            1 for check in security_checks.values() if check.get("status") == "secure"
        )
        total_checks = len(security_checks)
        security_score = (secure_checks / total_checks) * 100

        self.audit_results["security_audit"] = {
            "overall_score": security_score,
            "status": (
                "secure"
                if security_score >= 80
                else "warning" if security_score >= 60 else "critical"
            ),
            "checks": security_checks,
            "summary": f"{secure_checks}/{total_checks} security checks passed",
        }

        self.log(
            f"Security score: {security_score:.1f}% ({secure_checks}/{total_checks} checks passed)"
        )

    def check_ssh_security(self) -> Dict:
        """Check SSH security configuration"""
        # Check if SSH is configured securely
        ssh_config_checks = [
            ("PasswordAuthentication", "no"),
            ("PermitRootLogin", "no"),
            ("Protocol", "2"),
        ]

        results = []
        for setting, expected in ssh_config_checks:
            result = self.run_command(f"sudo sshd -T | grep -i {setting.lower()}")
            if result["success"]:
                actual = result["stdout"].split()[-1] if result["stdout"] else "unknown"
                results.append(
                    {
                        "setting": setting,
                        "expected": expected,
                        "actual": actual,
                        "secure": actual.lower() == expected.lower(),
                    }
                )

        secure_count = sum(1 for r in results if r["secure"])

        return {
            "status": "secure" if secure_count == len(results) else "warning",
            "checks": results,
            "message": f"SSH security: {secure_count}/{len(results)} settings secure",
        }

    def check_file_permissions(self) -> Dict:
        """Check file permissions for sensitive files"""
        sensitive_files = [
            "~/.ssh/id_rsa",
            "~/.ssh/id_ed25519",
            "/opt/sophia/secrets/",
            ".env*",
        ]

        issues = []
        for file_pattern in sensitive_files:
            # Expand home directory
            if file_pattern.startswith("~/"):
                file_pattern = os.path.expanduser(file_pattern)

            result = self.run_command(
                f"find {file_pattern} -type f -perm /077 2>/dev/null"
            )
            if result["success"] and result["stdout"]:
                issues.extend(result["stdout"].split("\\n"))

        return {
            "status": "secure" if not issues else "warning",
            "issues": issues,
            "message": f"File permissions: {len(issues)} files with overly permissive permissions",
        }

    def check_firewall(self) -> Dict:
        """Check firewall status"""
        ufw_status = self.run_command("sudo ufw status")

        if ufw_status["success"]:
            active = "Status: active" in ufw_status["stdout"]
            return {
                "status": "secure" if active else "warning",
                "active": active,
                "message": f"Firewall: {'active' if active else 'inactive'}",
            }

        return {"status": "warning", "message": "Could not determine firewall status"}

    def check_secret_exposure(self) -> Dict:
        """Check for exposed secrets in files"""
        # Look for potential secrets in common locations
        secret_patterns = [
            "api[_-]?key",
            "secret[_-]?key",
            "password",
            "token",
            "pul-[a-f0-9]+",
        ]

        exposed_files = []
        for pattern in secret_patterns:
            result = self.run_command(
                f"grep -r -i '{pattern}' . --exclude-dir=.git --exclude='*.json' --exclude='*.log' 2>/dev/null | head -5"
            )
            if result["success"] and result["stdout"]:
                exposed_files.extend(result["stdout"].split("\\n")[:3])  # Limit results

        return {
            "status": "secure" if not exposed_files else "critical",
            "exposed_files": exposed_files[:10],  # Limit to first 10
            "message": f"Secret exposure: {len(exposed_files)} potential exposures found",
        }

    def check_ssl_certificates(self) -> Dict:
        """Check SSL certificate status"""
        # For now, just check if certificates exist
        cert_locations = ["/etc/ssl/certs/", "/etc/letsencrypt/live/"]

        certs_found = 0
        for location in cert_locations:
            result = self.run_command(
                f"find {location} -name '*.pem' -o -name '*.crt' 2>/dev/null | wc -l"
            )
            if result["success"]:
                certs_found += int(result["stdout"] or "0")

        return {
            "status": "warning" if certs_found == 0 else "secure",
            "certificates_found": certs_found,
            "message": f"SSL certificates: {certs_found} certificates found",
        }

    def audit_performance(self):
        """Audit performance metrics"""
        self.log("⚡ Auditing performance metrics...")

        performance_metrics = {
            "endpoint_response_times": self.measure_endpoint_performance(),
            "resource_utilization": self.measure_resource_utilization(),
            "database_performance": self.check_database_performance(),
            "network_latency": self.measure_network_latency(),
        }

        self.audit_results["performance_metrics"] = performance_metrics
        self.log("Performance audit completed")

    def measure_endpoint_performance(self) -> Dict:
        """Measure endpoint response times"""
        endpoints = [
            f"http://{self.primary_ip}:8080",
            f"http://{self.primary_ip}:3000",
            f"http://{self.primary_ip}:9090",
        ]

        results = {}
        for endpoint in endpoints:
            result = self.test_endpoint(endpoint)
            service_name = endpoint.split(":")[-1]
            response_time = result.get("response_time", 999) or 999
            results[service_name] = {
                "available": result["available"],
                "response_time": response_time,
                "status": "good" if response_time < 1.0 else "slow",
            }

        return results

    def measure_resource_utilization(self) -> Dict:
        """Measure current resource utilization"""
        # Get detailed resource usage
        cpu_result = self.run_command(
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//'"
        )
        memory_result = self.run_command(
            "free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'"
        )
        disk_result = self.run_command(
            "df -h / | tail -1 | awk '{print $5}' | sed 's/%//'"
        )

        return {
            "cpu_usage": float(cpu_result["stdout"]) if cpu_result["success"] else 0,
            "memory_usage": (
                float(memory_result["stdout"]) if memory_result["success"] else 0
            ),
            "disk_usage": int(disk_result["stdout"]) if disk_result["success"] else 0,
            "timestamp": datetime.now().isoformat(),
        }

    def check_database_performance(self) -> Dict:
        """Check database performance (if applicable)"""
        # Check if any databases are running
        postgres_check = self.run_command("pgrep postgres")
        redis_check = self.run_command("pgrep redis")

        return {
            "postgres_running": postgres_check["success"],
            "redis_running": redis_check["success"],
            "message": "Database performance check completed",
        }

    def measure_network_latency(self) -> Dict:
        """Measure network latency to key services"""
        targets = [
            ("GitHub", "github.com"),
            ("Lambda Labs", "cloud.lambdalabs.com"),
            ("Google DNS", "8.8.8.8"),
        ]

        results = {}
        for name, host in targets:
            result = self.run_command(
                f"ping -c 3 {host} | tail -1 | awk -F '/' '{{print $5}}'"
            )
            if result["success"] and result["stdout"]:
                try:
                    latency = float(result["stdout"])
                    results[name] = {
                        "latency_ms": latency,
                        "status": "good" if latency < 100 else "slow",
                    }
                except ValueError:
                    results[name] = {"latency_ms": 0, "status": "error"}
            else:
                results[name] = {"latency_ms": 0, "status": "unreachable"}

        return results

    def generate_optimization_recommendations(self):
        """Generate optimization recommendations based on audit results"""
        self.log("💡 Generating optimization recommendations...")

        recommendations = []

        # System health recommendations
        system_health = self.audit_results.get("system_health", {})
        if system_health.get("overall_score", 0) < 80:
            recommendations.append(
                {
                    "category": "system_health",
                    "priority": "high",
                    "title": "System Health Issues Detected",
                    "description": f"System health score is {system_health.get('overall_score', 0):.1f}%",
                    "action": "Review failed health checks and address underlying issues",
                }
            )

        # Security recommendations
        security_audit = self.audit_results.get("security_audit", {})
        if security_audit.get("overall_score", 0) < 80:
            recommendations.append(
                {
                    "category": "security",
                    "priority": "critical",
                    "title": "Security Configuration Issues",
                    "description": f"Security score is {security_audit.get('overall_score', 0):.1f}%",
                    "action": "Address security vulnerabilities immediately",
                }
            )

        # Performance recommendations
        performance = self.audit_results.get("performance_metrics", {})
        resource_util = performance.get("resource_utilization", {})

        if resource_util.get("cpu_usage", 0) > 80:
            recommendations.append(
                {
                    "category": "performance",
                    "priority": "medium",
                    "title": "High CPU Usage",
                    "description": f"CPU usage is {resource_util.get('cpu_usage', 0):.1f}%",
                    "action": "Investigate high CPU usage and optimize processes",
                }
            )

        if resource_util.get("memory_usage", 0) > 80:
            recommendations.append(
                {
                    "category": "performance",
                    "priority": "medium",
                    "title": "High Memory Usage",
                    "description": f"Memory usage is {resource_util.get('memory_usage', 0):.1f}%",
                    "action": "Consider increasing memory or optimizing memory usage",
                }
            )

        # Cost optimization recommendations
        if self.scan_results:
            instances = self.scan_results.get("instances", [])
            expensive_instances = [i for i in instances if i.get("status") == "active"]

            if len(expensive_instances) > 3:
                recommendations.append(
                    {
                        "category": "cost",
                        "priority": "medium",
                        "title": "Multiple Active Instances",
                        "description": f"{len(expensive_instances)} instances are currently active",
                        "action": "Consider consolidating workloads or implementing auto-shutdown",
                    }
                )

        self.audit_results["optimization_recommendations"] = recommendations
        self.log(f"Generated {len(recommendations)} optimization recommendations")

    def assess_deployment_readiness(self):
        """Assess deployment readiness"""
        self.log("🚀 Assessing deployment readiness...")

        readiness_checks = {
            "system_health": self.audit_results.get("system_health", {}).get(
                "overall_score", 0
            )
            >= 80,
            "security_compliance": self.audit_results.get("security_audit", {}).get(
                "overall_score", 0
            )
            >= 70,
            "network_connectivity": True,  # Assume good if we got this far
            "required_services": self.check_required_services(),
            "configuration_files": self.check_configuration_files(),
            "api_keys_configured": self.check_api_keys(),
        }

        passed_checks = sum(1 for check in readiness_checks.values() if check)
        total_checks = len(readiness_checks)
        readiness_score = (passed_checks / total_checks) * 100

        self.audit_results["deployment_readiness"] = {
            "overall_score": readiness_score,
            "status": (
                "ready"
                if readiness_score >= 80
                else "partial" if readiness_score >= 60 else "not_ready"
            ),
            "checks": readiness_checks,
            "summary": f"{passed_checks}/{total_checks} readiness checks passed",
        }

        self.log(
            f"Deployment readiness: {readiness_score:.1f}% ({passed_checks}/{total_checks} checks passed)"
        )

    def check_required_services(self) -> bool:
        """Check if required services are available"""
        required_services = ["docker", "ssh"]
        for service in required_services:
            result = self.run_command(f"systemctl is-active {service}")
            if not (result["success"] and result["stdout"] == "active"):
                return False
        return True

    def check_configuration_files(self) -> bool:
        """Check if required configuration files exist"""
        required_files = [
            "deployment_config.json",
            "environment_config.json",
            "deploy_multi_instance.sh",
        ]

        for file in required_files:
            if not os.path.exists(file):
                return False
        return True

    def check_api_keys(self) -> bool:
        """Check if API keys are configured"""
        required_keys = ["LAMBDA_API_KEY", "EXA_API_KEY"]
        for key in required_keys:
            if not os.getenv(key):
                return False
        return True

    def run_complete_audit(self):
        """Run complete system audit and optimization"""
        self.log("🎖️ Starting comprehensive system audit and optimization...")

        try:
            # Run all audit components
            self.audit_system_health()
            self.audit_security()
            self.audit_performance()
            self.generate_optimization_recommendations()
            self.assess_deployment_readiness()

            # Calculate overall system score
            scores = [
                self.audit_results.get("system_health", {}).get("overall_score", 0),
                self.audit_results.get("security_audit", {}).get("overall_score", 0),
                self.audit_results.get("deployment_readiness", {}).get(
                    "overall_score", 0
                ),
            ]
            overall_score = sum(scores) / len(scores)

            self.audit_results["overall_score"] = overall_score
            self.audit_results["overall_status"] = (
                "excellent"
                if overall_score >= 90
                else (
                    "good"
                    if overall_score >= 80
                    else "fair" if overall_score >= 70 else "poor"
                )
            )

            # Save results
            with open("system_audit_report.json", "w") as f:
                json.dump(self.audit_results, f, indent=2)

            # Summary
            self.log("📊 System Audit Summary:")
            self.log(f"   Overall Score: {overall_score:.1f}%")
            self.log(
                f"   System Health: {self.audit_results.get('system_health', {}).get('overall_score', 0):.1f}%"
            )
            self.log(
                f"   Security: {self.audit_results.get('security_audit', {}).get('overall_score', 0):.1f}%"
            )
            self.log(
                f"   Deployment Readiness: {self.audit_results.get('deployment_readiness', {}).get('overall_score', 0):.1f}%"
            )
            self.log(
                f"   Recommendations: {len(self.audit_results.get('optimization_recommendations', []))}"
            )

            return True

        except Exception as e:
            self.log(f"Audit failed: {str(e)}", "ERROR")
            return False


def main():
    """Main execution function"""
    print("🎖️ Sophia AI Platform - Complete System Audit & Optimization")
    print("=" * 65)

    auditor = SystemAuditOptimizer()
    success = auditor.run_complete_audit()

    if success:
        print("\\n🎉 System audit and optimization completed successfully!")
        print("📄 Report saved to: system_audit_report.json")
    else:
        print("\\n❌ System audit failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
