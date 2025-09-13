#!/bin/bash
# Test all provider connections

echo "🧪 Testing All Providers"
echo "======================="

test_provider() {
    PROVIDER=$1
    MODEL=$2
    echo -n "Testing $PROVIDER... "
    
    RESPONSE=$(opencode run --provider "$PROVIDER" --model "$MODEL" "Say 'OK' if working" 2>&1)
    
    if echo "$RESPONSE" | grep -q "OK\|working"; then
        echo "✅ Working"
    else
        echo "❌ Failed"
        echo "  Error: ${RESPONSE:0:100}..."
    fi
}

# Test direct providers
test_provider "openai-direct" "gpt-3.5-turbo"
test_provider "anthropic-direct" "claude-3-haiku-20240307"
test_provider "groq-direct" "llama3-8b-8192"
test_provider "deepseek-direct" "deepseek-chat"
test_provider "mistral-direct" "mistral-medium"

# Test routers
test_provider "litellm" "gpt-3.5-turbo"
test_provider "portkey" "gpt-3.5-turbo"
test_provider "openrouter-direct" "openai/gpt-3.5-turbo"
test_provider "together-direct" "meta-llama/Llama-3-8b-chat-hf"
