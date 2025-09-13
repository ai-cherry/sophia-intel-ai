#!/bin/bash
# Cloud deployment script for Sophia Intel AI
# Supports multiple cloud providers with optimized configurations

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${SOPHIA_ENV_FILE:-}"
CLOUD_PROVIDER="${CLOUD_PROVIDER:-fly}"

# Load environment (cloud-only)
load_environment() {
    echo -e "${YELLOW}⚠️  Cloud-only script: env must be injected by CI/CD or set via SOPHIA_ENV_FILE. Do not use for local dev.${NC}"
    if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
        echo -e "${GREEN}✅ Loaded env from $ENV_FILE${NC}"
    fi
}

# Build multi-arch images
build_images() {
    echo -e "${BLUE}🔨 Building multi-architecture Docker images...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Setup buildx for multi-arch
    docker buildx create --use --name sophia-builder 2>/dev/null || true
    
    # Build images for ARM64 and AMD64
    echo "Building Bridge API..."
    docker buildx build \
        --platform linux/arm64,linux/amd64 \
        -t sophia-bridge:latest \
        -f infra/Dockerfile.bridge \
        --push \
        .
    
    echo "Building MCP servers..."
    docker buildx build \
        --platform linux/arm64,linux/amd64 \
        -t sophia-mcp:latest \
        -f infra/Dockerfile.mcp \
        --push \
        .
    
    # Coding UI is not built from this repo
    
    echo -e "${GREEN}✅ Images built and pushed${NC}"
}

# Deploy to Fly.io
deploy_fly() {
    echo -e "${BLUE}🚀 Deploying to Fly.io...${NC}"
    
    # Check if fly CLI is installed
    if ! command -v fly &> /dev/null; then
        echo -e "${RED}❌ Fly CLI not found. Install from https://fly.io/docs/getting-started/installing-flyctl/${NC}"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # Create app if not exists
    if ! fly apps list | grep -q sophia-intel-ai; then
        echo "Creating Fly.io app..."
        fly apps create sophia-intel-ai --org personal
    fi
    
    # Set secrets
    echo "Setting secrets..."
    fly secrets set \
        OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
        POSTGRES_URL="$FLY_POSTGRES_URL" \
        REDIS_URL="$FLY_REDIS_URL" \
        NEO4J_URI="$FLY_NEO4J_URI" \
        NEO4J_USER="$NEO4J_USER" \
        NEO4J_PASSWORD="$NEO4J_PASSWORD" \
        GITHUB_TOKEN="$GITHUB_TOKEN" \
        INDEX_ENABLED="true" \
        --app sophia-intel-ai
    
    # Deploy
    echo "Deploying application..."
    fly deploy --config fly.toml
    
    # Scale appropriately
    echo "Scaling services..."
    fly scale count 2 --app sophia-intel-ai
    
    # Check status
    fly status --app sophia-intel-ai
    
    echo -e "${GREEN}✅ Deployed to Fly.io${NC}"
    
    # Get app URL
    APP_URL=$(fly info --app sophia-intel-ai -j | jq -r '.Hostname')
    echo ""
    echo "Application available at: https://$APP_URL"
}

# Deploy to AWS ECS
deploy_aws() {
    echo -e "${BLUE}☁️  Deploying to AWS ECS...${NC}"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not found${NC}"
        exit 1
    fi
    
    # Create ECR repositories
    echo "Creating ECR repositories..."
    aws ecr create-repository --repository-name sophia-bridge 2>/dev/null || true
    aws ecr create-repository --repository-name sophia-mcp 2>/dev/null || true
    aws ecr create-repository --repository-name sophia-ui 2>/dev/null || true
    
    # Get registry URL
    REGISTRY=$(aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin)
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    REGION="us-west-2"
    
    # Tag and push images
    echo "Pushing images to ECR..."
    docker tag sophia-bridge:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/sophia-bridge:latest
    docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/sophia-bridge:latest
    
    docker tag sophia-mcp:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/sophia-mcp:latest
    docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/sophia-mcp:latest
    
    docker tag sophia-ui:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/sophia-ui:latest
    docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/sophia-ui:latest
    
    # Deploy CloudFormation stack
    echo "Deploying CloudFormation stack..."
    aws cloudformation deploy \
        --template-file "$PROJECT_ROOT/deploy/aws/ecs-stack.yaml" \
        --stack-name sophia-intel-ai \
        --parameter-overrides \
            OpenRouterApiKey="$OPENROUTER_API_KEY" \
            PostgresUrl="$AWS_POSTGRES_URL" \
            RedisUrl="$AWS_REDIS_URL" \
        --capabilities CAPABILITY_IAM
    
    echo -e "${GREEN}✅ Deployed to AWS ECS${NC}"
}

# Deploy to Google Cloud Run
deploy_gcp() {
    echo -e "${BLUE}☁️  Deploying to Google Cloud Run...${NC}"
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI not found${NC}"
        exit 1
    fi
    
    PROJECT_ID=$(gcloud config get-value project)
    REGION="us-central1"
    
    # Enable required APIs
    echo "Enabling required APIs..."
    gcloud services enable \
        run.googleapis.com \
        cloudbuild.googleapis.com \
        artifactregistry.googleapis.com
    
    # Build and push to Artifact Registry
    echo "Building with Cloud Build..."
    gcloud builds submit \
        --tag gcr.io/$PROJECT_ID/sophia-bridge \
        --file infra/Dockerfile.bridge \
        .
    
    # Deploy services
    echo "Deploying Bridge API..."
    gcloud run deploy sophia-bridge \
        --image gcr.io/$PROJECT_ID/sophia-bridge \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --set-env-vars="OPENROUTER_API_KEY=$OPENROUTER_API_KEY,REDIS_URL=$GCP_REDIS_URL" \
        --memory 2Gi \
        --cpu 2
    
    echo "Deploying MCP servers..."
    for service in memory filesystem git; do
        gcloud run deploy sophia-mcp-$service \
            --image gcr.io/$PROJECT_ID/sophia-mcp \
            --platform managed \
            --region $REGION \
            --allow-unauthenticated \
            --set-env-vars="SERVER_TYPE=$service,REDIS_URL=$GCP_REDIS_URL" \
            --memory 1Gi \
            --cpu 1
    done
    
    echo -e "${GREEN}✅ Deployed to Google Cloud Run${NC}"
}

# Deploy with Kubernetes
deploy_k8s() {
    echo -e "${BLUE}☸️  Deploying to Kubernetes...${NC}"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl not found${NC}"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # Create namespace
    kubectl create namespace sophia 2>/dev/null || true
    
    # Create secrets
    kubectl create secret generic sophia-secrets \
        --from-literal=openrouter-api-key="$OPENROUTER_API_KEY" \
        --from-literal=postgres-url="$POSTGRES_URL" \
        --from-literal=redis-url="$REDIS_URL" \
        --from-literal=github-token="$GITHUB_TOKEN" \
        --namespace sophia \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply manifests
    echo "Applying Kubernetes manifests..."
    kubectl apply -f deploy/k8s/ --namespace sophia
    
    # Wait for rollout
    echo "Waiting for deployment..."
    kubectl rollout status deployment/sophia-bridge --namespace sophia
    kubectl rollout status deployment/sophia-mcp-memory --namespace sophia
    kubectl rollout status deployment/sophia-mcp-filesystem --namespace sophia
    kubectl rollout status deployment/sophia-mcp-git --namespace sophia
    kubectl rollout status deployment/sophia-ui --namespace sophia
    
    # Get service URLs
    echo -e "${GREEN}✅ Deployed to Kubernetes${NC}"
    echo ""
    echo "Services:"
    kubectl get services --namespace sophia
}

# Health check for deployed services
cloud_health_check() {
    echo -e "${BLUE}🏥 Running cloud health checks...${NC}"
    
    case "$CLOUD_PROVIDER" in
        fly)
            fly status --app sophia-intel-ai
            APP_URL=$(fly info --app sophia-intel-ai -j | jq -r '.Hostname')
            curl -sf "https://$APP_URL/health" && echo -e "${GREEN}✅ Application is healthy${NC}"
            ;;
        aws)
            aws ecs describe-services \
                --cluster sophia-cluster \
                --services sophia-bridge sophia-mcp sophia-ui \
                --query 'services[*].[serviceName,runningCount,desiredCount]' \
                --output table
            ;;
        gcp)
            gcloud run services list --platform managed --region us-central1
            ;;
        k8s)
            kubectl get pods --namespace sophia
            kubectl get services --namespace sophia
            ;;
    esac
}

# Rollback deployment
rollback() {
    echo -e "${YELLOW}⚠️  Rolling back deployment...${NC}"
    
    case "$CLOUD_PROVIDER" in
        fly)
            fly releases --app sophia-intel-ai
            echo "Run: fly deploy --app sophia-intel-ai --image <previous-image>"
            ;;
        aws)
            # Implement ECS rollback
            echo "AWS ECS rollback not yet implemented"
            ;;
        gcp)
            # Implement Cloud Run rollback
            echo "GCP Cloud Run rollback not yet implemented"
            ;;
        k8s)
            kubectl rollout undo deployment/sophia-bridge --namespace sophia
            kubectl rollout undo deployment/sophia-mcp-memory --namespace sophia
            kubectl rollout undo deployment/sophia-mcp-filesystem --namespace sophia
            kubectl rollout undo deployment/sophia-mcp-git --namespace sophia
            kubectl rollout undo deployment/sophia-ui --namespace sophia
            ;;
    esac
}

# Main deployment
deploy() {
    echo -e "${BLUE}🚀 Cloud Deployment for Sophia Intel AI${NC}"
    echo "Provider: $CLOUD_PROVIDER"
    echo "=================================="
    
    load_environment
    build_images
    
    case "$CLOUD_PROVIDER" in
        fly)
            deploy_fly
            ;;
        aws)
            deploy_aws
            ;;
        gcp)
            deploy_gcp
            ;;
        k8s)
            deploy_k8s
            ;;
        *)
            echo -e "${RED}❌ Unknown cloud provider: $CLOUD_PROVIDER${NC}"
            echo "Supported: fly, aws, gcp, k8s"
            exit 1
            ;;
    esac
    
    # Run health check
    sleep 10
    cloud_health_check
    
    echo ""
    echo -e "${GREEN}🎉 Cloud deployment complete!${NC}"
}

# Command handler
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    health)
        cloud_health_check
        ;;
    rollback)
        rollback
        ;;
    logs)
        case "$CLOUD_PROVIDER" in
            fly)
                fly logs --app sophia-intel-ai
                ;;
            k8s)
                kubectl logs -f --namespace sophia -l app=sophia
                ;;
            *)
                echo "Logs not implemented for $CLOUD_PROVIDER"
                ;;
        esac
        ;;
    *)
        echo "Usage: $0 {deploy|health|rollback|logs}"
        echo "Set CLOUD_PROVIDER to: fly, aws, gcp, or k8s"
        exit 1
        ;;
esac
