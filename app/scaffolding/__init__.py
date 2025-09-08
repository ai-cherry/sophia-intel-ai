"""
Scaffolding package for meta-tagging and AI enhancement systems.
"""

from .ai_hints import (
    AIHint,
    AIHintsPipeline,
    HintType,
    Severity,
    generate_ai_hints,
    quick_pattern_analysis,
)
from .meta_tagging import (
    AutoTagger,
    Complexity,
    MetaTag,
    MetaTagRegistry,
    ModificationRisk,
    Priority,
    SemanticRole,
    auto_tag_directory,
    get_global_registry,
)
from .semantic_classifier import (
    AnalysisContext,
    ClassificationResult,
    PatternMatch,
    SemanticClassifier,
    detailed_analysis,
    quick_classify,
)

__all__ = [
    # Core meta-tagging
    "MetaTag",
    "MetaTagRegistry",
    "AutoTagger",
    "SemanticRole",
    "Complexity",
    "Priority",
    "ModificationRisk",
    "get_global_registry",
    "auto_tag_directory",
    # Semantic classification
    "SemanticClassifier",
    "ClassificationResult",
    "PatternMatch",
    "AnalysisContext",
    "quick_classify",
    "detailed_analysis",
    # AI hints
    "AIHint",
    "AIHintsPipeline",
    "HintType",
    "Severity",
    "generate_ai_hints",
    "quick_pattern_analysis",
]
