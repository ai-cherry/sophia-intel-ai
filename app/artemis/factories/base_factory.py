"""Base types for Artemis factories.

Contains shared enums and data models used across Artemis factory modules.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from app.models.schemas import ModelFieldsModel


class TechnicalAgentRole(str, Enum):
    """Technical roles specific to Artemis operations."""

    CODE_REVIEWER = "code_reviewer"
    SECURITY_AUDITOR = "security_auditor"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"
    ARCHITECTURE_CRITIC = "architecture_critic"
    VULNERABILITY_SCANNER = "vulnerability_scanner"
    TACTICAL_ANALYST = "tactical_analyst"
    THREAT_HUNTER = "threat_hunter"
    SYSTEM_ARCHITECT = "system_architect"
    CODE_REFACTORING_SPECIALIST = "code_refactoring_specialist"


class DomainTeamType(str, Enum):
    """Domain-specialized team types for integration intelligence."""

    BUSINESS_INTELLIGENCE = "business_intelligence"
    SALES_INTELLIGENCE = "sales_intelligence"
    DEVELOPMENT_INTELLIGENCE = "development_intelligence"
    KNOWLEDGE_MANAGEMENT = "knowledge_management"
    INTEGRATION_ORCHESTRATION = "integration_orchestration"


class TechnicalPersonality(str, Enum):
    """Technical personality traits for Artemis agents."""

    TACTICAL_PRECISE = "tactical_precise"
    PASSIONATE_TECHNICAL = "passionate_technical"
    CRITICAL_ANALYTICAL = "critical_analytical"
    SECURITY_PARANOID = "security_paranoid"
    PERFORMANCE_OBSESSED = "performance_obsessed"


class ArtemisAgentTemplate(ModelFieldsModel):
    """Template for Artemis technical agents."""

    name: str
    role: TechnicalAgentRole
    personality: TechnicalPersonality
    model_configuration: dict[str, Any]
    system_prompt: str
    capabilities: list[str]
    tools: list[str] = []
    virtual_key: str = "openai-vk-190a60"
    tactical_traits: dict[str, Any] = {}

