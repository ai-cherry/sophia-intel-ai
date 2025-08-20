"""
Pulumi IaC for Sophia Intel cloud deployment.
Builds Docker images and deploys to Fly.io using flyctl.
"""

import json
import os
import subprocess
from datetime import datetime

import pulumi
from pulumi import ResourceOptions, Output, Config
from pulumi_command import local as command
from pulumi_docker import Image, DockerBuild

cfg = Config()
registry = cfg.require_object("registry")  # { server, org, repoPrefix }
apps = cfg.require_object("apps")          # list of {name, context, dockerfile, flyToml, port}

# CI will pass in IMAGE_TAG or we default to short git sha + date
def git_sha_short():
    """Get short git SHA for image tagging."""
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        return "dev"

image_tag = os.getenv("IMAGE_TAG", f"{git_sha_short()}-{datetime.utcnow().strftime('%Y%m%d%H%M')}")

# Docker registry target e.g. ghcr.io/ai-cherry/sophia-<app>:<tag>
def registry_image_name(app_name: str) -> str:
    """Generate full registry image name for an app."""
    repo = f"{registry['repoPrefix']}-{app_name}"
    return f"{registry['server']}/{registry['org']}/{repo}:{image_tag}"

# Ensure flyctl is present at runtime (we invoke it via Pulumi command)
flyctl_path = os.getenv("FLYCTL_PATH", "flyctl")
fly_token = os.getenv("FLY_API_TOKEN") or pulumi.Config("fly").get("token")
if not fly_token:
    pulumi.log.warn("FLY_API_TOKEN not set; flyctl commands will fail until provided.")

built_images = {}
deploy_cmds = {}

for app in apps:
    app_name = app["name"]
    context = app["context"]
    dockerfile = app["dockerfile"]
    fly_toml = app["flyToml"]

    image_ref = registry_image_name(app_name)

    # Build & Push image
    img = Image(
        f"{app_name}-image",
        build=DockerBuild(
            context=context,
            dockerfile=dockerfile,
            platform="linux/amd64",  # change/extend as needed
            build_args={
                "MCP_ROLE": app_name.replace("sophia-", "")  # code, context, memory, research, business
            }
        ),
        image_name=image_ref,
        skip_push=False,  # push to registry
    )
    built_images[app_name] = img.image_name

    # Deploy via flyctl using the built image
    # We rely on per-app fly.toml and override image at deploy time
    deploy = command.Command(
        f"{app_name}-deploy",
        create=Output.concat(
            f"export FLY_API_TOKEN='{fly_token}' && ",
            flyctl_path, " deploy ",
            "--config ", fly_toml, " ",
            "--image ", img.image_name, " ",
            "--app ", app_name, " ",
            "--strategy immediate ",
            "--yes"
        ),
        opts=ResourceOptions(depends_on=[img]),
        environment={"FLY_API_TOKEN": fly_token} if fly_token else None,
        delete=Output.concat(
            f"export FLY_API_TOKEN='{fly_token}' && ",
            flyctl_path, " apps destroy ", app_name, " --yes"
        ),
    )
    deploy_cmds[app_name] = deploy

# Export results
pulumi.export("image_tag", image_tag)
pulumi.export("images", built_images)
pulumi.export("deployments", {name: "deployed" for name in deploy_cmds.keys()})

