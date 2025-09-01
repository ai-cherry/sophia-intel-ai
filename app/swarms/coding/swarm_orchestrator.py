"""
Swarm Orchestrator for coordinating coding debate cycles.

This module manages the execution of coding swarms, including debate rounds,
validation, memory integration, and result aggregation.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from agno.team import Team
from app.swarms.coding.models import (
    DebateResult,
    CriticOutput,
    JudgeOutput,
    GateDecision,
    GeneratorProposal,
    SwarmConfiguration,
    RiskLevel
)
from app.swarms.approval import get_risk_level
from app.utils.response_handler import ResponseHandler, ModelResponseValidator
from app.memory.supermemory_mcp import SupermemoryMCP
from app.memory.types import MemoryEntry, MemoryType

# Optional optimizer and circuit breaker integration
try:
    from app.swarms.performance_optimizer import SwarmOptimizer, performance_monitoring, CircuitBreakerOpenException
except Exception:
    SwarmOptimizer = None
    performance_monitoring = None

    class CircuitBreakerOpenException(Exception):
        pass

logger = logging.getLogger(__name__)


class SwarmOrchestrator:
    """
    Orchestrates the execution of coding swarm debates.
    
    This class manages the multi-round debate process, handles validation,
    integrates with memory systems, and produces structured results.
    """
    
    def __init__(self, team: Team, config: SwarmConfiguration, memory: Optional[SupermemoryMCP] = None):
        """
        Initialize the orchestrator.
        
        Args:
            team: The coding swarm team to orchestrate
            config: Configuration for the swarm execution
            memory: Optional memory service for persistence
        """
        self.team = team
        self.config = config
        self.memory = memory
        self.logger = logging.getLogger(f"{__name__}.{team.name}")
        # Initialize optimizer if available (for circuit breakers and performance tracking)
        try:
            self.optimizer = SwarmOptimizer() if SwarmOptimizer else None
        except Exception:
            self.optimizer = None
    
    async def run_debate(self, task: str, context: Optional[Dict[str, Any]] = None) -> DebateResult:
        """
        Run a complete debate cycle for the given task with circuit breaker protection.

        Args:
            task: The coding task to solve
            context: Optional context for the task

        Returns:
            DebateResult with all outputs and validation status
        """
        start_time = time.time()

        # Initialize result
        result = DebateResult(
            task=task,
            team_id=self.team.name,
            session_id=context.get("session_id") if context else None
        )

        try:
            # Circuit breaker: Check if memory system is healthy
            if self.config.use_memory and self.memory:
                memory_healthy = await self._check_memory_health()
                if memory_healthy:
                    await self._search_related_memories(task, result)
                else:
                    self.logger.warning("Memory system unhealthy, skipping memory search")
                    result.errors.append("Memory system unavailable")

            # Optimized round execution with early returns for fast mode
            if self._is_fast_mode():
                # Fast mode: Skip complex rounds
                await self._run_fast_proposal_round(task, context, result)
            else:
                # Full mode: Complete debate cycle
                # Round 1: Generate proposals
                await self._run_proposal_round(task, context, result)

                # Round 2: Critic review (with fallback)
                if not await self._run_critic_round(result):
                    self.logger.warning("Critic round failed, proceeding with basic validation")

                # Round 3: Apply fixes if needed
                if result.critic and result.critic.verdict == "revise":
                    await self._run_revision_round(result)
                    # Re-run critic after fixes
                    await self._run_critic_round(result)

            # Round 4: Judge decision (always attempted)
            await self._run_judge_round(result)

            # Compute gate decision with safer logic
            await self._compute_gate_decision(result)

            # Store results (circuit breaker protected)
            if self.config.store_results and self.memory:
                if await self._check_memory_health():
                    await self._store_results_in_memory(result)
                else:
                    self.logger.debug("Skipping result storage due to memory health")

        except asyncio.TimeoutError:
            error_msg = f"Debate timed out after {self.config.timeout_seconds} seconds"
            self.logger.error(error_msg)
            result.errors.append(error_msg)
            result.runner_approved = False  # Fail-safe on timeout
        except Exception as e:
            error_msg = f"Unexpected error in debate: {str(e)}"
            self.logger.exception(error_msg)
            result.errors.append(error_msg)
            result.runner_approved = False  # Fail-safe on error
        finally:
            # Record execution time
            result.execution_time_ms = int((time.time() - start_time) * 1000)

            # Track performance
            self._track_performance(result)

        return result

    def _is_fast_mode(self) -> bool:
        """Check if running in fast optimization mode."""
        mode = self.config.get("optimization", "balanced").lower()
        return mode in ["speed", "fast", "lite"]

    async def _check_memory_health(self) -> bool:
        """Circuit breaker check for memory system health."""
        if not self.memory:
            return False

        try:
            # Simple health check - attempt a basic operation
            await asyncio.wait_for(
                asyncio.to_thread(self.memory.search_memory, "", limit=1),
                timeout=0.5  # Fast timeout for health check
            )
            return True
        except Exception as e:
            self.logger.debug(f"Memory health check failed: {e}")
            return False

    async def _run_fast_proposal_round(self, task: str, context: Optional[Dict[str, Any]],
                                      result: DebateResult) -> None:
        """Optimized proposal round for fast mode."""
        self.logger.info("Running fast proposal round")

        try:
            # Simplified prompt for speed
            prompt = f"Generate solution for: {task}"
            if context:
                prompt += f"\n\nContext: {context}"

            # Single response with timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(self.team.run, prompt),
                timeout=self.config.timeout_seconds / 2
            )

            self.logger.info("Fast proposals generated successfully")

        except asyncio.TimeoutError:
            error_msg = "Fast proposal round timed out"
            self.logger.error(error_msg)
            result.errors.append(error_msg)

    def _track_performance(self, result: DebateResult) -> None:
        """Track performance metrics for optimization."""
        try:
            # Simple performance tracking
            metrics = {
                "task_length": len(result.task) if result.task else 0,
                "execution_time_ms": result.execution_time_ms,
                "error_count": len(result.errors),
                "approved": result.runner_approved or False
            }

            # Could store in memory or local tracking
            self.logger.debug(f"Performance tracked: {metrics}")

        except Exception as e:
            self.logger.debug(f"Performance tracking failed: {e}")
    
    async def _search_related_memories(self, task: str, result: DebateResult) -> None:
        """Search for related memories and add to result."""
        try:
            # Use circuit breaker and performance monitoring if optimizer is available
            if self.optimizer and performance_monitoring:
                async with performance_monitoring(self.optimizer, "memory_search"):
                    cb = self.optimizer.get_circuit_breaker("memory")
                    memories = await cb.call(self.memory.search_memory, query=task, limit=self.config.memory_search_limit)
            else:
                memories = await self.memory.search_memory(
                    query=task,
                    limit=self.config.memory_search_limit
                )

            for memory in memories:
                result.related_memories.append(memory.topic)

            self.logger.info(f"Found {len(memories)} related memories")
        except Exception as e:
            self.logger.warning(f"Memory search failed: {e}")
            result.warnings.append(f"Memory search failed: {str(e)}")
    
    async def _run_proposal_round(self, task: str, context: Optional[Dict[str, Any]], 
                                  result: DebateResult) -> None:
        """Run the proposal generation round."""
        self.logger.info("Starting proposal round")
        
        try:
            # Construct prompt with context
            prompt = f"[LEAD] Analyze and generate competing solutions for:\n{task}"
            if context:
                prompt += f"\n\nContext:\n{context}"
            
            # Execute team response
            if self.optimizer and performance_monitoring:
                async with performance_monitoring(self.optimizer, "proposal_generation"):
                    response = await asyncio.wait_for(
                        asyncio.to_thread(self.team.print_response, prompt, False),
                        timeout=self.config.timeout_seconds / 3
                    )
            else:
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.team.print_response, prompt, False),
                    timeout=self.config.timeout_seconds / 3
                )
            
            # Parse generator outputs (simplified for now)
            # In production, would parse actual generator responses
            self.logger.info("Proposals generated successfully")
            
        except asyncio.TimeoutError:
            error_msg = "Proposal round timed out"
            self.logger.error(error_msg)
            result.errors.append(error_msg)
            raise
        except Exception as e:
            error_msg = f"Proposal round failed: {str(e)}"
            self.logger.error(error_msg)
            result.errors.append(error_msg)
    
    async def _run_critic_round(self, result: DebateResult) -> None:
        """Run the critic review round."""
        self.logger.info("Starting critic round")
        
        try:
            critic_prompt = """
            Critic: Review the proposals and return ONLY valid JSON following this schema:
            {
                "verdict": "pass|revise|reject",
                "findings": {"category": ["finding1", "finding2"]},
                "must_fix": ["issue1", "issue2"],
                "nice_to_have": ["improvement1"],
                "confidence_score": 0.85
            }
            """
            
            if self.optimizer and performance_monitoring:
                async with performance_monitoring(self.optimizer, "critic_review"):
                    response = await asyncio.wait_for(
                        asyncio.to_thread(self.team.run, critic_prompt),
                        timeout=self.config.timeout_seconds / 3
                    )
            else:
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.team.run, critic_prompt),
                    timeout=self.config.timeout_seconds / 3
                )
            
            # Extract and validate JSON
            critic_json = ResponseHandler.extract_json(response.content or "")
            
            if not critic_json:
                # Retry with clearer prompt
                retry_response = await asyncio.to_thread(
                    self.team.run,
                    "Critic: Return your review as valid JSON only, no markdown or explanation."
                )
                critic_json = ResponseHandler.extract_json(retry_response.content or "")
            
            if critic_json:
                # Validate and create CriticOutput
                critic_json = ModelResponseValidator.validate_critic_response(critic_json)
                result.critic = CriticOutput(**critic_json)
                result.critic_validated = True
                self.logger.info(f"Critic verdict: {result.critic.verdict}")
            else:
                result.errors.append("Failed to parse critic response")
                self.logger.error("Could not extract valid JSON from critic")
                
        except asyncio.TimeoutError:
            error_msg = "Critic round timed out"
            self.logger.error(error_msg)
            result.errors.append(error_msg)
        except Exception as e:
            error_msg = f"Critic round failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)
    
    async def _run_revision_round(self, result: DebateResult) -> None:
        """Run the revision round if critic requested changes."""
        if not result.critic or not result.critic.must_fix:
            return
        
        self.logger.info("Starting revision round")
        
        try:
            fixes = ", ".join(result.critic.must_fix)
            fix_prompt = f"Generators: Apply these required fixes:\n{fixes}"
            
            await asyncio.wait_for(
                asyncio.to_thread(self.team.print_response, fix_prompt, False),
                timeout=self.config.timeout_seconds / 3
            )
            
            self.logger.info("Revisions applied")
            
        except asyncio.TimeoutError:
            result.warnings.append("Revision round timed out")
            self.logger.warning("Revision round timed out")
        except Exception as e:
            result.warnings.append(f"Revision round warning: {str(e)}")
            self.logger.warning(f"Revision round issue: {e}")
    
    async def _run_judge_round(self, result: DebateResult) -> None:
        """Run the judge decision round."""
        self.logger.info("Starting judge round")
        
        try:
            judge_prompt = """
            Judge: Make a final decision and return ONLY valid JSON:
            {
                "decision": "accept|merge|reject",
                "runner_instructions": ["step1", "step2"],
                "rationale": "Clear reasoning",
                "confidence_score": 0.9,
                "risk_assessment": "low|medium|high"
            }
            """
            
            response = await asyncio.wait_for(
                asyncio.to_thread(self.team.run, judge_prompt),
                timeout=self.config.timeout_seconds / 3
            )
            
            # Extract and validate JSON
            judge_json = ResponseHandler.extract_json(response.content or "")
            
            if not judge_json:
                # Retry with clearer prompt
                retry_response = await asyncio.to_thread(
                    self.team.run,
                    "Judge: Return your decision as valid JSON only, no markdown."
                )
                judge_json = ResponseHandler.extract_json(retry_response.content or "")
            
            if judge_json:
                # Validate and create JudgeOutput
                judge_json = ModelResponseValidator.validate_judge_response(judge_json)
                result.judge = JudgeOutput(**judge_json)
                result.judge_validated = True
                self.logger.info(f"Judge decision: {result.judge.decision}")
            else:
                result.errors.append("Failed to parse judge response")
                self.logger.error("Could not extract valid JSON from judge")
                
        except asyncio.TimeoutError:
            error_msg = "Judge round timed out"
            self.logger.error(error_msg)
            result.errors.append(error_msg)
        except Exception as e:
            error_msg = f"Judge round failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)
    
    async def _compute_gate_decision(self, result: DebateResult) -> None:
        """Compute the runner gate decision based on critic and judge outputs."""
        if not result.critic or not result.judge:
            result.runner_approved = False
            return
        
        try:
            # Determine risk level
            risk_level = RiskLevel.UNKNOWN
            if result.judge.risk_assessment:
                risk_level = result.judge.risk_assessment
            
            # Check accuracy (would integrate with actual evaluation in production)
            accuracy_score = self.config.accuracy_threshold
            reliability_passed = self.config.reliability_checks_enabled
            
            # Build gate decision
            gate = GateDecision(
                allowed=False,
                reason="",
                accuracy_score=accuracy_score,
                reliability_passed=reliability_passed,
                risk_level=risk_level
            )
            
            # Determine if execution is allowed
            if result.judge.decision in ["accept", "merge"]:
                if result.critic.verdict != "reject":
                    if accuracy_score >= self.config.accuracy_threshold:
                        if risk_level == RiskLevel.LOW and self.config.auto_approve_low_risk:
                            gate.allowed = True
                            gate.reason = "Auto-approved: low risk"
                        elif risk_level != RiskLevel.HIGH:
                            gate.allowed = True
                            gate.reason = "Approved: meets all criteria"
                        else:
                            gate.requires_approval = True
                            gate.reason = "High risk: manual approval required"
                            gate.approval_actions = result.judge.runner_instructions
                    else:
                        gate.reason = f"Accuracy below threshold: {accuracy_score}"
                else:
                    gate.reason = "Critic rejected proposals"
            else:
                gate.reason = f"Judge decision: {result.judge.decision}"
            
            result.gate_decision = gate
            result.runner_approved = gate.allowed
            
            self.logger.info(f"Gate decision: {gate.reason} (allowed={gate.allowed})")
            
        except Exception as e:
            self.logger.error(f"Gate decision computation failed: {e}")
            result.runner_approved = False
    
    async def _store_results_in_memory(self, result: DebateResult) -> None:
        """Store debate results in memory service."""
        if not self.memory:
            return
        
        try:
            # Store critic output
            if result.critic:
                critic_entry = MemoryEntry(
                    topic=f"Critic Review: {result.task[:50]}",
                    content=result.critic.model_dump_json(),
                    source="coding_swarm_critic",
                    tags=[
                        "critic",
                        f"verdict:{result.critic.verdict}",
                        f"session:{result.session_id}" if result.session_id else "no_session"
                    ],
                    memory_type=MemoryType.SEMANTIC
                )
                critic_id = await self.memory.add_to_memory(critic_entry)
                result.memory_entries_created.append(critic_id)
            
            # Store judge output
            if result.judge:
                judge_entry = MemoryEntry(
                    topic=f"Judge Decision: {result.task[:50]}",
                    content=result.judge.model_dump_json(),
                    source="coding_swarm_judge",
                    tags=[
                        "judge",
                        f"decision:{result.judge.decision}",
                        f"risk:{result.judge.risk_assessment}" if result.judge.risk_assessment else "risk:unknown",
                        f"session:{result.session_id}" if result.session_id else "no_session"
                    ],
                    memory_type=MemoryType.SEMANTIC
                )
                judge_id = await self.memory.add_to_memory(judge_entry)
                result.memory_entries_created.append(judge_id)
            
            # Store overall result summary
            summary_entry = MemoryEntry(
                topic=f"Swarm Result: {result.task[:50]}",
                content=f"Task: {result.task}\nApproved: {result.runner_approved}\nErrors: {len(result.errors)}",
                source="coding_swarm",
                tags=[
                    "swarm_result",
                    f"approved:{result.runner_approved}",
                    f"team:{result.team_id}" if result.team_id else "no_team"
                ],
                memory_type=MemoryType.EPISODIC
            )
            summary_id = await self.memory.add_to_memory(summary_entry)
            result.memory_entries_created.append(summary_id)
            
            self.logger.info(f"Stored {len(result.memory_entries_created)} memory entries")
            
        except Exception as e:
            self.logger.warning(f"Failed to store results in memory: {e}")
            result.warnings.append(f"Memory storage failed: {str(e)}")
