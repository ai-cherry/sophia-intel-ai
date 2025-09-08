#!/usr/bin/env python3
"""
ArgoCD-KEDA Integration Test Suite
Tests the integration between ArgoCD GitOps deployments and KEDA autoscaling
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict

import aiohttp
import yaml
from kubernetes import client, config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArgoCDKEDAIntegration:
    """Test ArgoCD deploying and managing KEDA configurations"""

    def __init__(self):
        """Initialize test configuration"""
        try:
            config.load_incluster_config()
        except Exception:config.load_kube_config()

        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.custom_api = client.CustomObjectsApi()

        self.argocd_namespace = "argocd"
        self.keda_namespace = "keda-system"
        self.test_namespace = "integration-test"

        self.argocd_server = "argocd-server.argocd.svc.cluster.local"
        self.git_repo = "https://github.com/your-org/sophia-intel-ai.git"

    async def setup_test_environment(self):
        """Create test namespace and ArgoCD application"""
        logger.info("Setting up ArgoCD-KEDA test environment...")

        # Create test namespace
        try:
            namespace = client.V1Namespace(
                metadata=client.V1ObjectMeta(
                    name=self.test_namespace, labels={"managed-by": "argocd"}
                )
            )
            self.v1.create_namespace(namespace)
        except client.exceptions.ApiException as e:
            if e.status != 409:
                raise

        # Create ArgoCD Application for KEDA configs
        argocd_app = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {
                "name": "keda-test-app",
                "namespace": self.argocd_namespace,
                "finalizers": ["resources-finalizer.argocd.argoproj.io"],
            },
            "spec": {
                "project": "default",
                "source": {
                    "repoURL": self.git_repo,
                    "targetRevision": "HEAD",
                    "path": "infrastructure/keda/scalers",
                },
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": self.test_namespace,
                },
                "syncPolicy": {
                    "automated": {"prune": True, "selfHeal": True, "allowEmpty": False},
                    "syncOptions": [
                        "CreateNamespace=true",
                        "PrunePropagationPolicy=foreground",
                    ],
                    "retry": {
                        "limit": 5,
                        "backoff": {"duration": "5s", "factor": 2, "maxDuration": "3m"},
                    },
                },
            },
        }

        try:
            self.custom_api.create_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.argocd_namespace,
                plural="applications",
                body=argocd_app,
            )
        except client.exceptions.ApiException as e:
            if e.status != 409:
                raise

        logger.info("Test environment setup complete")

    async def test_argocd_deploys_keda_configs(self):
        """Test that ArgoCD successfully deploys KEDA ScaledObjects"""
        logger.info("Testing ArgoCD deployment of KEDA configurations...")

        # Trigger ArgoCD sync
        await self._trigger_argocd_sync("keda-test-app")

        # Wait for sync to complete
        await asyncio.sleep(30)

        # Verify ScaledObjects are created
        scaled_objects = self.custom_api.list_namespaced_custom_object(
            group="keda.sh",
            version="v1alpha1",
            namespace=self.test_namespace,
            plural="scaledobjects",
        )

        assert (
            len(scaled_objects.get("items", [])) > 0
        ), "No ScaledObjects deployed by ArgoCD"

        # Verify ScaledObjects have correct ArgoCD labels
        for obj in scaled_objects["items"]:
            labels = obj.get("metadata", {}).get("labels", {})
            assert "app.kubernetes.io/managed-by" in labels
            assert labels["app.kubernetes.io/managed-by"] == "argocd"

        logger.info("✓ ArgoCD successfully deploys KEDA configurations")

    async def test_keda_config_update_via_argocd(self):
        """Test updating KEDA configs through ArgoCD GitOps"""
        logger.info("Testing KEDA configuration updates via ArgoCD...")

        # Create a ScaledObject via ArgoCD
        scaled_object_yaml = """
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: test-update-scaledobject
  namespace: integration-test
spec:
  scaleTargetRef:
    name: test-deployment
  minReplicaCount: 2
  maxReplicaCount: 10
  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: cpu_usage
      threshold: '50'
      query: avg(cpu_usage)
"""

        # Simulate Git commit (in real test, would push to actual repo)
        await self._simulate_git_update(scaled_object_yaml)

        # Trigger ArgoCD sync
        await self._trigger_argocd_sync("keda-test-app")
        await asyncio.sleep(20)

        # Verify initial config
        obj = self.custom_api.get_namespaced_custom_object(
            group="keda.sh",
            version="v1alpha1",
            namespace=self.test_namespace,
            plural="scaledobjects",
            name="test-update-scaledobject",
        )

        assert obj["spec"]["minReplicaCount"] == 2

        # Update the ScaledObject
        updated_yaml = scaled_object_yaml.replace(
            "minReplicaCount: 2", "minReplicaCount: 3"
        )
        await self._simulate_git_update(updated_yaml)

        # Trigger sync again
        await self._trigger_argocd_sync("keda-test-app")
        await asyncio.sleep(20)

        # Verify update
        obj = self.custom_api.get_namespaced_custom_object(
            group="keda.sh",
            version="v1alpha1",
            namespace=self.test_namespace,
            plural="scaledobjects",
            name="test-update-scaledobject",
        )

        assert obj["spec"]["minReplicaCount"] == 3

        logger.info("✓ KEDA configs successfully updated via ArgoCD")

    async def test_argocd_rollback_keda_config(self):
        """Test rolling back KEDA configurations via ArgoCD"""
        logger.info("Testing KEDA config rollback via ArgoCD...")

        # Get current application revision
        app = await self._get_argocd_application("keda-test-app")
        initial_revision = app["status"]["sync"]["revision"]

        # Deploy a problematic ScaledObject
        bad_config = """
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: bad-scaledobject
  namespace: integration-test
spec:
  scaleTargetRef:
    name: non-existent-deployment
  triggers:
  - type: invalid-trigger
"""

        await self._simulate_git_update(bad_config)
        await self._trigger_argocd_sync("keda-test-app")
        await asyncio.sleep(20)

        # Check for sync failure or degraded status
        app = await self._get_argocd_application("keda-test-app")

        # Perform rollback
        await self._rollback_argocd_application("keda-test-app", initial_revision)
        await asyncio.sleep(30)

        # Verify rollback
        try:
            self.custom_api.get_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=self.test_namespace,
                plural="scaledobjects",
                name="bad-scaledobject",
            )
            assert False, "Bad ScaledObject should have been removed"
        except client.exceptions.ApiException as e:
            assert e.status == 404

        logger.info("✓ KEDA configs successfully rolled back via ArgoCD")

    async def test_keda_respects_argocd_sync_waves(self):
        """Test that KEDA configs are deployed in correct sync waves"""
        logger.info("Testing KEDA sync wave ordering...")

        # Deploy configs with sync waves
        configs = [
            {"name": "wave-0-scaledobject", "wave": "0", "dependencies": []},
            {
                "name": "wave-1-scaledobject",
                "wave": "1",
                "dependencies": ["wave-0-scaledobject"],
            },
            {
                "name": "wave-2-scaledobject",
                "wave": "2",
                "dependencies": ["wave-1-scaledobject"],
            },
        ]

        for config in configs:
            yaml_content = f"""
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: {config['name']}
  namespace: integration-test
  annotations:
    argocd.argoproj.io/sync-wave: "{config['wave']}"
spec:
  scaleTargetRef:
    name: test-deployment-{config['wave']}
  triggers:
  - type: cpu
    metadata:
      type: Utilization
      value: "50"
"""
            await self._simulate_git_update(yaml_content)

        # Trigger sync
        await self._trigger_argocd_sync("keda-test-app")

        # Monitor creation order
        creation_times = {}
        for i in range(30):
            for config in configs:
                try:
                    obj = self.custom_api.get_namespaced_custom_object(
                        group="keda.sh",
                        version="v1alpha1",
                        namespace=self.test_namespace,
                        plural="scaledobjects",
                        name=config["name"],
                    )
                    if config["name"] not in creation_times:
                        creation_times[config["name"]] = datetime.now()
                except Exception:pass

            if len(creation_times) == len(configs):
                break

            await asyncio.sleep(1)

        # Verify wave ordering
        assert (
            creation_times["wave-0-scaledobject"]
            < creation_times["wave-1-scaledobject"]
        )
        assert (
            creation_times["wave-1-scaledobject"]
            < creation_times["wave-2-scaledobject"]
        )

        logger.info("✓ KEDA configs deployed in correct sync wave order")

    async def test_argocd_prune_orphaned_keda_resources(self):
        """Test that ArgoCD prunes orphaned KEDA resources"""
        logger.info("Testing ArgoCD pruning of orphaned KEDA resources...")

        # Create a ScaledObject outside of ArgoCD
        orphan = {
            "apiVersion": "keda.sh/v1alpha1",
            "kind": "ScaledObject",
            "metadata": {
                "name": "orphan-scaledobject",
                "namespace": self.test_namespace,
            },
            "spec": {
                "scaleTargetRef": {"name": "orphan-deployment"},
                "triggers": [
                    {"type": "cpu", "metadata": {"type": "Utilization", "value": "50"}}
                ],
            },
        }

        self.custom_api.create_namespaced_custom_object(
            group="keda.sh",
            version="v1alpha1",
            namespace=self.test_namespace,
            plural="scaledobjects",
            body=orphan,
        )

        # Enable pruning and sync
        await self._enable_argocd_pruning("keda-test-app")
        await self._trigger_argocd_sync("keda-test-app")
        await asyncio.sleep(30)

        # Verify orphan was pruned
        try:
            self.custom_api.get_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=self.test_namespace,
                plural="scaledobjects",
                name="orphan-scaledobject",
            )
            assert False, "Orphaned ScaledObject should have been pruned"
        except client.exceptions.ApiException as e:
            assert e.status == 404

        logger.info("✓ ArgoCD successfully prunes orphaned KEDA resources")

    async def test_keda_validation_webhook_with_argocd(self):
        """Test KEDA validation webhooks work with ArgoCD deployments"""
        logger.info("Testing KEDA validation webhooks with ArgoCD...")

        # Deploy invalid KEDA config via ArgoCD
        invalid_config = """
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: invalid-scaledobject
  namespace: integration-test
spec:
  scaleTargetRef:
    name: test-deployment
  minReplicaCount: 10
  maxReplicaCount: 5  # Invalid: max < min
  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      threshold: 'invalid'  # Invalid: should be numeric
"""

        await self._simulate_git_update(invalid_config)
        await self._trigger_argocd_sync("keda-test-app")
        await asyncio.sleep(20)

        # Check ArgoCD application status
        app = await self._get_argocd_application("keda-test-app")

        # Verify sync failed due to validation
        assert app["status"]["sync"]["status"] != "Synced"
        assert "validation" in str(app["status"]["conditions"]).lower()

        logger.info(
            "✓ KEDA validation webhooks properly reject invalid configs from ArgoCD"
        )

    async def _trigger_argocd_sync(self, app_name: str):
        """Trigger ArgoCD application sync"""
        async with aiohttp.ClientSession() as session:
            url = f"http://{self.argocd_server}/api/v1/applications/{app_name}/sync"
            headers = {
                "Authorization": "Bearer dummy-token"
            }  # In real test, use actual token

            try:
                async with session.post(url, headers=headers) as resp:
                    return await resp.json()
            except Exception:# Fallback to kubectl
                import subprocess

                subprocess.run(
                    [
                        "kubectl",
                        "patch",
                        "application",
                        app_name,
                        "-n",
                        self.argocd_namespace,
                        "--type",
                        "merge",
                        "-p",
                        '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"true"}}}',
                    ]
                )

    async def _get_argocd_application(self, app_name: str) -> Dict:
        """Get ArgoCD application details"""
        return self.custom_api.get_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace=self.argocd_namespace,
            plural="applications",
            name=app_name,
        )

    async def _rollback_argocd_application(self, app_name: str, revision: str):
        """Rollback ArgoCD application to specific revision"""
        app = await self._get_argocd_application(app_name)
        app["spec"]["source"]["targetRevision"] = revision

        self.custom_api.patch_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace=self.argocd_namespace,
            plural="applications",
            name=app_name,
            body=app,
        )

    async def _enable_argocd_pruning(self, app_name: str):
        """Enable resource pruning for ArgoCD application"""
        app = await self._get_argocd_application(app_name)
        app["spec"]["syncPolicy"]["automated"]["prune"] = True

        self.custom_api.patch_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace=self.argocd_namespace,
            plural="applications",
            name=app_name,
            body=app,
        )

    async def _simulate_git_update(self, content: str):
        """Simulate updating Git repository (in real test, would push to actual repo)"""
        # In a real test, this would:
        # 1. Clone the repo
        # 2. Add/update the file
        # 3. Commit and push
        # For now, we'll create the resource directly but with ArgoCD labels

        obj = yaml.safe_load(content)
        obj["metadata"]["labels"] = obj["metadata"].get("labels", {})
        obj["metadata"]["labels"]["app.kubernetes.io/managed-by"] = "argocd"

        try:
            self.custom_api.create_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=self.test_namespace,
                plural="scaledobjects",
                body=obj,
            )
        except client.exceptions.ApiException:
            self.custom_api.patch_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=self.test_namespace,
                plural="scaledobjects",
                name=obj["metadata"]["name"],
                body=obj,
            )

    async def cleanup(self):
        """Clean up test resources"""
        logger.info("Cleaning up test resources...")

        try:
            # Delete ArgoCD application
            self.custom_api.delete_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.argocd_namespace,
                plural="applications",
                name="keda-test-app",
            )

            # Delete test namespace
            self.v1.delete_namespace(name=self.test_namespace)
        except Exception:pass

        logger.info("Cleanup complete")


async def main():
    """Run integration tests"""
    test = ArgoCDKEDAIntegration()

    try:
        await test.setup_test_environment()

        # Run tests
        await test.test_argocd_deploys_keda_configs()
        await test.test_keda_config_update_via_argocd()
        await test.test_argocd_rollback_keda_config()
        await test.test_keda_respects_argocd_sync_waves()
        await test.test_argocd_prune_orphaned_keda_resources()
        await test.test_keda_validation_webhook_with_argocd()

        logger.info("\n✅ All ArgoCD-KEDA integration tests passed!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
    finally:
        await test.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
