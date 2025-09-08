"""
Environment Guard Agent - Ensures stable development environment
Monitors and maintains devcontainer stability with cloud-locked configuration
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from agents.core.base_agent import (
    AgentCapability,
    AgentConfig,
    BaseAgent,
    ResilienceConfig,
)

logger = structlog.get_logger(__name__)


class EnvironmentGuardAgent(BaseAgent):
    """
    Environment Guard Agent - Maintains stable development environment
    Prevents environment drift and ensures cloud-locked configuration
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="env_guard",
            agent_name="Environment Guard",
            agent_type="environment_guardian",
            capabilities=[
                AgentCapability.MONITORING,
                AgentCapability.MAINTENANCE,
            ],
            resilience=ResilienceConfig(
                enabled=True,
                max_retries=5,
                guardian_enabled=False,
                auto_recovery=True,
                checkpoint_interval=60,
            ),
        )
        super().__init__(config)

        # Environment configuration
        self.expected_env = {
            "VIRTUAL_ENV": "/opt/venv",
            "PYTHONPATH": "${WORKSPACE_ROOT:-${WORKSPACE_ROOT:-/workspaces/sophia-main}}",
            "LANGROID_CLOUD_MODE": "true",
            "ENVIRONMENT": "cloud-development",
        }

        # Critical paths
        self.critical_paths = [
            "/opt/venv",
            "${WORKSPACE_ROOT:-${WORKSPACE_ROOT:-/workspaces/sophia-main}}",
            "/opt/env-guard.sh",
        ]

        # Environment drift detection
        self.drift_threshold = 5  # seconds
        self.last_env_check = None
        self.drift_count = 0

        logger.info("Environment Guard Agent initialized")

    async def _execute_task_impl(
        self, task: dict[str, Any], context: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Execute environment guard tasks"""

        task_type = task.get("type", "check_environment")

        if task_type == "check_environment":
            return await self._check_environment()
        elif task_type == "fix_environment":
            return await self._fix_environment()
        elif task_type == "monitor_drift":
            return await self._monitor_drift()
        elif task_type == "enforce_stability":
            return await self._enforce_stability()
        else:
            raise ValueError(f"Unknown environment guard task: {task_type}")

    async def _check_environment(self) -> dict[str, Any]:
        """Comprehensive environment check"""

        check_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {
                "virtual_env": await self._check_virtual_env(),
                "python_path": await self._check_python_path(),
                "agno_mode": await self._check_agno_mode(),
                "critical_paths": await self._check_critical_paths(),
                "cloud_connectivity": await self._check_cloud_connectivity(),
                "environment_variables": await self._check_environment_variables(),
            },
            "issues": [],
            "fixes_applied": [],
        }

        # Analyze results
        for check_name, check_result in check_results["checks"].items():
            if not check_result["status"]:
                check_results["issues"].append(
                    {
                        "check": check_name,
                        "issue": check_result["message"],
                        "severity": check_result.get("severity", "medium"),
                    }
                )

        # Determine overall status
        critical_issues = [
            issue for issue in check_results["issues"] if issue["severity"] == "critical"
        ]
        if critical_issues:
            check_results["overall_status"] = "critical"
        elif check_results["issues"]:
            check_results["overall_status"] = "degraded"

        # Auto-fix if needed
        if check_results["issues"]:
            fix_results = await self._auto_fix_issues(check_results["issues"])
            check_results["fixes_applied"] = fix_results["fixes_applied"]

            # Re-check after fixes
            if fix_results["fixes_applied"]:
                logger.info(
                    "Re-checking environment after fixes",
                    fixes_count=len(fix_results["fixes_applied"]),
                )

                # Quick re-check of fixed items
                for fix in fix_results["fixes_applied"]:
                    if fix["check"] == "virtual_env":
                        check_results["checks"]["virtual_env"] = await self._check_virtual_env()
                    elif fix["check"] == "agno_mode":
                        check_results["checks"]["agno_mode"] = await self._check_agno_mode()

        logger.info(
            "Environment check completed",
            status=check_results["overall_status"],
            issues=len(check_results["issues"]),
            fixes=len(check_results["fixes_applied"]),
        )

        return check_results

    async def _check_virtual_env(self) -> dict[str, Any]:
        """Check virtual environment status"""

        current_venv = os.getenv("VIRTUAL_ENV")
        expected_venv = self.expected_env["VIRTUAL_ENV"]

        if current_venv == expected_venv:
            return {
                "status": True,
                "message": f"Virtual environment correct: {current_venv}",
                "current": current_venv,
                "expected": expected_venv,
            }
        else:
            return {
                "status": False,
                "message": f"Virtual environment drift: expected {expected_venv}, got {current_venv}",
                "current": current_venv,
                "expected": expected_venv,
                "severity": "critical",
            }

    async def _check_python_path(self) -> dict[str, Any]:
        """Check Python path configuration"""

        current_pythonpath = os.getenv("PYTHONPATH", "")
        expected_path = self.expected_env["PYTHONPATH"]

        if expected_path in current_pythonpath:
            return {
                "status": True,
                "message": f"Python path includes workspace: {expected_path}",
                "current": current_pythonpath,
                "expected": expected_path,
            }
        else:
            return {
                "status": False,
                "message": f"Python path missing workspace: {expected_path}",
                "current": current_pythonpath,
                "expected": expected_path,
                "severity": "medium",
            }

    async def _check_agno_mode(self) -> dict[str, Any]:
        """Check Agno cloud mode status"""

        current_mode = os.getenv("LANGROID_CLOUD_MODE", "false")
        expected_mode = self.expected_env["LANGROID_CLOUD_MODE"]

        if current_mode == expected_mode:
            return {
                "status": True,
                "message": f"Agno cloud mode correct: {current_mode}",
                "current": current_mode,
                "expected": expected_mode,
            }
        else:
            return {
                "status": False,
                "message": f"Agno cloud mode incorrect: expected {expected_mode}, got {current_mode}",
                "current": current_mode,
                "expected": expected_mode,
                "severity": "high",
            }

    async def _check_critical_paths(self) -> dict[str, Any]:
        """Check existence of critical paths"""

        missing_paths = []
        existing_paths = []

        for path in self.critical_paths:
            if Path(path).exists():
                existing_paths.append(path)
            else:
                missing_paths.append(path)

        if not missing_paths:
            return {
                "status": True,
                "message": f"All critical paths exist: {len(existing_paths)} paths",
                "existing": existing_paths,
                "missing": missing_paths,
            }
        else:
            return {
                "status": False,
                "message": f"Missing critical paths: {missing_paths}",
                "existing": existing_paths,
                "missing": missing_paths,
                "severity": "critical",
            }

    async def _check_cloud_connectivity(self) -> dict[str, Any]:
        """Check cloud service connectivity"""

        connectivity_results = {"qdrant": False, "redis": False, "github": False}

        # Check Qdrant
        qdrant_url = os.getenv("QDRANT_URL")
        if qdrant_url:
            try:
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{qdrant_url}/health", timeout=5) as response:
                        connectivity_results["qdrant"] = response.status == 200
            except:
                connectivity_results["qdrant"] = False

        # Check Redis
        redis_url = os.getenv("REDIS_URL")
        if redis_url and self.redis_client:
            try:
                await asyncio.to_thread(self.redis_client.ping)
                connectivity_results["redis"] = True
            except:
                connectivity_results["redis"] = False

        # Check GitHub
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.github.com", timeout=5) as response:
                    connectivity_results["github"] = response.status == 200
        except:
            connectivity_results["github"] = False

        connected_services = sum(connectivity_results.values())
        total_services = len(connectivity_results)

        if connected_services == total_services:
            return {
                "status": True,
                "message": f"All cloud services connected: {connected_services}/{total_services}",
                "connectivity": connectivity_results,
            }
        else:
            return {
                "status": False,
                "message": f"Cloud connectivity issues: {connected_services}/{total_services} services",
                "connectivity": connectivity_results,
                "severity": "medium",
            }

    async def _check_environment_variables(self) -> dict[str, Any]:
        """Check required environment variables"""

        required_vars = ["VIRTUAL_ENV", "PYTHONPATH", "LANGROID_CLOUD_MODE", "ENVIRONMENT"]

        missing_vars = []
        present_vars = []

        for var in required_vars:
            if os.getenv(var):
                present_vars.append(var)
            else:
                missing_vars.append(var)

        if not missing_vars:
            return {
                "status": True,
                "message": f"All required environment variables present: {len(present_vars)}",
                "present": present_vars,
                "missing": missing_vars,
            }
        else:
            return {
                "status": False,
                "message": f"Missing environment variables: {missing_vars}",
                "present": present_vars,
                "missing": missing_vars,
                "severity": "high",
            }

    async def _auto_fix_issues(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """Automatically fix detected issues"""

        fix_results = {
            "fixes_attempted": 0,
            "fixes_successful": 0,
            "fixes_applied": [],
            "fix_errors": [],
        }

        for issue in issues:
            try:
                fix_results["fixes_attempted"] += 1

                if issue["check"] == "virtual_env":
                    success = await self._fix_virtual_env()
                    if success:
                        fix_results["fixes_successful"] += 1
                        fix_results["fixes_applied"].append(
                            {
                                "check": "virtual_env",
                                "action": "activated_virtual_environment",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                elif issue["check"] == "python_path":
                    success = await self._fix_python_path()
                    if success:
                        fix_results["fixes_successful"] += 1
                        fix_results["fixes_applied"].append(
                            {
                                "check": "python_path",
                                "action": "updated_python_path",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                elif issue["check"] == "agno_mode":
                    success = await self._fix_agno_mode()
                    if success:
                        fix_results["fixes_successful"] += 1
                        fix_results["fixes_applied"].append(
                            {
                                "check": "agno_mode",
                                "action": "enabled_agno_cloud_mode",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                elif issue["check"] == "environment_variables":
                    success = await self._fix_environment_variables()
                    if success:
                        fix_results["fixes_successful"] += 1
                        fix_results["fixes_applied"].append(
                            {
                                "check": "environment_variables",
                                "action": "restored_environment_variables",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

            except Exception as e:
                fix_results["fix_errors"].append(
                    {
                        "check": issue["check"],
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                logger.error("Fix failed", check=issue["check"], error=str(e))

        logger.info(
            "Auto-fix completed",
            attempted=fix_results["fixes_attempted"],
            successful=fix_results["fixes_successful"],
            errors=len(fix_results["fix_errors"]),
        )

        return fix_results

    async def _fix_virtual_env(self) -> bool:
        """Fix virtual environment activation"""

        try:
            expected_venv = self.expected_env["VIRTUAL_ENV"]

            if Path(expected_venv).exists():
                # Update environment variables
                os.environ["VIRTUAL_ENV"] = expected_venv
                os.environ["PATH"] = f"{expected_venv}/bin:" + os.environ.get("PATH", "")

                logger.info("Virtual environment fixed", venv=expected_venv)
                return True
            else:
                logger.error("Virtual environment path does not exist", path=expected_venv)
                return False

        except Exception as e:
            logger.error("Failed to fix virtual environment", error=str(e))
            return False

    async def _fix_python_path(self) -> bool:
        """Fix Python path configuration"""

        try:
            expected_path = self.expected_env["PYTHONPATH"]
            current_pythonpath = os.environ.get("PYTHONPATH", "")

            if expected_path not in current_pythonpath:
                if current_pythonpath:
                    os.environ["PYTHONPATH"] = f"{expected_path}:{current_pythonpath}"
                else:
                    os.environ["PYTHONPATH"] = expected_path

                logger.info("Python path fixed", pythonpath=os.environ["PYTHONPATH"])
                return True

            return True

        except Exception as e:
            logger.error("Failed to fix Python path", error=str(e))
            return False

    async def _fix_agno_mode(self) -> bool:
        """Fix Agno cloud mode configuration"""

        try:
            expected_mode = self.expected_env["LANGROID_CLOUD_MODE"]
            os.environ["LANGROID_CLOUD_MODE"] = expected_mode

            logger.info("Agno cloud mode fixed", mode=expected_mode)
            return True

        except Exception as e:
            logger.error("Failed to fix Agno mode", error=str(e))
            return False

    async def _fix_environment_variables(self) -> bool:
        """Fix missing environment variables"""

        try:
            for var, value in self.expected_env.items():
                if not os.getenv(var):
                    os.environ[var] = value
                    logger.info("Environment variable restored", var=var, value=value)

            return True

        except Exception as e:
            logger.error("Failed to fix environment variables", error=str(e))
            return False

    async def _fix_environment(self) -> dict[str, Any]:
        """Fix environment issues (task implementation)"""

        # First check what needs fixing
        check_results = await self._check_environment()

        if check_results["overall_status"] == "healthy":
            return {
                "status": "no_fixes_needed",
                "message": "Environment is already healthy",
            }

        # Apply fixes
        fix_results = await self._auto_fix_issues(check_results["issues"])

        # Re-check after fixes
        post_fix_check = await self._check_environment()

        return {
            "status": "fixes_applied",
            "pre_fix_status": check_results["overall_status"],
            "post_fix_status": post_fix_check["overall_status"],
            "fixes_applied": fix_results["fixes_applied"],
            "remaining_issues": post_fix_check["issues"],
        }

    async def _monitor_drift(self) -> dict[str, Any]:
        """Monitor for environment drift"""

        current_time = datetime.now()

        if self.last_env_check:
            time_since_check = (current_time - self.last_env_check).total_seconds()

            if time_since_check > self.drift_threshold:
                self.drift_count += 1

                logger.warning(
                    "Environment drift detected",
                    time_since_check=time_since_check,
                    drift_count=self.drift_count,
                )

        self.last_env_check = current_time

        # Perform environment check
        check_results = await self._check_environment()

        return {
            "drift_monitoring": {
                "drift_count": self.drift_count,
                "last_check": current_time.isoformat(),
                "drift_threshold": self.drift_threshold,
            },
            "environment_status": check_results,
        }

    async def _enforce_stability(self) -> dict[str, Any]:
        """Enforce environment stability"""

        enforcement_results = {
            "timestamp": datetime.now().isoformat(),
            "actions_taken": [],
            "stability_score": 100,
        }

        # Check environment
        check_results = await self._check_environment()

        # Calculate stability score
        total_checks = len(check_results["checks"])
        passed_checks = sum(1 for check in check_results["checks"].values() if check["status"])
        enforcement_results["stability_score"] = int((passed_checks / total_checks) * 100)

        # Take enforcement actions based on issues
        if check_results["issues"]:
            # Apply fixes
            fix_results = await self._auto_fix_issues(check_results["issues"])
            enforcement_results["actions_taken"].extend(
                [f"fixed_{fix['check']}" for fix in fix_results["fixes_applied"]]
            )

            # Create stability checkpoint
            if self.redis_client:
                try:
                    stability_checkpoint = {
                        "timestamp": datetime.now().isoformat(),
                        "stability_score": enforcement_results["stability_score"],
                        "issues_fixed": len(fix_results["fixes_applied"]),
                        "agent_id": self.agent_id,
                    }

                    await asyncio.to_thread(
                        self.redis_client.setex,
                        "env_stability_checkpoint",
                        3600,  # TTL: 1 hour
                        json.dumps(stability_checkpoint),
                    )

                    enforcement_results["actions_taken"].append("stability_checkpoint_created")

                except Exception as e:
                    logger.error("Failed to create stability checkpoint", error=str(e))

        logger.info(
            "Stability enforcement completed",
            score=enforcement_results["stability_score"],
            actions=len(enforcement_results["actions_taken"]),
        )

        return enforcement_results

    async def get_environment_status(self) -> dict[str, Any]:
        """Get comprehensive environment status"""

        base_status = self.get_status()

        env_status = {
            **base_status,
            "environment_config": self.expected_env,
            "critical_paths": self.critical_paths,
            "drift_monitoring": {
                "drift_count": self.drift_count,
                "last_check": (self.last_env_check.isoformat() if self.last_env_check else None),
                "drift_threshold": self.drift_threshold,
            },
            "current_environment": {
                var: os.getenv(var, "NOT_SET") for var in self.expected_env.keys()
            },
        }

        return env_status
