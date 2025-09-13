#!/usr/bin/env python3
"""
Monitoring and Alerting Setup
Creates monitoring dashboards and alerting rules for Sophia Intel AI
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List

class MonitoringSetup:
    """Setup monitoring and alerting infrastructure"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.monitoring_path = self.base_path / "monitoring"
        self.monitoring_path.mkdir(exist_ok=True)
    
    def create_prometheus_config(self) -> Dict[str, Any]:
        """Create Prometheus configuration"""
        config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "rule_files": [
                "alerts.yml"
            ],
            "alertmanager": {
                "alertmanagers": [{
                    "static_configs": [{
                        "targets": ["localhost:9093"]
                    }]
                }]
            },
            "scrape_configs": [
                {
                    "job_name": "sophia-bridge",
                    "static_configs": [{
                        "targets": ["localhost:8003"]
                    }],
                    "metrics_path": "/metrics",
                    "scrape_interval": "10s"
                },
                {
                    "job_name": "sophia-health-check",
                    "static_configs": [{
                        "targets": ["localhost:8888"]
                    }],
                    "metrics_path": "/metrics",
                    "scrape_interval": "30s"
                },
                {
                    "job_name": "postgres-exporter",
                    "static_configs": [{
                        "targets": ["localhost:9187"]
                    }]
                },
                {
                    "job_name": "redis-exporter", 
                    "static_configs": [{
                        "targets": ["localhost:9121"]
                    }]
                }
            ]
        }
        return config
    
    def create_alerting_rules(self) -> Dict[str, Any]:
        """Create Prometheus alerting rules"""
        rules = {
            "groups": [
                {
                    "name": "sophia-critical",
                    "rules": [
                        {
                            "alert": "SophiaServiceDown",
                            "expr": "up{job=~\"sophia-.*\"} == 0",
                            "for": "30s",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "Sophia service {{ $labels.job }} is down",
                                "description": "Service {{ $labels.job }} has been down for more than 30 seconds"
                            }
                        },
                        {
                            "alert": "BrainIngestFailureRate",
                            "expr": "rate(brain_ingest_errors_total[5m]) > 0.1",
                            "for": "2m",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "High brain ingest failure rate",
                                "description": "Brain ingest error rate is {{ $value }} errors/sec"
                            }
                        },
                        {
                            "alert": "WeaviateConnectionFailure",
                            "expr": "weaviate_connection_failures_total > 5",
                            "for": "1m",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "Weaviate connection failures",
                                "description": "Multiple Weaviate connection failures detected"
                            }
                        }
                    ]
                },
                {
                    "name": "sophia-warning",
                    "rules": [
                        {
                            "alert": "HighResponseTime",
                            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2.0",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High response time on {{ $labels.endpoint }}",
                                "description": "95th percentile response time is {{ $value }}s"
                            }
                        },
                        {
                            "alert": "HighMemoryUsage",
                            "expr": "process_resident_memory_bytes / 1024 / 1024 > 1000",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High memory usage on {{ $labels.job }}",
                                "description": "Memory usage is {{ $value }}MB"
                            }
                        }
                    ]
                },
                {
                    "name": "sophia-infrastructure",
                    "rules": [
                        {
                            "alert": "PostgresConnectionFailure",
                            "expr": "pg_up == 0",
                            "for": "30s",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "PostgreSQL is down",
                                "description": "PostgreSQL database connection failed"
                            }
                        },
                        {
                            "alert": "RedisConnectionFailure", 
                            "expr": "redis_up == 0",
                            "for": "30s",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "Redis is down",
                                "description": "Redis connection failed"
                            }
                        },
                        {
                            "alert": "DiskSpaceRunningLow",
                            "expr": "node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"} < 0.1",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "Disk space running low",
                                "description": "Available disk space is less than 10%"
                            }
                        }
                    ]
                }
            ]
        }
        return rules
    
    def create_grafana_dashboard(self) -> Dict[str, Any]:
        """Create Grafana dashboard configuration"""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "Sophia Intel AI - System Overview",
                "description": "Main monitoring dashboard for Sophia Intel AI system",
                "tags": ["sophia", "ai", "monitoring"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Service Health Overview",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "up{job=~\"sophia-.*\"}",
                                "legendFormat": "{{ job }}"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "red", "value": 0},
                                        {"color": "green", "value": 1}
                                    ]
                                }
                            }
                        },
                        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Brain Ingest Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(brain_ingest_requests_total[5m])",
                                "legendFormat": "Requests/sec"
                            },
                            {
                                "expr": "rate(brain_ingest_errors_total[5m])",
                                "legendFormat": "Errors/sec"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 12, "x": 6, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Response Time Distribution",
                        "type": "heatmap",
                        "targets": [
                            {
                                "expr": "rate(http_request_duration_seconds_bucket[5m])",
                                "legendFormat": "{{ le }}"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 6}
                    },
                    {
                        "id": 4,
                        "title": "Vector Database Operations",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(weaviate_operations_total[5m])",
                                "legendFormat": "{{ operation }}"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 6}
                    },
                    {
                        "id": 5,
                        "title": "Memory Usage",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "process_resident_memory_bytes / 1024 / 1024",
                                "legendFormat": "{{ job }} Memory (MB)"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 12}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "10s"
            },
            "folderId": 0,
            "overwrite": True
        }
        return dashboard
    
    def create_docker_compose_monitoring(self) -> Dict[str, Any]:
        """Create Docker Compose file for monitoring stack"""
        compose = {
            "version": "3.8",
            "services": {
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "container_name": "sophia-prometheus",
                    "ports": ["9090:9090"],
                    "volumes": [
                        "./prometheus.yml:/etc/prometheus/prometheus.yml",
                        "./alerts.yml:/etc/prometheus/alerts.yml"
                    ],
                    "command": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus",
                        "--web.console.libraries=/etc/prometheus/console_libraries",
                        "--web.console.templates=/etc/prometheus/consoles",
                        "--storage.tsdb.retention.time=200h",
                        "--web.enable-lifecycle"
                    ]
                },
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "container_name": "sophia-grafana",
                    "ports": ["3001:3000"],
                    "environment": [
                        "GF_SECURITY_ADMIN_PASSWORD=admin"
                    ],
                    "volumes": [
                        "grafana-data:/var/lib/grafana",
                        "./grafana/dashboards:/etc/grafana/provisioning/dashboards",
                        "./grafana/datasources:/etc/grafana/provisioning/datasources"
                    ]
                },
                "alertmanager": {
                    "image": "prom/alertmanager:latest",
                    "container_name": "sophia-alertmanager",
                    "ports": ["9093:9093"],
                    "volumes": [
                        "./alertmanager.yml:/etc/alertmanager/alertmanager.yml"
                    ]
                },
                "postgres-exporter": {
                    "image": "prometheuscommunity/postgres-exporter:latest",
                    "container_name": "sophia-postgres-exporter",
                    "ports": ["9187:9187"],
                    "environment": [
                        "DATA_SOURCE_NAME=postgresql://builder:builder123@postgres:5432/builder?sslmode=disable"
                    ]
                },
                "redis-exporter": {
                    "image": "oliver006/redis_exporter:latest",
                    "container_name": "sophia-redis-exporter",
                    "ports": ["9121:9121"],
                    "environment": [
                        "REDIS_ADDR=redis://valkey:6379"
                    ]
                }
            },
            "volumes": ["grafana-data:"],
            "networks": {
                "default": {
                    "external": True,
                    "name": "builder-network"
                }
            }
        }
        return compose
    
    def setup_monitoring_infrastructure(self):
        """Set up complete monitoring infrastructure"""
        print("🔧 Setting up monitoring infrastructure...")
        
        # Create monitoring directory structure
        (self.monitoring_path / "grafana" / "dashboards").mkdir(parents=True, exist_ok=True)
        (self.monitoring_path / "grafana" / "datasources").mkdir(parents=True, exist_ok=True)
        
        # Write Prometheus configuration
        prometheus_config = self.create_prometheus_config()
        with open(self.monitoring_path / "prometheus.yml", "w") as f:
            import yaml
            yaml.dump(prometheus_config, f, default_flow_style=False)
        
        # Write alerting rules
        alerts = self.create_alerting_rules()
        with open(self.monitoring_path / "alerts.yml", "w") as f:
            import yaml
            yaml.dump(alerts, f, default_flow_style=False)
        
        # Write Grafana dashboard
        dashboard = self.create_grafana_dashboard()
        with open(self.monitoring_path / "grafana" / "dashboards" / "sophia-overview.json", "w") as f:
            json.dump(dashboard, f, indent=2)
        
        # Write Grafana datasource configuration
        datasource_config = {
            "apiVersion": 1,
            "datasources": [{
                "name": "Prometheus",
                "type": "prometheus",
                "access": "proxy",
                "url": "http://prometheus:9090",
                "isDefault": True
            }]
        }
        with open(self.monitoring_path / "grafana" / "datasources" / "datasources.yml", "w") as f:
            import yaml
            yaml.dump(datasource_config, f)
        
        # Write Docker Compose for monitoring
        monitoring_compose = self.create_docker_compose_monitoring()
        with open(self.monitoring_path / "docker-compose.monitoring.yml", "w") as f:
            import yaml
            yaml.dump(monitoring_compose, f, default_flow_style=False)
        
        # Create Alertmanager configuration
        alertmanager_config = {
            "global": {
                "smtp_smarthost": "localhost:587",
                "smtp_from": "sophia-ai@localhost"
            },
            "route": {
                "group_by": ["alertname"],
                "group_wait": "10s",
                "group_interval": "10s",
                "repeat_interval": "1h",
                "receiver": "web.hook"
            },
            "receivers": [{
                "name": "web.hook",
                "webhook_configs": [{
                    "url": "http://localhost:5001/alerts",
                    "send_resolved": True
                }]
            }]
        }
        with open(self.monitoring_path / "alertmanager.yml", "w") as f:
            import yaml
            yaml.dump(alertmanager_config, f)
        
        print("✅ Monitoring infrastructure setup complete!")
        print(f"📁 Files created in: {self.monitoring_path}")
        print("🚀 To start monitoring:")
        print(f"   cd {self.monitoring_path}")
        print("   docker-compose -f docker-compose.monitoring.yml up -d")
        print("🌐 Access points:")
        print("   - Prometheus: http://localhost:9090")
        print("   - Grafana: http://localhost:3001 (admin/admin)")
        print("   - Alertmanager: http://localhost:9093")

def main():
    """Main monitoring setup"""
    try:
        # Install required dependency
        import yaml
    except ImportError:
        print("Installing PyYAML...")
        import subprocess
        subprocess.check_call(["pip", "install", "PyYAML"])
        import yaml
    
    setup = MonitoringSetup()
    setup.setup_monitoring_infrastructure()

if __name__ == "__main__":
    main()