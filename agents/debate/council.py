#!/usr/bin/env python3
"""
SOPHIA Planning Council - Agent Debate System
Multi-agent planning with critics and consensus building
"""
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class VoteType(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    ABSTAIN = "abstain"

@dataclass
class Proposal:
    """Represents a proposal for debate"""
    id: str
    title: str
    description: str
    proposed_by: str
    created_at: datetime
    requirements: List[str]
    risks: List[str]
    benefits: List[str]
    implementation_plan: Dict[str, Any]

@dataclass
class Vote:
    """Represents a council member's vote"""
    agent_id: str
    vote_type: VoteType
    reasoning: str
    suggested_modifications: Optional[List[str]] = None
    confidence: float = 0.8

@dataclass
class DebateSession:
    """Represents a complete debate session"""
    session_id: str
    proposal: Proposal
    participants: List[str]
    votes: List[Vote]
    final_decision: Optional[VoteType] = None
    consensus_threshold: float = 0.7
    started_at: datetime = None
    ended_at: Optional[datetime] = None

class PlanningCouncil:
    """Orchestrates multi-agent planning debates"""
    
    def __init__(self, openrouter_api_key: str):
        self.openrouter_api_key = openrouter_api_key
        self.active_sessions: Dict[str, DebateSession] = {}
        
        # Council members with their roles
        self.council_members = {
            "architect": {
                "role": "System Architect",
                "focus": "Technical feasibility and system design",
                "model": "gpt-4o"
            },
            "security_critic": {
                "role": "Security Analyst", 
                "focus": "Security implications and vulnerabilities",
                "model": "gpt-4o"
            },
            "performance_critic": {
                "role": "Performance Engineer",
                "focus": "Performance, scalability, and resource usage",
                "model": "gpt-4o"
            },
            "user_advocate": {
                "role": "User Experience Advocate",
                "focus": "User impact and usability concerns",
                "model": "gpt-4o"
            },
            "maintainer": {
                "role": "Code Maintainer",
                "focus": "Code quality, maintainability, and technical debt",
                "model": "gpt-4o"
            }
        }
    
    async def start_debate(self, proposal: Proposal) -> str:
        """Start a new debate session"""
        session_id = f"debate_{proposal.id}_{int(datetime.now().timestamp())}"
        
        session = DebateSession(
            session_id=session_id,
            proposal=proposal,
            participants=list(self.council_members.keys()),
            votes=[],
            started_at=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        logger.info(f"Started debate session {session_id} for proposal: {proposal.title}")
        
        return session_id
    
    async def conduct_debate(self, session_id: str) -> DebateSession:
        """Conduct the full debate process"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Phase 1: Individual analysis
        logger.info(f"Phase 1: Individual analysis for {session_id}")
        analysis_tasks = []
        for agent_id in session.participants:
            task = self._get_agent_analysis(agent_id, session.proposal)
            analysis_tasks.append(task)
        
        analyses = await asyncio.gather(*analysis_tasks)
        
        # Phase 2: Cross-examination
        logger.info(f"Phase 2: Cross-examination for {session_id}")
        cross_exam_results = await self._conduct_cross_examination(session.proposal, analyses)
        
        # Phase 3: Final voting
        logger.info(f"Phase 3: Final voting for {session_id}")
        voting_tasks = []
        for i, agent_id in enumerate(session.participants):
            task = self._get_final_vote(agent_id, session.proposal, analyses[i], cross_exam_results)
            voting_tasks.append(task)
        
        votes = await asyncio.gather(*voting_tasks)
        session.votes = votes
        
        # Phase 4: Consensus determination
        session.final_decision = self._determine_consensus(votes, session.consensus_threshold)
        session.ended_at = datetime.now()
        
        logger.info(f"Debate completed for {session_id}. Decision: {session.final_decision}")
        return session
    
    async def _get_agent_analysis(self, agent_id: str, proposal: Proposal) -> Dict[str, Any]:
        """Get individual agent analysis of proposal"""
        member = self.council_members[agent_id]
        
        prompt = f"""
You are a {member['role']} in a planning council reviewing a technical proposal.
Your focus area is: {member['focus']}

PROPOSAL TO REVIEW:
Title: {proposal.title}
Description: {proposal.description}
Requirements: {', '.join(proposal.requirements)}
Proposed Benefits: {', '.join(proposal.benefits)}
Identified Risks: {', '.join(proposal.risks)}

Please provide your analysis in the following format:
1. ASSESSMENT: Your overall assessment from your expertise area
2. CONCERNS: Specific concerns or issues you identify
3. RECOMMENDATIONS: Specific recommendations for improvement
4. RISK_LEVEL: Rate the risk level (LOW/MEDIUM/HIGH) from your perspective
5. IMPLEMENTATION_NOTES: Technical notes about implementation

Be thorough but concise. Focus on your area of expertise.
"""
        
        # Simulate API call to OpenRouter (replace with actual implementation)
        response = await self._call_openrouter(member['model'], prompt)
        
        return {
            "agent_id": agent_id,
            "role": member['role'],
            "analysis": response,
            "timestamp": datetime.now()
        }
    
    async def _conduct_cross_examination(self, proposal: Proposal, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Conduct cross-examination between agents"""
        # Create summary of all analyses
        analysis_summary = "\n\n".join([
            f"{a['role']} Analysis:\n{a['analysis']}" for a in analyses
        ])
        
        prompt = f"""
You are facilitating a cross-examination session for a technical proposal.

PROPOSAL: {proposal.title}
DESCRIPTION: {proposal.description}

INDIVIDUAL ANALYSES:
{analysis_summary}

Based on these analyses, identify:
1. CONFLICTING_VIEWS: Where agents disagree and why
2. COMMON_CONCERNS: Issues raised by multiple agents
3. GAPS: Important aspects not covered by any agent
4. SYNTHESIS: A balanced view incorporating all perspectives
5. CRITICAL_QUESTIONS: Key questions that need resolution

Provide a structured response that helps inform final voting.
"""
        
        response = await self._call_openrouter("gpt-4o", prompt)
        
        return {
            "cross_examination": response,
            "timestamp": datetime.now()
        }
    
    async def _get_final_vote(self, agent_id: str, proposal: Proposal, 
                            initial_analysis: Dict[str, Any], 
                            cross_exam: Dict[str, Any]) -> Vote:
        """Get final vote from agent after cross-examination"""
        member = self.council_members[agent_id]
        
        prompt = f"""
You are a {member['role']} making your final vote on a technical proposal.

PROPOSAL: {proposal.title}
YOUR INITIAL ANALYSIS: {initial_analysis['analysis']}
CROSS-EXAMINATION RESULTS: {cross_exam['cross_examination']}

Based on your initial analysis and the cross-examination, cast your final vote:

Vote options:
- APPROVE: Proposal should be implemented as-is
- REJECT: Proposal should not be implemented
- MODIFY: Proposal needs modifications before implementation
- ABSTAIN: Insufficient information to make a decision

Provide your response in this JSON format:
{{
    "vote": "APPROVE|REJECT|MODIFY|ABSTAIN",
    "reasoning": "Detailed explanation of your vote",
    "confidence": 0.8,
    "suggested_modifications": ["modification 1", "modification 2"] // only if vote is MODIFY
}}

Be decisive but thoughtful. Consider the full context.
"""
        
        response = await self._call_openrouter(member['model'], prompt)
        
        try:
            vote_data = json.loads(response)
            return Vote(
                agent_id=agent_id,
                vote_type=VoteType(vote_data['vote'].lower()),
                reasoning=vote_data['reasoning'],
                confidence=vote_data.get('confidence', 0.8),
                suggested_modifications=vote_data.get('suggested_modifications')
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse vote from {agent_id}: {e}")
            # Fallback vote
            return Vote(
                agent_id=agent_id,
                vote_type=VoteType.ABSTAIN,
                reasoning=f"Failed to parse response: {response}",
                confidence=0.0
            )
    
    def _determine_consensus(self, votes: List[Vote], threshold: float) -> VoteType:
        """Determine consensus from votes"""
        if not votes:
            return VoteType.ABSTAIN
        
        # Count votes by type
        vote_counts = {}
        total_confidence = 0
        
        for vote in votes:
            vote_type = vote.vote_type
            if vote_type not in vote_counts:
                vote_counts[vote_type] = {'count': 0, 'confidence': 0}
            
            vote_counts[vote_type]['count'] += 1
            vote_counts[vote_type]['confidence'] += vote.confidence
            total_confidence += vote.confidence
        
        # Calculate weighted consensus
        total_votes = len(votes)
        
        for vote_type, data in vote_counts.items():
            weighted_score = (data['count'] / total_votes) * (data['confidence'] / data['count'])
            
            if weighted_score >= threshold:
                return vote_type
        
        # No consensus reached - default to modify if any modifications suggested
        modify_votes = [v for v in votes if v.vote_type == VoteType.MODIFY]
        if modify_votes:
            return VoteType.MODIFY
        
        # Otherwise, no consensus
        return VoteType.ABSTAIN
    
    async def _call_openrouter(self, model: str, prompt: str) -> str:
        """Call OpenRouter API (placeholder implementation)"""
        # This would be replaced with actual OpenRouter API call
        # For now, return a mock response
        return f"Mock response for {model}: Analysis of the proposal shows various considerations..."
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of debate session"""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        
        vote_summary = {}
        for vote in session.votes:
            vote_type = vote.vote_type.value
            if vote_type not in vote_summary:
                vote_summary[vote_type] = []
            vote_summary[vote_type].append({
                "agent": vote.agent_id,
                "reasoning": vote.reasoning,
                "confidence": vote.confidence
            })
        
        return {
            "session_id": session_id,
            "proposal_title": session.proposal.title,
            "participants": session.participants,
            "final_decision": session.final_decision.value if session.final_decision else None,
            "vote_summary": vote_summary,
            "duration_minutes": (session.ended_at - session.started_at).total_seconds() / 60 if session.ended_at else None,
            "consensus_reached": session.final_decision != VoteType.ABSTAIN if session.final_decision else False
        }

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_council():
        council = PlanningCouncil("test-api-key")
        
        # Create test proposal
        proposal = Proposal(
            id="test_001",
            title="Implement Real-time Code Analysis",
            description="Add real-time code analysis to the MCP server for immediate feedback",
            proposed_by="architect",
            created_at=datetime.now(),
            requirements=["AST parsing", "Real-time processing", "Error reporting"],
            risks=["Performance impact", "Memory usage", "Complexity"],
            benefits=["Faster feedback", "Better code quality", "Developer experience"],
            implementation_plan={"phase1": "AST integration", "phase2": "Real-time engine"}
        )
        
        # Start and conduct debate
        session_id = await council.start_debate(proposal)
        session = await council.conduct_debate(session_id)
        
        # Get summary
        summary = council.get_session_summary(session_id)
        print(json.dumps(summary, indent=2, default=str))
    
    # Run test
    asyncio.run(test_council())

