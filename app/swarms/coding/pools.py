"""
Concurrent generator pools for Coding Swarm.
These are OpenRouter model IDs routed via Portkey.
ONLY APPROVED MODELS - NO EXCEPTIONS.
"""

# Low-latency ideation (fast baseline)
FAST_POOL = [
    "google/gemini-2.5-flash",  # Fast responses
    "z-ai/glm-4.5-air",         # Lightweight
]

# Heavyweight generation (deeper reasoning/strong coders)
HEAVY_POOL = [
    "x-ai/grok-code-fast-1",    # Code specialist
    "x-ai/grok-4",              # Deep reasoning
    "openai/gpt-5",             # Premium capability
]

# Balanced pool (good mix of speed and quality)
BALANCED_POOL = [
    "google/gemini-2.5-pro",
    "qwen/qwen3-30b-a3b",
    "anthropic/claude-sonnet-4",
]

POOLS = {
    "fast": FAST_POOL,
    "heavy": HEAVY_POOL,
    "balanced": BALANCED_POOL,
}
