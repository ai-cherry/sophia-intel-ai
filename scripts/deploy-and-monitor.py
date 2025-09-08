#!/usr/bin/env python3
"""
Complete Cloud Deployment and Monitoring Script for Sophia Intel AI
Deploys all 6 services to Fly.io and sets up real-time monitoring
"""

import json
import os
import subprocess
import time
from datetime import datetime
from typing import Any

import requests

from app.core.ai_logger import logger


class ProductionDeploymentManager:
    """Manages production deployment and monitoring"""

    def __init__(self):
        self.fly_api_token = os.environ.get("FLY_API_TOKEN")
        if not self.fly_api_token:
            raise ValueError("FLY_API_TOKEN environment variable is required")

        os.environ["FLY_API_TOKEN"] = self.fly_api_token

        self.services = [
            {"name": "sophia-weaviate", "config": "fly-weaviate.toml", "priority": 1},
            {"name": "sophia-mcp", "config": "fly-mcp-server.toml", "priority": 2},
            {"name": "sophia-vector", "config": "fly-vector-store.toml", "priority": 3},
            {"name": "sophia-api", "config": "fly-unified-api.toml", "priority": 4},
            {"name": "sophia-bridge", "config": "fly-agno-bridge.toml", "priority": 5},
            {"name": "sophia-ui", "config": "fly-agent-ui.toml", "priority": 6},
        ]

    def install_fly_cli(self) -> bool:
        """Install Fly CLI if not present"""
        try:
            result = subprocess.run(["fly", "version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Fly CLI already installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass

        logger.info("📥 Installing Fly CLI...")
        try:
            # Install Fly CLI for macOS
            install_cmd = ["curl", "-L", "https://fly.io/install.sh", "|", "sh"]
            result = subprocess.run(
                " ".join(install_cmd), shell=True, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("✅ Fly CLI installed successfully")
                return True
            else:
                logger.info(f"❌ Failed to install Fly CLI: {result.stderr}")
                return False
        except Exception as e:
            logger.info(f"❌ Fly CLI installation error: {e}")
            return False

    def authenticate_fly(self) -> bool:
        """Authenticate with Fly.io"""
        try:
            result = subprocess.run(
                ["fly", "auth", "token"], input=self.fly_api_token, text=True, capture_output=True
            )

            if result.returncode == 0:
                logger.info("✅ Fly.io authentication successful")
                return True
            else:
                logger.info(f"❌ Fly.io authentication failed: {result.stderr}")
                return False
        except Exception as e:
            logger.info(f"❌ Authentication error: {e}")
            return False

    def create_fly_app(self, app_name: str) -> bool:
        """Create Fly.io application if it doesn't exist"""
        try:
            # Check if app exists
            check_cmd = ["fly", "status", "--app", app_name]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)

            if check_result.returncode == 0:
                logger.info(f"📱 App {app_name} already exists")
                return True

            # Create new app
            create_cmd = ["fly", "apps", "create", app_name, "--org", "personal"]
            create_result = subprocess.run(create_cmd, capture_output=True, text=True)

            if create_result.returncode == 0:
                logger.info(f"✅ Created Fly.io app: {app_name}")
                return True
            else:
                logger.info(f"⚠️  App creation warning for {app_name}: {create_result.stderr}")
                return True  # Continue anyway, might be name conflict

        except Exception as e:
            logger.info(f"❌ App creation error for {app_name}: {e}")
            return False

    def deploy_service(self, service: dict[str, Any]) -> dict[str, Any]:
        """Deploy a single service and monitor health"""

        app_name = service["name"]
        config_file = service["config"]

        logger.info(f"\n🚀 Deploying {app_name}...")

        # 1. Create app if needed
        if not self.create_fly_app(app_name):
            return {"status": "failed", "error": "App creation failed"}

        # 2. Deploy the service
        try:
            deploy_cmd = [
                "fly",
                "deploy",
                "--config",
                config_file,
                "--app",
                app_name,
                "--remote-only",
                "--detach",
            ]

            deploy_result = subprocess.run(deploy_cmd, capture_output=True, text=True, timeout=600)

            if deploy_result.returncode == 0:
                logger.info(f"✅ Deployment initiated for {app_name}")

                # 3. Monitor deployment status
                deployment_status = self.monitor_deployment(app_name)
                return {
                    "status": "deployed",
                    "app_name": app_name,
                    "public_url": f"https://{app_name}.fly.dev",
                    "health_status": deployment_status,
                }
            else:
                logger.info(f"⚠️  Deployment issue for {app_name}: {deploy_result.stderr}")
                return {"status": "warning", "app_name": app_name, "error": deploy_result.stderr}

        except subprocess.TimeoutExpired:
            logger.info(f"⏱️  Deployment timeout for {app_name} (continuing in background)")
            return {
                "status": "deploying",
                "app_name": app_name,
                "note": "Background deployment in progress",
            }
        except Exception as e:
            logger.info(f"❌ Deployment error for {app_name}: {e}")
            return {"status": "failed", "error": str(e)}

    def monitor_deployment(self, app_name: str, max_wait: int = 300) -> dict[str, Any]:
        """Monitor deployment health and status"""

        logger.info(f"⏳ Monitoring deployment health for {app_name}...")
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                # Check app status
                status_cmd = ["fly", "status", "--app", app_name, "--json"]
                status_result = subprocess.run(status_cmd, capture_output=True, text=True)

                if status_result.returncode == 0:
                    status_data = json.loads(status_result.stdout)

                    # Check if any machines are running
                    allocations = status_data.get("Allocations", [])
                    if allocations:
                        running_count = sum(
                            1 for alloc in allocations if alloc.get("Status") == "running"
                        )
                        if running_count > 0:
                            logger.info(f"✅ {app_name} is running ({running_count} instances)")
                            return {
                                "status": "healthy",
                                "running_instances": running_count,
                                "total_allocations": len(allocations),
                            }

                logger.info(
                    f"⏳ Waiting for {app_name} to start... ({int(time.time() - start_time)}s)"
                )
                time.sleep(30)

            except Exception as e:
                logger.info(f"⚠️  Monitoring error for {app_name}: {e}")
                time.sleep(30)

        logger.info(f"⏱️  Health check timeout for {app_name}")
        return {"status": "timeout", "waited_seconds": max_wait}

    def test_service_endpoint(self, app_name: str, health_path: str = "/health") -> dict[str, Any]:
        """Test service endpoint health"""

        url = f"https://{app_name}.fly.dev{health_path}"

        try:
            response = requests.get(url, timeout=10)

            return {
                "url": url,
                "status_code": response.status_code,
                "healthy": response.status_code == 200,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
            }
        except Exception as e:
            return {"url": url, "healthy": False, "error": str(e)}

    def set_production_secrets(self, app_name: str) -> bool:
        """Set production secrets for a service"""

        # Define secrets per service
        secrets_map = {
            "sophia-weaviate": {
                "WEAVIATE_API_KEY": os.environ.get("WEAVIATE_API_KEY", ""),
                "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
            },
            "sophia-mcp": {
                "NEON_DATABASE_URL": os.environ.get("NEON_DATABASE_URL", ""),
                "REDIS_PASSWORD": os.environ.get("REDIS_PASSWORD", ""),
            },
            "sophia-vector": {
                "PORTKEY_API_KEY": os.environ.get("PORTKEY_API_KEY", ""),
                "COHERE_API_KEY": os.environ.get("COHERE_API_KEY", ""),
            },
            "sophia-api": {
                "PORTKEY_API_KEY": os.environ.get("PORTKEY_API_KEY", ""),
                "NEON_DATABASE_URL": os.environ.get("NEON_DATABASE_URL", ""),
                "LAMBDA_LABS_API_KEY": os.environ.get("LAMBDA_LABS_API_KEY", ""),
                "REDIS_PASSWORD": os.environ.get("REDIS_PASSWORD", ""),
            },
            "sophia-bridge": {"PORTKEY_API_KEY": os.environ.get("PORTKEY_API_KEY", "")},
            "sophia-ui": {},  # Frontend doesn't need backend secrets
        }

        service_secrets = secrets_map.get(app_name, {})

        if not service_secrets:
            logger.info(f"ℹ️  No secrets configured for {app_name}")
            return True

        # Filter out empty secrets
        filtered_secrets = {k: v for k, v in service_secrets.items() if v}

        if not filtered_secrets:
            logger.info(f"⚠️  No non-empty secrets found for {app_name}")
            return True

        try:
            # Set secrets in bulk
            secret_pairs = [f"{key}={value}" for key, value in filtered_secrets.items()]
            secrets_cmd = ["fly", "secrets", "set"] + secret_pairs + ["--app", app_name]

            result = subprocess.run(secrets_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"🔐 Set {len(filtered_secrets)} secrets for {app_name}")
                return True
            else:
                logger.info(f"⚠️  Secrets warning for {app_name}: {result.stderr}")
                return False
        except Exception as e:
            logger.info(f"❌ Secrets error for {app_name}: {e}")
            return False

    def deploy_all_services(self) -> dict[str, Any]:
        """Deploy all services in dependency order with monitoring"""

        logger.info("🚀 Starting Production Deployment of Sophia Intel AI")
        logger.info("=" * 70)

        deployment_results = {}

        # Sort services by priority (dependencies first)
        sorted_services = sorted(self.services, key=lambda x: x["priority"])

        for service in sorted_services:
            app_name = service["name"]

            # Set secrets first
            secrets_success = self.set_production_secrets(app_name)

            # Deploy service
            deploy_result = self.deploy_service(service)
            deploy_result["secrets_configured"] = secrets_success

            deployment_results[app_name] = deploy_result

            # Wait between deployments to avoid overwhelming the system
            if service != sorted_services[-1]:  # Don't wait after last service
                logger.info("⏸️  Waiting 30 seconds before next deployment...")
                time.sleep(30)

        return deployment_results

    def monitor_all_services(self, deployment_results: dict[str, Any]) -> dict[str, Any]:
        """Monitor all deployed services"""

        logger.info("\n📊 MONITORING DEPLOYED SERVICES")
        logger.info("=" * 50)

        monitoring_results = {}

        # Test health endpoints
        health_endpoints = {
            "sophia-weaviate": "/v1/.well-known/ready",
            "sophia-mcp": "/health",
            "sophia-vector": "/health",
            "sophia-api": "/healthz",
            "sophia-bridge": "/healthz",
            "sophia-ui": "/",
        }

        for app_name, health_path in health_endpoints.items():
            if deployment_results.get(app_name, {}).get("status") in ["deployed", "deploying"]:
                logger.info(f"🔍 Testing {app_name} health endpoint...")
                health_result = self.test_service_endpoint(app_name, health_path)
                monitoring_results[app_name] = health_result

                if health_result.get("healthy"):
                    logger.info(
                        f"✅ {app_name} is healthy ({health_result['response_time_ms']:.0f}ms)"
                    )
                else:
                    logger.info(
                        f"⚠️  {app_name} health check failed: {health_result.get('error', 'Unknown')}"
                    )
            else:
                logger.info(f"⏭️  Skipping {app_name} - not deployed successfully")
                monitoring_results[app_name] = {"status": "not_deployed"}

        return monitoring_results

    def generate_deployment_report(
        self, deployment_results: dict[str, Any], monitoring_results: dict[str, Any]
    ) -> str:
        """Generate comprehensive deployment and monitoring report"""

        successful_deployments = len(
            [r for r in deployment_results.values() if r.get("status") == "deployed"]
        )
        healthy_services = len([r for r in monitoring_results.values() if r.get("healthy")])

        report = f"""
# Production Deployment Report - Sophia Intel AI
**Deployment Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Status**: {'🟢 SUCCESS' if successful_deployments == len(self.services) else '🟡 PARTIAL'}

## 📊 Deployment Summary
- **Services Deployed**: {successful_deployments}/{len(self.services)}
- **Services Healthy**: {healthy_services}/{len(self.services)}
- **Infrastructure**: Fly.io (Multi-region: SJC/IAD)

## 🏗️ Service Deployment Status
"""

        for service in self.services:
            app_name = service["name"]
            deploy_status = deployment_results.get(app_name, {})
            health_status = monitoring_results.get(app_name, {})

            status_emoji = "✅" if deploy_status.get("status") == "deployed" else "⚠️"
            health_emoji = "🟢" if health_status.get("healthy") else "🔴"

            report += f"\n### {status_emoji} **{app_name}**\n"
            report += f"- **Deployment**: {deploy_status.get('status', 'unknown')}\n"
            report += f"- **Health**: {health_emoji} {'Healthy' if health_status.get('healthy') else 'Unhealthy'}\n"

            if deploy_status.get("public_url"):
                report += f"- **URL**: {deploy_status['public_url']}\n"

            if health_status.get("response_time_ms"):
                report += f"- **Response Time**: {health_status['response_time_ms']:.0f}ms\n"

        report += """
## 🔗 Service URLs
"""

        for service in self.services:
            app_name = service["name"]
            report += f"- **{app_name}**: https://{app_name}.fly.dev\n"

        report += """
## 🎯 Next Steps
1. **Verify all services** are responding correctly
2. **Configure load testing** to validate auto-scaling
3. **Set up monitoring alerts** for production
4. **Test end-to-end workflows** across all services
5. **Configure backup procedures** for persistent data

## 📈 Monitoring Dashboard
Access Fly.io dashboard: https://fly.io/dashboard
Monitor logs: `fly logs --app <service-name>`
Check metrics: `fly metrics --app <service-name>`
"""

        return report


def main():
    """Main deployment and monitoring function"""

    logger.info("🚀 SOPHIA INTEL AI - PRODUCTION DEPLOYMENT & MONITORING")
    logger.info("=" * 70)

    try:
        # Initialize deployment manager
        manager = ProductionDeploymentManager()

        # Install and authenticate Fly CLI
        if not manager.install_fly_cli():
            logger.info("❌ Fly CLI installation failed")
            return False

        if not manager.authenticate_fly():
            logger.info("❌ Fly.io authentication failed")
            return False

        logger.info("✅ Deployment environment ready")
        logger.info("\n🎯 Starting deployment of all 6 services...")

        # Deploy all services
        deployment_results = manager.deploy_all_services()

        # Wait for services to stabilize
        logger.info("\n⏳ Waiting 2 minutes for services to stabilize...")
        time.sleep(120)

        # Monitor all services
        monitoring_results = manager.monitor_all_services(deployment_results)

        # Generate report
        report = manager.generate_deployment_report(deployment_results, monitoring_results)

        # Save report
        with open("PRODUCTION_DEPLOYMENT_REPORT.md", "w") as f:
            f.write(report)

        logger.info("\n💾 Deployment report saved: PRODUCTION_DEPLOYMENT_REPORT.md")

        # Save JSON results for automation
        with open("production-deployment-results.json", "w") as f:
            json.dump(
                {
                    "deployment": deployment_results,
                    "monitoring": monitoring_results,
                    "timestamp": datetime.now().isoformat(),
                    "success_rate": len(
                        [r for r in deployment_results.values() if r.get("status") == "deployed"]
                    )
                    / len(manager.services),
                },
                f,
                indent=2,
            )

        # Final summary
        successful = len([r for r in deployment_results.values() if r.get("status") == "deployed"])
        healthy = len([r for r in monitoring_results.values() if r.get("healthy")])

        logger.info("\n" + "=" * 70)
        logger.info("📊 FINAL DEPLOYMENT STATUS")
        logger.info("=" * 70)
        logger.info(f"✅ Services Deployed: {successful}/{len(manager.services)}")
        logger.info(f"🟢 Services Healthy: {healthy}/{len(manager.services)}")

        if successful == len(manager.services) and healthy == len(manager.services):
            logger.info("🎉 DEPLOYMENT SUCCESS: All services deployed and healthy!")
            return True
        else:
            logger.info("⚠️  PARTIAL DEPLOYMENT: Some services need attention")
            return False

    except Exception as e:
        logger.info(f"❌ Deployment failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
