#!/bin/bash
set -e

# SOPHIA MVP Deployment Script for Lambda Labs
# Deploys to existing sophia-development instance: 155.248.194.183

echo "🚀 SOPHIA MVP Production Deployment Starting..."
echo "================================================"

# Configuration
INSTANCE_IP="155.248.194.183"
SSH_KEY_PATH="$HOME/.ssh/sophia2025"
GITHUB_PAT="${GITHUB_PAT:-}"
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
LAMBDA_API_KEY="${LAMBDA_API_KEY:-secret_sophiacloudapi_17cf7f3cedca48f18b4b8ea46cbb258f.EsLXt0lkGlhZ1Nd369Ld5DMSuhJg9O9y}"
DNSIMPLE_API_KEY="${DNSIMPLE_API_KEY:-dnsimple_u_XBHeyhH3O8uKJF6HnqU76h7ANWdNvUzN}"

# Check prerequisites
echo "🔍 Checking prerequisites..."
if [ -z "$GITHUB_PAT" ]; then
    echo "❌ GITHUB_PAT environment variable not set"
    exit 1
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ OPENROUTER_API_KEY environment variable not set"
    exit 1
fi

echo "✅ Prerequisites check complete"

# Function to run commands on remote instance
run_remote() {
    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no ubuntu@$INSTANCE_IP "$1"
}

# Function to copy files to remote instance
copy_to_remote() {
    scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -r "$1" ubuntu@$INSTANCE_IP:"$2"
}

echo "📡 Testing connection to Lambda Labs instance..."
if ! run_remote "echo 'Connection successful'"; then
    echo "❌ Cannot connect to instance $INSTANCE_IP"
    echo "💡 Make sure SSH key is available and instance is running"
    exit 1
fi

echo "✅ Connection to $INSTANCE_IP successful"

# Update system and install Docker
echo "🔧 Setting up Docker and dependencies..."
run_remote "
    sudo apt-get update && 
    sudo apt-get install -y docker.io docker-compose curl git &&
    sudo systemctl enable docker &&
    sudo systemctl start docker &&
    sudo usermod -aG docker ubuntu
"

# Install K3s if not already installed
echo "🚢 Installing K3s..."
run_remote "
    if ! command -v k3s &> /dev/null; then
        curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
        sudo systemctl enable k3s
    fi
    sudo systemctl start k3s
"

# Wait for K3s to be ready
echo "⏳ Waiting for K3s to be ready..."
run_remote "
    timeout 120 bash -c 'until sudo k3s kubectl get nodes | grep Ready; do sleep 5; done'
"

# Install cert-manager
echo "🔐 Installing cert-manager..."
run_remote "
    sudo k3s kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    sleep 30
"

# Create project directory and copy files
echo "📁 Setting up project directory..."
run_remote "rm -rf /home/ubuntu/sophia-intel && mkdir -p /home/ubuntu/sophia-intel"
copy_to_remote "." "/home/ubuntu/sophia-intel/"

# Create environment file
echo "🔧 Creating environment configuration..."
run_remote "
    cd /home/ubuntu/sophia-intel
    cat > docker/production/.env << EOF
GITHUB_PAT=$GITHUB_PAT
OPENROUTER_API_KEY=$OPENROUTER_API_KEY
LAMBDA_API_KEY=$LAMBDA_API_KEY
DNSIMPLE_API_KEY=$DNSIMPLE_API_KEY
POSTGRES_PASSWORD=\$(openssl rand -base64 32)
REDIS_PASSWORD=\$(openssl rand -base64 32)
FLASK_SECRET_KEY=\$(openssl rand -base64 32)
DOMAIN=sophia-intel.ai
SUBDOMAIN_API=api.sophia-intel.ai
SUBDOMAIN_APP=app.sophia-intel.ai
SSL_EMAIL=admin@sophia-intel.ai
EOF
"

# Build Docker images
echo "🐳 Building Docker images..."
run_remote "
    cd /home/ubuntu/sophia-intel
    docker build -f docker/production/Dockerfile.api -t sophia-intel/api:latest .
    docker build -f docker/production/Dockerfile.dashboard -t sophia-intel/dashboard:latest .
    docker build -f docker/production/Dockerfile.mcp -t sophia-intel/mcp:latest .
"

# Deploy with Docker Compose first (for testing)
echo "🚀 Starting services with Docker Compose..."
run_remote "
    cd /home/ubuntu/sophia-intel/docker/production
    docker-compose -f docker-compose.prod.yml up -d
    sleep 30
"

# Check service health
echo "🏥 Checking service health..."
run_remote "
    cd /home/ubuntu/sophia-intel/docker/production
    docker-compose -f docker-compose.prod.yml ps
    
    echo 'Testing API health...'
    timeout 30 bash -c 'until curl -f http://localhost:5000/api/health; do sleep 2; done' || echo 'API health check failed'
    
    echo 'Testing Dashboard...'
    timeout 30 bash -c 'until curl -f http://localhost:80/health; do sleep 2; done' || echo 'Dashboard health check failed'
"

# Apply Kubernetes manifests
echo "☸️  Deploying to Kubernetes..."
run_remote "
    cd /home/ubuntu/sophia-intel
    
    # Create namespace
    sudo k3s kubectl apply -f k8s/manifests/namespace/
    
    # Create secrets (with real values)
    sed 's/GITHUB_PAT_PLACEHOLDER/$GITHUB_PAT/g; s/OPENROUTER_API_KEY_PLACEHOLDER/$OPENROUTER_API_KEY/g; s/LAMBDA_API_KEY_PLACEHOLDER/$LAMBDA_API_KEY/g; s/DNSIMPLE_API_KEY_PLACEHOLDER/$DNSIMPLE_API_KEY/g' k8s/manifests/secrets/sophia-secrets.yaml | sudo k3s kubectl apply -f -
    
    # Deploy services
    sudo k3s kubectl apply -f k8s/manifests/services/
    sudo k3s kubectl apply -f k8s/manifests/deployments/
    sudo k3s kubectl apply -f k8s/manifests/ingress/
"

# Configure DNS
echo "🌐 Configuring DNS records..."
python3 << EOF
import requests
import json

api_key = "$DNSIMPLE_API_KEY"
domain = "sophia-intel.ai"
instance_ip = "$INSTANCE_IP"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Get account ID
accounts_response = requests.get("https://api.dnsimple.com/v2/accounts", headers=headers)
if accounts_response.status_code == 200:
    account_id = accounts_response.json()["data"][0]["id"]
    print(f"✅ Account ID: {account_id}")
    
    # DNS records to create/update
    records = [
        {"name": "", "type": "A", "content": instance_ip},  # apex domain
        {"name": "www", "type": "A", "content": instance_ip},
        {"name": "app", "type": "A", "content": instance_ip},
        {"name": "api", "type": "A", "content": instance_ip}
    ]
    
    for record in records:
        # Check if record exists
        list_response = requests.get(
            f"https://api.dnsimple.com/v2/{account_id}/zones/{domain}/records",
            headers=headers,
            params={"name": record["name"], "type": record["type"]}
        )
        
        if list_response.status_code == 200:
            existing_records = list_response.json()["data"]
            
            if existing_records:
                # Update existing record
                record_id = existing_records[0]["id"]
                update_response = requests.patch(
                    f"https://api.dnsimple.com/v2/{account_id}/zones/{domain}/records/{record_id}",
                    headers=headers,
                    json={"content": record["content"]}
                )
                if update_response.status_code == 200:
                    print(f"✅ Updated {record['name'] or '@'}.{domain} -> {instance_ip}")
                else:
                    print(f"❌ Failed to update {record['name']}: {update_response.text}")
            else:
                # Create new record
                create_response = requests.post(
                    f"https://api.dnsimple.com/v2/{account_id}/zones/{domain}/records",
                    headers=headers,
                    json=record
                )
                if create_response.status_code == 201:
                    print(f"✅ Created {record['name'] or '@'}.{domain} -> {instance_ip}")
                else:
                    print(f"❌ Failed to create {record['name']}: {create_response.text}")
        else:
            print(f"❌ Failed to list records: {list_response.text}")
else:
    print(f"❌ Failed to get account: {accounts_response.text}")
EOF

echo ""
echo "🎉 SOPHIA MVP Deployment Complete!"
echo "=================================="
echo "🌐 Dashboard: https://www.sophia-intel.ai"
echo "🔗 App: https://app.sophia-intel.ai"
echo "⚡ API: https://api.sophia-intel.ai"
echo "🖥️  Instance: $INSTANCE_IP"
echo ""
echo "📋 Next Steps:"
echo "1. Wait 5-10 minutes for DNS propagation"
echo "2. Test all endpoints"
echo "3. Monitor logs: ssh -i $SSH_KEY_PATH ubuntu@$INSTANCE_IP 'docker logs sophia-api'"
echo "4. Check K8s status: ssh -i $SSH_KEY_PATH ubuntu@$INSTANCE_IP 'sudo k3s kubectl get pods -n sophia-mvp'"

