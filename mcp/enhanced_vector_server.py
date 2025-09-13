"""
DEPRECATED: Use canonical vector MCP at mcp/vector/server.py (port 8085).

Enhanced Vector Search with Redis Caching and Hybrid Search
High-value improvements without overcomplication
"""

import os
import asyncio
import json
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import structlog

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as redis

logger = structlog.get_logger(__name__)
app = FastAPI(title="Enhanced Vector Search MCP")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8005", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DB_PATH = "/Users/lynnmusil/sophia-intel-ai/data/vector_search.db"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Global clients
redis_client = None

class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    file_types: Optional[List[str]] = None
    date_range: Optional[List[str]] = None  # ["2025-09-01", "2025-09-10"]
    min_size: Optional[int] = None
    max_size: Optional[int] = None

class CachedSearchResult(BaseModel):
    query: str
    results: List[dict]
    cached_at: str
    cache_hit: bool = True

@app.on_event("startup")
async def startup():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL)
        await redis_client.ping()
        logger.info("Enhanced vector search server initialized", redis_url=REDIS_URL, db_path=DB_PATH)
    except Exception as e:
        logger.warning("Redis not available, caching disabled", error=str(e))
        redis_client = None

def detect_language(file_path: str) -> str:
    """Detect programming language from file extension"""
    ext = Path(file_path).suffix.lower()
    language_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.jsx': 'react', '.tsx': 'react-typescript', '.html': 'html',
        '.css': 'css', '.md': 'markdown', '.json': 'json',
        '.yaml': 'yaml', '.yml': 'yaml', '.sql': 'sql', '.sh': 'bash'
    }
    return language_map.get(ext, 'text')

def extract_keywords(content: str, language: str) -> List[str]:
    """Extract important keywords from code content"""
    keywords = set()
    
    # Language-specific keyword extraction
    if language == 'python':
        python_keywords = ['def ', 'class ', 'import ', 'from ', 'async ', 'await ']
        for keyword in python_keywords:
            if keyword in content:
                lines = [line.strip() for line in content.split('\n') if keyword in line]
                for line in lines[:5]:
                    keywords.update(word.strip('():,') for word in line.split())
    
    elif language in ['javascript', 'typescript']:
        js_keywords = ['function ', 'const ', 'let ', 'class ', 'export ', 'import ']
        for keyword in js_keywords:
            if keyword in content:
                lines = [line.strip() for line in content.split('\n') if keyword in line]
                for line in lines[:5]:
                    keywords.update(word.strip('():,{}') for word in line.split())
    
    # Common keywords for all languages
    common_keywords = ['TODO', 'FIXME', 'BUG', 'NOTE', 'API', 'database', 'config', 'auth', 'login']
    for keyword in common_keywords:
        if keyword.lower() in content.lower():
            keywords.add(keyword)
    
    return [kw for kw in keywords if len(kw) > 2][:20]

def enhanced_search_score(query: str, content: str, keywords: List[str], filename: str) -> float:
    """Enhanced search scoring with multiple factors"""
    score = 0.0
    query_lower = query.lower()
    content_lower = content.lower()
    filename_lower = filename.lower()
    
    # Filename match (highest priority)
    if query_lower in filename_lower:
        score += 50.0
    
    # Exact phrase match in content
    if query_lower in content_lower:
        score += 20.0
        # Bonus for multiple occurrences
        score += content_lower.count(query_lower) * 5.0
    
    # Word matches with position weighting
    query_words = query_lower.split()
    content_words = content_lower.split()
    
    for i, word in enumerate(query_words):
        if word in content_words:
            # Earlier words in query are more important
            weight = len(query_words) - i
            score += 3.0 * weight
            
        # Partial matches
        for content_word in content_words:
            if len(word) > 3 and (word in content_word or content_word in word):
                score += 1.0
    
    # Keyword matches (domain-specific terms)
    for keyword in keywords:
        if keyword.lower() in query_lower:
            score += 8.0
    
    # File size penalty for very large files (they're often less relevant)
    if len(content) > 10000:
        score *= 0.9
    
    return score

async def get_search_cache_key(query: str, filters: dict) -> str:
    """Generate cache key for search query with filters"""
    cache_data = {"query": query, "filters": filters}
    cache_string = json.dumps(cache_data, sort_keys=True)
    return f"search:{hashlib.md5(cache_string.encode()).hexdigest()}"

async def get_cached_search(cache_key: str) -> Optional[dict]:
    """Retrieve cached search results"""
    if not redis_client:
        return None
    
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            result = json.loads(cached)
            result["cache_hit"] = True
            return result
    except Exception as e:
        logger.warning("Cache retrieval failed", error=str(e))
    
    return None

async def cache_search_result(cache_key: str, result: dict, ttl: int = 3600):
    """Cache search results with TTL"""
    if not redis_client:
        return
    
    try:
        cache_data = {
            **result,
            "cached_at": datetime.now().isoformat(),
            "cache_hit": False
        }
        await redis_client.setex(cache_key, ttl, json.dumps(cache_data))
    except Exception as e:
        logger.warning("Cache storage failed", error=str(e))

def build_sql_filters(query: SearchQuery) -> tuple[str, list]:
    """Build SQL WHERE clause and parameters from search filters"""
    where_clauses = []
    params = []
    
    # Base content search
    where_clauses.append("(content LIKE ? OR filename LIKE ? OR summary LIKE ?)")
    search_term = f"%{query.query}%"
    params.extend([search_term, search_term, search_term])
    
    # File type filter
    if query.file_types:
        placeholders = ','.join('?' * len(query.file_types))
        where_clauses.append(f"language IN ({placeholders})")
        params.extend(query.file_types)
    
    # Date range filter
    if query.date_range and len(query.date_range) == 2:
        where_clauses.append("date(modified) BETWEEN date(?) AND date(?)")
        params.extend(query.date_range)
    
    # Size filters
    if query.min_size:
        where_clauses.append("size >= ?")
        params.append(query.min_size)
    
    if query.max_size:
        where_clauses.append("size <= ?")
        params.append(query.max_size)
    
    where_sql = " AND ".join(where_clauses)
    return where_sql, params

@app.post("/search")
async def enhanced_search(query: SearchQuery):
    """Enhanced search with caching and hybrid filtering"""
    # Check cache first
    filters = {
        "file_types": query.file_types,
        "date_range": query.date_range,
        "min_size": query.min_size,
        "max_size": query.max_size
    }
    
    cache_key = await get_search_cache_key(query.query, filters)
    cached_result = await get_cached_search(cache_key)
    
    if cached_result:
        logger.info("Cache hit for search", query=query.query)
        return cached_result
    
    # Perform fresh search
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Build hybrid SQL query
        where_sql, params = build_sql_filters(query)
        
        sql = f"""
            SELECT path, filename, language, size, content, summary, modified
            FROM indexed_files
            WHERE {where_sql}
            ORDER BY size DESC
            LIMIT ?
        """
        params.append(query.limit * 3)  # Get more for better ranking
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        # Enhanced scoring and ranking
        scored_results = []
        for row in results:
            path, filename, language, size, content, summary, modified = row
            keywords = extract_keywords(content, language)
            score = enhanced_search_score(query.query, content + " " + summary, keywords, filename)
            
            if score > 0:  # Only include relevant results
                scored_results.append({
                    "path": path,
                    "filename": filename,
                    "language": language,
                    "size": size,
                    "summary": summary,
                    "score": round(score, 2),
                    "preview": content[:300] + "..." if len(content) > 300 else content,
                    "modified": modified,
                    "keywords": keywords[:5]
                })
        
        # Sort by score and limit results
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        final_results = scored_results[:query.limit]
        
        # Log search
        cursor.execute("""
            INSERT INTO search_history (query, results_count)
            VALUES (?, ?)
        """, (query.query, len(final_results)))
        conn.commit()
        
        result = {
            "query": query.query,
            "total_results": len(final_results),
            "results": final_results,
            "filters_applied": filters,
            "cache_hit": False
        }
        
        # Cache the result
        await cache_search_result(cache_key, result)
        
        logger.info("Fresh search completed", query=query.query, results=len(final_results))
        return result
        
    finally:
        conn.close()

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    if not redis_client:
        return {"cache_enabled": False}
    
    try:
        # Get Redis info
        info = await redis_client.info()
        
        # Count search cache keys
        search_keys = await redis_client.keys("search:*")
        
        return {
            "cache_enabled": True,
            "total_keys": len(search_keys),
            "memory_usage": info.get("used_memory_human", "0B"),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": round(info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 2)
        }
    except Exception as e:
        return {"cache_enabled": False, "error": str(e)}

@app.delete("/cache/clear")
async def clear_cache():
    """Clear search cache"""
    if not redis_client:
        return {"cache_enabled": False}
    
    try:
        search_keys = await redis_client.keys("search:*")
        if search_keys:
            await redis_client.delete(*search_keys)
        
        return {"cleared_keys": len(search_keys)}
    except Exception as e:
        return {"error": str(e)}

class IndexRequest(BaseModel):
    path: str
    recursive: bool = True
    extensions: List[str] = [".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".json"]

def init_database():
    """Initialize SQLite database for file indexing"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indexed_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            language TEXT NOT NULL,
            size INTEGER NOT NULL,
            content TEXT NOT NULL,
            summary TEXT,
            hash TEXT NOT NULL,
            modified TIMESTAMP NOT NULL,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            results_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create search indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_filename ON indexed_files(filename)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_language ON indexed_files(language)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_content ON indexed_files(content)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_modified ON indexed_files(modified)")
    
    conn.commit()
    conn.close()

@app.post("/index")
async def index_codebase(request: IndexRequest):
    """Enhanced indexing with better performance"""
    # Initialize database if needed
    init_database()
    
    path = Path(request.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
        
        logger.info("Starting enhanced indexing", total_files=len(files_to_index))
        
        # Clear cache when re-indexing
        if redis_client:
            try:
                search_keys = await redis_client.keys("search:*")
                if search_keys:
                    await redis_client.delete(*search_keys)
                    logger.info("Cleared search cache for re-indexing")
            except:
                pass
        
        for file_path in files_to_index:
            try:
                # Read file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Skip empty files or very large files
                if not content.strip() or len(content) > 100000:
                    skipped_files.append(str(file_path))
                    continue
                
                # Get file metadata
                stat = file_path.stat()
                file_hash = hashlib.sha256(content.encode()).hexdigest()
                language = detect_language(str(file_path))
                modified = datetime.fromtimestamp(stat.st_mtime)
                filename = file_path.name
                
                # Extract keywords
                keywords = extract_keywords(content, language)
                summary = f"{language} file with {len(content)} chars, keywords: {', '.join(keywords[:5])}"
                
                # Store in database
                cursor.execute("""
                    INSERT OR REPLACE INTO indexed_files 
                    (path, filename, language, size, content, summary, hash, modified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(file_path),
                    filename,
                    language,
                    len(content),
                    content,
                    summary,
                    file_hash,
                    modified
                ))
                
                indexed_files.append({
                    "path": str(file_path),
                    "filename": filename,
                    "language": language,
                    "size": len(content),
                    "summary": summary
                })
                
            except Exception as e:
                logger.warning("Failed to index file", file=str(file_path), error=str(e))
                skipped_files.append(str(file_path))
        
        conn.commit()
        logger.info("Enhanced indexing completed", indexed=len(indexed_files), skipped=len(skipped_files))
        
        return {
            "status": "completed",
            "indexed_files": len(indexed_files),
            "skipped_files": len(skipped_files),
            "sample_files": indexed_files[:5],
            "cache_cleared": redis_client is not None
        }
        
    finally:
        conn.close()

@app.get("/stats")
async def get_stats():
    """Enhanced stats with cache information"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get file stats
        cursor.execute("SELECT COUNT(*), AVG(size) FROM indexed_files")
        file_count, avg_size = cursor.fetchone()
        
        # Get language breakdown
        cursor.execute("""
            SELECT language, COUNT(*) as count 
            FROM indexed_files 
            GROUP BY language 
            ORDER BY count DESC
        """)
        language_stats = dict(cursor.fetchall())
        
        # Get recent searches
        cursor.execute("""
            SELECT COUNT(*) FROM search_history 
            WHERE created_at > datetime('now', '-24 hours')
        """)
        searches_today = cursor.fetchone()[0]
        
        # Get cache stats
        cache_stats = await get_cache_stats()
        
        return {
            "files": {
                "total": file_count or 0,
                "average_size": int(avg_size or 0),
                "by_language": language_stats
            },
            "searches": {
                "today": searches_today or 0
            },
            "cache": cache_stats,
            "database": {
                "path": DB_PATH,
                "size_mb": round(Path(DB_PATH).stat().st_size / 1024 / 1024, 2) if Path(DB_PATH).exists() else 0
            }
        }
        
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    """Enhanced health check with cache status"""
    try:
        # Test database connection
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM indexed_files")
        file_count = cursor.fetchone()[0]
        conn.close()
        
        # Test Redis connection
        cache_healthy = False
        if redis_client:
            try:
                await redis_client.ping()
                cache_healthy = True
            except:
                pass
        
        return {
            "status": "healthy",
            "indexed_files": file_count,
            "database": "ready",
            "cache": "ready" if cache_healthy else "disabled",
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
    uvicorn.run(app, host="0.0.0.0", port=8086)
