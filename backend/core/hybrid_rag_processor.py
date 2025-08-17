"""
Hybrid RAG Processor for SOPHIA Intel
Combines LlamaIndex and LLAMA model for optimal business intelligence
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.database.unified_knowledge_repository import KnowledgeContext

class HybridRAGProcessor:
    """Hybrid RAG processor combining multiple RAG systems"""
    
    def __init__(self, llamaindex_rag, llama_integration):
        self.llamaindex_rag = llamaindex_rag
        self.llama_integration = llama_integration
        self.metrics = {
            "hybrid_queries_processed": 0,
            "llamaindex_usage": 0,
            "llama_usage": 0,
            "combined_usage": 0,
            "avg_processing_time": 0.0
        }
    
    async def process_hybrid_query(
        self,
        query: str,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> Dict[str, Any]:
        """Process query using hybrid RAG approach"""
        
        start_time = datetime.utcnow()
        
        try:
            # Determine optimal processing strategy
            strategy = self.determine_hybrid_strategy(query, knowledge_context, context)
            
            if strategy == "llamaindex_primary":
                result = await self.process_llamaindex_primary(query, knowledge_context, context)
                self.metrics["llamaindex_usage"] += 1
                
            elif strategy == "llama_primary":
                result = await self.process_llama_primary(query, knowledge_context, context)
                self.metrics["llama_usage"] += 1
                
            elif strategy == "combined":
                result = await self.process_combined(query, knowledge_context, context)
                self.metrics["combined_usage"] += 1
                
            else:
                # Fallback to LlamaIndex
                result = await self.process_llamaindex_primary(query, knowledge_context, context)
                self.metrics["llamaindex_usage"] += 1
            
            # Update metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.update_metrics(processing_time)
            
            # Add hybrid processing metadata
            result["hybrid_strategy"] = strategy
            result["processing_time"] = processing_time
            result["system_used"] = "hybrid_rag"
            
            return result
            
        except Exception as e:
            print(f"❌ Hybrid RAG processing error: {e}")
            return await self.fallback_processing(query, knowledge_context, context)
    
    def determine_hybrid_strategy(
        self,
        query: str,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> str:
        """Determine optimal hybrid processing strategy"""
        
        query_lower = query.lower()
        
        # Check for complex analysis requirements
        complex_analysis_indicators = [
            "analyze", "compare", "trend", "forecast", "predict", "strategy",
            "implications", "recommendations", "deep dive", "comprehensive"
        ]
        
        complexity_score = sum(1 for indicator in complex_analysis_indicators if indicator in query_lower)
        
        # Check available data richness
        data_richness = len(knowledge_context.get("entities", [])) + len(knowledge_context.get("relationships", []))
        
        # Check user role and context depth
        user_role = context.ui_context.get("user_role", "").lower()
        context_depth = context.context_depth
        
        # Decision logic
        if complexity_score >= 3 and data_richness >= 5:
            return "combined"  # Use both systems for maximum insight
        
        elif user_role in ["ceo", "cfo", "executive"] and context_depth == "deep":
            return "llama_primary"  # Use LLAMA for executive-level analysis
        
        elif data_richness >= 8 or context.chat_flags.get("cross_platform_correlation", False):
            return "llamaindex_primary"  # Use LlamaIndex for data-rich queries
        
        elif complexity_score >= 2:
            return "llama_primary"  # Use LLAMA for analytical queries
        
        else:
            return "llamaindex_primary"  # Default to LlamaIndex
    
    async def process_llamaindex_primary(
        self,
        query: str,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> Dict[str, Any]:
        """Process using LlamaIndex as primary system"""
        
        try:
            result = await self.llamaindex_rag.process_business_query(
                query, context, knowledge_context
            )
            
            # Enhance with LLAMA if available and beneficial
            if (self.llama_integration.available and 
                result.get("confidence_score", 0) < 0.8):
                
                llama_enhancement = await self.get_llama_enhancement(
                    query, result, context
                )
                
                if llama_enhancement:
                    result["llama_enhancement"] = llama_enhancement
                    result["confidence_score"] = min(0.95, result.get("confidence_score", 0) + 0.1)
            
            result["primary_system"] = "llamaindex"
            return result
            
        except Exception as e:
            print(f"⚠️  LlamaIndex primary processing error: {e}")
            return await self.fallback_processing(query, knowledge_context, context)
    
    async def process_llama_primary(
        self,
        query: str,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> Dict[str, Any]:
        """Process using LLAMA as primary system"""
        
        try:
            user_role = context.ui_context.get("user_role", "Business User")
            
            llama_result = await self.llama_integration.process_business_query(
                query, knowledge_context, user_role, "auto"
            )
            
            # Enhance with LlamaIndex vector search if available
            if self.llamaindex_rag.vector_store_available:
                vector_enhancement = await self.get_vector_enhancement(
                    query, knowledge_context
                )
                
                if vector_enhancement:
                    llama_result["vector_enhancement"] = vector_enhancement
                    llama_result["confidence_score"] = min(0.95, llama_result.get("confidence_score", 0) + 0.05)
            
            # Convert LLAMA result to standard format
            result = {
                "response": llama_result.get("response", ""),
                "system_used": "llama_primary",
                "confidence_score": llama_result.get("confidence_score", 0.7),
                "sources": self.extract_sources_from_context(knowledge_context),
                "knowledge_items_used": len(knowledge_context.get("entities", [])),
                "processing_method": "llama_enhanced",
                "llama_analysis_type": llama_result.get("analysis_type", "general"),
                "primary_system": "llama"
            }
            
            return result
            
        except Exception as e:
            print(f"⚠️  LLAMA primary processing error: {e}")
            return await self.fallback_processing(query, knowledge_context, context)
    
    async def process_combined(
        self,
        query: str,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> Dict[str, Any]:
        """Process using combined approach for maximum insight"""
        
        try:
            # Run both systems in parallel
            llamaindex_task = asyncio.create_task(
                self.llamaindex_rag.process_business_query(query, context, knowledge_context)
            )
            
            llama_task = asyncio.create_task(
                self.llama_integration.process_business_query(
                    query, knowledge_context, context.ui_context.get("user_role", "Business User"), "auto"
                )
            )
            
            # Wait for both results
            llamaindex_result, llama_result = await asyncio.gather(
                llamaindex_task, llama_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(llamaindex_result, Exception):
                print(f"⚠️  LlamaIndex error in combined processing: {llamaindex_result}")
                llamaindex_result = None
            
            if isinstance(llama_result, Exception):
                print(f"⚠️  LLAMA error in combined processing: {llama_result}")
                llama_result = None
            
            # Synthesize combined response
            combined_response = self.synthesize_combined_response(
                query, llamaindex_result, llama_result, knowledge_context
            )
            
            return combined_response
            
        except Exception as e:
            print(f"❌ Combined processing error: {e}")
            return await self.fallback_processing(query, knowledge_context, context)
    
    def synthesize_combined_response(
        self,
        query: str,
        llamaindex_result: Optional[Dict[str, Any]],
        llama_result: Optional[Dict[str, Any]],
        knowledge_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize response from both RAG systems"""
        
        response_parts = []
        confidence_scores = []
        sources = set()
        
        # Process LlamaIndex result
        if llamaindex_result and not llamaindex_result.get("error"):
            response_parts.append("**Data-Driven Analysis:**")
            response_parts.append(llamaindex_result.get("response", ""))
            confidence_scores.append(llamaindex_result.get("confidence_score", 0.0))
            sources.update(llamaindex_result.get("sources", []))
        
        # Process LLAMA result
        if llama_result and not llama_result.get("error"):
            response_parts.append("\n**Strategic Business Intelligence:**")
            response_parts.append(llama_result.get("response", ""))
            confidence_scores.append(llama_result.get("confidence_score", 0.0))
        
        # Fallback if both failed
        if not response_parts:
            response_parts.append(f"I'm processing your query: '{query}' but encountered issues with both analysis systems. Please try again or contact support.")
            confidence_scores.append(0.3)
        
        # Calculate combined confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.3
        combined_confidence = min(0.95, avg_confidence + 0.1)  # Bonus for combined analysis
        
        return {
            "response": "\n\n".join(response_parts),
            "system_used": "hybrid_combined",
            "confidence_score": combined_confidence,
            "sources": list(sources),
            "knowledge_items_used": len(knowledge_context.get("entities", [])),
            "processing_method": "hybrid_combined",
            "llamaindex_available": bool(llamaindex_result and not llamaindex_result.get("error")),
            "llama_available": bool(llama_result and not llama_result.get("error")),
            "primary_system": "combined"
        }
    
    async def get_llama_enhancement(
        self,
        query: str,
        llamaindex_result: Dict[str, Any],
        context: KnowledgeContext
    ) -> Optional[str]:
        """Get LLAMA enhancement for LlamaIndex result"""
        
        if not self.llama_integration.available:
            return None
        
        try:
            enhancement_query = f"Provide additional strategic insights for: {query}"
            
            enhancement_result = await self.llama_integration.process_business_query(
                enhancement_query, {}, context.ui_context.get("user_role", "Business User"), "strategic_analysis"
            )
            
            return enhancement_result.get("response", "")
            
        except Exception as e:
            print(f"⚠️  LLAMA enhancement error: {e}")
            return None
    
    async def get_vector_enhancement(
        self,
        query: str,
        knowledge_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get vector search enhancement for LLAMA result"""
        
        try:
            # This would perform additional vector searches
            # For now, return basic enhancement info
            return {
                "additional_entities": len(knowledge_context.get("entities", [])),
                "data_sources": knowledge_context.get("data_source_coverage", [])
            }
            
        except Exception as e:
            print(f"⚠️  Vector enhancement error: {e}")
            return None
    
    def extract_sources_from_context(self, knowledge_context: Dict[str, Any]) -> List[str]:
        """Extract sources from knowledge context"""
        sources = set()
        
        for entity in knowledge_context.get("entities", []):
            if entity.get("data_sources"):
                sources.update(entity["data_sources"])
        
        return list(sources)
    
    async def fallback_processing(
        self,
        query: str,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> Dict[str, Any]:
        """Fallback processing when hybrid systems fail"""
        
        entities = knowledge_context.get("entities", [])
        
        response_parts = []
        response_parts.append(f"I'm analyzing your query: '{query}' using available business data.")
        
        if entities:
            entity_names = [e["name"] for e in entities[:3]]
            response_parts.append(f"Found relevant information about: {', '.join(entity_names)}.")
        
        response_parts.append("The advanced RAG systems are currently experiencing issues. Basic analysis provided.")
        
        return {
            "response": " ".join(response_parts),
            "system_used": "hybrid_fallback",
            "confidence_score": 0.4,
            "sources": [],
            "knowledge_items_used": len(entities),
            "processing_method": "fallback",
            "error": "Hybrid RAG systems unavailable"
        }
    
    def update_metrics(self, processing_time: float):
        """Update hybrid processing metrics"""
        self.metrics["hybrid_queries_processed"] += 1
        
        # Update average processing time
        current_avg = self.metrics["avg_processing_time"]
        total_queries = self.metrics["hybrid_queries_processed"]
        self.metrics["avg_processing_time"] = (
            current_avg * (total_queries - 1) + processing_time
        ) / total_queries
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get hybrid system status"""
        return {
            "system_name": "Hybrid RAG Processor",
            "llamaindex_available": bool(self.llamaindex_rag),
            "llama_available": bool(self.llama_integration and self.llama_integration.available),
            "metrics": self.metrics,
            "timestamp": datetime.utcnow().isoformat()
        }

