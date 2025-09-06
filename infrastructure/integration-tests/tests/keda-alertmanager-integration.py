#!/usr/bin/env python3
"""
KEDA-AlertManager Integration Test Suite
Tests the integration between KEDA autoscaling and AlertManager alerting
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import pytest
from kubernetes import client, config
from prometheus_client.parser import text_string_to_metric_families

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KEDAAlertManagerIntegration:
    """Test KEDA scaling events triggering appropriate AlertManager alerts"""

    def __init__(self):
        """Initialize test configuration"""
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()

        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.custom_api = client.CustomObjectsApi()

        self.keda_namespace = "keda-system"
        self.alertmanager_namespace = "monitoring"
        self.test_namespace = "integration-test"

        self.alertmanager_url = "http://alertmanager.monitoring.svc.cluster.local:9093"
        self.prometheus_url = "http://prometheus.monitoring.svc.cluster.local:9090"

    async def setup_test_environment(self):
        """Create test namespace and deploy test workload"""
        logger.info("Setting up test environment...")

        # Create test namespace
        try:
            namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=self.test_namespace))
            self.v1.create_namespace(namespace)
        except client.exceptions.ApiException as e:
            if e.status != 409:  # Ignore if already exists
                raise

        # Deploy test workload
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name="test-workload", namespace=self.test_namespace),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels={"app": "test-workload"}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": "test-workload"}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="app",
                                image="nginx:latest",
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": "100m", "memory": "128Mi"},
                                    limits={"cpu": "500m", "memory": "512Mi"},
                                ),
                            )
                        ]
                    ),
                ),
            ),
        )

        try:
            self.apps_v1.create_namespaced_deployment(
                namespace=self.test_namespace, body=deployment
            )
        except client.exceptions.ApiException as e:
            if e.status != 409:
                raise

        # Create ScaledObject
        scaled_object = {
            "apiVersion": "keda.sh/v1alpha1",
            "kind": "ScaledObject",
            "metadata": {"name": "test-scaledobject", "namespace": self.test_namespace},
            "spec": {
                "scaleTargetRef": {"name": "test-workload"},
                "minReplicaCount": 1,
                "maxReplicaCount": 10,
                "triggers": [
                    {
                        "type": "prometheus",
                        "metadata": {
                            "serverAddress": self.prometheus_url,
                            "metricName": "test_workload_queue_length",
                            "threshold": "10",
                            "query": "sum(rate(test_workload_requests_total[1m]))",
                        },
                    }
                ],
            },
        }

        try:
            self.custom_api.create_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=self.test_namespace,
                plural="scaledobjects",
                body=scaled_object,
            )
        except client.exceptions.ApiException as e:
            if e.status != 409:
                raise

        logger.info("Test environment setup complete")

    async def test_scaling_alert_integration(self):
        """Test that KEDA scaling events trigger appropriate alerts"""
        logger.info("Testing KEDA scaling alert integration...")

        # Generate load to trigger scaling
        await self._generate_load()

        # Wait for KEDA to scale
        await asyncio.sleep(15)

        # Check if scaling occurred
        deployment = self.apps_v1.read_namespaced_deployment(
            name="test-workload", namespace=self.test_namespace
        )

        scaled_replicas = deployment.status.replicas
        logger.info(f"Deployment scaled to {scaled_replicas} replicas")

        # Verify AlertManager received scaling alert
        alerts = await self._get_active_alerts()

        scaling_alerts = [
            alert
            for alert in alerts
            if alert.get("labels", {}).get("alertname") == "KEDAScalingActive"
        ]

        assert len(scaling_alerts) > 0, "No KEDA scaling alerts found in AlertManager"

        # Verify alert contains correct metadata
        alert = scaling_alerts[0]
        assert alert["labels"]["namespace"] == self.test_namespace
        assert alert["labels"]["scaledobject"] == "test-scaledobject"
        assert "scaledReplicas" in alert["annotations"]

        logger.info("✓ KEDA scaling alerts properly integrated with AlertManager")

    async def test_scaling_failure_alert(self):
        """Test that KEDA scaling failures trigger critical alerts"""
        logger.info("Testing KEDA scaling failure alerts...")

        # Create invalid ScaledObject to trigger failure
        invalid_scaled_object = {
            "apiVersion": "keda.sh/v1alpha1",
            "kind": "ScaledObject",
            "metadata": {"name": "invalid-scaledobject", "namespace": self.test_namespace},
            "spec": {
                "scaleTargetRef": {"name": "non-existent-deployment"},
                "triggers": [
                    {
                        "type": "prometheus",
                        "metadata": {
                            "serverAddress": "http://invalid-prometheus:9090",
                            "metricName": "invalid_metric",
                            "threshold": "10",
                            "query": "invalid_query",
                        },
                    }
                ],
            },
        }

        try:
            self.custom_api.create_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=self.test_namespace,
                plural="scaledobjects",
                body=invalid_scaled_object,
            )
        except:
            pass

        # Wait for error to be detected
        await asyncio.sleep(30)

        # Check for failure alerts
        alerts = await self._get_active_alerts()

        failure_alerts = [
            alert
            for alert in alerts
            if alert.get("labels", {}).get("alertname") in ["KEDAScalerFailed", "KEDAScalingError"]
        ]

        assert len(failure_alerts) > 0, "No KEDA failure alerts found"

        # Verify alert severity
        alert = failure_alerts[0]
        assert alert["labels"]["severity"] in ["critical", "warning"]

        logger.info("✓ KEDA scaling failures properly trigger alerts")

    async def test_alert_deduplication(self):
        """Test that duplicate KEDA events don't create duplicate alerts"""
        logger.info("Testing alert deduplication...")

        # Trigger multiple scaling events rapidly
        for i in range(5):
            await self._generate_load()
            await asyncio.sleep(2)

        # Wait for alerts to be processed
        await asyncio.sleep(10)

        # Get active alerts
        alerts = await self._get_active_alerts()

        # Group alerts by fingerprint
        fingerprints = {}
        for alert in alerts:
            fp = alert.get("fingerprint", "")
            if fp:
                fingerprints[fp] = fingerprints.get(fp, 0) + 1

        # Verify no duplicates
        duplicates = [fp for fp, count in fingerprints.items() if count > 1]
        assert len(duplicates) == 0, f"Found duplicate alerts: {duplicates}"

        logger.info("✓ Alert deduplication working correctly")

    async def test_alert_grouping(self):
        """Test that related KEDA alerts are properly grouped"""
        logger.info("Testing alert grouping...")

        # Create multiple ScaledObjects
        for i in range(3):
            scaled_object = {
                "apiVersion": "keda.sh/v1alpha1",
                "kind": "ScaledObject",
                "metadata": {"name": f"test-scaledobject-{i}", "namespace": self.test_namespace},
                "spec": {
                    "scaleTargetRef": {"name": "test-workload"},
                    "triggers": [
                        {"type": "cpu", "metadata": {"type": "Utilization", "value": "50"}}
                    ],
                },
            }

            try:
                self.custom_api.create_namespaced_custom_object(
                    group="keda.sh",
                    version="v1alpha1",
                    namespace=self.test_namespace,
                    plural="scaledobjects",
                    body=scaled_object,
                )
            except:
                pass

        # Generate load to trigger alerts
        await self._generate_load()
        await asyncio.sleep(20)

        # Check alert groups
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.alertmanager_url}/api/v1/alerts/groups") as resp:
                groups = await resp.json()

        # Find KEDA alert group
        keda_groups = [
            group
            for group in groups.get("data", [])
            if any(
                "KEDA" in alert.get("labels", {}).get("alertname", "")
                for alert in group.get("alerts", [])
            )
        ]

        assert len(keda_groups) > 0, "No KEDA alert groups found"

        # Verify grouping logic
        group = keda_groups[0]
        assert len(group["alerts"]) > 1, "Alerts not properly grouped"

        logger.info("✓ Alert grouping configured correctly")

    async def test_metric_correlation(self):
        """Test correlation between KEDA metrics and alerts"""
        logger.info("Testing KEDA metrics and alert correlation...")

        # Get KEDA metrics
        async with aiohttp.ClientSession() as session:
            # Query KEDA scaler metrics
            query = 'keda_scaler_active{namespace="' + self.test_namespace + '"}'
            async with session.get(
                f"{self.prometheus_url}/api/v1/query", params={"query": query}
            ) as resp:
                metrics = await resp.json()

        # Get active alerts
        alerts = await self._get_active_alerts()

        # Correlate metrics with alerts
        active_scalers = len(metrics.get("data", {}).get("result", []))
        scaling_alerts = len(
            [a for a in alerts if "KEDA" in a.get("labels", {}).get("alertname", "")]
        )

        logger.info(f"Active scalers: {active_scalers}, Scaling alerts: {scaling_alerts}")

        # Verify correlation
        if active_scalers > 0:
            assert scaling_alerts > 0, "Active scalers but no alerts"

        logger.info("✓ Metrics and alerts properly correlated")

    async def _generate_load(self):
        """Generate load to trigger KEDA scaling"""
        # Simulate load by updating metrics
        async with aiohttp.ClientSession() as session:
            # Send synthetic metrics to Prometheus pushgateway if available
            try:
                metrics = """
                # TYPE test_workload_requests_total counter
                test_workload_requests_total{job="test"} 1000
                """
                await session.post(
                    "http://pushgateway.monitoring.svc.cluster.local:9091/metrics/job/test",
                    data=metrics,
                )
            except:
                logger.warning("Could not push metrics to pushgateway")

    async def _get_active_alerts(self) -> List[Dict]:
        """Get active alerts from AlertManager"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.alertmanager_url}/api/v1/alerts") as resp:
                data = await resp.json()
                return data.get("data", [])

    async def cleanup(self):
        """Clean up test resources"""
        logger.info("Cleaning up test resources...")

        try:
            # Delete ScaledObjects
            self.custom_api.delete_collection_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=self.test_namespace,
                plural="scaledobjects",
            )

            # Delete test namespace
            self.v1.delete_namespace(name=self.test_namespace)
        except:
            pass

        logger.info("Cleanup complete")


async def main():
    """Run integration tests"""
    test = KEDAAlertManagerIntegration()

    try:
        await test.setup_test_environment()

        # Run tests
        await test.test_scaling_alert_integration()
        await test.test_scaling_failure_alert()
        await test.test_alert_deduplication()
        await test.test_alert_grouping()
        await test.test_metric_correlation()

        logger.info("\n✅ All KEDA-AlertManager integration tests passed!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
    finally:
        await test.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
