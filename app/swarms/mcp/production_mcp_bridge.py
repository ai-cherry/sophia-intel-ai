import asyncio
import logging
import os
import threading
import time
from datetime import datetime
from typing import Any

import aioredis

from app.core.circuit_breaker import with_circuit_breaker
from app.core.retry import exponential, retry
from app.observability.prometheus_metrics import (
    mcp_bridge_call_duration_seconds,
    mcp_bridge_errors_total,
    mcp_bridge_message_translations_total,
    mcp_bridge_participants_total,
)
from app.swarms.communication.message_bus import MessageType, SwarmMessage
from app.swarms.core.enhanced_swarm_manager import EnhancedSwarmManager
from app.swarms.mcp.swarm_mcp_bridge import SwarmMCPBridge

logger = logging.getLogger(__name__)

class ProductionMCPBridge(SwarmMCPBridge):
    """Production-ready MCP bridge with high availability features"""

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        self.redis_client = None
        self.service_discovery = ServiceDiscovery()
        self.load_balancer = LoadBalancer()
        self.message_queue = MessageQueue()
        self.mcp_participants = {}
        self.participant_lock = threading.Lock()
        self.start_time = datetime.now()

    async def initialize_with_ha(self):
        """Initialize with high availability features including Redis coordination"""
        try:
            # Initialize Redis connection
            self.redis_client = await aioredis.create_redis_pool(
                self.config.get('REDIS_URL', 'redis://localhost:6379'),
                minsize=5,
                maxsize=10
            )

            # Register with service discovery
            await self.service_discovery.register(
                service_name="swarm_mcp_bridge",
                host=self.get_host(),
                port=self.get_port(),
                health_check_url="/mcp/health"
            )

            # Initialize message queue for reliability
            await self.message_queue.connect()

            # Start background processes
            asyncio.create_task(self.periodic_health_check())
            asyncio.create_task(self.periodic_participant_sync())

            logger.info(f"✅ MCP bridge initialized with HA: {self.config.get('ENV', 'local')}")
            return True

        except Exception as e:
            logger.error(f"MCP bridge initialization failed: {str(e)}")
            mcp_bridge_errors_total.inc()
            return False

    async def periodical_health_check(self):
        """Periodically check and announce bridge health"""
        while True:
            await asyncio.sleep(30)
            try:
                if self.redis_client:
                    await self.redis_client.setex(
                        f"mcp_bridge:health:{self.name}",
                        60,
                        "alive"
                    )
                    logger.debug(f"MCP bridge health ping: {self.name}")
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")

    async def periodic_participant_sync(self):
        """Periodically sync participants with registry"""
        while True:
            await asyncio.sleep(60)
            try:
                participants = await self.get_active_participants()
                with self.participant_lock:
                    self.mcp_participants = participants
                mcp_bridge_participants_total.set(len(participants))
                logger.debug(f"Synced {len(participants)} MCP participants")
            except Exception as e:
                logger.error(f"Participant sync failed: {str(e)}")

    async def handle_cloud_deployment(self):
        """Handle cloud-specific deployment requirements"""
        if self.config.get('ENV', '') in ['aws', 'gcp', 'kubernetes']:
            try:
                # Cloud service discovery
                self.service_discovery.set_cloud_discovery_config(self.config['ENV'])

                # Cloud load balancing
                cloud_lb_config = {
                    'provider': self.config['ENV'],
                    'region': os.getenv('AWS_REGION', 'us-east-1'),
                    'vpc': os.getenv('VPC_ID', 'default')
                }
                self.load_balancer.configure(cloud_lb_config)

                # Cloud monitoring
                if self.config.get('METRICS_ENDPOINT'):
                    monitoring_url = f"{self.config['METRICS_ENDPOINT']}/mcp-bridge"
                    await self.setup_cloud_monitoring(monitoring_url)

                logger.info(f"Cloud deployment configured for {self.config['ENV']}")
            except Exception as e:
                logger.error(f"Cloud deployment failed: {str(e)}")
                mcp_bridge_errors_total.inc()
                raise

    @with_circuit_breaker
    @retry(attempts=3, backoff=exponential)
    async def coordinate_task(self, task: dict) -> dict:
        """Coordinate task execution across MCP participants with retry and CB"""
        # Record timing and metric
        start_time = time.time()
        try:
            # Get swarm manager instance (already initialized)
            swarm_manager = EnhancedSwarmManager.get_instance()

            # Use swarm manager for coordination
            primary_swarm = self._determine_primary_swarm(task)
            result = await swarm_manager.execute_with_failover(
                task,
                primary_swarm=primary_swarm
            )

            # Log successful coordination
            mcp_bridge_call_duration_seconds.observe(time.time() - start_time)
            logger.info(f"✅ Task coordination successful: {task.get('task_id', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"Task coordination failed: {str(e)}")
            mcp_bridge_errors_total.inc()
            raise

    def _determine_primary_swarm(self, task: dict) -> str:
        """Determine which swarm to use as primary based on task type"""
        task_type = task.get('type', 'default')
        if 'api' in task_type or 'rest' in task_type:
            return "coding_swarm"
        elif 'research' in task_type or 'analysis' in task_type:
            return "research_swarm"
        elif 'ui' in task_type or 'visualization' in task_type:
            return "ui_swarm"
        return "default_swarm"

    async def broadcast_proposal(self, proposal: dict) -> bool:
        """Broadcast a proposal to all MCP participants"""
        try:
            # Create a broadcast message
            message = SwarmMessage(
                sender_agent_id=self.name,
                message_type=MessageType.PROPOSAL,
                content=proposal,
                thread_id=f"proposal:{datetime.now().timestamp()}"
            )

            # Publish via message bus
            await self.message_bus.publish(message)

            # Record message broadcast metric
            mcp_bridge_message_translations_total.labels('broadcast').inc()
            return True
        except Exception as e:
            logger.error(f"Proposal broadcast failed: {str(e)}")
            mcp_bridge_errors_total.inc()
            return False

    async def vote_on_proposal(self, proposal_id: str, vote: str) -> bool:
        """Record a vote on a proposal"""
        try:
            # Create a vote message
            message = SwarmMessage(
                sender_agent_id=self.name,
                message_type=MessageType.VOTE,
                content={
                    "proposal_id": proposal_id,
                    "vote": vote
                },
                thread_id=f"proposal:{proposal_id}"
            )

            # Publish via message bus
            await self.message_bus.publish(message)
            return True
        except Exception as e:
            logger.error(f"Vote recording failed: {str(e)}")
            mcp_bridge_errors_total.inc()
            return False

    async def get_consensus(self, thread_id: str) -> dict:
        """Get consensus result for a specific thread"""
        try:
            # Retrieve messages in thread
            messages = await self.message_bus.get_thread_history(thread_id)

            # Process messages to determine consensus
            consensus = self._analyze_consensus(messages)

            logger.debug(f"Consensus result: {consensus}")
            return consensus
        except Exception as e:
            logger.error(f"Consensus retrieval failed: {str(e)}")
            mcp_bridge_errors_total.inc()
            raise

    def _analyze_consensus(self, messages: list[SwarmMessage]) -> dict:
        """Analyze messages to determine consensus"""
        votes = {}
        for message in messages:
            if message.message_type == MessageType.VOTE:
                proposal_id = message.content.get("proposal_id")
                vote = message.content.get("vote")
                votes[proposal_id] = votes.get(proposal_id, []) + [vote]

        # Determine winning proposal
        if votes:
            winning_proposal = max(votes.items(), key=lambda x: len(x[1]))
            return {
                "proposal_id": winning_proposal[0],
                "vote_count": len(winning_proposal[1]),
                "consensus": "majority"
            }
        return {"consensus": "unknown"}

    async def setup_cloud_monitoring(self, url: str):
        """Set up cloud monitoring integration"""
        try:
            # Simulate sending metrics to cloud monitoring
            logger.info(f"Setting up cloud monitoring at {url}")
            await self.redis_client.set("mcp_bridge:monitoring:url", url)
            return True
        except Exception as e:
            logger.error(f"Cloud monitoring setup failed: {str(e)}")
            raise

    async def is_ready(self) -> bool:
        """Check if MCP bridge is ready for use"""
        if not self.redis_client or not self.service_discovery.is_registered():
            return False
        return await self.redis_client.get(f"mcp_bridge:health:{self.name}") == "alive"

class ServiceDiscovery:
    """Service discovery manager for MCP bridge"""

    def __init__(self):
        self._service_registry = {}
        self._cloud_discovery = None

    async def register(self, service_name: str, host: str, port: int, health_check_url: str):
        """Register with service discovery"""
        self._service_registry[service_name] = {
            'host': host,
            'port': port,
            'health_check': health_check_url
        }
        logger.info(f"Registered service {service_name} at {host}:{port}")

    def set_cloud_discovery_config(self, cloud_env: str):
        """Set cloud-specific discovery configuration"""
        if cloud_env == 'aws':
            self._cloud_discovery = 'aws_route53'
        elif cloud_env == 'gcp':
            self._cloud_discovery = 'gcp_service_discovery'
        elif cloud_env == 'kubernetes':
            self._cloud_discovery = 'k8s_endpoints'
        logger.info(f"Set cloud discovery for {cloud_env}: {self._cloud_discovery}")

    def is_registered(self) -> bool:
        """Check if service is registered"""
        return bool(self._service_registry)

class LoadBalancer:
    """Load balancer for MCP bridge"""

    def __init__(self):
        self._config = {}

    def configure(self, config: dict):
        """Configure load balancer"""
        self._config = config
        logger.info(f"Configured load balancer: {config}")

    def select_target(self, task: dict) -> str:
        """Select target based on task or load"""
        # Simple round-robin implementation
        return "target-1" if task.get('type', '').startswith('fast') else "target-2"

class MessageQueue:
    """Message queue for reliable message handling"""

    def __init__(self):
        self._queue = None
        self._is_connected = False

    async def connect(self):
        """Connect to message queue service"""
        try:
            self._queue = await aioredis.create_redis_pool(
                self.config.get('REDIS_URL', 'redis://localhost:6379'),
                minsize=1,
                maxsize=5
            )
            self._is_connected = True
            logger.info("Connected to message queue service")
        except Exception as e:
            logger.error(f"Message queue connection failed: {str(e)}")
            raise

    async def enqueue(self, message: dict):
        """Enqueue a message for processing"""
        if self._is_connected:
            await self._queue.rpush("mcp_bridge_queue", json.dumps(message))
            logger.debug("Message enqueued for MCP bridge")

    async def dequeue(self):
        """Dequeue a message from the queue"""
        if self._is_connected:
            message = await self._queue.lpop("mcp_bridge_queue")
            if message:
                return json.loads(message)
            return None
        return None

# Example usage
if __name__ == "__main__":
    async def demo():
        # Sample configuration
        config = {
            "REDIS_URL": "redis://localhost:6379",
            "ENV": "local"
        }

        bridge = ProductionMCPBridge(config)
        await bridge.initialize_with_ha()

        # Simulate task coordination
        task = {
            "task_id": "task_123",
            "type": "api_generation",
            "description": "Generate REST API for user management"
        }

        # Coordinate task
        try:
            result = await bridge.coordinate_task(task)
            print(f"Coordination result: {result}")
        except Exception as e:
            print(f"Coordination failed: {str(e)}")

        # Cleanup
        await bridge.redis_client.close()

    asyncio.run(demo())
