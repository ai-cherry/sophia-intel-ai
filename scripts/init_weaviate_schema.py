#!/usr/bin/env python3
"""
Initialize Weaviate schema for BusinessDocument if not present.

Fields:
  - content: text
  - source: string
  - entityId: string
  - timestamp: date
  - metadata: object
Vectorizer: text2vec-openai (config depends on your Weaviate setup)
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    try:
        import weaviate

        # Support both cloud and local configurations
        endpoint = os.getenv("WEAVIATE_ENDPOINT") or os.getenv("WEAVIATE_URL", "http://localhost:8080")
        api_key = os.getenv("WEAVIATE_ADMIN_API_KEY") or os.getenv("WEAVIATE_API_KEY")
        
        print(f"Connecting to Weaviate at: {endpoint}")
        print(f"Using API key: {'Yes' if api_key else 'No (anonymous)'}")
        
        # Use v3 client for compatibility
        if api_key:
            auth_config = weaviate.auth.AuthApiKey(api_key=api_key)
            client = weaviate.Client(url=endpoint, auth_client_secret=auth_config)
        else:
            client = weaviate.Client(url=endpoint)
        
        # Check if schema exists
        schema = client.schema.get()
        existing_classes = [cls['class'] for cls in schema.get('classes', [])]
        
        if "BusinessDocument" in existing_classes:
            print("BusinessDocument schema already exists")
            return 0
        
        # Create BusinessDocument class using v3 API
        business_document_class = {
            "class": "BusinessDocument",
            "description": "Business documents and transcripts indexed for Sophia RAG",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "text-embedding-3-small",
                    "dimensions": 1536,
                    "type": "text"
                }
            },
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Main document content",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "source", 
                    "dataType": ["text"],
                    "description": "Source system (slack, gong, asana, etc.)",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "entityId",
                    "dataType": ["text"], 
                    "description": "Unique ID from source system",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "timestamp",
                    "dataType": ["date"],
                    "description": "Document timestamp"
                },
                {
                    "name": "metadata",
                    "dataType": ["text"],
                    "description": "Additional metadata as JSON string",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "contentHash",
                    "dataType": ["text"],
                    "description": "SHA256 hash for deduplication",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True,
                            "vectorizePropertyName": False
                        }
                    }
                }
            ]
        }
        
        client.schema.create_class(business_document_class)
        print("BusinessDocument schema created successfully")
        
        # Verify creation
        schema = client.schema.get()
        classes = [cls['class'] for cls in schema.get('classes', [])]
        if "BusinessDocument" in classes:
            print("✅ Schema verification successful")
            return 0
        else:
            print("❌ Schema verification failed")
            return 1
    except Exception as e:
        print(f"Schema init failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

