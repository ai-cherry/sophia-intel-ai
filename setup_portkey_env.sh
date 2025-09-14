#!/bin/bash

# Portkey Environment Setup Script for Sophia Intel AI
# This script configures the necessary environment variables for Portkey integration

echo "Setting up Portkey environment variables..."

# Main Portkey API Key
export PORTKEY_API_KEY="nYraiE8dOR9A1gDwaRNpSSXRkXBc"

# Virtual Keys for each provider
export PORTKEY_VK_ANTHROPIC="anthropic-vk-b42804"
export PORTKEY_VK_DEEPSEEK="deepseek-vk-24102f"
export PORTKEY_VK_GROQ="groq-vk-6b9b52"
export PORTKEY_VK_OPENAI="openai-vk-190a60"
export PORTKEY_VK_PERPLEXITY="perplexity-vk-56c172"
export PORTKEY_VK_TOGETHER="together-ai-670469"
export PORTKEY_VK_OPENROUTER="vkj-openrouter-cc4151"
export PORTKEY_VK_X="xai-vk-e65d0f"
export PORTKEY_VK_GITHUB="github-vk-a5b609"
export PORTKEY_VK_STABILITY="stability-vk-a575fb"

# For X-AI/Grok models through OpenRouter
export PORTKEY_VK_X_AI="vkj-openrouter-cc4151"

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