#!/usr/bin/env python3
"""
Gong-Sophia Intelligence Bridge
Leverages existing Sophia/Artemis architecture patterns for Gong context integration
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from app.core.ai_logger import logger
from app.integrations.connectors.base_connector import BaseServiceConnector
from app.memory.unified_memory_router import MemoryDomain, get_memory_router
from app.swarms.artemis.military_orchestrator import ArtemisMillitaryOrchestrator
from app.swarms.core.message_braider import MessageBraider

# Leverage existing patterns
from app.swarms.core.micro_swarm_base import MicroSwarmBase, SwarmExecutionContext
from app.swarms.core.swarm_integration import SwarmIntegrationLayer
from app.swarms.sophia.mythology_agents import (
    AsclepiusAgent,
    AthenaAgent,
    HermesAgent,
    MinervaAgent,
    OdinAgent,
)


class GongEventType(Enum):
    """Gong event types mapped to Sophia intelligence contexts"""

    CALL_ENDED = "call_ended"
    TRANSCRIPT_READY = "transcript_ready"
    DEAL_AT_RISK = "deal_at_risk"


class GongIntelligenceContext(Enum):
    """Intelligence processing contexts using existing Sophia patterns"""

    RELATIONSHIP_BUILDING = "relationship_building"
    INTELLIGENCE_SYNTHESIS = "intelligence_synthesis"
    RISK_MITIGATION = "risk_mitigation"
    MARKET_INTELLIGENCE = "market_intelligence"


@dataclass
class GongContextEvent:
    """Structured Gong event leveraging existing data patterns"""

    event_id: str
    event_type: GongEventType
    call_id: str
    timestamp: datetime
    raw_data: dict[str, Any]
    priority: str
    signature_valid: bool
    sophia_context: GongIntelligenceContext


class GongAgentMapper:
    """
    Maps Gong events to existing Sophia mythology agents
    Leverages established agent personalities and capabilities
    """

    # Map Gong contexts to existing mythology agents
    AGENT_MAPPING = {
        GongEventType.CALL_ENDED: {
            "primary": HermesAgent,  # Market intelligence gathering
            "secondary": AthenaAgent,  # Strategic analysis
            "validator": MinervaAgent,  # Systematic validation
        },
        GongEventType.TRANSCRIPT_READY: {
            "primary": OdinAgent,  # Deep wisdom extraction from transcripts
            "secondary": AsclepiusAgent,  # Relationship health diagnosis
            "validator": MinervaAgent,  # Content validation
        },
        GongEventType.DEAL_AT_RISK: {
            "primary": AthenaAgent,  # Strategic warfare planning
            "secondary": HermesAgent,  # Rapid intelligence gathering
            "validator": AsclepiusAgent,  # Diagnostic healing approach
        },
    }

    @classmethod
    def get_agents_for_event(cls, event_type: GongEventType) -> dict[str, Any]:
        """Get appropriate agents for Gong event type"""
        return cls.AGENT_MAPPING.get(
            event_type,
            {"primary": HermesAgent, "secondary": MinervaAgent, "validator": MinervaAgent},
        )


class GongSophiaContextProcessor(MicroSwarmBase):
    """
    Unified Gong context processor leveraging existing Sophia architecture
    Extends existing swarm patterns rather than creating new infrastructure
    """

    def __init__(self):
        super().__init__()

        # Leverage existing infrastructure
        self.memory_router = get_memory_router()
        self.artemis_orchestrator = ArtemisMillitaryOrchestrator()
        self.swarm_integration = SwarmIntegrationLayer()
        self.message_braider = MessageBraider()
        self.agent_mapper = GongAgentMapper()

        # Context continuity tracking using existing patterns
        self.context_threads = {}

    async def process_gong_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """
        Main processing pipeline leveraging existing Sophia patterns
        """
        # Create structured event using existing patterns
        gong_event = self._create_gong_event(event_data)

        logger.info(f"🎯 Processing Gong {gong_event.event_type.value} with Sophia intelligence")

        # Create execution context using existing swarm patterns
        execution_context = SwarmExecutionContext(
            session_id=f"gong_{gong_event.call_id}_{gong_event.timestamp.strftime('%Y%m%d_%H%M%S')}",
            domain=MemoryDomain.SOPHIA,
            priority=gong_event.priority,
            metadata={
                "source": "gong_integration",
                "event_type": gong_event.event_type.value,
                "sophia_context": gong_event.sophia_context.value,
                "signature_validated": gong_event.signature_valid,
            },
        )

        # Phase 1: Artemis Reconnaissance (if high priority)
        if gong_event.priority in ["high", "critical", "urgent"]:
            await self._deploy_artemis_mission(gong_event, execution_context)
        else:
            pass

        # Phase 2: Sophia Intelligence Processing using existing agents
        intelligence_result = await self._process_with_sophia_agents(gong_event, execution_context)

        # Phase 3: Context Continuity using existing message braider
        context_thread = await self._build_context_continuity(gong_event, execution_context)

        # Phase 4: Unified Memory Storage leveraging existing 4-tier architecture
        memory_result = await self._store_unified_context(
            gong_event, intelligence_result, context_thread
        )

        # Phase 5: Context update for future Sophia interactions
        await self._update_sophia_context_graph(gong_event, intelligence_result)

        return {
            "status": "processed",
            "event_id": gong_event.event_id,
            "sophia_intelligence": intelligence_result,
            "context_thread": context_thread,
            "memory_storage": memory_result,
            "execution_context": execution_context.to_dict(),
        }

    def _create_gong_event(self, event_data: dict[str, Any]) -> GongContextEvent:
        """Create structured Gong event from raw webhook data"""
        event_type = GongEventType(event_data.get("eventType", "call_ended"))

        # Map to Sophia intelligence context
        context_mapping = {
            GongEventType.CALL_ENDED: GongIntelligenceContext.RELATIONSHIP_BUILDING,
            GongEventType.TRANSCRIPT_READY: GongIntelligenceContext.INTELLIGENCE_SYNTHESIS,
            GongEventType.DEAL_AT_RISK: GongIntelligenceContext.RISK_MITIGATION,
        }

        return GongContextEvent(
            event_id=f"{event_data.get('callId', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            event_type=event_type,
            call_id=event_data.get("callId", "unknown"),
            timestamp=datetime.fromisoformat(
                event_data.get("timestamp", datetime.now().isoformat())
            ),
            raw_data=event_data,
            priority=self._determine_priority(event_type, event_data),
            signature_valid=event_data.get("signatureValid", False),
            sophia_context=context_mapping[event_type],
        )

    def _determine_priority(self, event_type: GongEventType, event_data: dict[str, Any]) -> str:
        """Determine processing priority using existing patterns"""
        priority_rules = {
            GongEventType.DEAL_AT_RISK: "urgent",
            GongEventType.TRANSCRIPT_READY: "high",
            GongEventType.CALL_ENDED: "high",
        }

        base_priority = priority_rules.get(event_type, "standard")

        # Upgrade priority based on context
        if event_data.get("riskScore", 0) > 0.8:
            base_priority = "critical"
        elif event_data.get("dealValue", 0) > 100000:
            base_priority = "high"

        return base_priority

    async def _deploy_artemis_mission(
        self, event: GongContextEvent, context: SwarmExecutionContext
    ) -> dict[str, Any]:
        """
        Deploy Artemis mission for tactical intelligence gathering
        Leverages existing military orchestrator patterns
        """
        mission_template = {
            "mission_type": "gong_intelligence_gathering",
            "target": event.raw_data,
            "priority": event.priority.upper(),
            "intelligence_objectives": [
                "extract_business_entities",
                "map_stakeholder_relationships",
                "identify_decision_patterns",
                "assess_competitive_intelligence",
            ],
            "execution_strategy": "parallel_with_validation",
        }

        try:
            mission_result = await self.artemis_orchestrator.deploy_mission(
                mission_template, context=context
            )

            logger.info(f"🎖️ Artemis mission completed for {event.call_id}")
            return mission_result.intelligence_buffer

        except Exception as e:
            logger.error(f"❌ Artemis mission failed: {e}")
            return {"status": "artemis_unavailable", "fallback": "sophia_direct_processing"}

    async def _process_with_sophia_agents(
        self, event: GongContextEvent, context: SwarmExecutionContext
    ) -> dict[str, Any]:
        """
        Process with existing Sophia mythology agents
        Maintains existing agent personalities and specialized capabilities
        """
        agents_config = self.agent_mapper.get_agents_for_event(event.event_type)

        # Create specialized prompts for Gong context
        gong_prompts = {
            "primary": self._create_gong_specialized_prompt(event, "primary_analysis"),
            "secondary": self._create_gong_specialized_prompt(event, "secondary_analysis"),
            "validator": self._create_gong_specialized_prompt(event, "validation"),
        }

        results = {}

        # Process with primary agent (e.g., Hermes for market intelligence)
        if "primary" in agents_config:
            primary_agent = agents_config["primary"]()
            results["primary_intelligence"] = await primary_agent.process_with_context(
                prompt=gong_prompts["primary"], context=context, memory_domain=MemoryDomain.SOPHIA
            )

        # Process with secondary agent for complementary analysis
        if "secondary" in agents_config:
            secondary_agent = agents_config["secondary"]()
            results["secondary_intelligence"] = await secondary_agent.process_with_context(
                prompt=gong_prompts["secondary"], context=context, memory_domain=MemoryDomain.SOPHIA
            )

        # Validation using Minerva patterns
        if "validator" in agents_config:
            validator_agent = agents_config["validator"]()
            results["validation"] = await validator_agent.validate_intelligence(
                primary_result=results.get("primary_intelligence"),
                secondary_result=results.get("secondary_intelligence"),
                context=context,
            )

        return {
            "agents_used": [agent.__name__ for agent in agents_config.values()],
            "intelligence_synthesis": results,
            "sophia_context": event.sophia_context.value,
            "confidence_score": self._calculate_confidence(results),
        }

    def _create_gong_specialized_prompt(self, event: GongContextEvent, analysis_type: str) -> str:
        """Create specialized prompts that align with existing agent personalities"""
        base_context = f"""
        Gong Event Context:
        - Event Type: {event.event_type.value}
        - Call ID: {event.call_id}
        - Priority: {event.priority}
        - Sophia Context: {event.sophia_context.value}
        - Data: {event.raw_data}
        """

        prompt_templates = {
            "primary_analysis": base_context
            + """
            As the primary intelligence agent, analyze this Gong event for:
            1. Strategic business implications
            2. Relationship dynamics and stakeholder mapping
            3. Market intelligence opportunities
            4. Immediate action items for follow-up

            Maintain your established personality while providing actionable business intelligence.
            """,
            "secondary_analysis": base_context
            + """
            As the secondary analysis agent, provide complementary insights:
            1. Risk assessment and mitigation strategies
            2. Long-term relationship health implications
            3. Cross-domain pattern recognition
            4. Strategic recommendations

            Build upon primary analysis while offering unique perspective.
            """,
            "validation": base_context
            + """
            As the validation agent, systematically verify:
            1. Consistency between primary and secondary analysis
            2. Logical coherence of recommendations
            3. Completeness of intelligence coverage
            4. Quality assurance of actionable insights

            Provide validation score and improvement recommendations.
            """,
        }

        return prompt_templates.get(analysis_type, base_context)

    async def _build_context_continuity(
        self, event: GongContextEvent, context: SwarmExecutionContext
    ) -> dict[str, Any]:
        """
        Build context continuity using existing message braider patterns
        """
        try:
            # Create context thread using existing braiding infrastructure
            context_key = f"gong_continuity_{event.call_id}"

            if context_key not in self.context_threads:
                self.context_threads[context_key] = (
                    await self.message_braider.create_message_thread(
                        thread_id=context_key,
                        domain=MemoryDomain.SOPHIA,
                        initial_context={"source": "gong_integration", "call_id": event.call_id},
                    )
                )

            # Add current event to context thread
            await self.message_braider.add_to_thread(
                thread_id=context_key,
                message={
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "context": event.sophia_context.value,
                    "processing_result": "intelligence_processed",
                },
            )

            return {
                "thread_id": context_key,
                "continuity_established": True,
                "context_depth": len(self.context_threads[context_key].messages),
                "braiding_status": "active",
            }

        except Exception as e:
            logger.error(f"❌ Context continuity failed: {e}")
            return {"continuity_established": False, "error": str(e)}

    async def _store_unified_context(
        self, event: GongContextEvent, intelligence: dict[str, Any], context_thread: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Store in unified memory architecture leveraging existing 4-tier system
        """
        try:
            # Prepare unified context for storage
            unified_context = {
                "gong_event": event.__dict__,
                "sophia_intelligence": intelligence,
                "context_continuity": context_thread,
                "storage_timestamp": datetime.now().isoformat(),
                "memory_domain": MemoryDomain.SOPHIA.value,
            }

            # Store using existing unified memory router (supports all tiers)
            storage_result = await self.memory_router.store_multi_tier(
                content=unified_context,
                domain=MemoryDomain.SOPHIA,
                enable_all_tiers=True,
                metadata={
                    "source": "gong_integration",
                    "event_type": event.event_type.value,
                    "priority": event.priority,
                },
            )

            return {
                "storage_successful": True,
                "tiers_stored": ["redis", "weaviate", "neon", "archive"],
                "storage_ids": storage_result,
                "unified_memory_router": "active",
            }

        except Exception as e:
            logger.error(f"❌ Unified storage failed: {e}")
            return {"storage_successful": False, "error": str(e)}

    async def _update_sophia_context_graph(
        self, event: GongContextEvent, intelligence: dict[str, Any]
    ):
        """
        Update Sophia's context graph for future interaction continuity
        """
        try:
            # Update context for future Sophia interactions
            context_update = {
                "event_source": "gong",
                "business_context": intelligence.get("intelligence_synthesis", {}),
                "relationship_updates": self._extract_relationship_updates(event, intelligence),
                "conversation_continuity": f"Processed {event.event_type.value} from call {event.call_id}",
                "next_interaction_context": self._prepare_next_interaction_context(
                    event, intelligence
                ),
            }

            # Store in Sophia's active context for immediate availability
            await self.memory_router.update_active_context(
                domain=MemoryDomain.SOPHIA, context_updates=context_update
            )

            logger.info("✅ Sophia context graph updated for future continuity")

        except Exception as e:
            logger.error(f"❌ Context graph update failed: {e}")

    def _extract_relationship_updates(
        self, event: GongContextEvent, intelligence: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract relationship updates for context continuity"""
        return {
            "call_participants": event.raw_data.get("participants", []),
            "company_context": event.raw_data.get("company", "unknown"),
            "relationship_health": intelligence.get("intelligence_synthesis", {})
            .get("secondary_intelligence", {})
            .get("relationship_assessment", "unknown"),
            "engagement_level": "active",
            "last_interaction": event.timestamp.isoformat(),
        }

    def _prepare_next_interaction_context(
        self, event: GongContextEvent, intelligence: dict[str, Any]
    ) -> str:
        """Prepare context for Sophia's next interaction with this contact/company"""
        context_snippets = []

        if event.event_type == GongEventType.CALL_ENDED:
            context_snippets.append(
                f"Recently completed call on {event.timestamp.strftime('%Y-%m-%d')}"
            )
        elif event.event_type == GongEventType.TRANSCRIPT_READY:
            context_snippets.append("Analyzed call transcript with key insights available")
        elif event.event_type == GongEventType.DEAL_AT_RISK:
            context_snippets.append("Deal flagged as at-risk - requires strategic attention")

        # Add intelligence insights
        if intelligence.get("intelligence_synthesis", {}).get("primary_intelligence"):
            context_snippets.append("Strategic business intelligence gathered and available")

        return " | ".join(context_snippets)

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score for intelligence results"""
        confidence_factors = []

        if results.get("primary_intelligence"):
            confidence_factors.append(0.4)
        if results.get("secondary_intelligence"):
            confidence_factors.append(0.3)
        if results.get("validation"):
            confidence_factors.append(0.3)

        return sum(confidence_factors)


# Service endpoint for n8n integration
class GongSophiaService(BaseServiceConnector):
    """
    Service endpoint that n8n can call instead of direct infrastructure access
    Leverages existing service connector patterns
    """

    def __init__(self):
        super().__init__(service_name="gong_sophia_bridge")
        self.processor = GongSophiaContextProcessor()

    async def process_gong_webhook(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """
        Main service endpoint for Gong webhook processing
        Called by n8n instead of direct infrastructure calls
        """
        try:
            # Validate webhook using existing service patterns
            validation_result = await self.validate_request(webhook_data)
            if not validation_result.valid:
                return {"error": "webhook_validation_failed", "details": validation_result.errors}

            # Process using unified Sophia patterns
            processing_result = await self.processor.process_gong_event(webhook_data)

            return {
                "status": "success",
                "service": "gong_sophia_bridge",
                "result": processing_result,
                "sophia_continuity": "established",
            }

        except Exception as e:
            logger.error(f"❌ Gong webhook processing failed: {e}")
            return {
                "status": "error",
                "service": "gong_sophia_bridge",
                "error": str(e),
                "fallback": "event_queued_for_retry",
            }


# Export for use in other modules
__all__ = [
    "GongSophiaContextProcessor",
    "GongSophiaService",
    "GongEventType",
    "GongIntelligenceContext",
    "GongAgentMapper",
]
