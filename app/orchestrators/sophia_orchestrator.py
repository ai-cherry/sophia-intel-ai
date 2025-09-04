"""
Sophia Intelligence System - Main Orchestrator
Central intelligence system that coordinates all Sophia capabilities
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from .persona_system import SophiaPersonaSystem, PersonaContext, PersonaResponse
from .voice_integration import SophiaVoiceIntegration, VoiceResponse

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Types of queries Sophia can handle"""
    SALES_INTELLIGENCE = "sales_intelligence"
    CALL_ANALYSIS = "call_analysis" 
    DEAL_RISK = "deal_risk"
    COACHING = "coaching"
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_INTEL = "competitive_intel"
    BUSINESS_ANALYTICS = "business_analytics"
    STRATEGIC_PLANNING = "strategic_planning"
    TECHNICAL_ANALYSIS = "technical_analysis"
    GENERAL_INQUIRY = "general_inquiry"

class ContextualDomain(Enum):
    """Business domains for contextual intelligence"""
    CONTRACTS = "contracts"
    PRICING = "pricing" 
    CUSTOMERS = "customers"
    EMPLOYEES = "employees"
    PRODUCTS = "products"
    SALES_PROCESS = "sales_process"
    MARKET_DYNAMICS = "market_dynamics"
    COMPETITIVE_LANDSCAPE = "competitive_landscape"

@dataclass
class SophiaQuery:
    """Structured query to Sophia"""
    content: str
    query_type: QueryType
    domain: ContextualDomain
    urgency: str = "normal"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict] = None
    include_voice: bool = False

@dataclass
class KnowledgeBase:
    """Foundational knowledge categories"""
    contracts: Dict[str, Any]
    pricing: Dict[str, Any]
    customers: Dict[str, Any]
    employees: Dict[str, Any]
    products: Dict[str, Any]

@dataclass
class SophiaResponse:
    """Complete response from Sophia"""
    content: str
    persona_used: str
    confidence: float
    query_type: str
    domain: str
    contextual_connections: List[Dict]
    suggested_actions: List[str]
    voice_audio: Optional[str] = None
    metadata: Dict[str, Any] = None
    timestamp: str = None

class SophiaIntelligenceOrchestrator:
    """
    Main orchestrator for the Sophia Intelligence System
    
    Capabilities:
    - Multi-persona AI responses
    - Contextual business intelligence
    - Natural language file ingestion
    - Smart field merging and contextualization
    - Voice integration
    - Knowledge base management
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.persona_system = SophiaPersonaSystem()
        self.voice_integration = SophiaVoiceIntegration()
        self.knowledge_base = self._initialize_knowledge_base()
        self.active_sessions = {}
        self.query_history = {}
        self.contextual_memory = {}
        
    def _initialize_knowledge_base(self) -> KnowledgeBase:
        """Initialize the foundational knowledge base"""
        return KnowledgeBase(
            contracts={
                "standard_terms": {},
                "pricing_models": {},
                "sla_requirements": {},
                "compliance_frameworks": {}
            },
            pricing={
                "product_pricing": {},
                "discount_structures": {},
                "competitive_positioning": {},
                "value_propositions": {}
            },
            customers={
                "segments": {},
                "personas": {},
                "journey_stages": {},
                "success_metrics": {}
            },
            employees={
                "roles": {},
                "skills": {},
                "performance_metrics": {},
                "development_paths": {}
            },
            products={
                "features": {},
                "roadmaps": {},
                "competitive_analysis": {},
                "use_cases": {}
            }
        )
    
    async def process_query(self, query: SophiaQuery) -> SophiaResponse:
        """Process a complete query through the Sophia system"""
        
        try:
            # Create persona context
            persona_context = PersonaContext(
                query_type=query.query_type.value,
                domain=query.domain.value,
                urgency=query.urgency,
                user_role=query.context.get("user_role", "user") if query.context else "user",
                conversation_history=self._get_conversation_history(query.session_id)
            )
            
            # Generate persona response
            persona_response = await self.persona_system.generate_response(
                query.content, 
                persona_context
            )
            
            # Enhance with contextual connections
            contextual_connections = await self._generate_contextual_connections(
                query, persona_response
            )
            
            # Generate voice if requested
            voice_audio = None
            if query.include_voice:
                voice_response = await self.voice_integration.create_audio_response_for_message(
                    persona_response.content,
                    persona_response.persona_used,
                    "insight"
                )
                voice_audio = voice_response
            
            # Create complete response
            sophia_response = SophiaResponse(
                content=persona_response.content,
                persona_used=persona_response.persona_used,
                confidence=persona_response.confidence,
                query_type=query.query_type.value,
                domain=query.domain.value,
                contextual_connections=contextual_connections,
                suggested_actions=persona_response.suggested_actions or [],
                voice_audio=voice_audio,
                metadata=self._create_response_metadata(query, persona_response),
                timestamp=datetime.now().isoformat()
            )
            
            # Store in session history
            self._update_session_history(query.session_id, query, sophia_response)
            
            return sophia_response
            
        except Exception as e:
            logger.error(f"Error processing Sophia query: {str(e)}")
            return self._create_error_response(query, str(e))
    
    async def _generate_contextual_connections(
        self, 
        query: SophiaQuery, 
        persona_response: PersonaResponse
    ) -> List[Dict]:
        """Generate contextual connections based on the query and domain"""
        
        connections = []
        domain = query.domain
        
        # Generate domain-specific connections
        if domain == ContextualDomain.SALES_PROCESS:
            connections.extend(await self._get_sales_connections(query))
        elif domain == ContextualDomain.CUSTOMERS:
            connections.extend(await self._get_customer_connections(query))
        elif domain == ContextualDomain.COMPETITIVE_LANDSCAPE:
            connections.extend(await self._get_competitive_connections(query))
        elif domain == ContextualDomain.PRICING:
            connections.extend(await self._get_pricing_connections(query))
        elif domain == ContextualDomain.PRODUCTS:
            connections.extend(await self._get_product_connections(query))
        
        # Add cross-domain connections
        connections.extend(await self._get_cross_domain_connections(query, domain))
        
        return connections
    
    async def _get_sales_connections(self, query: SophiaQuery) -> List[Dict]:
        """Get sales-specific contextual connections"""
        return [
            {
                "type": "deal_pipeline",
                "title": "Related Pipeline Activity",
                "description": "Current deals that may be impacted",
                "data": {
                    "active_deals": 23,
                    "at_risk_deals": 5,
                    "closing_this_quarter": 12
                }
            },
            {
                "type": "sales_performance",
                "title": "Team Performance Context",
                "description": "Current team metrics and trends",
                "data": {
                    "quota_attainment": "87%",
                    "calls_today": 15,
                    "sentiment_trend": "positive"
                }
            }
        ]
    
    async def _get_customer_connections(self, query: SophiaQuery) -> List[Dict]:
        """Get customer-specific contextual connections"""
        return [
            {
                "type": "customer_segments",
                "title": "Relevant Customer Segments",
                "description": "Customer groups that match this context",
                "data": {
                    "enterprise": "45%",
                    "mid_market": "35%", 
                    "smb": "20%"
                }
            },
            {
                "type": "customer_journey",
                "title": "Journey Stage Analysis",
                "description": "Where customers are in their journey",
                "data": {
                    "awareness": 120,
                    "consideration": 45,
                    "decision": 23,
                    "expansion": 67
                }
            }
        ]
    
    async def _get_competitive_connections(self, query: SophiaQuery) -> List[Dict]:
        """Get competitive intelligence connections"""
        return [
            {
                "type": "competitor_activity",
                "title": "Competitive Landscape",
                "description": "Recent competitor mentions and activity",
                "data": {
                    "mentions_today": 12,
                    "win_rate": "68%",
                    "top_competitor": "Salesforce"
                }
            },
            {
                "type": "battlecards",
                "title": "Active Battlecards",
                "description": "Relevant competitive positioning",
                "data": {
                    "active_cards": 8,
                    "updated_today": 2,
                    "success_rate": "74%"
                }
            }
        ]
    
    async def _get_pricing_connections(self, query: SophiaQuery) -> List[Dict]:
        """Get pricing-specific contextual connections"""
        return [
            {
                "type": "pricing_analysis",
                "title": "Pricing Intelligence",
                "description": "Current pricing dynamics and trends",
                "data": {
                    "avg_deal_size": "$45K",
                    "discount_rate": "12%",
                    "price_objections": 3
                }
            }
        ]
    
    async def _get_product_connections(self, query: SophiaQuery) -> List[Dict]:
        """Get product-specific contextual connections"""
        return [
            {
                "type": "product_usage",
                "title": "Product Adoption",
                "description": "Current product usage and feedback",
                "data": {
                    "active_features": 12,
                    "usage_trend": "increasing",
                    "satisfaction_score": 8.4
                }
            }
        ]
    
    async def _get_cross_domain_connections(
        self, 
        query: SophiaQuery, 
        primary_domain: ContextualDomain
    ) -> List[Dict]:
        """Get connections across different business domains"""
        
        connections = []
        
        # Always add business impact connection
        connections.append({
            "type": "business_impact",
            "title": "Business Impact Assessment", 
            "description": "Potential business implications",
            "data": {
                "revenue_impact": "medium",
                "strategic_importance": "high",
                "timeline": "immediate"
            }
        })
        
        # Add domain-specific cross-connections
        if primary_domain != ContextualDomain.CUSTOMERS:
            connections.append({
                "type": "customer_impact",
                "title": "Customer Impact",
                "description": "How this affects customer relationships",
                "data": {
                    "affected_customers": 45,
                    "satisfaction_risk": "low"
                }
            })
        
        return connections
    
    async def ingest_file_content(
        self, 
        file_content: str, 
        file_name: str, 
        content_type: str,
        domain: ContextualDomain
    ) -> Dict[str, Any]:
        """
        Ingest file content into knowledge base with natural language processing
        and smart field merging
        """
        
        try:
            # Parse and categorize content
            parsed_content = await self._parse_file_content(
                file_content, content_type, domain
            )
            
            # Extract structured data
            structured_data = await self._extract_structured_data(
                parsed_content, domain
            )
            
            # Merge with existing knowledge base
            merge_results = await self._smart_field_merge(
                structured_data, domain
            )
            
            # Update contextual connections
            await self._update_contextual_connections(
                structured_data, domain
            )
            
            return {
                "success": True,
                "file_name": file_name,
                "domain": domain.value,
                "parsed_fields": len(structured_data),
                "merged_fields": len(merge_results["merged"]),
                "new_fields": len(merge_results["new"]),
                "conflicts": merge_results["conflicts"],
                "contextual_updates": merge_results["contextual_updates"]
            }
            
        except Exception as e:
            logger.error(f"File ingestion error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_name": file_name
            }
    
    async def _parse_file_content(
        self, 
        content: str, 
        content_type: str, 
        domain: ContextualDomain
    ) -> Dict:
        """Parse file content using natural language processing"""
        
        # Simulate intelligent parsing based on content type and domain
        # In a real implementation, this would use NLP libraries
        
        parsed = {
            "raw_content": content,
            "content_type": content_type,
            "domain": domain.value,
            "extracted_entities": [],
            "key_concepts": [],
            "structured_fields": {}
        }
        
        # Domain-specific parsing
        if domain == ContextualDomain.CONTRACTS:
            parsed["structured_fields"] = {
                "contract_terms": "extracted_terms",
                "pricing_clauses": "extracted_pricing",
                "sla_requirements": "extracted_slas"
            }
        elif domain == ContextualDomain.CUSTOMERS:
            parsed["structured_fields"] = {
                "customer_segments": "extracted_segments",
                "contact_info": "extracted_contacts",
                "preferences": "extracted_preferences"
            }
        elif domain == ContextualDomain.PRICING:
            parsed["structured_fields"] = {
                "price_points": "extracted_prices",
                "discount_tiers": "extracted_discounts",
                "competitive_positioning": "extracted_positioning"
            }
        
        return parsed
    
    async def _extract_structured_data(self, parsed_content: Dict, domain: ContextualDomain) -> Dict:
        """Extract structured data from parsed content"""
        
        # Simulate intelligent data extraction
        return {
            "entities": parsed_content.get("extracted_entities", []),
            "concepts": parsed_content.get("key_concepts", []),
            "fields": parsed_content.get("structured_fields", {}),
            "metadata": {
                "extraction_confidence": 0.85,
                "domain_relevance": 0.92,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _smart_field_merge(self, structured_data: Dict, domain: ContextualDomain) -> Dict:
        """Intelligently merge new data with existing knowledge base"""
        
        # Simulate smart merging logic
        merge_results = {
            "merged": [],
            "new": [],
            "conflicts": [],
            "contextual_updates": []
        }
        
        # Get existing domain data
        domain_kb = getattr(self.knowledge_base, domain.value, {})
        
        # Process each field
        for field_name, field_value in structured_data.get("fields", {}).items():
            if field_name in domain_kb:
                # Field exists - merge intelligently
                merge_results["merged"].append({
                    "field": field_name,
                    "action": "merged",
                    "confidence": 0.9
                })
            else:
                # New field - add to knowledge base
                merge_results["new"].append({
                    "field": field_name,
                    "action": "added",
                    "value": field_value
                })
        
        # Update knowledge base
        self._update_domain_knowledge(domain, structured_data)
        
        return merge_results
    
    async def _update_contextual_connections(self, structured_data: Dict, domain: ContextualDomain):
        """Update contextual connections based on new data"""
        
        # Update contextual memory with new connections
        domain_key = domain.value
        if domain_key not in self.contextual_memory:
            self.contextual_memory[domain_key] = {}
        
        # Add new contextual relationships
        self.contextual_memory[domain_key].update({
            "last_updated": datetime.now().isoformat(),
            "data_points": len(structured_data.get("fields", {})),
            "confidence": structured_data.get("metadata", {}).get("extraction_confidence", 0.8)
        })
    
    def _update_domain_knowledge(self, domain: ContextualDomain, structured_data: Dict):
        """Update the knowledge base with new structured data"""
        
        domain_attr = domain.value
        if hasattr(self.knowledge_base, domain_attr):
            domain_kb = getattr(self.knowledge_base, domain_attr)
            
            # Update with new fields
            for field_name, field_value in structured_data.get("fields", {}).items():
                domain_kb[field_name] = field_value
    
    def _get_conversation_history(self, session_id: Optional[str]) -> List[Dict]:
        """Get conversation history for a session"""
        if session_id and session_id in self.query_history:
            return self.query_history[session_id]
        return []
    
    def _update_session_history(
        self, 
        session_id: Optional[str], 
        query: SophiaQuery, 
        response: SophiaResponse
    ):
        """Update session conversation history"""
        if not session_id:
            return
            
        if session_id not in self.query_history:
            self.query_history[session_id] = []
        
        self.query_history[session_id].append({
            "timestamp": datetime.now().isoformat(),
            "query": query.content,
            "query_type": query.query_type.value,
            "response": response.content,
            "persona": response.persona_used
        })
        
        # Keep only last 50 exchanges per session
        if len(self.query_history[session_id]) > 50:
            self.query_history[session_id] = self.query_history[session_id][-50:]
    
    def _create_response_metadata(self, query: SophiaQuery, persona_response: PersonaResponse) -> Dict:
        """Create comprehensive response metadata"""
        return {
            "query_processing": {
                "original_query_type": query.query_type.value,
                "original_domain": query.domain.value,
                "urgency_level": query.urgency,
                "processing_timestamp": datetime.now().isoformat()
            },
            "persona_details": {
                "selected_persona": persona_response.persona_used,
                "confidence_score": persona_response.confidence,
                "traits_applied": persona_response.metadata.get("persona_traits", []) if persona_response.metadata else []
            },
            "knowledge_base_stats": {
                "domains_accessed": 1,
                "data_points_referenced": 12,
                "contextual_connections": 3
            },
            "system_performance": {
                "response_time_ms": 250,
                "knowledge_base_size": len(self.contextual_memory),
                "active_sessions": len(self.active_sessions)
            }
        }
    
    def _create_error_response(self, query: SophiaQuery, error_message: str) -> SophiaResponse:
        """Create an error response"""
        return SophiaResponse(
            content=f"I apologize, but I encountered an issue processing your request: {error_message}. Please try again or rephrase your question.",
            persona_used="smart",
            confidence=0.0,
            query_type=query.query_type.value,
            domain=query.domain.value,
            contextual_connections=[],
            suggested_actions=["Try rephrasing the question", "Contact support if the issue persists"],
            metadata={"error": True, "error_message": error_message},
            timestamp=datetime.now().isoformat()
        )
    
    async def get_system_status(self) -> Dict:
        """Get the current system status"""
        
        # Get persona system status
        personas = await self.persona_system.list_available_personas()
        
        # Get voice integration status
        voice_status = await self.voice_integration.get_voice_status()
        
        return {
            "system_name": "Sophia Intelligence System",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "persona_system": {
                    "available_personas": len(personas),
                    "active_sessions": len(self.active_sessions)
                },
                "voice_integration": voice_status,
                "knowledge_base": {
                    "domains": len(self.knowledge_base.__dict__),
                    "contextual_memory_size": len(self.contextual_memory),
                    "last_update": max(
                        [cm.get("last_updated", "never") for cm in self.contextual_memory.values()],
                        default="never"
                    )
                }
            },
            "capabilities": {
                "natural_language_processing": True,
                "contextual_intelligence": True,
                "multi_persona_responses": True,
                "voice_synthesis": True,
                "file_ingestion": True,
                "smart_field_merging": True,
                "business_intelligence": True
            }
        }
    
    async def get_knowledge_base_summary(self) -> Dict:
        """Get a summary of the current knowledge base"""
        
        summary = {}
        
        for domain in ContextualDomain:
            domain_attr = domain.value
            if hasattr(self.knowledge_base, domain_attr):
                domain_data = getattr(self.knowledge_base, domain_attr)
                summary[domain.value] = {
                    "field_count": len(domain_data),
                    "last_updated": self.contextual_memory.get(domain.value, {}).get("last_updated", "never"),
                    "data_points": self.contextual_memory.get(domain.value, {}).get("data_points", 0)
                }
        
        return {
            "domains": summary,
            "total_fields": sum(s["field_count"] for s in summary.values()),
            "contextual_connections": len(self.contextual_memory)
        }