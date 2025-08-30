"""
Concurrent generator pools for Coding Swarm.
These are OpenRouter model IDs routed via Portkey.
Tune/extend as you see fit.
"""

# Low-latency ideation (fast baseline)
FAST_POOL = [
    "google/gemini-2.0-flash-exp:free",  # Fast and free
    "openai/gpt-4o-mini",                 # Quick GPT-4 variant
]

# Heavyweight generation (deeper reasoning/strong coders)
HEAVY_POOL = [
    "deepseek/deepseek-coder",           # Strong code generation
    "qwen/qwen-2.5-coder-32b-instruct",  # Excellent for complex code
    "x-ai/grok-2-1212",                  # Deep reasoning capability
]

# Balanced pool (good mix of speed and quality)
BALANCED_POOL = [
    "openai/gpt-4o",
    "anthropic/claude-3.5-sonnet-20241022",
]

POOLS = {
    "fast": FAST_POOL,
    "heavy": HEAVY_POOL,
    "balanced": BALANCED_POOL,
}