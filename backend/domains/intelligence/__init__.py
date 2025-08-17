"""
Intelligence Domain - AI-powered development pipeline and adaptive architecture
Handles code generation, architecture adaptation, and continuous improvement
"""

from .service import IntelligenceService
from .models import CodeGenerationRequest, ArchitectureAnalysis, ImprovementSuggestion
from .code_generator import AICodeGenerator
from .architecture_adapter import ArchitectureAdapter
from .improvement_agent import ContinuousImprovementAgent

__all__ = [
    "IntelligenceService",
    "CodeGenerationRequest",
    "ArchitectureAnalysis", 
    "ImprovementSuggestion",
    "AICodeGenerator",
    "ArchitectureAdapter",
    "ContinuousImprovementAgent"
]

