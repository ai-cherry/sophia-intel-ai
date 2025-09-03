"""
Improved Agent Swarm System with 8 Enhancement Patterns
Combines MCP-UI integration with advanced swarm coordination patterns
"""

import asyncio
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.ai_logger import logger

logger = logging.getLogger(__name__)

# ============================================
# Pattern 1: Structured Adversarial Debate
# ============================================

class AdversarialDebateSystem:
    """Implements structured debate between agents to improve solution quality."""

    def __init__(self, agents: list[Any]):
        self.agents = agents
        self.debate_history = []

    async def conduct_debate(self, problem: str, solutions: list[dict]) -> dict:
        """Run adversarial debate on proposed solutions."""
        debate_results = []

        for solution in solutions:
            # Assign random advocate and critic
            advocate = random.choice(self.agents)
            remaining = [a for a in self.agents if a != advocate]
            critic = random.choice(remaining) if remaining else advocate

            # Generate arguments
            pro_argument = await self._generate_pro_argument(advocate, solution)
            con_argument = await self._generate_con_argument(critic, solution)

            # Judge evaluates
            judge = random.choice([a for a in self.agents if a not in [advocate, critic]])
            verdict = await self._evaluate_arguments(judge, pro_argument, con_argument, solution)

            debate_results.append({
                "solution": solution,
                "pro_argument": pro_argument,
                "con_argument": con_argument,
                "verdict": verdict,
                "score": verdict.get("score", 0.5)
            })

        # Select best solution based on debate outcomes
        best_debate = max(debate_results, key=lambda x: x["score"])
        self.debate_history.append({
            "problem": problem,
            "winner": best_debate,
            "timestamp": datetime.now().isoformat()
        })

        return best_debate

    async def _generate_pro_argument(self, agent, solution):
        """Generate supporting argument for solution."""
        return {
            "agent": str(agent),
            "stance": "support",
            "points": [
                "Efficient implementation",
                "Scalable architecture",
                "Well-tested approach"
            ],
            "confidence": 0.85
        }

    async def _generate_con_argument(self, agent, solution):
        """Generate opposing argument against solution."""
        return {
            "agent": str(agent),
            "stance": "oppose",
            "points": [
                "Potential edge cases not covered",
                "Performance concerns at scale",
                "Maintenance complexity"
            ],
            "confidence": 0.75
        }

    async def _evaluate_arguments(self, judge, pro, con, solution):
        """Judge evaluates both arguments."""
        # Simulate evaluation logic
        pro_strength = pro["confidence"]
        con_strength = con["confidence"]

        if pro_strength > con_strength:
            decision = "accept"
            score = pro_strength
        else:
            decision = "reject"
            score = 1 - con_strength

        return {
            "judge": str(judge),
            "decision": decision,
            "score": score,
            "reasoning": f"Pro argument strength: {pro_strength}, Con: {con_strength}"
        }


# ============================================
# Pattern 2: Quality Gates with Automatic Retry
# ============================================

class QualityGateSystem:
    """Implements quality thresholds with automatic retry strategies."""

    def __init__(self, config: dict):
        self.config = config
        self.min_quality = config.get("min_quality_threshold", 0.7)
        self.max_retries = config.get("max_retry_rounds", 3)
        self.retry_strategies = config.get("retry_strategies", {})

    async def execute_with_quality_gates(self, problem: dict, agents: list) -> dict:
        """Execute workflow with quality gates and retries."""

        for round_num in range(self.max_retries):
            # Execute agent workflow
            result = await self._execute_workflow(problem, agents)
            quality_score = await self._assess_quality(result)

            logger.info(f"Round {round_num + 1}: Quality score = {quality_score}")

            if quality_score >= self.min_quality:
                return {
                    "result": result,
                    "quality_score": quality_score,
                    "rounds_required": round_num + 1,
                    "status": "success"
                }

            # Apply retry strategy based on quality level
            if quality_score < 0.4 and "low_quality" in self.retry_strategies:
                agents = await self._expand_agent_team(agents)
            elif quality_score < 0.6 and "medium_quality" in self.retry_strategies:
                agents = await self._increase_creativity(agents)

        return {
            "result": result,
            "quality_score": quality_score,
            "rounds_required": self.max_retries,
            "status": "max_rounds_exceeded"
        }

    async def _execute_workflow(self, problem, agents):
        """Execute the agent workflow WITH REAL LLM via OpenRouter."""
        # Import REAL OpenRouter gateway
        from app.api.openrouter_gateway import execute_real_llm_call

        # Make REAL API call via OpenRouter
        try:
            # Build prompt from problem
            prompt = problem.get("query") or problem.get("description") or str(problem)

            # Execute with REAL OpenRouter API
            response = await execute_real_llm_call(
                prompt=prompt,
                role="generator",  # Use generator role for problem solving
                temperature=0.7,
                max_tokens=2048
            )

            # Return REAL response from OpenRouter
            return {
                "solution": response.get("content", ""),
                "confidence": response.get("metadata", {}).get("real_api_call", False) and 0.9 or 0.5,
                "model_used": response.get("metadata", {}).get("model_used", "unknown"),
                "real_api": response.get("metadata", {}).get("real_api_call", False),
                "provider": response.get("metadata", {}).get("provider", "unknown")
            }
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            # Still try to return something useful
            return {
                "solution": f"Error with OpenRouter API: {str(e)}",
                "confidence": 0.1,
                "error": str(e),
                "real_api": False
            }

    async def _assess_quality(self, result):
        """Assess solution quality."""
        # Simulate quality assessment
        return result.get("confidence", 0.5)

    async def _expand_agent_team(self, agents):
        """Add more agents to the team."""
        logger.info("Expanding agent team due to low quality")
        # In real implementation, would add specialized agents
        return agents + ["specialist_agent"]

    async def _increase_creativity(self, agents):
        """Adjust agent parameters for more creative solutions."""
        logger.info("Increasing creativity parameters")
        # In real implementation, would adjust temperature/top_p
        return agents


# ============================================
# Pattern 3: Strategy Archive and Reuse
# ============================================

class StrategyArchive:
    """Archives and reuses successful agent interaction patterns."""

    def __init__(self, archive_path: str = "data/strategy_archive.json"):
        self.archive_path = Path(archive_path)
        self.patterns = self._load_archive()

    def _load_archive(self) -> dict:
        """Load existing archive from disk."""
        if self.archive_path.exists():
            with open(self.archive_path) as f:
                return json.load(f)
        return {"problem_types": {}}

    def save_archive(self):
        """Save archive to disk."""
        self.archive_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.archive_path, 'w') as f:
            json.dump(self.patterns, f, indent=2)

    def archive_success(self, problem_type: str, roles: list[str],
                       interaction_sequence: str, quality_score: float):
        """Archive a successful pattern."""
        if quality_score < 0.8:
            return  # Only archive high-quality solutions

        pattern = {
            "pattern_id": f"{problem_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "roles": roles,
            "interaction_sequence": interaction_sequence,
            "success_score": quality_score,
            "usage_count": 1,
            "last_updated": datetime.now().isoformat()
        }

        if problem_type not in self.patterns["problem_types"]:
            self.patterns["problem_types"][problem_type] = {"successful_patterns": []}

        self.patterns["problem_types"][problem_type]["successful_patterns"].append(pattern)
        self.save_archive()
        logger.info(f"Archived successful pattern for {problem_type}")

    def retrieve_best_pattern(self, problem_type: str) -> dict | None:
        """Retrieve the best pattern for a problem type."""
        if problem_type not in self.patterns["problem_types"]:
            return None

        patterns = self.patterns["problem_types"][problem_type]["successful_patterns"]
        if not patterns:
            return None

        best_pattern = max(patterns, key=lambda x: x["success_score"])
        best_pattern["usage_count"] += 1
        self.save_archive()

        return best_pattern


# ============================================
# Pattern 4: Simple Safety Boundaries
# ============================================

class SafetyBoundarySystem:
    """Implements safety controls to prevent harmful behavior."""

    def __init__(self, config: dict):
        self.config = config
        self.max_risk = config.get("max_risk_level", 0.7)
        self.prohibited_actions = set(config.get("prohibited_actions", []))
        self.require_approval = set(config.get("require_human_approval", []))

    async def check_safety(self, task: dict) -> tuple[bool, dict]:
        """Check if task is safe to execute."""

        # Assess risk level
        risk_score = await self._assess_risk(task)

        if risk_score > self.max_risk:
            return False, {
                "status": "rejected",
                "reason": "Risk score exceeds maximum threshold",
                "risk_score": risk_score
            }

        # Check for prohibited actions
        detected_actions = await self._detect_actions(task)
        prohibited = detected_actions & self.prohibited_actions

        if prohibited:
            return False, {
                "status": "rejected",
                "reason": f"Contains prohibited actions: {prohibited}",
                "detected_actions": list(detected_actions)
            }

        # Check if human approval needed
        needs_approval = detected_actions & self.require_approval

        if needs_approval:
            return True, {
                "status": "requires_approval",
                "actions_requiring_approval": list(needs_approval),
                "risk_score": risk_score
            }

        return True, {
            "status": "approved",
            "risk_score": risk_score,
            "detected_actions": list(detected_actions)
        }

    async def _assess_risk(self, task):
        """Assess risk level of task."""
        # Simulate risk assessment
        keywords = ["delete", "modify", "execute", "system", "credential"]
        task_str = str(task).lower()
        risk = sum(0.2 for kw in keywords if kw in task_str)
        return min(risk, 1.0)

    async def _detect_actions(self, task):
        """Detect actions in task."""
        # Simulate action detection
        actions = set()
        task_str = str(task).lower()

        if "file" in task_str:
            actions.add("file_system_write")
        if "code" in task_str:
            actions.add("code_execution")
        if "api" in task_str:
            actions.add("external_api_calls")

        return actions


# ============================================
# Pattern 5: Dynamic Role Assignment
# ============================================

class DynamicRoleAssigner:
    """Assigns agent roles based on problem analysis."""

    def __init__(self, config: dict):
        self.config = config
        self.complexity_thresholds = config.get("complexity_thresholds", {})
        self.domain_specs = config.get("domain_specializations", {})

    async def assign_roles(self, problem: dict) -> list[str]:
        """Dynamically assign roles based on problem characteristics."""

        # Analyze problem complexity
        complexity = await self._analyze_complexity(problem)

        # Determine base roles from complexity
        if complexity < 0.3:
            roles = ["generator", "validator"]
        elif complexity < 0.7:
            roles = ["planner", "generator", "critic"]
        else:
            roles = ["planner", "specialist_a", "specialist_b", "critic", "judge"]

        # Add domain-specific roles
        domain = await self._identify_domain(problem)
        if domain in self.domain_specs:
            domain_roles = self.domain_specs[domain]
            roles = self._merge_roles(roles, domain_roles)

        logger.info(f"Assigned roles for complexity {complexity}: {roles}")
        return roles

    async def _analyze_complexity(self, problem):
        """Analyze problem complexity."""
        # Simulate complexity analysis
        problem_str = str(problem)
        complexity = min(len(problem_str) / 1000, 1.0)
        return complexity

    async def _identify_domain(self, problem):
        """Identify problem domain."""
        problem_str = str(problem).lower()

        if "code" in problem_str or "function" in problem_str:
            return "code"
        elif "research" in problem_str or "analyze" in problem_str:
            return "research"
        elif "data" in problem_str:
            return "analysis"

        return "general"

    def _merge_roles(self, base_roles, domain_roles):
        """Merge base and domain-specific roles."""
        # Keep unique roles while preserving order
        seen = set()
        merged = []

        for role in base_roles + domain_roles:
            if role not in seen:
                seen.add(role)
                merged.append(role)

        return merged[:7]  # Limit to 7 roles max


# ============================================
# Pattern 6: Consensus with Tie-Breaking
# ============================================

class ConsensusSystem:
    """Handles disagreements between agents systematically."""

    def __init__(self, config: dict):
        self.config = config
        self.agreement_threshold = config.get("agreement_threshold", 0.7)
        self.tie_breaking = config.get("tie_breaking_methods", {})

    async def reach_consensus(self, agents: list, options: list) -> dict:
        """Reach consensus among agents."""

        # Collect votes from all agents
        votes = await self._collect_votes(agents, options)

        # Calculate agreement level
        agreement_level = self._calculate_agreement(votes)

        if agreement_level >= self.agreement_threshold:
            # Clear consensus reached
            winner = max(votes.items(), key=lambda x: x[1])[0]
            return {
                "consensus": True,
                "winner": winner,
                "agreement_level": agreement_level,
                "votes": votes
            }

        # Need tie-breaking
        tied_options = self._get_tied_options(votes)

        if len(agents) <= 3:
            # Small group - use judge
            winner = await self._judge_tiebreak(tied_options)
        else:
            # Large group - use ranked voting
            winner = await self._ranked_voting(agents, tied_options)

        return {
            "consensus": False,
            "winner": winner,
            "agreement_level": agreement_level,
            "tie_broken_by": "judge" if len(agents) <= 3 else "ranked_voting",
            "votes": votes
        }

    async def _collect_votes(self, agents, options):
        """Collect votes from agents."""
        votes = dict.fromkeys(options, 0)

        for agent in agents:
            # Simulate voting
            choice = random.choice(options)
            votes[choice] += 1

        return votes

    def _calculate_agreement(self, votes):
        """Calculate agreement level."""
        if not votes:
            return 0

        total_votes = sum(votes.values())
        max_votes = max(votes.values())

        return max_votes / total_votes if total_votes > 0 else 0

    def _get_tied_options(self, votes):
        """Get options with highest votes."""
        max_votes = max(votes.values())
        return [opt for opt, v in votes.items() if v == max_votes]

    async def _judge_tiebreak(self, options):
        """Use judge agent for tie-breaking."""
        return random.choice(options)

    async def _ranked_voting(self, agents, options):
        """Use ranked choice voting."""
        # Simulate ranked voting
        return random.choice(options)


# ============================================
# Pattern 7: Adaptive Parameters
# ============================================

class AdaptiveParameterManager:
    """Manages adaptive parameters based on performance."""

    def __init__(self, config: dict):
        self.config = config
        self.parameters = config.get("parameters", {})
        self.learning_rate = config.get("learning_rate", 0.1)
        self.history_window = config.get("history_window", 5)
        self.performance_history = []

    def update_parameters(self, result: dict):
        """Update parameters based on performance."""

        quality_score = result.get("quality_score", 0.5)
        self.performance_history.append(quality_score)

        # Keep only recent history
        if len(self.performance_history) > self.history_window:
            self.performance_history.pop(0)

        # Calculate average performance
        avg_performance = sum(self.performance_history) / len(self.performance_history)

        # Adjust parameters based on performance
        if avg_performance < 0.6:
            # Poor performance - increase diversity
            self._adjust_parameter("temperature", 0.1)
            self._adjust_parameter("agent_count", 1)
        elif avg_performance > 0.85:
            # Excellent performance - optimize for efficiency
            self._adjust_parameter("temperature", -0.05)
            self._adjust_parameter("agent_count", 0)

        logger.info(f"Parameters adjusted. Avg performance: {avg_performance:.2f}")

    def _adjust_parameter(self, param_name: str, delta: float):
        """Adjust a single parameter."""
        if param_name not in self.parameters:
            return

        param_config = self.parameters[param_name]
        current = param_config.get("current", param_config["default"])

        new_value = current + (delta * self.learning_rate)
        new_value = max(param_config["min"], min(param_config["max"], new_value))

        param_config["current"] = new_value
        logger.debug(f"Adjusted {param_name}: {current:.2f} -> {new_value:.2f}")

    def get_current_parameters(self) -> dict:
        """Get current parameter values."""
        return {
            name: config.get("current", config["default"])
            for name, config in self.parameters.items()
        }


# ============================================
# Pattern 8: Cross-Domain Knowledge Transfer
# ============================================

class KnowledgeTransferSystem:
    """Transfers successful strategies between problem domains."""

    def __init__(self, config: dict):
        self.config = config
        self.transfer_threshold = config.get("transfer_success_threshold", 0.6)
        self.domain_mappings = {}
        self.transfer_history = []

    async def attempt_transfer(self, source_domain: str, target_domain: str,
                              pattern: dict) -> dict | None:
        """Attempt to transfer knowledge between domains."""

        # Calculate similarity between domains
        similarity = await self._calculate_domain_similarity(source_domain, target_domain)

        if similarity < self.transfer_threshold:
            return None

        # Adapt pattern for target domain
        adapted_pattern = await self._adapt_pattern(pattern, source_domain, target_domain)

        # Test adapted pattern
        success_rate = await self._test_adaptation(adapted_pattern, target_domain)

        if success_rate >= self.transfer_threshold:
            self.transfer_history.append({
                "source": source_domain,
                "target": target_domain,
                "pattern": adapted_pattern,
                "success_rate": success_rate,
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"Successfully transferred pattern from {source_domain} to {target_domain}")
            return adapted_pattern

        return None

    async def _calculate_domain_similarity(self, domain1, domain2):
        """Calculate similarity between domains."""
        # Simulate similarity calculation
        if domain1 == domain2:
            return 1.0

        related = {
            "code": ["analysis", "research"],
            "research": ["analysis", "code"],
            "analysis": ["code", "research"]
        }

        if domain2 in related.get(domain1, []):
            return 0.7

        return 0.3

    async def _adapt_pattern(self, pattern, source, target):
        """Adapt pattern from source to target domain."""
        adapted = pattern.copy()

        # Adapt terminology
        if source == "code" and target == "research":
            adapted["roles"] = [r.replace("code_", "research_") for r in adapted.get("roles", [])]

        return adapted

    async def _test_adaptation(self, pattern, domain):
        """Test adapted pattern in target domain."""
        # Simulate testing
        return random.uniform(0.5, 0.9)


# ============================================
# Main Improved Agent Swarm Class
# ============================================

class ImprovedAgentSwarm:
    """Unified improved agent swarm with optimized pattern selection."""

    def __init__(self, agents: list, config_file: str = "swarm_config.json"):
        self.agents = agents
        self.config = self._load_config(config_file)

        # Initialize optimizer for pattern selection
        try:
            from app.swarms.performance_optimizer import SwarmOptimizer
            self.optimizer = SwarmOptimizer()
        except ImportError:
            logger.warning("SwarmOptimizer not available - using basic optimization")
            self.optimizer = None

        # Initialize patterns based on optimization mode
        self.optimization_mode = self.config.get("optimization", "balanced")
        self.enabled_patterns = self.config.get("enabled_patterns", ["all"])

        # Always initialize safety system (critical)
        self.safety_system = SafetyBoundarySystem(self.config.get("safety_config", {}))

        # Initialize patterns based on configuration
        self.patterns = self._initialize_patterns_selectively()

        # Backward compatibility attributes
        self.debate_system = self.patterns.get("debate")
        self.quality_gates = self.patterns.get("quality_gates", self._create_minimal_quality_gates())
        self.strategy_archive = self.patterns.get("strategy_archive")
        self.role_assigner = self.patterns.get("role_assigner")
        self.consensus_system = self.patterns.get("consensus")
        self.param_manager = self.patterns.get("param_manager")
        self.transfer_system = self.patterns.get("transfer_system")

        # Performance tracking with optimization awareness
        self.performance_history = []
        self.pattern_usage_stats = {}
        self.pattern_effectiveness = {}

        logger.info(f"Improved Agent Swarm initialized with {self.optimization_mode} mode ({len(self.patterns)} patterns)")

    def _load_config(self, config_file: str) -> dict:
        """Load configuration from file."""
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)

        # Return default config if file doesn't exist
        return self._get_default_config()

    def _initialize_patterns_selectively(self) -> dict[str, Any]:
        """Initialize patterns based on optimization configuration."""
        patterns = {}

        # Determine which patterns to enable based on mode and config
        if self.enabled_patterns == ["all"] or "all" in self.enabled_patterns:
            # Enable patterns based on optimization mode
            if self.optimization_mode == "lite":
                enabled = ["quality_gates"]
            elif self.optimization_mode == "balanced":
                enabled = ["quality_gates", "debate", "strategy_archive", "role_assigner"]
            else:  # quality mode
                enabled = ["debate", "quality_gates", "strategy_archive", "role_assigner",
                          "consensus", "param_manager", "transfer_system"]
        else:
            enabled = self.enabled_patterns

        # Initialize enabled patterns
        if "debate" in enabled:
            patterns["debate"] = AdversarialDebateSystem(self.agents)

        if "quality_gates" in enabled:
            patterns["quality_gates"] = QualityGateSystem(self.config.get("quality_gates", {}))

        if "strategy_archive" in enabled:
            patterns["strategy_archive"] = StrategyArchive()

        if "role_assigner" in enabled:
            patterns["role_assigner"] = DynamicRoleAssigner(self.config.get("role_assignment", {}))

        if "consensus" in enabled:
            patterns["consensus"] = ConsensusSystem(self.config.get("consensus_config", {}))

        if "param_manager" in enabled:
            patterns["param_manager"] = AdaptiveParameterManager(self.config.get("adaptive_parameters", {}))

        if "transfer_system" in enabled:
            patterns["transfer_system"] = KnowledgeTransferSystem(self.config.get("knowledge_transfer", {}))

        return patterns

    def _create_minimal_quality_gates(self) -> QualityGateSystem:
        """Create minimal quality gates when not enabled."""
        minimal_config = {
            "min_quality_threshold": 0.6,
            "max_retry_rounds": 1,
            "retry_strategies": {}
        }
        return QualityGateSystem(minimal_config)

    def _get_default_config(self) -> dict:
        """Get default configuration with optimization settings."""
        return {
            "optimization": "balanced",
            "enabled_patterns": ["all"],
            "quality_gates": {
                "min_quality_threshold": 0.7,
                "max_retry_rounds": 3,
                "retry_strategies": {
                    "low_quality": {"threshold": 0.4, "action": "expand_agent_team"},
                    "medium_quality": {"threshold": 0.6, "action": "increase_creativity"}
                }
            },
            "safety_config": {
                "max_risk_level": 0.7,
                "prohibited_actions": ["file_delete", "system_modification"],
                "require_human_approval": ["code_execution", "external_api_calls"]
            },
            "role_assignment": {
                "complexity_thresholds": {
                    "simple": {"max": 0.3, "roles": ["generator", "validator"]},
                    "medium": {"max": 0.7, "roles": ["planner", "generator", "critic"]},
                    "complex": {"max": 1.0, "roles": ["planner", "specialist_a", "specialist_b", "critic", "judge"]}
                }
            },
            "consensus_config": {
                "agreement_threshold": 0.7,
                "tie_breaking_methods": {
                    "small_group": {"max_agents": 3, "method": "judge_agent"},
                    "large_group": {"min_agents": 4, "method": "ranked_voting"}
                }
            },
            "adaptive_parameters": {
                "parameters": {
                    "temperature": {"min": 0.1, "max": 1.0, "default": 0.7},
                    "agent_count": {"min": 2, "max": 10, "default": 3}
                },
                "learning_rate": 0.1,
                "history_window": 5
            },
            "knowledge_transfer": {
                "transfer_success_threshold": 0.6
            }
        }

    async def solve_with_improvements(self, problem: dict) -> dict:
        """Solve problem using all improvement patterns."""

        start_time = datetime.now()

        # Pattern 4: Safety check first
        is_safe, safety_result = await self.safety_system.check_safety(problem)
        if not is_safe:
            return safety_result

        # Dynamic mode selection from upstream dispatcher (if provided)
        # Allows NL dispatcher or API caller to select lite/balanced/quality per-task
        desired_mode = problem.get("mode", self.optimization_mode)
        if desired_mode and desired_mode != self.optimization_mode:
            logger.info(f"Switching optimization mode: {self.optimization_mode} -> {desired_mode}")
            self.optimization_mode = desired_mode
            # Re-initialize patterns based on new mode
            self.patterns = self._initialize_patterns_selectively()
            # Refresh pattern handles
            self.debate_system = self.patterns.get("debate")
            self.quality_gates = self.patterns.get("quality_gates", self._create_minimal_quality_gates())
            self.strategy_archive = self.patterns.get("strategy_archive")
            self.role_assigner = self.patterns.get("role_assigner")
            self.consensus_system = self.patterns.get("consensus")
            self.param_manager = self.patterns.get("param_manager")
            self.transfer_system = self.patterns.get("transfer_system")

        # Pattern 5: Dynamic role assignment
        problem_type = problem.get("type", "general")
        agent_roles = await self.role_assigner.assign_roles(problem)

        # Pattern 3: Check strategy archive
        archived_pattern = self.strategy_archive.retrieve_best_pattern(problem_type)
        if archived_pattern:
            logger.info(f"Using archived pattern: {archived_pattern['pattern_id']}")
            agent_roles = archived_pattern.get("roles", agent_roles)

        # Pattern 2: Quality-gated execution
        initial_result = await self.quality_gates.execute_with_quality_gates(
            problem, self.agents[:len(agent_roles)]
        )

        # Pattern 1: Adversarial debate if quality is borderline
        if 0.6 <= initial_result["quality_score"] < 0.8:
            logger.info("Running adversarial debate to improve solution")

            # Generate alternative solutions
            alternatives = [initial_result["result"]] + [
                {"solution": f"Alternative {i}", "confidence": random.uniform(0.5, 0.9)}
                for i in range(2)
            ]

            debate_result = await self.debate_system.conduct_debate(
                str(problem), alternatives
            )
            initial_result["result"] = debate_result["solution"]
            initial_result["quality_score"] = debate_result["score"]

        # Pattern 6: Consensus if multiple valid solutions
        if initial_result.get("multiple_solutions"):
            consensus_result = await self.consensus_system.reach_consensus(
                self.agents, initial_result["multiple_solutions"]
            )
            initial_result["consensus"] = consensus_result

        # Archive successful pattern
        if initial_result["quality_score"] > 0.8:
            self.strategy_archive.archive_success(
                problem_type,
                agent_roles,
                "standard_flow",
                initial_result["quality_score"]
            )

        # Pattern 7: Update adaptive parameters
        if self.param_manager:
            self.param_manager.update_parameters(initial_result)

        # Pattern 8: Attempt knowledge transfer
        if initial_result["quality_score"] > 0.85 and self.transfer_system:
            for target_domain in ["code", "research", "analysis"]:
                if target_domain != problem_type:
                    await self.transfer_system.attempt_transfer(
                        problem_type, target_domain,
                        {"roles": agent_roles, "quality": initial_result["quality_score"]}
                    )

        # Track performance
        execution_time = (datetime.now() - start_time).total_seconds()
        self.performance_history.append({
            "problem": problem,
            "quality_score": initial_result["quality_score"],
            "execution_time": execution_time,
            "patterns_used": [
                "safety_check", "dynamic_roles", "quality_gates",
                "adversarial_debate" if initial_result["quality_score"] < 0.8 else None
            ]
        })

        return {
            **initial_result,
            "execution_time": execution_time,
            "agent_roles": agent_roles,
            "safety_check": safety_result,
            "current_parameters": self.param_manager.get_current_parameters()
        }

    def get_performance_metrics(self) -> dict:
        """Get performance metrics."""
        if not self.performance_history:
            return {}

        quality_scores = [p["quality_score"] for p in self.performance_history]
        execution_times = [p["execution_time"] for p in self.performance_history]

        return {
            "avg_quality": sum(quality_scores) / len(quality_scores),
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "total_executions": len(self.performance_history),
            "debate_count": len(self.debate_system.debate_history),
            "archived_patterns": sum(
                len(pt["successful_patterns"])
                for pt in self.strategy_archive.patterns["problem_types"].values()
            ),
            "transfer_attempts": len(self.transfer_system.transfer_history)
        }


# ============================================
# MCP-UI Integration
# ============================================

class MCPUIIntegration:
    """Integrates MCP-UI capabilities with the improved swarm."""

    def __init__(self, swarm: ImprovedAgentSwarm):
        self.swarm = swarm
        self.ui_resources = {}

    def create_swarm_control_panel(self) -> dict:
        """Create UI panel for swarm control."""
        return {
            "uri": "ui://swarm/control",
            "type": "remoteDom",
            "content": {
                "title": "Improved Swarm Control Panel",
                "sections": [
                    {
                        "name": "Performance Metrics",
                        "type": "dashboard",
                        "data": self.swarm.get_performance_metrics()
                    },
                    {
                        "name": "Pattern Controls",
                        "type": "toggles",
                        "patterns": [
                            {"id": "adversarial_debate", "enabled": True},
                            {"id": "quality_gates", "enabled": True},
                            {"id": "strategy_archive", "enabled": True},
                            {"id": "safety_boundaries", "enabled": True}
                        ]
                    },
                    {
                        "name": "Agent Management",
                        "type": "list",
                        "agents": [str(a) for a in self.swarm.agents]
                    }
                ],
                "actions": [
                    {"label": "Run Test", "tool": "swarm.test", "params": {}},
                    {"label": "Clear Archive", "tool": "swarm.clear_archive", "params": {}},
                    {"label": "Reset Parameters", "tool": "swarm.reset_params", "params": {}}
                ]
            }
        }

    def create_debate_viewer(self, debate_id: str) -> dict:
        """Create UI for viewing debate history."""
        debates = self.swarm.debate_system.debate_history

        return {
            "uri": f"ui://swarm/debate/{debate_id}",
            "type": "remoteDom",
            "content": {
                "title": "Adversarial Debate Viewer",
                "debate_count": len(debates),
                "recent_debates": debates[-5:] if debates else []
            }
        }


if __name__ == "__main__":
    # Example usage
    async def test_improved_swarm():
        # Create mock agents
        agents = ["planner", "generator_a", "generator_b", "critic", "judge"]

        # Initialize improved swarm
        swarm = ImprovedAgentSwarm(agents)

        # Test problem
        test_problem = {
            "type": "code",
            "description": "Create a function to validate email addresses",
            "complexity": 0.5
        }

        # Solve with improvements
        result = await swarm.solve_with_improvements(test_problem)

        logger.info("Solution Result:")
        logger.info(json.dumps(result, indent=2, default=str))

        logger.info("\nPerformance Metrics:")
        logger.info(json.dumps(swarm.get_performance_metrics(), indent=2))

        # Create UI integration
        ui = MCPUIIntegration(swarm)
        control_panel = ui.create_swarm_control_panel()

        logger.info("\nUI Control Panel:")
        logger.info(json.dumps(control_panel, indent=2, default=str))

    # Run test
    asyncio.run(test_improved_swarm())
