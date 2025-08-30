"""Enhanced Supermemory MCP Server with reliability improvements."""
import asyncio
import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncContextManager, Dict, Any
import logging
from dataclasses import dataclass
import json
from fastapi import HTTPException
from datetime import datetime
import hashlib

@dataclass
class MemoryEntry:
    """Memory entry dataclass."""
    topic: str
    content: str
    source: str
    tags: list
    timestamp: datetime = None
    memory_type: str = "episodic"
    embedding_vector: list = None
    hash_id: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()
        if not self.hash_id:
            content_hash = hashlib.sha256(f"{self.topic}:{self.content}".encode()).hexdigest()
            self.hash_id = content_hash[:16]
    
    def to_dict(self):
        return {
            "hash_id": self.hash_id,
            "topic": self.topic,
            "content": self.content,
            "source": self.source,
            "tags": json.dumps(self.tags) if self.tags else "[]",
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "memory_type": self.memory_type,
            "embedding_vector": json.dumps(self.embedding_vector) if self.embedding_vector else None
        }

class SupermemoryMCP:
    """Mock SupermemoryMCP for testing."""
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MCPServerConfig:
    """Enhanced MCP server configuration."""
    db_path: str = "tmp/supermemory.db"
    connection_pool_size: int = 10
    connection_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 0.1
    enable_metrics: bool = True

class EnhancedMCPServer:
    """Enhanced MCP server with connection pooling and error recovery."""
    
    def __init__(self, config: MCPServerConfig = None):
        self.config = config or MCPServerConfig()
        self._connection_pool: asyncio.Queue = None
        self._pool_initialized = False
        self._metrics = {"requests": 0, "errors": 0, "avg_latency": 0.0}
        
    async def initialize_pool(self):
        """Initialize database connection pool."""
        if self._pool_initialized:
            return
            
        self._connection_pool = asyncio.Queue(maxsize=self.config.connection_pool_size)
        
        # Pre-populate pool with connections
        for _ in range(self.config.connection_pool_size):
            conn = await aiosqlite.connect(
                self.config.db_path,
                timeout=self.config.connection_timeout
            )
            await self._connection_pool.put(conn)
        
        self._pool_initialized = True
        logger.info(f"Initialized connection pool with {self.config.connection_pool_size} connections")

    @asynccontextmanager
    async def get_connection(self) -> AsyncContextManager[aiosqlite.Connection]:
        """Get database connection from pool with timeout."""
        if not self._pool_initialized:
            await self.initialize_pool()
        
        try:
            # Get connection with timeout
            conn = await asyncio.wait_for(
                self._connection_pool.get(),
                timeout=self.config.connection_timeout
            )
            yield conn
        except asyncio.TimeoutError:
            logger.error("Database connection timeout")
            raise HTTPException(503, "Database connection timeout")
        finally:
            # Return connection to pool
            if 'conn' in locals():
                await self._connection_pool.put(conn)

    async def execute_with_retry(self, operation, *args, **kwargs):
        """Execute operation with exponential backoff retry."""
        last_exception = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = asyncio.get_event_loop().time()
                result = await operation(*args, **kwargs)
                
                # Update metrics
                if self.config.enable_metrics:
                    latency = (asyncio.get_event_loop().time() - start_time) * 1000
                    self._metrics["requests"] += 1
                    self._metrics["avg_latency"] = (
                        (self._metrics["avg_latency"] * (self._metrics["requests"] - 1) + latency) 
                        / self._metrics["requests"]
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Operation failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Operation failed after {self.config.retry_attempts} attempts: {e}")
                    if self.config.enable_metrics:
                        self._metrics["errors"] += 1
        
        raise last_exception

    async def add_to_memory_enhanced(self, entry: MemoryEntry) -> Dict[str, Any]:
        """Enhanced memory addition with connection pooling."""
        async def _add_operation():
            async with self.get_connection() as conn:
                # Check for duplicate
                cursor = await conn.execute(
                    "SELECT hash_id FROM memory_entries WHERE hash_id = ?",
                    (entry.hash_id,)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    # Update access count
                    await conn.execute("""
                        UPDATE memory_entries 
                        SET access_count = access_count + 1,
                            last_accessed = CURRENT_TIMESTAMP
                        WHERE hash_id = ?
                    """, (entry.hash_id,))
                    await conn.commit()
                    return {"status": "duplicate", "hash_id": entry.hash_id}
                
                # Insert new entry
                entry_dict = entry.to_dict()
                await conn.execute("""
                    INSERT INTO memory_entries
                    (hash_id, topic, content, source, tags, timestamp, memory_type, embedding_vector)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, tuple(entry_dict.values()))
                await conn.commit()
                return {"status": "added", "hash_id": entry.hash_id}
        
        return await self.execute_with_retry(_add_operation)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get server performance metrics."""
        pool_stats = {
            "pool_size": self.config.connection_pool_size,
            "available_connections": self._connection_pool.qsize() if self._connection_pool else 0,
        }
        return {**self._metrics, **pool_stats}

    async def health_check(self) -> Dict[str, str]:
        """Enhanced health check with connection testing."""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute("SELECT 1")
                await cursor.fetchone()
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def close(self):
        """Gracefully close all connections."""
        if not self._connection_pool:
            return
            
        logger.info("Closing connection pool...")
        connections = []
        
        # Collect all connections
        while not self._connection_pool.empty():
            try:
                conn = self._connection_pool.get_nowait()
                connections.append(conn)
            except asyncio.QueueEmpty:
                break
        
        # Close connections
        for conn in connections:
            await conn.close()
            
        logger.info(f"Closed {len(connections)} database connections")

# Usage example
async def main():
    """Example usage of enhanced MCP server."""
    config = MCPServerConfig(
        connection_pool_size=5,
        retry_attempts=3,
        enable_metrics=True
    )
    
    server = EnhancedMCPServer(config)
    
    try:
        # Initialize and test
        await server.initialize_pool()
        health = await server.health_check()
        print(f"Server health: {health}")
        
        # Example memory operation
        entry = MemoryEntry(
            topic="Enhanced MCP",
            content="Connection pooling and retry logic implemented",
            source="mcp_enhancement.py",
            tags=["improvement", "reliability"]
        )
        
        result = await server.add_to_memory_enhanced(entry)
        print(f"Memory operation: {result}")
        
        # Get metrics
        metrics = await server.get_metrics()
        print(f"Server metrics: {metrics}")
        
    finally:
        await server.close()

if __name__ == "__main__":
    asyncio.run(main())