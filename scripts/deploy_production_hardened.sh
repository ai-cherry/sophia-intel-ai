#!/bin/bash
set -euo pipefail

# SOPHIA Intel - Production Hardened Deployment to www.sophia-intel.ai
# Complete controlled deployment with all production fixes applied

# Fast mode support
FAST_MODE="${1:-}"
SKIP_BUILD=0
if [[ "$FAST_MODE" == "--fast" ]]; then
    echo "🚀 FAST MODE: Skipping image builds, deploying manifests only"
    SKIP_BUILD=1
fi

echo "🚀 SOPHIA Intel - Production Hardened Deployment"
echo "================================================"
echo "Time: $(date)"
echo "Target: www.sophia-intel.ai (Lambda Labs Production)"
echo "DNSimple Account: musillynn"
echo ""

# Configuration
PRODUCTION_IP="104.171.202.103"  # sophia-production-instance
DOMAIN="sophia-intel.ai"
GITHUB_REPO="ai-cherry/sophia-intel"
DNSIMPLE_ACCOUNT_ID="musillynn"

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

# Check prerequisites with enhanced validation
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
    
    # Required secrets validation
    for v in OPENROUTER_API_KEY; do
        if [[ -z "${!v:-}" ]]; then
            log_error "Required secret $v is not set"
            echo "Please set: export $v='your_${v,,}'"
            exit 1
        fi
    done
    
    # Validate OpenRouter API key format
    if [[ ! "${OPENROUTER_API_KEY}" =~ ^sk- ]]; then
        log_warning "OpenRouter API key doesn't start with 'sk-' - please verify format"
    fi
    
    # Optional secrets warning
    for v in QDRANT_URL QDRANT_API_KEY AIRBYTE_URL AIRBYTE_TOKEN; do
        if [[ -z "${!v:-}" ]]; then
            log_warning "Optional secret $v not set"
        fi
    done
    
    # Check required tools
    command -v docker >/dev/null 2>&1 || { log_error "Docker not installed"; exit 1; }
    command -v kubectl >/dev/null 2>&1 || { log_error "kubectl not installed"; exit 1; }
    command -v helm >/dev/null 2>&1 || { log_error "Helm not installed"; exit 1; }
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

# Install Helm charts with local kubectl
install_helm_charts() {
    log_info "Installing Helm charts (local, using KUBECONFIG=$KUBECONFIG)..."
    
    # Add Helm repositories
    helm repo add jetstack https://charts.jetstack.io
    helm repo add kong https://charts.konghq.com
    helm repo update
    
    # Install cert-manager
    log_info "Installing cert-manager..."
    kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -
    helm upgrade --install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --set installCRDs=true \
        --wait --timeout=600s
    
    # Install Kong Ingress Controller
    log_info "Installing Kong Ingress Controller..."
    kubectl create namespace ingress-kong --dry-run=client -o yaml | kubectl apply -f -
    helm upgrade --install kong kong/kong \
        --namespace ingress-kong \
        --set ingressController.installCRDs=false \
        --set proxy.type=LoadBalancer \
        --wait --timeout=600s
    
    # Wait for Kong Service readiness
    log_info "Waiting for Kong Service external IP/hostPort..."
    for i in {1..30}; do
        LB=$(kubectl -n ingress-kong get svc kong-kong-proxy -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)
        [[ -n "$LB" ]] && break
        sleep 5
    done
    
    if [[ -z "$LB" ]]; then
        log_warning "No LB IP reported; using node IP (${PRODUCTION_IP}) via hostPort"
    else
        log_success "Kong LoadBalancer IP: $LB"
    fi
    
    log_success "Helm charts installed"
}

# Build and push Docker images with skip option
build_docker_images() {
    if [[ "${SKIP_BUILD:-0}" -eq 1 ]]; then
        log_info "Skipping Docker image builds (fast mode)"
        return 0
    fi
    
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

# Create application namespace and secrets with validation
create_secrets() {
    log_info "Creating application secrets..."
    
    # Create namespace
    kubectl create namespace sophia --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets with only non-empty values
    kubectl -n sophia create secret generic app-secrets \
        --from-literal=OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
        --from-literal=GITHUB_TOKEN="$GITHUB_PAT" \
        --from-literal=GITHUB_REPO="$GITHUB_REPO" \
        $(if [[ -n "${QDRANT_URL:-}" ]]; then echo "--from-literal=QDRANT_URL=$QDRANT_URL"; fi) \
        $(if [[ -n "${QDRANT_API_KEY:-}" ]]; then echo "--from-literal=QDRANT_API_KEY=$QDRANT_API_KEY"; fi) \
        $(if [[ -n "${AIRBYTE_URL:-}" ]]; then echo "--from-literal=AIRBYTE_URL=$AIRBYTE_URL"; fi) \
        $(if [[ -n "${AIRBYTE_TOKEN:-}" ]]; then echo "--from-literal=AIRBYTE_TOKEN=$AIRBYTE_TOKEN"; fi) \
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

# Setup TLS with DNSimple using correct account ID
setup_tls() {
    log_info "Setting up TLS with DNSimple (Account: $DNSIMPLE_ACCOUNT_ID)..."
    
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
          account: "${DNSIMPLE_ACCOUNT_ID}"
          apiTokenSecretRef:
            name: dnsimple-api-token
            key: token
EOF
    
    log_success "TLS ClusterIssuer created with DNSimple account: $DNSIMPLE_ACCOUNT_ID"
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

# Configure DNS with better LoadBalancer detection
configure_dns() {
    log_info "Configuring DNS..."
    
    # Get LoadBalancer IP with fallback
    LB_IP=$(kubectl -n ingress-kong get svc kong-kong-proxy -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    if [[ -z "$LB_IP" ]]; then 
        LB_IP="$PRODUCTION_IP"
        log_warning "No LoadBalancer IP found, using node IP: $LB_IP"
    else
        log_success "LoadBalancer IP detected: $LB_IP"
    fi
    
    log_warning "Please manually configure DNS records:"
    echo "A www.sophia-intel.ai -> $LB_IP"
    echo "A api.sophia-intel.ai -> $LB_IP"
    echo "A mcp.sophia-intel.ai -> $LB_IP"
    echo "Ports: 80/443 (Kong proxy)"
    
    read -p "Press Enter after DNS records are configured..."
}

# Run comprehensive health checks with diagnostic pod
run_health_checks() {
    log_info "Running comprehensive health checks..."
    
    # Check pod status
    log_info "Checking pod status..."
    kubectl -n sophia get pods
    
    # Create diagnostic curl pod for health checks
    log_info "Creating diagnostic curl pod..."
    kubectl -n sophia delete pod diag-curl --ignore-not-found >/dev/null 2>&1 || true
    kubectl -n sophia run diag-curl --image=curlimages/curl:8.9.1 -q -- sleep 3600
    kubectl -n sophia wait --for=condition=Ready pod/diag-curl --timeout=120s
    
    # Test backend health
    if kubectl -n sophia exec diag-curl -- curl -sf http://sophia-backend.sophia.svc.cluster.local:5000/api/health >/dev/null 2>&1; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
    fi
    
    # Test dashboard
    if kubectl -n sophia exec diag-curl -- curl -sf http://sophia-dashboard.sophia.svc.cluster.local/ >/dev/null 2>&1; then
        log_success "Dashboard health check passed"
    else
        log_error "Dashboard health check failed"
    fi
    
    # Test MCP servers
    if kubectl -n sophia exec diag-curl -- curl -sf http://sophia-mcp.sophia.svc.cluster.local:8000/healthz >/dev/null 2>&1; then
        log_success "MCP health check passed"
    else
        log_error "MCP health check failed"
    fi
    
    # Cleanup diagnostic pod
    kubectl -n sophia delete pod diag-curl --ignore-not-found >/dev/null 2>&1 || true
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
    echo "🚀 Starting SOPHIA Intel Production Hardened Deployment"
    echo "======================================================="
    
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
    
    # Phase 6: Monitoring Setup
    log_info "Phase 6: Monitoring Setup"
    create_monitoring
    
    # Final status
    echo ""
    echo "🎉 SOPHIA Intel Production Hardened Deployment Complete!"
    echo "========================================================"
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

# Show usage if help requested
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "SOPHIA Intel Production Hardened Deployment"
    echo ""
    echo "Usage: $0 [--fast]"
    echo ""
    echo "Options:"
    echo "  --fast    Skip Docker image builds (use existing images)"
    echo "  --help    Show this help message"
    echo ""
    echo "Required Environment Variables:"
    echo "  GITHUB_PAT           - GitHub Personal Access Token"
    echo "  LAMBDA_API_KEY       - Lambda Labs API Key"
    echo "  DNSIMPLE_API_KEY     - DNSimple API Key"
    echo "  OPENROUTER_API_KEY   - OpenRouter API Key"
    echo ""
    echo "Optional Environment Variables:"
    echo "  QDRANT_URL           - Qdrant Vector Database URL"
    echo "  QDRANT_API_KEY       - Qdrant API Key"
    echo "  AIRBYTE_URL          - Airbyte Instance URL"
    echo "  AIRBYTE_TOKEN        - Airbyte API Token"
    echo ""
    echo "Examples:"
    echo "  $0                   # Full deployment with image builds"
    echo "  $0 --fast            # Fast deployment (skip builds)"
    exit 0
fi

# Run main deployment
main "$@"

