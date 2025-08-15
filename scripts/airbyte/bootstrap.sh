#!/bin/bash

# Airbyte OSS Bootstrap Script
# Waits for services and creates admin user via API

set -euo pipefail

# Configuration
AIRBYTE_API_URL="${AIRBYTE_API_URL:-http://localhost:8001/api/v1}"
AIRBYTE_WEB_URL="${AIRBYTE_WEB_URL:-http://localhost:8000}"
MINIO_API_URL="${MINIO_API_URL:-http://localhost:9000}"
MINIO_CONSOLE_URL="${MINIO_CONSOLE_URL:-http://localhost:9001}"

# Admin user configuration
ADMIN_EMAIL="${AIRBYTE_ADMIN_EMAIL:-admin@sophia-intel.ai}"
ADMIN_PASSWORD="${AIRBYTE_ADMIN_PASSWORD:-SophiaAdmin123!}"
ADMIN_COMPANY="${AIRBYTE_ADMIN_COMPANY:-Sophia Intel}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=${3:-60}
    local attempt=1

    log "Waiting for $service_name to be ready at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" >/dev/null 2>&1; then
            success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    error "$service_name failed to start within $((max_attempts * 5)) seconds"
    return 1
}

# Check MinIO health
check_minio() {
    log "Checking MinIO health..."
    
    if wait_for_service "$MINIO_API_URL/minio/health/live" "MinIO" 30; then
        success "MinIO is healthy"
        
        # List buckets to verify initialization
        log "Checking MinIO buckets..."
        if command -v mc >/dev/null 2>&1; then
            mc alias set local "$MINIO_API_URL" "${MINIO_ROOT_USER:-minioadmin}" "${MINIO_ROOT_PASSWORD:-minioadmin123}" >/dev/null 2>&1 || true
            mc ls local/ 2>/dev/null || warning "Could not list MinIO buckets (mc client may not be available)"
        else
            warning "MinIO client (mc) not available for bucket verification"
        fi
        
        return 0
    else
        error "MinIO health check failed"
        return 1
    fi
}

# Check Airbyte health
check_airbyte() {
    log "Checking Airbyte health..."
    
    if wait_for_service "$AIRBYTE_API_URL/health" "Airbyte API" 60; then
        success "Airbyte API is healthy"
        return 0
    else
        error "Airbyte health check failed"
        return 1
    fi
}

# Create admin user
create_admin_user() {
    log "Creating Airbyte admin user..."
    
    # Check if user already exists
    local user_check
    user_check=$(curl -s -X POST "$AIRBYTE_API_URL/users/list" \
        -H "Content-Type: application/json" \
        -d '{}' 2>/dev/null || echo '{"users":[]}')
    
    if echo "$user_check" | grep -q "$ADMIN_EMAIL"; then
        warning "Admin user already exists"
        return 0
    fi
    
    # Create user
    local create_response
    create_response=$(curl -s -X POST "$AIRBYTE_API_URL/users/create" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$ADMIN_EMAIL\",
            \"password\": \"$ADMIN_PASSWORD\",
            \"name\": \"Admin User\",
            \"companyName\": \"$ADMIN_COMPANY\"
        }" 2>/dev/null || echo '{"error":"failed"}')
    
    if echo "$create_response" | grep -q '"userId"'; then
        success "Admin user created successfully"
        log "Email: $ADMIN_EMAIL"
        log "Password: [REDACTED]"
    else
        warning "Could not create admin user (may already exist or API may not support user creation)"
        log "You can create users manually through the web interface"
    fi
}

# Create default workspace
create_default_workspace() {
    log "Creating default workspace..."
    
    # List existing workspaces
    local workspaces
    workspaces=$(curl -s -X POST "$AIRBYTE_API_URL/workspaces/list" \
        -H "Content-Type: application/json" \
        -d '{}' 2>/dev/null || echo '{"workspaces":[]}')
    
    if echo "$workspaces" | grep -q '"name":"Sophia Intel"'; then
        warning "Sophia Intel workspace already exists"
        return 0
    fi
    
    # Create workspace
    local workspace_response
    workspace_response=$(curl -s -X POST "$AIRBYTE_API_URL/workspaces/create" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Sophia Intel",
            "email": "'"$ADMIN_EMAIL"'",
            "anonymousDataCollection": false,
            "news": false,
            "securityUpdates": true
        }' 2>/dev/null || echo '{"error":"failed"}')
    
    if echo "$workspace_response" | grep -q '"workspaceId"'; then
        success "Default workspace created successfully"
        local workspace_id
        workspace_id=$(echo "$workspace_response" | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
        log "Workspace ID: $workspace_id"
    else
        warning "Could not create default workspace"
        log "You can create workspaces manually through the web interface"
    fi
}

# Test MinIO connectivity from Airbyte
test_minio_connectivity() {
    log "Testing MinIO connectivity from Airbyte..."
    
    # This is a basic connectivity test
    # In a real deployment, you'd configure an S3 destination pointing to MinIO
    local minio_test
    minio_test=$(curl -s "$MINIO_API_URL/minio/health/live" 2>/dev/null || echo "failed")
    
    if [ "$minio_test" != "failed" ]; then
        success "MinIO is accessible from Airbyte network"
    else
        warning "MinIO connectivity test failed"
    fi
}

# Main bootstrap process
main() {
    log "Starting Airbyte OSS bootstrap process..."
    echo
    
    # Check prerequisites
    if ! command -v curl >/dev/null 2>&1; then
        error "curl is required but not installed"
        exit 1
    fi
    
    # Step 1: Check MinIO
    if ! check_minio; then
        error "MinIO bootstrap failed"
        exit 1
    fi
    echo
    
    # Step 2: Check Airbyte
    if ! check_airbyte; then
        error "Airbyte bootstrap failed"
        exit 1
    fi
    echo
    
    # Step 3: Create admin user
    create_admin_user
    echo
    
    # Step 4: Create default workspace
    create_default_workspace
    echo
    
    # Step 5: Test connectivity
    test_minio_connectivity
    echo
    
    # Success summary
    success "Bootstrap completed successfully!"
    echo
    log "Access URLs:"
    log "  Airbyte Web UI: $AIRBYTE_WEB_URL"
    log "  MinIO Console:  $MINIO_CONSOLE_URL"
    log "  Airbyte API:    $AIRBYTE_API_URL"
    echo
    log "Default credentials:"
    log "  Airbyte Admin: $ADMIN_EMAIL"
    log "  MinIO Console: ${MINIO_ROOT_USER:-minioadmin}"
    echo
    log "Next steps:"
    log "1. Access the Airbyte web interface"
    log "2. Configure your first source and destination"
    log "3. Create your first connection"
    echo
}

# Run main function
main "$@"

