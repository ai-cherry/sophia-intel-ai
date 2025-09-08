#!/bin/bash
# Sophia AI Platform - Environment Setup Script
# Sets up all API credentials as environment variables
# NOTE: This script should be populated with actual credentials from secure storage

echo "🔧 Setting up Sophia AI environment variables..."

# Cloud Infrastructure
export LAMBDA_API_KEY="${LAMBDA_API_KEY:-your_lambda_api_key_here}"
export LAMBDA_CLOUD_API_KEY="${LAMBDA_CLOUD_API_KEY:-your_lambda_cloud_api_key_here}"
export NEON_API_TOKEN="${NEON_API_TOKEN:-your_neon_api_token_here}"
export QDRANT_API_KEY="${QDRANT_API_KEY:-your_qdrant_api_key_here}"
export REDIS_USER_API_KEY="${REDIS_USER_API_KEY:-your_redis_user_api_key_here}"
export REDIS_ACCOUNT_KEY="${REDIS_ACCOUNT_KEY:-your_redis_account_key_here}"
export ESTUARY_ACCESS_TOKEN="${ESTUARY_ACCESS_TOKEN:-your_estuary_access_token_here}"
export N8N_API_KEY="${N8N_API_KEY:-your_n8n_api_key_here}"
export PULUMI_ACCESS_TOKEN="${PULUMI_ACCESS_TOKEN:-your_pulumi_access_token_here}"

# Version Control & CI/CD
export GITHUB_TOKEN="${GITHUB_TOKEN:-your_github_token_here}"

# AI Providers - Extended Set
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-your_openrouter_api_key_here}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-your_anthropic_api_key_here}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-your_openai_api_key_here}"
export GROK_AI_API_KEY="${GROK_AI_API_KEY:-your_grok_ai_api_key_here}"
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-your_deepseek_api_key_here}"
export HUGGINGFACE_API_TOKEN="${HUGGINGFACE_API_TOKEN:-your_huggingface_api_token_here}"
export MISTRAL_API_KEY="${MISTRAL_API_KEY:-your_mistral_api_key_here}"
export EXA_API_KEY="${EXA_API_KEY:-your_exa_api_key_here}"
export LLAMA_API_KEY="${LLAMA_API_KEY:-your_llama_api_key_here}"
export TOGETHER_AI_API_KEY="${TOGETHER_AI_API_KEY:-your_together_ai_api_key_here}"
export PERPLEXITY_API_KEY="${PERPLEXITY_API_KEY:-your_perplexity_api_key_here}"
export STABILITY_API_KEY="${STABILITY_API_KEY:-your_stability_api_key_here}"
export VENICE_API_KEY="${VENICE_API_KEY:-your_venice_api_key_here}"
export MUREKA_API_KEY="${MUREKA_API_KEY:-your_mureka_api_key_here}"
export GEMINI_API_KEY="${GEMINI_API_KEY:-your_gemini_api_key_here}"

# Memory & Context
export MEM0_API_KEY="${MEM0_API_KEY:-your_mem0_api_key_here}"

# UV Configuration
export UV_CACHE_DIR="/opt/uv-cache"
export UV_PYTHON_PREFERENCE="managed"
export UV_COMPILE_BYTECODE="1"
export UV_LINK_MODE="hardlink"

echo "✅ Environment variables configured successfully!"
echo "🔍 Run 'python validate_credentials.py' to test all credentials"
echo "⚠️  Note: Replace placeholder values with actual credentials from secure storage"

