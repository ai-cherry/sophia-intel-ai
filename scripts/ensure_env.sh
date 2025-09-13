#!/bin/bash
# Ensure environment is loaded from master file
# This script ensures ALL services and scripts get the real API keys

MASTER_ENV="/Users/lynnmusil/sophia-intel-ai/.env.master"

# Function to load environment
load_env() {
    if [ -f "$MASTER_ENV" ]; then
        set -a  # Export all variables
        source "$MASTER_ENV"
        set +a
        echo "✅ Environment loaded from $MASTER_ENV"
        echo "   Found $(grep -c "API_KEY" $MASTER_ENV) API keys"
    else
        echo "❌ ERROR: $MASTER_ENV not found!"
        exit 1
    fi
}

# Function to verify keys
verify_keys() {
    local required_keys=(
        "PORTKEY_API_KEY"
    )
    
    local missing=0
    for key in "${required_keys[@]}"; do
        if [ -z "${!key}" ]; then
            echo "❌ Missing: $key"
            ((missing++))
        else
            echo "✅ Found: $key = ${!key:0:20}..."
        fi
    done
    
    if [ $missing -gt 0 ]; then
        echo "⚠️  WARNING: $missing keys missing"
    else
        echo "✅ All required keys present"
    fi
}

# Main
load_env
verify_keys
