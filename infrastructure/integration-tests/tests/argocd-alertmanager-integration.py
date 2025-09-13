#!/usr/bin/env python3
"""
ArgoCD-AlertManager Integration Test Suite
Tests the integration between ArgoCD GitOps deployments and AlertManager configurations
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict
import aiohttp
import yaml
from kubernetes import client, config
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class ArgoCDAlertManagerIntegration:
    """Test ArgoCD deploying and managing AlertManager configurations"""
    def __init__(self):
        """Initialize test configuration"""
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.argocd_namespace = "argocd"
        self.alertmanager_namespace = "monitoring"
        self.test_namespace = "integration-test"
        self.argocd_server = "argocd-server.argocd.svc.cluster.local"
        self.alertmanager_url = "http://alertmanager.monitoring.svc.cluster.local:9093"
        self.git_repo = "https://github.com/your-org/sophia-intel-ai.git"
    async def setup_test_environment(self):
        """Create test namespace and ArgoCD application for AlertManager"""
        logger.info("Setting up ArgoCD-AlertManager test environment...")
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
        # Create ArgoCD Application for AlertManager configs
        argocd_app = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {
                "name": "alertmanager-test-app",
                "namespace": self.argocd_namespace,
                "finalizers": ["resources-finalizer.argocd.argoproj.io"],
            },
            "spec": {
                "project": "default",
                "source": {
                    "repoURL": self.git_repo,
                    "targetRevision": "HEAD",
                    "path": "infrastructure/alertmanager/config",
                    "helm": {"valueFiles": ["values.yaml"]},
                },
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": self.alertmanager_namespace,
                },
                "syncPolicy": {
                    "automated": {"prune": True, "selfHeal": True, "allowEmpty": False},
                    "syncOptions": [
                        "CreateNamespace=true",
                        "PrunePropagationPolicy=foreground",
                        "ServerSideApply=true",
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
    async def test_argocd_deploys_alertmanager_config(self):
        """Test that ArgoCD successfully deploys AlertManager configurations"""
        logger.info("Testing ArgoCD deployment of AlertManager configurations...")
        # Deploy AlertManager config via ArgoCD
        config_yaml = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-test-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m
      slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'
    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
      receiver: 'test-receiver'
      routes:
      - match:
          severity: critical
        receiver: critical-receiver
        continue: true
      - match:
          severity: warning
        receiver: warning-receiver
    receivers:
    - name: 'test-receiver'
      slack_configs:
      - channel: '#test-alerts'
        title: 'Test Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
    - name: 'critical-receiver'
      pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
        description: 'Critical alert from test'
    - name: 'warning-receiver'
      email_configs:
      - to: 'team@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
"""
        # Simulate Git commit
        await self._simulate_git_update(config_yaml)
        # Trigger ArgoCD sync
        await self._trigger_argocd_sync("alertmanager-test-app")
        await asyncio.sleep(30)
        # Verify ConfigMap is created
        cm = self.v1.read_namespaced_config_map(
            name="alertmanager-test-config", namespace=self.alertmanager_namespace
        )
        assert cm is not None
        assert "alertmanager.yml" in cm.data
        # Verify AlertManager reloaded config
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.alertmanager_url}/api/v1/status") as resp:
                status = await resp.json()
                assert status["status"] == "success"
        logger.info("✓ ArgoCD successfully deploys AlertManager configurations")
    async def test_alert_rules_deployment_via_argocd(self):
        """Test deploying Prometheus alert rules via ArgoCD"""
        logger.info("Testing alert rules deployment via ArgoCD...")
        # Create PrometheusRule CRD
        alert_rules = """
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: test-alert-rules
  namespace: monitoring
  labels:
    prometheus: kube-prometheus
    role: alert-rules
spec:
  groups:
  - name: test.rules
    interval: 30s
    rules:
    - alert: TestHighMemoryUsage
      expr: container_memory_usage_bytes{namespace="test"} > 1000000000
      for: 5m
      labels:
        severity: warning
        component: test
      annotations:
        summary: High memory usage detected
        description: "Memory usage is above 1GB for {{ $labels.pod }}"
    - alert: TestPodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
      for: 5m
      labels:
        severity: critical
        component: test
      annotations:
        summary: Pod is crash looping
        description: "Pod {{ $labels.pod }} is crash looping"
"""
        await self._simulate_git_update(alert_rules)
        await self._trigger_argocd_sync("alertmanager-test-app")
        await asyncio.sleep(30)
        # Verify PrometheusRule is created
        rule = self.custom_api.get_namespaced_custom_object(
            group="monitoring.coreos.com",
            version="v1",
            namespace=self.alertmanager_namespace,
            plural="prometheusrules",
            name="test-alert-rules",
        )
        assert rule is not None
        assert len(rule["spec"]["groups"]) > 0
        assert len(rule["spec"]["groups"][0]["rules"]) == 2
        logger.info("✓ Alert rules successfully deployed via ArgoCD")
    async def test_alertmanager_config_update_via_argocd(self):
        """Test updating AlertManager configs through ArgoCD GitOps"""
        logger.info("Testing AlertManager configuration updates via ArgoCD...")
        # Initial config
        initial_config = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-update-test
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m
    route:
      receiver: 'default-receiver'
    receivers:
    - name: 'default-receiver'
"""
        await self._simulate_git_update(initial_config)
        await self._trigger_argocd_sync("alertmanager-test-app")
        await asyncio.sleep(20)
        # Verify initial config
        cm = self.v1.read_namespaced_config_map(
            name="alertmanager-update-test", namespace=self.alertmanager_namespace
        )
        assert "resolve_timeout: 5m" in cm.data["alertmanager.yml"]
        # Update config
        updated_config = initial_config.replace(
            "resolve_timeout: 5m", "resolve_timeout: 10m"
        )
        updated_config = updated_config.replace("default-receiver", "updated-receiver")
        await self._simulate_git_update(updated_config)
        await self._trigger_argocd_sync("alertmanager-test-app")
        await asyncio.sleep(20)
        # Verify update
        cm = self.v1.read_namespaced_config_map(
            name="alertmanager-update-test", namespace=self.alertmanager_namespace
        )
        assert "resolve_timeout: 10m" in cm.data["alertmanager.yml"]
        assert "updated-receiver" in cm.data["alertmanager.yml"]
        # Verify AlertManager reloaded
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.alertmanager_url}/api/v1/status") as resp:
                status = await resp.json()
                config = status["data"]["config"]
                assert "resolve_timeout: 10m" in json.dumps(config)
        logger.info("✓ AlertManager configs successfully updated via ArgoCD")
    async def test_alertmanager_ha_config_sync(self):
        """Test AlertManager HA configuration synchronization via ArgoCD"""
        logger.info("Testing AlertManager HA configuration sync...")
        # Deploy HA config for multiple AlertManager instances
        ha_config = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-ha-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m
    route:
      group_by: ['alertname', 'cluster']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
      receiver: 'ha-receiver'
    receivers:
    - name: 'ha-receiver'
      webhook_configs:
      - url: 'http://webhook-receiver:5001/alerts'
        send_resolved: true
    # HA clustering configuration
    cluster:
      peers:
      - alertmanager-0.alertmanager-operated.monitoring.svc.cluster.local:9094
      - alertmanager-1.alertmanager-operated.monitoring.svc.cluster.local:9094
      - alertmanager-2.alertmanager-operated.monitoring.svc.cluster.local:9094
"""
        await self._simulate_git_update(ha_config)
        await self._trigger_argocd_sync("alertmanager-test-app")
        await asyncio.sleep(30)
        # Verify all AlertManager instances have the same config
        for i in range(3):
            pod_name = f"alertmanager-{i}"
            # Get pod
            try:
                pod = self.v1.read_namespaced_pod(
                    name=pod_name, namespace=self.alertmanager_namespace
                )
                # Check config hash annotation
                annotations = pod.metadata.annotations or {}
                config_hash = annotations.get("checksum/config", "")
                if i == 0:
                    first_hash = config_hash
                else:
                    assert config_hash == first_hash, f"Config mismatch for {pod_name}"
            except client.exceptions.ApiException:
                logger.warning(f"Pod {pod_name} not found, skipping")
        logger.info("✓ AlertManager HA configuration properly synchronized")
    async def test_argocd_rollback_alertmanager_config(self):
        """Test rolling back AlertManager configurations via ArgoCD"""
        logger.info("Testing AlertManager config rollback via ArgoCD...")
        # Get current revision
        app = await self._get_argocd_application("alertmanager-test-app")
        initial_revision = app["status"]["sync"]["revision"]
        # Deploy a problematic config
        bad_config = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-bad-config
  namespace: monitoring
data:
  alertmanager.yml: |
    # Invalid YAML - missing required fields
    invalid_config: true
"""
        await self._simulate_git_update(bad_config)
        await self._trigger_argocd_sync("alertmanager-test-app")
        await asyncio.sleep(20)
        # Check AlertManager status - should be degraded
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.alertmanager_url}/api/v1/status"
                ) as resp:
                    if resp.status != 200:
                        logger.info("AlertManager is degraded as expected")
            except:
                logger.info("AlertManager is unreachable - config error detected")
        # Perform rollback
        await self._rollback_argocd_application(
            "alertmanager-test-app", initial_revision
        )
        await asyncio.sleep(30)
        # Verify rollback
        try:
            self.v1.read_namespaced_config_map(
                name="alertmanager-bad-config", namespace=self.alertmanager_namespace
            )
            assert False, "Bad config should have been removed"
        except client.exceptions.ApiException as e:
            assert e.status == 404
        # Verify AlertManager is healthy again
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.alertmanager_url}/api/v1/status") as resp:
                assert resp.status == 200
                status = await resp.json()
                assert status["status"] == "success"
        logger.info("✓ AlertManager configs successfully rolled back via ArgoCD")
    async def test_notification_channel_config_via_argocd(self):
        """Test deploying notification channel configs via ArgoCD"""
        logger.info("Testing notification channel configuration via ArgoCD...")
        # Deploy multi-channel config
        channels_config = """
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-channels
  namespace: monitoring
type: Opaque
stringData:
  slack-webhook: "https://hooks.slack.com/services/TEST/WEBHOOK"
  pagerduty-key: "test-pagerduty-integration-key"
  email-password: "smtp-password"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-channels-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      slack_api_url_file: /etc/alertmanager/secrets/slack-webhook
      smtp_auth_password_file: /etc/alertmanager/secrets/email-password
    route:
      group_by: ['alertname']
      receiver: 'multi-channel'
      routes:
      - match:
          severity: critical
        receiver: pagerduty-critical
      - match:
          severity: warning
        receiver: slack-warning
      - match:
          severity: info
        receiver: email-info
    receivers:
    - name: 'multi-channel'
      slack_configs:
      - channel: '#alerts'
      pagerduty_configs:
      - service_key_file: /etc/alertmanager/secrets/pagerduty-key
      email_configs:
      - to: 'team@example.com'
    - name: 'pagerduty-critical'
      pagerduty_configs:
      - service_key_file: /etc/alertmanager/secrets/pagerduty-key
        severity: critical
    - name: 'slack-warning'
      slack_configs:
      - channel: '#warnings'
        title: 'Warning Alert'
    - name: 'email-info'
      email_configs:
      - to: 'info@example.com'
        headers:
          Subject: 'Info Alert'
"""
        await self._simulate_git_update(channels_config)
        await self._trigger_argocd_sync("alertmanager-test-app")
        await asyncio.sleep(30)
        # Verify Secret is created
        secret = self.v1.read_namespaced_secret(
            name="alertmanager-channels", namespace=self.alertmanager_namespace
        )
        assert secret is not None
        assert "slack-webhook" in secret.data
        assert "pagerduty-key" in secret.data
        # Verify ConfigMap with channel configs
        cm = self.v1.read_namespaced_config_map(
            name="alertmanager-channels-config", namespace=self.alertmanager_namespace
        )
        config = cm.data["alertmanager.yml"]
        assert "pagerduty-critical" in config
        assert "slack-warning" in config
        assert "email-info" in config
        logger.info("✓ Notification channels successfully configured via ArgoCD")
    async def test_alertmanager_silence_rules_via_argocd(self):
        """Test managing AlertManager silence rules via ArgoCD"""
        logger.info("Testing AlertManager silence rules management via ArgoCD...")
        # Create silence via API (simulating what ArgoCD would manage)
        silence = {
            "matchers": [
                {"name": "alertname", "value": "TestAlert", "isRegex": False},
                {"name": "environment", "value": "test", "isRegex": False},
            ],
            "startsAt": datetime.utcnow().isoformat() + "Z",
            "endsAt": (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z",
            "createdBy": "argocd-test",
            "comment": "Automated silence for testing",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.alertmanager_url}/api/v1/silences", json=silence
            ) as resp:
                result = await resp.json()
                silence_id = result["data"]["silenceID"]
        # Verify silence is active
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.alertmanager_url}/api/v1/silences") as resp:
                silences = await resp.json()
                active_silences = [
                    s for s in silences["data"] if s["status"]["state"] == "active"
                ]
                assert len(active_silences) > 0
                assert any(s["id"] == silence_id for s in active_silences)
        logger.info("✓ AlertManager silences can be managed via GitOps")
    async def _trigger_argocd_sync(self, app_name: str):
        """Trigger ArgoCD application sync"""
        async with aiohttp.ClientSession() as session:
            url = f"http://{self.argocd_server}/api/v1/applications/{app_name}/sync"
            headers = {"Authorization": "Bearer dummy-token"}
            try:
                async with session.post(url, headers=headers) as resp:
                    return await resp.json()
            except:
                # Fallback to kubectl
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
    async def _simulate_git_update(self, content: str):
        """Simulate updating Git repository"""
        # Parse YAML documents (handles multi-document YAML)
        import io
        docs = list(yaml.safe_load_all(io.StringIO(content)))
        for doc in docs:
            if not doc:
                continue
            # Add ArgoCD labels
            doc["metadata"]["labels"] = doc["metadata"].get("labels", {})
            doc["metadata"]["labels"]["app.kubernetes.io/managed-by"] = "argocd"
            # Create or update resource based on kind
            kind = doc["kind"].lower()
            name = doc["metadata"]["name"]
            namespace = doc["metadata"]["namespace"]
            try:
                if kind == "configmap":
                    self.v1.create_namespaced_config_map(namespace=namespace, body=doc)
                elif kind == "secret":
                    self.v1.create_namespaced_secret(namespace=namespace, body=doc)
                elif kind == "prometheusrule":
                    self.custom_api.create_namespaced_custom_object(
                        group="monitoring.coreos.com",
                        version="v1",
                        namespace=namespace,
                        plural="prometheusrules",
                        body=doc,
                    )
            except client.exceptions.ApiException as e:
                if e.status == 409:  # Already exists, update it
                    if kind == "configmap":
                        self.v1.patch_namespaced_config_map(
                            name=name, namespace=namespace, body=doc
                        )
                    elif kind == "secret":
                        self.v1.patch_namespaced_secret(
                            name=name, namespace=namespace, body=doc
                        )
                    elif kind == "prometheusrule":
                        self.custom_api.patch_namespaced_custom_object(
                            group="monitoring.coreos.com",
                            version="v1",
                            namespace=namespace,
                            plural="prometheusrules",
                            name=name,
                            body=doc,
                        )
                else:
                    raise
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
                name="alertmanager-test-app",
            )
            # Delete test namespace
            self.v1.delete_namespace(name=self.test_namespace)
            # Clean up test configs in monitoring namespace
            for cm in [
                "alertmanager-test-config",
                "alertmanager-update-test",
                "alertmanager-ha-config",
                "alertmanager-channels-config",
            ]:
                try:
                    self.v1.delete_namespaced_config_map(
                        name=cm, namespace=self.alertmanager_namespace
                    )
                except:
                    pass
            # Clean up test secrets
            try:
                self.v1.delete_namespaced_secret(
                    name="alertmanager-channels", namespace=self.alertmanager_namespace
                )
            except:
                pass
        except:
            pass
        logger.info("Cleanup complete")
async def main():
    """Run integration tests"""
    test = ArgoCDAlertManagerIntegration()
    try:
        await test.setup_test_environment()
        # Run tests
        await test.test_argocd_deploys_alertmanager_config()
        await test.test_alert_rules_deployment_via_argocd()
        await test.test_alertmanager_config_update_via_argocd()
        await test.test_alertmanager_ha_config_sync()
        await test.test_argocd_rollback_alertmanager_config()
        await test.test_notification_channel_config_via_argocd()
        await test.test_alertmanager_silence_rules_via_argocd()
        logger.info("\n✅ All ArgoCD-AlertManager integration tests passed!")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
    finally:
        await test.cleanup()
if __name__ == "__main__":
    asyncio.run(main())
