"""
Traffic Manager for Sophia-Artemis Service Mesh
Manages traffic shifting, canary deployments, and failover scenarios
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class DeploymentStrategy(Enum):
    """Deployment strategies"""

    CANARY = "canary"
    BLUE_GREEN = "blue_green"
    A_B_TESTING = "a_b_testing"
    ROLLING = "rolling"
    RECREATE = "recreate"


class TrafficShiftMode(Enum):
    """Traffic shifting modes"""

    GRADUAL = "gradual"
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"


@dataclass
class TrafficPolicy:
    """Traffic policy configuration"""

    service_name: str
    namespace: str
    strategy: DeploymentStrategy
    shift_mode: TrafficShiftMode
    target_version: str
    canary_percentage: int = 10
    increment_percentage: int = 10
    increment_interval: timedelta = timedelta(minutes=5)
    success_threshold: float = 0.95
    rollback_threshold: float = 0.90
    max_request_rate: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TrafficSplit:
    """Traffic split configuration"""

    service_name: str
    namespace: str
    splits: Dict[str, int]  # version -> percentage
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CanaryDeployment:
    """Canary deployment state"""

    service_name: str
    namespace: str
    stable_version: str
    canary_version: str
    current_percentage: int
    target_percentage: int
    status: str = "in_progress"
    metrics: Dict[str, float] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)


class TrafficManager:
    """
    Manages traffic routing and deployment strategies in the service mesh
    """

    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        prometheus_url: str = "http://prometheus.istio-system:9090",
    ):
        """
        Initialize the traffic manager

        Args:
            kubeconfig_path: Path to kubeconfig file (None for in-cluster)
            prometheus_url: Prometheus URL for metrics
        """
        self.prometheus_url = prometheus_url
        self.policies: Dict[str, TrafficPolicy] = {}
        self.active_canaries: Dict[str, CanaryDeployment] = {}
        self.traffic_splits: Dict[str, TrafficSplit] = {}
        self.running = False

        # Initialize Kubernetes client
        try:
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                config.load_incluster_config()

            self.custom_api = client.CustomObjectsApi()
            self.apps_v1 = client.AppsV1Api()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    async def start(self):
        """Start the traffic manager"""
        logger.info("Starting traffic manager")
        self.running = True

        # Start monitoring active deployments
        asyncio.create_task(self.monitor_deployments())

        # Start traffic shift executor
        asyncio.create_task(self.execute_traffic_shifts())

        logger.info("Traffic manager started")

    async def stop(self):
        """Stop the traffic manager"""
        logger.info("Stopping traffic manager")
        self.running = False
        logger.info("Traffic manager stopped")

    async def create_canary_deployment(
        self,
        service_name: str,
        namespace: str,
        stable_version: str,
        canary_version: str,
        initial_percentage: int = 10,
        target_percentage: int = 100,
    ) -> CanaryDeployment:
        """
        Create a canary deployment

        Args:
            service_name: Service name
            namespace: Service namespace
            stable_version: Stable version
            canary_version: Canary version
            initial_percentage: Initial traffic percentage for canary
            target_percentage: Target traffic percentage for canary

        Returns:
            CanaryDeployment object
        """
        logger.info(f"Creating canary deployment for {namespace}/{service_name}")

        # Create canary deployment
        canary = CanaryDeployment(
            service_name=service_name,
            namespace=namespace,
            stable_version=stable_version,
            canary_version=canary_version,
            current_percentage=0,
            target_percentage=target_percentage,
        )

        # Store canary
        canary_key = f"{namespace}/{service_name}"
        self.active_canaries[canary_key] = canary

        # Update virtual service for initial traffic split
        await self.update_traffic_split(
            service_name,
            namespace,
            {stable_version: 100 - initial_percentage, canary_version: initial_percentage},
        )

        canary.current_percentage = initial_percentage
        canary.last_update = datetime.now()

        logger.info(f"Canary deployment created: {canary_key}")
        return canary

    async def update_traffic_split(self, service_name: str, namespace: str, splits: Dict[str, int]):
        """
        Update traffic split for a service

        Args:
            service_name: Service name
            namespace: Service namespace
            splits: Traffic splits (version -> percentage)
        """
        # Validate splits
        total = sum(splits.values())
        if total != 100:
            raise ValueError(f"Traffic splits must sum to 100, got {total}")

        logger.info(f"Updating traffic split for {namespace}/{service_name}: {splits}")

        try:
            # Get existing virtual service
            vs = self.custom_api.get_namespaced_custom_object(
                group="networking.istio.io",
                version="v1beta1",
                namespace=namespace,
                plural="virtualservices",
                name=service_name,
            )

            # Update route weights
            if "spec" in vs and "http" in vs["spec"]:
                for http_route in vs["spec"]["http"]:
                    if "route" in http_route:
                        http_route["route"] = []
                        for version, percentage in splits.items():
                            http_route["route"].append(
                                {
                                    "destination": {"host": service_name, "subset": version},
                                    "weight": percentage,
                                }
                            )

            # Apply update
            self.custom_api.patch_namespaced_custom_object(
                group="networking.istio.io",
                version="v1beta1",
                namespace=namespace,
                plural="virtualservices",
                name=service_name,
                body=vs,
            )

            # Store traffic split
            split_key = f"{namespace}/{service_name}"
            self.traffic_splits[split_key] = TrafficSplit(
                service_name=service_name, namespace=namespace, splits=splits
            )

            logger.info(f"Traffic split updated for {split_key}")

        except ApiException as e:
            logger.error(f"Failed to update traffic split: {e}")
            raise

    async def rollout_canary(self, service_name: str, namespace: str, increment: int = 10):
        """
        Increase canary traffic by increment

        Args:
            service_name: Service name
            namespace: Service namespace
            increment: Traffic increment percentage
        """
        canary_key = f"{namespace}/{service_name}"
        if canary_key not in self.active_canaries:
            raise ValueError(f"No active canary deployment for {canary_key}")

        canary = self.active_canaries[canary_key]

        # Calculate new percentage
        new_percentage = min(canary.current_percentage + increment, canary.target_percentage)

        # Update traffic split
        await self.update_traffic_split(
            service_name,
            namespace,
            {canary.stable_version: 100 - new_percentage, canary.canary_version: new_percentage},
        )

        canary.current_percentage = new_percentage
        canary.last_update = datetime.now()

        # Check if rollout complete
        if canary.current_percentage >= canary.target_percentage:
            canary.status = "completed"
            logger.info(f"Canary rollout completed for {canary_key}")

        logger.info(f"Canary traffic increased to {new_percentage}% for {canary_key}")

    async def rollback_canary(self, service_name: str, namespace: str):
        """
        Rollback a canary deployment

        Args:
            service_name: Service name
            namespace: Service namespace
        """
        canary_key = f"{namespace}/{service_name}"
        if canary_key not in self.active_canaries:
            raise ValueError(f"No active canary deployment for {canary_key}")

        canary = self.active_canaries[canary_key]

        logger.warning(f"Rolling back canary deployment for {canary_key}")

        # Reset traffic to stable version
        await self.update_traffic_split(
            service_name, namespace, {canary.stable_version: 100, canary.canary_version: 0}
        )

        canary.status = "rolled_back"
        canary.current_percentage = 0
        canary.last_update = datetime.now()

        logger.info(f"Canary rollback completed for {canary_key}")

    async def implement_blue_green(
        self,
        service_name: str,
        namespace: str,
        blue_version: str,
        green_version: str,
        switch_to_green: bool = True,
    ):
        """
        Implement blue-green deployment

        Args:
            service_name: Service name
            namespace: Service namespace
            blue_version: Blue version
            green_version: Green version
            switch_to_green: Whether to switch to green
        """
        logger.info(f"Implementing blue-green deployment for {namespace}/{service_name}")

        if switch_to_green:
            splits = {blue_version: 0, green_version: 100}
        else:
            splits = {blue_version: 100, green_version: 0}

        await self.update_traffic_split(service_name, namespace, splits)

        logger.info(
            f"Blue-green deployment completed: {'green' if switch_to_green else 'blue'} is active"
        )

    async def setup_ab_testing(
        self,
        service_name: str,
        namespace: str,
        version_splits: Dict[str, int],
        routing_rules: Optional[Dict[str, Any]] = None,
    ):
        """
        Setup A/B testing

        Args:
            service_name: Service name
            namespace: Service namespace
            version_splits: Version traffic splits
            routing_rules: Optional routing rules for A/B testing
        """
        logger.info(f"Setting up A/B testing for {namespace}/{service_name}")

        # Update traffic splits
        await self.update_traffic_split(service_name, namespace, version_splits)

        # Apply routing rules if provided
        if routing_rules:
            await self._apply_ab_routing_rules(service_name, namespace, routing_rules)

        logger.info(f"A/B testing setup completed for {namespace}/{service_name}")

    async def handle_failover(
        self, service_name: str, namespace: str, failed_version: str, fallback_version: str
    ):
        """
        Handle failover scenario

        Args:
            service_name: Service name
            namespace: Service namespace
            failed_version: Failed version
            fallback_version: Fallback version
        """
        logger.warning(f"Handling failover for {namespace}/{service_name}")

        # Redirect all traffic to fallback version
        await self.update_traffic_split(
            service_name, namespace, {failed_version: 0, fallback_version: 100}
        )

        # Update destination rule to exclude failed version
        await self._update_outlier_detection(service_name, namespace, failed_version)

        logger.info(f"Failover completed: traffic redirected to {fallback_version}")

    async def monitor_deployments(self):
        """Monitor active deployments and auto-progress canaries"""
        while self.running:
            try:
                for canary_key, canary in list(self.active_canaries.items()):
                    if canary.status != "in_progress":
                        continue

                    # Get metrics for canary
                    metrics = await self._get_canary_metrics(
                        canary.service_name, canary.namespace, canary.canary_version
                    )

                    canary.metrics = metrics

                    # Check if should rollback
                    if metrics.get("success_rate", 0) < 0.90:
                        logger.warning(f"Canary metrics below threshold for {canary_key}")
                        await self.rollback_canary(canary.service_name, canary.namespace)
                        continue

                    # Check if should progress
                    if metrics.get("success_rate", 0) >= 0.95:
                        time_since_update = datetime.now() - canary.last_update
                        if time_since_update >= timedelta(minutes=5):
                            await self.rollout_canary(
                                canary.service_name, canary.namespace, increment=10
                            )

            except Exception as e:
                logger.error(f"Error monitoring deployments: {e}")

            await asyncio.sleep(30)

    async def execute_traffic_shifts(self):
        """Execute gradual traffic shifts"""
        while self.running:
            try:
                for policy_key, policy in list(self.policies.items()):
                    if policy.shift_mode != TrafficShiftMode.GRADUAL:
                        continue

                    # Check if should shift traffic
                    time_since_update = datetime.now() - policy.updated_at
                    if time_since_update >= policy.increment_interval:
                        canary_key = f"{policy.namespace}/{policy.service_name}"
                        if canary_key in self.active_canaries:
                            await self.rollout_canary(
                                policy.service_name, policy.namespace, policy.increment_percentage
                            )
                            policy.updated_at = datetime.now()

            except Exception as e:
                logger.error(f"Error executing traffic shifts: {e}")

            await asyncio.sleep(60)

    async def _get_canary_metrics(
        self, service_name: str, namespace: str, version: str
    ) -> Dict[str, float]:
        """Get metrics for canary version"""
        metrics = {}

        try:
            async with aiohttp.ClientSession() as session:
                # Success rate query
                query = f"""
                    sum(rate(istio_request_total{{
                        destination_service_name="{service_name}",
                        destination_service_namespace="{namespace}",
                        destination_version="{version}",
                        response_code!~"5.."
                    }}[5m])) /
                    sum(rate(istio_request_total{{
                        destination_service_name="{service_name}",
                        destination_service_namespace="{namespace}",
                        destination_version="{version}"
                    }}[5m]))
                """

                async with session.get(
                    f"{self.prometheus_url}/api/v1/query", params={"query": query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["status"] == "success" and data["data"]["result"]:
                            metrics["success_rate"] = float(data["data"]["result"][0]["value"][1])

                # P95 latency query
                query = f"""
                    histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{{
                        destination_service_name="{service_name}",
                        destination_service_namespace="{namespace}",
                        destination_version="{version}"
                    }}[5m])) by (le))
                """

                async with session.get(
                    f"{self.prometheus_url}/api/v1/query", params={"query": query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["status"] == "success" and data["data"]["result"]:
                            metrics["p95_latency"] = float(data["data"]["result"][0]["value"][1])

                # Request rate query
                query = f"""
                    sum(rate(istio_request_total{{
                        destination_service_name="{service_name}",
                        destination_service_namespace="{namespace}",
                        destination_version="{version}"
                    }}[5m]))
                """

                async with session.get(
                    f"{self.prometheus_url}/api/v1/query", params={"query": query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["status"] == "success" and data["data"]["result"]:
                            metrics["request_rate"] = float(data["data"]["result"][0]["value"][1])

        except Exception as e:
            logger.error(f"Error getting canary metrics: {e}")

        return metrics

    async def _apply_ab_routing_rules(
        self, service_name: str, namespace: str, routing_rules: Dict[str, Any]
    ):
        """Apply A/B testing routing rules"""
        try:
            # Get existing virtual service
            vs = self.custom_api.get_namespaced_custom_object(
                group="networking.istio.io",
                version="v1beta1",
                namespace=namespace,
                plural="virtualservices",
                name=service_name,
            )

            # Add match conditions for A/B testing
            if "spec" in vs and "http" in vs["spec"]:
                # Insert A/B testing rules before default routes
                ab_routes = []

                for rule_name, rule_config in routing_rules.items():
                    route = {"name": rule_name, "match": rule_config.get("match", []), "route": []}

                    # Add destinations based on rule
                    for version, weight in rule_config.get("route_to", {}).items():
                        route["route"].append(
                            {
                                "destination": {"host": service_name, "subset": version},
                                "weight": weight,
                            }
                        )

                    ab_routes.append(route)

                # Combine A/B routes with existing routes
                vs["spec"]["http"] = ab_routes + vs["spec"]["http"]

            # Apply update
            self.custom_api.patch_namespaced_custom_object(
                group="networking.istio.io",
                version="v1beta1",
                namespace=namespace,
                plural="virtualservices",
                name=service_name,
                body=vs,
            )

            logger.info(f"A/B routing rules applied for {namespace}/{service_name}")

        except ApiException as e:
            logger.error(f"Failed to apply A/B routing rules: {e}")
            raise

    async def _update_outlier_detection(
        self, service_name: str, namespace: str, excluded_version: str
    ):
        """Update outlier detection to exclude failed version"""
        try:
            # Get existing destination rule
            dr = self.custom_api.get_namespaced_custom_object(
                group="networking.istio.io",
                version="v1beta1",
                namespace=namespace,
                plural="destinationrules",
                name=service_name,
            )

            # Update outlier detection
            if "spec" not in dr:
                dr["spec"] = {}

            if "trafficPolicy" not in dr["spec"]:
                dr["spec"]["trafficPolicy"] = {}

            dr["spec"]["trafficPolicy"]["outlierDetection"] = {
                "consecutiveErrors": 1,
                "interval": "1s",
                "baseEjectionTime": "3600s",
                "maxEjectionPercent": 100,
                "minHealthPercent": 0,
                "splitExternalLocalOriginErrors": True,
            }

            # Mark excluded version subset as unhealthy
            if "subsets" in dr["spec"]:
                for subset in dr["spec"]["subsets"]:
                    if subset.get("name") == excluded_version:
                        if "trafficPolicy" not in subset:
                            subset["trafficPolicy"] = {}
                        subset["trafficPolicy"]["outlierDetection"] = {
                            "consecutiveErrors": 1,
                            "baseEjectionTime": "3600s",
                        }

            # Apply update
            self.custom_api.patch_namespaced_custom_object(
                group="networking.istio.io",
                version="v1beta1",
                namespace=namespace,
                plural="destinationrules",
                name=service_name,
                body=dr,
            )

            logger.info(f"Outlier detection updated for {namespace}/{service_name}")

        except ApiException as e:
            logger.error(f"Failed to update outlier detection: {e}")
            raise

    async def get_traffic_split(self, service_name: str, namespace: str) -> Optional[TrafficSplit]:
        """
        Get current traffic split for a service

        Args:
            service_name: Service name
            namespace: Service namespace

        Returns:
            TrafficSplit or None
        """
        split_key = f"{namespace}/{service_name}"
        return self.traffic_splits.get(split_key)

    async def get_canary_status(
        self, service_name: str, namespace: str
    ) -> Optional[CanaryDeployment]:
        """
        Get canary deployment status

        Args:
            service_name: Service name
            namespace: Service namespace

        Returns:
            CanaryDeployment or None
        """
        canary_key = f"{namespace}/{service_name}"
        return self.active_canaries.get(canary_key)

    def create_traffic_policy(
        self, service_name: str, namespace: str, strategy: DeploymentStrategy, **kwargs
    ) -> TrafficPolicy:
        """
        Create a traffic policy

        Args:
            service_name: Service name
            namespace: Service namespace
            strategy: Deployment strategy
            **kwargs: Additional policy parameters

        Returns:
            TrafficPolicy object
        """
        policy = TrafficPolicy(
            service_name=service_name,
            namespace=namespace,
            strategy=strategy,
            shift_mode=kwargs.get("shift_mode", TrafficShiftMode.GRADUAL),
            target_version=kwargs.get("target_version", "unknown"),
            canary_percentage=kwargs.get("canary_percentage", 10),
            increment_percentage=kwargs.get("increment_percentage", 10),
            increment_interval=kwargs.get("increment_interval", timedelta(minutes=5)),
            success_threshold=kwargs.get("success_threshold", 0.95),
            rollback_threshold=kwargs.get("rollback_threshold", 0.90),
            max_request_rate=kwargs.get("max_request_rate"),
        )

        policy_key = f"{namespace}/{service_name}"
        self.policies[policy_key] = policy

        return policy
