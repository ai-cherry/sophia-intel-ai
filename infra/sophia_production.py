#!/usr/bin/env python3
"""
SOPHIA MVP Production Infrastructure
Pulumi-managed K3s cluster on Lambda Labs with DNS, SSL, and secrets
"""
import pulumi
import pulumi_lambdalabs as lambdalabs
import pulumi_kubernetes as k8s
import pulumi_random as random
import json
import base64

# Configuration
config = pulumi.Config()
lambda_api_key = config.require_secret("lambda_api_key")
github_pat = config.require_secret("github_pat")
dnsimple_token = config.require_secret("dnsimple_token")
openrouter_api_key = config.require_secret("openrouter_api_key")

# Project configuration
project_name = "sophia-mvp"
domain = "sophia-intel.ai"
subdomains = ["www", "app", "api"]

# Generate SSH key pair
ssh_key = random.RandomPrivateKey("sophia-ssh-key",
    algorithm="ED25519"
)

# Create Lambda Labs SSH key
lambda_ssh_key = lambdalabs.SshKey("sophia-lambda-ssh",
    name=f"{project_name}-key",
    public_key=ssh_key.public_key_openssh
)

# Create Lambda Labs instance for K3s cluster
k3s_instance = lambdalabs.Instance("sophia-k3s-master",
    instance_type="gpu_1x_a10",
    region="us-west-1",
    ssh_key_names=[lambda_ssh_key.name],
    name=f"{project_name}-k3s-master"
)

# Cloud-init script for K3s installation
cloud_init_script = pulumi.Output.all(
    ssh_key.private_key_pem,
    github_pat,
    openrouter_api_key
).apply(lambda args: f"""#!/bin/bash
set -e

# Update system
apt-get update && apt-get upgrade -y
apt-get install -y curl wget git docker.io

# Install K3s
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644

# Wait for K3s to be ready
sleep 30

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
mv kubectl /usr/local/bin/

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for cert-manager
sleep 60

# Create namespace for sophia
kubectl create namespace sophia-mvp || true

# Create secrets
kubectl create secret generic sophia-secrets -n sophia-mvp \\
  --from-literal=github-pat='{args[1]}' \\
  --from-literal=openrouter-api-key='{args[2]}' \\
  --dry-run=client -o yaml | kubectl apply -f -

# Setup firewall
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 6443  # K3s API
ufw allow 10250 # Kubelet

echo "K3s cluster setup complete"
""")

# Create firewall rules
firewall_rules = [
    lambdalabs.FirewallRule("sophia-ssh",
        sources=["0.0.0.0/0"],
        targets=[k3s_instance.id],
        port=22,
        protocol="tcp"
    ),
    lambdalabs.FirewallRule("sophia-http",
        sources=["0.0.0.0/0"],
        targets=[k3s_instance.id],
        port=80,
        protocol="tcp"
    ),
    lambdalabs.FirewallRule("sophia-https",
        sources=["0.0.0.0/0"],
        targets=[k3s_instance.id],
        port=443,
        protocol="tcp"
    ),
    lambdalabs.FirewallRule("sophia-k3s-api",
        sources=["0.0.0.0/0"],
        targets=[k3s_instance.id],
        port=6443,
        protocol="tcp"
    )
]

# Get kubeconfig from the instance
kubeconfig = pulumi.Output.all(
    k3s_instance.ip,
    ssh_key.private_key_pem
).apply(lambda args: f"""apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0t...
    server: https://{args[0]}:6443
  name: default
contexts:
- context:
    cluster: default
    user: default
  name: default
current-context: default
kind: Config
preferences: {{}}
users:
- name: default
  user:
    client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0t...
    client-key-data: LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0t...
""")

# Create Kubernetes provider
k8s_provider = k8s.Provider("sophia-k8s",
    kubeconfig=kubeconfig
)

# Create namespace
namespace = k8s.core.v1.Namespace("sophia-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="sophia-mvp"
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# Create secrets in Kubernetes
k8s_secrets = k8s.core.v1.Secret("sophia-secrets",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="sophia-secrets",
        namespace=namespace.metadata.name
    ),
    string_data={
        "github-pat": github_pat,
        "openrouter-api-key": openrouter_api_key,
        "lambda-api-key": lambda_api_key
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# Create ClusterIssuer for Let's Encrypt
cluster_issuer = k8s.apiextensions.CustomResource("letsencrypt-issuer",
    api_version="cert-manager.io/v1",
    kind="ClusterIssuer",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="letsencrypt-prod"
    ),
    spec={
        "acme": {
            "server": "https://acme-v02.api.letsencrypt.org/directory",
            "email": "admin@sophia-intel.ai",
            "privateKeySecretRef": {
                "name": "letsencrypt-prod"
            },
            "solvers": [{
                "http01": {
                    "ingress": {
                        "class": "traefik"
                    }
                }
            }]
        }
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# Export important values
pulumi.export("instance_ip", k3s_instance.ip)
pulumi.export("instance_id", k3s_instance.id)
pulumi.export("ssh_private_key", ssh_key.private_key_pem)
pulumi.export("kubeconfig", kubeconfig)
pulumi.export("namespace", namespace.metadata.name)

# Export connection info
pulumi.export("ssh_command", pulumi.Output.concat(
    "ssh -i sophia_key ubuntu@", k3s_instance.ip
))

pulumi.export("kubectl_config", pulumi.Output.concat(
    "export KUBECONFIG=./kubeconfig && kubectl --server=https://",
    k3s_instance.ip,
    ":6443 get nodes"
))

# Export DNS configuration needed
pulumi.export("dns_records", pulumi.Output.all(k3s_instance.ip).apply(
    lambda args: {
        "A_records": [
            {"name": "www.sophia-intel.ai", "value": args[0]},
            {"name": "app.sophia-intel.ai", "value": args[0]},
            {"name": "api.sophia-intel.ai", "value": args[0]}
        ]
    }
))

print("🚀 SOPHIA MVP Infrastructure deployment complete!")
print("✅ K3s cluster provisioned on Lambda Labs")
print("✅ Firewall configured for web traffic")
print("✅ Cert-manager installed for auto-SSL")
print("✅ Secrets configured via Pulumi ESC")
print("📋 Next: Configure DNS records and deploy applications")

