#!/usr/bin/env python3
"""
SOPHIA Intel: Advanced RAG Implementation
Integrates LlamaIndex, Haystack Enterprise, and cutting-edge RAG technologies
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

# LlamaIndex imports
from llama_index.core import VectorStoreIndex, ServiceContext, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openrouter import OpenRouter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import PropertyGraphIndex
from llama_index.core.query_engine import RetrieverQueryEngine

# Haystack imports
from haystack import Pipeline, Document as HaystackDocument
from haystack.components.retrievers import QdrantEmbeddingRetriever
from haystack.components.generators import OpenAIGenerator
from haystack.components.builders import PromptBuilder
from haystack.components.joiners import DocumentJoiner

# Multi-modal imports
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.core.schema import ImageDocument

# Graph database imports
from neo4j import GraphDatabase
import networkx as nx

# Vector database
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Document processing
import pandas as pd
from pathlib import Path
import fitz  # PyMuPDF for PDF processing
from PIL import Image

from loguru import logger

class RAGTier(Enum):
    BASIC = "basic"
    ENHANCED = "enhanced"
    ENTERPRISE = "enterprise"
    ADVANCED = "advanced"

class DocumentType(Enum):
    TEXT = "text"
    PDF = "pdf"
    IMAGE = "image"
    STRUCTURED = "structured"
    MULTIMODAL = "multimodal"

@dataclass
class RAGConfig:
    """Configuration for advanced RAG system"""
    tier: RAGTier
    openai_api_key: str
    openrouter_api_key: str
    qdrant_url: str
    qdrant_api_key: Optional[str] = None
    neo4j_uri: Optional[str] = None
    neo4j_user: Optional[str] = None
    neo4j_password: Optional[str] = None
    llama_cloud_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 3072
    chunk_size: int = 1024
    chunk_overlap: int = 200

class AdvancedDocumentProcessor:
    """Advanced document processing with multi-modal capabilities"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.setup_processors()
    
    def setup_processors(self):
        """Setup document processors"""
        # Multi-modal LLM for image analysis
        if self.config.tier in [RAGTier.ENTERPRISE, RAGTier.ADVANCED]:
            self.mm_llm = OpenAIMultiModal(
                model="gpt-4-vision-preview",
                api_key=self.config.openai_api_key
            )
        
        # LlamaParse for advanced document parsing
        if self.config.llama_cloud_api_key and self.config.tier != RAGTier.BASIC:
            try:
                from llama_parse import LlamaParse
                self.llama_parse = LlamaParse(
                    api_key=self.config.llama_cloud_api_key,
                    result_type="markdown",
                    premium_mode=True
                )
            except ImportError:
                logger.warning("LlamaParse not available, using standard processing")
                self.llama_parse = None
        else:
            self.llama_parse = None
    
    async def process_documents(self, file_paths: List[str]) -> List[Document]:
        """Process multiple documents with appropriate handlers"""
        documents = []
        
        for file_path in file_paths:
            doc_type = self.identify_document_type(file_path)
            
            if doc_type == DocumentType.PDF:
                docs = await self.process_pdf_document(file_path)
            elif doc_type == DocumentType.IMAGE:
                docs = await self.process_image_document(file_path)
            elif doc_type == DocumentType.STRUCTURED:
                docs = await self.process_structured_document(file_path)
            else:
                docs = await self.process_text_document(file_path)
            
            documents.extend(docs)
        
        return documents
    
    def identify_document_type(self, file_path: str) -> DocumentType:
        """Identify document type from file extension"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.pdf':
            return DocumentType.PDF
        elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return DocumentType.IMAGE
        elif suffix in ['.csv', '.xlsx', '.xls']:
            return DocumentType.STRUCTURED
        else:
            return DocumentType.TEXT
    
    async def process_pdf_document(self, file_path: str) -> List[Document]:
        """Process PDF with advanced parsing"""
        documents = []
        
        if self.llama_parse and self.config.tier != RAGTier.BASIC:
            # Use LlamaParse for advanced PDF processing
            try:
                parsed_docs = await self.llama_parse.aload_data(file_path)
                return parsed_docs
            except Exception as e:
                logger.warning(f"LlamaParse failed for {file_path}: {e}, falling back to standard processing")
        
        # Standard PDF processing
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            if text.strip():
                document = Document(
                    text=text,
                    metadata={
                        "source": file_path,
                        "page": page_num + 1,
                        "document_type": "pdf"
                    }
                )
                documents.append(document)
            
            # Extract images if multi-modal processing is enabled
            if self.config.tier in [RAGTier.ENTERPRISE, RAGTier.ADVANCED]:
                images = page.get_images()
                for img_index, img in enumerate(images):
                    # Process embedded images
                    image_doc = await self.process_embedded_image(page, img, file_path, page_num, img_index)
                    if image_doc:
                        documents.append(image_doc)
        
        doc.close()
        return documents
    
    async def process_image_document(self, file_path: str) -> List[Document]:
        """Process image document with business intelligence focus"""
        if self.config.tier not in [RAGTier.ENTERPRISE, RAGTier.ADVANCED]:
            # Basic tier: just store image metadata
            return [Document(
                text=f"Image file: {file_path}",
                metadata={"source": file_path, "document_type": "image"}
            )]
        
        # Advanced image analysis
        business_analysis_prompt = """
        Analyze this business image/chart/dashboard for Pay Ready (fintech/payments company).
        
        Extract and structure:
        1. Key metrics and KPIs visible
        2. Numerical values and percentages
        3. Time periods and date ranges
        4. Trends and patterns
        5. Performance indicators (colors, alerts)
        6. Business insights and implications
        7. Data quality assessment
        
        Format as structured business intelligence data suitable for RAG retrieval.
        """
        
        try:
            response = await self.mm_llm.acomplete(
                prompt=business_analysis_prompt,
                image_documents=[ImageDocument(image_path=file_path)]
            )
            
            return [Document(
                text=response.text,
                metadata={
                    "source": file_path,
                    "document_type": "image_analysis",
                    "analysis_type": "business_intelligence"
                }
            )]
        except Exception as e:
            logger.error(f"Failed to analyze image {file_path}: {e}")
            return []
    
    async def process_structured_document(self, file_path: str) -> List[Document]:
        """Process structured data (CSV, Excel) as business documents"""
        documents = []
        
        # Load structured data
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Create summary document
        summary_text = f"""
        Structured Data Summary for {Path(file_path).name}:
        
        Dataset Overview:
        - Total Records: {len(df)}
        - Columns: {list(df.columns)}
        - Data Types: {df.dtypes.to_dict()}
        
        Statistical Summary:
        {df.describe().to_string()}
        
        Sample Data:
        {df.head().to_string()}
        """
        
        documents.append(Document(
            text=summary_text,
            metadata={
                "source": file_path,
                "document_type": "structured_summary",
                "record_count": len(df),
                "columns": list(df.columns)
            }
        ))
        
        # Create documents for significant rows (if dataset is small enough)
        if len(df) <= 1000:  # Only for manageable datasets
            for idx, row in df.iterrows():
                row_text = self.create_business_row_document(row, file_path, idx)
                documents.append(Document(
                    text=row_text,
                    metadata={
                        "source": file_path,
                        "document_type": "structured_row",
                        "row_index": idx
                    }
                ))
        
        return documents
    
    def create_business_row_document(self, row: pd.Series, file_path: str, row_index: int) -> str:
        """Create business-focused document from data row"""
        doc_text = f"Data Record {row_index + 1} from {Path(file_path).name}:\n\n"
        
        for column, value in row.items():
            if pd.notna(value):
                # Format based on likely business context
                if any(keyword in column.lower() for keyword in ['revenue', 'sales', 'amount', 'price', 'cost']):
                    doc_text += f"• {column}: ${value:,.2f}\n" if isinstance(value, (int, float)) else f"• {column}: {value}\n"
                elif any(keyword in column.lower() for keyword in ['date', 'time']):
                    doc_text += f"• {column}: {value}\n"
                elif any(keyword in column.lower() for keyword in ['rate', 'percent', '%']):
                    doc_text += f"• {column}: {value}%\n" if isinstance(value, (int, float)) else f"• {column}: {value}\n"
                else:
                    doc_text += f"• {column}: {value}\n"
        
        return doc_text
    
    async def process_text_document(self, file_path: str) -> List[Document]:
        """Process standard text document"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return [Document(
            text=content,
            metadata={
                "source": file_path,
                "document_type": "text"
            }
        )]

class LlamaIndexRAGSystem:
    """Advanced RAG system using LlamaIndex"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.setup_components()
    
    def setup_components(self):
        """Setup LlamaIndex components"""
        # LLM setup
        self.llm = OpenRouter(
            api_key=self.config.openrouter_api_key,
            model="anthropic/claude-3.5-sonnet"
        )
        
        # Enhanced embeddings
        self.embed_model = OpenAIEmbedding(
            model=self.config.embedding_model,
            api_key=self.config.openai_api_key,
            dimensions=self.config.embedding_dimensions
        )
        
        # Vector store
        self.qdrant_client = QdrantClient(
            url=self.config.qdrant_url,
            api_key=self.config.qdrant_api_key
        )
        
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name="sophia_advanced_rag"
        )
        
        # Service context
        self.service_context = ServiceContext.from_defaults(
            llm=self.llm,
            embed_model=self.embed_model,
            node_parser=SentenceSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap
            )
        )
        
        # Document processor
        self.doc_processor = AdvancedDocumentProcessor(config)
    
    async def create_advanced_index(self, documents: List[Document]) -> VectorStoreIndex:
        """Create advanced index with business context"""
        
        if self.config.tier == RAGTier.ADVANCED:
            # Use Property Graph Index for advanced relationship mapping
            index = PropertyGraphIndex.from_documents(
                documents,
                service_context=self.service_context,
                vector_store=self.vector_store,
                show_progress=True
            )
        else:
            # Standard vector index
            index = VectorStoreIndex.from_documents(
                documents,
                service_context=self.service_context,
                vector_store=self.vector_store,
                show_progress=True
            )
        
        return index
    
    async def advanced_query(
        self, 
        query: str, 
        business_context: Dict[str, Any],
        index: VectorStoreIndex
    ) -> Dict[str, Any]:
        """Execute advanced business intelligence query"""
        
        # Enhanced prompt with Pay Ready business context
        enhanced_prompt = f"""
        You are SOPHIA, Pay Ready's advanced business intelligence AI assistant.
        
        Business Context:
        - Company: Pay Ready (fintech/payments industry)
        - User Role: {business_context.get('user_role', 'analyst')}
        - Department: {business_context.get('department', 'general')}
        - Current Priority: {business_context.get('business_priority', 'growth')}
        - Data Sources Available: {business_context.get('data_sources', [])}
        
        User Query: {query}
        
        Provide a comprehensive business intelligence response that:
        1. Directly addresses the query with specific data points
        2. Identifies relevant business metrics and KPIs
        3. Provides actionable recommendations
        4. Highlights data quality and confidence levels
        5. Suggests follow-up analyses or questions
        6. References specific sources used
        
        Format your response for executive consumption with clear insights and next steps.
        """
        
        # Create query engine with advanced settings
        query_engine = index.as_query_engine(
            response_mode="tree_summarize",
            similarity_top_k=15,
            use_async=True,
            streaming=False
        )
        
        # Execute query
        response = await query_engine.aquery(enhanced_prompt)
        
        return {
            "response": response.response,
            "source_nodes": [
                {
                    "text": node.text[:200] + "...",
                    "source": node.metadata.get("source", "unknown"),
                    "score": node.score if hasattr(node, 'score') else 0.0
                }
                for node in response.source_nodes
            ],
            "metadata": response.metadata,
            "business_context": business_context,
            "confidence_score": self.calculate_response_confidence(response)
        }
    
    def calculate_response_confidence(self, response) -> float:
        """Calculate confidence score for response"""
        # Simple confidence calculation based on source nodes
        if not response.source_nodes:
            return 0.0
        
        # Average score of source nodes
        scores = [getattr(node, 'score', 0.5) for node in response.source_nodes]
        avg_score = sum(scores) / len(scores)
        
        # Adjust based on number of sources
        source_bonus = min(0.2, len(response.source_nodes) * 0.02)
        
        return min(1.0, avg_score + source_bonus)

class HaystackEnterpriseRAG:
    """Enterprise RAG system using Haystack"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.setup_enterprise_pipeline()
    
    def setup_enterprise_pipeline(self):
        """Setup enterprise-grade RAG pipeline"""
        
        # Advanced retriever with hybrid search
        self.retriever = QdrantEmbeddingRetriever(
            document_store=self.setup_document_store(),
            top_k=20,
            scale_score=True,
            return_embedding=True
        )
        
        # Business-focused prompt builder
        self.prompt_builder = PromptBuilder(
            template="""
            You are SOPHIA, Pay Ready's enterprise business intelligence AI.
            
            Business Intelligence Context:
            - Company: Pay Ready (fintech/payments)
            - Analysis Type: {{analysis_type}}
            - User Role: {{user_role}}
            - Department: {{department}}
            - Priority Focus: {{business_priority}}
            - Time Frame: {{time_frame}}
            
            Retrieved Business Data:
            {% for doc in documents %}
            Source: {{doc.meta.source}}
            Relevance: {{doc.score | round(3)}}
            Content: {{doc.content}}
            ---
            {% endfor %}
            
            Business Query: {{query}}
            
            Provide enterprise-grade business intelligence analysis:
            
            ## Executive Summary
            [Key findings and recommendations]
            
            ## Detailed Analysis
            [Comprehensive analysis with data points]
            
            ## Business Metrics & KPIs
            [Relevant metrics and performance indicators]
            
            ## Actionable Recommendations
            [Specific next steps and strategies]
            
            ## Data Quality Assessment
            [Confidence levels and data limitations]
            
            ## Follow-up Opportunities
            [Suggested additional analyses]
            
            Analysis:
            """
        )
        
        # Enterprise generator with advanced settings
        self.generator = OpenAIGenerator(
            api_key=self.config.openai_api_key,
            model="gpt-4-turbo",
            generation_kwargs={
                "temperature": 0.1,
                "max_tokens": 3000,
                "top_p": 0.95
            }
        )
        
        # Build the pipeline
        self.pipeline = Pipeline()
        self.pipeline.add_component("retriever", self.retriever)
        self.pipeline.add_component("prompt_builder", self.prompt_builder)
        self.pipeline.add_component("generator", self.generator)
        
        # Connect components
        self.pipeline.connect("retriever", "prompt_builder.documents")
        self.pipeline.connect("prompt_builder", "generator")
    
    def setup_document_store(self):
        """Setup Qdrant document store for Haystack"""
        # This would be implemented based on Haystack's Qdrant integration
        # Placeholder for actual implementation
        pass
    
    async def enterprise_query(
        self, 
        query: str, 
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute enterprise business intelligence query"""
        
        result = self.pipeline.run({
            "retriever": {"query": query},
            "prompt_builder": {
                "query": query,
                "analysis_type": business_context.get("analysis_type", "general"),
                "user_role": business_context.get("user_role", "analyst"),
                "department": business_context.get("department", "general"),
                "business_priority": business_context.get("business_priority", "growth"),
                "time_frame": business_context.get("time_frame", "current")
            }
        })
        
        return {
            "response": result["generator"]["replies"][0],
            "sources": [
                {
                    "source": doc.meta.get("source", "unknown"),
                    "score": doc.score,
                    "content_preview": doc.content[:150] + "..."
                }
                for doc in result["retriever"]["documents"]
            ],
            "business_context": business_context,
            "confidence": self.calculate_enterprise_confidence(result),
            "analysis_type": "enterprise_rag"
        }
    
    def calculate_enterprise_confidence(self, result) -> float:
        """Calculate confidence for enterprise response"""
        documents = result["retriever"]["documents"]
        if not documents:
            return 0.0
        
        # Calculate based on document scores and diversity
        scores = [doc.score for doc in documents]
        avg_score = sum(scores) / len(scores)
        
        # Bonus for source diversity
        sources = set(doc.meta.get("source", "unknown") for doc in documents)
        diversity_bonus = min(0.3, len(sources) * 0.05)
        
        return min(1.0, avg_score + diversity_bonus)

class GraphEnhancedRAG:
    """Graph-enhanced RAG for complex business relationships"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        if config.neo4j_uri:
            self.neo4j_driver = GraphDatabase.driver(
                config.neo4j_uri,
                auth=(config.neo4j_user, config.neo4j_password)
            )
            self.setup_business_graph()
        else:
            self.neo4j_driver = None
    
    def setup_business_graph(self):
        """Setup Pay Ready business knowledge graph"""
        if not self.neo4j_driver:
            return
        
        with self.neo4j_driver.session() as session:
            # Create constraints
            session.run("""
                CREATE CONSTRAINT business_entity_name IF NOT EXISTS 
                FOR (e:BusinessEntity) REQUIRE e.name IS UNIQUE
            """)
            
            # Create Pay Ready specific entity types
            session.run("""
                MERGE (customer:EntityType {name: 'Customer', domain: 'pay_ready'})
                MERGE (product:EntityType {name: 'Product', domain: 'pay_ready'})
                MERGE (metric:EntityType {name: 'Metric', domain: 'pay_ready'})
                MERGE (process:EntityType {name: 'Process', domain: 'pay_ready'})
                MERGE (person:EntityType {name: 'Person', domain: 'pay_ready'})
                MERGE (system:EntityType {name: 'System', domain: 'pay_ready'})
            """)
    
    async def create_business_knowledge_graph(
        self, 
        entities: List[Dict], 
        relationships: List[Dict]
    ):
        """Create business knowledge graph from extracted entities"""
        if not self.neo4j_driver:
            logger.warning("Neo4j not configured, skipping graph creation")
            return
        
        with self.neo4j_driver.session() as session:
            # Create business entities
            for entity in entities:
                session.run("""
                    MERGE (e:BusinessEntity {name: $name})
                    SET e.type = $type,
                        e.description = $description,
                        e.confidence = $confidence,
                        e.data_sources = $data_sources,
                        e.domain = 'pay_ready',
                        e.created_at = datetime(),
                        e.updated_at = datetime()
                """, **entity)
            
            # Create relationships
            for rel in relationships:
                session.run("""
                    MATCH (a:BusinessEntity {name: $source})
                    MATCH (b:BusinessEntity {name: $target})
                    MERGE (a)-[r:BUSINESS_RELATIONSHIP {type: $rel_type}]->(b)
                    SET r.strength = $strength,
                        r.evidence_count = $evidence_count,
                        r.created_at = datetime(),
                        r.updated_at = datetime()
                """, **rel)
    
    async def graph_enhanced_query(
        self, 
        query: str, 
        vector_rag_system: LlamaIndexRAGSystem
    ) -> Dict[str, Any]:
        """Execute graph-enhanced RAG query"""
        
        if not self.neo4j_driver:
            # Fallback to vector-only RAG
            return await vector_rag_system.advanced_query(query, {}, vector_rag_system.index)
        
        # Extract entities from query
        query_entities = await self.extract_entities_from_query(query)
        
        # Find related entities in graph
        with self.neo4j_driver.session() as session:
            graph_context = session.run("""
                MATCH (e:BusinessEntity)
                WHERE e.name IN $entities
                OPTIONAL MATCH (e)-[r:BUSINESS_RELATIONSHIP]-(related:BusinessEntity)
                RETURN e.name as entity, 
                       e.type as entity_type,
                       collect({
                           name: related.name, 
                           type: related.type,
                           relationship: r.type,
                           strength: r.strength
                       }) as related_entities
            """, entities=query_entities).data()
        
        # Enhance query with graph context
        enhanced_query = self.build_graph_enhanced_query(query, graph_context)
        
        # Execute enhanced vector RAG
        vector_result = await vector_rag_system.advanced_query(
            enhanced_query, 
            {"analysis_type": "graph_enhanced"}, 
            vector_rag_system.index
        )
        
        return {
            **vector_result,
            "graph_context": graph_context,
            "entity_relationships": self.analyze_entity_relationships(graph_context),
            "analysis_type": "graph_enhanced_rag"
        }
    
    async def extract_entities_from_query(self, query: str) -> List[str]:
        """Extract business entities from query text"""
        # Simple entity extraction - in production, use NER models
        common_entities = [
            "revenue", "sales", "customers", "products", "pipeline", "conversion",
            "churn", "retention", "growth", "market", "competition", "pricing",
            "costs", "expenses", "profit", "margin", "forecast", "budget"
        ]
        
        entities = []
        query_lower = query.lower()
        for entity in common_entities:
            if entity in query_lower:
                entities.append(entity)
        
        return entities
    
    def build_graph_enhanced_query(self, original_query: str, graph_context: List[Dict]) -> str:
        """Build enhanced query with graph context"""
        if not graph_context:
            return original_query
        
        context_text = "Related business entities and relationships:\n"
        for item in graph_context:
            context_text += f"- {item['entity']} ({item['entity_type']})\n"
            for rel in item['related_entities']:
                if rel['name']:  # Skip None values
                    context_text += f"  → {rel['relationship']}: {rel['name']} (strength: {rel['strength']})\n"
        
        enhanced_query = f"{context_text}\n\nOriginal Query: {original_query}"
        return enhanced_query
    
    def analyze_entity_relationships(self, graph_context: List[Dict]) -> Dict[str, Any]:
        """Analyze entity relationships for insights"""
        if not graph_context:
            return {}
        
        total_entities = len(graph_context)
        total_relationships = sum(len(item['related_entities']) for item in graph_context)
        
        # Calculate relationship strengths
        strengths = []
        for item in graph_context:
            for rel in item['related_entities']:
                if rel['strength'] is not None:
                    strengths.append(rel['strength'])
        
        avg_strength = sum(strengths) / len(strengths) if strengths else 0.0
        
        return {
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "average_relationship_strength": avg_strength,
            "relationship_density": total_relationships / total_entities if total_entities > 0 else 0
        }

class AdvancedRAGOrchestrator:
    """Main orchestrator for advanced RAG system"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.setup_systems()
    
    def setup_systems(self):
        """Setup all RAG systems based on tier"""
        # Always setup basic LlamaIndex system
        self.llama_rag = LlamaIndexRAGSystem(self.config)
        
        # Setup enterprise systems for higher tiers
        if self.config.tier in [RAGTier.ENTERPRISE, RAGTier.ADVANCED]:
            self.haystack_rag = HaystackEnterpriseRAG(self.config)
        
        # Setup graph system for advanced tier
        if self.config.tier == RAGTier.ADVANCED:
            self.graph_rag = GraphEnhancedRAG(self.config)
    
    async def initialize(self, document_paths: List[str]):
        """Initialize the RAG system with documents"""
        logger.info(f"Initializing Advanced RAG System (Tier: {self.config.tier.value})")
        
        # Process documents
        documents = await self.llama_rag.doc_processor.process_documents(document_paths)
        logger.info(f"Processed {len(documents)} documents")
        
        # Create index
        self.index = await self.llama_rag.create_advanced_index(documents)
        logger.info("Created advanced index")
        
        # Setup graph if advanced tier
        if self.config.tier == RAGTier.ADVANCED and hasattr(self, 'graph_rag'):
            # Extract entities and relationships for graph
            entities, relationships = await self.extract_business_entities_and_relationships(documents)
            await self.graph_rag.create_business_knowledge_graph(entities, relationships)
            logger.info("Created business knowledge graph")
    
    async def query(
        self, 
        query: str, 
        business_context: Dict[str, Any],
        preferred_system: str = "auto"
    ) -> Dict[str, Any]:
        """Execute query using appropriate RAG system"""
        
        if preferred_system == "auto":
            # Auto-select based on query complexity and tier
            if self.config.tier == RAGTier.ADVANCED and self.is_complex_query(query):
                preferred_system = "graph"
            elif self.config.tier in [RAGTier.ENTERPRISE, RAGTier.ADVANCED]:
                preferred_system = "haystack"
            else:
                preferred_system = "llama"
        
        # Execute query with selected system
        if preferred_system == "graph" and hasattr(self, 'graph_rag'):
            result = await self.graph_rag.graph_enhanced_query(query, self.llama_rag)
        elif preferred_system == "haystack" and hasattr(self, 'haystack_rag'):
            result = await self.haystack_rag.enterprise_query(query, business_context)
        else:
            result = await self.llama_rag.advanced_query(query, business_context, self.index)
        
        # Add system metadata
        result["system_used"] = preferred_system
        result["tier"] = self.config.tier.value
        result["timestamp"] = datetime.utcnow().isoformat()
        
        return result
    
    def is_complex_query(self, query: str) -> bool:
        """Determine if query is complex enough for graph RAG"""
        complexity_indicators = [
            "relationship", "correlation", "impact", "influence", "connected",
            "related", "affects", "causes", "leads to", "results in",
            "between", "among", "across", "compare", "contrast"
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in complexity_indicators)
    
    async def extract_business_entities_and_relationships(
        self, 
        documents: List[Document]
    ) -> tuple[List[Dict], List[Dict]]:
        """Extract business entities and relationships from documents"""
        # Simplified extraction - in production, use advanced NER and relationship extraction
        entities = []
        relationships = []
        
        # Common Pay Ready business entities
        business_entities = {
            "revenue": {"type": "metric", "description": "Company revenue"},
            "customers": {"type": "stakeholder", "description": "Customer base"},
            "products": {"type": "offering", "description": "Product portfolio"},
            "sales": {"type": "process", "description": "Sales operations"},
            "marketing": {"type": "process", "description": "Marketing operations"},
            "support": {"type": "process", "description": "Customer support"}
        }
        
        for name, info in business_entities.items():
            entities.append({
                "name": name,
                "type": info["type"],
                "description": info["description"],
                "confidence": 0.8,
                "data_sources": ["documents"]
            })
        
        # Simple relationships
        simple_relationships = [
            {"source": "sales", "target": "revenue", "rel_type": "drives", "strength": 0.9, "evidence_count": 1},
            {"source": "customers", "target": "revenue", "rel_type": "generates", "strength": 0.8, "evidence_count": 1},
            {"source": "marketing", "target": "customers", "rel_type": "acquires", "strength": 0.7, "evidence_count": 1},
            {"source": "products", "target": "sales", "rel_type": "enables", "strength": 0.8, "evidence_count": 1}
        ]
        
        relationships.extend(simple_relationships)
        
        return entities, relationships

# Example usage and configuration
async def main():
    """Example usage of advanced RAG system"""
    
    # Configuration for different tiers
    configs = {
        "enhanced": RAGConfig(
            tier=RAGTier.ENHANCED,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            qdrant_url="http://localhost:6333",
            embedding_model="text-embedding-3-large",
            embedding_dimensions=3072
        ),
        "enterprise": RAGConfig(
            tier=RAGTier.ENTERPRISE,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            qdrant_url="http://localhost:6333",
            llama_cloud_api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
            embedding_model="text-embedding-3-large",
            embedding_dimensions=3072
        ),
        "advanced": RAGConfig(
            tier=RAGTier.ADVANCED,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            qdrant_url="http://localhost:6333",
            llama_cloud_api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
            neo4j_uri=os.getenv("NEO4J_URI"),
            neo4j_user=os.getenv("NEO4J_USER"),
            neo4j_password=os.getenv("NEO4J_PASSWORD"),
            embedding_model="text-embedding-3-large",
            embedding_dimensions=3072
        )
    }
    
    # Initialize advanced RAG system
    config = configs["enhanced"]  # Start with enhanced tier
    orchestrator = AdvancedRAGOrchestrator(config)
    
    # Example document paths
    document_paths = [
        "/path/to/pay_ready_business_plan.pdf",
        "/path/to/financial_reports.xlsx",
        "/path/to/sales_dashboard.png",
        "/path/to/customer_data.csv"
    ]
    
    # Initialize with documents
    await orchestrator.initialize(document_paths)
    
    # Example business context
    business_context = {
        "user_role": "ceo",
        "department": "executive",
        "business_priority": "growth",
        "analysis_type": "strategic",
        "time_frame": "quarterly"
    }
    
    # Example queries
    queries = [
        "What are our key revenue drivers and how can we optimize them?",
        "Analyze the relationship between customer acquisition cost and lifetime value",
        "What trends do you see in our sales pipeline and conversion rates?",
        "How does our product performance correlate with customer satisfaction?"
    ]
    
    # Execute queries
    for query in queries:
        print(f"\n🔍 Query: {query}")
        result = await orchestrator.query(query, business_context)
        print(f"📊 System Used: {result['system_used']}")
        print(f"🎯 Confidence: {result['confidence_score']:.2f}")
        print(f"📝 Response: {result['response'][:200]}...")
        print(f"📚 Sources: {len(result['source_nodes'])} documents")

if __name__ == "__main__":
    asyncio.run(main())

