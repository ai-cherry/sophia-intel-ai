"""
Persona agents module for AI team members
Provides sales coaching, client health monitoring, and other specialized personas
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
# Data classes for persona interactions
@dataclass
class DealAnalysis:
    """Data structure for deal analysis"""
    deal_id: str
    stage: str
    value: float
    probability: float
    key_stakeholders: list[str]
    competitors: list[str]
    pain_points: list[str]
    next_steps: list[str]
    risks: list[str]
    rep_name: str
    timestamp: Optional[datetime] = None
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
@dataclass
class PerformanceReview:
    """Data structure for performance review"""
    rep_id: str
    period: str
    metrics: dict[str, Any]
    deals_closed: list[str]
    deals_lost: list[str]
    activities: dict[str, int]
    timestamp: Optional[datetime] = None
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
@dataclass
class ClientHealthAssessment:
    """Data structure for client health assessment"""
    client_id: str
    client_name: str
    usage_metrics: dict[str, Any]
    engagement_score: float
    support_tickets: int
    last_contact_days: int
    contract_value: float
    renewal_date: Optional[str] = None
    stakeholders: list[str] = None
    timestamp: Optional[datetime] = None
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.stakeholders is None:
            self.stakeholders = []
class PersonaRegistry:
    """Registry for managing available personas"""
    def __init__(self):
        self._personas = {
            "marcus": {
                "name": "Marcus",
                "type": "sales_coach",
                "class": "SalesCoachAgent",
                "module": "app.agents.personas.sales_coach",
                "description": "Elite sales coach specializing in deal strategy and skill development",
            },
            "sarah": {
                "name": "Sarah",
                "type": "client_health",
                "class": "ClientHealthAgent",
                "module": "app.agents.personas.client_health",
                "description": "Client success specialist focused on health monitoring and retention",
            },
        }
    def list_personas(self) -> list[str]:
        """Get list of available persona IDs"""
        return list(self._personas.keys())
    def get_persona_info(self, persona_id: str) -> Optional[dict[str, Any]]:
        """Get information about a specific persona"""
        return self._personas.get(persona_id)
    def register_persona(self, persona_id: str, info: dict[str, Any]):
        """Register a new persona"""
        self._personas[persona_id] = info
    def is_registered(self, persona_id: str) -> bool:
        """Check if a persona is registered"""
        return persona_id in self._personas
# Create global registry instance
PERSONA_REGISTRY = PersonaRegistry()
# Export key components
__all__ = [
    "PERSONA_REGISTRY",
    "DealAnalysis",
    "PerformanceReview",
    "ClientHealthAssessment",
]
