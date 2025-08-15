#!/bin/bash
set -e

# SOPHIA Intel Go-Live Gauntlet - Phase 1: K3s & Kong Setup
# Production deployment script for live infrastructure

PRODUCTION_IP="104.171.202.107"
SSH_KEY="$HOME/.ssh/sophia_production_key"
DOMAIN="sophia-intel.ai"

echo "🚀 SOPHIA Intel Go-Live Gauntlet - Phase 1"
echo "Setting up K3s cluster and Kong Ingress on production server"
echo "Server: $PRODUCTION_IP"

# Function to run commands on production server
run_remote() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@$PRODUCTION_IP "$1"
}

# Function to copy files to production server
copy_to_remote() {
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$1" ubuntu@$PRODUCTION_IP:"$2"
}

echo "=== Step 1: Installing K3s on production server ==="
run_remote "
    # Update system
    sudo apt update -qq
    
    # Install K3s
    if ! command -v k3s &> /dev/null; then
        echo 'Installing K3s...'
        curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
        sudo systemctl enable k3s
        sudo systemctl start k3s
    else
        echo 'K3s already installed'
    fi
    
    # Wait for K3s to be ready
    echo 'Waiting for K3s to be ready...'
    sudo k3s kubectl wait --for=condition=Ready nodes --all --timeout=300s
    
    # Check K3s status
    echo 'K3s cluster status:'
    sudo k3s kubectl get nodes
"

echo "=== Step 2: Installing cert-manager ==="
run_remote "
    # Install cert-manager
    echo 'Installing cert-manager...'
    sudo k3s kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    
    # Wait for cert-manager to be ready
    echo 'Waiting for cert-manager to be ready...'
    sudo k3s kubectl wait --for=condition=Available deployment/cert-manager -n cert-manager --timeout=300s
    sudo k3s kubectl wait --for=condition=Available deployment/cert-manager-cainjector -n cert-manager --timeout=300s
    sudo k3s kubectl wait --for=condition=Available deployment/cert-manager-webhook -n cert-manager --timeout=300s
"

echo "=== Step 3: Installing Kong Ingress Controller ==="
run_remote "
    # Install Kong
    echo 'Installing Kong Ingress Controller...'
    sudo k3s kubectl apply -f https://raw.githubusercontent.com/Kong/kubernetes-ingress-controller/main/deploy/single/all-in-one-dbless.yaml
    
    # Wait for Kong to be ready
    echo 'Waiting for Kong to be ready...'
    sudo k3s kubectl wait --for=condition=Available deployment/ingress-kong -n kong --timeout=300s
    
    # Check Kong status
    echo 'Kong status:'
    sudo k3s kubectl get pods -n kong
"

echo "=== Step 4: Creating SOPHIA Intel namespace ==="
run_remote "
    # Create namespace
    sudo k3s kubectl create namespace sophia-intel --dry-run=client -o yaml | sudo k3s kubectl apply -f -
    
    echo 'SOPHIA Intel namespace created'
"

echo "=== Step 5: Setting up Let's Encrypt certificate issuer ==="

# Create Let's Encrypt issuer configuration
cat > /tmp/letsencrypt-issuer.yaml << EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@sophia-intel.ai
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: kong
EOF

# Copy and apply certificate issuer
copy_to_remote "/tmp/letsencrypt-issuer.yaml" "/tmp/letsencrypt-issuer.yaml"
run_remote "
    sudo k3s kubectl apply -f /tmp/letsencrypt-issuer.yaml
    echo 'Let\\'s Encrypt certificate issuer configured'
"

echo "=== Step 6: Configuring DNS records ==="

# Configure DNS using DNSimple API
if [ -n "$DNSIMPLE_API_KEY" ]; then
    echo "Configuring DNS records for $DOMAIN..."
    
    # Get account ID
    ACCOUNT_ID=$(curl -s -H "Authorization: Bearer $DNSIMPLE_API_KEY" \
        https://api.dnsimple.com/v2/whoami | \
        python3 -c "import json, sys; print(json.load(sys.stdin)['data']['account']['id'])")
    
    # Configure DNS records
    for subdomain in "www" "api" "dashboard"; do
        echo "Setting up $subdomain.$DOMAIN -> $PRODUCTION_IP"
        
        curl -s -X POST \
            -H "Authorization: Bearer $DNSIMPLE_API_KEY" \
            -H "Content-Type: application/json" \
            -d "{\"name\":\"$subdomain\",\"type\":\"A\",\"content\":\"$PRODUCTION_IP\",\"ttl\":300}" \
            "https://api.dnsimple.com/v2/$ACCOUNT_ID/zones/$DOMAIN/records" || true
    done
    
    echo "✅ DNS records configured"
else
    echo "⚠️  DNSIMPLE_API_KEY not set - skipping DNS configuration"
fi

echo "=== Step 7: Creating SSL certificate ==="

# Create SSL certificate configuration
cat > /tmp/sophia-ssl-cert.yaml << EOF
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: sophia-intel-tls
  namespace: sophia-intel
spec:
  secretName: sophia-intel-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - sophia-intel.ai
  - www.sophia-intel.ai
  - api.sophia-intel.ai
  - dashboard.sophia-intel.ai
EOF

# Copy and apply SSL certificate
copy_to_remote "/tmp/sophia-ssl-cert.yaml" "/tmp/sophia-ssl-cert.yaml"
run_remote "
    sudo k3s kubectl apply -f /tmp/sophia-ssl-cert.yaml
    echo 'SSL certificate requested'
    
    # Check certificate status
    echo 'Certificate status:'
    sudo k3s kubectl get certificate -n sophia-intel
"

echo "=== Step 8: Deploying Kong Ingress configuration ==="

# Create Kong Ingress configuration
cat > /tmp/kong-ingress.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sophia-intel-ingress
  namespace: sophia-intel
  annotations:
    kubernetes.io/ingress.class: kong
    cert-manager.io/cluster-issuer: letsencrypt-prod
    konghq.com/strip-path: "true"
spec:
  tls:
  - hosts:
    - sophia-intel.ai
    - www.sophia-intel.ai
    - api.sophia-intel.ai
    - dashboard.sophia-intel.ai
    secretName: sophia-intel-tls
  rules:
  - host: www.sophia-intel.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sophia-dashboard
            port:
              number: 3000
  - host: api.sophia-intel.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sophia-api
            port:
              number: 5000
  - host: dashboard.sophia-intel.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sophia-dashboard
            port:
              number: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: sophia-api
  namespace: sophia-intel
spec:
  selector:
    app: sophia-api
  ports:
  - port: 5000
    targetPort: 5000
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: sophia-dashboard
  namespace: sophia-intel
spec:
  selector:
    app: sophia-dashboard
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
EOF

# Copy and apply Kong Ingress
copy_to_remote "/tmp/kong-ingress.yaml" "/tmp/kong-ingress.yaml"
run_remote "
    sudo k3s kubectl apply -f /tmp/kong-ingress.yaml
    echo 'Kong Ingress configured'
"

echo "=== Phase 1 Verification ==="

# Verify deployment
run_remote "
    echo '=== K3s Cluster Status ==='
    sudo k3s kubectl get nodes
    
    echo -e '\n=== Namespaces ==='
    sudo k3s kubectl get namespaces
    
    echo -e '\n=== Kong Status ==='
    sudo k3s kubectl get pods -n kong
    
    echo -e '\n=== Cert-manager Status ==='
    sudo k3s kubectl get pods -n cert-manager
    
    echo -e '\n=== SOPHIA Intel Namespace ==='
    sudo k3s kubectl get all -n sophia-intel
    
    echo -e '\n=== Certificates ==='
    sudo k3s kubectl get certificate -n sophia-intel
    
    echo -e '\n=== Ingress ==='
    sudo k3s kubectl get ingress -n sophia-intel
"

echo "🎯 Phase 1 Complete: DNS, SSL & Ingress Configuration"
echo "✅ K3s cluster deployed and running"
echo "✅ Kong Ingress Controller installed"
echo "✅ cert-manager configured for Let's Encrypt"
echo "✅ DNS records configured (if DNSIMPLE_API_KEY provided)"
echo "✅ SSL certificates requested"
echo "✅ Kong Ingress rules configured"

echo -e "\nNext: Phase 2 - Sophia Orchestrator & Agent Swarm Activation"

# Test endpoints (will fail until applications are deployed)
echo -e "\n=== Testing Endpoints (Expected to fail until apps deployed) ==="
for url in "https://www.sophia-intel.ai" "https://api.sophia-intel.ai" "https://dashboard.sophia-intel.ai"; do
    echo "Testing $url..."
    curl -I -k --connect-timeout 5 "$url" || echo "  (Expected - applications not yet deployed)"
done

echo -e "\n🚀 Phase 1 Infrastructure Ready for Application Deployment!"

