"""
Swarm Orchestrator for coordinating coding team debates.
"""

import asyncio
import json
import logging
import time
import traceback
from typing import Any, Dict, List, Optional
from datetime import datetime

from agno.team import Team

from app.swarms.coding.models import (
    CriticOutput,
    CriticVerdict,
    DebateResult,
    GateDecision,
    GeneratorProposal,
    JudgeDecision,
    JudgeOutput,
    RiskLevel,
    SwarmConfiguration
)

logger = logging.getLogger(__name__)


class SwarmOrchestrator:
    """Orchestrates debate cycles for coding swarms."""
    
    def __init__(
        self,
        team: Team,
        config: SwarmConfiguration,
        memory: Optional[Any] = None
    ):
        """
        Initialize the orchestrator.
        
        Args:
            team: The coding swarm team
            config: Configuration for the swarm
            memory: Optional memory service
        """
        self.team = team
        self.config = config
        self.memory = memory
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def run_debate(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DebateResult:
        """
        Run a complete debate cycle.
        
        Args:
            task: The task description
            context: Optional context for the task
        
        Returns:
            DebateResult with debate outcomes
        """
        start_time = time.time()
        session_id = context.get("session_id") if context else None
        team_id = self.team.name if hasattr(self.team, 'name') else "default-team"
        
        logger.info(f"Starting debate cycle for task: {task[:100]}...")
        
        # Initialize result
        result = DebateResult(
            task=task,
            team_id=team_id,
            session_id=session_id,
            proposals=[],
            critic=None,
            judge=None,
            critic_validated=False,
            judge_validated=False,
            gate_decision=None,
            runner_approved=False,
            errors=[],
            warnings=[],
            execution_time_ms=0
        )
        
        try:
            # Phase 1: Generate proposals
            logger.info("Phase 1: Generating proposals from multiple agents...")
            proposals = await self._run_generator_phase(task, context, result)
            result.proposals = proposals
            
            if not proposals:
                error_msg = "No proposals generated"
                logger.error(error_msg)
                result.errors.append(error_msg)
                result.execution_time_ms = int((time.time() - start_time) * 1000)
                return result
            
            # Phase 2: Critic review
            logger.info("Phase 2: Running critic review on proposals...")
            critic_output = await self._run_critic_phase(proposals, task, context, result)
            result.critic = critic_output
            
            if critic_output:
                result.critic_validated = critic_output.verdict == CriticVerdict.PASS
                logger.info(f"Critic verdict: {critic_output.verdict}, validated: {result.critic_validated}")
            
            # Phase 3: Judge decision
            logger.info("Phase 3: Judge evaluating proposals and critic feedback...")
            judge_output = await self._run_judge_phase(proposals, critic_output, task, context, result)
            result.judge = judge_output
            
            if judge_output:
                result.judge_validated = judge_output.decision == JudgeDecision.ACCEPT
                logger.info(f"Judge decision: {judge_output.decision}, validated: {result.judge_validated}")
            
            # Phase 4: Runner gate decision
            logger.info("Phase 4: Evaluating runner gate decision...")
            gate_decision = await self._evaluate_runner_gate(
                proposals, critic_output, judge_output, result
            )
            result.gate_decision = gate_decision
            result.runner_approved = gate_decision.allowed if gate_decision else False
            
            logger.info(f"Runner gate decision: approved={result.runner_approved}")
            
            # Store in memory if configured
            if self.memory and self.config.store_results:
                await self._store_in_memory(result)
            
        except Exception as e:
            error_msg = f"Error during debate cycle: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            result.errors.append(error_msg)
            result.runner_approved = False
        
        finally:
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Debate completed in {result.execution_time_ms}ms with "
                       f"{len(result.proposals)} proposals, "
                       f"approved={result.runner_approved}, "
                       f"errors={len(result.errors)}")
        
        return result
    
    async def _run_generator_phase(
        self,
        task: str,
        context: Optional[Dict[str, Any]],
        result: DebateResult
    ) -> List[GeneratorProposal]:
        """
        Coordinate multiple generator agents to propose solutions.
        
        Args:
            task: The task description
            context: Optional context
            result: The debate result to update
        
        Returns:
            List of generator proposals
        """
        proposals = []
        
        # Find all generator agents in the team
        generator_agents = self._get_generator_agents()
        
        if not generator_agents:
            logger.warning("No generator agents found in team")
            result.warnings.append("No generator agents available")
            return proposals
        
        logger.info(f"Running {len(generator_agents)} generator agents in parallel...")
        
        # Create tasks for parallel execution
        generator_tasks = []
        for agent_name in generator_agents:
            generator_tasks.append(
                self._get_generator_proposal(agent_name, task, context)
            )
        
        # Execute generators in parallel with timeout
        try:
            timeout = min(self.config.timeout_seconds / 3, 100)  # 1/3 of total timeout for generators
            generator_results = await asyncio.wait_for(
                asyncio.gather(*generator_tasks, return_exceptions=True),
                timeout=timeout
            )
            
            # Process results
            for agent_name, result_or_error in zip(generator_agents, generator_results):
                if isinstance(result_or_error, Exception):
                    error_msg = f"Generator {agent_name} failed: {str(result_or_error)}"
                    logger.error(error_msg)
                    result.warnings.append(error_msg)
                elif result_or_error:
                    proposals.append(result_or_error)
                    logger.info(f"Received proposal from {agent_name}: "
                               f"approach={result_or_error.approach[:50]}...")
        
        except asyncio.TimeoutError:
            error_msg = f"Generator phase timed out after {timeout}s"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        return proposals
    
    async def _get_generator_proposal(
        self,
        agent_name: str,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> GeneratorProposal:
        """
        Get a proposal from a specific generator agent.
        
        Args:
            agent_name: Name of the generator agent
            task: The task description
            context: Optional context
        
        Returns:
            GeneratorProposal from the agent
        """
        prompt = f"""
        Task: {task}
        
        Please propose a solution approach. Return your response as JSON with:
        - approach: Your implementation strategy
        - code_changes: Specific code changes needed
        - test_code: Test code to validate the changes
        - risk_level: Assessment of risk (low/medium/high)
        - confidence: Your confidence in this approach (0.0 to 1.0)
        - tools_used: List of tools you would use
        """
        
        if context:
            prompt += f"\n\nContext: {json.dumps(context, indent=2)}"
        
        try:
            # Run the agent with retry logic
            for attempt in range(self.max_retries):
                try:
                    # Use team's run method with specific agent
                    response = await self._run_agent_with_team(
                        agent_name=agent_name,
                        messages=[{"role": "user", "content": prompt}],
                        stream=self.config.stream_responses
                    )
                    
                    # Parse response into GeneratorProposal
                    return self._parse_generator_response(agent_name, response)
                
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {agent_name}: {e}")
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                    else:
                        raise
        
        except Exception as e:
            logger.error(f"Failed to get proposal from {agent_name}: {e}")
            # Return a default proposal on error
            return GeneratorProposal(
                agent_name=agent_name,
                approach=f"Error: {str(e)}",
                code_changes="",
                test_code=None,
                risk_level=RiskLevel.UNKNOWN,
                confidence=0.0,
                tools_used=[]
            )
    
    async def _run_critic_phase(
        self,
        proposals: List[GeneratorProposal],
        task: str,
        context: Optional[Dict[str, Any]],
        result: DebateResult
    ) -> Optional[CriticOutput]:
        """
        Send all proposals to the critic agent for review.
        
        Args:
            proposals: List of generator proposals
            task: The task description
            context: Optional context
            result: The debate result to update
        
        Returns:
            CriticOutput or None if failed
        """
        critic_agent = self._find_agent_by_role("critic")
        if not critic_agent:
            logger.warning("No critic agent found")
            result.warnings.append("Critic agent not available")
            return None
        
        # Format proposals for critic review
        proposals_text = self._format_proposals_for_review(proposals)
        
        prompt = f"""
        Task: {task}
        
        Review the following proposals from the generators:
        
        {proposals_text}
        
        Provide a structured review with:
        - verdict: Your overall verdict (pass/revise/reject)
        - findings: Categorized findings by area (security, logic, performance, etc.)
        - must_fix: Critical issues that must be addressed
        - nice_to_haves: Improvements that would be beneficial
        - confidence_score: Your confidence in the review (0.0 to 1.0)
        
        Return your response as JSON.
        """
        
        try:
            response = await self._run_agent_with_team(
                agent_name=critic_agent,
                messages=[{"role": "user", "content": prompt}],
                stream=self.config.stream_responses
            )
            
            return self._parse_critic_response(response)
        
        except Exception as e:
            error_msg = f"Critic phase failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return None
    
    async def _run_judge_phase(
        self,
        proposals: List[GeneratorProposal],
        critic_output: Optional[CriticOutput],
        task: str,
        context: Optional[Dict[str, Any]],
        result: DebateResult
    ) -> Optional[JudgeOutput]:
        """
        Send proposals and critic feedback to judge for final decision.
        
        Args:
            proposals: List of generator proposals
            critic_output: Critic's review
            task: The task description
            context: Optional context
            result: The debate result to update
        
        Returns:
            JudgeOutput or None if failed
        """
        judge_agent = self._find_agent_by_role("judge")
        if not judge_agent:
            logger.warning("No judge agent found")
            result.warnings.append("Judge agent not available")
            return None
        
        # Format inputs for judge
        proposals_text = self._format_proposals_for_review(proposals)
        critic_text = self._format_critic_for_judge(critic_output) if critic_output else "No critic review available"
        
        prompt = f"""
        Task: {task}
        
        Generator Proposals:
        {proposals_text}
        
        Critic Review:
        {critic_text}
        
        Make a final decision on the best approach:
        - decision: Your decision (accept/merge/reject)
        - runner_instructions: Step-by-step instructions for the runner
        - rationale: Explanation of your decision
        - confidence_score: Your confidence (0.0 to 1.0)
        - risk_assessment: Overall risk level (low/medium/high)
        
        Return your response as JSON.
        """
        
        try:
            response = await self._run_agent_with_team(
                agent_name=judge_agent,
                messages=[{"role": "user", "content": prompt}],
                stream=self.config.stream_responses
            )
            
            return self._parse_judge_response(response)
        
        except Exception as e:
            error_msg = f"Judge phase failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return None
    
    async def _evaluate_runner_gate(
        self,
        proposals: List[GeneratorProposal],
        critic_output: Optional[CriticOutput],
        judge_output: Optional[JudgeOutput],
        result: DebateResult
    ) -> GateDecision:
        """
        Evaluate if code should be executed based on all outputs.
        
        Args:
            proposals: List of generator proposals
            critic_output: Critic's review
            judge_output: Judge's decision
            result: The debate result
        
        Returns:
            GateDecision with approval status
        """
        # Calculate composite accuracy score
        accuracy_score = 0.0
        factors = []
        
        # Factor in critic validation
        if critic_output:
            if critic_output.verdict == CriticVerdict.PASS:
                accuracy_score += 3.0
                factors.append("Critic approved")
            elif critic_output.verdict == CriticVerdict.REVISE:
                accuracy_score += 1.5
                factors.append("Critic suggests revision")
            else:
                factors.append("Critic rejected")
            
            accuracy_score += critic_output.confidence_score * 2.0
        
        # Factor in judge decision
        if judge_output:
            if judge_output.decision == JudgeDecision.ACCEPT:
                accuracy_score += 3.0
                factors.append("Judge accepted")
            elif judge_output.decision == JudgeDecision.MERGE:
                accuracy_score += 2.0
                factors.append("Judge suggests merge")
            else:
                factors.append("Judge rejected")
            
            accuracy_score += judge_output.confidence_score * 2.0
        
        # Determine risk level
        risk_level = RiskLevel.UNKNOWN
        if judge_output and judge_output.risk_assessment:
            risk_level = judge_output.risk_assessment
        elif proposals:
            # Use highest risk from proposals
            risk_levels = [p.risk_level for p in proposals if p.risk_level != RiskLevel.UNKNOWN]
            if risk_levels:
                if RiskLevel.HIGH in risk_levels:
                    risk_level = RiskLevel.HIGH
                elif RiskLevel.MEDIUM in risk_levels:
                    risk_level = RiskLevel.MEDIUM
                else:
                    risk_level = RiskLevel.LOW
        
        # Check reliability
        reliability_passed = (
            critic_output is not None and
            judge_output is not None and
            len(result.errors) == 0
        )
        
        # Determine if approved
        allowed = False
        reason = ""
        requires_approval = False
        approval_actions = []
        
        if accuracy_score >= self.config.accuracy_threshold:
            if risk_level == RiskLevel.LOW and self.config.auto_approve_low_risk:
                allowed = True
                reason = f"Auto-approved: Low risk, accuracy={accuracy_score:.1f}"
            elif risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
                requires_approval = True
                reason = f"Manual approval required: {risk_level} risk, accuracy={accuracy_score:.1f}"
                approval_actions = [
                    "Review generated code changes",
                    "Verify test coverage",
                    "Check for security implications"
                ]
            else:
                allowed = reliability_passed
                reason = f"Gate decision: reliability={reliability_passed}, accuracy={accuracy_score:.1f}"
        else:
            reason = f"Below accuracy threshold: {accuracy_score:.1f} < {self.config.accuracy_threshold}"
        
        # Add factors to reason
        if factors:
            reason += f" ({', '.join(factors)})"
        
        return GateDecision(
            allowed=allowed,
            reason=reason,
            accuracy_score=min(accuracy_score, 10.0),
            reliability_passed=reliability_passed,
            risk_level=risk_level,
            requires_approval=requires_approval,
            approval_actions=approval_actions
        )
    
    async def _run_agent_with_team(
        self,
        agent_name: str,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> str:
        """
        Run a specific agent using the team's run method.
        
        Args:
            agent_name: Name of the agent to run
            messages: Messages to send to the agent
            stream: Whether to stream responses
        
        Returns:
            Agent's response as string
        """
        try:
            # Use team's run method with agent parameter
            if hasattr(self.team, 'run'):
                response = await asyncio.to_thread(
                    self.team.run,
                    messages=messages,
                    agent=agent_name,
                    stream=stream
                )
                
                # Extract content from response
                if hasattr(response, 'content'):
                    return response.content
                elif isinstance(response, dict) and 'content' in response:
                    return response['content']
                else:
                    return str(response)
            else:
                # Fallback for teams without run method
                logger.warning(f"Team does not have run method, using mock response")
                return f"Mock response from {agent_name}"
        
        except Exception as e:
            logger.error(f"Error running agent {agent_name}: {e}")
            raise
    
    async def _store_in_memory(self, result: DebateResult):
        """Store debate result in memory service."""
        if not self.memory:
            return
        
        try:
            # Store as memory entry
            memory_id = await self.memory.store({
                "type": "debate_result",
                "task": result.task,
                "team_id": result.team_id,
                "session_id": result.session_id,
                "approved": result.runner_approved,
                "proposals_count": len(result.proposals),
                "execution_time_ms": result.execution_time_ms,
                "timestamp": result.timestamp.isoformat()
            })
            
            if memory_id:
                result.memory_entries_created.append(memory_id)
                logger.info(f"Stored debate result in memory: {memory_id}")
        
        except Exception as e:
            logger.error(f"Failed to store in memory: {e}")
            result.warnings.append(f"Memory storage failed: {str(e)}")
    
    def _get_generator_agents(self) -> List[str]:
        """Get list of generator agent names from the team."""
        generators = []
        
        # Check team members
        if hasattr(self.team, 'members'):
            for member in self.team.members:
                if hasattr(member, 'name'):
                    name = member.name.lower()
                    # Identify generators by name patterns
                    if any(pattern in name for pattern in ['coder', 'generator', 'developer']):
                        generators.append(member.name)
        
        # Ensure we have at least some generators
        if not generators:
            # Default generator names
            generators = ['Coder-A', 'Coder-B']
            logger.warning(f"No generators found in team, using defaults: {generators}")
        
        # Limit to max_generators
        if len(generators) > self.config.max_generators:
            generators = generators[:self.config.max_generators]
        
        return generators
    
    def _find_agent_by_role(self, role: str) -> Optional[str]:
        """Find an agent by role keyword."""
        role_lower = role.lower()
        
        if hasattr(self.team, 'members'):
            for member in self.team.members:
                if hasattr(member, 'name'):
                    name_lower = member.name.lower()
                    if role_lower in name_lower:
                        return member.name
        
        # Fallback to known names
        role_map = {
            'critic': 'Critic',
            'judge': 'Judge',
            'runner': 'Runner',
            'lead': 'Lead-Engineer'
        }
        
        return role_map.get(role_lower)
    
    def _format_proposals_for_review(self, proposals: List[GeneratorProposal]) -> str:
        """Format proposals for review by critic/judge."""
        formatted = []
        for i, proposal in enumerate(proposals, 1):
            formatted.append(f"""
Proposal {i} from {proposal.agent_name}:
- Approach: {proposal.approach}
- Code Changes: {proposal.code_changes[:500]}...
- Has Tests: {'Yes' if proposal.test_code else 'No'}
- Risk Level: {proposal.risk_level}
- Confidence: {proposal.confidence:.2f}
- Tools: {', '.join(proposal.tools_used) if proposal.tools_used else 'None'}
""")
        return "\n".join(formatted)
    
    def _format_critic_for_judge(self, critic: CriticOutput) -> str:
        """Format critic output for judge review."""
        findings_text = ""
        if critic.findings:
            findings_text = "\n".join([
                f"- {category}: {', '.join(items)}"
                for category, items in critic.findings.items()
            ])
        
        return f"""
Verdict: {critic.verdict}
Confidence: {critic.confidence_score:.2f}

Findings:
{findings_text}

Must Fix:
{chr(10).join(['- ' + item for item in critic.must_fix]) if critic.must_fix else 'None'}

Nice to Have:
{chr(10).join(['- ' + item for item in critic.nice_to_have]) if critic.nice_to_have else 'None'}
"""
    
    def _parse_generator_response(self, agent_name: str, response: str) -> GeneratorProposal:
        """Parse generator response into GeneratorProposal."""
        try:
            # Try to parse as JSON
            if '{' in response and '}' in response:
                json_start = response.index('{')
                json_end = response.rindex('}') + 1
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return GeneratorProposal(
                    agent_name=agent_name,
                    approach=data.get('approach', ''),
                    code_changes=data.get('code_changes', ''),
                    test_code=data.get('test_code'),
                    risk_level=RiskLevel(data.get('risk_level', 'unknown')),
                    confidence=float(data.get('confidence', 0.5)),
                    tools_used=data.get('tools_used', [])
                )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON from {agent_name}: {e}")
        
        # Fallback: extract what we can from text
        return GeneratorProposal(
            agent_name=agent_name,
            approach=response[:500],  # First 500 chars as approach
            code_changes=response,
            test_code=None,
            risk_level=RiskLevel.UNKNOWN,
            confidence=0.5,
            tools_used=[]
        )
    
    def _parse_critic_response(self, response: str) -> CriticOutput:
        """Parse critic response into CriticOutput."""
        try:
            # Try to parse as JSON
            if '{' in response and '}' in response:
                json_start = response.index('{')
                json_end = response.rindex('}') + 1
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return CriticOutput(
                    verdict=CriticVerdict(data.get('verdict', 'revise')),
                    findings=data.get('findings', {}),
                    must_fix=data.get('must_fix', []),
                    nice_to_have=data.get('nice_to_haves', data.get('nice_to_have', [])),
                    confidence_score=float(data.get('confidence_score', 0.5))
                )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse critic JSON: {e}")
        
        # Fallback: basic parsing from text
        verdict = CriticVerdict.REVISE
        if 'pass' in response.lower():
            verdict = CriticVerdict.PASS
        elif 'reject' in response.lower():
            verdict = CriticVerdict.REJECT
        
        return CriticOutput(
            verdict=verdict,
            findings={},
            must_fix=[],
            nice_to_have=[],
            confidence_score=0.5
        )
    
    def _parse_judge_response(self, response: str) -> JudgeOutput:
        """Parse judge response into JudgeOutput."""
        try:
            # Try to parse as JSON
            if '{' in response and '}' in response:
                json_start = response.index('{')
                json_end = response.rindex('}') + 1
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return JudgeOutput(
                    decision=JudgeDecision(data.get('decision', 'reject')),
                    runner_instructions=data.get('runner_instructions', []),
                    rationale=data.get('rationale', ''),
                    confidence_score=float(data.get('confidence_score', 0.5)),
                    risk_assessment=RiskLevel(data.get('risk_assessment', 'unknown'))
                        if data.get('risk_assessment') else None
                )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse judge JSON: {e}")
        
        # Fallback: basic parsing from text
        decision = JudgeDecision.REJECT
        if 'accept' in response.lower():
            decision = JudgeDecision.ACCEPT
        elif 'merge' in response.lower():
            decision = JudgeDecision.MERGE
        
        return JudgeOutput(
            decision=decision,
            runner_instructions=[],
            rationale=response[:200],
            confidence_score=0.5,
            risk_assessment=None
        )