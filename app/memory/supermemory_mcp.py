"""
Supermemory MCP Server Integration.
Universal, persistent memory layer shared by agents/tools.
"""

import os
import json
import hashlib
import sqlite3
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from enum import Enum
from app.core.circuit_breaker import with_circuit_breaker, get_llm_circuit_breaker, get_weaviate_circuit_breaker, get_redis_circuit_breaker, get_webhook_circuit_breaker

# ============================================
# Configuration
# ============================================

MEMORY_DB_PATH = "tmp/supermemory.db"
MAX_RESULTS = 50
LATENCY_TARGET_MS = 400

class MemoryType(Enum):
    """Types of memory entries."""
    EPISODIC = "episodic"  # Per-task notes, recent decisions
    SEMANTIC = "semantic"  # Patterns, conventions, architectural idioms
    PROCEDURAL = "procedural"  # Step checklists, fix recipes

@dataclass
class MemoryEntry:
    """Structured memory entry with deduplication."""
    topic: str
    content: str
    source: str
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    memory_type: MemoryType = MemoryType.SEMANTIC
    embedding_vector: Optional[List[float]] = None
    hash_id: Optional[str] = None
    
    def __post_init__(self):
        """Generate hash ID for deduplication."""
        if not self.hash_id:
            content_hash = hashlib.sha256(
                f"{self.topic}:{self.content}:{self.source}".encode()
            ).hexdigest()[:16]
            self.hash_id = content_hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "hash_id": self.hash_id,
            "topic": self.topic,
            "content": self.content,
            "source": self.source,
            "tags": json.dumps(self.tags),
            "timestamp": self.timestamp.isoformat(),
            "memory_type": self.memory_type.value,
            "embedding_vector": json.dumps(self.embedding_vector) if self.embedding_vector else None
        }

# ============================================
# Supermemory Store
# ============================================

class SupermemoryStore:
    """
    Persistent memory store with deduplication and semantic search.
    """
    
    def __init__(self, db_path: str = MEMORY_DB_PATH):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure database exists with proper schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    hash_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    tags TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    memory_type TEXT NOT NULL,
                    embedding_vector TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP
                )
            """)
            
            # Indexes for fast retrieval
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_topic 
                ON memory_entries(topic)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type 
                ON memory_entries(memory_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON memory_entries(timestamp DESC)
            """)
            
            # FTS5 for full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    hash_id UNINDEXED,
                    topic,
                    content,
                    tags,
                    content=memory_entries,
                    content_rowid=rowid
                )
            """)
            
            # Triggers to keep FTS in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_fts_insert 
                AFTER INSERT ON memory_entries BEGIN
                    INSERT INTO memory_fts(hash_id, topic, content, tags)
                    VALUES (new.hash_id, new.topic, new.content, new.tags);
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_fts_update 
                AFTER UPDATE ON memory_entries BEGIN
                    UPDATE memory_fts 
                    SET topic = new.topic, content = new.content, tags = new.tags
                    WHERE hash_id = new.hash_id;
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_fts_delete 
                AFTER DELETE ON memory_entries BEGIN
                    DELETE FROM memory_fts WHERE hash_id = old.hash_id;
                END
            """)
            
            conn.commit()
    
    async def add_to_memory(
        self,
        entry: MemoryEntry,
        deduplicate: bool = True
    ) -> Dict[str, Any]:
        """
        Add entry to memory with deduplication.
        
        Args:
            entry: Memory entry to add
            deduplicate: Whether to check for duplicates
        
        Returns:
            Result with status and entry ID
        """
        start_time = asyncio.get_event_loop().time()
        
        with sqlite3.connect(self.db_path) as conn:
            # Check for duplicate if enabled
            if deduplicate:
                existing = conn.execute(
                    "SELECT hash_id FROM memory_entries WHERE hash_id = ?",
                    (entry.hash_id,)
                ).fetchone()
                
                if existing:
                    # Update access count
                    conn.execute("""
                        UPDATE memory_entries 
                        SET access_count = access_count + 1,
                            last_accessed = CURRENT_TIMESTAMP
                        WHERE hash_id = ?
                    """, (entry.hash_id,))
                    conn.commit()
                    
                    latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                    return {
                        "status": "duplicate",
                        "hash_id": entry.hash_id,
                        "latency_ms": latency_ms
                    }
            
            # Insert new entry
            entry_dict = entry.to_dict()
            conn.execute("""
                INSERT OR REPLACE INTO memory_entries 
                (hash_id, topic, content, source, tags, timestamp, memory_type, embedding_vector)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_dict["hash_id"],
                entry_dict["topic"],
                entry_dict["content"],
                entry_dict["source"],
                entry_dict["tags"],
                entry_dict["timestamp"],
                entry_dict["memory_type"],
                entry_dict["embedding_vector"]
            ))
            conn.commit()
        
        latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        return {
            "status": "added",
            "hash_id": entry.hash_id,
            "latency_ms": latency_ms
        }
    
    @with_circuit_breaker("database")
    async def search_memory(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        tags: Optional[List[str]] = None,
        source_pattern: Optional[str] = None,
        limit: int = MAX_RESULTS,
        use_fts: bool = True
    ) -> List[MemoryEntry]:
        """
        Search memory with multiple filters.
        
        Args:
            query: Search query text
            memory_types: Filter by memory types
            tags: Filter by tags
            source_pattern: Filter by source pattern
            limit: Maximum results
            use_fts: Use full-text search
        
        Returns:
            List of matching memory entries
        """
        start_time = asyncio.get_event_loop().time()
        
        with sqlite3.connect(self.db_path) as conn:
            # Build query
            if use_fts and query:
                # Use FTS5 for text search (sanitize query for FTS5)
                sanitized_query = query.replace('"', '').replace("'", "").replace(".", " ")
                base_query = """
                    SELECT DISTINCT m.*
                    FROM memory_entries m
                    JOIN memory_fts f ON m.hash_id = f.hash_id
                    WHERE memory_fts MATCH ?
                """
                params = [f'"{sanitized_query}"']
            else:
                # Regular search
                base_query = """
                    SELECT * FROM memory_entries
                    WHERE (topic LIKE ? OR content LIKE ?)
                """
                params = [f"%{query}%", f"%{query}%"]
            
            # Add filters
            conditions = []
            
            if memory_types:
                type_placeholders = ",".join(["?"] * len(memory_types))
                conditions.append(f"memory_type IN ({type_placeholders})")
                params.extend([t.value for t in memory_types])
            
            if tags:
                for tag in tags:
                    conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
            
            if source_pattern:
                conditions.append("source LIKE ?")
                params.append(f"%{source_pattern}%")
            
            if conditions:
                if use_fts and query:
                    base_query += " AND " + " AND ".join(conditions)
                else:
                    base_query += " AND " + " AND ".join(conditions)
            
            # Add ordering and limit
            base_query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            # Execute query
            cursor = conn.execute(base_query, params)
            rows = cursor.fetchall()
            
            # Convert to MemoryEntry objects
            entries = []
            for row in rows:
                entry = MemoryEntry(
                    topic=row[1],
                    content=row[2],
                    source=row[3],
                    tags=json.loads(row[4]) if row[4] else [],
                    timestamp=datetime.fromisoformat(row[5]),
                    memory_type=MemoryType(row[6]),
                    embedding_vector=json.loads(row[7]) if row[7] else None,
                    hash_id=row[0]
                )
                entries.append(entry)
            
            # Update access counts
            if entries:
                hash_ids = [e.hash_id for e in entries]
                placeholders = ",".join(["?"] * len(hash_ids))
                conn.execute(f"""
                    UPDATE memory_entries 
                    SET access_count = access_count + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE hash_id IN ({placeholders})
                """, hash_ids)
                conn.commit()
        
        latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Check latency target
        if latency_ms > LATENCY_TARGET_MS:
            print(f"⚠️ Supermemory search exceeded target: {latency_ms:.0f}ms > {LATENCY_TARGET_MS}ms")
        
        return entries
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone()[0]
            
            by_type = {}
            for memory_type in MemoryType:
                count = conn.execute(
                    "SELECT COUNT(*) FROM memory_entries WHERE memory_type = ?",
                    (memory_type.value,)
                ).fetchone()[0]
                by_type[memory_type.value] = count
            
            most_accessed = conn.execute("""
                SELECT topic, access_count 
                FROM memory_entries 
                ORDER BY access_count DESC 
                LIMIT 5
            """).fetchall()
            
            return {
                "total_entries": total,
                "by_type": by_type,
                "most_accessed": [
                    {"topic": row[0], "count": row[1]} 
                    for row in most_accessed
                ]
            }

# ============================================
# Memory Patterns
# ============================================

class MemoryPatterns:
    """
    Common patterns for memory usage.
    """
    
    @staticmethod
    def create_decision_memory(
        decision: str,
        rationale: List[str],
        source: str,
        alternatives: Optional[List[str]] = None
    ) -> MemoryEntry:
        """Create memory entry for architectural decisions."""
        content = f"Decision: {decision}\n"
        content += f"Rationale: {'; '.join(rationale)}\n"
        if alternatives:
            content += f"Alternatives considered: {', '.join(alternatives)}"
        
        return MemoryEntry(
            topic=f"Decision: {decision[:50]}",
            content=content,
            source=source,
            tags=["decision", "architecture"],
            memory_type=MemoryType.SEMANTIC
        )
    
    @staticmethod
    def create_pattern_memory(
        pattern_name: str,
        implementation: str,
        use_cases: List[str],
        source: str
    ) -> MemoryEntry:
        """Create memory entry for code patterns."""
        content = f"Pattern: {pattern_name}\n"
        content += f"Implementation:\n{implementation}\n"
        content += f"Use cases: {'; '.join(use_cases)}"
        
        return MemoryEntry(
            topic=f"Pattern: {pattern_name}",
            content=content,
            source=source,
            tags=["pattern", "reusable"],
            memory_type=MemoryType.PROCEDURAL
        )
    
    @staticmethod
    def create_edge_case_memory(
        issue: str,
        solution: str,
        source: str,
        prevention: Optional[str] = None
    ) -> MemoryEntry:
        """Create memory entry for edge cases."""
        content = f"Issue: {issue}\n"
        content += f"Solution: {solution}\n"
        if prevention:
            content += f"Prevention: {prevention}"
        
        return MemoryEntry(
            topic=f"Edge case: {issue[:50]}",
            content=content,
            source=source,
            tags=["edge-case", "gotcha"],
            memory_type=MemoryType.EPISODIC
        )

# ============================================
# MCP Server Interface
# ============================================

class SupermemoryMCP:
    """
    MCP server interface for Supermemory.
    """
    
    def __init__(self):
        self.store = SupermemoryStore()
    
    @with_circuit_breaker("database")
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP request.
        
        Args:
            request: MCP request object
        
        Returns:
            MCP response object
        """
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "add_to_memory":
            entry = MemoryEntry(
                topic=params["topic"],
                content=params["content"],
                source=params["source"],
                tags=params.get("tags", []),
                memory_type=MemoryType(params.get("memory_type", "semantic"))
            )
            result = await self.store.add_to_memory(entry)
            return {"result": result}
        
        elif method == "search_memory":
            entries = await self.store.search_memory(
                query=params.get("query", ""),
                memory_types=[MemoryType(t) for t in params.get("memory_types", [])],
                tags=params.get("tags"),
                source_pattern=params.get("source_pattern"),
                limit=params.get("limit", MAX_RESULTS)
            )
            return {
                "result": {
                    "entries": [
                        {
                            "topic": e.topic,
                            "content": e.content,
                            "source": e.source,
                            "tags": e.tags,
                            "timestamp": e.timestamp.isoformat(),
                            "memory_type": e.memory_type.value
                        }
                        for e in entries
                    ],
                    "count": len(entries)
                }
            }
        
        elif method == "get_stats":
            stats = await self.store.get_stats()
            return {"result": stats}
        
        else:
            return {"error": f"Unknown method: {method}"}

# ============================================
# Usage Helpers
# ============================================

async def memorize_task_learnings(
    task: str,
    learnings: List[str],
    source: str
) -> None:
    """
    Add task learnings to memory.
    
    Args:
        task: Task description
        learnings: List of learnings
        source: Source file or context
    """
    store = SupermemoryStore()
    
    for learning in learnings:
        entry = MemoryEntry(
            topic=f"Learning: {task[:30]}",
            content=learning,
            source=source,
            tags=["learning", "task"],
            memory_type=MemoryType.EPISODIC
        )
        await store.add_to_memory(entry)

@with_circuit_breaker("database")
async def recall_relevant_memories(
    query: str,
    limit: int = 10
) -> List[MemoryEntry]:
    """
    Recall memories relevant to a query.
    
    Args:
        query: Search query
        limit: Maximum results
    
    Returns:
        List of relevant memory entries
    """
    store = SupermemoryStore()
    return await store.search_memory(query, limit=limit)

# ============================================
# CLI Interface
# ============================================

@with_circuit_breaker("database")
async def main():
    """CLI for Supermemory testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Supermemory MCP")
    parser.add_argument("--add", help="Add memory entry")
    parser.add_argument("--search", help="Search memories")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--topic", help="Topic for new entry")
    parser.add_argument("--source", default="cli", help="Source for new entry")
    
    args = parser.parse_args()
    
    store = SupermemoryStore()
    
    if args.add and args.topic:
        entry = MemoryEntry(
            topic=args.topic,
            content=args.add,
            source=args.source,
            tags=["cli"]
        )
        result = await store.add_to_memory(entry)
        print(f"✅ Memory added: {result}")
    
    elif args.search:
        entries = await store.search_memory(args.search)
        print(f"\n📚 Found {len(entries)} memories:")
        for entry in entries:
            print(f"\n  Topic: {entry.topic}")
            print(f"  Content: {entry.content[:100]}...")
            print(f"  Source: {entry.source}")
            print(f"  Tags: {', '.join(entry.tags)}")
    
    elif args.stats:
        stats = await store.get_stats()
        print("\n📊 Supermemory Statistics:")
        print(f"  Total entries: {stats['total_entries']}")
        print(f"  By type: {stats['by_type']}")
        print(f"  Most accessed: {stats['most_accessed']}")

if __name__ == "__main__":
    asyncio.run(main())