#!/usr/bin/env python3
"""
Create domain separation configuration files for Sophia and Artemis
"""

import json
import os
from pathlib import Path


def create_domain_separation_config():
    """Create domain separation configuration files"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    # Artemis config - CEO-only technical dashboard
    artemis_config = {
        "domain": "artemis",
        "name": "Artemis AI Orchestrator",
        "description": "CEO-only technical dashboard for repository and coding environment",
        "user": "lynn_patrick_musil",
        "qdrant": {
            "collection": "artemis_tech",
            "host": os.getenv("QDRANT_CLOUD_URL", "https://your-cluster.qdrant.io"),
        },
        "redis": {
            "db": 0,
            "url": os.getenv("REDIS_CLOUD_URL", "redis://redis-cloud.upstash.io:6379"),
        },
        "ports": {"min": 9100, "max": 9199},
        "services": {
            "allowed": [
                "github",
                "mcp_servers",
                "code_agents",
                "repository_tools",
                "technical_metrics",
                "dev_environment",
            ],
            "forbidden": [
                "slack",
                "asana",
                "linear",
                "notion",
                "gong",
                "intercom",
                "hubspot",
                "salesforce",
                "pay_ready_crm",
                "business_analytics",
            ],
        },
    }

    # Sophia config - Business intelligence dashboard
    sophia_config = {
        "domain": "sophia",
        "name": "Sophia Business Orchestrator",
        "description": "Business intelligence dashboard for Pay Ready team",
        "users": ["lynn_patrick_musil"],
        "qdrant": {
            "collection": "sophia_business",
            "host": os.getenv("QDRANT_CLOUD_URL", "https://your-cluster.qdrant.io"),
        },
        "redis": {
            "db": 1,
            "url": os.getenv("REDIS_CLOUD_URL", "redis://redis-cloud.upstash.io:6379"),
        },
        "ports": {"min": 9000, "max": 9099},
        "services": {
            "allowed": [
                "slack",
                "asana",
                "linear",
                "notion",
                "gong",
                "intercom",
                "hubspot",
                "salesforce",
                "pay_ready_crm",
                "business_analytics",
                "revenue_tracking",
                "customer_data",
            ],
            "forbidden": [
                "github",
                "code_agents",
                "repository_tools",
                "technical_metrics",
                "dev_environment",
                "mcp_servers",
            ],
        },
    }

    # Save configs
    with open(config_dir / "artemis.json", "w") as f:
        json.dump(artemis_config, f, indent=2)

    with open(config_dir / "sophia.json", "w") as f:
        json.dump(sophia_config, f, indent=2)

    print("✅ Domain separation configs created")
    print("Artemis:", artemis_config["name"])
    print("Sophia:", sophia_config["name"])

    return artemis_config, sophia_config


if __name__ == "__main__":
    create_domain_separation_config()
