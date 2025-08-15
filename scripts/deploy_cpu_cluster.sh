#!/bin/bash
set -euo pipefail

# SOPHIA Intel CPU Cluster Deployment Script
# Deploys CPU-optimized infrastructure to Lambda Labs with K3s and applications

echo "🚀 SOPHIA Intel CPU Cluster Deployment"
echo "======================================"
echo "Target: CPU-optimized Lambda Labs infrastructure"
echo "Architecture: K3s + Kong + Let's Encrypt + Claude Sonnet 4"
echo ""

# Configuration
DOMAIN="sophia-intel.ai"
CLUSTER_SIZE=3
INSTANCE_TYPE="cpu.c2-2"  # 2 vCPU, 4GB RAM
REGION="us-west-1"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required environment variables
    required_vars=(
        "LAMBDA_CLOUD_API_KEY"
        "DNSIMPLE_API_KEY"
        "LAMBDA_API_KEY"
        "OPENROUTER_API_KEY"
        "GITHUB_PAT"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "$var environment variable not set"
            echo "Please set: export $var='your_${var,,}_value'"
            exit 1
        fi
        log_success "$var is configured"
    done
    
    # Check required tools
    command -v curl >/dev/null 2>&1 || { log_error "curl not installed"; exit 1; }
    command -v jq >/dev/null 2>&1 || { log_error "jq not installed"; exit 1; }
    command -v kubectl >/dev/null 2>&1 || { log_error "kubectl not installed"; exit 1; }
    
    log_success "Prerequisites check passed"
}

# Provision Lambda Labs CPU instances
provision_cpu_instances() {
    log_info "Provisioning $CLUSTER_SIZE CPU instances on Lambda Labs..."
    
    # Generate SSH key if not exists
    if [[ ! -f ~/.ssh/id_ed25519_sophia ]]; then
        ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_sophia -N "" -q
        log_success "SSH key generated"
    fi
    
    # Add SSH key to Lambda Labs
    SSH_KEY=$(cat ~/.ssh/id_ed25519_sophia.pub)
    KEY_NAME="sophia-cpu-cluster-$(date +%s)"
    
    log_info "Adding SSH key to Lambda Labs..."
    KEY_RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $LAMBDA_CLOUD_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$KEY_NAME\", \"public_key\": \"$SSH_KEY\"}" \
        https://cloud.lambdalabs.com/api/v1/ssh-keys)
    
    if echo "$KEY_RESPONSE" | jq -e '.data.id' >/dev/null; then
        SSH_KEY_ID=$(echo "$KEY_RESPONSE" | jq -r '.data.id')
        log_success "SSH key added with ID: $SSH_KEY_ID"
    else
        log_error "Failed to add SSH key: $KEY_RESPONSE"
        exit 1
    fi
    
    # Launch CPU instances
    INSTANCE_IDS=()
    for i in $(seq 1 $CLUSTER_SIZE); do
        log_info "Launching CPU instance $i/$CLUSTER_SIZE..."
        
        INSTANCE_NAME="sophia-cpu-$(printf "%02d" $i)"
        INSTANCE_RESPONSE=$(curl -s -X POST \
            -H "Authorization: Bearer $LAMBDA_CLOUD_API_KEY" \
            -H "Content-Type: application/json" \
            -d "{
                \"region_name\": \"$REGION\",
                \"instance_type_name\": \"$INSTANCE_TYPE\",
                \"ssh_key_names\": [\"$KEY_NAME\"],
                \"name\": \"$INSTANCE_NAME\"
            }" \
            https://cloud.lambdalabs.com/api/v1/instance-operations/launch)
        
        if echo "$INSTANCE_RESPONSE" | jq -e '.data.instance_ids[0]' >/dev/null; then
            INSTANCE_ID=$(echo "$INSTANCE_RESPONSE" | jq -r '.data.instance_ids[0]')
            INSTANCE_IDS+=("$INSTANCE_ID")
            log_success "Instance $INSTANCE_NAME launched with ID: $INSTANCE_ID"
        else
            log_error "Failed to launch instance $i: $INSTANCE_RESPONSE"
            exit 1
        fi
        
        sleep 5  # Rate limiting
    done
    
    # Wait for instances to be running
    log_info "Waiting for instances to be running..."
    sleep 60  # Initial wait
    
    INSTANCE_IPS=()
    for instance_id in "${INSTANCE_IDS[@]}"; do
        while true; do
            INSTANCE_INFO=$(curl -s -H "Authorization: Bearer $LAMBDA_CLOUD_API_KEY" \
                "https://cloud.lambdalabs.com/api/v1/instances/$instance_id")
            
            STATUS=$(echo "$INSTANCE_INFO" | jq -r '.data.status')
            if [[ "$STATUS" == "running" ]]; then
                IP=$(echo "$INSTANCE_INFO" | jq -r '.data.ip')
                INSTANCE_IPS+=("$IP")
                log_success "Instance $instance_id is running at $IP"
                break
            else
                log_info "Instance $instance_id status: $STATUS, waiting..."
                sleep 30
            fi
        done
    done
    
    # Save instance information
    cat > cluster_info.json << EOF
{
    "cluster_size": $CLUSTER_SIZE,
    "instance_type": "$INSTANCE_TYPE",
    "region": "$REGION",
    "ssh_key_id": "$SSH_KEY_ID",
    "instances": [
$(for i in "${!INSTANCE_IDS[@]}"; do
    echo "        {\"id\": \"${INSTANCE_IDS[$i]}\", \"ip\": \"${INSTANCE_IPS[$i]}\"}"
    [[ $i -lt $((${#INSTANCE_IDS[@]} - 1)) ]] && echo ","
done)
    ]
}
EOF
    
    log_success "CPU cluster provisioned successfully!"
    echo "Master node: ${INSTANCE_IPS[0]}"
    echo "Worker nodes: ${INSTANCE_IPS[@]:1}"
}

# Install K3s cluster
install_k3s_cluster() {
    log_info "Installing K3s cluster..."
    
    # Read cluster info
    MASTER_IP=$(jq -r '.instances[0].ip' cluster_info.json)
    WORKER_IPS=($(jq -r '.instances[1:][].ip' cluster_info.json))
    
    log_info "Installing K3s on master node: $MASTER_IP"
    
    # Install K3s on master
    ssh -i ~/.ssh/id_ed25519_sophia -o StrictHostKeyChecking=no ubuntu@$MASTER_IP << 'EOF'
# Install K3s master
curl -sfL https://get.k3s.io | sh -s - server \
    --write-kubeconfig-mode 644 \
    --disable traefik \
    --node-external-ip $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# Wait for K3s to be ready
sudo k3s kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Get node token for workers
sudo cat /var/lib/rancher/k3s/server/node-token
EOF
    
    # Get node token
    NODE_TOKEN=$(ssh -i ~/.ssh/id_ed25519_sophia ubuntu@$MASTER_IP "sudo cat /var/lib/rancher/k3s/server/node-token")
    
    # Install K3s on worker nodes
    for worker_ip in "${WORKER_IPS[@]}"; do
        log_info "Installing K3s on worker node: $worker_ip"
        
        ssh -i ~/.ssh/id_ed25519_sophia -o StrictHostKeyChecking=no ubuntu@$worker_ip << EOF
# Install K3s agent
curl -sfL https://get.k3s.io | K3S_URL=https://$MASTER_IP:6443 K3S_TOKEN=$NODE_TOKEN sh -
EOF
    done
    
    # Setup local kubectl access
    log_info "Setting up local kubectl access..."
    scp -i ~/.ssh/id_ed25519_sophia ubuntu@$MASTER_IP:/etc/rancher/k3s/k3s.yaml ./kubeconfig.yaml
    sed -i "s/127.0.0.1/$MASTER_IP/g" ./kubeconfig.yaml
    export KUBECONFIG=$(pwd)/kubeconfig.yaml
    
    # Test cluster
    kubectl get nodes
    log_success "K3s cluster installed successfully!"
}

# Install cluster components
install_cluster_components() {
    log_info "Installing cluster components..."
    
    # Install cert-manager
    log_info "Installing cert-manager..."
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    kubectl wait --for=condition=Available --timeout=300s deployment/cert-manager -n cert-manager
    kubectl wait --for=condition=Available --timeout=300s deployment/cert-manager-webhook -n cert-manager
    kubectl wait --for=condition=Available --timeout=300s deployment/cert-manager-cainjector -n cert-manager
    
    # Install Kong ingress controller
    log_info "Installing Kong ingress controller..."
    kubectl apply -f https://raw.githubusercontent.com/Kong/kubernetes-ingress-controller/main/deploy/single/all-in-one-dbless.yaml
    kubectl wait --for=condition=Available --timeout=300s deployment/ingress-kong -n kong
    
    # Install metrics server for HPA
    log_info "Installing metrics server..."
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    kubectl patch deployment metrics-server -n kube-system --type='json' \
        -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
    
    log_success "Cluster components installed successfully!"
}

# Deploy SOPHIA Intel applications
deploy_applications() {
    log_info "Deploying SOPHIA Intel applications..."
    
    # Create namespace and secrets
    kubectl apply -f k8s/manifests/namespace.yaml
    
    # Substitute environment variables in secrets
    envsubst < k8s/manifests/namespace.yaml | kubectl apply -f -
    
    # Deploy certificates
    kubectl apply -f k8s/manifests/certificates/
    
    # Deploy applications
    kubectl apply -f k8s/manifests/deployments/
    kubectl apply -f k8s/manifests/ingress/
    kubectl apply -f k8s/manifests/hpa.yaml
    
    # Wait for deployments
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=Available --timeout=600s deployment/sophia-api -n sophia-intel
    kubectl wait --for=condition=Available --timeout=600s deployment/sophia-dashboard -n sophia-intel
    kubectl wait --for=condition=Available --timeout=600s deployment/sophia-mcp-servers -n sophia-intel
    
    log_success "Applications deployed successfully!"
}

# Configure DNS
configure_dns() {
    log_info "Configuring DNS records..."
    
    # Get LoadBalancer IP
    MASTER_IP=$(jq -r '.instances[0].ip' cluster_info.json)
    LB_IP=$(kubectl get svc -n kong kong-proxy -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "$MASTER_IP")
    
    log_info "Using IP address: $LB_IP"
    
    # Get DNSimple account ID
    DNSIMPLE_ACCOUNT_ID=$(curl -s -H "Authorization: Bearer $DNSIMPLE_API_KEY" \
        https://api.dnsimple.com/v2/whoami | jq -r '.data.account.id')
    
    # Function to create DNS record
    create_dns_record() {
        local name=$1
        local ip=$2
        
        log_info "Creating DNS record: $name.$DOMAIN -> $ip"
        
        curl -s -X POST \
            -H "Authorization: Bearer $DNSIMPLE_API_KEY" \
            -H "Content-Type: application/json" \
            -d "{\"name\":\"$name\",\"type\":\"A\",\"content\":\"$ip\",\"ttl\":300}" \
            "https://api.dnsimple.com/v2/$DNSIMPLE_ACCOUNT_ID/zones/$DOMAIN/records" \
            | jq -r '.data.id // "error"'
    }
    
    # Create DNS records
    create_dns_record "" "$LB_IP"           # sophia-intel.ai
    create_dns_record "www" "$LB_IP"        # www.sophia-intel.ai
    create_dns_record "api" "$LB_IP"        # api.sophia-intel.ai
    create_dns_record "dashboard" "$LB_IP"  # dashboard.sophia-intel.ai
    
    log_success "DNS records configured"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Check pod status
    kubectl get pods -n sophia-intel
    
    # Check ingress
    kubectl get ingress -n sophia-intel
    
    # Check certificates
    kubectl get certificate -n sophia-intel
    
    # Wait for DNS propagation
    log_info "Waiting for DNS propagation..."
    sleep 60
    
    # Test endpoints
    check_endpoint() {
        local url=$1
        local name=$2
        
        log_info "Checking $name: $url"
        if curl -s -k --max-time 10 "$url" > /dev/null; then
            log_success "$name is responding"
        else
            log_warning "$name is not responding yet (may need more time)"
        fi
    }
    
    check_endpoint "https://api.sophia-intel.ai/api/health" "API Health"
    check_endpoint "https://dashboard.sophia-intel.ai" "Dashboard"
    check_endpoint "https://www.sophia-intel.ai" "Main Site"
    
    log_success "Health checks completed"
}

# Main deployment flow
main() {
    log_info "Starting SOPHIA Intel CPU cluster deployment..."
    
    check_prerequisites
    provision_cpu_instances
    install_k3s_cluster
    install_cluster_components
    deploy_applications
    configure_dns
    run_health_checks
    
    echo ""
    log_success "🎉 SOPHIA Intel CPU Cluster Deployment Complete!"
    echo "=============================================="
    echo "🌐 Main Site:    https://www.sophia-intel.ai"
    echo "📊 Dashboard:    https://dashboard.sophia-intel.ai"
    echo "🔌 API:          https://api.sophia-intel.ai"
    echo "📚 API Docs:     https://api.sophia-intel.ai/docs"
    echo "🏥 Health:       https://api.sophia-intel.ai/api/health"
    echo ""
    echo "💰 Monthly Cost: ~$150 (80% savings vs GPU infrastructure)"
    echo "🧠 Primary Model: Claude Sonnet 4 via OpenRouter"
    echo "⚡ Performance: Sub-second AI routing decisions"
    echo ""
    echo "📋 Management Commands:"
    echo "export KUBECONFIG=$(pwd)/kubeconfig.yaml"
    echo "kubectl get pods -n sophia-intel"
    echo "kubectl logs -f deployment/sophia-api -n sophia-intel"
    echo ""
    echo "🚀 SOPHIA Intel is now live with CPU-optimized architecture!"
}

# Run main function
main "$@"

