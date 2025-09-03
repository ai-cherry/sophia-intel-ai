import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from app.core.ai_logger import logger
from app.core.circuit_breaker import CircuitBreaker
from app.observability.prometheus_metrics import (
    swarm_failure_rate,
    swarm_health_status,
    swarm_instances_total,
)
from app.swarms.communication.message_bus import MessageBus
from app.swarms.core.swarm_base import SwarmBase

logger = logging.getLogger(__name__)

@dataclass
class SwarmConfig:
    """Production swarm configuration with enhanced parameters"""
    name: str
    type: str
    agents: int
    max_concurrent_tasks: int = 10
    timeout_seconds: int = 30
    retry_attempts: int = 3
    circuit_breaker_threshold: float = 0.5
    cache_ttl_seconds: int = 300
    enabled_patterns: list[str] = None
    memory_enabled: bool = True

class EnhancedSwarmManager:
    """Production-grade swarm lifecycle management with HA and observability"""

    def __init__(self, message_bus: MessageBus = None):
        self.message_bus = message_bus
        self.swarms: dict[str, SwarmBase] = {}
        self.health_status: dict[str, bool] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.version = "1.0.0"
        self._initialized = False

        # Identify environment for cloud-specific behavior
        self.environment = self._detect_environment()

    def _detect_environment(self) -> str:
        """Detect deployment environment for cloud-specific configuration"""
        if 'AWS_REGION' in os.environ:
            return "aws"
        elif 'GCP_PROJECT' in os.environ:
            return "gcp"
        elif 'KUBERNETES_SERVICE_HOST' in os.environ:
            return "kubernetes"
        elif os.path.exists('/.dockerenv'):
            return "docker"
        return "local"

    async def initialize_swarm_constellation(self, configs: list[SwarmConfig]):
        """Initialize all swarms with production configuration"""
        for config in configs:
            try:
                # Create swarm instance
                swarm = await self._create_swarm(config)
                self.swarms[config.name] = swarm

                # Initialize circuit breakers
                self.circuit_breakers[config.name] = CircuitBreaker(
                    failure_threshold=config.circuit_breaker_threshold,
                    recovery_timeout=60,
                    name=f"swarm_{config.name}"
                )

                # Register with message bus for health monitoring
                if self.message_bus:
                    await self.message_bus.subscribe(
                        f"swarm_{config.name}",
                        [MessageType.EVENT]
                    )

                logger.info(f"✅ Swarm '{config.name}' initialized successfully in {self.environment} environment")

                # Track metrics
                swarm_instances_total.inc()
                self.health_status[config.name] = True

            except Exception as e:
                logger.error(f"Error initializing swarm {config.name}: {str(e)}")
                self.health_status[config.name] = False
                raise

    async def _create_swarm(self, config: SwarmConfig) -> SwarmBase:
        """Create a new swarm instance with configuration"""
        # In a real implementation, this would use SwarmFactory
        # For now, we'll use swarm_base directly
        return SwarmBase(
            config=SwarmConfig.from_dict({
                **config.__dict__,
                'enabled_patterns': config.enabled_patterns or ["quality_gates", "consensus"]
            }),
            agents=[f"agent-{i}" for i in range(config.agents)]
        )

    async def execute_with_failover(self, task: dict, primary_swarm: str, thrust_threshold: float = 0.3):
        """Execute task with automatic failover to backup swarms"""
        # Check primary swarm health
        if self.health_status.get(primary_swarm, False):
            try:
                # Execute with primary
                result = await self._execute_task_with_swarm(task, primary_swarm)
                return result
            except Exception as e:
                # Mark as failed for CB
                if primary_swarm in self.circuit_breakers:
                    self.circuit_breakers[primary_swarm].fail()
                logger.warning(f"Failed execution with primary swarm '{primary_swarm}': {str(e)}")

        # Failure threshold check for primary
        if primary_swarm in self.circuit_breakers:
            failure_rate = self.circuit_breakers[primary_swarm].failure_rate
            if failure_rate >= thrust_threshold:
                logger.warning(f"Swarm '{primary_swarm}' failure rate ({failure_rate:.2%}) exceeds threshold {thrust_threshold:.0%}")
                # Find replacement swarm
                backup_swarm = self._find_available_swarm(primary_swarm)
                if backup_swarm:
                    logger.info(f"Switching to backup swarm: {backup_swarm}")
                    return await self._execute_task_with_swarm(task, backup_swarm)

        # Fallback to a default swarm
        default_swarm = next(iter(self.swarms.keys()), None)
        if default_swarm:
            logger.warning(f"Using default swarm '{default_swarm}' as fallback")
            return await self._execute_task_with_swarm(task, default_swarm)

        raise RuntimeError("No available swarms for task execution")

    async def _execute_task_with_swarm(self, task: dict, swarm_name: str) -> Any:
        """Execute task with a specific swarm, including retries and CB"""
        if swarm_name not in self.swarms:
            raise ValueError(f"Swarm {swarm_name} not found")

        # Get swarm instance
        swarm = self.swarms[swarm_name]

        # Wrap in circuit breaker
        result = await self.circuit_breakers[swarm_name].wrap(
            swarm.solve_problem,
            task
        )

        # Track success metrics
        if result and isinstance(result, dict) and result.get('success', False):
            swarm_failure_rate.labels(swarm_name).set(0.0)
        else:
            swarm_failure_rate.labels(swarm_name).set(
                self.circuit_breakers[swarm_name].failure_rate
            )

        return result

    def _find_available_swarm(self, excluded_swarm: str) -> str | None:
        """Find a swarm that's healthy and not the excluded one"""
        for name, health in self.health_status.items():
            if health and name != excluded_swarm:
                return name
        return None

    async def get_swarm_metrics(self, swarm_name: str | None = None) -> dict[str, Any]:
        """Collect comprehensive swarm metrics for monitoring"""
        results = {}

        if swarm_name:
            if swarm_name not in self.swarms:
                logger.error(f"Swarm {swarm_name} not found")
                return {}
            swarm = self.swarms[swarm_name]
            results[swarm_name] = self._collect_swarm_metrics(swarm)
        else:
            for name, swarm in self.swarms.items():
                results[name] = self._collect_swarm_metrics(swarm)

        # Update health status metrics
        for name, status in results.items():
            swarm_health_status.labels(name).set(1 if status.get('is_healthy', False) else 0)

        return results

    def _collect_swarm_metrics(self, swarm: SwarmBase) -> dict[str, Any]:
        """Collect metrics for a specific swarm"""
        status = swarm.get_swarm_status()

        # Determine health based on status
        is_healthy = (
            status.get('is_initialized', False) and
            status.get('metrics', {}).get('performance_score', 0) > 50
        )

        return {
            "name": status.get('swarm_id'),
            "type": status.get('swarm_type'),
            "agents": status.get('agent_count'),
            "is_healthy": is_healthy,
            "performance_score": status.get('metrics', {}).get('performance_score', 0),
            "active_tasks": len(swarm.get_active_tasks()),
            "circuit_breaker": {
                "state": self.circuit_breakers.get(swarm.config.swarm_id, {}).state,
                "failure_rate": self.circuit_breakers.get(swarm.config.swarm_id, {}).failure_rate
            }
        }

    def announce_swarm_health(self, swarm_id: str):
        """Announce swarm health state via message bus"""
        if self.message_bus:
            try:
                message = SwarmMessage(
                    sender_agent_id="swarm_manager",
                    message_type=MessageType.EVENT,
                    content={
                        "event_type": "swarm_health",
                        "swarm_id": swarm_id,
                        "status": "healthy" if self.health_status.get(swarm_id, False) else "unhealthy",
                        "timestamp": datetime.now().isoformat()
                    },
                    thread_id=f"health:{swarm_id}"
                )
                asyncio.create_task(self.message_bus.publish(message))
            except Exception as e:
                logger.error(f"Failed to publish swarm health: {str(e)}")

    async def register_swarm_with_mcp(self, swarm_id: str):
        """Register swarm with MCP server for discovery and coordination"""
        # In a real implementation, this would call MCP registration service
        logger.info(f"Registering swarm {swarm_id} with MCP for coordination")
        return True

    async def run_health_check_cycle(self):
        """Periodically check swarm health for automatic recovery"""
        while True:
            for name, swarm in self.swarms.items():
                try:
                    # Check swarm health through proxy
                    # This would typically use a sentinel endpoint
                    if not self.health_status[name]:
                        swarm_status = await self._fetch_swarm_health(swarm)
                        self.health_status[name] = swarm_status
                except Exception as e:
                    logger.error(f"Health check failed for {name}: {str(e)}")
                    self.health_status[name] = False
                finally:
                    # Announce health
                    self.announce_swarm_health(name)

            # 30 second interval
            await asyncio.sleep(30)

    async def _fetch_swarm_health(self, swarm: SwarmBase) -> bool:
        """Fetch swarm health from internal endpoints (simulated)"""
        # In real implementation, this would call endpoint like /health
        return True if swarm.get_swarm_status().get('is_initialized', False) else False

# Example usage
if __name__ == "__main__":
    async def demo():
        # Initialize message bus
        bus = MessageBus()
        await bus.initialize()

        # Create swarm manager
        manager = EnhancedSwarmManager(message_bus=bus)

        # Configure and initialize swarms
        configs = [
            SwarmConfig(
                name="coding_swarm",
                type="coding",
                agents=5,
                enabled_patterns=["quality_gates", "code_review"]
            ),
            SwarmConfig(
                name="research_swarm",
                type="research",
                agents=3
            )
        ]

        await manager.initialize_swarm_constellation(configs)

        # Simulate execution
        task = {"question": "How to build a REST API in Python?"}
        result = await manager.execute_with_failover(
            task,
            primary_swarm="coding_swarm"
        )

        logger.info(f"Execution result: {result}")

        # Run health checks in background
        asyncio.create_task(manager.run_health_check_cycle())

        # Keep running for 60 seconds to test
        await asyncio.sleep(60)

        # Cleanup
        await bus.close()

    asyncio.run(demo())
