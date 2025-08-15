#!/usr/bin/env python3
"""
Qdrant connectivity smoke test with working credentials
"""
import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import numpy as np

def test_qdrant_connection():
    """Test Qdrant connection and basic operations"""
    
    # Working credentials
    api_key = os.getenv('QDRANT_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzY1NTkxNjEzfQ.a4uBhUimAhpzdGLLOmSwHwGWF4rAQynEFZG8A9pDHkQ')
    url = os.getenv('QDRANT_URL', 'https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io:6333')
    
    try:
        client = QdrantClient(url=url, api_key=api_key)
        
        # Test connection
        collections = client.get_collections()
        print(f"✅ Qdrant connection successful!")
        print(f"Collections: {[c.name for c in collections.collections]}")
        
        # Test vector operations
        test_collection = 'sophia_test_smoke'
        
        # Create test collection if not exists
        try:
            client.create_collection(
                collection_name=test_collection,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"✅ Created test collection: {test_collection}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"✅ Test collection already exists: {test_collection}")
            else:
                raise e
        
        # Test vector operations with proper UUID
        test_vector = np.random.rand(384).tolist()
        point_id = str(uuid.uuid4())
        
        # Insert
        client.upsert(
            collection_name=test_collection,
            points=[{
                'id': point_id,
                'vector': test_vector,
                'payload': {'text': 'Smoke test vector', 'timestamp': '2025-01-14'}
            }]
        )
        print("✅ Vector insert successful!")
        
        # Search
        search_results = client.query_points(
            collection_name=test_collection,
            query=test_vector,
            limit=1
        )
        print(f"✅ Vector search successful! Found {len(search_results.points)} results")
        
        # Collection info
        collection_info = client.get_collection(test_collection)
        print(f"✅ Collection info: {collection_info.points_count} points")
        
        return True
        
    except Exception as e:
        print(f"❌ Qdrant test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_qdrant_connection()
    exit(0 if success else 1)
