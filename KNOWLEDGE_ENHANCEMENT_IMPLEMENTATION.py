#!/usr/bin/env python3
"""
SOPHIA Intel: Knowledge Architecture Enhancement Implementation
Implements continuous learning and business context accumulation for Pay Ready
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import re

import asyncpg
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, CreateCollection, PointStruct
import openai
from loguru import logger

class KnowledgeType(Enum):
    BUSINESS_ENTITY = "business_entity"
    BUSINESS_PROCESS = "business_process"
    TECHNICAL_KNOWLEDGE = "technical_knowledge"
    REPOSITORY_INSIGHT = "repository_insight"
    USER_FEEDBACK = "user_feedback"
    CROSS_PLATFORM_CORRELATION = "cross_platform_correlation"

class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"

@dataclass
class BusinessEntity:
    """Represents a Pay Ready business entity"""
    name: str
    entity_type: str  # customer, product, process, metric, person, etc.
    description: str
    attributes: Dict[str, Any]
    data_sources: List[str]  # Which systems this entity appears in
    confidence_score: float
    relationships: List[Dict[str, Any]]
    embedding_id: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class KnowledgeItem:
    """Individual knowledge item extracted from interactions"""
    content: str
    knowledge_type: KnowledgeType
    entities_mentioned: List[str]
    confidence_level: ConfidenceLevel
    source_interaction_id: str
    metadata: Dict[str, Any]
    embedding_vector: Optional[List[float]] = None
    created_at: datetime = None

class PayReadyEntityRecognizer:
    """Recognizes Pay Ready specific business entities from text"""
    
    def __init__(self):
        self.entity_patterns = {
            "customer": [
                r"\b(?:customer|client|account|prospect)\s+([A-Z][a-zA-Z\s&]+(?:Inc|LLC|Corp|Ltd)?)\b",
                r"\b([A-Z][a-zA-Z\s&]+(?:Inc|LLC|Corp|Ltd))\s+(?:customer|client|account)\b"
            ],
            "product": [
                r"\b(?:product|solution|platform|service)\s+([A-Z][a-zA-Z\s]+)\b",
                r"\b([A-Z][a-zA-Z\s]+)\s+(?:product|solution|platform|service)\b"
            ],
            "metric": [
                r"\b(ARR|MRR|CAC|LTV|churn\s+rate|conversion\s+rate|pipeline\s+value)\b",
                r"\b(\d+(?:\.\d+)?%?\s+(?:growth|increase|decrease|improvement))\b"
            ],
            "process": [
                r"\b(sales\s+process|onboarding\s+process|support\s+process|billing\s+process)\b",
                r"\b(lead\s+qualification|deal\s+review|customer\s+success)\b"
            ],
            "person": [
                r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+from\s+|\s+at\s+|\s+in\s+)\b",
                r"\b(?:CEO|CTO|VP|Director|Manager)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b"
            ]
        }
        
        self.pay_ready_specific = {
            "departments": ["sales", "marketing", "customer success", "product", "engineering", "finance"],
            "systems": ["salesforce", "hubspot", "gong", "intercom", "slack", "asana", "linear", "netsuite", "looker", "factor ai", "notion"],
            "metrics": ["arr", "mrr", "cac", "ltv", "nps", "churn rate", "pipeline value", "conversion rate", "deal velocity"],
            "processes": ["lead qualification", "deal review", "customer onboarding", "support ticket resolution", "feature development"]
        }
    
    async def extract_entities(self, text: str) -> List[BusinessEntity]:
        """Extract business entities from text"""
        entities = []
        
        # Extract using regex patterns
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_name = match.group(1).strip()
                    
                    # Skip if too short or generic
                    if len(entity_name) < 3 or entity_name.lower() in ['the', 'and', 'for', 'with']:
                        continue
                    
                    entity = BusinessEntity(
                        name=entity_name,
                        entity_type=entity_type,
                        description=f"{entity_type.title()} identified from conversation",
                        attributes={"source_pattern": pattern, "match_context": match.group(0)},
                        data_sources=["conversation"],
                        confidence_score=0.7,
                        relationships=[],
                        created_at=datetime.utcnow()
                    )
                    entities.append(entity)
        
        # Extract Pay Ready specific entities
        for category, items in self.pay_ready_specific.items():
            for item in items:
                if item.lower() in text.lower():
                    entity = BusinessEntity(
                        name=item,
                        entity_type=category,
                        description=f"Pay Ready {category} entity",
                        attributes={"category": category, "pay_ready_specific": True},
                        data_sources=["conversation"],
                        confidence_score=0.9,
                        relationships=[],
                        created_at=datetime.utcnow()
                    )
                    entities.append(entity)
        
        return entities

class KnowledgeExtractor:
    """Extracts structured knowledge from conversations"""
    
    def __init__(self, openai_api_key: str):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
    
    async def extract_knowledge(
        self, 
        interaction_text: str, 
        entities: List[BusinessEntity],
        context: Dict[str, Any]
    ) -> List[KnowledgeItem]:
        """Extract structured knowledge from interaction"""
        
        knowledge_items = []
        
        # Use OpenAI to extract structured knowledge
        prompt = f"""
        Analyze the following business conversation and extract key knowledge items:
        
        Conversation: {interaction_text}
        
        Identified Entities: {[e.name for e in entities]}
        
        Extract:
        1. Business processes mentioned
        2. Key relationships between entities
        3. Important metrics or KPIs
        4. Decision criteria or business rules
        5. Technical insights or requirements
        
        Format as JSON with fields: content, type, confidence, entities_mentioned, metadata
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Parse response and create knowledge items
            extracted_data = json.loads(response.choices[0].message.content)
            
            for item_data in extracted_data.get("knowledge_items", []):
                knowledge_item = KnowledgeItem(
                    content=item_data.get("content", ""),
                    knowledge_type=KnowledgeType(item_data.get("type", "business_entity")),
                    entities_mentioned=item_data.get("entities_mentioned", []),
                    confidence_level=ConfidenceLevel(item_data.get("confidence", "medium")),
                    source_interaction_id=context.get("interaction_id", ""),
                    metadata=item_data.get("metadata", {}),
                    created_at=datetime.utcnow()
                )
                knowledge_items.append(knowledge_item)
                
        except Exception as e:
            logger.error(f"Failed to extract knowledge: {e}")
            
            # Fallback: Create basic knowledge item from interaction
            knowledge_item = KnowledgeItem(
                content=interaction_text[:500],  # Truncate for storage
                knowledge_type=KnowledgeType.USER_FEEDBACK,
                entities_mentioned=[e.name for e in entities],
                confidence_level=ConfidenceLevel.MEDIUM,
                source_interaction_id=context.get("interaction_id", ""),
                metadata={"extraction_method": "fallback", "error": str(e)},
                created_at=datetime.utcnow()
            )
            knowledge_items.append(knowledge_item)
        
        return knowledge_items

class EnhancedKnowledgeDatabase:
    """Enhanced database operations for knowledge management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(self.database_url)
        await self.create_enhanced_schema()
    
    async def create_enhanced_schema(self):
        """Create enhanced database schema for knowledge management"""
        schema_sql = """
        -- Enhanced business entities table
        CREATE TABLE IF NOT EXISTS business_entities (
            id SERIAL PRIMARY KEY,
            entity_type VARCHAR(100) NOT NULL,
            entity_name VARCHAR(255) NOT NULL,
            description TEXT,
            attributes JSONB DEFAULT '{}',
            data_sources TEXT[] DEFAULT '{}',
            confidence_score FLOAT DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
            embedding_id VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(entity_type, entity_name)
        );
        
        -- Knowledge interactions tracking
        CREATE TABLE IF NOT EXISTS knowledge_interactions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(100),
            interaction_type VARCHAR(50) DEFAULT 'conversation',
            content TEXT NOT NULL,
            extracted_knowledge JSONB DEFAULT '{}',
            entities_mentioned TEXT[] DEFAULT '{}',
            confidence_score FLOAT DEFAULT 0.5,
            feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5),
            outcome_tracked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Entity relationships graph
        CREATE TABLE IF NOT EXISTS knowledge_graph_edges (
            id SERIAL PRIMARY KEY,
            source_entity_id INTEGER REFERENCES business_entities(id) ON DELETE CASCADE,
            target_entity_id INTEGER REFERENCES business_entities(id) ON DELETE CASCADE,
            relationship_type VARCHAR(100) NOT NULL,
            strength FLOAT DEFAULT 0.5 CHECK (strength >= 0 AND strength <= 1),
            evidence_count INTEGER DEFAULT 1,
            metadata JSONB DEFAULT '{}',
            last_reinforced TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_entity_id, target_entity_id, relationship_type)
        );
        
        -- Repository knowledge storage
        CREATE TABLE IF NOT EXISTS repository_knowledge (
            id SERIAL PRIMARY KEY,
            knowledge_type VARCHAR(100) NOT NULL,
            component_path VARCHAR(500),
            knowledge_text TEXT NOT NULL,
            code_examples TEXT,
            related_issues TEXT[] DEFAULT '{}',
            performance_impact JSONB DEFAULT '{}',
            best_practices JSONB DEFAULT '{}',
            confidence_score FLOAT DEFAULT 0.5,
            embedding_id VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Cross-platform data correlations
        CREATE TABLE IF NOT EXISTS cross_platform_correlations (
            id SERIAL PRIMARY KEY,
            entity_name VARCHAR(255) NOT NULL,
            platform_a VARCHAR(100) NOT NULL,
            platform_b VARCHAR(100) NOT NULL,
            correlation_type VARCHAR(100) NOT NULL,
            correlation_strength FLOAT DEFAULT 0.5,
            evidence JSONB DEFAULT '{}',
            last_verified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(entity_name, platform_a, platform_b, correlation_type)
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_business_entities_type ON business_entities(entity_type);
        CREATE INDEX IF NOT EXISTS idx_business_entities_name ON business_entities(entity_name);
        CREATE INDEX IF NOT EXISTS idx_business_entities_confidence ON business_entities(confidence_score);
        CREATE INDEX IF NOT EXISTS idx_knowledge_interactions_session ON knowledge_interactions(session_id);
        CREATE INDEX IF NOT EXISTS idx_knowledge_interactions_user ON knowledge_interactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_knowledge_graph_source ON knowledge_graph_edges(source_entity_id);
        CREATE INDEX IF NOT EXISTS idx_knowledge_graph_target ON knowledge_graph_edges(target_entity_id);
        CREATE INDEX IF NOT EXISTS idx_repository_knowledge_type ON repository_knowledge(knowledge_type);
        CREATE INDEX IF NOT EXISTS idx_cross_platform_entity ON cross_platform_correlations(entity_name);
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
        
        logger.info("Enhanced knowledge database schema created")
    
    async def store_business_entity(self, entity: BusinessEntity) -> int:
        """Store or update business entity"""
        async with self.pool.acquire() as conn:
            # Try to insert, update if exists
            result = await conn.fetchrow("""
                INSERT INTO business_entities 
                (entity_type, entity_name, description, attributes, data_sources, confidence_score, embedding_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (entity_type, entity_name) 
                DO UPDATE SET 
                    description = EXCLUDED.description,
                    attributes = business_entities.attributes || EXCLUDED.attributes,
                    data_sources = array(SELECT DISTINCT unnest(business_entities.data_sources || EXCLUDED.data_sources)),
                    confidence_score = GREATEST(business_entities.confidence_score, EXCLUDED.confidence_score),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, entity.entity_type, entity.name, entity.description, 
                json.dumps(entity.attributes), entity.data_sources, 
                entity.confidence_score, entity.embedding_id)
            
            return result['id']
    
    async def store_knowledge_interaction(
        self, 
        session_id: str, 
        content: str, 
        extracted_knowledge: List[KnowledgeItem],
        entities_mentioned: List[str],
        user_id: str = None
    ) -> int:
        """Store knowledge interaction"""
        async with self.pool.acquire() as conn:
            # Calculate average confidence
            avg_confidence = sum(
                0.8 if item.confidence_level == ConfidenceLevel.HIGH else
                0.6 if item.confidence_level == ConfidenceLevel.MEDIUM else
                0.4 if item.confidence_level == ConfidenceLevel.LOW else 0.2
                for item in extracted_knowledge
            ) / len(extracted_knowledge) if extracted_knowledge else 0.5
            
            result = await conn.fetchrow("""
                INSERT INTO knowledge_interactions 
                (session_id, user_id, content, extracted_knowledge, entities_mentioned, confidence_score)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, session_id, user_id, content, 
                json.dumps([asdict(item) for item in extracted_knowledge]), 
                entities_mentioned, avg_confidence)
            
            return result['id']
    
    async def get_entity_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get relationships for an entity"""
        async with self.pool.acquire() as conn:
            # Get entity ID
            entity_result = await conn.fetchrow("""
                SELECT id FROM business_entities WHERE entity_name = $1
            """, entity_name)
            
            if not entity_result:
                return []
            
            entity_id = entity_result['id']
            
            # Get relationships
            relationships = await conn.fetch("""
                SELECT 
                    e.relationship_type,
                    e.strength,
                    e.evidence_count,
                    e.metadata,
                    be.entity_name as related_entity,
                    be.entity_type as related_entity_type
                FROM knowledge_graph_edges e
                JOIN business_entities be ON (
                    CASE 
                        WHEN e.source_entity_id = $1 THEN e.target_entity_id = be.id
                        ELSE e.source_entity_id = be.id
                    END
                )
                WHERE e.source_entity_id = $1 OR e.target_entity_id = $1
                ORDER BY e.strength DESC
            """, entity_id)
            
            return [dict(row) for row in relationships]

class ContinuousLearningOrchestrator:
    """Main orchestrator for continuous learning system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.entity_recognizer = PayReadyEntityRecognizer()
        self.knowledge_extractor = KnowledgeExtractor(config['openai_api_key'])
        self.database = EnhancedKnowledgeDatabase(config['database_url'])
        self.vector_client = QdrantClient(
            url=config['qdrant_url'], 
            api_key=config.get('qdrant_api_key')
        )
        
        # Initialize embedding client
        self.embedding_client = openai.OpenAI(api_key=config['openai_api_key'])
    
    async def initialize(self):
        """Initialize all components"""
        await self.database.initialize()
        await self.setup_vector_collections()
        logger.info("Continuous Learning Orchestrator initialized")
    
    async def setup_vector_collections(self):
        """Setup Qdrant collections for knowledge storage"""
        collections = [
            ("pay_ready_entities", 1536, "Business entities and their relationships"),
            ("knowledge_items", 1536, "Extracted knowledge items from conversations"),
            ("repository_insights", 1536, "Technical insights from repository analysis"),
            ("cross_platform_data", 1536, "Correlated data across multiple platforms")
        ]
        
        for collection_name, vector_size, description in collections:
            try:
                self.vector_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                logger.info(f"Created vector collection: {collection_name}")
            except Exception as e:
                if "already exists" not in str(e):
                    logger.error(f"Failed to create collection {collection_name}: {e}")
    
    async def process_user_interaction(
        self, 
        session_id: str, 
        user_message: str, 
        context: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Process user interaction for knowledge extraction"""
        
        try:
            # Extract business entities
            entities = await self.entity_recognizer.extract_entities(user_message)
            logger.info(f"Extracted {len(entities)} entities from interaction")
            
            # Extract structured knowledge
            knowledge_items = await self.knowledge_extractor.extract_knowledge(
                user_message, entities, context
            )
            logger.info(f"Extracted {len(knowledge_items)} knowledge items")
            
            # Store entities in database and vector store
            entity_ids = []
            for entity in entities:
                # Generate embedding for entity
                embedding = await self.generate_embedding(
                    f"{entity.name} {entity.description} {entity.entity_type}"
                )
                entity.embedding_id = f"entity_{hashlib.md5(entity.name.encode()).hexdigest()}"
                
                # Store in database
                entity_id = await self.database.store_business_entity(entity)
                entity_ids.append(entity_id)
                
                # Store in vector database
                await self.store_entity_vector(entity, embedding)
            
            # Store knowledge interaction
            interaction_id = await self.database.store_knowledge_interaction(
                session_id, user_message, knowledge_items, 
                [e.name for e in entities], user_id
            )
            
            # Store knowledge items in vector store
            for knowledge_item in knowledge_items:
                embedding = await self.generate_embedding(knowledge_item.content)
                await self.store_knowledge_vector(knowledge_item, embedding, interaction_id)
            
            return {
                "interaction_id": interaction_id,
                "entities_extracted": len(entities),
                "knowledge_items_extracted": len(knowledge_items),
                "entities": [{"name": e.name, "type": e.entity_type, "confidence": e.confidence_score} for e in entities],
                "knowledge_summary": [{"content": k.content[:100], "type": k.knowledge_type.value} for k in knowledge_items],
                "processing_status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to process user interaction: {e}")
            return {
                "interaction_id": None,
                "entities_extracted": 0,
                "knowledge_items_extracted": 0,
                "error": str(e),
                "processing_status": "failed"
            }
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            response = await self.embedding_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * 1536  # Return zero vector as fallback
    
    async def store_entity_vector(self, entity: BusinessEntity, embedding: List[float]):
        """Store entity vector in Qdrant"""
        try:
            self.vector_client.upsert(
                collection_name="pay_ready_entities",
                points=[
                    PointStruct(
                        id=entity.embedding_id,
                        vector=embedding,
                        payload={
                            "name": entity.name,
                            "type": entity.entity_type,
                            "description": entity.description,
                            "confidence": entity.confidence_score,
                            "data_sources": entity.data_sources,
                            "attributes": entity.attributes
                        }
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Failed to store entity vector: {e}")
    
    async def store_knowledge_vector(
        self, 
        knowledge_item: KnowledgeItem, 
        embedding: List[float], 
        interaction_id: int
    ):
        """Store knowledge item vector in Qdrant"""
        try:
            vector_id = f"knowledge_{interaction_id}_{hashlib.md5(knowledge_item.content.encode()).hexdigest()[:8]}"
            
            self.vector_client.upsert(
                collection_name="knowledge_items",
                points=[
                    PointStruct(
                        id=vector_id,
                        vector=embedding,
                        payload={
                            "content": knowledge_item.content,
                            "type": knowledge_item.knowledge_type.value,
                            "confidence": knowledge_item.confidence_level.value,
                            "entities_mentioned": knowledge_item.entities_mentioned,
                            "interaction_id": interaction_id,
                            "metadata": knowledge_item.metadata
                        }
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Failed to store knowledge vector: {e}")
    
    async def get_contextual_knowledge(
        self, 
        query: str, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """Retrieve contextual knowledge for a query"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Search entities
            entity_results = self.vector_client.search(
                collection_name="pay_ready_entities",
                query_vector=query_embedding,
                limit=limit
            )
            
            # Search knowledge items
            knowledge_results = self.vector_client.search(
                collection_name="knowledge_items",
                query_vector=query_embedding,
                limit=limit
            )
            
            return {
                "query": query,
                "relevant_entities": [
                    {
                        "name": result.payload["name"],
                        "type": result.payload["type"],
                        "description": result.payload["description"],
                        "relevance_score": result.score
                    }
                    for result in entity_results
                ],
                "relevant_knowledge": [
                    {
                        "content": result.payload["content"],
                        "type": result.payload["type"],
                        "confidence": result.payload["confidence"],
                        "relevance_score": result.score
                    }
                    for result in knowledge_results
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve contextual knowledge: {e}")
            return {"query": query, "relevant_entities": [], "relevant_knowledge": [], "error": str(e)}

# Example usage and testing
async def main():
    """Example usage of the continuous learning system"""
    
    config = {
        "openai_api_key": "your-openai-api-key",
        "database_url": "postgresql://user:password@localhost/sophia_intel",
        "qdrant_url": "http://localhost:6333",
        "qdrant_api_key": None
    }
    
    # Initialize the system
    orchestrator = ContinuousLearningOrchestrator(config)
    await orchestrator.initialize()
    
    # Example interaction
    result = await orchestrator.process_user_interaction(
        session_id="test_session_001",
        user_message="We need to improve our sales conversion rate from Salesforce leads. The current rate is 15% but we want to get to 25%. Can you analyze the Gong call data to identify what our top performers are doing differently?",
        context={"user_role": "sales_manager", "interaction_type": "business_analysis"},
        user_id="john_doe"
    )
    
    print("Processing Result:", json.dumps(result, indent=2))
    
    # Example knowledge retrieval
    knowledge = await orchestrator.get_contextual_knowledge(
        "sales conversion rate optimization strategies"
    )
    
    print("Contextual Knowledge:", json.dumps(knowledge, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

