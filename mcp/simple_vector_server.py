"""
Simplified Vector Search MCP Server
Works with existing infrastructure without external dependencies
"""

import os
import asyncio
import json
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import sqlite3
import structlog

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = structlog.get_logger(__name__)
app = FastAPI(title="Simple Vector Search MCP")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8005", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use SQLite for simplicity - no external dependencies
DB_PATH = "/Users/lynnmusil/sophia-intel-ai/data/vector_search.db"

class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    file_types: Optional[List[str]] = None

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
    
    conn.commit()
    conn.close()

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
        '.sh': 'bash'
    }
    return language_map.get(ext, 'text')

def extract_keywords(content: str, language: str) -> List[str]:
    """Extract important keywords from code content"""
    keywords = set()
    
    # Basic keyword extraction based on language
    if language == 'python':
        python_keywords = ['def ', 'class ', 'import ', 'from ', 'async ', 'await ']
        for keyword in python_keywords:
            if keyword in content:
                # Extract function/class names
                lines = [line.strip() for line in content.split('\n') if keyword in line]
                keywords.update(line.split() for line in lines[:5])  # Top 5 matches
    
    elif language in ['javascript', 'typescript']:
        js_keywords = ['function ', 'const ', 'let ', 'class ', 'export ', 'import ']
        for keyword in js_keywords:
            if keyword in content:
                lines = [line.strip() for line in content.split('\n') if keyword in line]
                keywords.update(line.split() for line in lines[:5])
    
    # General keywords for all languages
    common_keywords = ['TODO', 'FIXME', 'BUG', 'NOTE', 'API', 'database', 'config']
    for keyword in common_keywords:
        if keyword.lower() in content.lower():
            keywords.add(keyword)
    
    # Flatten and clean keywords
    flat_keywords = []
    for item in keywords:
        if isinstance(item, list):
            flat_keywords.extend(item)
        else:
            flat_keywords.append(item)
    
    # Return cleaned keywords
    return [kw.strip('(){}[],:;') for kw in flat_keywords if len(kw.strip('(){}[],:;')) > 2][:20]

def simple_search(query: str, content: str, keywords: List[str]) -> float:
    """Simple text-based search scoring"""
    score = 0.0
    query_lower = query.lower()
    content_lower = content.lower()
    
    # Exact phrase match
    if query_lower in content_lower:
        score += 10.0
    
    # Word matches
    query_words = query_lower.split()
    content_words = content_lower.split()
    
    for word in query_words:
        if word in content_words:
            score += 2.0
        # Partial matches
        for content_word in content_words:
            if word in content_word or content_word in word:
                score += 0.5
    
    # Keyword matches
    for keyword in keywords:
        if keyword.lower() in query_lower:
            score += 5.0
    
    return score

@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    init_database()
    logger.info("Simple vector search server initialized", db_path=DB_PATH)

@app.post("/index")
async def index_codebase(request: IndexRequest):
    """Index a codebase directory"""
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
        
        logger.info("Starting indexing", total_files=len(files_to_index))
        
        for file_path in files_to_index:
            try:
                # Read file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Skip empty or very large files
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
        logger.info("Indexing completed", indexed=len(indexed_files), skipped=len(skipped_files))
        
        return {
            "status": "completed",
            "indexed_files": len(indexed_files),
            "skipped_files": len(skipped_files),
            "sample_files": indexed_files[:5]
        }
        
    finally:
        conn.close()

@app.post("/search")
async def search_code(query: SearchQuery):
    """Search indexed code files"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Basic SQL search with scoring
        sql = """
            SELECT path, filename, language, size, content, summary
            FROM indexed_files
            WHERE content LIKE ? OR filename LIKE ? OR summary LIKE ?
        """
        
        params = [f"%{query.query}%"] * 3
        
        if query.file_types:
            placeholders = ','.join('?' * len(query.file_types))
            sql += f" AND language IN ({placeholders})"
            params.extend(query.file_types)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        # Score and rank results
        scored_results = []
        for row in results:
            path, filename, language, size, content, summary = row
            keywords = extract_keywords(content, language)
            score = simple_search(query.query, content + " " + summary, keywords)
            
            scored_results.append({
                "path": path,
                "filename": filename,
                "language": language,
                "size": size,
                "summary": summary,
                "score": score,
                "preview": content[:300] + "..." if len(content) > 300 else content
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
        
        return {
            "query": query.query,
            "total_results": len(final_results),
            "results": final_results
        }
        
    finally:
        conn.close()

@app.get("/stats")
async def get_stats():
    """Get indexing and search statistics"""
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
        
        return {
            "files": {
                "total": file_count or 0,
                "average_size": int(avg_size or 0),
                "by_language": language_stats
            },
            "searches": {
                "today": searches_today or 0
            },
            "database": {
                "path": DB_PATH,
                "size_mb": round(Path(DB_PATH).stat().st_size / 1024 / 1024, 2) if Path(DB_PATH).exists() else 0
            }
        }
        
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM indexed_files")
        file_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "indexed_files": file_count,
            "database": "ready",
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