"""
Prioritized Swarm Factory - Optimized Model Assignments Based on Specific Use Cases
Implements the strategic model allocation for coding, scouting, and reasoning tasks
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.aimlapi_config import aimlapi_manager
from app.core.enhanced_llm_router import LLMProviderType, enhanced_router

logger = logging.getLogger(__name__)


class SwarmType(Enum):
    """Types of specialized swarms"""

    CODING_SWARM = "coding_swarm"
    REPOSITORY_SCOUTING = "repository_scouting"
    REASONING_COUNCIL = "reasoning_council"
    ORCHESTRATOR_CONTROL = "orchestrator_control"


@dataclass
class SwarmModelConfig:
    """Configuration for swarm model assignments"""

    swarm_type: SwarmType
    models: List[Dict[str, Any]]
    coordination_strategy: str
    cost_optimization: bool = True


class PrioritizedSwarmFactory:
    """Factory for creating optimized swarms based on prioritized model assignments"""

    def __init__(self):
        self.aimlapi = aimlapi_manager
        self.router = enhanced_router

        # Define swarm configurations based on priorities
        self.swarm_configs = {
            SwarmType.CODING_SWARM: SwarmModelConfig(
                swarm_type=SwarmType.CODING_SWARM,
                models=[
                    {
                        "name": "SpeedCoder",
                        "model": "grok-code-fast-1",
                        "role": "fast_generation",
                        "description": "92 tokens/sec ultra-fast code generation",
                        "cost": "$0.20/$1.50 per 1M tokens",
                        "priority": 1,
                    },
                    {
                        "name": "ContextMaster",
                        "model": "qwen3-coder-480b",
                        "role": "large_context_analysis",
                        "description": "256K-1M token context for massive codebases",
                        "priority": 2,
                    },
                    {
                        "name": "QuickFixer",
                        "model": "glm-4.5-air",
                        "role": "rapid_fixes",
                        "description": "Lightweight rapid response for quick fixes",
                        "priority": 3,
                    },
                ],
                coordination_strategy="parallel_with_aggregation",
                cost_optimization=True,
            ),
            SwarmType.REPOSITORY_SCOUTING: SwarmModelConfig(
                swarm_type=SwarmType.REPOSITORY_SCOUTING,
                models=[
                    {
                        "name": "QuickScanner",
                        "model": "gemini-2.5-flash",
                        "role": "initial_scan",
                        "description": "Fast efficient repository scanning",
                        "priority": 1,
                    },
                    {
                        "name": "PatternScout",
                        "model": "llama-4-scout",
                        "role": "pattern_recognition",
                        "description": "Specialized reconnaissance and pattern finding",
                        "priority": 2,
                    },
                    {
                        "name": "DeepAnalyzer",
                        "model": "llama-4-maverick",
                        "role": "deep_analysis",
                        "description": "Multimodal deep dive, beats GPT-4o",
                        "priority": 3,
                    },
                ],
                coordination_strategy="sequential_refinement",
                cost_optimization=True,
            ),
            SwarmType.REASONING_COUNCIL: SwarmModelConfig(
                swarm_type=SwarmType.REASONING_COUNCIL,
                models=[
                    {
                        "name": "MasterCoordinator",
                        "model": "gpt-5",
                        "role": "orchestration",
                        "description": "GPT-5 master coordination and decision making",
                        "priority": 1,
                    },
                    {
                        "name": "ComplexSolver",
                        "model": "grok-4-heavy",
                        "role": "multi_agent_reasoning",
                        "description": "5-10x compute, 44.4% on Humanity's Last Exam",
                        "priority": 2,
                    },
                    {
                        "name": "StrategicThinker",
                        "model": "claude-opus-4.1",
                        "role": "strategic_analysis",
                        "description": "Nuanced strategic reasoning and analysis",
                        "priority": 3,
                    },
                ],
                coordination_strategy="consensus_with_escalation",
                cost_optimization=False,  # Premium tier for complex reasoning
            ),
            SwarmType.ORCHESTRATOR_CONTROL: SwarmModelConfig(
                swarm_type=SwarmType.ORCHESTRATOR_CONTROL,
                models=[
                    {
                        "name": "PrimaryOrchestrator",
                        "model": "gpt-5",
                        "role": "primary_control",
                        "description": "Main orchestrator using GPT-5",
                        "priority": 1,
                    },
                    {
                        "name": "FallbackOrchestrator",
                        "model": "claude-opus-4.1",
                        "role": "fallback_control",
                        "description": "Fallback orchestrator for reliability",
                        "priority": 2,
                    },
                ],
                coordination_strategy="primary_with_fallback",
                cost_optimization=False,
            ),
        }

        logger.info(
            f"Prioritized Swarm Factory initialized with {len(self.swarm_configs)} swarm types"
        )

    def create_coding_swarm(self, task_description: str) -> Dict[str, Any]:
        """Create an optimized coding swarm"""
        config = self.swarm_configs[SwarmType.CODING_SWARM]

        agents = []
        for model_config in config.models:
            agent = {
                "name": model_config["name"],
                "model": model_config["model"],
                "role": model_config["role"],
                "system_prompt": self._generate_coding_prompt(model_config),
                "priority": model_config["priority"],
                "metadata": model_config,
            }
            agents.append(agent)

        return {
            "swarm_type": "coding_swarm",
            "task": task_description,
            "agents": agents,
            "coordination": config.coordination_strategy,
            "execution_plan": self._generate_coding_execution_plan(task_description),
        }

    def create_repository_scouting_swarm(
        self, repo_path: str, objectives: List[str]
    ) -> Dict[str, Any]:
        """Create a repository scouting swarm"""
        config = self.swarm_configs[SwarmType.REPOSITORY_SCOUTING]

        agents = []
        for model_config in config.models:
            agent = {
                "name": model_config["name"],
                "model": model_config["model"],
                "role": model_config["role"],
                "system_prompt": self._generate_scouting_prompt(model_config, repo_path),
                "priority": model_config["priority"],
                "metadata": model_config,
            }
            agents.append(agent)

        return {
            "swarm_type": "repository_scouting",
            "repo_path": repo_path,
            "objectives": objectives,
            "agents": agents,
            "coordination": config.coordination_strategy,
            "execution_plan": self._generate_scouting_execution_plan(objectives),
        }

    def create_reasoning_council(
        self, problem: str, complexity_level: str = "high"
    ) -> Dict[str, Any]:
        """Create a reasoning council for complex problems"""
        config = self.swarm_configs[SwarmType.REASONING_COUNCIL]

        agents = []
        for model_config in config.models:
            agent = {
                "name": model_config["name"],
                "model": model_config["model"],
                "role": model_config["role"],
                "system_prompt": self._generate_reasoning_prompt(model_config, complexity_level),
                "priority": model_config["priority"],
                "metadata": model_config,
            }
            agents.append(agent)

        return {
            "swarm_type": "reasoning_council",
            "problem": problem,
            "complexity": complexity_level,
            "agents": agents,
            "coordination": config.coordination_strategy,
            "execution_plan": self._generate_reasoning_execution_plan(complexity_level),
        }

    def _generate_coding_prompt(self, model_config: Dict) -> str:
        """Generate specialized prompts for coding agents"""
        prompts = {
            "fast_generation": f"""You are {model_config['name']}, powered by Grok Code Fast 1.
You are the SPEED LEADER of the coding swarm with 92 tokens/second throughput.
Your role: Generate initial code implementations FAST.
- Focus on rapid prototyping and initial structure
- Write clean, functional code quickly
- Pass to ContextMaster for deep analysis if needed
- Cost-optimized at $0.20/$1.50 per 1M tokens""",
            "large_context_analysis": f"""You are {model_config['name']}, powered by Qwen3-Coder-480B.
You are the CONTEXT MASTER handling 256K-1M token contexts.
Your role: Analyze and refactor large codebases.
- Handle massive files and multi-file analysis
- Perform deep refactoring and optimization
- Maintain context across entire repositories
- 480B parameters with 35B active for elite coding""",
            "rapid_fixes": f"""You are {model_config['name']}, powered by GLM-4.5-Air.
You are the QUICK FIXER for rapid validations and syntax fixes.
Your role: Fast validation and quick fixes.
- Syntax checking and quick corrections
- Rapid unit test generation
- Quick documentation updates
- Lightweight and efficient processing""",
        }
        return prompts.get(model_config["role"], f"You are {model_config['name']}")

    def _generate_scouting_prompt(self, model_config: Dict, repo_path: str) -> str:
        """Generate specialized prompts for scouting agents"""
        prompts = {
            "initial_scan": f"""You are {model_config['name']}, powered by Gemini 2.5 Flash.
You are the QUICK SCANNER for repository {repo_path}.
Your role: Fast initial repository scanning.
- Quickly identify repository structure
- Find key files and patterns
- Create initial map for deeper analysis
- Optimized for speed and efficiency""",
            "pattern_recognition": f"""You are {model_config['name']}, powered by Llama-4-Scout.
You are the PATTERN SCOUT for repository {repo_path}.
Your role: Specialized reconnaissance and pattern finding.
- Identify architectural patterns
- Find code smells and antipatterns
- Detect security vulnerabilities
- Map dependencies and relationships""",
            "deep_analysis": f"""You are {model_config['name']}, powered by Llama-4-Maverick.
You are the DEEP ANALYZER for repository {repo_path}.
Your role: Comprehensive multimodal analysis.
- Deep dive into complex areas
- Analyze code quality and performance
- Vision capabilities for diagrams/screenshots
- Performance that beats GPT-4o and Gemini 2.0 Flash""",
        }
        return prompts.get(model_config["role"], f"You are {model_config['name']}")

    def _generate_reasoning_prompt(self, model_config: Dict, complexity: str) -> str:
        """Generate specialized prompts for reasoning agents"""
        prompts = {
            "orchestration": f"""You are {model_config['name']}, the MASTER COORDINATOR powered by GPT-5.
You orchestrate the reasoning council for {complexity} complexity problems.
Your role: Coordinate and synthesize all reasoning.
- Direct other agents based on problem requirements
- Synthesize insights from multiple perspectives
- Make final decisions and recommendations
- Leverage GPT-5's 256K context and advanced reasoning""",
            "multi_agent_reasoning": f"""You are {model_config['name']}, powered by Grok 4 Heavy.
You handle MULTI-AGENT REASONING with 5-10x test-time compute.
Your role: Solve complex problems through multi-agent collaboration.
- Achieved 44.4% on Humanity's Last Exam (vs 26.9% for Gemini 2.5 Pro)
- Coordinate multiple reasoning paths
- Handle problems requiring deep computation
- Priority processing for fastest response times""",
            "strategic_analysis": f"""You are {model_config['name']}, powered by Claude Opus 4.1.
You provide STRATEGIC ANALYSIS with nuanced understanding.
Your role: Deep strategic and business reasoning.
- Analyze complex strategic scenarios
- Provide nuanced, balanced perspectives
- Consider long-term implications
- Excel at business and organizational analysis""",
        }
        return prompts.get(model_config["role"], f"You are {model_config['name']}")

    def _generate_coding_execution_plan(self, task: str) -> Dict[str, Any]:
        """Generate execution plan for coding swarm"""
        return {
            "phases": [
                {
                    "phase": 1,
                    "agent": "SpeedCoder",
                    "action": "Generate initial implementation",
                    "estimated_time": "5-10 seconds",
                },
                {
                    "phase": 2,
                    "agent": "ContextMaster",
                    "action": "Analyze context and refactor if needed",
                    "condition": "if_context_exceeds_10k_tokens",
                },
                {
                    "phase": 3,
                    "agent": "QuickFixer",
                    "action": "Validate and fix any issues",
                    "estimated_time": "2-5 seconds",
                },
            ],
            "optimization": "Use Grok Code Fast for 90% cost savings on simple tasks",
        }

    def _generate_scouting_execution_plan(self, objectives: List[str]) -> Dict[str, Any]:
        """Generate execution plan for repository scouting"""
        return {
            "phases": [
                {
                    "phase": 1,
                    "agent": "QuickScanner",
                    "action": "Initial repository scan",
                    "output": "Repository structure map",
                },
                {
                    "phase": 2,
                    "agent": "PatternScout",
                    "action": "Pattern and vulnerability detection",
                    "output": "Pattern analysis report",
                },
                {
                    "phase": 3,
                    "agent": "DeepAnalyzer",
                    "action": "Deep dive on identified areas",
                    "output": "Comprehensive analysis",
                },
            ],
            "objectives": objectives,
        }

    def _generate_reasoning_execution_plan(self, complexity: str) -> Dict[str, Any]:
        """Generate execution plan for reasoning council"""
        if complexity == "extreme":
            return {
                "primary": "grok-4-heavy",
                "strategy": "Use Grok 4 Heavy's multi-agent reasoning",
                "fallback": "gpt-5",
                "escalation": "Escalate to human if confidence < 70%",
            }
        else:
            return {
                "primary": "gpt-5",
                "strategy": "GPT-5 coordinates with specialist input",
                "support": ["claude-opus-4.1", "grok-4-heavy"],
                "consensus": "Require agreement from 2/3 agents",
            }

    def get_cost_estimate(self, swarm_type: SwarmType, estimated_tokens: int) -> Dict[str, float]:
        """Estimate costs for different swarm configurations"""
        cost_per_million = {
            "grok-code-fast-1": {"input": 0.20, "output": 1.50},
            "grok-3-mini": {"input": 0.30, "output": 0.50},
            "grok-4": {"input": 3.00, "output": 15.00},
            "grok-4-heavy": {"input": 5.00, "output": 25.00},  # Estimated premium
            "gpt-5": {"input": 4.00, "output": 20.00},  # Estimated
            "claude-opus-4.1": {"input": 3.50, "output": 17.50},  # Estimated
            "gemini-2.5-flash": {"input": 0.50, "output": 1.50},  # Estimated
        }

        config = self.swarm_configs[swarm_type]
        total_cost = 0.0

        for model_config in config.models:
            model = model_config["model"]
            if model in cost_per_million:
                costs = cost_per_million[model]
                # Assume 30% input, 70% output for estimation
                est_cost = (
                    estimated_tokens * 0.3 * costs["input"] / 1_000_000
                    + estimated_tokens * 0.7 * costs["output"] / 1_000_000
                )
                total_cost += est_cost

        return {
            "estimated_cost": total_cost,
            "tokens": estimated_tokens,
            "swarm_type": swarm_type.value,
        }


# Singleton instance
prioritized_swarm_factory = PrioritizedSwarmFactory()
