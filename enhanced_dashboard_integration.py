#!/usr/bin/env python3
"""
Enhanced Sophia AI Platform - Integrated Dashboard System
Professional secret monitoring and environment management dashboard
"""

import asyncio
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Dashboard metrics data structure"""

    timestamp: str
    environment: str
    secret_health_score: float
    total_secrets: int
    valid_secrets: int
    invalid_secrets: int
    missing_secrets: int
    api_response_times: Dict[str, float]
    pulumi_connectivity: str
    system_uptime: float
    last_rotation: Optional[str]
    alerts: List[Dict]


class EnhancedSophiaDashboard:
    """Enhanced integrated dashboard for Sophia AI Platform monitoring"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.dashboard_dir = self.project_root / ".sophia" / "dashboard"
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)

        # Import our enhanced modules
        sys.path.append(str(self.project_root))

        # Dashboard configuration
        self.config = {
            "refresh_interval": 30,  # seconds
            "metrics_retention": 7,  # days
            "alert_thresholds": {
                "secret_health_critical": 60,
                "secret_health_warning": 80,
                "response_time_warning": 5000,  # ms
                "response_time_critical": 10000,  # ms
            },
            "dashboard_port": 8080,
            "grafana_integration": True,
        }

        # Metrics storage
        self.metrics_history = []
        self.current_alerts = []

        # Load historical metrics
        self._load_metrics_history()

    def _load_metrics_history(self):
        """Load historical metrics from storage"""

        metrics_file = self.dashboard_dir / "metrics_history.json"
        if metrics_file.exists():
            try:
                with open(metrics_file) as f:
                    data = json.load(f)
                    self.metrics_history = data.get("metrics", [])
                    self.current_alerts = data.get("alerts", [])
            except Exception as e:
                logger.warning(f"Failed to load metrics history: {e}")

    def _save_metrics_history(self):
        """Save metrics history to storage"""

        # Cleanup old metrics (keep only last 7 days)
        cutoff_time = datetime.now() - timedelta(days=self.config["metrics_retention"])

        self.metrics_history = [
            metric
            for metric in self.metrics_history
            if datetime.fromisoformat(metric["timestamp"]) > cutoff_time
        ]

        # Save to file
        metrics_file = self.dashboard_dir / "metrics_history.json"
        data = {
            "metrics": self.metrics_history,
            "alerts": self.current_alerts,
            "last_updated": datetime.now().isoformat(),
        }

        with open(metrics_file, "w") as f:
            json.dump(data, f, indent=2)

    async def collect_comprehensive_metrics(
        self, environment: str = None
    ) -> DashboardMetrics:
        """Collect comprehensive metrics for dashboard"""

        logger.info("📊 Collecting comprehensive metrics for dashboard")

        try:
            # Import enhanced secret manager
            from enhanced_secret_manager import EnhancedSecretManager

            from environment_selector import EnvironmentManager

            secret_manager = EnhancedSecretManager()
            env_manager = EnvironmentManager()

            # Determine environment
            if not environment:
                environment = env_manager.current_env or "development"

            # Collect secret validation metrics
            validation_results = await secret_manager.validate_all_secrets(environment)
            secret_health_report = secret_manager.generate_secret_health_report(
                validation_results
            )

            # Collect environment status
            env_status = env_manager.get_environment_status(environment)

            # Calculate API response times
            api_response_times = {}
            for secret_name, result in validation_results.items():
                if result.response_time > 0:
                    api_response_times[secret_name] = (
                        result.response_time * 1000
                    )  # Convert to ms

            # Get system uptime
            system_uptime = self._get_system_uptime()

            # Generate alerts
            alerts = self._generate_alerts(
                secret_health_report, api_response_times, env_status
            )

            # Create metrics object
            metrics = DashboardMetrics(
                timestamp=datetime.now().isoformat(),
                environment=environment,
                secret_health_score=secret_health_report["health_score"],
                total_secrets=secret_health_report["summary"]["total_secrets"],
                valid_secrets=secret_health_report["summary"]["valid_secrets"],
                invalid_secrets=secret_health_report["summary"]["invalid_secrets"],
                missing_secrets=len(secret_health_report["issues"]["missing"]),
                api_response_times=api_response_times,
                pulumi_connectivity=env_status.get("pulumi_connectivity", {}).get(
                    "status", "unknown"
                ),
                system_uptime=system_uptime,
                last_rotation=self._get_last_rotation_time(),
                alerts=alerts,
            )

            # Store metrics
            self.metrics_history.append(asdict(metrics))
            self.current_alerts = alerts
            self._save_metrics_history()

            return metrics

        except Exception as e:
            logger.error(f"❌ Failed to collect metrics: {e}")
            # Return minimal metrics on error
            return DashboardMetrics(
                timestamp=datetime.now().isoformat(),
                environment=environment or "unknown",
                secret_health_score=0.0,
                total_secrets=0,
                valid_secrets=0,
                invalid_secrets=0,
                missing_secrets=0,
                api_response_times={},
                pulumi_connectivity="error",
                system_uptime=0.0,
                last_rotation=None,
                alerts=[
                    {
                        "level": "critical",
                        "message": f"Dashboard metrics collection failed: {e}",
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
            )

    def _get_system_uptime(self) -> float:
        """Get system uptime in hours"""

        try:
            with open("/proc/uptime") as f:
                uptime_seconds = float(f.readline().split()[0])
                return uptime_seconds / 3600  # Convert to hours
        except Exception:
            return 0.0

    def _get_last_rotation_time(self) -> Optional[str]:
        """Get timestamp of last secret rotation"""

        rotation_file = self.dashboard_dir / "last_rotation.txt"
        if rotation_file.exists():
            try:
                return rotation_file.read_text().strip()
            except Exception:
                return None
        return None

    def _generate_alerts(
        self, health_report: Dict, response_times: Dict, env_status: Dict
    ) -> List[Dict]:
        """Generate alerts based on current metrics"""

        alerts = []
        now = datetime.now().isoformat()

        # Secret health alerts
        health_score = health_report["health_score"]
        if health_score < self.config["alert_thresholds"]["secret_health_critical"]:
            alerts.append(
                {
                    "level": "critical",
                    "category": "secret_health",
                    "message": f'Secret health critical: {health_score:.1f}% (threshold: {self.config["alert_thresholds"]["secret_health_critical"]}%)',
                    "timestamp": now,
                    "details": health_report["issues"],
                }
            )
        elif health_score < self.config["alert_thresholds"]["secret_health_warning"]:
            alerts.append(
                {
                    "level": "warning",
                    "category": "secret_health",
                    "message": f'Secret health warning: {health_score:.1f}% (threshold: {self.config["alert_thresholds"]["secret_health_warning"]}%)',
                    "timestamp": now,
                    "details": health_report["issues"],
                }
            )

        # API response time alerts
        for api_name, response_time in response_times.items():
            if (
                response_time
                > self.config["alert_thresholds"]["response_time_critical"]
            ):
                alerts.append(
                    {
                        "level": "critical",
                        "category": "performance",
                        "message": f"{api_name} response time critical: {response_time:.0f}ms",
                        "timestamp": now,
                        "api": api_name,
                    }
                )
            elif (
                response_time > self.config["alert_thresholds"]["response_time_warning"]
            ):
                alerts.append(
                    {
                        "level": "warning",
                        "category": "performance",
                        "message": f"{api_name} response time warning: {response_time:.0f}ms",
                        "timestamp": now,
                        "api": api_name,
                    }
                )

        # Pulumi connectivity alerts
        pulumi_status = env_status.get("pulumi_connectivity", {}).get("status")
        if pulumi_status in ["error", "timeout"]:
            alerts.append(
                {
                    "level": "warning",
                    "category": "connectivity",
                    "message": f"Pulumi ESC connectivity issue: {pulumi_status}",
                    "timestamp": now,
                    "details": env_status.get("pulumi_connectivity", {}),
                }
            )

        # Missing secrets alerts
        missing_secrets = health_report["issues"]["missing"]
        if missing_secrets:
            alerts.append(
                {
                    "level": "warning",
                    "category": "configuration",
                    "message": f'Missing secrets: {", ".join(missing_secrets)}',
                    "timestamp": now,
                    "missing_secrets": missing_secrets,
                }
            )

        return alerts

    def integrate_with_main_dashboard(self) -> Dict:
        """Integrate secret monitoring into main Sophia dashboard"""

        # Create integration configuration for main dashboard
        integration_config = {
            "secret_monitoring": {
                "enabled": True,
                "endpoint": "/api/secrets/metrics",
                "refresh_interval": 30,
                "panels": [
                    {
                        "type": "secret_health_score",
                        "title": "Secret Health Score",
                        "position": {"row": 1, "col": 1, "width": 3, "height": 2},
                    },
                    {
                        "type": "secret_status_distribution",
                        "title": "Secret Status",
                        "position": {"row": 1, "col": 4, "width": 3, "height": 2},
                    },
                    {
                        "type": "api_response_times",
                        "title": "API Response Times",
                        "position": {"row": 2, "col": 1, "width": 6, "height": 3},
                    },
                    {
                        "type": "environment_status",
                        "title": "Environment Status",
                        "position": {"row": 3, "col": 1, "width": 4, "height": 2},
                    },
                    {
                        "type": "active_alerts",
                        "title": "Secret Management Alerts",
                        "position": {"row": 3, "col": 5, "width": 2, "height": 2},
                    },
                ],
            },
            "environment_management": {
                "enabled": True,
                "endpoint": "/api/environment/status",
                "controls": [
                    {
                        "type": "environment_selector",
                        "title": "Environment",
                        "options": ["production", "staging", "development"],
                    },
                    {
                        "type": "secret_validation_trigger",
                        "title": "Validate Secrets",
                        "action": "validate_all_secrets",
                    },
                    {
                        "type": "environment_switch",
                        "title": "Switch Environment",
                        "action": "switch_environment",
                    },
                ],
            },
        }

        # Save integration config
        integration_file = self.dashboard_dir / "main_dashboard_integration.json"
        with open(integration_file, "w") as f:
            json.dump(integration_config, f, indent=2)

        return integration_config

    def generate_dashboard_widgets(self) -> Dict:
        """Generate dashboard widgets for integration"""

        widgets = {
            "secret_health_widget": {
                "component": "SecretHealthWidget",
                "props": {
                    "title": "Secret Health Score",
                    "endpoint": "/api/secrets/health",
                    "refresh_interval": 30,
                    "thresholds": {"critical": 60, "warning": 80, "good": 95},
                },
                "style": {
                    "width": "300px",
                    "height": "200px",
                    "background": "white",
                    "border_radius": "8px",
                    "box_shadow": "0 2px 10px rgba(0,0,0,0.1)",
                },
            },
            "environment_selector_widget": {
                "component": "EnvironmentSelectorWidget",
                "props": {
                    "title": "Environment",
                    "endpoint": "/api/environment/list",
                    "current_endpoint": "/api/environment/current",
                    "switch_endpoint": "/api/environment/switch",
                    "environments": [
                        {
                            "name": "production",
                            "label": "Production",
                            "color": "#dc3545",
                        },
                        {"name": "staging", "label": "Staging", "color": "#ffc107"},
                        {
                            "name": "development",
                            "label": "Development",
                            "color": "#28a745",
                        },
                    ],
                },
            },
            "api_status_widget": {
                "component": "APIStatusWidget",
                "props": {
                    "title": "API Status",
                    "endpoint": "/api/secrets/validation",
                    "apis": [
                        "OPENAI_API_KEY",
                        "ANTHROPIC_API_KEY",
                        "LAMBDA_API_KEY",
                        "EXA_API_KEY",
                    ],
                },
            },
            "alerts_widget": {
                "component": "AlertsWidget",
                "props": {
                    "title": "Secret Management Alerts",
                    "endpoint": "/api/secrets/alerts",
                    "max_alerts": 5,
                    "auto_refresh": True,
                },
            },
        }

        return widgets

    def create_dashboard_api_endpoints(self) -> Dict:
        """Create API endpoints for dashboard integration"""

        endpoints = {
            "/api/secrets/health": {
                "method": "GET",
                "description": "Get secret health score and summary",
                "handler": "get_secret_health",
            },
            "/api/secrets/metrics": {
                "method": "GET",
                "description": "Get comprehensive secret metrics",
                "handler": "get_secret_metrics",
            },
            "/api/secrets/validation": {
                "method": "POST",
                "description": "Trigger secret validation",
                "handler": "validate_secrets",
            },
            "/api/secrets/alerts": {
                "method": "GET",
                "description": "Get active secret management alerts",
                "handler": "get_secret_alerts",
            },
            "/api/environment/current": {
                "method": "GET",
                "description": "Get current environment",
                "handler": "get_current_environment",
            },
            "/api/environment/list": {
                "method": "GET",
                "description": "List all available environments",
                "handler": "list_environments",
            },
            "/api/environment/switch": {
                "method": "POST",
                "description": "Switch to different environment",
                "handler": "switch_environment",
            },
            "/api/environment/status": {
                "method": "GET",
                "description": "Get environment status",
                "handler": "get_environment_status",
            },
        }

        return endpoints

    def generate_main_dashboard_integration_code(self) -> str:
        """Generate integration code for main dashboard"""

        integration_code = '''
# Sophia AI Platform - Secret Management Dashboard Integration
# Add this to your main dashboard application

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

class SecretManagementIntegration:
    """Integration class for secret management in main dashboard"""
    
    def __init__(self, dashboard_instance):
        self.dashboard = dashboard_instance
        self.secret_manager = None
        self.env_manager = None
        self._initialize_managers()
    
    def _initialize_managers(self):
        """Initialize secret and environment managers"""
        try:
            from enhanced_secret_manager import EnhancedSecretManager
            from environment_selector import EnvironmentManager
            
            self.secret_manager = EnhancedSecretManager()
            self.env_manager = EnvironmentManager()
        except ImportError as e:
            print(f"Warning: Could not import secret management modules: {e}")
    
    async def get_secret_health_data(self) -> Dict:
        """Get secret health data for dashboard"""
        if not self.secret_manager:
            return {"error": "Secret manager not available"}
        
        try:
            current_env = self.env_manager.current_env or 'development'
            validation_results = await self.secret_manager.validate_all_secrets(current_env)
            health_report = self.secret_manager.generate_secret_health_report(validation_results)
            
            return {
                "health_score": health_report['health_score'],
                "total_secrets": health_report['summary']['total_secrets'],
                "valid_secrets": health_report['summary']['valid_secrets'],
                "invalid_secrets": health_report['summary']['invalid_secrets'],
                "environment": current_env,
                "status": "healthy" if health_report['health_score'] >= 80 else "warning" if health_report['health_score'] >= 60 else "critical",
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_environment_data(self) -> Dict:
        """Get environment data for dashboard"""
        if not self.env_manager:
            return {"error": "Environment manager not available"}
        
        try:
            environments = self.env_manager.list_environments()
            current_status = self.env_manager.get_environment_status()
            
            return {
                "environments": environments['environments'],
                "current_environment": environments['current_environment'],
                "current_status": current_status,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def switch_environment(self, environment: str) -> Dict:
        """Switch environment"""
        if not self.env_manager:
            return {"error": "Environment manager not available"}
        
        try:
            result = self.env_manager.switch_environment(environment)
            return result
        except Exception as e:
            return {"error": str(e)}

# Usage in main dashboard:
# 1. Import this integration class
# 2. Initialize: secret_integration = SecretManagementIntegration(dashboard_instance)
# 3. Add API endpoints that call the integration methods
# 4. Add dashboard widgets that consume the API endpoints
'''

        return integration_code

    def setup_complete_integration(self) -> Dict:
        """Setup complete integration with main dashboard"""

        logger.info("🔧 Setting up complete dashboard integration")

        # Generate all integration components
        integration_config = self.integrate_with_main_dashboard()
        widgets = self.generate_dashboard_widgets()
        endpoints = self.create_dashboard_api_endpoints()
        integration_code = self.generate_main_dashboard_integration_code()

        # Save all integration files
        integration_dir = self.dashboard_dir / "integration"
        integration_dir.mkdir(exist_ok=True)

        # Save configuration
        config_file = integration_dir / "dashboard_config.json"
        with open(config_file, "w") as f:
            json.dump(integration_config, f, indent=2)

        # Save widgets
        widgets_file = integration_dir / "dashboard_widgets.json"
        with open(widgets_file, "w") as f:
            json.dump(widgets, f, indent=2)

        # Save endpoints
        endpoints_file = integration_dir / "api_endpoints.json"
        with open(endpoints_file, "w") as f:
            json.dump(endpoints, f, indent=2)

        # Save integration code
        code_file = integration_dir / "integration_code.py"
        with open(code_file, "w") as f:
            f.write(integration_code)

        # Create README
        readme_content = f"""# Sophia AI Platform - Dashboard Integration

## Overview
This directory contains all the necessary files to integrate secret management and environment monitoring into the main Sophia AI Platform dashboard.

## Files
- `dashboard_config.json`: Configuration for dashboard panels and layout
- `dashboard_widgets.json`: Widget definitions for secret monitoring
- `api_endpoints.json`: API endpoint specifications
- `integration_code.py`: Python integration code for main dashboard

## Integration Steps
1. Copy the integration code from `integration_code.py` into your main dashboard application
2. Add the API endpoints defined in `api_endpoints.json`
3. Import the widget definitions from `dashboard_widgets.json`
4. Apply the configuration from `dashboard_config.json`

## Generated: {datetime.now().isoformat()}
"""

        readme_file = integration_dir / "README.md"
        with open(readme_file, "w") as f:
            f.write(readme_content)

        return {
            "status": "success",
            "integration_directory": str(integration_dir),
            "files_created": [
                "dashboard_config.json",
                "dashboard_widgets.json",
                "api_endpoints.json",
                "integration_code.py",
                "README.md",
            ],
            "widgets_count": len(widgets),
            "endpoints_count": len(endpoints),
            "panels_count": len(integration_config["secret_monitoring"]["panels"]),
        }


async def main():
    """Main function for testing the enhanced dashboard integration"""

    print("🎖️ ENHANCED SOPHIA AI PLATFORM - INTEGRATED DASHBOARD SYSTEM")
    print("=" * 80)
    print("Professional secret monitoring and environment management integration")
    print("=" * 80)

    dashboard = EnhancedSophiaDashboard()

    # Setup complete integration
    print("\\n🔧 Setting up complete dashboard integration:")

    integration_result = dashboard.setup_complete_integration()

    if integration_result["status"] == "success":
        print("✅ Integration setup complete!")
        print(
            f"📁 Integration directory: {integration_result['integration_directory']}"
        )
        print(f"📊 Created {integration_result['widgets_count']} dashboard widgets")
        print(f"🔌 Created {integration_result['endpoints_count']} API endpoints")
        print(f"📋 Created {integration_result['panels_count']} dashboard panels")
        print(f"📄 Files created: {', '.join(integration_result['files_created'])}")
    else:
        print("❌ Integration setup failed")

    # Collect and display sample metrics
    print("\\n📊 Collecting sample metrics for all environments:")

    environments = ["production", "staging", "development"]

    for env in environments:
        print(f"\\n🌍 {env.upper()} Environment:")

        try:
            metrics = await dashboard.collect_comprehensive_metrics(env)

            print(f"  Health Score: {metrics.secret_health_score:.1f}%")
            print(f"  Secrets: {metrics.valid_secrets}/{metrics.total_secrets} valid")
            print(f"  Alerts: {len(metrics.alerts)} active")
            print(f"  Pulumi ESC: {metrics.pulumi_connectivity}")

            if metrics.alerts:
                print("  Active Alerts:")
                for alert in metrics.alerts[:2]:  # Show first 2 alerts
                    print(f"    - {alert['level'].upper()}: {alert['message']}")

        except Exception as e:
            print(f"  ❌ Error collecting metrics: {e}")

    print("\\n🎉 Enhanced Dashboard Integration System Complete!")
    print("\\n📋 Next Steps:")
    print("1. Review integration files in .sophia/dashboard/integration/")
    print("2. Copy integration code to your main dashboard application")
    print("3. Add API endpoints and widgets to your dashboard")
    print("4. Test the integrated secret monitoring features")


if __name__ == "__main__":
    asyncio.run(main())
