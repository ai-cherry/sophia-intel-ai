import os
import pulumi
from pulumi import Config, export, ResourceOptions
from pulumi_command import local
from lambda_dynamic import LambdaSSHKey, LambdaInstance, LambdaFirewall
from k3s import K3sCluster
from dns_tls import setup_dns_tls

# Load config
config = Config()
region = config.get('lambda:region') or 'us-east-1'
control_type = config.get('lambda:controlType') or 'gpu_1x_a100'
worker_type = config.get('lambda:workerType') or 'gpu_1x_a100'
allowed_ssh_cidrs = config.get('firewall:allowedSshCidrs')

# Read canonical SSH public key
key_path = os.path.expanduser('~/.ssh/id_ed25519_sophia_prod.pub')
if not os.path.exists(key_path):
    raise Exception(
        f"SSH public key not found at {key_path}. Run scripts/gen_ssh_key.sh first.")
with open(key_path) as f:
    pubkey = f.read().strip()

# Create Lambda SSH Key
ssh_key = LambdaSSHKey('sophia-key', public_key=pubkey)

# Create Firewall
firewall = LambdaFirewall('sophia-fw',
                          allowed_ssh_cidrs=allowed_ssh_cidrs,
                          allow_http=True,
                          allow_https=True,
                          ssh_key_id=ssh_key.id)

# Create K3s cluster (2 nodes)
cluster = K3sCluster('sophia-k3s',
                     region=region,
                     control_type=control_type,
                     worker_type=worker_type,
                     ssh_key_id=ssh_key.id,
                     firewall_id=firewall.id)

# DNS/TLS (stub)
setup_dns_tls(cluster)

# Outputs
export('kubeconfig', cluster.kubeconfig)
export('control_ip', cluster.control_ip)
export('worker_ip', cluster.worker_ip)
export('firewall_id', firewall.id)
export('ssh_key_id', ssh_key.id)
