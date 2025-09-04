"""
Premium Research-Enhanced Audit Swarm Configuration
Integrates cutting-edge AI research agents with latest 2025 best practices
Based on research of HuggingFace GAIA benchmark winners and multi-agent frameworks
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import os

class ResearchAgentTier(Enum):
    """Research agent performance tiers based on 2025 capabilities"""
    FRONTIER = "frontier"        # Latest GPT-5, Claude Sonnet 4, Gemini Ultra
    RESEARCH_GRADE = "research"  # Specialized research models  
    CODE_SPECIALIST = "code"     # DeepSeek, Qwen Coder optimized
    ANALYSIS_ENGINE = "analysis" # Groq, Together AI for fast analysis
    VALIDATION = "validation"    # Cross-validation specialists

class ResearchCapability(Enum):
    """Advanced research capabilities for 2025"""
    LITERATURE_REVIEW = "literature_review"
    TREND_ANALYSIS = "trend_analysis"
    BEST_PRACTICES_RESEARCH = "best_practices_research"
    BENCHMARK_ANALYSIS = "benchmark_analysis"
    FRAMEWORK_EVALUATION = "framework_evaluation"
    PATTERN_DISCOVERY = "pattern_discovery"
    SECURITY_RESEARCH = "security_research"
    PERFORMANCE_RESEARCH = "performance_research"
    ARCHITECTURE_RESEARCH = "architecture_research"
    TOOL_EVALUATION = "tool_evaluation"

# Enhanced model assignments with multiple provider redundancy
PREMIUM_RESEARCH_MODELS = {
    # Frontier Tier - Latest and most capable models
    "research_commander": "openai/gpt-5",                    # OpenAI's latest
    "architecture_researcher": "anthropic/claude-sonnet-4",  # Claude's best
    "security_researcher": "google/gemini-2.5-pro",         # Google's flagship
    "performance_researcher": "x-ai/grok-4",                # xAI's latest
    
    # Research Grade - Specialized research models
    "literature_analyst": "openai/gpt-4.1",                 # Research optimized
    "trend_analyst": "anthropic/claude-3.7-sonnet",         # Trend analysis
    "benchmark_specialist": "google/gemini-2.5-flash",      # Fast benchmarking
    "framework_evaluator": "mistralai/mistral-large-2407",  # Framework analysis
    
    # Code Specialist - Optimized for code analysis
    "code_researcher": "deepseek/deepseek-chat-v3.1",       # Latest DeepSeek
    "pattern_detector": "qwen/qwen3-coder-480b-a35b",       # Qwen Coder
    "quality_researcher": "x-ai/grok-code-fast-1",          # Fast code analysis
    "refactoring_expert": "deepseek/deepseek-chat-v3-0324", # Refactoring specialist
    
    # Analysis Engine - Fast processing and synthesis
    "rapid_researcher": "groq/llama-3.3-70b-versatile",     # Groq speed
    "synthesis_engine": "together/meta-llama-3.1-405b",     # Large context
    "validation_agent": "openai/gpt-4.1-mini",              # Efficient validation
    "cross_validator": "anthropic/claude-3-haiku-20240307", # Quick validation
    
    # HuggingFace Research Models - Direct API access
    "hf_code_analyst": "microsoft/DialoGPT-large",          # Conversational code analysis
    "hf_pattern_finder": "facebook/opt-66b",                # Pattern recognition
    "hf_vulnerability_scanner": "EleutherAI/gpt-j-6b",      # Security focused
    "hf_performance_optimizer": "bigscience/bloom-560m"      # Performance analysis
}

@dataclass
class ResearchAgentSpec:
    """Enhanced agent specification with research capabilities"""
    name: str
    role: str
    model: str
    backup_models: List[str] = field(default_factory=list)
    research_capabilities: List[ResearchCapability] = field(default_factory=list)
    confidence_threshold: float = 0.85
    collaboration_style: str = "researcher"
    research_depth: str = "comprehensive"  # "surface", "standard", "comprehensive", "deep"
    citation_required: bool = True
    validation_rounds: int = 2
    api_provider: str = "openrouter"
    fallback_providers: List[str] = field(default_factory=lambda: ["openai", "anthropic", "groq"])

# Premium Research Agent Roster for 2025
PREMIUM_RESEARCH_AGENTS = {
    "research_commander": ResearchAgentSpec(
        name="AI Research Commander",
        role="research_coordination",
        model=PREMIUM_RESEARCH_MODELS["research_commander"],
        backup_models=["anthropic/claude-sonnet-4", "google/gemini-2.5-pro"],
        research_capabilities=[
            ResearchCapability.LITERATURE_REVIEW,
            ResearchCapability.TREND_ANALYSIS,
            ResearchCapability.FRAMEWORK_EVALUATION
        ],
        confidence_threshold=0.95,
        research_depth="deep",
        validation_rounds=3
    ),
    
    "architecture_researcher": ResearchAgentSpec(
        name="Advanced Architecture Research Agent",
        role="architecture_research",
        model=PREMIUM_RESEARCH_MODELS["architecture_researcher"],
        backup_models=["openai/gpt-5", "x-ai/grok-4"],
        research_capabilities=[
            ResearchCapability.ARCHITECTURE_RESEARCH,
            ResearchCapability.PATTERN_DISCOVERY,
            ResearchCapability.BEST_PRACTICES_RESEARCH
        ],
        confidence_threshold=0.92,
        research_depth="comprehensive"
    ),
    
    "security_researcher": ResearchAgentSpec(
        name="Advanced Security Research Specialist",
        role="security_research",
        model=PREMIUM_RESEARCH_MODELS["security_researcher"],
        backup_models=["anthropic/claude-sonnet-4", "x-ai/grok-4"],
        research_capabilities=[
            ResearchCapability.SECURITY_RESEARCH,
            ResearchCapability.LITERATURE_REVIEW,
            ResearchCapability.BENCHMARK_ANALYSIS
        ],
        confidence_threshold=0.94,
        research_depth="deep",
        validation_rounds=3
    ),
    
    "performance_researcher": ResearchAgentSpec(
        name="Performance Research & Optimization Expert",
        role="performance_research",
        model=PREMIUM_RESEARCH_MODELS["performance_researcher"],
        backup_models=["google/gemini-2.5-pro", "deepseek/deepseek-chat-v3.1"],
        research_capabilities=[
            ResearchCapability.PERFORMANCE_RESEARCH,
            ResearchCapability.BENCHMARK_ANALYSIS,
            ResearchCapability.TOOL_EVALUATION
        ],
        confidence_threshold=0.90,
        research_depth="comprehensive"
    ),
    
    "literature_analyst": ResearchAgentSpec(
        name="AI Literature Analysis Engine",
        role="literature_analysis",
        model=PREMIUM_RESEARCH_MODELS["literature_analyst"],
        backup_models=["anthropic/claude-3.7-sonnet", "mistralai/mistral-large-2407"],
        research_capabilities=[
            ResearchCapability.LITERATURE_REVIEW,
            ResearchCapability.TREND_ANALYSIS,
            ResearchCapability.PATTERN_DISCOVERY
        ],
        confidence_threshold=0.88,
        research_depth="comprehensive",
        citation_required=True
    ),
    
    "trend_analyst": ResearchAgentSpec(
        name="Technology Trend Analysis Agent",
        role="trend_analysis", 
        model=PREMIUM_RESEARCH_MODELS["trend_analyst"],
        backup_models=["google/gemini-2.5-flash", "openai/gpt-4.1"],
        research_capabilities=[
            ResearchCapability.TREND_ANALYSIS,
            ResearchCapability.FRAMEWORK_EVALUATION,
            ResearchCapability.BEST_PRACTICES_RESEARCH
        ],
        confidence_threshold=0.87,
        research_depth="standard"
    ),
    
    "code_researcher": ResearchAgentSpec(
        name="Advanced Code Research Agent",
        role="code_research",
        model=PREMIUM_RESEARCH_MODELS["code_researcher"],
        backup_models=["qwen/qwen3-coder-480b-a35b", "x-ai/grok-code-fast-1"],
        research_capabilities=[
            ResearchCapability.PATTERN_DISCOVERY,
            ResearchCapability.BEST_PRACTICES_RESEARCH,
            ResearchCapability.TOOL_EVALUATION
        ],
        confidence_threshold=0.91,
        research_depth="comprehensive",
        api_provider="deepseek"
    ),
    
    "hf_research_specialist": ResearchAgentSpec(
        name="HuggingFace Research Specialist",
        role="hf_research",
        model=PREMIUM_RESEARCH_MODELS["hf_code_analyst"],
        backup_models=["facebook/opt-66b", "EleutherAI/gpt-j-6b"],
        research_capabilities=[
            ResearchCapability.BENCHMARK_ANALYSIS,
            ResearchCapability.FRAMEWORK_EVALUATION,
            ResearchCapability.TOOL_EVALUATION
        ],
        confidence_threshold=0.85,
        research_depth="standard",
        api_provider="huggingface"
    ),
    
    # Additional agents for formations
    "rapid_researcher": ResearchAgentSpec(
        name="Rapid Research Agent",
        role="rapid_research",
        model=PREMIUM_RESEARCH_MODELS["rapid_researcher"],
        backup_models=["together/meta-llama-3.1-405b", "openai/gpt-4.1-mini"],
        research_capabilities=[
            ResearchCapability.TREND_ANALYSIS,
            ResearchCapability.BEST_PRACTICES_RESEARCH
        ],
        confidence_threshold=0.82,
        research_depth="standard",
        api_provider="groq"
    ),
    
    "synthesis_engine": ResearchAgentSpec(
        name="Research Synthesis Engine",
        role="research_synthesis",
        model=PREMIUM_RESEARCH_MODELS["synthesis_engine"],
        backup_models=["groq/llama-3.3-70b-versatile", "openai/gpt-4.1"],
        research_capabilities=[
            ResearchCapability.PATTERN_DISCOVERY,
            ResearchCapability.FRAMEWORK_EVALUATION
        ],
        confidence_threshold=0.86,
        research_depth="comprehensive"
    ),
    
    "validation_agent": ResearchAgentSpec(
        name="Research Validation Agent",
        role="research_validation",
        model=PREMIUM_RESEARCH_MODELS["validation_agent"],
        backup_models=["anthropic/claude-3-haiku-20240307", "groq/llama-3.3-70b-versatile"],
        research_capabilities=[
            ResearchCapability.BENCHMARK_ANALYSIS,
            ResearchCapability.LITERATURE_REVIEW
        ],
        confidence_threshold=0.88,
        research_depth="standard",
        validation_rounds=3
    ),
    
    "pattern_detector": ResearchAgentSpec(
        name="Pattern Detection Specialist",
        role="pattern_detection",
        model=PREMIUM_RESEARCH_MODELS["pattern_detector"],
        backup_models=["deepseek/deepseek-chat-v3-0324", "x-ai/grok-code-fast-1"],
        research_capabilities=[
            ResearchCapability.PATTERN_DISCOVERY,
            ResearchCapability.BEST_PRACTICES_RESEARCH
        ],
        confidence_threshold=0.89,
        research_depth="comprehensive"
    ),
    
    "framework_evaluator": ResearchAgentSpec(
        name="Framework Evaluation Expert",
        role="framework_evaluation",
        model=PREMIUM_RESEARCH_MODELS["framework_evaluator"],
        backup_models=["google/gemini-2.5-flash", "openai/gpt-4.1"],
        research_capabilities=[
            ResearchCapability.FRAMEWORK_EVALUATION,
            ResearchCapability.TOOL_EVALUATION,
            ResearchCapability.BENCHMARK_ANALYSIS
        ],
        confidence_threshold=0.87,
        research_depth="comprehensive"
    ),
    
    "benchmark_specialist": ResearchAgentSpec(
        name="Benchmark Analysis Specialist",
        role="benchmark_analysis",
        model=PREMIUM_RESEARCH_MODELS["benchmark_specialist"],
        backup_models=["x-ai/grok-4", "google/gemini-2.5-pro"],
        research_capabilities=[
            ResearchCapability.BENCHMARK_ANALYSIS,
            ResearchCapability.PERFORMANCE_RESEARCH
        ],
        confidence_threshold=0.90,
        research_depth="deep",
        validation_rounds=2
    )
}

# Enhanced audit formations with research integration
RESEARCH_ENHANCED_FORMATIONS = {
    "full_research_spectrum": {
        "description": "Complete research-enhanced audit with all premium agents",
        "agents": list(PREMIUM_RESEARCH_AGENTS.keys()),
        "research_phases": [
            "literature_review", 
            "best_practices_research", 
            "trend_analysis", 
            "framework_evaluation",
            "architecture_research",
            "security_research", 
            "performance_research",
            "synthesis_and_validation"
        ],
        "expected_duration": "75-90 minutes",
        "research_depth": "deep",
        "citation_requirement": "mandatory"
    },
    
    "rapid_research_audit": {
        "description": "Fast research-enhanced audit for time-sensitive analysis",
        "agents": [
            "research_commander", "rapid_researcher", "synthesis_engine", 
            "validation_agent", "trend_analyst"
        ],
        "research_phases": [
            "trend_analysis", "rapid_literature_review", "best_practices_synthesis"
        ],
        "expected_duration": "25-35 minutes",
        "research_depth": "standard"
    },
    
    "architecture_research_deep_dive": {
        "description": "Deep architectural research with latest best practices",
        "agents": [
            "research_commander", "architecture_researcher", "pattern_detector",
            "literature_analyst", "framework_evaluator", "synthesis_engine"
        ],
        "research_phases": [
            "architecture_literature_review", "pattern_analysis", "framework_comparison",
            "best_practices_integration", "future_trends_assessment"
        ],
        "expected_duration": "45-60 minutes",
        "research_depth": "deep"
    },
    
    "security_research_audit": {
        "description": "Comprehensive security research with latest threat intelligence",
        "agents": [
            "security_researcher", "hf_research_specialist", "literature_analyst",
            "benchmark_specialist", "validation_agent"
        ],
        "research_phases": [
            "security_literature_review", "threat_landscape_analysis", 
            "vulnerability_research", "compliance_standards_review"
        ],
        "expected_duration": "40-55 minutes",
        "research_depth": "deep"
    },
    
    "performance_research_optimization": {
        "description": "Performance research with latest optimization techniques",
        "agents": [
            "performance_researcher", "benchmark_specialist", "code_researcher",
            "trend_analyst", "synthesis_engine"
        ],
        "research_phases": [
            "performance_literature_review", "benchmark_analysis",
            "optimization_techniques_research", "tool_evaluation"
        ],
        "expected_duration": "35-50 minutes",
        "research_depth": "comprehensive"
    }
}

# Research methodology configuration based on 2025 best practices
RESEARCH_METHODOLOGIES = {
    "systematic_literature_review": {
        "steps": [
            "define_research_questions",
            "search_strategy_development", 
            "inclusion_exclusion_criteria",
            "quality_assessment",
            "data_extraction",
            "synthesis_and_analysis"
        ],
        "min_sources": 20,
        "recency_requirement": "2024-2025 preferred",
        "validation_required": True
    },
    
    "rapid_evidence_synthesis": {
        "steps": [
            "focused_search",
            "quick_quality_filter",
            "key_insights_extraction",
            "trend_identification"
        ],
        "min_sources": 8,
        "recency_requirement": "2025 only",
        "validation_required": False
    },
    
    "benchmark_comparative_analysis": {
        "steps": [
            "benchmark_identification",
            "performance_comparison",
            "methodology_analysis", 
            "recommendations_synthesis"
        ],
        "benchmark_sources": ["HuggingFace", "Papers with Code", "GitHub"],
        "validation_required": True
    }
}

# API Configuration with fallbacks
API_CONFIGURATIONS = {
    "openrouter": {
        "api_key": os.getenv("OPENROUTER_API_KEY", "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"),
        "base_url": "https://openrouter.ai/api/v1",
        "priority": 1
    },
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", "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"),
        "base_url": "https://api.openai.com/v1",
        "priority": 2
    },
    "anthropic": {
        "api_key": os.getenv("ANTHROPIC_API_KEY", "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"),
        "base_url": "https://api.anthropic.com",
        "priority": 3
    },
    "huggingface": {
        "api_key": os.getenv("HUGGINGFACE_API_TOKEN", "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"),
        "base_url": "https://api-inference.huggingface.co",
        "priority": 4
    },
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY", "sk-c8a5f1725d7b4f96b29a3d041848cb74"),
        "base_url": "https://api.deepseek.com",
        "priority": 5
    },
    "groq": {
        "api_key": os.getenv("GROQ_API_KEY", "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"),
        "base_url": "https://api.groq.com/openai/v1",
        "priority": 6
    },
    "together": {
        "api_key": os.getenv("TOGETHER_AI_API_KEY", "tgp_v1_HE_uluFh-fELZDmEP9xKZXuSBT4a8EHd6s9CmSe5WWo"),
        "base_url": "https://api.together.xyz",
        "priority": 7
    },
    "mistral": {
        "api_key": os.getenv("MISTRAL_API_KEY", "jCGVZEeBzppPH0pPVL0vxRCPnZuWL90i"),
        "base_url": "https://api.mistral.ai/v1",
        "priority": 8
    }
}

# Enhanced quality gates for research-enhanced audits
RESEARCH_QUALITY_GATES = {
    "research_coverage_minimum": 85,    # % of research areas covered
    "citation_accuracy_minimum": 90,   # % of citations verified
    "recency_score_minimum": 80,       # % of sources from 2024-2025
    "cross_validation_agreement": 75,  # % agreement between agents
    "methodology_rigor_score": 80,     # Systematic methodology adherence
    "evidence_strength_minimum": 70,   # Evidence quality assessment
    "research_depth_score": 75,        # Comprehensiveness of research
    "innovation_factor_minimum": 60    # Novel insights percentage
}

def get_research_formation_config(formation_name: str) -> Dict[str, Any]:
    """Get configuration for research-enhanced formation"""
    return RESEARCH_ENHANCED_FORMATIONS.get(formation_name, RESEARCH_ENHANCED_FORMATIONS["full_research_spectrum"])

def get_research_agents_for_formation(formation_name: str) -> List[ResearchAgentSpec]:
    """Get research agent specifications for a formation"""
    formation = get_research_formation_config(formation_name)
    return [PREMIUM_RESEARCH_AGENTS[agent_name] for agent_name in formation["agents"]]

def get_api_config(provider: str) -> Dict[str, Any]:
    """Get API configuration with fallback handling"""
    return API_CONFIGURATIONS.get(provider, API_CONFIGURATIONS["openrouter"])

def validate_research_quality(results: Dict[str, Any]) -> Dict[str, bool]:
    """Validate research results against quality gates"""
    validation = {}
    for gate, threshold in RESEARCH_QUALITY_GATES.items():
        if "minimum" in gate:
            validation[gate] = results.get(gate.replace("_minimum", ""), 0) >= threshold
        else:
            validation[gate] = results.get(gate, 0) >= threshold
    return validation