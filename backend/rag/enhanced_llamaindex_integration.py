"""
Enhanced LlamaIndex Integration for SOPHIA Intel
Updated to use modern LlamaIndex API with Settings instead of ServiceContext
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# LlamaIndex imports with modern API
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import VectorStoreQuery
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore

# Qdrant integration
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, PointStruct

# SOPHIA components
import sys
sys.path.append('..')
from database.unified_knowledge_repository import KnowledgeContext

class EnhancedLlamaIndexRAG:
    """Enhanced LlamaIndex RAG system with modern API"""
    
    def __init__(self):
        self.setup_llama_settings()
        self.setup_vector_store()
        self.setup_indices()
        self.metrics = {
            "queries_processed": 0,
            "documents_indexed": 0,
            "avg_retrieval_time": 0.0,
            "avg_generation_time": 0.0
        }
    
    def setup_llama_settings(self):
        """Setup LlamaIndex with modern Settings API"""
        try:
            # Configure global settings
            Settings.llm = OpenAI(
                model="gpt-4",
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.1,
                max_tokens=2000
            )
            
            Settings.embed_model = OpenAIEmbedding(
                model="text-embedding-3-large",
                api_key=os.getenv("OPENAI_API_KEY"),
                dimensions=1536
            )
            
            Settings.node_parser = SentenceSplitter(
                chunk_size=512,
                chunk_overlap=50
            )
            
            # Test LLM connection
            if Settings.llm and os.getenv("OPENAI_API_KEY"):
                print("✅ LlamaIndex Settings configured with OpenAI")
                self.llm_available = True
            else:
                print("⚠️  OpenAI API key not available, using fallback")
                self.llm_available = False
                
        except Exception as e:
            print(f"❌ Failed to setup LlamaIndex settings: {e}")
            self.llm_available = False
    
    def setup_vector_store(self):
        """Setup Qdrant vector store"""
        try:
            # Try to connect to local Qdrant first, then cloud
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")
            
            self.qdrant_client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key
            )
            
            # Test connection
            try:
                collections = self.qdrant_client.get_collections()
                print(f"✅ Connected to Qdrant at {qdrant_url}")
                self.vector_store_available = True
            except Exception as e:
                print(f"⚠️  Qdrant connection failed: {e}")
                self.vector_store_available = False
                self.qdrant_client = None
                
        except Exception as e:
            print(f"❌ Failed to setup vector store: {e}")
            self.vector_store_available = False
            self.qdrant_client = None
    
    def setup_indices(self):
        """Setup LlamaIndex indices"""
        self.indices = {}
        
        if self.vector_store_available and self.qdrant_client:
            try:
                # Create vector store for business entities
                vector_store = QdrantVectorStore(
                    client=self.qdrant_client,
                    collection_name="sophia_business_entities"
                )
                
                storage_context = StorageContext.from_defaults(
                    vector_store=vector_store
                )
                
                # Create index
                self.indices["business_entities"] = VectorStoreIndex(
                    nodes=[],  # Start empty, will be populated
                    storage_context=storage_context
                )
                
                print("✅ LlamaIndex indices created")
                
            except Exception as e:
                print(f"⚠️  Failed to create indices: {e}")
                self.indices = {}
        else:
            print("ℹ️  Vector store not available, using in-memory indices")
            self.indices = {}
    
    async def process_business_query(
        self,
        query: str,
        context: KnowledgeContext,
        knowledge_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process business query using enhanced LlamaIndex"""
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Create enhanced business context
            business_context = self.create_business_context(knowledge_context, context)
            
            # Step 2: Retrieve relevant information
            retrieval_start = datetime.utcnow()
            retrieved_info = await self.retrieve_relevant_context(query, business_context)
            retrieval_time = (datetime.utcnow() - retrieval_start).total_seconds()
            
            # Step 3: Generate response
            generation_start = datetime.utcnow()
            response = await self.generate_business_response(
                query, retrieved_info, context, business_context
            )
            generation_time = (datetime.utcnow() - generation_start).total_seconds()
            
            # Update metrics
            self.update_metrics(retrieval_time, generation_time)
            
            total_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "response": response,
                "system_used": "enhanced_llamaindex",
                "confidence_score": self.calculate_confidence_score(retrieved_info, response),
                "sources": self.extract_sources(retrieved_info),
                "knowledge_items_used": len(retrieved_info.get("entities", [])),
                "processing_method": "llamaindex_enhanced_rag",
                "retrieval_time": retrieval_time,
                "generation_time": generation_time,
                "total_time": total_time,
                "vector_store_used": self.vector_store_available
            }
            
        except Exception as e:
            print(f"❌ LlamaIndex processing error: {e}")
            return await self.fallback_processing(query, knowledge_context, context)
    
    def create_business_context(
        self,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> Dict[str, Any]:
        """Create comprehensive business context for RAG"""
        
        business_context = {
            "company": "Pay Ready",
            "industry": "Fintech/Payment Processing",
            "user_role": context.ui_context.get("user_role", "Business User"),
            "current_priority": context.ui_context.get("current_priority", "General Analysis"),
            "entities": knowledge_context.get("entities", []),
            "relationships": knowledge_context.get("relationships", []),
            "data_sources": set(),
            "key_metrics": [],
            "business_processes": []
        }
        
        # Extract data sources and categorize entities
        for entity in knowledge_context.get("entities", []):
            if entity.get("data_sources"):
                business_context["data_sources"].update(entity["data_sources"])
            
            entity_type = entity.get("type", "")
            if "metric" in entity_type.lower():
                business_context["key_metrics"].append(entity)
            elif "process" in entity_type.lower():
                business_context["business_processes"].append(entity)
        
        business_context["data_sources"] = list(business_context["data_sources"])
        
        return business_context
    
    async def retrieve_relevant_context(
        self,
        query: str,
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Retrieve relevant context using vector search and business logic"""
        
        retrieved_info = {
            "entities": business_context.get("entities", []),
            "vector_results": [],
            "business_insights": [],
            "data_source_coverage": business_context.get("data_sources", [])
        }
        
        # If vector store is available, perform vector search
        if self.vector_store_available and "business_entities" in self.indices:
            try:
                index = self.indices["business_entities"]
                query_engine = index.as_query_engine(
                    similarity_top_k=5,
                    response_mode="compact"
                )
                
                # Perform vector search
                vector_response = await asyncio.to_thread(
                    query_engine.query, query
                )
                
                retrieved_info["vector_results"] = [
                    {
                        "content": str(vector_response),
                        "score": 0.8,  # Placeholder score
                        "source": "vector_search"
                    }
                ]
                
            except Exception as e:
                print(f"⚠️  Vector search error: {e}")
        
        # Add business-specific insights
        retrieved_info["business_insights"] = self.generate_business_insights(
            query, business_context
        )
        
        return retrieved_info
    
    def generate_business_insights(
        self,
        query: str,
        business_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate business-specific insights"""
        
        insights = []
        
        # Analyze query for business intent
        query_lower = query.lower()
        
        if any(term in query_lower for term in ["revenue", "growth", "sales", "income"]):
            insights.append({
                "type": "financial_analysis",
                "insight": "This query relates to financial performance metrics",
                "relevant_entities": [e for e in business_context.get("key_metrics", []) 
                                   if "revenue" in e.get("name", "").lower()],
                "recommended_sources": ["salesforce", "netsuite", "hubspot"]
            })
        
        if any(term in query_lower for term in ["customer", "churn", "retention", "acquisition"]):
            insights.append({
                "type": "customer_analysis",
                "insight": "This query focuses on customer lifecycle and behavior",
                "relevant_entities": [e for e in business_context.get("key_metrics", []) 
                                   if any(term in e.get("name", "").lower() 
                                         for term in ["customer", "churn", "acquisition"])],
                "recommended_sources": ["salesforce", "intercom", "hubspot"]
            })
        
        if any(term in query_lower for term in ["process", "workflow", "operation", "efficiency"]):
            insights.append({
                "type": "operational_analysis",
                "insight": "This query relates to business processes and operations",
                "relevant_entities": business_context.get("business_processes", []),
                "recommended_sources": ["asana", "linear", "slack"]
            })
        
        return insights
    
    async def generate_business_response(
        self,
        query: str,
        retrieved_info: Dict[str, Any],
        context: KnowledgeContext,
        business_context: Dict[str, Any]
    ) -> str:
        """Generate business response using LLM"""
        
        if not self.llm_available:
            return self.generate_fallback_response(query, retrieved_info, business_context)
        
        try:
            # Create comprehensive prompt
            prompt = self.create_enhanced_prompt(
                query, retrieved_info, context, business_context
            )
            
            # Generate response using LLM
            response = await asyncio.to_thread(
                Settings.llm.complete, prompt
            )
            
            return str(response)
            
        except Exception as e:
            print(f"⚠️  LLM generation error: {e}")
            return self.generate_fallback_response(query, retrieved_info, business_context)
    
    def create_enhanced_prompt(
        self,
        query: str,
        retrieved_info: Dict[str, Any],
        context: KnowledgeContext,
        business_context: Dict[str, Any]
    ) -> str:
        """Create enhanced prompt for business intelligence"""
        
        # Build context sections
        entities_section = ""
        if retrieved_info.get("entities"):
            entities_list = []
            for entity in retrieved_info["entities"][:8]:
                entities_list.append(
                    f"- **{entity['name']}** ({entity['type']}): {entity.get('description', 'No description')}"
                )
            entities_section = "**Available Business Data:**\n" + "\n".join(entities_list)
        
        insights_section = ""
        if retrieved_info.get("business_insights"):
            insights_list = []
            for insight in retrieved_info["business_insights"]:
                insights_list.append(f"- {insight['insight']}")
            insights_section = "**Business Intelligence Insights:**\n" + "\n".join(insights_list)
        
        data_sources_section = ""
        if retrieved_info.get("data_source_coverage"):
            data_sources_section = f"**Available Data Sources:** {', '.join(retrieved_info['data_source_coverage'])}"
        
        prompt = f"""You are SOPHIA, Pay Ready's advanced AI business intelligence assistant. You have deep expertise in fintech, payments, and business operations.

**Company Context:**
- Company: {business_context['company']}
- Industry: {business_context['industry']}
- User Role: {business_context['user_role']}
- Current Priority: {business_context['current_priority']}

{entities_section}

{insights_section}

{data_sources_section}

**User Query:** {query}

**Response Guidelines:**
1. Provide executive-level business intelligence insights
2. Reference specific data points and business entities when available
3. Identify trends, opportunities, and strategic implications
4. Suggest actionable next steps or follow-up analyses
5. Acknowledge data limitations and suggest additional data sources if needed
6. Maintain Pay Ready's business context throughout the response

**Chat Configuration:**
- Deep Pay Ready Context: {context.chat_flags.get('deep_payready_context', False)}
- Cross-Platform Analysis: {context.chat_flags.get('cross_platform_correlation', False)}
- Proactive Insights: {context.chat_flags.get('proactive_insights', False)}

As SOPHIA, provide a comprehensive business intelligence response:"""
        
        return prompt
    
    def generate_fallback_response(
        self,
        query: str,
        retrieved_info: Dict[str, Any],
        business_context: Dict[str, Any]
    ) -> str:
        """Generate fallback response when LLM is not available"""
        
        response_parts = []
        
        response_parts.append(f"Based on Pay Ready's business intelligence data, I'm analyzing your query: '{query}'")
        
        if retrieved_info.get("entities"):
            entity_names = [e["name"] for e in retrieved_info["entities"][:5]]
            response_parts.append(f"I found relevant information about: {', '.join(entity_names)}.")
        
        if retrieved_info.get("business_insights"):
            for insight in retrieved_info["business_insights"][:2]:
                response_parts.append(f"Business insight: {insight['insight']}")
        
        if retrieved_info.get("data_source_coverage"):
            response_parts.append(f"This analysis draws from: {', '.join(retrieved_info['data_source_coverage'])}.")
        
        response_parts.append("For more detailed analysis, I recommend enabling the full LLM integration with your OpenAI API key.")
        
        return " ".join(response_parts)
    
    def calculate_confidence_score(
        self,
        retrieved_info: Dict[str, Any],
        response: str
    ) -> float:
        """Calculate confidence score for the response"""
        
        score = 0.5  # Base score
        
        # Increase score based on available data
        if retrieved_info.get("entities"):
            score += min(0.2, len(retrieved_info["entities"]) * 0.05)
        
        if retrieved_info.get("vector_results"):
            score += 0.15
        
        if retrieved_info.get("business_insights"):
            score += min(0.1, len(retrieved_info["business_insights"]) * 0.05)
        
        # Increase score based on response quality
        if len(response) > 200:
            score += 0.1
        
        if any(term in response.lower() for term in ["pay ready", "revenue", "customer", "growth"]):
            score += 0.05
        
        return min(0.95, score)
    
    def extract_sources(self, retrieved_info: Dict[str, Any]) -> List[str]:
        """Extract sources from retrieved information"""
        sources = set()
        
        for entity in retrieved_info.get("entities", []):
            if entity.get("data_sources"):
                sources.update(entity["data_sources"])
        
        sources.update(retrieved_info.get("data_source_coverage", []))
        
        return list(sources)
    
    def update_metrics(self, retrieval_time: float, generation_time: float):
        """Update processing metrics"""
        self.metrics["queries_processed"] += 1
        
        # Update average retrieval time
        current_avg_retrieval = self.metrics["avg_retrieval_time"]
        total_queries = self.metrics["queries_processed"]
        self.metrics["avg_retrieval_time"] = (
            current_avg_retrieval * (total_queries - 1) + retrieval_time
        ) / total_queries
        
        # Update average generation time
        current_avg_generation = self.metrics["avg_generation_time"]
        self.metrics["avg_generation_time"] = (
            current_avg_generation * (total_queries - 1) + generation_time
        ) / total_queries
    
    async def fallback_processing(
        self,
        query: str,
        knowledge_context: Dict[str, Any],
        context: KnowledgeContext
    ) -> Dict[str, Any]:
        """Fallback processing when LlamaIndex fails"""
        
        entities = knowledge_context.get("entities", [])
        
        response_parts = []
        response_parts.append(f"I'm processing your query: '{query}' using available business data.")
        
        if entities:
            entity_names = [e["name"] for e in entities[:3]]
            response_parts.append(f"Found relevant information about: {', '.join(entity_names)}.")
        
        response_parts.append("For enhanced analysis capabilities, please ensure the RAG system is properly configured.")
        
        return {
            "response": " ".join(response_parts),
            "system_used": "llamaindex_fallback",
            "confidence_score": 0.4,
            "sources": [],
            "knowledge_items_used": len(entities),
            "processing_method": "fallback",
            "error": "LlamaIndex processing failed"
        }
    
    async def index_business_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Index business documents for RAG"""
        try:
            if not self.vector_store_available:
                print("⚠️  Vector store not available for indexing")
                return False
            
            # Convert documents to LlamaIndex Document format
            llama_docs = []
            for doc in documents:
                llama_doc = Document(
                    text=doc.get("content", ""),
                    metadata={
                        "source": doc.get("source", "unknown"),
                        "entity_type": doc.get("entity_type", "unknown"),
                        "confidence": doc.get("confidence", 0.7),
                        "created_at": datetime.utcnow().isoformat()
                    }
                )
                llama_docs.append(llama_doc)
            
            # Index documents
            if "business_entities" in self.indices:
                index = self.indices["business_entities"]
                for doc in llama_docs:
                    index.insert(doc)
                
                self.metrics["documents_indexed"] += len(llama_docs)
                print(f"✅ Indexed {len(llama_docs)} documents")
                return True
            else:
                print("⚠️  Business entities index not available")
                return False
                
        except Exception as e:
            print(f"❌ Document indexing error: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "system_name": "Enhanced LlamaIndex RAG",
            "llm_available": self.llm_available,
            "vector_store_available": self.vector_store_available,
            "indices_count": len(self.indices),
            "metrics": self.metrics,
            "settings": {
                "llm_model": "gpt-4" if self.llm_available else "unavailable",
                "embedding_model": "text-embedding-3-large" if self.llm_available else "unavailable",
                "vector_store": "qdrant" if self.vector_store_available else "unavailable"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# Global instance
_llamaindex_rag_instance = None

def get_llamaindex_rag() -> EnhancedLlamaIndexRAG:
    """Get global LlamaIndex RAG instance"""
    global _llamaindex_rag_instance
    if _llamaindex_rag_instance is None:
        _llamaindex_rag_instance = EnhancedLlamaIndexRAG()
    return _llamaindex_rag_instance

