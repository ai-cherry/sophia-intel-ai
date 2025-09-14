#!/bin/bash

# Portkey Environment Setup Script for Sophia Intel AI
# This script configures the necessary environment variables for Portkey integration

echo "Setting up Portkey environment variables..."

# Portkey Keys (both user and service keys)
export PORTKEY_USER_KEY="p2pibAbU+7DU7fKTmUjfJ34qAZaz"
export PORTKEY_SERVICE_KEY="0rzc3nPU4g4czkbWzFwhsv5zDL5x"
# Use the user key as PORTKEY_API_KEY (this one works)
export PORTKEY_API_KEY="p2pibAbU+7DU7fKTmUjfJ34qAZaz"

# Virtual Keys for each provider (without "@" for direct header usage)
export PORTKEY_VK_ANTHROPIC="anthropic-vk-b42804"
export PORTKEY_VK_DEEPSEEK="deepseek-vk-24102f"
export PORTKEY_VK_GROQ="groq-vk-6b9b52"
export PORTKEY_VK_OPENAI="openai-vk-2267b0"
export PORTKEY_VK_PERPLEXITY="perplexity-vk-56c172"
export PORTKEY_VK_TOGETHER="together-ai-670469"
export PORTKEY_VK_OPENROUTER="openrouter-vk-45aeee"
export PORTKEY_VK_X="xai-vk-e65d0f"
export PORTKEY_VK_XAI="xai-vk-e65d0f"
export PORTKEY_VK_X_AI="xai-vk-e65d0f"
export PORTKEY_VK_GITHUB="github-vk-a5b609"
export PORTKEY_VK_STABILITY="stability-vk-a575fb"
export PORTKEY_VK_HUGGINGFACE="huggingface-vk-28240e"
export PORTKEY_VK_COHERE="cohere-vk-496fa9"
export PORTKEY_VK_QDRANT="qdrant-vk-d2b62a"
export PORTKEY_VK_MILVUS="milvus-vk-34fa02"
export PORTKEY_VK_MISTRAL="mistral-vk-f92861"
export PORTKEY_VK_MISTRALAI="mistral-vk-f92861"

echo "Environment variables set!"
echo ""
echo "Available models:"
echo "  - openai/gpt-4o-mini (uses PORTKEY_VK_OPENAI)"
echo "  - anthropic/claude-3-opus-20240229 (uses PORTKEY_VK_ANTHROPIC)"
echo "  - deepseek/deepseek-chat (uses PORTKEY_VK_DEEPSEEK)"
echo "  - openrouter/x-ai/grok-beta (uses PORTKEY_VK_OPENROUTER)"
echo ""
echo "To test the CLI:"
echo "  ./bin/sophia plan --model openai/gpt-4o-mini --task \"Your task here\""
echo ""
echo "Note: Source this file to set the variables in your current shell:"
echo "  source setup_portkey_env.sh"