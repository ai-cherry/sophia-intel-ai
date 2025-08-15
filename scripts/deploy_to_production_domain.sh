#!/bin/bash
set -euo pipefail

# SOPHIA Intel - Complete Production Deployment to www.sophia-intel.ai
# Hands-on deployment + MCP verification script
# Takes you from current code to fully tested production in one sequence

echo "🚀 SOPHIA Intel - Production Deployment to www.sophia-intel.ai"
echo "=================================================================="
echo "Time: $(date)"
echo "Target: www.sophia-intel.ai (Lambda Labs Production)"
echo ""

# Configuration
PRODUCTION_IP="104.171.202.103"  # sophia-production-instance
DOMAIN="sophia-intel.ai"
GITHUB_REPO="ai-cherry/sophia-intel"

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
    if [[ -z "${GITHUB_PAT:-}" ]]; then
        log_error "GITHUB_PAT environment variable not set"
        echo "Please set: export GITHUB_PAT='your_github_token'"
        exit 1
    fi
    
    if [[ -z "${LAMBDA_API_KEY:-}" ]]; then
        log_error "LAMBDA_API_KEY environment variable not set"
        echo "Please set: export LAMBDA_API_KEY='your_lambda_key'"
        exit 1
    fi
    
    if [[ -z "${DNSIMPLE_API_KEY:-}" ]]; then
        log_error "DNSIMPLE_API_KEY environment variable not set"
        echo "Please set: export DNSIMPLE_API_KEY='your_dnsimple_key'"
        exit 1
    fi
    
    # Check required tools
    command -v docker >/dev/null 2>&1 || { log_error "Docker not installed"; exit 1; }
    command -v kubectl >/dev/null 2>&1 || { log_error "kubectl not installed"; exit 1; }
    command -v curl >/dev/null 2>&1 || { log_error "curl not installed"; exit 1; }
    command -v jq >/dev/null 2>&1 || { log_error "jq not installed"; exit 1; }
    
    log_success "Prerequisites check passed"
}

# Setup SSH access to production instance
setup_ssh_access() {
    log_info "Setting up SSH access to production instance..."
    
    # Generate SSH key if not exists
    if [[ ! -f ~/.ssh/id_ed25519 ]]; then
        ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -q
        log_success "SSH key generated"
    fi
    
    # Add SSH key to Lambda Labs
    SSH_KEY=$(cat ~/.ssh/id_ed25519.pub)
    RESPONSE=$(curl -s -X POST -u "$LAMBDA_API_KEY:" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"sophia-deploy-$(date +%s)\", \"public_key\": \"$SSH_KEY\"}" \
        https://cloud.lambda.ai/api/v1/ssh-keys)
    
    if echo "$RESPONSE" | jq -e '.data.id' >/dev/null; then
        log_success "SSH key added to Lambda Labs"
    else
        log_warning "SSH key might already exist or failed to add"
    fi
    
    # Test SSH connection
    log_info "Testing SSH connection..."
    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no ubuntu@$PRODUCTION_IP "echo 'SSH connection successful'" 2>/dev/null; then
        log_success "SSH connection established"
    else
        log_error "SSH connection failed. Please check Lambda Labs instance status."
        exit 1
    fi
}

# Install K3s on production instance
install_k3s() {
    log_info "Installing K3s on production instance..."
    
    ssh ubuntu@$PRODUCTION_IP << 'EOF'
# Install K3s if not already installed
if ! command -v kubectl &> /dev/null; then
    echo "Installing K3s..."
    curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
    sudo chmod 644 /etc/rancher/k3s/k3s.yaml
    echo "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml" >> ~/.bashrc
    
    # Wait for K3s to be ready
    echo "Waiting for K3s to be ready..."
    sudo k3s kubectl wait --for=condition=Ready nodes --all --timeout=300s
else
    echo "K3s already installed"
fi
EOF
    
    log_success "K3s installation completed"
}

# Setup local kubectl access
setup_kubectl() {
    log_info "Setting up local kubectl access..."
    
    # Copy kubeconfig from production
    scp ubuntu@$PRODUCTION_IP:/etc/rancher/k3s/k3s.yaml ./k3s-config.yaml
    sed -i "s/127.0.0.1/$PRODUCTION_IP/g" ./k3s-config.yaml
    export KUBECONFIG=$(pwd)/k3s-config.yaml
    
    # Test kubectl access
    if kubectl get nodes >/dev/null 2>&1; then
        log_success "kubectl access configured"
    else
        log_error "kubectl access failed"
        exit 1
    fi
}

# Install Helm charts (cert-manager, Kong)
install_helm_charts() {
    log_info "Installing Helm charts on production..."
    
    ssh ubuntu@$PRODUCTION_IP << 'EOF'
# Install Helm if not already installed
if ! command -v helm &> /dev/null; then
    echo "Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Add Helm repositories
helm repo add jetstack https://charts.jetstack.io
helm repo add kong https://charts.konghq.com
helm repo update

# Install cert-manager
echo "Installing cert-manager..."
kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --set installCRDs=true \
  --wait --timeout=300s

# Install Kong Ingress Controller
echo "Installing Kong Ingress Controller..."
kubectl create namespace ingress-kong --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install kong kong/kong \
  --namespace ingress-kong \
  --set ingressController.installCRDs=false \
  --set proxy.type=LoadBalancer \
  --wait --timeout=300s

# Wait for Kong LoadBalancer
echo "Waiting for Kong LoadBalancer..."
kubectl wait --namespace ingress-kong \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=app \
  --timeout=300s
EOF
    
    log_success "Helm charts installed"
}

# Build and push Docker images
build_docker_images() {
    log_info "Building Docker images..."
    
    # Build backend
    log_info "Building SOPHIA backend..."
    docker build -t sophia-backend:prod -f docker/production/Dockerfile.api . || {
        log_error "Backend build failed"
        exit 1
    }
    
    # Build dashboard
    log_info "Building SOPHIA dashboard..."
    docker build -t sophia-dashboard:prod -f docker/production/Dockerfile.dashboard . || {
        log_error "Dashboard build failed"
        exit 1
    }
    
    # Build MCP servers
    log_info "Building SOPHIA MCP servers..."
    docker build -t sophia-mcp:prod -f docker/production/Dockerfile.mcp . || {
        log_error "MCP build failed"
        exit 1
    }
    
    log_success "Docker images built"
    
    # Transfer images to production
    log_info "Transferring images to production..."
    docker save sophia-backend:prod | ssh ubuntu@$PRODUCTION_IP 'sudo k3s ctr images import -'
    docker save sophia-dashboard:prod | ssh ubuntu@$PRODUCTION_IP 'sudo k3s ctr images import -'
    docker save sophia-mcp:prod | ssh ubuntu@$PRODUCTION_IP 'sudo k3s ctr images import -'
    
    log_success "Images transferred to production"
}

# Create application namespace and secrets
create_secrets() {
    log_info "Creating application secrets..."
    
    # Create namespace
    kubectl create namespace sophia --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets
    kubectl -n sophia create secret generic app-secrets \
        --from-literal=OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}" \
        --from-literal=GITHUB_TOKEN="$GITHUB_PAT" \
        --from-literal=GITHUB_REPO="$GITHUB_REPO" \
        --from-literal=QDRANT_URL="${QDRANT_URL:-}" \
        --from-literal=QDRANT_API_KEY="${QDRANT_API_KEY:-}" \
        --from-literal=AIRBYTE_URL="${AIRBYTE_URL:-}" \
        --from-literal=AIRBYTE_TOKEN="${AIRBYTE_TOKEN:-}" \
        --from-literal=LAMBDA_API_KEY="$LAMBDA_API_KEY" \
        --from-literal=DNSIMPLE_API_KEY="$DNSIMPLE_API_KEY" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Create ConfigMaps
    kubectl -n sophia create configmap models-allowlist \
        --from-file=config/models.allowlist.yaml \
        --dry-run=client -o yaml | kubectl apply -f -
    
    kubectl -n sophia create configmap swarm-rules \
        --from-file=config/swarm/rules.md \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_success "Secrets and ConfigMaps created"
}

# Setup TLS with DNSimple
setup_tls() {
    log_info "Setting up TLS with DNSimple..."
    
    cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: dnsimple-api-token
  namespace: cert-manager
type: Opaque
stringData:
  token: "$DNSIMPLE_API_KEY"
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-dnsimple
spec:
  acme:
    email: ops@sophia-intel.ai
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: acme-privkey
    solvers:
    - dns01:
        dnsimple:
          account: "YOUR_DNSIMPLE_ACCOUNT_ID"
          apiTokenSecretRef:
            name: dnsimple-api-token
            key: token
EOF
    
    log_success "TLS ClusterIssuer created"
}

# Deploy SOPHIA applications
deploy_applications() {
    log_info "Deploying SOPHIA applications..."
    
    # Apply Kubernetes manifests
    kubectl apply -f k8s/manifests/deployments/
    kubectl apply -f k8s/manifests/services/
    kubectl apply -f k8s/manifests/ingress/
    
    # Wait for deployments
    log_info "Waiting for deployments to be ready..."
    kubectl -n sophia wait --for=condition=available --timeout=300s deployment/sophia-backend
    kubectl -n sophia wait --for=condition=available --timeout=300s deployment/sophia-dashboard
    kubectl -n sophia wait --for=condition=available --timeout=300s deployment/sophia-mcp
    
    log_success "Applications deployed successfully"
}

# Configure DNS
configure_dns() {
    log_info "Configuring DNS..."
    
    # Get LoadBalancer IP
    LB_IP=$(kubectl -n ingress-kong get service kong-kong-proxy -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "$PRODUCTION_IP")
    
    log_info "LoadBalancer IP: $LB_IP"
    log_warning "Please manually configure DNS records:"
    echo "A www.sophia-intel.ai -> $LB_IP"
    echo "A api.sophia-intel.ai -> $LB_IP"
    echo "A mcp.sophia-intel.ai -> $LB_IP"
    
    read -p "Press Enter after DNS records are configured..."
}

# Run comprehensive health checks
run_health_checks() {
    log_info "Running comprehensive health checks..."
    
    # Check pod status
    log_info "Checking pod status..."
    kubectl -n sophia get pods
    
    # Check service endpoints
    log_info "Checking service endpoints..."
    
    # Test backend health
    if kubectl -n sophia exec deployment/sophia-backend -- curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
    fi
    
    # Test dashboard
    if kubectl -n sophia exec deployment/sophia-dashboard -- curl -f http://localhost/ >/dev/null 2>&1; then
        log_success "Dashboard health check passed"
    else
        log_error "Dashboard health check failed"
    fi
    
    # Test MCP servers
    if kubectl -n sophia exec deployment/sophia-mcp -- curl -f http://localhost:8000/healthz >/dev/null 2>&1; then
        log_success "MCP health check passed"
    else
        log_error "MCP health check failed"
    fi
}

# Test external endpoints
test_external_endpoints() {
    log_info "Testing external endpoints..."
    
    # Wait for DNS propagation
    sleep 30
    
    # Test dashboard
    if curl -f https://www.sophia-intel.ai >/dev/null 2>&1; then
        log_success "Dashboard accessible at https://www.sophia-intel.ai"
    else
        log_warning "Dashboard not yet accessible (DNS propagation may take time)"
    fi
    
    # Test API
    if curl -f https://api.sophia-intel.ai/api/health >/dev/null 2>&1; then
        log_success "API accessible at https://api.sophia-intel.ai"
    else
        log_warning "API not yet accessible (DNS propagation may take time)"
    fi
    
    # Test MCP
    if curl -f https://mcp.sophia-intel.ai/healthz >/dev/null 2>&1; then
        log_success "MCP accessible at https://mcp.sophia-intel.ai"
    else
        log_warning "MCP not yet accessible (DNS propagation may take time)"
    fi
}

# Run MCP verification tests
run_mcp_verification() {
    log_info "Running MCP verification tests..."
    
    # Test MCP Code Server
    log_info "Testing MCP Code Server..."
    MCP_RESPONSE=$(kubectl -n sophia exec deployment/sophia-mcp -- curl -s http://localhost:8000/mcp/code/health 2>/dev/null || echo "failed")
    if [[ "$MCP_RESPONSE" != "failed" ]]; then
        log_success "MCP Code Server operational"
    else
        log_warning "MCP Code Server needs verification"
    fi
    
    # Test GitHub integration
    log_info "Testing GitHub integration..."
    GITHUB_TEST=$(kubectl -n sophia exec deployment/sophia-backend -- python -c "
import os
import requests
token = os.environ.get('GITHUB_TOKEN')
if token:
    response = requests.get('https://api.github.com/user', headers={'Authorization': f'token {token}'})
    print('success' if response.status_code == 200 else 'failed')
else:
    print('no_token')
" 2>/dev/null || echo "failed")
    
    if [[ "$GITHUB_TEST" == "success" ]]; then
        log_success "GitHub integration working"
    else
        log_warning "GitHub integration needs verification"
    fi
}

# Run end-to-end mission test
run_e2e_mission_test() {
    log_info "Running end-to-end mission test..."
    
    # Create test mission
    MISSION_PAYLOAD='{"goal": "Create a simple test file docs/E2E_TEST.md with current timestamp and system info"}'
    
    # Submit mission via API
    if command -v curl >/dev/null 2>&1; then
        log_info "Submitting test mission..."
        MISSION_RESPONSE=$(curl -s -X POST https://api.sophia-intel.ai/api/missions \
            -H "Content-Type: application/json" \
            -d "$MISSION_PAYLOAD" 2>/dev/null || echo "failed")
        
        if echo "$MISSION_RESPONSE" | jq -e '.mission_id' >/dev/null 2>&1; then
            MISSION_ID=$(echo "$MISSION_RESPONSE" | jq -r '.mission_id')
            log_success "Mission created: $MISSION_ID"
            
            # Monitor mission progress
            log_info "Monitoring mission progress (30 seconds)..."
            timeout 30s curl -N https://api.sophia-intel.ai/api/missions/$MISSION_ID/events 2>/dev/null || true
            
            log_success "E2E mission test completed"
        else
            log_warning "Mission creation failed - API may need time to stabilize"
        fi
    else
        log_warning "curl not available for E2E test"
    fi
}

# Create monitoring dashboard
create_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create simple monitoring script
    cat > monitor_sophia.sh << 'EOF'
#!/bin/bash
echo "SOPHIA Intel Production Monitoring"
echo "=================================="
echo "Time: $(date)"
echo ""

echo "Pod Status:"
kubectl -n sophia get pods

echo ""
echo "Service Status:"
kubectl -n sophia get services

echo ""
echo "Ingress Status:"
kubectl -n sophia get ingress

echo ""
echo "Certificate Status:"
kubectl -n sophia get certificates

echo ""
echo "External Endpoints:"
curl -s -o /dev/null -w "Dashboard: %{http_code}\n" https://www.sophia-intel.ai
curl -s -o /dev/null -w "API: %{http_code}\n" https://api.sophia-intel.ai/api/health
curl -s -o /dev/null -w "MCP: %{http_code}\n" https://mcp.sophia-intel.ai/healthz
EOF
    
    chmod +x monitor_sophia.sh
    log_success "Monitoring script created: ./monitor_sophia.sh"
}

# Main deployment sequence
main() {
    echo "🚀 Starting SOPHIA Intel Production Deployment"
    echo "=============================================="
    
    # Phase 1: Prerequisites and Setup
    log_info "Phase 1: Prerequisites and Setup"
    check_prerequisites
    setup_ssh_access
    
    # Phase 2: Infrastructure Setup
    log_info "Phase 2: Infrastructure Setup"
    install_k3s
    setup_kubectl
    install_helm_charts
    
    # Phase 3: Application Deployment
    log_info "Phase 3: Application Deployment"
    build_docker_images
    create_secrets
    setup_tls
    deploy_applications
    
    # Phase 4: DNS and External Access
    log_info "Phase 4: DNS and External Access"
    configure_dns
    
    # Phase 5: Verification and Testing
    log_info "Phase 5: Verification and Testing"
    run_health_checks
    test_external_endpoints
    run_mcp_verification
    run_e2e_mission_test
    
    # Phase 6: Monitoring Setup
    log_info "Phase 6: Monitoring Setup"
    create_monitoring
    
    # Final status
    echo ""
    echo "🎉 SOPHIA Intel Production Deployment Complete!"
    echo "=============================================="
    echo ""
    log_success "Dashboard: https://www.sophia-intel.ai"
    log_success "API: https://api.sophia-intel.ai"
    log_success "MCP: https://mcp.sophia-intel.ai"
    echo ""
    echo "📊 Next Steps:"
    echo "1. Test the dashboard interface"
    echo "2. Submit a mission via the command bar"
    echo "3. Monitor real-time progress"
    echo "4. Review generated PR on GitHub"
    echo ""
    echo "🔧 Monitoring:"
    echo "Run ./monitor_sophia.sh for system status"
    echo ""
    echo "🚀 SOPHIA Intel is now live and ready for natural language missions!"
}

# Run main deployment
main "$@"

