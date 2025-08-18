import pulumi
import pulumi_fly as fly
import pulumi_docker as docker
import os

# Configuration
config = pulumi.Config()
app_name = "sophia-intel"
region = "us-west-2"

# Create Fly.io application
app = fly.App(
    app_name,
    fly.AppArgs(
        name=app_name,
        org="personal"
    )
)

# Fly.io Secrets Management
secrets = [
    "MCP_API_KEY",
    "AGNO_API_KEY", 
    "ANTHROPIC_API_KEY",
    "APIFY_API_TOKEN",
    "NOTION_API_KEY",
    "SALESFORCE_ACCESS_TOKEN",
    "SLACK_API_TOKEN",
    "POSTGRES_PASSWORD",
    "QDRANT_API_KEY",
    "GITHUB_PAT"
]

# Set secrets in Fly.io (these would be set via CLI or GitHub Actions)
for secret in secrets:
    fly.Secret(
        f"{app_name}-{secret.lower().replace('_', '-')}",
        fly.SecretArgs(
            app=app.name,
            name=secret,
            value=config.get_secret(secret) or f"${{{secret}}}"  # Use Pulumi config or env var
        )
    )

# Create Fly.io machine with enhanced configuration
machine = fly.Machine(
    f"{app_name}-machine",
    fly.MachineArgs(
        app=app.name,
        region=region,
        image="python:3.13-slim",
        cpu_kind="shared",
        cpus=2,
        memory_mb=4096,
        env={
            "QDRANT_URL": "https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io:6333",
            "REDIS_HOST": "redis",
            "POSTGRES_HOST": "postgres",
            "ENVIRONMENT": "production"
        },
        services=[
            fly.MachineServiceArgs(
                protocol="tcp",
                internal_port=5000,
                ports=[
                    fly.MachineServicePortArgs(
                        port=443,
                        handlers=["tls", "http"]
                    ),
                    fly.MachineServicePortArgs(
                        port=80,
                        handlers=["http"]
                    )
                ]
            )
        ],
        mounts=[
            fly.MachineMountArgs(
                volume="sophia_data",
                path="/app/data"
            )
        ]
    )
)

# Create persistent volume for data storage
volume = fly.Volume(
    f"{app_name}-volume",
    fly.VolumeArgs(
        app=app.name,
        name="sophia_data",
        region=region,
        size_gb=10
    )
)

# Create SSL certificate for custom domain
cert = fly.Cert(
    f"{app_name}-cert",
    fly.CertArgs(
        app=app.name,
        hostname="www.sophia-intel.ai"
    )
)

# MCP Server machine (separate service)
mcp_machine = fly.Machine(
    f"{app_name}-mcp-machine",
    fly.MachineArgs(
        app=app.name,
        region=region,
        image="python:3.13-slim",
        cpu_kind="shared",
        cpus=1,
        memory_mb=2048,
        env={
            "SERVICE_TYPE": "mcp_server",
            "REDIS_HOST": "redis"
        },
        services=[
            fly.MachineServiceArgs(
                protocol="tcp",
                internal_port=8000,
                ports=[
                    fly.MachineServicePortArgs(
                        port=8000,
                        handlers=["http"]
                    )
                ]
            )
        ]
    )
)

# External service configurations
postgres_config = {
    "host": config.get("postgres_host") or "postgres.fly.dev",
    "database": "sophia",
    "user": "sophia",
    "port": 5432
}

redis_config = {
    "host": config.get("redis_host") or "redis.fly.dev",
    "port": 6379
}

qdrant_config = {
    "url": "https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io:6333",
    "collection": "sophia_memory"
}

# Export important values
pulumi.export("app_name", app.name)
pulumi.export("app_url", f"https://{app_name}.fly.dev")
pulumi.export("custom_domain", "https://www.sophia-intel.ai")
pulumi.export("machine_id", machine.id)
pulumi.export("mcp_machine_id", mcp_machine.id)
pulumi.export("volume_id", volume.id)
pulumi.export("cert_hostname", cert.hostname)
pulumi.export("postgres_config", postgres_config)
pulumi.export("redis_config", redis_config)
pulumi.export("qdrant_config", qdrant_config)
pulumi.export("secrets_configured", secrets)

