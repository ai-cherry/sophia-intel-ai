"""
Factory Bootstrap System
Comprehensive initialization scripts for the entire swarm factory ecosystem
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Supporting services
from app.core.portkey_manager import get_portkey_manager

# Core factory components
from app.factory.comprehensive_swarm_factory import get_comprehensive_factory
from app.factory.deployment_config import get_deployment_manager, start_automated_deployments
from app.factory.model_routing_config import get_routing_engine
from app.factory.slack_delivery_templates import get_template_manager
from app.memory.unified_memory_router import get_memory_router
from app.swarms.core.slack_delivery import get_delivery_engine

logger = logging.getLogger(__name__)


class FactoryBootstrapError(Exception):
    """Custom exception for bootstrap failures"""

    pass


class FactoryBootstrap:
    """
    Comprehensive bootstrap system for swarm factory
    Initializes all components, validates configurations, and performs health checks
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("app/factory/config")
        self.initialization_log: List[Dict[str, Any]] = []
        self.failed_components: List[str] = []
        self.warnings: List[str] = []

        # Component status tracking
        self.component_status = {
            "portkey_manager": False,
            "memory_router": False,
            "model_routing": False,
            "comprehensive_factory": False,
            "deployment_manager": False,
            "slack_delivery": False,
            "template_manager": False,
        }

    async def bootstrap_complete_system(
        self,
        skip_validation: bool = False,
        start_scheduler: bool = True,
        create_test_swarms: bool = False,
    ) -> Dict[str, Any]:
        """
        Bootstrap the complete swarm factory system

        Args:
            skip_validation: Skip component validation (for testing)
            start_scheduler: Start automated deployment scheduler
            create_test_swarms: Create test swarms for validation

        Returns:
            Bootstrap result summary
        """
        logger.info("🚀 Starting comprehensive swarm factory bootstrap...")
        start_time = datetime.now()

        try:
            # Phase 1: Core Infrastructure
            await self._bootstrap_core_infrastructure()

            # Phase 2: Model and Routing Systems
            await self._bootstrap_model_systems()

            # Phase 3: Factory and Swarm Systems
            await self._bootstrap_factory_systems()

            # Phase 4: Delivery and Communication
            await self._bootstrap_delivery_systems()

            # Phase 5: Deployment and Automation
            await self._bootstrap_deployment_systems(start_scheduler)

            # Phase 6: Validation and Testing
            if not skip_validation:
                await self._validate_system_health()

            # Phase 7: Optional test swarm creation
            if create_test_swarms:
                await self._create_test_swarms()

            # Final system status
            bootstrap_time = (datetime.now() - start_time).total_seconds()
            success = len(self.failed_components) == 0

            result = {
                "success": success,
                "bootstrap_time_seconds": bootstrap_time,
                "components_initialized": sum(self.component_status.values()),
                "total_components": len(self.component_status),
                "component_status": self.component_status,
                "failed_components": self.failed_components,
                "warnings": self.warnings,
                "initialization_log": self.initialization_log,
                "system_ready": success and all(self.component_status.values()),
            }

            if success:
                logger.info(f"✅ Factory bootstrap completed successfully in {bootstrap_time:.2f}s")
                self._log_success_summary(result)
            else:
                logger.error(
                    f"❌ Factory bootstrap failed with {len(self.failed_components)} component failures"
                )
                self._log_failure_summary(result)

            return result

        except Exception as e:
            logger.error(f"💥 Critical bootstrap failure: {e}")
            return {
                "success": False,
                "error": str(e),
                "component_status": self.component_status,
                "failed_components": self.failed_components,
                "warnings": self.warnings,
            }

    async def _bootstrap_core_infrastructure(self):
        """Bootstrap core infrastructure components"""
        logger.info("🔧 Phase 1: Bootstrapping core infrastructure...")

        # Initialize Portkey Manager
        try:
            portkey_manager = get_portkey_manager()

            # Validate virtual keys
            validation_results = portkey_manager.validate_virtual_keys()
            working_keys = sum(1 for result in validation_results.values() if result)

            if working_keys > 0:
                self.component_status["portkey_manager"] = True
                self._log_success(
                    "Portkey Manager",
                    f"{working_keys}/{len(validation_results)} virtual keys working",
                )
            else:
                self._log_failure("Portkey Manager", "No working virtual keys found")

        except Exception as e:
            self._log_failure("Portkey Manager", str(e))

        # Initialize Memory Router
        try:
            memory_router = get_memory_router()
            # Simple health check - this would be more comprehensive in production
            self.component_status["memory_router"] = True
            self._log_success("Memory Router", "Initialized successfully")
        except Exception as e:
            self._log_failure("Memory Router", str(e))

    async def _bootstrap_model_systems(self):
        """Bootstrap model routing and AI systems"""
        logger.info("🧠 Phase 2: Bootstrapping model systems...")

        # Initialize Model Routing Engine
        try:
            routing_engine = get_routing_engine()

            # Check routing rules
            stats = routing_engine.get_routing_statistics()
            rule_count = stats.get("total_rules", 0)

            if rule_count > 0:
                self.component_status["model_routing"] = True
                self._log_success("Model Routing Engine", f"{rule_count} routing rules loaded")
            else:
                self._log_failure("Model Routing Engine", "No routing rules found")

        except Exception as e:
            self._log_failure("Model Routing Engine", str(e))

    async def _bootstrap_factory_systems(self):
        """Bootstrap swarm factory systems"""
        logger.info("🏭 Phase 3: Bootstrapping factory systems...")

        # Initialize Comprehensive Factory
        try:
            factory = get_comprehensive_factory()

            # Check available swarms
            available_swarms = factory.get_available_swarms()
            swarm_count = len(available_swarms)

            if swarm_count > 0:
                self.component_status["comprehensive_factory"] = True
                self._log_success(
                    "Comprehensive Factory", f"{swarm_count} swarm configurations available"
                )
            else:
                self._log_failure("Comprehensive Factory", "No swarm configurations found")

        except Exception as e:
            self._log_failure("Comprehensive Factory", str(e))

    async def _bootstrap_delivery_systems(self):
        """Bootstrap delivery and communication systems"""
        logger.info("📢 Phase 4: Bootstrapping delivery systems...")

        # Initialize Slack Delivery Engine
        try:
            delivery_engine = get_delivery_engine()

            # Check delivery statistics
            stats = delivery_engine.get_delivery_statistics()

            self.component_status["slack_delivery"] = True
            self._log_success("Slack Delivery Engine", "Initialized with delivery templates")

        except Exception as e:
            self._log_failure("Slack Delivery Engine", str(e))

        # Initialize Template Manager
        try:
            template_manager = get_template_manager()

            # Check available templates
            template_count = len(template_manager.delivery_configs)

            if template_count > 0:
                self.component_status["template_manager"] = True
                self._log_success(
                    "Template Manager", f"{template_count} delivery configurations loaded"
                )
            else:
                self._log_warning("Template Manager", "No delivery configurations found")

        except Exception as e:
            self._log_failure("Template Manager", str(e))

    async def _bootstrap_deployment_systems(self, start_scheduler: bool):
        """Bootstrap deployment and automation systems"""
        logger.info("⚡ Phase 5: Bootstrapping deployment systems...")

        # Initialize Deployment Manager
        try:
            deployment_manager = get_deployment_manager()

            # Check deployment templates
            status = deployment_manager.get_deployment_status()
            template_count = status["overview"]["total_templates"]

            if template_count > 0:
                self.component_status["deployment_manager"] = True
                self._log_success(
                    "Deployment Manager", f"{template_count} deployment templates loaded"
                )

                # Start scheduler if requested
                if start_scheduler:
                    await start_automated_deployments()
                    self._log_success("Deployment Scheduler", "Automated deployments started")

            else:
                self._log_failure("Deployment Manager", "No deployment templates found")

        except Exception as e:
            self._log_failure("Deployment Manager", str(e))

    async def _validate_system_health(self):
        """Validate system health and component integration"""
        logger.info("🔍 Phase 6: Validating system health...")

        validation_results = []

        # Test 1: Model routing integration
        try:
            routing_engine = get_routing_engine()
            from app.core.portkey_manager import TaskType
            from app.factory.model_routing_config import SwarmModelProfile
            from app.swarms.core.micro_swarm_base import AgentRole

            routing_result = routing_engine.route_request(
                agent_role=AgentRole.ANALYST,
                task_type=TaskType.GENERAL,
                swarm_profile=SwarmModelProfile.HYBRID_BALANCED,
                estimated_tokens=100,
            )

            if routing_result and "primary_model" in routing_result:
                validation_results.append(
                    ("Model Routing Integration", True, "Routing test successful")
                )
            else:
                validation_results.append(
                    ("Model Routing Integration", False, "Routing test failed")
                )

        except Exception as e:
            validation_results.append(("Model Routing Integration", False, str(e)))

        # Test 2: Factory swarm creation
        try:
            factory = get_comprehensive_factory()
            available_swarms = factory.get_available_swarms()

            if available_swarms:
                # Test creating a swarm configuration (not actual swarm)
                test_config = list(factory.swarm_configs.values())[0]
                validation_results.append(
                    ("Factory Configuration", True, f"Test config '{test_config.name}' accessible")
                )
            else:
                validation_results.append(
                    ("Factory Configuration", False, "No swarm configurations available")
                )

        except Exception as e:
            validation_results.append(("Factory Configuration", False, str(e)))

        # Test 3: Delivery system integration
        try:
            template_manager = get_template_manager()
            test_config = template_manager.get_delivery_config("daily_intelligence")

            if test_config:
                validation_results.append(
                    ("Delivery Integration", True, "Template system accessible")
                )
            else:
                validation_results.append(
                    ("Delivery Integration", False, "Template system not accessible")
                )

        except Exception as e:
            validation_results.append(("Delivery Integration", False, str(e)))

        # Log validation results
        for test_name, success, message in validation_results:
            if success:
                self._log_success(f"Validation: {test_name}", message)
            else:
                self._log_failure(f"Validation: {test_name}", message)

    async def _create_test_swarms(self):
        """Create test swarms for system validation"""
        logger.info("🧪 Phase 7: Creating test swarms...")

        try:
            factory = get_comprehensive_factory()

            # Create a simple test swarm
            from app.factory.comprehensive_swarm_factory import SwarmFactoryConfig, SwarmType
            from app.swarms.core.micro_swarm_base import CoordinationPattern

            test_config = SwarmFactoryConfig(
                name="Bootstrap Test Swarm",
                swarm_type=SwarmType.MYTHOLOGY_BUSINESS,
                coordination_pattern=CoordinationPattern.SEQUENTIAL,
                max_cost_per_execution=0.5,
                auto_deliver_results=False,
                tags=["test", "bootstrap", "validation"],
            )

            swarm_id = await factory.create_swarm(test_config)
            self._log_success("Test Swarm Creation", f"Created test swarm: {swarm_id}")

            # Clean up test swarm (remove from active swarms)
            if swarm_id in factory.active_swarms:
                del factory.active_swarms[swarm_id]
                self._log_success("Test Cleanup", "Removed test swarm")

        except Exception as e:
            self._log_failure("Test Swarm Creation", str(e))

    def _log_success(self, component: str, message: str):
        """Log successful component initialization"""
        self.initialization_log.append(
            {
                "component": component,
                "status": "success",
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )
        logger.info(f"✅ {component}: {message}")

    def _log_failure(self, component: str, message: str):
        """Log component initialization failure"""
        self.failed_components.append(component)
        self.initialization_log.append(
            {
                "component": component,
                "status": "failed",
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )
        logger.error(f"❌ {component}: {message}")

    def _log_warning(self, component: str, message: str):
        """Log component initialization warning"""
        self.warnings.append(f"{component}: {message}")
        self.initialization_log.append(
            {
                "component": component,
                "status": "warning",
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )
        logger.warning(f"⚠️ {component}: {message}")

    def _log_success_summary(self, result: Dict[str, Any]):
        """Log successful bootstrap summary"""
        logger.info("=" * 60)
        logger.info("🎉 SWARM FACTORY BOOTSTRAP COMPLETE")
        logger.info("=" * 60)
        logger.info("✅ Status: SUCCESS")
        logger.info(f"⏱️  Time: {result['bootstrap_time_seconds']:.2f}s")
        logger.info(
            f"🔧 Components: {result['components_initialized']}/{result['total_components']}"
        )

        if self.warnings:
            logger.info(f"⚠️  Warnings: {len(self.warnings)}")

        logger.info("\n🏭 Factory Components Ready:")
        for component, status in self.component_status.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {component.replace('_', ' ').title()}")

        logger.info("\n🚀 System is ready for swarm operations!")
        logger.info("=" * 60)

    def _log_failure_summary(self, result: Dict[str, Any]):
        """Log failed bootstrap summary"""
        logger.error("=" * 60)
        logger.error("💥 SWARM FACTORY BOOTSTRAP FAILED")
        logger.error("=" * 60)
        logger.error("❌ Status: FAILED")
        logger.error(f"⏱️  Time: {result['bootstrap_time_seconds']:.2f}s")
        logger.error(
            f"🔧 Components: {result['components_initialized']}/{result['total_components']}"
        )
        logger.error(f"💥 Failures: {len(self.failed_components)}")

        logger.error("\n❌ Failed Components:")
        for component in self.failed_components:
            logger.error(f"   • {component}")

        if self.warnings:
            logger.error(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:  # Show first 5 warnings
                logger.error(f"   • {warning}")

        logger.error("\n🔧 Please resolve component failures before proceeding")
        logger.error("=" * 60)


# Global bootstrap instance
_bootstrap = None


def get_bootstrap() -> FactoryBootstrap:
    """Get global bootstrap instance"""
    global _bootstrap
    if _bootstrap is None:
        _bootstrap = FactoryBootstrap()
    return _bootstrap


# Convenience functions for different bootstrap scenarios
async def quick_bootstrap(start_scheduler: bool = False) -> Dict[str, Any]:
    """Quick bootstrap for development/testing"""
    bootstrap = get_bootstrap()
    return await bootstrap.bootstrap_complete_system(
        skip_validation=True, start_scheduler=start_scheduler, create_test_swarms=False
    )


async def production_bootstrap() -> Dict[str, Any]:
    """Full production bootstrap with all validations"""
    bootstrap = get_bootstrap()
    return await bootstrap.bootstrap_complete_system(
        skip_validation=False, start_scheduler=True, create_test_swarms=False
    )


async def development_bootstrap() -> Dict[str, Any]:
    """Development bootstrap with test swarms"""
    bootstrap = get_bootstrap()
    return await bootstrap.bootstrap_complete_system(
        skip_validation=False, start_scheduler=False, create_test_swarms=True
    )


async def minimal_bootstrap() -> Dict[str, Any]:
    """Minimal bootstrap - core components only"""
    bootstrap = get_bootstrap()

    # Override to only bootstrap core components
    await bootstrap._bootstrap_core_infrastructure()
    await bootstrap._bootstrap_model_systems()
    await bootstrap._bootstrap_factory_systems()

    return {
        "success": len(bootstrap.failed_components) == 0,
        "component_status": bootstrap.component_status,
        "failed_components": bootstrap.failed_components,
        "minimal_mode": True,
    }


# CLI interface for bootstrap
async def main():
    """CLI interface for factory bootstrap"""

    if len(sys.argv) < 2:
        print("Usage: python factory_bootstrap.py [quick|production|development|minimal]")
        sys.exit(1)

    mode = sys.argv[1].lower()

    bootstrap_functions = {
        "quick": quick_bootstrap,
        "production": production_bootstrap,
        "development": development_bootstrap,
        "minimal": minimal_bootstrap,
    }

    if mode not in bootstrap_functions:
        print(f"Invalid mode: {mode}")
        print("Available modes: quick, production, development, minimal")
        sys.exit(1)

    try:
        result = await bootstrap_functions[mode]()

        if result["success"]:
            print(f"\n✅ Bootstrap completed successfully in {mode} mode")
            sys.exit(0)
        else:
            print(f"\n❌ Bootstrap failed in {mode} mode")
            print(f"Failed components: {', '.join(result['failed_components'])}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Bootstrap interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Bootstrap failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
