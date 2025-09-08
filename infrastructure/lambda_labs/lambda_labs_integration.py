#!/usr/bin/env python3
"""
Lambda Labs GPU Integration for Sophia AI Platform
Optimized for AI agent workloads with auto-scaling and cost optimization
"""

import asyncio
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LambdaLabsConfig:
    """Lambda Labs configuration with API credentials"""

    api_key: str
    api_endpoint: str = "https://cloud.lambdalabs.com/api/v1"

    # Instance preferences
    preferred_gpu_types: list[str] = None
    preferred_regions: list[str] = None

    # Auto-scaling configuration
    min_instances: int = 1
    max_instances: int = 10
    scale_up_threshold: float = 80.0  # CPU/GPU utilization %
    scale_down_threshold: float = 20.0

    # Cost optimization
    max_hourly_cost: float = 50.0  # Maximum cost per hour
    use_spot_instances: bool = True

    def __post_init__(self):
        if self.preferred_gpu_types is None:
            self.preferred_gpu_types = ["A100", "H100", "RTX_6000_Ada"]
        if self.preferred_regions is None:
            self.preferred_regions = ["us-east-1", "us-west-1", "eu-central-1"]

    @classmethod
    def from_env(cls) -> "LambdaLabsConfig":
        """Load configuration from environment variables"""
        return cls(
            api_key=os.getenv("LAMBDA_LABS_API_KEY", ""),
            api_endpoint=os.getenv("LAMBDA_LABS_ENDPOINT", "https://cloud.lambdalabs.com/api/v1"),
            preferred_gpu_types=os.getenv("LAMBDA_LABS_GPU_TYPES", "A100,H100,RTX_6000_Ada").split(
                ","
            ),
            preferred_regions=os.getenv("LAMBDA_LABS_REGIONS", "us-east-1,us-west-1").split(","),
            min_instances=int(os.getenv("LAMBDA_LABS_MIN_INSTANCES", "1")),
            max_instances=int(os.getenv("LAMBDA_LABS_MAX_INSTANCES", "10")),
            max_hourly_cost=float(os.getenv("LAMBDA_LABS_MAX_COST", "50.0")),
        )


@dataclass
class GPUInstance:
    """GPU instance representation"""

    instance_id: str
    instance_type: str
    gpu_type: str
    region: str
    status: str
    ip_address: str | None = None
    cost_per_hour: float = 0.0
    created_at: datetime | None = None
    utilization: dict[str, float] = None

    def __post_init__(self):
        if self.utilization is None:
            self.utilization = {"cpu": 0.0, "gpu": 0.0, "memory": 0.0}


class LambdaLabsClient:
    """Lambda Labs API client for GPU management"""

    def __init__(self, config: LambdaLabsConfig):
        self.config = config
        self.session = None
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_instance_types(self) -> list[dict[str, Any]]:
        """Get available GPU instance types and pricing"""
        try:
            async with self.session.get(f"{self.config.api_endpoint}/instance-types") as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("data", [])
        except Exception as e:
            logger.error(f"Failed to get instance types: {e}")
            return []

    async def launch_instance(
        self, instance_type: str, region: str, name: str = None
    ) -> GPUInstance | None:
        """Launch a new GPU instance"""
        try:
            payload = {
                "region_name": region,
                "instance_type_name": instance_type,
                "ssh_key_names": [],  # Add SSH keys if needed
                "file_system_names": [],
                "quantity": 1,
            }

            if name:
                payload["name"] = name

            async with self.session.post(
                f"{self.config.api_endpoint}/instance-operations/launch", json=payload
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get("data", {}).get("instance_ids"):
                    instance_id = data["data"]["instance_ids"][0]
                    logger.info(f"Launched instance: {instance_id}")

                    # Get instance details
                    return await self.get_instance(instance_id)

        except Exception as e:
            logger.error(f"Failed to launch instance: {e}")
            return None

    async def get_instance(self, instance_id: str) -> GPUInstance | None:
        """Get instance details"""
        try:
            async with self.session.get(
                f"{self.config.api_endpoint}/instances/{instance_id}"
            ) as response:
                response.raise_for_status()
                data = await response.json()

                instance_data = data.get("data", {})
                return GPUInstance(
                    instance_id=instance_data.get("id", ""),
                    instance_type=instance_data.get("instance_type", {}).get("name", ""),
                    gpu_type=instance_data.get("instance_type", {}).get("description", ""),
                    region=instance_data.get("region", {}).get("name", ""),
                    status=instance_data.get("status", ""),
                    ip_address=instance_data.get("ip", ""),
                    cost_per_hour=float(
                        instance_data.get("instance_type", {}).get("price_cents_per_hour", 0)
                    )
                    / 100,
                    created_at=(
                        datetime.fromisoformat(
                            instance_data.get("created_at", "").replace("Z", "+00:00")
                        )
                        if instance_data.get("created_at")
                        else None
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to get instance {instance_id}: {e}")
            return None

    async def list_instances(self) -> list[GPUInstance]:
        """List all instances"""
        try:
            async with self.session.get(f"{self.config.api_endpoint}/instances") as response:
                response.raise_for_status()
                data = await response.json()

                instances = []
                for instance_data in data.get("data", []):
                    instance = GPUInstance(
                        instance_id=instance_data.get("id", ""),
                        instance_type=instance_data.get("instance_type", {}).get("name", ""),
                        gpu_type=instance_data.get("instance_type", {}).get("description", ""),
                        region=instance_data.get("region", {}).get("name", ""),
                        status=instance_data.get("status", ""),
                        ip_address=instance_data.get("ip", ""),
                        cost_per_hour=float(
                            instance_data.get("instance_type", {}).get("price_cents_per_hour", 0)
                        )
                        / 100,
                        created_at=(
                            datetime.fromisoformat(
                                instance_data.get("created_at", "").replace("Z", "+00:00")
                            )
                            if instance_data.get("created_at")
                            else None
                        ),
                    )
                    instances.append(instance)

                return instances

        except Exception as e:
            logger.error(f"Failed to list instances: {e}")
            return []

    async def terminate_instance(self, instance_id: str) -> bool:
        """Terminate an instance"""
        try:
            payload = {"instance_ids": [instance_id]}

            async with self.session.post(
                f"{self.config.api_endpoint}/instance-operations/terminate",
                json=payload,
            ) as response:
                response.raise_for_status()
                logger.info(f"Terminated instance: {instance_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to terminate instance {instance_id}: {e}")
            return False

    async def restart_instance(self, instance_id: str) -> bool:
        """Restart an instance"""
        try:
            payload = {"instance_ids": [instance_id]}

            async with self.session.post(
                f"{self.config.api_endpoint}/instance-operations/restart", json=payload
            ) as response:
                response.raise_for_status()
                logger.info(f"Restarted instance: {instance_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to restart instance {instance_id}: {e}")
            return False


class SophiaAIWorkloadManager:
    """Workload manager optimized for Sophia AI agents"""

    def __init__(self, lambda_client: LambdaLabsClient):
        self.client = lambda_client
        self.config = lambda_client.config
        self.active_instances: dict[str, GPUInstance] = {}
        self.workload_queue: list[dict[str, Any]] = []

    async def get_optimal_instance_type(self, workload_type: str = "ai_agent") -> str | None:
        """Get optimal instance type for workload"""

        instance_types = await self.client.get_instance_types()

        # Workload-specific preferences
        workload_preferences = {
            "ai_agent": {
                "min_gpu_memory": 24,  # GB
                "preferred_gpus": ["A100", "H100", "RTX_6000_Ada"],
                "max_cost_per_hour": 3.0,
            },
            "training": {
                "min_gpu_memory": 40,
                "preferred_gpus": ["A100", "H100"],
                "max_cost_per_hour": 5.0,
            },
            "inference": {
                "min_gpu_memory": 16,
                "preferred_gpus": ["RTX_6000_Ada", "A100"],
                "max_cost_per_hour": 2.0,
            },
        }

        preferences = workload_preferences.get(workload_type, workload_preferences["ai_agent"])

        # Filter and rank instance types
        suitable_instances = []
        for instance_type in instance_types:
            gpu_info = instance_type.get("instance_type", {})
            gpu_memory = gpu_info.get("gpu_memory_gb", 0)
            cost_per_hour = float(gpu_info.get("price_cents_per_hour", 0)) / 100
            gpu_name = gpu_info.get("description", "")

            # Check if meets requirements
            if (
                gpu_memory >= preferences["min_gpu_memory"]
                and cost_per_hour <= preferences["max_cost_per_hour"]
                and any(gpu in gpu_name for gpu in preferences["preferred_gpus"])
            ):

                suitable_instances.append(
                    {
                        "name": gpu_info.get("name", ""),
                        "gpu_memory": gpu_memory,
                        "cost_per_hour": cost_per_hour,
                        "gpu_name": gpu_name,
                        "score": gpu_memory / cost_per_hour,  # Performance per dollar
                    }
                )

        # Sort by score (performance per dollar)
        suitable_instances.sort(key=lambda x: x["score"], reverse=True)

        if suitable_instances:
            best_instance = suitable_instances[0]
            logger.info(
                f"Selected optimal instance: {best_instance['name']} ({best_instance['gpu_name']}) - ${best_instance['cost_per_hour']:.2f}/hour"
            )
            return best_instance["name"]

        logger.warning("No suitable instance type found for workload")
        return None

    async def scale_up(self, target_instances: int = None) -> list[GPUInstance]:
        """Scale up GPU instances for increased workload"""

        current_count = len(self.active_instances)
        if target_instances is None:
            target_instances = min(current_count + 1, self.config.max_instances)

        if target_instances <= current_count:
            logger.info(f"No scale-up needed. Current: {current_count}, Target: {target_instances}")
            return []

        instances_to_launch = target_instances - current_count
        logger.info(f"Scaling up: launching {instances_to_launch} instances")

        # Get optimal instance type
        instance_type = await self.get_optimal_instance_type("ai_agent")
        if not instance_type:
            logger.error("Cannot scale up: no suitable instance type found")
            return []

        # Launch instances
        launched_instances = []
        for i in range(instances_to_launch):
            # Try different regions for availability
            for region in self.config.preferred_regions:
                instance_name = f"sophia-ai-agent-{int(time.time())}-{i}"
                instance = await self.client.launch_instance(instance_type, region, instance_name)

                if instance:
                    self.active_instances[instance.instance_id] = instance
                    launched_instances.append(instance)
                    logger.info(f"Launched instance {instance.instance_id} in {region}")
                    break
            else:
                logger.warning(f"Failed to launch instance {i} in any region")

        return launched_instances

    async def scale_down(self, target_instances: int = None) -> list[str]:
        """Scale down GPU instances to reduce costs"""

        current_count = len(self.active_instances)
        if target_instances is None:
            target_instances = max(current_count - 1, self.config.min_instances)

        if target_instances >= current_count:
            logger.info(
                f"No scale-down needed. Current: {current_count}, Target: {target_instances}"
            )
            return []

        instances_to_terminate = current_count - target_instances
        logger.info(f"Scaling down: terminating {instances_to_terminate} instances")

        # Sort instances by cost (terminate most expensive first)
        instances_by_cost = sorted(
            self.active_instances.values(), key=lambda x: x.cost_per_hour, reverse=True
        )

        terminated_instances = []
        for i in range(instances_to_terminate):
            if i < len(instances_by_cost):
                instance = instances_by_cost[i]
                success = await self.client.terminate_instance(instance.instance_id)

                if success:
                    del self.active_instances[instance.instance_id]
                    terminated_instances.append(instance.instance_id)
                    logger.info(f"Terminated instance {instance.instance_id}")

        return terminated_instances

    async def monitor_and_autoscale(self) -> dict[str, Any]:
        """Monitor instances and auto-scale based on utilization"""

        # Refresh instance list
        all_instances = await self.client.list_instances()
        self.active_instances = {
            inst.instance_id: inst
            for inst in all_instances
            if inst.status in ["running", "booting"]
        }

        current_count = len(self.active_instances)
        total_cost_per_hour = sum(inst.cost_per_hour for inst in self.active_instances.values())

        # Calculate average utilization (simulated for now)
        # In production, you'd get real metrics from monitoring agents
        avg_utilization = 50.0  # Placeholder

        scaling_action = None

        # Auto-scaling logic
        if (
            avg_utilization > self.config.scale_up_threshold
            and current_count < self.config.max_instances
        ):
            if total_cost_per_hour < self.config.max_hourly_cost:
                await self.scale_up()
                scaling_action = "scale_up"
            else:
                logger.warning(
                    f"Cannot scale up: would exceed cost limit (${total_cost_per_hour:.2f}/hour)"
                )

        elif (
            avg_utilization < self.config.scale_down_threshold
            and current_count > self.config.min_instances
        ):
            await self.scale_down()
            scaling_action = "scale_down"

        return {
            "timestamp": datetime.now().isoformat(),
            "active_instances": current_count,
            "total_cost_per_hour": total_cost_per_hour,
            "avg_utilization": avg_utilization,
            "scaling_action": scaling_action,
            "instances": [asdict(inst) for inst in self.active_instances.values()],
        }

    async def deploy_sophia_ai_stack(self, instance_id: str) -> bool:
        """Deploy Sophia AI stack to a GPU instance"""

        instance = self.active_instances.get(instance_id)
        if not instance or not instance.ip_address:
            logger.error(f"Instance {instance_id} not found or no IP address")
            return False

        # Deployment script (would be executed via SSH in production)

        logger.info(f"Deployment script prepared for instance {instance_id}")
        # In production, execute this script via SSH
        # For now, just log the deployment

        return True


class CostOptimizer:
    """Cost optimization for Lambda Labs usage"""

    def __init__(self, workload_manager: SophiaAIWorkloadManager):
        self.workload_manager = workload_manager
        self.cost_history: list[dict[str, Any]] = []

    async def analyze_costs(self, days: int = 7) -> dict[str, Any]:
        """Analyze costs over the specified period"""

        # Get current instances and costs
        instances = await self.workload_manager.client.list_instances()
        current_hourly_cost = sum(
            inst.cost_per_hour for inst in instances if inst.status == "running"
        )

        # Estimate daily and monthly costs
        daily_cost = current_hourly_cost * 24
        monthly_cost = daily_cost * 30

        # Cost breakdown by instance type
        cost_breakdown = {}
        for instance in instances:
            if instance.status == "running":
                if instance.instance_type not in cost_breakdown:
                    cost_breakdown[instance.instance_type] = {
                        "count": 0,
                        "hourly_cost": 0,
                        "gpu_type": instance.gpu_type,
                    }
                cost_breakdown[instance.instance_type]["count"] += 1
                cost_breakdown[instance.instance_type]["hourly_cost"] += instance.cost_per_hour

        # Optimization recommendations
        recommendations = []

        if current_hourly_cost > 10:
            recommendations.append("Consider using spot instances for non-critical workloads")

        if len(instances) > 5:
            recommendations.append("Evaluate if all instances are actively used")

        if monthly_cost > 1000:
            recommendations.append("Consider reserved instances for long-term workloads")

        return {
            "current_hourly_cost": current_hourly_cost,
            "estimated_daily_cost": daily_cost,
            "estimated_monthly_cost": monthly_cost,
            "active_instances": len([i for i in instances if i.status == "running"]),
            "cost_breakdown": cost_breakdown,
            "recommendations": recommendations,
            "analysis_date": datetime.now().isoformat(),
        }

    async def suggest_optimizations(self) -> list[str]:
        """Suggest cost optimizations"""

        cost_analysis = await self.analyze_costs()
        suggestions = []

        # High-level suggestions
        if cost_analysis["estimated_monthly_cost"] > 2000:
            suggestions.append(
                "🚨 High monthly cost detected. Consider implementing more aggressive auto-scaling."
            )

        if cost_analysis["active_instances"] > 8:
            suggestions.append(
                "📊 Many active instances. Review workload distribution and consolidation opportunities."
            )

        # Instance-specific suggestions
        for instance_type, details in cost_analysis["cost_breakdown"].items():
            if details["hourly_cost"] > 5:
                suggestions.append(
                    f"💰 {instance_type} instances are expensive (${details['hourly_cost']:.2f}/hour). Consider smaller instances for development."
                )

        return suggestions


async def main():
    """Main function for testing Lambda Labs integration"""

    # Load configuration
    config = LambdaLabsConfig.from_env()

    if not config.api_key:
        logger.error("Missing LAMBDA_LABS_API_KEY environment variable")
        return

    async with LambdaLabsClient(config) as client:
        # Initialize workload manager
        workload_manager = SophiaAIWorkloadManager(client)

        # Test basic functionality
        logger.info("🔍 Testing Lambda Labs integration...")

        # Get available instance types
        instance_types = await client.get_instance_types()
        logger.info(f"Available instance types: {len(instance_types)}")

        # Get optimal instance type
        optimal_type = await workload_manager.get_optimal_instance_type("ai_agent")
        logger.info(f"Optimal instance type for AI agents: {optimal_type}")

        # List current instances
        instances = await client.list_instances()
        logger.info(f"Current instances: {len(instances)}")

        # Monitor and analyze costs
        cost_optimizer = CostOptimizer(workload_manager)
        cost_analysis = await cost_optimizer.analyze_costs()
        logger.info(f"Cost analysis: ${cost_analysis['estimated_monthly_cost']:.2f}/month")

        # Get optimization suggestions
        suggestions = await cost_optimizer.suggest_optimizations()
        for suggestion in suggestions:
            logger.info(f"💡 {suggestion}")

        logger.info("✅ Lambda Labs integration test completed")


if __name__ == "__main__":
    asyncio.run(main())
