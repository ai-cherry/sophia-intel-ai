#!/usr/bin/env python3
"""
Setup Vector Collections for Primary Mentor Initiative
Creates and configures Qdrant collections for the knowledge architecture
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, CreateCollection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QdrantCollectionSetup:
    def __init__(self, qdrant_url: str = "http://localhost:6333", api_key: Optional[str] = None):
        """Initialize Qdrant client"""
        self.client = QdrantClient(url=qdrant_url, api_key=api_key)
        logger.info(f"Connected to Qdrant at {qdrant_url}")
    
    def create_collection_if_not_exists(self, collection_name: str, vector_size: int = 1536, distance: Distance = Distance.COSINE) -> bool:
        """Create a collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            existing_names = [col.name for col in collections.collections]
            
            if collection_name in existing_names:
                logger.info(f"Collection '{collection_name}' already exists")
                return True
            
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance)
            )
            logger.info(f"Created collection '{collection_name}' with vector size {vector_size}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {str(e)}")
            return False
    
    def setup_all_collections(self) -> Dict[str, bool]:
        """Setup all required collections for Primary Mentor Initiative"""
        collections_config = {
            # Foundational knowledge - highest priority
            "sophia_foundational_knowledge": {
                "description": "Canonical principles and core truths about SOPHIA and Pay Ready",
                "vector_size": 1536,
                "distance": Distance.COSINE
            },
            
            # Document collections
            "foundational_docs": {
                "description": "Core company documents, policies, and foundational materials",
                "vector_size": 1536,
                "distance": Distance.COSINE
            },
            
            "code_repo": {
                "description": "Code repository contents, documentation, and technical knowledge",
                "vector_size": 1536,
                "distance": Distance.COSINE
            },
            
            "external_sources": {
                "description": "External web sources, research papers, and third-party documentation",
                "vector_size": 1536,
                "distance": Distance.COSINE
            },
            
            # Interaction history
            "chat_history": {
                "description": "CEO chat transcripts and interaction history for pattern analysis",
                "vector_size": 1536,
                "distance": Distance.COSINE
            }
        }
        
        results = {}
        logger.info("Setting up Qdrant collections for Primary Mentor Initiative...")
        
        for collection_name, config in collections_config.items():
            logger.info(f"Setting up collection: {collection_name}")
            logger.info(f"Description: {config['description']}")
            
            success = self.create_collection_if_not_exists(
                collection_name=collection_name,
                vector_size=config["vector_size"],
                distance=config["distance"]
            )
            results[collection_name] = success
        
        return results
    
    def verify_collections(self) -> Dict[str, Dict]:
        """Verify all collections are properly created"""
        try:
            collections = self.client.get_collections()
            collection_info = {}
            
            for collection in collections.collections:
                info = self.client.get_collection(collection.name)
                collection_info[collection.name] = {
                    "vectors_count": info.vectors_count,
                    "indexed_vectors_count": info.indexed_vectors_count,
                    "points_count": info.points_count,
                    "status": info.status
                }
            
            return collection_info
            
        except Exception as e:
            logger.error(f"Failed to verify collections: {str(e)}")
            return {}
    
    def create_sample_embeddings(self):
        """Create sample embeddings for testing"""
        import openai
        
        # Sample canonical principles for embedding
        sample_principles = [
            {
                "id": "principle_1",
                "text": "Always prioritize accuracy and truthfulness over speed of response",
                "entity_type": "AI_ASSISTANT",
                "entity_name": "SOPHIA",
                "importance": 10
            },
            {
                "id": "principle_2", 
                "text": "Maintain context awareness throughout conversations",
                "entity_type": "AI_ASSISTANT",
                "entity_name": "SOPHIA",
                "importance": 9
            },
            {
                "id": "principle_3",
                "text": "Security and data privacy are non-negotiable",
                "entity_type": "ORGANIZATION",
                "entity_name": "Pay Ready",
                "importance": 10
            }
        ]
        
        try:
            # Note: In production, this would use the actual OpenAI client
            # For now, we'll create dummy vectors
            logger.info("Creating sample embeddings in sophia_foundational_knowledge...")
            
            for principle in sample_principles:
                # Create a dummy embedding vector (1536 dimensions)
                dummy_vector = [0.1] * 1536
                
                self.client.upsert(
                    collection_name="sophia_foundational_knowledge",
                    points=[{
                        "id": principle["id"],
                        "vector": dummy_vector,
                        "payload": {
                            "text": principle["text"],
                            "entity_type": principle["entity_type"],
                            "entity_name": principle["entity_name"],
                            "importance": principle["importance"],
                            "source": "system_initialization",
                            "created_at": "2025-08-15T20:00:00Z"
                        }
                    }]
                )
            
            logger.info(f"Created {len(sample_principles)} sample embeddings")
            
        except Exception as e:
            logger.error(f"Failed to create sample embeddings: {str(e)}")

def main():
    """Main execution function"""
    # Get Qdrant connection details from environment or use defaults
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    logger.info("🧭 Primary Mentor Initiative - Vector Store Setup")
    logger.info(f"Qdrant URL: {qdrant_url}")
    
    try:
        # Initialize setup
        setup = QdrantCollectionSetup(qdrant_url, qdrant_api_key)
        
        # Create collections
        results = setup.setup_all_collections()
        
        # Verify collections
        collection_info = setup.verify_collections()
        
        # Create sample embeddings
        setup.create_sample_embeddings()
        
        # Print results
        print("\n" + "="*60)
        print("QDRANT COLLECTIONS SETUP RESULTS")
        print("="*60)
        
        for collection_name, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{status}: {collection_name}")
            
            if collection_name in collection_info:
                info = collection_info[collection_name]
                print(f"   Points: {info['points_count']}, Status: {info['status']}")
        
        print("\n" + "="*60)
        print("COLLECTION VERIFICATION")
        print("="*60)
        
        for name, info in collection_info.items():
            print(f"📊 {name}:")
            print(f"   Vectors: {info['vectors_count']}")
            print(f"   Points: {info['points_count']}")
            print(f"   Status: {info['status']}")
        
        # Check if all collections were created successfully
        all_success = all(results.values())
        if all_success:
            print("\n🎉 All collections created successfully!")
            print("Primary Mentor vector store is ready for use.")
            return 0
        else:
            print("\n⚠️  Some collections failed to create.")
            return 1
            
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

