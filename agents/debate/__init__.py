"""
SOPHIA Agent Debate System
Multi-agent planning and consensus building
"""

from .council import DebateSession, PlanningCouncil, Proposal, Vote, VoteType

__all__ = ["PlanningCouncil", "Proposal", "Vote", "VoteType", "DebateSession"]
