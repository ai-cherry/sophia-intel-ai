"""
Experimental Swarm Evolution Module - ADR-002 Implementation

⚠️ EXPERIMENTAL FEATURES ⚠️

This module contains experimental genetic algorithm implementations for autonomous 
swarm evolution. All features are disabled by default and require explicit 
acknowledgment to enable.

Key Components:
- ExperimentalEvolutionEngine: Main genetic algorithm system
- SwarmChromosome: Chromosome representation for swarm configurations  
- Multi-objective fitness evaluation with safety controls
- Pattern recognition and breakthrough detection
- Memory integration for historical learning
- Safety boundaries and rollback mechanisms

Usage:
    from app.swarms.evolution import create_experimental_evolution_engine, ExperimentalMode
    
    # Safe default (disabled)
    engine = create_experimental_evolution_engine()
    
    # Enable experimental features (requires acknowledgment)
    engine = create_experimental_evolution_engine(
        mode=ExperimentalMode.CAUTIOUS,
        enable_experimental=True,
        acknowledge_experimental=True,  # Required!
        dry_run_mode=True  # Recommended for testing
    )
"""

from .experimental_evolution_engine import (
    ExperimentalEvolutionEngine,
    ExperimentalMode,
    ExperimentalEvolutionConfig,
    ExperimentalSafetyBounds,
    SwarmChromosome,
    ExperimentalFitnessEvaluation,
    create_experimental_evolution_engine,
    EXPERIMENTAL_EVOLUTION_EXAMPLES
)

__all__ = [
    'ExperimentalEvolutionEngine',
    'ExperimentalMode', 
    'ExperimentalEvolutionConfig',
    'ExperimentalSafetyBounds',
    'SwarmChromosome',
    'ExperimentalFitnessEvaluation',
    'create_experimental_evolution_engine',
    'EXPERIMENTAL_EVOLUTION_EXAMPLES'
]

# Version and safety warnings
__version__ = "0.1.0-experimental"
__experimental__ = True
__safety_warning__ = """
⚠️ EXPERIMENTAL EVOLUTION FEATURES ⚠️

These are experimental genetic algorithm implementations that:
- May produce unexpected behaviors
- Require careful monitoring in production
- Are disabled by default for safety
- Need explicit acknowledgment to enable
- Should be tested thoroughly before deployment

Always use dry_run_mode=True for initial testing!
"""

def get_experimental_info():
    """Get information about experimental evolution features."""
    return {
        "version": __version__,
        "experimental": __experimental__,
        "safety_warning": __safety_warning__,
        "default_mode": ExperimentalMode.DISABLED,
        "available_modes": list(ExperimentalMode),
        "configuration_examples": list(EXPERIMENTAL_EVOLUTION_EXAMPLES.keys())
    }