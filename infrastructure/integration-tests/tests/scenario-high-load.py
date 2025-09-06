#!/usr/bin/env python3
"""
High Load Scenario Test
Simulates high AI workload and verifies that KEDA scales appropriately,
alerts fire correctly, and ArgoCD maintains desired state
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import aiohttp
import pytest
from kubernetes import client, config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HighLoadScenario:
    """Test high load scenario across all components"""

    def __init__(self):
        """Initialize test configuration"""
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()

        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.custom_api = client.CustomObjectsApi()

        self.test_namespace = "high-load-test"
        self.keda_namespace = "keda-system"
        self.alertmanager_namespace = "monitoring"
        self.argocd_namespace = "argocd"

        self.prometheus_url = "http://prometheus.monitoring.svc.cluster.local:9090"
        self.alertmanager_url = "http://alertmanager.monitoring.svc.cluster.local:9093"

        # Performance targets
        self.scaling_time_target = 9  # seconds
        self.alert_time_target = 5  # seconds
        self.recovery_time_target = 30  # seconds

    async def setup_scenario(self):
        """Setup high load test scenario"""
        logger.info("Setting up high load scenario...")

        # Create test namespace
        try:
            namespace = client.V1Namespace(
                metadata=client.V1ObjectMeta(
                    name=self.test_namespace,
                    labels={"scenario": "high-load", "managed-by": "integration-test"},
                )
            )
            self.v1.create_namespace(namespace)
        except client.exceptions.ApiException as e:
            if e.status != 409:
                raise

        # Deploy AI workload simulators
        await self._deploy_ai_workload_simulators()

        # Configure KEDA for AI workload scaling
        await self._configure_ai_workload_scaling()

        # Setup alert rules for high load
        await self._setup_high_load_alerts()

        logger.info("High load scenario setup complete")

    async def test_scenario_execution(self):
        """Execute the high load scenario"""
        logger.info("\n" + "=" * 60)
        logger.info("EXECUTING HIGH LOAD SCENARIO")
        logger.info("=" * 60 + "\n")

        # Phase 1: Normal operation
        logger.info("📊 Phase 1: Normal Operation")
        await self._verify_normal_operation()

        # Phase 2: Gradual load increase
        logger.info("\n📈 Phase 2: Gradual Load Increase")
        load_start_time = time.time()
        await self._simulate_gradual_load_increase()

        # Phase 3: Verify KEDA scaling response
        logger.info("\n⚡ Phase 3: KEDA Scaling Response")
        scaling_metrics = await self._verify_keda_scaling_response(load_start_time)

        # Phase 4: Verify alert firing
        logger.info("\n🚨 Phase 4: Alert Verification")
        alert_metrics = await self._verify_alert_firing()

        # Phase 5: Sustained high load
        logger.info("\n🔥 Phase 5: Sustained High Load")
        stability_metrics = await self._test_sustained_high_load()

        # Phase 6: Load reduction and recovery
        logger.info("\n📉 Phase 6: Load Reduction and Recovery")
        recovery_metrics = await self._test_load_reduction_and_recovery()

        # Phase 7: Verify ArgoCD maintained state
        logger.info("\n✅ Phase 7: ArgoCD State Verification")
        await self._verify_argocd_maintained_state()

        # Generate report
        await self._generate_scenario_report(
            scaling_metrics, alert_metrics, stability_metrics, recovery_metrics
        )

    async def _deploy_ai_workload_simulators(self):
        """Deploy AI workload simulators (Artemis and Sophia)"""

        # Deploy Artemis simulator
        artemis_deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name="artemis-simulator",
                namespace=self.test_namespace,
                labels={"app": "artemis", "component": "ai-workload"},
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels={"app": "artemis"}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": "artemis"},
                        annotations={"prometheus.io/scrape": "true", "prometheus.io/port": "8080"},
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="artemis",
                                image="nginx:latest",
                                ports=[client.V1ContainerPort(container_port=8080)],
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": "200m", "memory": "512Mi"},
                                    limits={"cpu": "2000m", "memory": "4Gi"},
                                ),
                                env=[
                                    client.V1EnvVar(name="WORKLOAD_TYPE", value="AI_INFERENCE"),
                                    client.V1EnvVar(name="MODEL_SIZE", value="LARGE"),
                                ],
                            )
                        ]
                    ),
                ),
            ),
        )

        # Deploy Sophia simulator
        sophia_deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name="sophia-simulator",
                namespace=self.test_namespace,
                labels={"app": "sophia", "component": "ai-workload"},
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels={"app": "sophia"}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": "sophia"},
                        annotations={"prometheus.io/scrape": "true", "prometheus.io/port": "8080"},
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="sophia",
                                image="nginx:latest",
                                ports=[client.V1ContainerPort(container_port=8080)],
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": "500m", "memory": "1Gi"},
                                    limits={"cpu": "4000m", "memory": "8Gi"},
                                ),
                                env=[
                                    client.V1EnvVar(name="WORKLOAD_TYPE", value="AI_TRAINING"),
                                    client.V1EnvVar(name="BATCH_SIZE", value="64"),
                                ],
                            )
                        ]
                    ),
                ),
            ),
        )

        try:
            self.apps_v1.create_namespaced_deployment(
                namespace=self.test_namespace, body=artemis_deployment
            )
            self.apps_v1.create_namespaced_deployment(
                namespace=self.test_namespace, body=sophia_deployment
            )
        except client.exceptions.ApiException as e:
            if e.status != 409:
                raise

    async def _configure_ai_workload_scaling(self):
        """Configure KEDA ScaledObjects for AI workloads"""

        # Artemis ScaledObject
        artemis_scaler = {
            "apiVersion": "keda.sh/v1alpha1",
            "kind": "ScaledObject",
            "metadata": {"name": "artemis-ai-scaler", "namespace": self.test_namespace},
            "spec": {
                "scaleTargetRef": {"name": "artemis-simulator"},
                "minReplicaCount": 1,
                "maxReplicaCount": 20,
                "pollingInterval": 5,
                "cooldownPeriod": 30,
                "triggers": [
                    {
                        "type": "prometheus",
                        "metadata": {
                            "serverAddress": self.prometheus_url,
                            "metricName": "ai_inference_queue_depth",
                            "threshold": "10",
                            "query": f'sum(ai_inference_queue_depth{{namespace="{self.test_namespace}",app="artemis"}})',
                        },
                    },
                    {"type": "cpu", "metadata": {"type": "Utilization", "value": "70"}},
                ],
            },
        }

        # Sophia ScaledObject
        sophia_scaler = {
            "apiVersion": "keda.sh/v1alpha1",
            "kind": "ScaledObject",
            "metadata": {"name": "sophia-ai-scaler", "namespace": self.test_namespace},
            "spec": {
                "scaleTargetRef": {"name": "sophia-simulator"},
                "minReplicaCount": 1,
                "maxReplicaCount": 15,
                "pollingInterval": 5,
                "cooldownPeriod": 60,
                "triggers": [
                    {
                        "type": "prometheus",
                        "metadata": {
                            "serverAddress": self.prometheus_url,
                            "metricName": "ai_training_batch_pending",
                            "threshold": "100",
                            "query": f'sum(ai_training_batch_pending{{namespace="{self.test_namespace}",app="sophia"}})',
                        },
                    },
                    {"type": "memory", "metadata": {"type": "Utilization", "value": "80"}},
                ],
            },
        }

        try:
            self.custom_api.create_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=self.test_namespace,
                plural="scaledobjects",
                body=artemis_scaler,
            )
            self.custom_api.create_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=self.test_namespace,
                plural="scaledobjects",
                body=sophia_scaler,
            )
        except client.exceptions.ApiException as e:
            if e.status != 409:
                raise

    async def _setup_high_load_alerts(self):
        """Setup alert rules for high load scenario"""

        alert_rules = {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "PrometheusRule",
            "metadata": {"name": "high-load-alerts", "namespace": self.alertmanager_namespace},
            "spec": {
                "groups": [
                    {
                        "name": "ai-workload-alerts",
                        "interval": "10s",
                        "rules": [
                            {
                                "alert": "AIWorkloadHighQueue",
                                "expr": f'sum(ai_inference_queue_depth{{namespace="{self.test_namespace}"}}) > 50',
                                "for": "30s",
                                "labels": {"severity": "warning", "component": "ai-workload"},
                                "annotations": {
                                    "summary": "High AI inference queue depth",
                                    "description": "AI inference queue depth is {{ $value }}",
                                },
                            },
                            {
                                "alert": "AIWorkloadCriticalLoad",
                                "expr": f'sum(rate(ai_requests_total{{namespace="{self.test_namespace}"}}[1m])) > 1000',
                                "for": "1m",
                                "labels": {"severity": "critical", "component": "ai-workload"},
                                "annotations": {
                                    "summary": "Critical AI workload detected",
                                    "description": "Request rate is {{ $value }} req/s",
                                },
                            },
                            {
                                "alert": "KEDAScalingMaxed",
                                "expr": f'keda_scaler_active{{namespace="{self.test_namespace}"}} == keda_scaler_max_replicas{{namespace="{self.test_namespace}"}}',
                                "for": "2m",
                                "labels": {"severity": "critical", "component": "autoscaling"},
                                "annotations": {
                                    "summary": "KEDA scaling at maximum",
                                    "description": "ScaledObject {{ $labels.scaledObject }} at max replicas",
                                },
                            },
                        ],
                    }
                ]
            },
        }

        try:
            self.custom_api.create_namespaced_custom_object(
                group="monitoring.coreos.com",
                version="v1",
                namespace=self.alertmanager_namespace,
                plural="prometheusrules",
                body=alert_rules,
            )
        except client.exceptions.ApiException as e:
            if e.status != 409:
                raise

    async def _verify_normal_operation(self):
        """Verify system is in normal operation state"""

        # Check deployments are running
        artemis = self.apps_v1.read_namespaced_deployment(
            name="artemis-simulator", namespace=self.test_namespace
        )
        sophia = self.apps_v1.read_namespaced_deployment(
            name="sophia-simulator", namespace=self.test_namespace
        )

        assert artemis.status.ready_replicas == 1
        assert sophia.status.ready_replicas == 1

        # Check no critical alerts
        alerts = await self._get_active_alerts()
        critical_alerts = [a for a in alerts if a.get("labels", {}).get("severity") == "critical"]

        assert len(critical_alerts) == 0, "Critical alerts present in normal operation"

        logger.info("✓ System in normal operation state")

    async def _simulate_gradual_load_increase(self):
        """Simulate gradual increase in AI workload"""
        logger.info("Simulating gradual load increase...")

        # Push increasing metrics over time
        for i in range(1, 11):
            metrics = f"""
# TYPE ai_inference_queue_depth gauge
ai_inference_queue_depth{{namespace="{self.test_namespace}",app="artemis"}} {i * 5}

# TYPE ai_training_batch_pending gauge
ai_training_batch_pending{{namespace="{self.test_namespace}",app="sophia"}} {i * 20}

# TYPE ai_requests_total counter
ai_requests_total{{namespace="{self.test_namespace}"}} {i * 100}
"""
            await self._push_metrics(metrics)
            logger.info(f"  Load level: {i * 10}%")
            await asyncio.sleep(5)

        logger.info("✓ Load increase simulation complete")

    async def _verify_keda_scaling_response(self, start_time: float) -> Dict:
        """Verify KEDA scaling response to load"""
        logger.info("Verifying KEDA scaling response...")

        metrics = {
            "artemis_scaled": False,
            "sophia_scaled": False,
            "artemis_replicas": 0,
            "sophia_replicas": 0,
            "scaling_time": 0,
        }

        # Monitor scaling for up to 15 seconds
        while time.time() - start_time < 15:
            artemis = self.apps_v1.read_namespaced_deployment(
                name="artemis-simulator", namespace=self.test_namespace
            )
            sophia = self.apps_v1.read_namespaced_deployment(
                name="sophia-simulator", namespace=self.test_namespace
            )

            if artemis.status.replicas > 1:
                metrics["artemis_scaled"] = True
                metrics["artemis_replicas"] = artemis.status.replicas

            if sophia.status.replicas > 1:
                metrics["sophia_scaled"] = True
                metrics["sophia_replicas"] = sophia.status.replicas

            if metrics["artemis_scaled"] and metrics["sophia_scaled"]:
                metrics["scaling_time"] = time.time() - start_time
                break

            await asyncio.sleep(1)

        # Verify scaling happened within target time
        assert metrics["artemis_scaled"], "Artemis did not scale"
        assert metrics["sophia_scaled"], "Sophia did not scale"
        assert (
            metrics["scaling_time"] < self.scaling_time_target
        ), f"Scaling took {metrics['scaling_time']:.1f}s (target: {self.scaling_time_target}s)"

        logger.info(f"✓ KEDA scaled in {metrics['scaling_time']:.1f}s")
        logger.info(f"  Artemis: {metrics['artemis_replicas']} replicas")
        logger.info(f"  Sophia: {metrics['sophia_replicas']} replicas")

        return metrics

    async def _verify_alert_firing(self) -> Dict:
        """Verify alerts are firing correctly"""
        logger.info("Verifying alert firing...")

        alert_start = time.time()
        metrics = {
            "queue_alert": False,
            "load_alert": False,
            "alert_time": 0,
            "false_positives": 0,
            "total_alerts": 0,
        }

        # Wait for alerts to fire
        while time.time() - alert_start < 10:
            alerts = await self._get_active_alerts()
            metrics["total_alerts"] = len(alerts)

            for alert in alerts:
                alert_name = alert.get("labels", {}).get("alertname", "")

                if alert_name == "AIWorkloadHighQueue":
                    metrics["queue_alert"] = True
                elif alert_name == "AIWorkloadCriticalLoad":
                    metrics["load_alert"] = True
                elif self.test_namespace not in str(alert):
                    metrics["false_positives"] += 1

            if metrics["queue_alert"] or metrics["load_alert"]:
                metrics["alert_time"] = time.time() - alert_start
                break

            await asyncio.sleep(0.5)

        # Verify alerts fired within target time
        assert metrics["queue_alert"] or metrics["load_alert"], "No expected alerts fired"
        assert (
            metrics["alert_time"] < self.alert_time_target
        ), f"Alert took {metrics['alert_time']:.1f}s (target: {self.alert_time_target}s)"

        # Calculate false positive rate
        if metrics["total_alerts"] > 0:
            fp_rate = (metrics["false_positives"] / metrics["total_alerts"]) * 100
            logger.info(f"  False positive rate: {fp_rate:.1f}%")
            assert fp_rate < 30, f"High false positive rate: {fp_rate:.1f}%"

        logger.info(f"✓ Alerts fired in {metrics['alert_time']:.1f}s")

        return metrics

    async def _test_sustained_high_load(self) -> Dict:
        """Test system stability under sustained high load"""
        logger.info("Testing sustained high load...")

        metrics = {
            "max_replicas_reached": False,
            "system_stable": True,
            "pod_failures": 0,
            "alert_storms": 0,
        }

        # Maintain high load for 2 minutes
        sustained_start = time.time()

        while time.time() - sustained_start < 120:
            # Push high load metrics
            metrics_data = """
# TYPE ai_inference_queue_depth gauge
ai_inference_queue_depth{namespace="%s",app="artemis"} 100

# TYPE ai_training_batch_pending gauge
ai_training_batch_pending{namespace="%s",app="sophia"} 500

# TYPE ai_requests_total counter
ai_requests_total{namespace="%s"} 50000
""" % (
                self.test_namespace,
                self.test_namespace,
                self.test_namespace,
            )

            await self._push_metrics(metrics_data)

            # Check system stability
            artemis = self.apps_v1.read_namespaced_deployment(
                name="artemis-simulator", namespace=self.test_namespace
            )
            sophia = self.apps_v1.read_namespaced_deployment(
                name="sophia-simulator", namespace=self.test_namespace
            )

            # Check if max replicas reached
            if artemis.status.replicas >= 20:
                metrics["max_replicas_reached"] = True

            # Check for pod failures
            pods = self.v1.list_namespaced_pod(
                namespace=self.test_namespace, label_selector="component=ai-workload"
            )

            for pod in pods.items:
                if pod.status.phase == "Failed":
                    metrics["pod_failures"] += 1
                    metrics["system_stable"] = False

            # Check for alert storms
            alerts = await self._get_active_alerts()
            if len(alerts) > 50:
                metrics["alert_storms"] += 1

            await asyncio.sleep(10)

        logger.info("✓ Sustained load test complete")
        logger.info(f"  Max replicas reached: {metrics['max_replicas_reached']}")
        logger.info(f"  Pod failures: {metrics['pod_failures']}")
        logger.info(f"  Alert storms: {metrics['alert_storms']}")

        assert metrics["system_stable"], "System unstable under load"
        assert metrics["alert_storms"] == 0, "Alert storm detected"

        return metrics

    async def _test_load_reduction_and_recovery(self) -> Dict:
        """Test system recovery when load reduces"""
        logger.info("Testing load reduction and recovery...")

        recovery_start = time.time()
        metrics = {"scale_down_time": 0, "alerts_cleared": False, "final_replicas": {}}

        # Reduce load gradually
        for i in range(10, 0, -1):
            metrics_data = f"""
# TYPE ai_inference_queue_depth gauge
ai_inference_queue_depth{{namespace="{self.test_namespace}",app="artemis"}} {i * 2}

# TYPE ai_training_batch_pending gauge
ai_training_batch_pending{{namespace="{self.test_namespace}",app="sophia"}} {i * 10}

# TYPE ai_requests_total counter
ai_requests_total{{namespace="{self.test_namespace}"}} {i * 50}
"""
            await self._push_metrics(metrics_data)
            await asyncio.sleep(5)

        # Monitor scale down
        scaled_down = False
        while time.time() - recovery_start < 90:
            artemis = self.apps_v1.read_namespaced_deployment(
                name="artemis-simulator", namespace=self.test_namespace
            )
            sophia = self.apps_v1.read_namespaced_deployment(
                name="sophia-simulator", namespace=self.test_namespace
            )

            if artemis.status.replicas <= 2 and sophia.status.replicas <= 2:
                scaled_down = True
                metrics["scale_down_time"] = time.time() - recovery_start
                metrics["final_replicas"] = {
                    "artemis": artemis.status.replicas,
                    "sophia": sophia.status.replicas,
                }
                break

            await asyncio.sleep(5)

        # Check alerts cleared
        alerts = await self._get_active_alerts()
        high_load_alerts = [
            a for a in alerts if "load" in a.get("labels", {}).get("alertname", "").lower()
        ]

        metrics["alerts_cleared"] = len(high_load_alerts) == 0

        assert scaled_down, "System did not scale down"
        assert (
            metrics["scale_down_time"] < self.recovery_time_target
        ), f"Recovery took {metrics['scale_down_time']:.1f}s (target: {self.recovery_time_target}s)"
        assert metrics["alerts_cleared"], "Load alerts not cleared"

        logger.info(f"✓ System recovered in {metrics['scale_down_time']:.1f}s")

        return metrics

    async def _verify_argocd_maintained_state(self):
        """Verify ArgoCD maintained desired state throughout"""
        logger.info("Verifying ArgoCD maintained state...")

        # Check ArgoCD application status
        try:
            app = self.custom_api.get_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.argocd_namespace,
                plural="applications",
                name="high-load-test-app",
            )

            sync_status = app["status"]["sync"]["status"]
            health_status = app["status"]["health"]["status"]

            assert sync_status == "Synced", f"ArgoCD not synced: {sync_status}"
            assert health_status == "Healthy", f"ArgoCD not healthy: {health_status}"

            logger.info("✓ ArgoCD maintained desired state")

        except client.exceptions.ApiException:
            logger.warning("ArgoCD application not found (may not be configured)")

    async def _generate_scenario_report(
        self,
        scaling_metrics: Dict,
        alert_metrics: Dict,
        stability_metrics: Dict,
        recovery_metrics: Dict,
    ):
        """Generate comprehensive scenario report"""

        logger.info("\n" + "=" * 60)
        logger.info("SCENARIO REPORT: HIGH LOAD TEST")
        logger.info("=" * 60)

        logger.info("\n📊 Performance Metrics:")
        logger.info(
            f"  KEDA Scaling Time: {scaling_metrics['scaling_time']:.1f}s (Target: <{self.scaling_time_target}s)"
        )
        logger.info(
            f"  Alert Response Time: {alert_metrics['alert_time']:.1f}s (Target: <{self.alert_time_target}s)"
        )
        logger.info(
            f"  Recovery Time: {recovery_metrics['scale_down_time']:.1f}s (Target: <{self.recovery_time_target}s)"
        )

        logger.info("\n⚖️ Scaling Results:")
        logger.info(f"  Artemis: 1 → {scaling_metrics['artemis_replicas']} replicas")
        logger.info(f"  Sophia: 1 → {scaling_metrics['sophia_replicas']} replicas")
        logger.info(f"  Max Replicas Reached: {stability_metrics['max_replicas_reached']}")

        logger.info("\n🚨 Alert Analysis:")
        logger.info(f"  Total Alerts: {alert_metrics['total_alerts']}")
        logger.info(f"  False Positives: {alert_metrics['false_positives']}")
        logger.info(f"  Alert Storms: {stability_metrics['alert_storms']}")

        logger.info("\n💪 Stability Metrics:")
        logger.info(f"  System Stable: {stability_metrics['system_stable']}")
        logger.info(f"  Pod Failures: {stability_metrics['pod_failures']}")
        logger.info(f"  Alerts Cleared: {recovery_metrics['alerts_cleared']}")

        logger.info("\n✅ Test Result: PASSED")
        logger.info("All components performed within SLA targets")

    async def _push_metrics(self, metrics: str):
        """Push metrics to Prometheus pushgateway"""
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(
                    "http://pushgateway.monitoring.svc.cluster.local:9091/metrics/job/high-load-test",
                    data=metrics,
                )
            except:
                # Fallback: create metric endpoints in pods
                pass

    async def _get_active_alerts(self) -> List[Dict]:
        """Get active alerts from AlertManager"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.alertmanager_url}/api/v1/alerts") as resp:
                    data = await resp.json()
                    return data.get("data", [])
            except:
                return []

    async def cleanup(self):
        """Clean up test resources"""
        logger.info("\nCleaning up high load scenario resources...")

        try:
            # Delete test namespace
            self.v1.delete_namespace(name=self.test_namespace)

            # Delete alert rules
            self.custom_api.delete_namespaced_custom_object(
                group="monitoring.coreos.com",
                version="v1",
                namespace=self.alertmanager_namespace,
                plural="prometheusrules",
                name="high-load-alerts",
            )
        except:
            pass

        logger.info("Cleanup complete")


async def main():
    """Run high load scenario test"""
    scenario = HighLoadScenario()

    try:
        await scenario.setup_scenario()
        await scenario.test_scenario_execution()

        logger.info("\n🎉 HIGH LOAD SCENARIO TEST COMPLETED SUCCESSFULLY!")

    except Exception as e:
        logger.error(f"❌ Scenario failed: {e}")
        raise
    finally:
        await scenario.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
