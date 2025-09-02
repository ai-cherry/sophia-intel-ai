"""
Test Suite for Experimental Evolution Engine - ADR-002

⚠️ EXPERIMENTAL TESTING ⚠️

This test suite provides comprehensive validation for the experimental evolution 
engine, including safety controls, genetic algorithms, and integration points.

Run tests with:
    pytest app/swarms/evolution/tests/ -v
    
Or run specific test classes:
    pytest app/swarms/evolution/tests/test_experimental_evolution.py::TestExperimentalEvolutionEngine -v
"""

from .test_experimental_evolution import (
    TestExperimentalEvolutionConfig,
    TestExperimentalEvolutionEngine,
    TestFactoryFunctions,
    TestIntegrationAdapter,
    TestSafetyValidation,
    TestSwarmChromosome,
)

__all__ = [
    'TestExperimentalEvolutionConfig',
    'TestSwarmChromosome',
    'TestExperimentalEvolutionEngine',
    'TestIntegrationAdapter',
    'TestFactoryFunctions',
    'TestSafetyValidation'
]

# Test configuration for CI/CD
TEST_CONFIG = {
    "experimental_testing_enabled": True,
    "safety_testing_required": True,
    "integration_testing_required": True,
    "performance_testing_enabled": False,  # Disabled for CI speed
    "test_timeout_seconds": 30
}

def get_test_info():
    """Get information about the experimental evolution test suite."""
    return {
        "test_classes": len(__all__),
        "safety_testing": TEST_CONFIG["safety_testing_required"],
        "integration_testing": TEST_CONFIG["integration_testing_required"],
        "experimental_features_tested": True,
        "coverage_areas": [
            "Configuration validation",
            "Genetic algorithm operations",
            "Safety controls and rollback",
            "Integration adapter functionality",
            "Factory function safety",
            "Edge case handling"
        ]
    }
