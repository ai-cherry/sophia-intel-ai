#!/bin/bash
# ==============================================
# OLLAMA MODEL DOWNLOAD SCRIPT
# Phase 2, Week 1-2: Pull Llama 3.2 models for local development
# ==============================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
MODELS=("llama3.2:3b" "llama3.2:7b" "nomic-embed-text") # Include embedding model

# Functions
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%H:%M:%S')

    case $level in
        "INFO")  echo -e "${BLUE}[${timestamp}] INFO: ${message}${NC}" ;;
        "SUCCESS") echo -e "${GREEN}[${timestamp}] SUCCESS: ${message}${NC}" ;;
        "WARNING") echo -e "${YELLOW}[${timestamp}] WARNING: ${message}${NC}" ;;
        "ERROR")   echo -e "${RED}[${timestamp}] ERROR: ${message}${NC}" ;;
    esac
}

check_ollama() {
    log "INFO" "Checking Ollama service..."

    if curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        log "SUCCESS" "Ollama is running at ${OLLAMA_HOST}"
        return 0
    else
        log "ERROR" "Ollama is not accessible at ${OLLAMA_HOST}"
        log "INFO" "Please ensure Ollama is running with: docker-compose -f docker-compose.minimal.yml up -d ollama"
        return 1
    fi
}

list_models() {
    log "INFO" "Currently available models:"
    curl -s "${OLLAMA_HOST}/api/tags" | python3 -m json.tool | grep '"name"' || echo "No models found"
}

pull_model() {
    local model=$1
    log "INFO" "Pulling model: ${model}"

    # Pull the model using Ollama API
    response=$(curl -s -X POST "${OLLAMA_HOST}/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"${model}\"}")

    if [ $? -eq 0 ]; then
        log "SUCCESS" "Successfully initiated pull for ${model}"

        # Monitor progress
        log "INFO" "Downloading ${model}... This may take several minutes..."

        # Use ollama CLI if available, otherwise use API
        if command -v ollama &> /dev/null; then
            ollama pull "${model}"
        else
            # Wait and check status via API
            sleep 5
            while true; do
                if curl -s "${OLLAMA_HOST}/api/tags" | grep -q "${model}"; then
                    log "SUCCESS" "Model ${model} is now available"
                    break
                fi
                echo -n "."
                sleep 10
            done
        fi
    else
        log "ERROR" "Failed to pull ${model}"
        return 1
    fi
}

test_model() {
    local model=$1
    log "INFO" "Testing model: ${model}"

    # Simple test prompt
    response=$(curl -s -X POST "${OLLAMA_HOST}/api/generate" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"${model}\",
            \"prompt\": \"Hello! Please respond with a simple greeting.\",
            \"stream\": false,
            \"options\": {
                \"temperature\": 0.1,
                \"num_predict\": 50
            }
        }")

    if echo "$response" | grep -q "response"; then
        log "SUCCESS" "Model ${model} is working correctly"
        echo -e "${GREEN}Response: $(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('response', 'No response')[:100])")${NC}"
    else
        log "ERROR" "Model ${model} test failed"
        return 1
    fi
}

main() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  🤖 OLLAMA MODEL SETUP FOR SOPHIA INTEL AI"
    echo -e "${BLUE}  📅 $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

    # Check if Ollama is running
    if ! check_ollama; then
        exit 1
    fi

    # List current models
    list_models

    # Pull each model
    for model in "${MODELS[@]}"; do
        echo -e "\n${BLUE}────────────────────────────────────────${NC}"

        # Check if model already exists
        if curl -s "${OLLAMA_HOST}/api/tags" | grep -q "\"${model}\""; then
            log "INFO" "Model ${model} already exists, skipping download"
        else
            if ! pull_model "${model}"; then
                log "WARNING" "Failed to pull ${model}, continuing with other models..."
                continue
            fi
        fi

        # Test the model
        test_model "${model}"
    done

    echo -e "\n${BLUE}════════════════════════════════════════════════════════════════${NC}"
    log "SUCCESS" "Model setup completed!"

    # Final model list
    echo -e "\n${GREEN}Available models:${NC}"
    list_models

    echo -e "\n${GREEN}Next steps:${NC}"
    echo "1. Models are ready for use with the RAG pipeline"
    echo "2. Default model is set to: llama3.2:3b"
    echo "3. For better performance, use: llama3.2:7b"
    echo "4. Run the test script: python app/quickstart/test_rag.py"
}

# Parse command line arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "list")
        check_ollama && list_models
        ;;
    "test")
        model="${2:-llama3.2:3b}"
        check_ollama && test_model "$model"
        ;;
    "pull")
        model="${2:-llama3.2:3b}"
        check_ollama && pull_model "$model"
        ;;
    *)
        echo "Usage: $0 {setup|list|test [model]|pull [model]}"
        echo ""
        echo "  setup     - Pull all required models (default)"
        echo "  list      - List available models"
        echo "  test      - Test a specific model"
        echo "  pull      - Pull a specific model"
        exit 1
        ;;
esac
