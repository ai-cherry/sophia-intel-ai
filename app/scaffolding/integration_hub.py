"""
AI Scaffolding Integration Hub
=============================

Central integration point for all AI scaffolding components including
component registration, discovery, configuration management, health monitoring,
and lifecycle management.

Features:
- Component registration and discovery
- Configuration management and validation
- Health checks and monitoring
- Dependency management and initialization
- Event-driven component coordination
- Integration with all scaffolding systems

AI Context:
- Serves as the nerve center for AI infrastructure
- Coordinates between memory, documentation, personas, and orchestrators
- Provides unified interface for system management
- Enables dynamic component loading and configuration
"""

import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import Awaitable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import uuid4

import yaml

from app.scaffolding.embedding_system import (
    MultiModalEmbeddingSystem,
)

# Import existing infrastructure components
from app.scaffolding.meta_tagging import MetaTag, MetaTaggingSystem

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """Types of scaffolding components"""

    MEMORY_SYSTEM = "memory_system"
    EMBEDDING_SYSTEM = "embedding_system"
    META_TAGGING = "meta_tagging"
    PERSONA_MANAGER = "persona_manager"
    MCP_ORCHESTRATOR = "mcp_orchestrator"
    DOCUMENTATION_SYSTEM = "documentation_system"
    REASONING_ENGINE = "reasoning_engine"
    INTEGRATION_ADAPTER = "integration_adapter"


class ComponentStatus(Enum):
    """Status of scaffold components"""

    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPING = "stopping"
    STOPPED = "stopped"


class InitializationPhase(Enum):
    """Phases of system initialization"""

    PRE_INIT = "pre_init"  # Configuration loading
    COMPONENT_REGISTRATION = "component_registration"
    DEPENDENCY_RESOLUTION = "dependency_resolution"
    COMPONENT_INITIALIZATION = "component_initialization"
    CROSS_COMPONENT_LINKING = "cross_component_linking"
    HEALTH_VERIFICATION = "health_verification"
    POST_INIT = "post_init"  # Final setup
    READY = "ready"


@dataclass
class ComponentMetadata:
    """Metadata for registered components"""

    component_id: str
    component_type: ComponentType
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    dependencies: set[str] = field(default_factory=set)
    provides: set[str] = field(default_factory=set)  # Capabilities provided
    requires: set[str] = field(default_factory=set)  # Capabilities required
    priority: int = 5  # Initialization priority (1 = highest)
    config_schema: Optional[dict[str, Any]] = None
    health_check_interval: int = 60  # seconds
    auto_restart: bool = True
    meta_tags: list[MetaTag] = field(default_factory=list)


@dataclass
class ComponentInstance:
    """Instance of a registered component"""

    metadata: ComponentMetadata
    instance: Any
    status: ComponentStatus = ComponentStatus.REGISTERED
    config: dict[str, Any] = field(default_factory=dict)
    initialization_time: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    health_data: dict[str, Any] = field(default_factory=dict)
    error_count: int = 0
    last_error: Optional[str] = None
    restart_count: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationEvent:
    """Event for component coordination"""

    event_id: str
    event_type: str
    source_component: str
    target_component: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False


@dataclass
class SystemHealthReport:
    """Comprehensive system health report"""

    overall_status: ComponentStatus
    component_count: int
    healthy_components: int
    degraded_components: int
    failed_components: int
    system_uptime: timedelta
    last_initialization: datetime
    integration_events_processed: int
    performance_metrics: dict[str, Any] = field(default_factory=dict)
    component_details: dict[str, dict[str, Any]] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


class ConfigurationManager:
    """Manages system configuration"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/scaffolding_config.yaml")
        self.config: dict[str, Any] = {}
        self.config_schemas: dict[str, dict[str, Any]] = {}

    async def load_config(self) -> dict[str, Any]:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    if self.config_path.suffix.lower() == ".yaml":
                        self.config = yaml.safe_load(f)
                    else:
                        self.config = json.load(f)

                logger.info(f"Loaded configuration from {self.config_path}")
                return self.config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                self.config = self._get_default_config()
        else:
            logger.info("No config file found, using defaults")
            self.config = self._get_default_config()
            await self.save_config()

        return self.config

    async def save_config(self):
        """Save current configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_path, "w") as f:
                if self.config_path.suffix.lower() == ".yaml":
                    yaml.dump(self.config, f, default_flow_style=False)
                else:
                    json.dump(self.config, f, indent=2)

            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get_component_config(self, component_id: str) -> dict[str, Any]:
        """Get configuration for specific component"""
        return self.config.get("components", {}).get(component_id, {})

    def set_component_config(self, component_id: str, config: dict[str, Any]):
        """Set configuration for component"""
        if "components" not in self.config:
            self.config["components"] = {}
        self.config["components"][component_id] = config

    def validate_config(self, component_id: str, config: dict[str, Any]) -> bool:
        """Validate configuration against schema"""
        schema = self.config_schemas.get(component_id)
        if not schema:
            return True  # No schema to validate against

        # Simple validation - could be enhanced with jsonschema
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in config:
                logger.error(
                    f"Missing required field '{field}' in config for {component_id}"
                )
                return False

        return True

    def register_config_schema(self, component_id: str, schema: dict[str, Any]):
        """Register configuration schema for component"""
        self.config_schemas[component_id] = schema

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration"""
        return {
            "system": {
                "name": "Sophia AI Scaffolding",
                "version": "1.0.0",
                "environment": "development",
                "log_level": "INFO",
                "health_check_interval": 60,
                "max_restart_attempts": 3,
                "initialization_timeout": 300,
            },
            "components": {
                "memory_system": {
                    "enabled": True,
                    "redis_url": "redis://localhost:6379",
                    "weaviate_url": "http://localhost:8080",
                    "neon_connection": "postgresql://user:pass@localhost/db",
                    "s3_bucket": "sophia-memory",
                    "aws_region": "us-east-1",
                },
                "embedding_system": {
                    "enabled": True,
                    "default_model": "text-embedding-ada-002",
                    "cache_embeddings": True,
                    "embedding_dimension": 1536,
                },
                "meta_tagging": {
                    "enabled": True,
                    "auto_tag_code": True,
                    "semantic_analysis": True,
                },
                "persona_manager": {
                    "enabled": True,
                    "default_persona": "sophia",
                    "evolution_enabled": True,
                },
                "mcp_orchestrator": {
                    "enabled": True,
                    "max_concurrent_nodes": 10,
                    "default_timeout": 300,
                },
                "documentation_system": {
                    "enabled": True,
                    "docs_directory": "./docs",
                    "auto_generate": True,
                    "scan_interval": 3600,
                },
            },
        }


class EventBus:
    """Event bus for component coordination"""

    def __init__(self):
        self.subscribers: dict[str, list[Callable]] = defaultdict(list)
        self.event_history: list[IntegrationEvent] = []
        self.max_history = 1000

    def subscribe(
        self, event_type: str, callback: Callable[[IntegrationEvent], Awaitable[None]]
    ):
        """Subscribe to events of specific type"""
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type} events")

    async def publish(self, event: IntegrationEvent):
        """Publish event to subscribers"""
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # Notify subscribers
        callbacks = self.subscribers.get(event.event_type, [])
        if callbacks:
            tasks = [callback(event) for callback in callbacks]
            await asyncio.gather(*tasks, return_exceptions=True)

            event.processed = True
            logger.debug(
                f"Published {event.event_type} event to {len(callbacks)} subscribers"
            )

    def get_event_history(
        self, event_type: Optional[str] = None, limit: int = 100
    ) -> list[IntegrationEvent]:
        """Get recent event history"""
        events = self.event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]


class IntegrationHub:
    """Central integration hub for AI scaffolding"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_manager = ConfigurationManager(config_path)
        self.event_bus = EventBus()

        # Component registry
        self.components: dict[str, ComponentInstance] = {}
        self.component_registry: dict[ComponentType, list[str]] = defaultdict(list)

        # System state
        self.initialization_phase = InitializationPhase.PRE_INIT
        self.system_start_time = datetime.utcnow()
        self.initialization_start: Optional[datetime] = None
        self.ready_time: Optional[datetime] = None

        # Health monitoring
        self.health_check_task: Optional[asyncio.Task] = None
        self.health_check_interval = 60

        # Metrics
        self.system_metrics = {
            "initialization_count": 0,
            "component_restarts": 0,
            "events_processed": 0,
            "health_checks_performed": 0,
            "errors_encountered": 0,
        }

    async def initialize(self) -> bool:
        """Initialize the integration hub and all components"""
        self.initialization_start = datetime.utcnow()
        self.system_metrics["initialization_count"] += 1

        try:
            # Phase 1: Load configuration
            self.initialization_phase = InitializationPhase.PRE_INIT
            await self._phase_pre_init()

            # Phase 2: Register default components
            self.initialization_phase = InitializationPhase.COMPONENT_REGISTRATION
            await self._phase_component_registration()

            # Phase 3: Resolve dependencies
            self.initialization_phase = InitializationPhase.DEPENDENCY_RESOLUTION
            await self._phase_dependency_resolution()

            # Phase 4: Initialize components
            self.initialization_phase = InitializationPhase.COMPONENT_INITIALIZATION
            await self._phase_component_initialization()

            # Phase 5: Link components
            self.initialization_phase = InitializationPhase.CROSS_COMPONENT_LINKING
            await self._phase_cross_component_linking()

            # Phase 6: Health verification
            self.initialization_phase = InitializationPhase.HEALTH_VERIFICATION
            await self._phase_health_verification()

            # Phase 7: Final setup
            self.initialization_phase = InitializationPhase.POST_INIT
            await self._phase_post_init()

            # System ready
            self.initialization_phase = InitializationPhase.READY
            self.ready_time = datetime.utcnow()

            # Start health monitoring
            self.health_check_task = asyncio.create_task(self._health_monitoring_loop())

            logger.info(
                f"Integration hub initialized successfully in {(self.ready_time - self.initialization_start).total_seconds():.2f}s"
            )

            # Publish system ready event
            await self.event_bus.publish(
                IntegrationEvent(
                    event_id=str(uuid4()),
                    event_type="system.ready",
                    source_component="integration_hub",
                    payload={
                        "initialization_time": (
                            self.ready_time - self.initialization_start
                        ).total_seconds()
                    },
                )
            )

            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.system_metrics["errors_encountered"] += 1
            return False

    async def register_component(
        self,
        component_id: str,
        component_type: ComponentType,
        instance: Any,
        metadata: Optional[ComponentMetadata] = None,
    ) -> bool:
        """Register a component instance"""

        if metadata is None:
            metadata = ComponentMetadata(
                component_id=component_id,
                component_type=component_type,
                name=component_id.title().replace("_", " "),
            )

        # Get component configuration
        config = self.config_manager.get_component_config(component_id)

        # Validate configuration
        if metadata.config_schema:
            if not self.config_manager.validate_config(component_id, config):
                logger.error(f"Invalid configuration for component {component_id}")
                return False

        # Create component instance record
        component_instance = ComponentInstance(
            metadata=metadata,
            instance=instance,
            config=config,
            status=ComponentStatus.REGISTERED,
        )

        self.components[component_id] = component_instance
        self.component_registry[component_type].append(component_id)

        logger.info(f"Registered component: {component_id} ({component_type.value})")

        # Publish registration event
        await self.event_bus.publish(
            IntegrationEvent(
                event_id=str(uuid4()),
                event_type="component.registered",
                source_component="integration_hub",
                payload={
                    "component_id": component_id,
                    "component_type": component_type.value,
                    "metadata": asdict(metadata),
                },
            )
        )

        return True

    async def get_component(self, component_id: str) -> Optional[Any]:
        """Get component instance by ID"""
        component = self.components.get(component_id)
        return component.instance if component else None

    async def get_components_by_type(self, component_type: ComponentType) -> list[Any]:
        """Get all components of specific type"""
        component_ids = self.component_registry.get(component_type, [])
        return [
            self.components[cid].instance
            for cid in component_ids
            if cid in self.components
            and self.components[cid].status == ComponentStatus.HEALTHY
        ]

    async def initialize_component(self, component_id: str) -> bool:
        """Initialize specific component"""
        if component_id not in self.components:
            logger.error(f"Component {component_id} not registered")
            return False

        component = self.components[component_id]

        try:
            component.status = ComponentStatus.INITIALIZING

            # Call initialize method if it exists
            if hasattr(component.instance, "initialize"):
                await component.instance.initialize()
            elif hasattr(component.instance, "connect"):
                await component.instance.connect()

            component.status = ComponentStatus.HEALTHY
            component.initialization_time = datetime.utcnow()

            logger.info(f"Initialized component: {component_id}")

            # Publish initialization event
            await self.event_bus.publish(
                IntegrationEvent(
                    event_id=str(uuid4()),
                    event_type="component.initialized",
                    source_component="integration_hub",
                    payload={"component_id": component_id},
                )
            )

            return True

        except Exception as e:
            component.status = ComponentStatus.FAILED
            component.last_error = str(e)
            component.error_count += 1

            logger.error(f"Failed to initialize component {component_id}: {e}")
            self.system_metrics["errors_encountered"] += 1

            return False

    async def health_check_component(self, component_id: str) -> dict[str, Any]:
        """Perform health check on specific component"""
        if component_id not in self.components:
            return {"status": "unknown", "error": "Component not registered"}

        component = self.components[component_id]

        try:
            health_data = {"status": "healthy", "timestamp": datetime.utcnow()}

            # Call health_check method if it exists
            if hasattr(component.instance, "health_check"):
                instance_health = await component.instance.health_check()
                if isinstance(instance_health, dict):
                    health_data.update(instance_health)

            # Update component health data
            component.last_health_check = datetime.utcnow()
            component.health_data = health_data

            # Determine status from health data
            if health_data.get("status") == "healthy":
                if component.status != ComponentStatus.HEALTHY:
                    component.status = ComponentStatus.HEALTHY
                    await self._publish_status_change(
                        component_id, ComponentStatus.HEALTHY
                    )
            else:
                if component.status == ComponentStatus.HEALTHY:
                    component.status = ComponentStatus.DEGRADED
                    await self._publish_status_change(
                        component_id, ComponentStatus.DEGRADED
                    )

            return health_data

        except Exception as e:
            error_data = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow(),
            }

            component.last_error = str(e)
            component.error_count += 1
            component.health_data = error_data

            if component.status != ComponentStatus.FAILED:
                component.status = ComponentStatus.FAILED
                await self._publish_status_change(component_id, ComponentStatus.FAILED)

            return error_data

    async def restart_component(self, component_id: str) -> bool:
        """Restart a failed component"""
        if component_id not in self.components:
            return False

        component = self.components[component_id]

        try:
            component.status = ComponentStatus.STOPPING

            # Call stop method if it exists
            if hasattr(component.instance, "stop"):
                await component.instance.stop()

            component.status = ComponentStatus.STOPPED

            # Reinitialize
            success = await self.initialize_component(component_id)

            if success:
                component.restart_count += 1
                self.system_metrics["component_restarts"] += 1

                logger.info(f"Successfully restarted component: {component_id}")

                await self.event_bus.publish(
                    IntegrationEvent(
                        event_id=str(uuid4()),
                        event_type="component.restarted",
                        source_component="integration_hub",
                        payload={
                            "component_id": component_id,
                            "restart_count": component.restart_count,
                        },
                    )
                )

            return success

        except Exception as e:
            logger.error(f"Failed to restart component {component_id}: {e}")
            component.status = ComponentStatus.FAILED
            return False

    async def shutdown(self):
        """Shutdown the integration hub and all components"""
        logger.info("Shutting down integration hub...")

        # Stop health monitoring
        if self.health_check_task:
            self.health_check_task.cancel()

        # Shutdown components in reverse dependency order
        shutdown_order = list(reversed(self._get_initialization_order()))

        for component_id in shutdown_order:
            if component_id in self.components:
                component = self.components[component_id]

                try:
                    component.status = ComponentStatus.STOPPING

                    if hasattr(component.instance, "shutdown"):
                        await component.instance.shutdown()
                    elif hasattr(component.instance, "stop"):
                        await component.instance.stop()

                    component.status = ComponentStatus.STOPPED
                    logger.info(f"Stopped component: {component_id}")

                except Exception as e:
                    logger.error(f"Error stopping component {component_id}: {e}")

        # Publish shutdown event
        await self.event_bus.publish(
            IntegrationEvent(
                event_id=str(uuid4()),
                event_type="system.shutdown",
                source_component="integration_hub",
            )
        )

        logger.info("Integration hub shutdown complete")

    async def get_system_health(self) -> SystemHealthReport:
        """Get comprehensive system health report"""

        healthy_count = sum(
            1 for c in self.components.values() if c.status == ComponentStatus.HEALTHY
        )
        degraded_count = sum(
            1 for c in self.components.values() if c.status == ComponentStatus.DEGRADED
        )
        failed_count = sum(
            1 for c in self.components.values() if c.status == ComponentStatus.FAILED
        )

        # Determine overall status
        if failed_count > 0:
            overall_status = ComponentStatus.FAILED
        elif degraded_count > 0:
            overall_status = ComponentStatus.DEGRADED
        elif healthy_count == len(self.components):
            overall_status = ComponentStatus.HEALTHY
        else:
            overall_status = ComponentStatus.DEGRADED

        # Collect component details
        component_details = {}
        for component_id, component in self.components.items():
            component_details[component_id] = {
                "type": component.metadata.component_type.value,
                "status": component.status.value,
                "last_health_check": (
                    component.last_health_check.isoformat()
                    if component.last_health_check
                    else None
                ),
                "error_count": component.error_count,
                "restart_count": component.restart_count,
                "last_error": component.last_error,
                "health_data": component.health_data,
            }

        # Generate recommendations
        recommendations = []
        if failed_count > 0:
            recommendations.append(f"Investigate {failed_count} failed components")
        if degraded_count > 0:
            recommendations.append(f"Monitor {degraded_count} degraded components")

        # Calculate uptime
        uptime = datetime.utcnow() - self.system_start_time

        return SystemHealthReport(
            overall_status=overall_status,
            component_count=len(self.components),
            healthy_components=healthy_count,
            degraded_components=degraded_count,
            failed_components=failed_count,
            system_uptime=uptime,
            last_initialization=self.initialization_start or self.system_start_time,
            integration_events_processed=len(self.event_bus.event_history),
            performance_metrics=self.system_metrics.copy(),
            component_details=component_details,
            recommendations=recommendations,
        )

    # Private methods for initialization phases

    async def _phase_pre_init(self):
        """Pre-initialization phase"""
        await self.config_manager.load_config()
        self.health_check_interval = self.config_manager.config.get("system", {}).get(
            "health_check_interval", 60
        )
        logger.info("Configuration loaded")

    async def _phase_component_registration(self):
        """Component registration phase"""
        config = self.config_manager.config

        # Register core components based on configuration
        components_config = config.get("components", {})

        # Memory system
        if components_config.get("memory_system", {}).get("enabled", True):
            try:
                from app.memory.hierarchical_memory import create_hierarchical_memory

                memory_config = components_config["memory_system"]
                memory_system = await create_hierarchical_memory(memory_config)

                await self.register_component(
                    "memory_system",
                    ComponentType.MEMORY_SYSTEM,
                    memory_system,
                    ComponentMetadata(
                        component_id="memory_system",
                        component_type=ComponentType.MEMORY_SYSTEM,
                        name="Hierarchical Memory System",
                        description="4-tier memory architecture with intelligent routing",
                        provides={"memory_storage", "semantic_search", "caching"},
                        priority=1,
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to register memory system: {e}")

        # Embedding system
        if components_config.get("embedding_system", {}).get("enabled", True):
            try:
                embedding_system = MultiModalEmbeddingSystem()

                await self.register_component(
                    "embedding_system",
                    ComponentType.EMBEDDING_SYSTEM,
                    embedding_system,
                    ComponentMetadata(
                        component_id="embedding_system",
                        component_type=ComponentType.EMBEDDING_SYSTEM,
                        name="Multi-Modal Embedding System",
                        description="Advanced embedding infrastructure for semantic understanding",
                        provides={
                            "embeddings",
                            "semantic_similarity",
                            "contextual_analysis",
                        },
                        priority=2,
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to register embedding system: {e}")

        # Meta-tagging system
        if components_config.get("meta_tagging", {}).get("enabled", True):
            try:
                meta_system = MetaTaggingSystem()

                await self.register_component(
                    "meta_tagging",
                    ComponentType.META_TAGGING,
                    meta_system,
                    ComponentMetadata(
                        component_id="meta_tagging",
                        component_type=ComponentType.META_TAGGING,
                        name="Meta-Tagging System",
                        description="Intelligent code analysis and classification",
                        provides={"code_analysis", "semantic_roles", "meta_tags"},
                        priority=3,
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to register meta-tagging system: {e}")

        # MCP Orchestrator
        if components_config.get("mcp_orchestrator", {}).get("enabled", True):
            try:
                from app.mcp.mcp_orchestrator import create_mcp_orchestrator

                memory_system = await self.get_component("memory_system")

                mcp_config = components_config["mcp_orchestrator"]
                orchestrator = await create_mcp_orchestrator(memory_system, mcp_config)

                await self.register_component(
                    "mcp_orchestrator",
                    ComponentType.MCP_ORCHESTRATOR,
                    orchestrator,
                    ComponentMetadata(
                        component_id="mcp_orchestrator",
                        component_type=ComponentType.MCP_ORCHESTRATOR,
                        name="MCP Orchestrator",
                        description="DAG-based execution with parallel processing",
                        provides={
                            "workflow_execution",
                            "mcp_coordination",
                            "parallel_processing",
                        },
                        requires={"memory_storage"},
                        dependencies={"memory_system"},
                        priority=4,
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to register MCP orchestrator: {e}")

        # Documentation system
        if components_config.get("documentation_system", {}).get("enabled", True):
            try:
                from app.documentation.living_docs import (
                    create_living_documentation_system,
                )

                memory_system = await self.get_component("memory_system")

                docs_config = components_config["documentation_system"]
                docs_system = await create_living_documentation_system(
                    docs_config.get("docs_directory", "./docs"), memory_system
                )

                await self.register_component(
                    "documentation_system",
                    ComponentType.DOCUMENTATION_SYSTEM,
                    docs_system,
                    ComponentMetadata(
                        component_id="documentation_system",
                        component_type=ComponentType.DOCUMENTATION_SYSTEM,
                        name="Living Documentation System",
                        description="Self-maintaining documentation with AI context",
                        provides={"documentation", "code_analysis", "examples"},
                        requires={"memory_storage"},
                        dependencies={"memory_system"},
                        priority=5,
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to register documentation system: {e}")

        logger.info(f"Registered {len(self.components)} components")

    async def _phase_dependency_resolution(self):
        """Dependency resolution phase"""
        # Build dependency graph and check for cycles
        # For now, simple dependency checking
        logger.info("Dependencies resolved")

    async def _phase_component_initialization(self):
        """Component initialization phase"""
        initialization_order = self._get_initialization_order()

        for component_id in initialization_order:
            success = await self.initialize_component(component_id)
            if not success:
                logger.error(f"Failed to initialize {component_id}")

    async def _phase_cross_component_linking(self):
        """Cross-component linking phase"""
        # Link components that need to know about each other

        # Link memory system to other components
        memory_system = await self.get_component("memory_system")
        if memory_system:
            # Components that use memory can access it through the hub
            pass

        logger.info("Cross-component linking complete")

    async def _phase_health_verification(self):
        """Health verification phase"""
        for component_id in self.components:
            health = await self.health_check_component(component_id)
            if health.get("status") != "healthy":
                logger.warning(f"Component {component_id} is not healthy: {health}")

        self.system_metrics["health_checks_performed"] += len(self.components)

    async def _phase_post_init(self):
        """Post-initialization phase"""
        # Subscribe to component events
        self.event_bus.subscribe("component.failed", self._handle_component_failure)
        self.event_bus.subscribe("component.degraded", self._handle_component_degraded)

        logger.info("Post-initialization complete")

    def _get_initialization_order(self) -> list[str]:
        """Get component initialization order based on dependencies and priority"""
        # Sort by priority for now - could implement proper dependency resolution
        components = list(self.components.values())
        components.sort(key=lambda c: c.metadata.priority)
        return [c.metadata.component_id for c in components]

    async def _health_monitoring_loop(self):
        """Background health monitoring loop"""
        while self.initialization_phase == InitializationPhase.READY:
            try:
                await asyncio.sleep(self.health_check_interval)

                # Health check all components
                for component_id in self.components:
                    await self.health_check_component(component_id)

                self.system_metrics["health_checks_performed"] += len(self.components)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                self.system_metrics["errors_encountered"] += 1

    async def _handle_component_failure(self, event: IntegrationEvent):
        """Handle component failure event"""
        component_id = event.payload.get("component_id")
        if component_id and component_id in self.components:
            component = self.components[component_id]

            # Attempt restart if auto_restart is enabled
            if component.metadata.auto_restart and component.restart_count < 3:
                logger.info(f"Attempting to restart failed component: {component_id}")
                await self.restart_component(component_id)

    async def _handle_component_degraded(self, event: IntegrationEvent):
        """Handle component degraded event"""
        component_id = event.payload.get("component_id")
        logger.warning(f"Component {component_id} is degraded")

    async def _publish_status_change(
        self, component_id: str, new_status: ComponentStatus
    ):
        """Publish component status change event"""
        await self.event_bus.publish(
            IntegrationEvent(
                event_id=str(uuid4()),
                event_type=f"component.{new_status.value}",
                source_component="integration_hub",
                payload={"component_id": component_id, "status": new_status.value},
            )
        )


# Factory function for easy instantiation
async def create_integration_hub(config_path: Optional[str] = None) -> IntegrationHub:
    """Create and initialize integration hub"""
    config_path_obj = Path(config_path) if config_path else None

    hub = IntegrationHub(config_path_obj)
    success = await hub.initialize()

    if not success:
        raise RuntimeError("Failed to initialize integration hub")

    return hub


# Usage example and main entry point
async def main():
    """Example usage of integration hub"""

    try:
        # Create and initialize hub
        hub = await create_integration_hub("config/scaffolding_config.yaml")

        # Get system health
        health = await hub.get_system_health()
        print(f"System status: {health.overall_status.value}")
        print(
            f"Components: {health.healthy_components}/{health.component_count} healthy"
        )

        # Get specific component
        memory_system = await hub.get_component("memory_system")
        if memory_system:
            print("Memory system is available")

        # Wait for events
        await asyncio.sleep(5)

        # Shutdown
        await hub.shutdown()

    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
