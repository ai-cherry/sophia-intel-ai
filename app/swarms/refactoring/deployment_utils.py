"""
Deployment Management Utilities for Code Refactoring Swarm
Handles initialization, health checks, and operational management
"""

import json
import logging
import shutil
import time
from pathlib import Path
from typing import Any, Optional

from app.swarms.refactoring.code_refactoring_swarm import (
    CodeRefactoringSwarm,
    RefactoringRisk,
    RefactoringType,
)
from app.swarms.refactoring.refactoring_swarm_config import (
    DeploymentEnvironment,
    RefactoringSwarmConfiguration,
)

logger = logging.getLogger(__name__)


class SwarmDeploymentManager:
    """Manages deployment and lifecycle of Code Refactoring Swarm"""

    def __init__(self, config: RefactoringSwarmConfiguration):
        self.config = config
        self.swarm: Optional[CodeRefactoringSwarm] = None
        self.deployment_path = Path.cwd() / "deployment" / "refactoring_swarm"
        self.is_healthy = False
        self.deployment_time: Optional[float] = None

    async def deploy(self) -> bool:
        """Deploy the refactoring swarm with full initialization"""
        try:
            logger.info(
                f"Deploying Code Refactoring Swarm in {self.config.environment.value} environment"
            )

            # Validate configuration
            validation_issues = self.config.validate()
            if validation_issues:
                logger.error(f"Configuration validation failed: {validation_issues}")
                return False

            # Create deployment directory structure
            await self._setup_deployment_structure()

            # Save configuration
            await self._save_configuration()

            # Initialize swarm
            self.swarm = CodeRefactoringSwarm(self.config.to_dict())
            await self.swarm.initialize()

            # Run health checks
            health_status = await self.health_check()
            if not health_status["healthy"]:
                logger.error(f"Health check failed: {health_status}")
                return False

            self.deployment_time = time.time()
            self.is_healthy = True

            logger.info("Code Refactoring Swarm deployed successfully")
            return True

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

    async def _setup_deployment_structure(self):
        """Create deployment directory structure"""
        directories = [
            self.deployment_path / "config",
            self.deployment_path / "logs",
            self.deployment_path / "sessions",
            self.deployment_path / "backups",
            self.deployment_path / "metrics",
            self.deployment_path / "temp",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"Deployment structure created at {self.deployment_path}")

    async def _save_configuration(self):
        """Save configuration to deployment directory"""
        config_file = self.deployment_path / "config" / "swarm_config.json"
        with open(config_file, "w") as f:
            json.dump(self.config.to_dict(), f, indent=2)

        logger.info(f"Configuration saved to {config_file}")

    async def health_check(self) -> dict[str, Any]:
        """Comprehensive health check of the swarm"""
        health_status = {
            "healthy": True,
            "timestamp": time.time(),
            "checks": {},
            "warnings": [],
            "errors": [],
        }

        try:
            # Check swarm initialization
            if not self.swarm:
                health_status["healthy"] = False
                health_status["errors"].append("Swarm not initialized")
                return health_status

            health_status["checks"]["swarm_initialized"] = True

            # Check agent initialization
            agent_count = len(self.swarm.agents)
            expected_agent_count = 10  # Based on our swarm design

            if agent_count < expected_agent_count:
                health_status["warnings"].append(
                    f"Expected {expected_agent_count} agents, found {agent_count}"
                )

            health_status["checks"]["agents_initialized"] = agent_count

            # Check memory client
            if hasattr(self.swarm, "memory_client") and self.swarm.memory_client:
                health_status["checks"]["memory_enabled"] = True
            else:
                health_status["warnings"].append("Memory client not available")
                health_status["checks"]["memory_enabled"] = False

            # Check deployment structure
            required_dirs = ["config", "logs", "sessions", "backups"]
            for dir_name in required_dirs:
                dir_path = self.deployment_path / dir_name
                if not dir_path.exists():
                    health_status["errors"].append(
                        f"Required directory missing: {dir_name}"
                    )
                    health_status["healthy"] = False
                else:
                    health_status["checks"][f"directory_{dir_name}"] = True

            # Check configuration validity
            config_issues = self.config.validate()
            if config_issues:
                health_status["errors"].extend(config_issues)
                health_status["healthy"] = False
            else:
                health_status["checks"]["configuration_valid"] = True

            # Resource availability checks
            import psutil

            # Memory check
            memory = psutil.virtual_memory()
            required_memory_mb = (
                self.config.resources.max_concurrent_agents
                * self.config.resources.max_memory_per_agent_mb
            )
            available_memory_mb = memory.available // 1024 // 1024

            if available_memory_mb < required_memory_mb:
                health_status["warnings"].append(
                    f"Low memory: need {required_memory_mb}MB, available {available_memory_mb}MB"
                )

            health_status["checks"]["memory_available_mb"] = available_memory_mb
            health_status["checks"]["memory_required_mb"] = required_memory_mb

            # CPU check
            cpu_count = psutil.cpu_count()
            if cpu_count < self.config.resources.max_concurrent_agents:
                health_status["warnings"].append(
                    f"Limited CPU cores: {cpu_count} cores for {self.config.resources.max_concurrent_agents} agents"
                )

            health_status["checks"]["cpu_cores"] = cpu_count

            logger.info(
                f"Health check completed: {'HEALTHY' if health_status['healthy'] else 'UNHEALTHY'}"
            )

        except Exception as e:
            health_status["healthy"] = False
            health_status["errors"].append(f"Health check failed: {str(e)}")
            logger.error(f"Health check error: {e}")

        return health_status

    async def execute_test_session(
        self, test_codebase_path: str = None
    ) -> dict[str, Any]:
        """Execute a test refactoring session to validate deployment"""
        if not self.swarm:
            return {"success": False, "error": "Swarm not deployed"}

        # Use current directory as test codebase if not specified
        test_path = test_codebase_path or str(Path.cwd())

        try:
            logger.info("Executing test refactoring session")

            # Run a safe dry-run session
            result = await self.swarm.execute_refactoring_session(
                codebase_path=test_path,
                refactoring_types=[RefactoringType.QUALITY],
                risk_tolerance=RefactoringRisk.LOW,
                dry_run=True,
            )

            test_result = {
                "success": result.success,
                "session_id": result.plan_id,
                "execution_time": result.execution_time,
                "opportunities_found": len(result.executed_opportunities),
                "test_completed": True,
            }

            logger.info(f"Test session completed: {test_result}")
            return test_result

        except Exception as e:
            logger.error(f"Test session failed: {e}")
            return {"success": False, "error": str(e), "test_completed": False}

    async def shutdown(self) -> bool:
        """Gracefully shutdown the swarm"""
        try:
            logger.info("Shutting down Code Refactoring Swarm")

            if self.swarm:
                await self.swarm.cleanup()
                self.swarm = None

            self.is_healthy = False
            logger.info("Swarm shutdown completed")
            return True

        except Exception as e:
            logger.error(f"Shutdown failed: {e}")
            return False

    def get_status(self) -> dict[str, Any]:
        """Get current deployment status"""
        return {
            "deployed": self.swarm is not None,
            "healthy": self.is_healthy,
            "environment": self.config.environment.value,
            "deployment_time": self.deployment_time,
            "uptime_seconds": (
                time.time() - self.deployment_time if self.deployment_time else 0
            ),
            "configuration": {
                "swarm_name": self.config.swarm_name,
                "version": self.config.version,
                "agents_configured": len(self.swarm.agents) if self.swarm else 0,
            },
        }

    async def create_backup(self) -> str:
        """Create backup of current deployment"""
        try:
            backup_timestamp = int(time.time())
            backup_name = f"refactoring_swarm_backup_{backup_timestamp}"
            backup_path = self.deployment_path / "backups" / backup_name

            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)

            # Backup configuration
            config_backup = backup_path / "config.json"
            shutil.copy2(
                self.deployment_path / "config" / "swarm_config.json", config_backup
            )

            # Backup session data if it exists
            sessions_dir = self.deployment_path / "sessions"
            if sessions_dir.exists():
                backup_sessions = backup_path / "sessions"
                shutil.copytree(sessions_dir, backup_sessions, dirs_exist_ok=True)

            # Create backup manifest
            manifest = {
                "backup_name": backup_name,
                "timestamp": backup_timestamp,
                "environment": self.config.environment.value,
                "version": self.config.version,
                "files": ["config.json", "sessions/"],
            }

            manifest_file = backup_path / "manifest.json"
            with open(manifest_file, "w") as f:
                json.dump(manifest, f, indent=2)

            logger.info(f"Backup created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise

    async def restore_from_backup(self, backup_path: str) -> bool:
        """Restore deployment from backup"""
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                raise ValueError(f"Backup path does not exist: {backup_path}")

            # Read backup manifest
            manifest_file = backup_dir / "manifest.json"
            with open(manifest_file) as f:
                manifest = json.load(f)

            logger.info(f"Restoring from backup: {manifest['backup_name']}")

            # Restore configuration
            config_backup = backup_dir / "config.json"
            if config_backup.exists():
                shutil.copy2(
                    config_backup, self.deployment_path / "config" / "swarm_config.json"
                )

            # Restore sessions
            sessions_backup = backup_dir / "sessions"
            if sessions_backup.exists():
                sessions_target = self.deployment_path / "sessions"
                if sessions_target.exists():
                    shutil.rmtree(sessions_target)
                shutil.copytree(sessions_backup, sessions_target)

            logger.info("Backup restoration completed")
            return True

        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return False


class SwarmOperations:
    """High-level operations for managing refactoring swarm"""

    @staticmethod
    async def quick_deploy(
        environment: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT,
    ) -> SwarmDeploymentManager:
        """Quick deployment with environment-specific configuration"""
        config = RefactoringSwarmConfiguration.for_environment(environment)
        manager = SwarmDeploymentManager(config)

        success = await manager.deploy()
        if not success:
            raise RuntimeError(
                f"Failed to deploy swarm in {environment.value} environment"
            )

        return manager

    @staticmethod
    async def deploy_from_config_file(config_file_path: str) -> SwarmDeploymentManager:
        """Deploy swarm from configuration file"""
        with open(config_file_path) as f:
            config_data = json.load(f)

        config = RefactoringSwarmConfiguration.from_dict(config_data)
        manager = SwarmDeploymentManager(config)

        success = await manager.deploy()
        if not success:
            raise RuntimeError(
                f"Failed to deploy swarm from config: {config_file_path}"
            )

        return manager

    @staticmethod
    async def production_deployment_checklist(
        config: RefactoringSwarmConfiguration,
    ) -> list[dict[str, Any]]:
        """Generate production deployment readiness checklist"""
        checklist = []

        # Configuration checks
        config_issues = config.validate()
        checklist.append(
            {
                "category": "Configuration",
                "check": "Configuration validation",
                "status": "PASS" if not config_issues else "FAIL",
                "details": config_issues if config_issues else "Configuration is valid",
            }
        )

        # Safety checks
        safety_checks = [
            ("Backups required", config.safety.require_backup),
            ("Tests required", config.safety.require_tests),
            (
                "Risk approval configured",
                bool(config.safety.approval_required_for_risk),
            ),
            ("Forbidden paths configured", bool(config.safety.forbidden_paths)),
        ]

        for check_name, condition in safety_checks:
            checklist.append(
                {
                    "category": "Safety",
                    "check": check_name,
                    "status": "PASS" if condition else "FAIL",
                    "details": f"Status: {condition}",
                }
            )

        # Resource checks
        checklist.append(
            {
                "category": "Resources",
                "check": "Circuit breaker configured",
                "status": (
                    "PASS"
                    if config.resources.circuit_breaker_threshold <= 3
                    else "WARN"
                ),
                "details": f"Threshold: {config.resources.circuit_breaker_threshold}",
            }
        )

        # Monitoring checks
        monitoring_checks = [
            ("Alerts enabled", config.monitoring.alerts_enabled),
            ("Metrics enabled", config.monitoring.metrics_enabled),
            ("Logging enabled", config.monitoring.logging_enabled),
        ]

        for check_name, condition in monitoring_checks:
            checklist.append(
                {
                    "category": "Monitoring",
                    "check": check_name,
                    "status": "PASS" if condition else "WARN",
                    "details": f"Status: {condition}",
                }
            )

        # Integration checks
        if config.environment == DeploymentEnvironment.PRODUCTION:
            checklist.append(
                {
                    "category": "Integration",
                    "check": "CI/CD integration",
                    "status": "PASS" if config.ci_cd_integration else "WARN",
                    "details": f"CI/CD enabled: {config.ci_cd_integration}",
                }
            )

        return checklist

    @staticmethod
    async def run_comprehensive_test(manager: SwarmDeploymentManager) -> dict[str, Any]:
        """Run comprehensive testing suite on deployed swarm"""
        test_results = {
            "overall_status": "PASS",
            "test_timestamp": time.time(),
            "tests": {},
        }

        try:
            # Health check
            health_status = await manager.health_check()
            test_results["tests"]["health_check"] = {
                "status": "PASS" if health_status["healthy"] else "FAIL",
                "details": health_status,
            }

            # Test session execution
            session_result = await manager.execute_test_session()
            test_results["tests"]["test_session"] = {
                "status": "PASS" if session_result["success"] else "FAIL",
                "details": session_result,
            }

            # Configuration validation
            config_issues = manager.config.validate()
            test_results["tests"]["configuration"] = {
                "status": "PASS" if not config_issues else "FAIL",
                "details": config_issues,
            }

            # Backup/restore test
            try:
                backup_path = await manager.create_backup()
                test_results["tests"]["backup_creation"] = {
                    "status": "PASS",
                    "details": f"Backup created at {backup_path}",
                }
            except Exception as e:
                test_results["tests"]["backup_creation"] = {
                    "status": "FAIL",
                    "details": str(e),
                }

            # Determine overall status
            failed_tests = [
                test
                for test in test_results["tests"].values()
                if test["status"] == "FAIL"
            ]

            if failed_tests:
                test_results["overall_status"] = "FAIL"
                test_results["failed_count"] = len(failed_tests)

            test_results["passed_count"] = len(
                [
                    test
                    for test in test_results["tests"].values()
                    if test["status"] == "PASS"
                ]
            )

        except Exception as e:
            test_results["overall_status"] = "ERROR"
            test_results["error"] = str(e)

        return test_results


# Convenience functions for common deployment scenarios
async def deploy_development_swarm() -> SwarmDeploymentManager:
    """Deploy swarm for development environment"""
    return await SwarmOperations.quick_deploy(DeploymentEnvironment.DEVELOPMENT)


async def deploy_production_swarm() -> SwarmDeploymentManager:
    """Deploy swarm for production environment with full validation"""
    config = RefactoringSwarmConfiguration.for_environment(
        DeploymentEnvironment.PRODUCTION
    )

    # Run production readiness checklist
    checklist = await SwarmOperations.production_deployment_checklist(config)
    failed_checks = [check for check in checklist if check["status"] == "FAIL"]

    if failed_checks:
        raise RuntimeError(
            f"Production deployment blocked by {len(failed_checks)} failed checks"
        )

    manager = SwarmDeploymentManager(config)
    success = await manager.deploy()

    if not success:
        raise RuntimeError("Production deployment failed")

    # Run comprehensive tests
    test_results = await SwarmOperations.run_comprehensive_test(manager)
    if test_results["overall_status"] != "PASS":
        await manager.shutdown()
        raise RuntimeError(f"Production deployment tests failed: {test_results}")

    return manager
