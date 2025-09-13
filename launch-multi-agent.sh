#!/bin/bash
# Launch multiple agents with different providers

echo "🤖 Launching Multi-Agent Swarm"
echo "=============================="

# Agent 1: Fast code generation (Groq)
echo "Agent 1: Groq Mixtral for fast code..."
opencode run --provider groq-direct --model mixtral-8x7b-32768 "Generate a Python web scraper" &

# Agent 2: Complex reasoning (Anthropic)
echo "Agent 2: Claude for analysis..."
opencode run --provider anthropic-direct --model claude-3-5-sonnet-20241022 "Analyze security vulnerabilities" &

# Agent 3: Cost-optimized (LiteLLM with fallbacks)
echo "Agent 3: LiteLLM with auto-fallback..."
opencode run --provider litellm --model cheap "Generate test cases" &

# Agent 4: Research with web (Perplexity)
echo "Agent 4: Perplexity for research..."
opencode run --provider perplexity-direct --model sonar-medium-online "Latest Python security best practices" &

echo ""
echo "All agents launched. Waiting for completion..."
wait
echo "✅ All agents completed"
