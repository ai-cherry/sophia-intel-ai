import pulumi
import pulumi_fly as fly
import pulumi_docker as docker

# Create Fly.io application
app = fly.App(
    "sophia-intel",
    fly.AppArgs(
        name="sophia-intel",
        org="personal"
    )
)

# Create Fly.io machine
machine = fly.Machine(
    "sophia-intel-machine",
    fly.MachineArgs(
        app=app.name,
        region="us-west-2",
        image="python:3.13",
        cpu_kind="shared",
        cpus=2,
        memory_mb=4096,
        envs={
            "QDRANT_URL": "https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io:6333",
            "POSTGRES_PASSWORD": "securepassword",
            "REDIS_HOST": "redis"
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
        ]
    )
)

# Create SSL certificate
cert = fly.Cert(
    "sophia-intel-cert",
    fly.CertArgs(
        app=app.name,
        hostname="www.sophia-intel.ai"
    )
)

# Docker Compose for local services
docker_compose = docker.Compose(
    "sophia-intel-services",
    docker.ComposeArgs(
        compose_file="docker-compose.yml"
    )
)

# Export outputs
pulumi.export("app_url", app.url)
pulumi.export("machine_id", machine.id)
pulumi.export("cert_hostname", cert.hostname)

