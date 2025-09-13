"""
Vector Search MCP Server
Integrates Weaviate, Redis, and PostgreSQL for intelligent codebase indexing
"""

import os
import asyncio
import json
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import structlog

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import weaviate
import redis.asyncio as redis
import psycopg2
from psycopg2.extras import RealDictCursor
import httpx

logger = structlog.get_logger(__name__)

app = FastAPI(title="Vector Search MCP Server")

# Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://localhost/sophia_intel")
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")

# Global clients
weaviate_client = None
redis_client = None
postgres_conn = None

class CodeFile(BaseModel):
    path: str
    content: str
    language: str
    size: int
    modified: datetime

class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None

class IndexRequest(BaseModel):
    path: str
    recursive: bool = True
    extensions: List[str] = [".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".json"]

@app.on_event("startup")
async def startup():
    """Initialize connections to vector databases and caches"""
    global weaviate_client, redis_client, postgres_conn
    
    try:
        # Initialize Weaviate
        weaviate_client = weaviate.Client(url=WEAVIATE_URL)
        
        # Create schema if it doesn't exist
        await ensure_weaviate_schema()
        
        # Initialize Redis
        redis_client = redis.from_url(REDIS_URL)
        await redis_client.ping()
        
        # Initialize PostgreSQL
        postgres_conn = psycopg2.connect(POSTGRES_URL, cursor_factory=RealDictCursor)
        await ensure_postgres_tables()
        
        logger.info("Vector search server initialized", 
                   weaviate=WEAVIATE_URL, 
                   redis=REDIS_URL,
                   postgres=POSTGRES_URL)
                   
    except Exception as e:
        logger.error("Failed to initialize vector search server", error=str(e))
        raise

async def ensure_weaviate_schema():
    """Ensure Weaviate schema exists for code files"""
    schema = {
        "class": "CodeFile",
        "description": "Source code files with semantic vectors",
        "vectorizer": "text2vec-openai" if OPENROUTER_API_KEY else "none",
        "properties": [
            {
                "name": "path",
                "dataType": ["string"],
                "description": "File path"
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "File content"
            },
            {
                "name": "language",
                "dataType": ["string"],
                "description": "Programming language"
            },
            {
                "name": "size",
                "dataType": ["int"],
                "description": "File size in bytes"
            },
            {
                "name": "modified",
                "dataType": ["date"],
                "description": "Last modified timestamp"
            },
            {
                "name": "summary",
                "dataType": ["text"],
                "description": "AI-generated summary"
            }
        ]
    }
    
    try:
        if not weaviate_client.schema.exists("CodeFile"):
            weaviate_client.schema.create_class(schema)
            logger.info("Created Weaviate schema for CodeFile")
    except Exception as e:
        logger.warning("Schema creation skipped", error=str(e))

async def ensure_postgres_tables():
    """Ensure PostgreSQL tables exist for metadata"""
    create_tables_sql = """
    CREATE EXTENSION IF NOT EXISTS vector;
    
    CREATE TABLE IF NOT EXISTS file_metadata (
        id SERIAL PRIMARY KEY,
        path VARCHAR(500) UNIQUE NOT NULL,
        language VARCHAR(50),
        size INTEGER,
        modified TIMESTAMP,
        hash VARCHAR(64),
        indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        embedding vector(1536)
    );
    
    CREATE TABLE IF NOT EXISTS search_sessions (
        id SERIAL PRIMARY KEY,
        query TEXT NOT NULL,
        results JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_file_path ON file_metadata(path);
    CREATE INDEX IF NOT EXISTS idx_file_language ON file_metadata(language);
    CREATE INDEX IF NOT EXISTS idx_file_embedding ON file_metadata USING ivfflat (embedding vector_cosine_ops);
    """
    
    try:
        with postgres_conn.cursor() as cursor:
            cursor.execute(create_tables_sql)
            postgres_conn.commit()
            logger.info("PostgreSQL tables ensured")
    except Exception as e:
        logger.warning("Table creation skipped", error=str(e))

def detect_language(file_path: str) -> str:
    """Detect programming language from file extension"""
    ext = Path(file_path).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'react',
        '.tsx': 'react-typescript',
        '.html': 'html',
        '.css': 'css',
        '.md': 'markdown',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.sql': 'sql',
        '.sh': 'bash',
        '.dockerfile': 'dockerfile'
    }
    return language_map.get(ext, 'text')

async def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using Portkey (OpenAI provider)"""
    if not PORTKEY_API_KEY:
        return None
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.portkey.ai/v1/embeddings",
                headers={
                    "x-portkey-api-key": PORTKEY_API_KEY,
                    "x-portkey-provider": "openai",
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.getenv("EMBED_MODEL", "text-embedding-3-small"),
                    "input": text[:8000]  # Limit input size
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data["data"][0]["embedding"]
    except Exception as e:
        logger.warning("Embedding generation failed", error=str(e))
    
    return None

async def summarize_code(content: str, language: str) -> str:
    """Generate AI summary of code file via Portkey"""
    if not PORTKEY_API_KEY or len(content) < 100:
        return f"A {language} file with {len(content)} characters"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.portkey.ai/v1/chat/completions",
                headers={
                    "x-portkey-api-key": PORTKEY_API_KEY,
                    "x-portkey-provider": os.getenv("SUMMARY_PROVIDER", "openai"),
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.getenv("SUMMARY_MODEL", "gpt-4o-mini"),
                    "messages": [
                        {
                            "role": "system",
                            "content": "Summarize this code file in 1-2 sentences. Focus on its purpose and key functionality."
                        },
                        {
                            "role": "user",
                            "content": f"Language: {language}\n\nCode:\n{content[:2000]}"
                        }
                    ],
                    "max_tokens": 100,
                    "temperature": 0.3
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("Code summarization failed", error=str(e))
    
    return f"A {language} file with {len(content)} characters"

@app.post("/index")
async def index_codebase(request: IndexRequest):
    """Index a codebase directory for vector search"""
    path = Path(request.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    
    indexed_files = []
    skipped_files = []
    
    try:
        # Get all files to index
        files_to_index = []
        if path.is_file():
            files_to_index = [path]
        else:
            for ext in request.extensions:
                pattern = f"**/*{ext}" if request.recursive else f"*{ext}"
                files_to_index.extend(path.glob(pattern))
        
        logger.info("Starting codebase indexing", total_files=len(files_to_index))
        
        for file_path in files_to_index:
            try:
                # Read file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Skip empty files or very large files
                if not content.strip() or len(content) > 50000:
                    skipped_files.append(str(file_path))
                    continue
                
                # Get file metadata
                stat = file_path.stat()
                file_hash = hashlib.sha256(content.encode()).hexdigest()
                language = detect_language(str(file_path))
                modified = datetime.fromtimestamp(stat.st_mtime)
                
                # Check if file already indexed and unchanged
                cache_key = f"file_hash:{file_path}"
                cached_hash = await redis_client.get(cache_key)
                if cached_hash and cached_hash.decode() == file_hash:
                    continue
                
                # Generate embedding and summary
                embedding = await generate_embedding(content)
                summary = await summarize_code(content, language)
                
                # Store in Weaviate
                weaviate_client.data_object.create(
                    data_object={
                        "path": str(file_path),
                        "content": content,
                        "language": language,
                        "size": len(content),
                        "modified": modified.isoformat(),
                        "summary": summary
                    },
                    class_name="CodeFile"
                )
                
                # Store in PostgreSQL
                with postgres_conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO file_metadata (path, language, size, modified, hash, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (path) DO UPDATE SET
                            language = EXCLUDED.language,
                            size = EXCLUDED.size,
                            modified = EXCLUDED.modified,
                            hash = EXCLUDED.hash,
                            embedding = EXCLUDED.embedding,
                            indexed_at = CURRENT_TIMESTAMP
                    """, (
                        str(file_path),
                        language,
                        len(content),
                        modified,
                        file_hash,
                        embedding
                    ))
                    postgres_conn.commit()
                
                # Cache file hash
                await redis_client.setex(cache_key, 3600, file_hash)
                
                indexed_files.append({
                    "path": str(file_path),
                    "language": language,
                    "size": len(content),
                    "summary": summary
                })
                
            except Exception as e:
                logger.warning("Failed to index file", file=str(file_path), error=str(e))
                skipped_files.append(str(file_path))
        
        logger.info("Codebase indexing completed", 
                   indexed=len(indexed_files), 
                   skipped=len(skipped_files))
        
        return {
            "status": "completed",
            "indexed_files": len(indexed_files),
            "skipped_files": len(skipped_files),
            "files": indexed_files[:10]  # Return first 10 for preview
        }
        
    except Exception as e:
        logger.error("Codebase indexing failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_code(query: SearchQuery):
    """Search codebase using vector similarity"""
    try:
        # Cache key for search results
        cache_key = f"search:{hashlib.md5(query.query.encode()).hexdigest()}"
        cached_result = await redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        # Search in Weaviate
        result = weaviate_client.query.get("CodeFile", [
            "path", "content", "language", "size", "summary"
        ]).with_near_text({
            "concepts": [query.query]
        }).with_limit(query.limit).do()
        
        search_results = []
        if "data" in result and "Get" in result["data"] and "CodeFile" in result["data"]["Get"]:
            for item in result["data"]["Get"]["CodeFile"]:
                search_results.append({
                    "path": item["path"],
                    "language": item["language"],
                    "size": item["size"],
                    "summary": item["summary"],
                    "content_preview": item["content"][:200] + "..." if len(item["content"]) > 200 else item["content"]
                })
        
        # Store search session in PostgreSQL
        with postgres_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO search_sessions (query, results)
                VALUES (%s, %s)
            """, (query.query, json.dumps(search_results)))
            postgres_conn.commit()
        
        response = {
            "query": query.query,
            "total_results": len(search_results),
            "results": search_results
        }
        
        # Cache results for 5 minutes
        await redis_client.setex(cache_key, 300, json.dumps(response))
        
        return response
        
    except Exception as e:
        logger.error("Search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get indexing and search statistics"""
    try:
        # Get file count from PostgreSQL
        with postgres_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*), AVG(size) FROM file_metadata")
            file_count, avg_size = cursor.fetchone()
            
            cursor.execute("""
                SELECT language, COUNT(*) as count 
                FROM file_metadata 
                GROUP BY language 
                ORDER BY count DESC
            """)
            language_stats = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) FROM search_sessions WHERE created_at > NOW() - INTERVAL '24 hours'")
            searches_today = cursor.fetchone()[0]
        
        # Get cache stats from Redis
        cache_info = await redis_client.info()
        
        return {
            "files": {
                "total": file_count or 0,
                "average_size": int(avg_size or 0),
                "by_language": dict(language_stats) if language_stats else {}
            },
            "searches": {
                "today": searches_today or 0
            },
            "cache": {
                "memory_usage": cache_info.get("used_memory_human", "0B"),
                "hits": cache_info.get("keyspace_hits", 0),
                "misses": cache_info.get("keyspace_misses", 0)
            }
        }
        
    except Exception as e:
        logger.error("Stats retrieval failed", error=str(e))
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test all connections
        weaviate_ready = weaviate_client.is_ready()
        await redis_client.ping()
        
        with postgres_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "services": {
                "weaviate": "ready" if weaviate_ready else "not_ready",
                "redis": "ready",
                "postgres": "ready"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
