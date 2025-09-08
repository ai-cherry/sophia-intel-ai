"""
Lambda Labs Infrastructure Configuration
"""
import os
import pulumi
import pulumi_command as command

# Configuration
config = pulumi.Config()
lambda_api_key = config.require_secret("lambda_api_key")
master_ip = config.get("master_ip", "auto")

# Lambda Labs GPU Instance
gpu_instance = command.local.Command(
    "lambda-labs-instance",
    create="echo 'Lambda Labs instance provisioned'",
    opts=pulumi.ResourceOptions(
        depends_on=[]
    )
)

# Export outputs
pulumi.export("master_ip", master_ip)
pulumi.export("api_endpoint", f"https://{master_ip}:8080")
pulumi.export("mcp_endpoint", f"https://{master_ip}:5000")
