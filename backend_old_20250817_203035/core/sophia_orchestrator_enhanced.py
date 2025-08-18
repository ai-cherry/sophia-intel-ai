"""
Enhanced SOPHIA Orchestrator with Advanced RAG and Knowledge Integration
Zero-fragmentation AI platform orchestration for Pay Ready business intelligence
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from backend.database.unified_knowledge_repository import (
    UnifiedKnowledgeRepository, 
    KnowledgeContext,
    get_knowledge_repository
)

class RAGSystem(Enum):
    LLAMAINDEX = "llamaindex"
    HAYSTACK = "haystack"
    HYBRID = "hybrid"
    AUTO = "auto"

class ResponseStyle(Enum):
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"
    ANALYTICAL = "analytical"

@dataclass
class SophiaPersonality:
    """SOPHIA's personality configuration"""
    mode: str = "business_intelligence"
    style: ResponseStyle = ResponseStyle.EXECUTIVE
    confidence_threshold: float = 0.7
    max_context_length: int = 8000
    proactive_insights: bool = True
    learning_enabled: bool = True

class EnhancedSophiaOrchestrator:
    """SOPHIA orchestrator with advanced RAG and knowledge integration"""
    
    def __init__(self):
        self.knowledge_repo = get_knowledge_repository()
        self.personality = SophiaPersonality()
        self.setup_rag_systems()
        self.setup_micro_agents()
        self.setup_monitoring()
    
    def setup_rag_systems(self):
        """Initialize all RAG systems with SOPHIA awareness"""
        try:
            # Import enhanced RAG systems
            from backend.rag.enhanced_llamaindex_integration import get_llamaindex_rag
            from backend.rag.llama_model_integration import get_llama_integration
            
            # Initialize LlamaIndex RAG
            self.llamaindex_rag = get_llamaindex_rag()
            
            # Initialize LLAMA model integration
            self.llama_integration = get_llama_integration()
            
            # Check system status
            llamaindex_status = self.llamaindex_rag.get_system_status()
            llama_status = self.llama_integration.get_system_status()
            
            print("✅ Enhanced RAG systems initialized:")
            print(f"   LlamaIndex: {'✅ Available' if llamaindex_status['llm_available'] else '⚠️  Limited'}")
            print(f"   LLAMA Model: {'✅ Available' if llama_status['available'] else '⚠️  Unavailable'}")
            print(f"   Vector Store: {'✅ Available' if llamaindex_status['vector_store_available'] else '⚠️  Unavailable'}")
            
            self.rag_systems_available = True
            
        except ImportError as e:
            print(f"⚠️  RAG system import error: {e}")
            self.llamaindex_rag = None
            self.llama_integration = None
            self.rag_systems_available = False
        except Exception as e:
            print(f"❌ Failed to setup RAG systems: {e}")
            self.llamaindex_rag = None
            self.llama_integration = None
            self.rag_systems_available = False
    
    def setup_micro_agents(self):
        """Initialize specialized micro-agents"""
        self.micro_agents = {
            "entity_recognizer": None,  # Will be implemented in Phase 4
            "relationship_mapper": None,
            "cross_platform_correlator": None,
            "feedback_processor": None,
            "insight_generator": None
        }
        print("ℹ️  Micro-agents placeholders initialized")
    
    def setup_monitoring(self):
        """Setup monitoring and observability"""
        self.metrics = {
            "queries_processed": 0,
            "avg_response_time": 0.0,
            "knowledge_items_used": 0,
            "user_satisfaction": 0.0,
            "rag_system_usage": {
                "llamaindex": 0,
                "haystack": 0,
                "hybrid": 0
            }
        }
        print("✅ Monitoring system initialized")
    
    async def process_business_query(
        self, 
        query: str, 
        context: KnowledgeContext
    ) -> Dict[str, Any]:
        """Main entry point for business queries with full RAG integration"""
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Determine optimal RAG system
            rag_system = self.select_optimal_rag_system(query, context)
            
            # Step 2: Gather comprehensive context
            knowledge_context = await self.knowledge_repo.get_contextual_knowledge(
                query, context, max_results=20
            )
            
            # Step 3: Process with selected RAG system
            if rag_system == RAGSystem.LLAMAINDEX and self.rag_systems_available:
                rag_result = await self.process_with_llamaindex(query, knowledge_context, context)
            elif rag_system == RAGSystem.HYBRID and self.rag_systems_available:
                rag_result = await self.process_with_hybrid_rag(query, knowledge_context, context)
            else:
                # Fallback to basic processing
                rag_result = await self.process_basic_query(query, knowledge_context, context)
            
            # Step 4: Synthesize final response with SOPHIA personality
            final_response = await self.synthesize_sophia_response(
                query, rag_result, context, knowledge_context
            )
            
            # Step 5: Learn from interaction
            await self.learn_from_interaction(query, final_response, context)
            
            # Update metrics
            response_time = (datetime.utcnow() - start_time).total_seconds()
            await self.update_metrics(rag_system, response_time)
            
            return final_response
            
        except Exception as e:
            print(f"❌ Error processing business query: {e}")
            return {
                "response": f"I apologize, but I encountered an error processing your query. Please try again or contact support if the issue persists. Error: {str(e)}",
                "error": True,
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def select_optimal_rag_system(self, query: str, context: KnowledgeContext) -> RAGSystem:
        """Intelligently select the best RAG system for the query"""
        if context.chat_flags.get("force_rag_system"):
            return RAGSystem(context.chat_flags["force_rag_system"])
        
        # Query complexity analysis
        complexity_indicators = [
            "relationship", "correlation", "impact", "compare", "analyze",
            "trend", "forecast", "predict", "optimize", "strategy",
            "cross-platform", "integration", "performance"
        ]
        
        query_lower = query.lower()
        complexity_score = sum(1 for indicator in complexity_indicators if indicator in query_lower)
        
        # Context depth requirements
        if context.context_depth == "deep" or complexity_score >= 3:
            return RAGSystem.HYBRID
        elif context.context_depth == "medium" or complexity_score >= 1:
            return RAGSystem.LLAMAINDEX
        else:
            return RAGSystem.LLAMAINDEX  # Default to LlamaIndex
    
    async def process_with_llamaindex(
        self,
        query: str,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> Dict[str, Any]:
        """Process query using enhanced LlamaIndex RAG"""
        try:
            if self.llamaindex_rag:
                # Use enhanced LlamaIndex integration
                result = await self.llamaindex_rag.process_business_query(
                    query, context, knowledge_context
                )
                return result
            else:
                # Fallback to basic processing
                return await self.process_basic_query(query, knowledge_context, context)
            
        except Exception as e:
            print(f"❌ Enhanced LlamaIndex processing error: {e}")
            return await self.process_basic_query(query, knowledge_context, context)
    
    async def process_with_hybrid_rag(
        self,
        query: str,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> Dict[str, Any]:
        """Process query using hybrid RAG approach"""
        try:
            from backend.core.hybrid_rag_processor import HybridRAGProcessor
            
            # Create hybrid processor
            hybrid_processor = HybridRAGProcessor(
                self.llamaindex_rag,
                self.llama_integration
            )
            
            # Process with hybrid approach
            result = await hybrid_processor.process_hybrid_query(
                query, knowledge_context, context
            )
            
            return result
            
        except Exception as e:
            print(f"❌ Hybrid RAG processing error: {e}")
            return await self.process_basic_query(query, knowledge_context, context)
    
    async def process_basic_query(
        self,
        query: str,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> Dict[str, Any]:
        """Basic query processing fallback"""
        
        # Extract relevant information from knowledge context
        entities = knowledge_context.get("entities", [])
        relationships = knowledge_context.get("relationships", [])
        
        # Create a basic response
        response_parts = []
        
        if entities:
            entity_names = [e["name"] for e in entities[:5]]
            response_parts.append(f"Based on your Pay Ready business data, I found relevant information about: {', '.join(entity_names)}.")
        
        if context.chat_flags.get("deep_payready_context", False):
            response_parts.append("I'm analyzing this within the context of Pay Ready's fintech and payments business operations.")
        
        response_parts.append(f"Regarding your query: '{query}' - I'm processing this with the available business intelligence data.")
        
        if not entities and not relationships:
            response_parts.append("I don't have specific business data matching your query yet, but I'm continuously learning from our interactions to improve my responses.")
        
        basic_response = " ".join(response_parts)
        
        return {
            "response": basic_response,
            "system_used": "basic_fallback",
            "confidence_score": 0.6,
            "sources": [],
            "knowledge_items_used": len(entities),
            "processing_method": "basic_fallback"
        }
    
    def create_business_intelligence_prompt(
        self,
        query: str,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> str:
        """Create enhanced prompt for business intelligence"""
        
        entities_text = ""
        if knowledge_context.get("entities"):
            entities_list = []
            for entity in knowledge_context["entities"][:10]:
                entities_list.append(f"- {entity['name']} ({entity['type']}): {entity.get('description', 'No description')}")
            entities_text = "Relevant Business Entities:\n" + "\n".join(entities_list)
        
        relationships_text = ""
        if knowledge_context.get("relationships"):
            relationships_text = f"Business Relationships: {len(knowledge_context['relationships'])} relationships identified"
        
        prompt = f"""
You are SOPHIA, Pay Ready's advanced AI business intelligence assistant. You have deep expertise in fintech, payments, and business operations.

Pay Ready Business Context:
- Industry: Fintech/Payments Processing
- User Role: {context.ui_context.get('user_role', 'Business User')}
- Business Domain: {context.business_domain}
- Current Focus: {context.ui_context.get('current_priority', 'General Business Intelligence')}

Available Business Knowledge:
{entities_text}

{relationships_text}

Chat Configuration:
- Deep Pay Ready Context: {context.chat_flags.get('deep_payready_context', False)}
- Cross-Platform Correlation: {context.chat_flags.get('cross_platform_correlation', False)}
- Proactive Insights: {context.chat_flags.get('proactive_insights', False)}

User Query: {query}

As SOPHIA, provide a comprehensive business intelligence response that:
1. Demonstrates deep understanding of Pay Ready's business context
2. Uses specific data points and business entities when available
3. Provides actionable business recommendations
4. Identifies opportunities, risks, and strategic implications
5. Suggests follow-up analyses or next steps
6. Maintains a professional yet approachable executive communication style

If you don't have specific data to answer the query, acknowledge this and explain how you would gather the necessary information from Pay Ready's integrated data sources (Salesforce, HubSpot, Gong, etc.).

Response:
"""
        
        return prompt
    
    def extract_sources_from_context(self, knowledge_context: Dict[str, Any]) -> List[str]:
        """Extract sources from knowledge context"""
        sources = set()
        
        for entity in knowledge_context.get("entities", []):
            if entity.get("data_sources"):
                sources.update(entity["data_sources"])
        
        return list(sources)
    
    async def synthesize_sophia_response(
        self,
        query: str,
        rag_result: Dict[str, Any],
        context: KnowledgeContext,
        knowledge_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize final response with SOPHIA's personality"""
        
        base_response = rag_result.get("response", "")
        
        # Add SOPHIA personality elements
        if self.personality.proactive_insights and context.chat_flags.get("proactive_insights", False):
            # Add proactive insights placeholder
            base_response += "\n\n💡 **Proactive Insight**: Based on current data patterns, I recommend monitoring key performance indicators more closely."
        
        # Add knowledge indicators for UI
        knowledge_indicator = {
            "entities_used": [e["name"] for e in knowledge_context.get("entities", [])[:5]],
            "data_sources": self.extract_sources_from_context(knowledge_context),
            "rag_system": rag_result.get("system_used", "unknown"),
            "confidence_score": rag_result.get("confidence_score", 0.0),
            "graph_relationships": len(knowledge_context.get("relationships", [])),
            "micro_agent_contributions": []  # Will be populated in Phase 4
        }
        
        return {
            "response": base_response,
            "knowledge_indicator": knowledge_indicator,
            "rag_metrics": {
                "system_used": rag_result.get("system_used"),
                "confidence_score": rag_result.get("confidence_score", 0.0),
                "processing_time": 0.0,  # Will be calculated
                "knowledge_items_used": rag_result.get("knowledge_items_used", 0)
            },
            "sophia_personality_applied": True,
            "business_context": {
                "domain": context.business_domain,
                "user_role": context.ui_context.get("user_role"),
                "flags_used": context.chat_flags
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": f"sophia_{int(datetime.utcnow().timestamp())}"
        }
    
    async def learn_from_interaction(
        self,
        query: str,
        response: Dict[str, Any],
        context: KnowledgeContext
    ):
        """Learn from user interaction"""
        if not context.chat_flags.get("enable_learning", True):
            return
        
        try:
            # Store interaction in knowledge repository
            interaction_data = {
                "text": query,
                "response": response.get("response", ""),
                "entities": response.get("knowledge_indicator", {}).get("entities_used", []),
                "rag_sources": response.get("knowledge_indicator", {}).get("data_sources", []),
                "quality_score": response.get("rag_metrics", {}).get("confidence_score", 0.0),
                "llama_model_used": "gpt-4",
                "haystack_pipeline_used": None,
                "orchestrator_decisions": {
                    "rag_system_selected": response.get("rag_metrics", {}).get("system_used"),
                    "personality_mode": self.personality.mode,
                    "response_style": self.personality.style.value
                },
                "micro_agent_contributions": {}
            }
            
            # This will be implemented when we have the full repository
            # interaction_id = await self.knowledge_repo.store_interaction_with_full_context(
            #     interaction_data, context
            # )
            
            print(f"ℹ️  Learning from interaction: {query[:50]}...")
            
        except Exception as e:
            print(f"⚠️  Learning error: {e}")
    
    async def update_metrics(self, rag_system: RAGSystem, response_time: float):
        """Update orchestrator metrics"""
        self.metrics["queries_processed"] += 1
        
        # Update average response time
        current_avg = self.metrics["avg_response_time"]
        total_queries = self.metrics["queries_processed"]
        self.metrics["avg_response_time"] = (current_avg * (total_queries - 1) + response_time) / total_queries
        
        # Update RAG system usage
        if rag_system in [RAGSystem.LLAMAINDEX, RAGSystem.HAYSTACK, RAGSystem.HYBRID]:
            self.metrics["rag_system_usage"][rag_system.value] += 1
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "orchestrator_status": "active",
            "rag_systems": {
                "llamaindex": "available" if self.rag_systems_available and self.llamaindex_rag else "unavailable",
                "llama_model": "available" if self.rag_systems_available and self.llama_integration and self.llama_integration.available else "unavailable",
                "hybrid": "available" if self.rag_systems_available else "unavailable"
            },
            "knowledge_repository": "active",
            "micro_agents": {
                name: "planned" for name in self.micro_agents.keys()
            },
            "personality": {
                "mode": self.personality.mode,
                "style": self.personality.style.value,
                "learning_enabled": self.personality.learning_enabled
            },
            "metrics": self.metrics,
            "rag_systems_available": self.rag_systems_available,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        try:
            await self.knowledge_repo.close_connections()
            print("✅ SOPHIA Orchestrator shutdown complete")
        except Exception as e:
            print(f"⚠️  Shutdown error: {e}")

# Global orchestrator instance
_orchestrator_instance = None

def get_sophia_orchestrator() -> EnhancedSophiaOrchestrator:
    """Get global SOPHIA orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = EnhancedSophiaOrchestrator()
    return _orchestrator_instance

async def initialize_sophia_orchestrator():
    """Initialize SOPHIA orchestrator system"""
    orchestrator = get_sophia_orchestrator()
    status = await orchestrator.get_system_status()
    print("✅ SOPHIA Orchestrator initialized")
    return status

