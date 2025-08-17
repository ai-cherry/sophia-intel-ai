#!/bin/bash

# Railway Variables Setup Script
# Project ID: 381dde06-1aff-40b2-a1c9-470a2acabe3f

export RAILWAY_TOKEN="32f097ac-7c3a-4a81-8385-b4ce98a2ca1f"

echo "🚂 Setting Railway Environment Variables..."

# Function to set variable using Railway API
set_variable() {
    local key="$1"
    local value="$2"
    
    echo "Setting $key..."
    
    # Try Railway v2 API
    curl -X POST \
        -H "Authorization: Bearer $RAILWAY_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"key\":\"$key\",\"value\":\"$value\"}" \
        "https://railway.app/api/v2/projects/381dde06-1aff-40b2-a1c9-470a2acabe3f/variables" \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ $key set successfully"
    else
        echo "❌ Failed to set $key"
    fi
}

# Set all required variables
set_variable "REDIS_URL" "redis://default:S666q3cr9wmzpetc6iud02iqv26774azveodh2pfadrd7pgq8l7@redis:6379"
set_variable "CELERY_BROKER_URL" "redis://default:S666q3cr9wmzpetc6iud02iqv26774azveodh2pfadrd7pgq8l7@redis:6379"
set_variable "CELERY_RESULT_BACKEND" "redis://default:S666q3cr9wmzpetc6iud02iqv26774azveodh2pfadrd7pgq8l7@redis:6379"
set_variable "JWT_SECRET_KEY" "sophia-intel-production-jwt-secret-2025"
set_variable "ENCRYPTION_KEY" "sophia-intel-32-byte-encryption-key"
set_variable "API_KEY_SALT" "sophia-api-salt-2025"

echo "🚀 Railway variables setup complete!"
echo ""
echo "Next steps:"
echo "1. Check Railway dashboard for variables"
echo "2. Monitor deployment in Railway"
echo "3. Test application at generated URL"

