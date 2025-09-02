"""
Swarm-specific model assignments for different swarms.
Configures which models are used for each role within a swarm.
"""

SWARM_MODEL_ASSIGNMENTS = {
    "coding_swarm": {
        "architect": "openai/gpt-5",  # Complex architecture decisions
        "implementer": "x-ai/grok-code-fast-1",  # Fast code generation
        "reviewer": "anthropic/claude-sonnet-4",  # Balanced review
        "tester": "google/gemini-2.5-flash"  # Quick test generation
    },

    "debate_swarm": {
        "moderator": "openai/gpt-5",  # Advanced reasoning
        "proponent": "x-ai/grok-4",  # Strong arguments
        "opponent": "anthropic/claude-sonnet-4",  # Counter-arguments
        "summarizer": "google/gemini-2.5-pro"  # Comprehensive summary
    },

    "consensus_swarm": {
        "facilitator": "openai/gpt-5",  # Complex consensus building
        "analyzer": "google/gemini-2.5-pro",  # Data analysis
        "validator": "anthropic/claude-sonnet-4",  # Validation
        "documenter": "deepseek/deepseek-chat-v3.1"  # Documentation
    },

    "memory_swarm": {
        "indexer": "deepseek/deepseek-chat-v3.1",  # Context management
        "retriever": "z-ai/glm-4.5-air",  # Fast retrieval
        "curator": "qwen/qwen3-30b-a3b",  # Deep understanding
        "embedder": "text-embedding-3-large"  # Embedding generation
    }
}
