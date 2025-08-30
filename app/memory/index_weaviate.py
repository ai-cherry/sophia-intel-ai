import weaviate
from weaviate import Client
from typing import List, Dict, Any, Optional
from app import settings

def get_client() -> Client:
    """Get Weaviate client instance."""
    auth_config = None
    if settings.WEAVIATE_API_KEY:
        auth_config = weaviate.auth.AuthApiKey(api_key=settings.WEAVIATE_API_KEY)
    
    return Client(
        url=settings.WEAVIATE_URL,
        auth_client_secret=auth_config
    )

def ensure_schema(client: Client):
    """Ensure the required classes exist in Weaviate schema."""
    
    code_class = {
        "class": settings.WEAVIATE_CLASS_CODE,
        "properties": [
            {"name": "content", "dataType": ["text"]},
            {"name": "filepath", "dataType": ["string"]},
            {"name": "language", "dataType": ["string"]},
            {"name": "start_line", "dataType": ["int"]},
            {"name": "end_line", "dataType": ["int"]}
        ]
    }
    
    doc_class = {
        "class": settings.WEAVIATE_CLASS_DOC,
        "properties": [
            {"name": "content", "dataType": ["text"]},
            {"name": "title", "dataType": ["string"]},
            {"name": "source", "dataType": ["string"]},
            {"name": "metadata", "dataType": ["text"]}
        ]
    }
    
    existing_classes = {c["class"] for c in client.schema.get()["classes"]}
    
    if settings.WEAVIATE_CLASS_CODE not in existing_classes:
        client.schema.create_class(code_class)
    
    if settings.WEAVIATE_CLASS_DOC not in existing_classes:
        client.schema.create_class(doc_class)

async def search_by_vector(
    vector: List[float], 
    class_name: str = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search Weaviate using a vector.
    
    Args:
        vector: Embedding vector to search with
        class_name: Weaviate class to search (defaults to CodeChunk)
        limit: Maximum number of results
    
    Returns:
        List of matching documents
    """
    client = get_client()
    class_name = class_name or settings.WEAVIATE_CLASS_CODE
    
    result = (
        client.query
        .get(class_name)
        .with_near_vector({"vector": vector})
        .with_limit(limit)
        .with_additional(["certainty", "id"])
        .do()
    )
    
    if "data" in result and "Get" in result["data"]:
        return result["data"]["Get"].get(class_name, [])
    return []