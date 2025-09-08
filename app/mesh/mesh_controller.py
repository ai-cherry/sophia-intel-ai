"""
Service Mesh Controller for Sophia-Artemis
Manages service discovery, registration, and mesh configuration updates
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import aiohttp
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status in the mesh"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceEndpoint:
    """Represents a service endpoint in the mesh"""

    name: str
    namespace: str
    address: str
    port: int
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    version: str = "unknown"
    protocol: str = "http"


@dataclass
class MeshService:
    """Represents a service in the mesh"""

    name: str
    namespace: str
    domain: str  # artemis, sophia, or shared
    endpoints: list[ServiceEndpoint] = field(default_factory=list)
    virtual_service: Optional[str] = None
    destination_rule: Optional[str] = None
    service_entry: Optional[str] = None
    labels: dict[str, str] = field(default_factory=dict)
    selectors: dict[str, str] = field(default_factory=dict)
    ports: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class MeshController:
    """
    Controls service mesh operations including discovery and registration
    """

    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        istio_namespace: str = "istio-system",
        prometheus_url: str = "http://prometheus.istio-system:9090",
    ):
        """
        Initialize the mesh controller

        Args:
            kubeconfig_path: Path to kubeconfig file (None for in-cluster)
            istio_namespace: Istio system namespace
            prometheus_url: Prometheus URL for metrics
        """
        self.istio_namespace = istio_namespace
        self.prometheus_url = prometheus_url
        self.services: dict[str, MeshService] = {}
        self.watchers: dict[str, watch.Watch] = {}
        self.running = False

        # Initialize Kubernetes client
        try:
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                config.load_incluster_config()

            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1beta1 = client.NetworkingV1beta1Api()
            self.custom_api = client.CustomObjectsApi()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    async def start(self):
        """Start the mesh controller"""
        logger.info("Starting mesh controller")
        self.running = True

        # Start service discovery
        await self.discover_services()

        # Start watchers for changes
        await self.start_watchers()

        # Start health monitoring
        asyncio.create_task(self.monitor_health())

        logger.info("Mesh controller started")

    async def stop(self):
        """Stop the mesh controller"""
        logger.info("Stopping mesh controller")
        self.running = False

        # Stop all watchers
        for watcher in self.watchers.values():
            watcher.stop()

        logger.info("Mesh controller stopped")

    async def discover_services(self):
        """Discover all services in the mesh"""
        logger.info("Discovering services in mesh")

        namespaces = ["artemis-mesh", "sophia-mesh", "shared-services"]

        for namespace in namespaces:
            try:
                # Get services
                services = self.v1.list_namespaced_service(namespace)

                for svc in services.items:
                    await self.register_service(svc, namespace)

            except ApiException as e:
                logger.error(f"Failed to discover services in {namespace}: {e}")

        logger.info(f"Discovered {len(self.services)} services")

    async def register_service(
        self, service: Any, namespace: str
    ) -> Optional[MeshService]:
        """
        Register a service in the mesh

        Args:
            service: Kubernetes service object
            namespace: Service namespace

        Returns:
            Registered MeshService or None
        """
        try:
            # Determine domain
            domain = self._get_domain_from_namespace(namespace)

            # Create MeshService
            mesh_service = MeshService(
                name=service.metadata.name,
                namespace=namespace,
                domain=domain,
                labels=service.metadata.labels or {},
                selectors=service.spec.selector or {},
                ports=(
                    [
                        {
                            "name": p.name,
                            "port": p.port,
                            "targetPort": p.target_port,
                            "protocol": p.protocol,
                        }
                        for p in service.spec.ports
                    ]
                    if service.spec.ports
                    else []
                ),
            )

            # Get endpoints
            endpoints = self.v1.list_namespaced_endpoints(
                namespace, field_selector=f"metadata.name={service.metadata.name}"
            )

            for ep in endpoints.items:
                if ep.subsets:
                    for subset in ep.subsets:
                        if subset.addresses:
                            for addr in subset.addresses:
                                for port in subset.ports or []:
                                    endpoint = ServiceEndpoint(
                                        name=f"{service.metadata.name}-{addr.ip}",
                                        namespace=namespace,
                                        address=addr.ip,
                                        port=port.port,
                                        protocol=port.protocol or "TCP",
                                    )
                                    mesh_service.endpoints.append(endpoint)

            # Check for Istio configurations
            mesh_service.virtual_service = await self._get_virtual_service(
                service.metadata.name, namespace
            )
            mesh_service.destination_rule = await self._get_destination_rule(
                service.metadata.name, namespace
            )

            # Store service
            service_key = f"{namespace}/{service.metadata.name}"
            self.services[service_key] = mesh_service

            logger.info(f"Registered service: {service_key}")
            return mesh_service

        except Exception as e:
            logger.error(f"Failed to register service {service.metadata.name}: {e}")
            return None

    async def deregister_service(self, name: str, namespace: str):
        """
        Deregister a service from the mesh

        Args:
            name: Service name
            namespace: Service namespace
        """
        service_key = f"{namespace}/{name}"
        if service_key in self.services:
            del self.services[service_key]
            logger.info(f"Deregistered service: {service_key}")

    async def update_service(self, name: str, namespace: str, updates: dict[str, Any]):
        """
        Update service configuration

        Args:
            name: Service name
            namespace: Service namespace
            updates: Updates to apply
        """
        service_key = f"{namespace}/{name}"
        if service_key in self.services:
            service = self.services[service_key]

            # Apply updates
            for key, value in updates.items():
                if hasattr(service, key):
                    setattr(service, key, value)

            service.updated_at = datetime.now()
            logger.info(f"Updated service: {service_key}")

    async def get_service(self, name: str, namespace: str) -> Optional[MeshService]:
        """
        Get a service from the mesh

        Args:
            name: Service name
            namespace: Service namespace

        Returns:
            MeshService or None
        """
        service_key = f"{namespace}/{name}"
        return self.services.get(service_key)

    async def list_services(
        self, domain: Optional[str] = None, namespace: Optional[str] = None
    ) -> list[MeshService]:
        """
        List services in the mesh

        Args:
            domain: Filter by domain
            namespace: Filter by namespace

        Returns:
            List of MeshService objects
        """
        services = list(self.services.values())

        if domain:
            services = [s for s in services if s.domain == domain]

        if namespace:
            services = [s for s in services if s.namespace == namespace]

        return services

    async def get_healthy_endpoints(
        self, name: str, namespace: str
    ) -> list[ServiceEndpoint]:
        """
        Get healthy endpoints for a service

        Args:
            name: Service name
            namespace: Service namespace

        Returns:
            List of healthy endpoints
        """
        service = await self.get_service(name, namespace)
        if not service:
            return []

        return [
            ep
            for ep in service.endpoints
            if ep.status in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN]
        ]

    async def start_watchers(self):
        """Start Kubernetes watchers for service changes"""
        namespaces = ["artemis-mesh", "sophia-mesh", "shared-services"]

        for namespace in namespaces:
            # Watch services
            asyncio.create_task(self._watch_services(namespace))

            # Watch endpoints
            asyncio.create_task(self._watch_endpoints(namespace))

    async def _watch_services(self, namespace: str):
        """Watch for service changes in a namespace"""
        w = watch.Watch()
        self.watchers[f"services-{namespace}"] = w

        try:
            async for event in w.stream(
                self.v1.list_namespaced_service, namespace=namespace
            ):
                if not self.running:
                    break

                event_type = event["type"]
                service = event["object"]

                if event_type == "ADDED" or event_type == "MODIFIED":
                    await self.register_service(service, namespace)
                elif event_type == "DELETED":
                    await self.deregister_service(service.metadata.name, namespace)
        except Exception as e:
            logger.error(f"Error watching services in {namespace}: {e}")

    async def _watch_endpoints(self, namespace: str):
        """Watch for endpoint changes in a namespace"""
        w = watch.Watch()
        self.watchers[f"endpoints-{namespace}"] = w

        try:
            async for event in w.stream(
                self.v1.list_namespaced_endpoints, namespace=namespace
            ):
                if not self.running:
                    break

                event["type"]
                endpoints = event["object"]

                # Update service endpoints
                service_key = f"{namespace}/{endpoints.metadata.name}"
                if service_key in self.services:
                    service = self.services[service_key]
                    service.endpoints.clear()

                    if endpoints.subsets:
                        for subset in endpoints.subsets:
                            if subset.addresses:
                                for addr in subset.addresses:
                                    for port in subset.ports or []:
                                        endpoint = ServiceEndpoint(
                                            name=f"{endpoints.metadata.name}-{addr.ip}",
                                            namespace=namespace,
                                            address=addr.ip,
                                            port=port.port,
                                            protocol=port.protocol or "TCP",
                                        )
                                        service.endpoints.append(endpoint)

                    service.updated_at = datetime.now()

        except Exception as e:
            logger.error(f"Error watching endpoints in {namespace}: {e}")

    async def monitor_health(self):
        """Monitor health of services"""
        while self.running:
            try:
                # Query Prometheus for service health metrics
                async with aiohttp.ClientSession() as session:
                    # Check success rate
                    query = 'sum by (destination_service_name, destination_service_namespace) (rate(istio_request_total{response_code!~"5.."}[5m])) / sum by (destination_service_name, destination_service_namespace) (rate(istio_request_total[5m]))'

                    async with session.get(
                        f"{self.prometheus_url}/api/v1/query", params={"query": query}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data["status"] == "success":
                                for result in data["data"]["result"]:
                                    metric = result["metric"]
                                    value = float(result["value"][1])

                                    service_key = f"{metric['destination_service_namespace']}/{metric['destination_service_name']}"
                                    if service_key in self.services:
                                        service = self.services[service_key]

                                        # Update endpoint status based on success rate
                                        if value >= 0.99:
                                            status = ServiceStatus.HEALTHY
                                        elif value >= 0.95:
                                            status = ServiceStatus.DEGRADED
                                        else:
                                            status = ServiceStatus.UNHEALTHY

                                        for endpoint in service.endpoints:
                                            endpoint.status = status
                                            endpoint.last_health_check = datetime.now()

            except Exception as e:
                logger.error(f"Error monitoring service health: {e}")

            # Wait before next check
            await asyncio.sleep(30)

    async def _get_virtual_service(self, name: str, namespace: str) -> Optional[str]:
        """Get virtual service name for a service"""
        try:
            vs_list = self.custom_api.list_namespaced_custom_object(
                group="networking.istio.io",
                version="v1beta1",
                namespace=namespace,
                plural="virtualservices",
            )

            for vs in vs_list.get("items", []):
                if vs["metadata"]["name"] == name:
                    return name

                # Check if service is in hosts
                hosts = vs.get("spec", {}).get("hosts", [])
                if name in hosts or f"{name}.{namespace}.svc.cluster.local" in hosts:
                    return vs["metadata"]["name"]

        except Exception as e:
            logger.debug(f"Error getting virtual service for {name}: {e}")

        return None

    async def _get_destination_rule(self, name: str, namespace: str) -> Optional[str]:
        """Get destination rule name for a service"""
        try:
            dr_list = self.custom_api.list_namespaced_custom_object(
                group="networking.istio.io",
                version="v1beta1",
                namespace=namespace,
                plural="destinationrules",
            )

            for dr in dr_list.get("items", []):
                if dr["metadata"]["name"] == name:
                    return name

                # Check if service is the host
                host = dr.get("spec", {}).get("host", "")
                if host == name or host == f"{name}.{namespace}.svc.cluster.local":
                    return dr["metadata"]["name"]

        except Exception as e:
            logger.debug(f"Error getting destination rule for {name}: {e}")

        return None

    def _get_domain_from_namespace(self, namespace: str) -> str:
        """Get domain from namespace"""
        if namespace == "artemis-mesh":
            return "artemis"
        elif namespace == "sophia-mesh":
            return "sophia"
        elif namespace == "shared-services":
            return "shared"
        else:
            return "unknown"

    async def apply_mesh_config(self, config: dict[str, Any]):
        """
        Apply mesh configuration updates

        Args:
            config: Configuration to apply
        """
        try:
            # Apply VirtualService configurations
            if "virtualServices" in config:
                for vs_config in config["virtualServices"]:
                    await self._apply_virtual_service(vs_config)

            # Apply DestinationRule configurations
            if "destinationRules" in config:
                for dr_config in config["destinationRules"]:
                    await self._apply_destination_rule(dr_config)

            # Apply ServiceEntry configurations
            if "serviceEntries" in config:
                for se_config in config["serviceEntries"]:
                    await self._apply_service_entry(se_config)

            logger.info("Applied mesh configuration updates")

        except Exception as e:
            logger.error(f"Failed to apply mesh configuration: {e}")
            raise

    async def _apply_virtual_service(self, config: dict[str, Any]):
        """Apply VirtualService configuration"""
        try:
            namespace = config.get("namespace", "default")
            name = config["name"]

            # Check if exists
            try:
                existing = self.custom_api.get_namespaced_custom_object(
                    group="networking.istio.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="virtualservices",
                    name=name,
                )

                # Update existing
                existing["spec"] = config["spec"]
                self.custom_api.patch_namespaced_custom_object(
                    group="networking.istio.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="virtualservices",
                    name=name,
                    body=existing,
                )
                logger.info(f"Updated VirtualService {namespace}/{name}")

            except ApiException as e:
                if e.status == 404:
                    # Create new
                    body = {
                        "apiVersion": "networking.istio.io/v1beta1",
                        "kind": "VirtualService",
                        "metadata": {"name": name, "namespace": namespace},
                        "spec": config["spec"],
                    }
                    self.custom_api.create_namespaced_custom_object(
                        group="networking.istio.io",
                        version="v1beta1",
                        namespace=namespace,
                        plural="virtualservices",
                        body=body,
                    )
                    logger.info(f"Created VirtualService {namespace}/{name}")
                else:
                    raise

        except Exception as e:
            logger.error(f"Failed to apply VirtualService: {e}")
            raise

    async def _apply_destination_rule(self, config: dict[str, Any]):
        """Apply DestinationRule configuration"""
        try:
            namespace = config.get("namespace", "default")
            name = config["name"]

            # Check if exists
            try:
                existing = self.custom_api.get_namespaced_custom_object(
                    group="networking.istio.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="destinationrules",
                    name=name,
                )

                # Update existing
                existing["spec"] = config["spec"]
                self.custom_api.patch_namespaced_custom_object(
                    group="networking.istio.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="destinationrules",
                    name=name,
                    body=existing,
                )
                logger.info(f"Updated DestinationRule {namespace}/{name}")

            except ApiException as e:
                if e.status == 404:
                    # Create new
                    body = {
                        "apiVersion": "networking.istio.io/v1beta1",
                        "kind": "DestinationRule",
                        "metadata": {"name": name, "namespace": namespace},
                        "spec": config["spec"],
                    }
                    self.custom_api.create_namespaced_custom_object(
                        group="networking.istio.io",
                        version="v1beta1",
                        namespace=namespace,
                        plural="destinationrules",
                        body=body,
                    )
                    logger.info(f"Created DestinationRule {namespace}/{name}")
                else:
                    raise

        except Exception as e:
            logger.error(f"Failed to apply DestinationRule: {e}")
            raise

    async def _apply_service_entry(self, config: dict[str, Any]):
        """Apply ServiceEntry configuration"""
        try:
            namespace = config.get("namespace", "default")
            name = config["name"]

            # Check if exists
            try:
                existing = self.custom_api.get_namespaced_custom_object(
                    group="networking.istio.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="serviceentries",
                    name=name,
                )

                # Update existing
                existing["spec"] = config["spec"]
                self.custom_api.patch_namespaced_custom_object(
                    group="networking.istio.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="serviceentries",
                    name=name,
                    body=existing,
                )
                logger.info(f"Updated ServiceEntry {namespace}/{name}")

            except ApiException as e:
                if e.status == 404:
                    # Create new
                    body = {
                        "apiVersion": "networking.istio.io/v1beta1",
                        "kind": "ServiceEntry",
                        "metadata": {"name": name, "namespace": namespace},
                        "spec": config["spec"],
                    }
                    self.custom_api.create_namespaced_custom_object(
                        group="networking.istio.io",
                        version="v1beta1",
                        namespace=namespace,
                        plural="serviceentries",
                        body=body,
                    )
                    logger.info(f"Created ServiceEntry {namespace}/{name}")
                else:
                    raise

        except Exception as e:
            logger.error(f"Failed to apply ServiceEntry: {e}")
            raise
