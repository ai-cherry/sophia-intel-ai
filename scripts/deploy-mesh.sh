#!/bin/bash

# Sophia-Sophia Service Mesh Deployment Script
# Installs Istio and deploys the consolidated system with service mesh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ISTIO_VERSION=${ISTIO_VERSION:-"1.20.0"}
NAMESPACE_ISTIO="istio-system"
NAMESPACE_ARTEMIS="sophia-mesh"
NAMESPACE_SOPHIA="sophia-mesh"
NAMESPACE_SHARED="shared-services"
HELM_RELEASE="sophia-sophia"
HELM_CHART="./helm/sophia-sophia"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi

    # Check helm
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        exit 1
    fi

    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    log_info "Prerequisites check passed"
}

install_istio() {
    log_info "Installing Istio ${ISTIO_VERSION}..."

    # Download istioctl if not present
    if ! command -v istioctl &> /dev/null; then
        log_info "Downloading istioctl..."
        curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh -
        export PATH=$PWD/istio-${ISTIO_VERSION}/bin:$PATH
    fi

    # Check if Istio is already installed
    if kubectl get namespace ${NAMESPACE_ISTIO} &> /dev/null; then
        log_warning "Istio namespace already exists"
        read -p "Do you want to reinstall Istio? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Skipping Istio installation"
            return
        fi
    fi

    # Create Istio namespace
    kubectl create namespace ${NAMESPACE_ISTIO} --dry-run=client -o yaml | kubectl apply -f -

    # Apply Istio operator configuration
    log_info "Applying Istio operator configuration..."
    kubectl apply -f infrastructure/istio/base/istio-operator.yaml

    # Install Istio using operator
    istioctl install --set values.pilot.env.PILOT_ENABLE_WORKLOAD_ENTRY_AUTOREGISTRATION=true \
                     --set values.global.meshID=sophia-sophia \
                     --set values.global.multiCluster.clusterName=primary \
                     --set values.global.network=sophia-sophia-network \
                     -y

    # Wait for Istio to be ready
    log_info "Waiting for Istio components to be ready..."
    kubectl wait --for=condition=Ready pod -l app=istiod -n ${NAMESPACE_ISTIO} --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=istio-ingressgateway -n ${NAMESPACE_ISTIO} --timeout=300s

    log_info "Istio installed successfully"
}

create_namespaces() {
    log_info "Creating namespaces..."

    kubectl apply -f infrastructure/istio/base/namespace.yaml

    # Label namespaces for Istio injection
    kubectl label namespace ${NAMESPACE_ARTEMIS} istio-injection=enabled --overwrite
    kubectl label namespace ${NAMESPACE_SOPHIA} istio-injection=enabled --overwrite
    kubectl label namespace ${NAMESPACE_SHARED} istio-injection=enabled --overwrite

    log_info "Namespaces created and configured"
}

apply_istio_configs() {
    log_info "Applying Istio configurations..."

    # Apply networking configurations
    log_info "Applying virtual services..."
    kubectl apply -f infrastructure/istio/networking/sophia-virtual-service.yaml
    kubectl apply -f infrastructure/istio/networking/sophia-virtual-service.yaml

    log_info "Applying destination rules..."
    kubectl apply -f infrastructure/istio/networking/sophia-destination-rule.yaml
    kubectl apply -f infrastructure/istio/networking/sophia-destination-rule.yaml

    log_info "Applying service entries..."
    kubectl apply -f infrastructure/istio/networking/service-entries.yaml

    # Apply security configurations
    log_info "Applying security policies..."
    kubectl apply -f infrastructure/istio/security/peer-authentication.yaml
    kubectl apply -f infrastructure/istio/security/authorization-policies.yaml

    # Apply traffic management
    log_info "Applying traffic management policies..."
    kubectl apply -f infrastructure/istio/traffic/gateway.yaml
    kubectl apply -f infrastructure/istio/traffic/rate-limiting.yaml

    # Apply observability
    log_info "Applying observability configuration..."
    kubectl apply -f infrastructure/istio/observability/telemetry.yaml
    kubectl apply -f infrastructure/istio/observability/prometheus-config.yaml
    kubectl apply -f infrastructure/istio/observability/grafana-dashboards.yaml

    log_info "Istio configurations applied"
}

deploy_applications() {
    log_info "Deploying applications..."

    # Apply ConfigMaps
    log_info "Applying ConfigMaps..."
    kubectl apply -f k8s/shared/configmap.yaml

    # Deploy using Helm
    log_info "Installing Helm chart..."
    helm upgrade --install ${HELM_RELEASE} ${HELM_CHART} \
        --namespace ${NAMESPACE_ISTIO} \
        --create-namespace \
        --values ${HELM_CHART}/values.yaml \
        --wait \
        --timeout 10m

    # Alternative: Deploy using kubectl (if not using Helm)
    # log_info "Deploying Sophia..."
    # kubectl apply -f k8s/sophia/deployment.yaml

    # log_info "Deploying Sophia..."
    # kubectl apply -f k8s/sophia/deployment.yaml

    log_info "Applications deployed successfully"
}

configure_ingress() {
    log_info "Configuring ingress..."

    # Get ingress gateway external IP/hostname
    INGRESS_HOST=$(kubectl get svc istio-ingressgateway -n ${NAMESPACE_ISTIO} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$INGRESS_HOST" ]; then
        INGRESS_HOST=$(kubectl get svc istio-ingressgateway -n ${NAMESPACE_ISTIO} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi

    if [ -z "$INGRESS_HOST" ]; then
        log_warning "Could not determine ingress gateway address. Using NodePort instead."
        INGRESS_PORT=$(kubectl get svc istio-ingressgateway -n ${NAMESPACE_ISTIO} -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
        SECURE_INGRESS_PORT=$(kubectl get svc istio-ingressgateway -n ${NAMESPACE_ISTIO} -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')
        INGRESS_HOST=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')

        log_info "Ingress Gateway (NodePort):"
        log_info "  HTTP:  http://${INGRESS_HOST}:${INGRESS_PORT}"
        log_info "  HTTPS: https://${INGRESS_HOST}:${SECURE_INGRESS_PORT}"
    else
        log_info "Ingress Gateway: ${INGRESS_HOST}"
    fi

    log_info "Ingress configured"
}

enable_addons() {
    log_info "Enabling Istio addons..."

    # Install Kiali
    log_info "Installing Kiali..."
    kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-${ISTIO_VERSION%%.*}/samples/addons/kiali.yaml

    # Install Prometheus (if not using custom config)
    log_info "Installing Prometheus..."
    kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-${ISTIO_VERSION%%.*}/samples/addons/prometheus.yaml

    # Install Grafana
    log_info "Installing Grafana..."
    kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-${ISTIO_VERSION%%.*}/samples/addons/grafana.yaml

    # Install Zipkin
    log_info "Installing Zipkin..."
    kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-${ISTIO_VERSION%%.*}/samples/addons/extras/zipkin.yaml

    log_info "Addons enabled"
}

verify_deployment() {
    log_info "Verifying deployment..."

    # Check pods in all namespaces
    log_info "Checking pod status..."
    kubectl get pods -n ${NAMESPACE_ISTIO}
    kubectl get pods -n ${NAMESPACE_ARTEMIS}
    kubectl get pods -n ${NAMESPACE_SOPHIA}
    kubectl get pods -n ${NAMESPACE_SHARED}

    # Check services
    log_info "Checking services..."
    kubectl get svc -n ${NAMESPACE_ARTEMIS}
    kubectl get svc -n ${NAMESPACE_SOPHIA}

    # Check Istio configuration
    log_info "Checking Istio configuration..."
    istioctl analyze --all-namespaces

    # Check proxy status
    log_info "Checking proxy status..."
    istioctl proxy-status

    log_info "Deployment verification complete"
}

print_access_info() {
    echo
    echo "========================================="
    echo "Sophia-Sophia Service Mesh Deployed!"
    echo "========================================="
    echo
    echo "Access Information:"
    echo "-------------------"
    echo "Sophia UI: http://sophia.sophia-sophia.local"
    echo "Sophia UI:  http://sophia.sophia-sophia.local"
    echo "Kiali:      http://localhost:20001 (run: istioctl dashboard kiali)"
    echo "Grafana:    http://localhost:3000 (run: istioctl dashboard grafana)"
    echo "Zipkin:     http://localhost:9411 (run: istioctl dashboard zipkin)"
    echo
    echo "To access services locally, add to /etc/hosts:"
    echo "${INGRESS_HOST} sophia.sophia-sophia.local sophia.sophia-sophia.local"
    echo
    echo "To check mesh status:"
    echo "  istioctl proxy-status"
    echo "  kubectl get pods --all-namespaces -l istio-injection=enabled"
    echo
}

# Main execution
main() {
    log_info "Starting Sophia-Sophia Service Mesh deployment..."

    check_prerequisites
    install_istio
    create_namespaces
    apply_istio_configs
    deploy_applications
    configure_ingress
    enable_addons
    verify_deployment
    print_access_info

    log_info "Deployment completed successfully!"
}

# Run main function
main "$@"
