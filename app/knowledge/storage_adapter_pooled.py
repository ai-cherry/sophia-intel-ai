"""
Enhanced Storage Adapter with Connection Pooling

Provides database-agnostic operations with connection pooling for improved performance
and scalability, especially for PostgreSQL deployments.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor

    PSYCOPG2_AVAILABLE = True
except ImportError:
    psycopg2 = None
    pool = None
    PSYCOPG2_AVAILABLE = False

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool, QueuePool

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

from app.core.ai_logger import logger
from app.core.config import settings
from app.knowledge.models import (
    KnowledgeEntity,
    KnowledgeRelationship,
    KnowledgeTag,
    KnowledgeVersion,
    SyncConflict,
    SyncOperation,
)


class ConnectionPool:
    """Abstract base class for connection pooling"""

    def get_connection(self):
        raise NotImplementedError

    def put_connection(self, conn):
        raise NotImplementedError

    def close_all(self):
        raise NotImplementedError


class PostgreSQLPool(ConnectionPool):
    """PostgreSQL connection pool using psycopg2"""

    def __init__(self, **kwargs):
        if not PSYCOPG2_AVAILABLE:
            raise ImportError(
                "psycopg2 required for PostgreSQL. Install with: pip install psycopg2-binary psycopg2-pool"
            )

        # Connection pool configuration
        self.min_connections = kwargs.get("min_connections", 2)
        self.max_connections = kwargs.get("max_connections", 20)

        # Create connection pool
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                self.min_connections,
                self.max_connections,
                host=kwargs.get("host", os.getenv("DB_HOST", "localhost")),
                port=int(kwargs.get("port", os.getenv("DB_PORT", "5432"))),
                database=kwargs.get("database", os.getenv("DB_NAME", "sophia")),
                user=kwargs.get("user", os.getenv("DB_USER", "sophia")),
                password=kwargs.get("password", os.getenv("DB_PASSWORD", "")),
                cursor_factory=RealDictCursor,
                connect_timeout=kwargs.get("connect_timeout", 10),
            )
            logger.info(
                f"PostgreSQL connection pool created: {self.min_connections}-{self.max_connections} connections"
            )
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        finally:
            if conn:
                self.pool.putconn(conn)

    def close_all(self):
        """Close all connections in the pool"""
        if hasattr(self, "pool"):
            self.pool.closeall()
            logger.info("PostgreSQL connection pool closed")


class SQLitePool(ConnectionPool):
    """SQLite connection pool (thread-safe singleton)"""

    def __init__(self, **kwargs):
        self.db_path = kwargs.get("db_path", os.getenv("DB_PATH", "sophia.db"))
        self._connection = None
        self._lock = threading.Lock()
        self._connect()

    def _connect(self):
        """Create SQLite connection"""
        # SQLite doesn't benefit from connection pooling in the same way
        # Use a single connection with thread safety
        self._connection = sqlite3.connect(
            self.db_path, check_same_thread=False, isolation_level=None  # Autocommit mode
        )
        self._connection.row_factory = sqlite3.Row

        # Enable WAL mode for better concurrency
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=NORMAL")

        logger.info(f"SQLite connection established: {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Get the SQLite connection with thread safety"""
        with self._lock:
            yield self._connection

    def close_all(self):
        """Close the SQLite connection"""
        if self._connection:
            self._connection.close()
            logger.info("SQLite connection closed")


class SQLAlchemyPool(ConnectionPool):
    """SQLAlchemy-based connection pool for any database"""

    def __init__(self, **kwargs):
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("SQLAlchemy required. Install with: pip install sqlalchemy")

        # Build connection URL
        db_type = kwargs.get("db_type", os.getenv("DB_TYPE", "sqlite"))

        if db_type == "sqlite":
            db_path = kwargs.get("db_path", os.getenv("DB_PATH", "sophia.db"))
            url = f"sqlite:///{db_path}"
            poolclass = NullPool  # No pooling for SQLite
        elif db_type == "postgresql":
            host = kwargs.get("host", os.getenv("DB_HOST", "localhost"))
            port = kwargs.get("port", os.getenv("DB_PORT", "5432"))
            database = kwargs.get("database", os.getenv("DB_NAME", "sophia"))
            user = kwargs.get("user", os.getenv("DB_USER", "sophia"))
            password = kwargs.get("password", os.getenv("DB_PASSWORD", ""))
            url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            poolclass = QueuePool
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        # Create engine with connection pooling
        self.engine = create_engine(
            url,
            poolclass=poolclass,
            pool_size=kwargs.get("pool_size", 10),
            max_overflow=kwargs.get("max_overflow", 20),
            pool_timeout=kwargs.get("pool_timeout", 30),
            pool_recycle=kwargs.get("pool_recycle", 3600),
            pool_pre_ping=True,  # Test connections before using
            echo=kwargs.get("echo", False),
        )

        logger.info(f"SQLAlchemy connection pool created for {db_type}")

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        with self.engine.connect() as conn:
            yield conn

    def close_all(self):
        """Dispose of the connection pool"""
        self.engine.dispose()
        logger.info("SQLAlchemy connection pool disposed")


class PooledStorageAdapter:
    """
    Enhanced storage adapter with connection pooling support.

    Features:
    - Connection pooling for PostgreSQL
    - Thread-safe SQLite connections
    - Automatic retry on connection failures
    - Query performance monitoring
    - Prepared statement support
    """

    def __init__(self, **kwargs):
        """Initialize storage adapter with connection pooling"""
        self.db_type = kwargs.get("db_type", os.getenv("DB_TYPE", "sqlite"))

        # Initialize appropriate connection pool
        if self.db_type == "sqlite":
            self.pool = SQLitePool(**kwargs)
        elif self.db_type == "postgresql":
            # Use native psycopg2 pool if available, otherwise SQLAlchemy
            if PSYCOPG2_AVAILABLE and kwargs.get("use_native_pool", True):
                self.pool = PostgreSQLPool(**kwargs)
            elif SQLALCHEMY_AVAILABLE:
                self.pool = SQLAlchemyPool(db_type="postgresql", **kwargs)
            else:
                raise ImportError(
                    "PostgreSQL support requires psycopg2 or SQLAlchemy. "
                    "Install with: pip install psycopg2-binary psycopg2-pool"
                )
        else:
            # Try SQLAlchemy for other database types
            if SQLALCHEMY_AVAILABLE:
                self.pool = SQLAlchemyPool(db_type=self.db_type, **kwargs)
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

        # Query statistics
        self._query_stats = {
            "total_queries": 0,
            "total_time": 0.0,
            "slow_queries": [],
        }

        # Prepared statements cache
        self._prepared_statements = {}

        logger.info(f"PooledStorageAdapter initialized for {self.db_type}")

    def _execute(self, query: str, params: tuple = (), retry_count: int = 3) -> Any:
        """Execute query with connection pooling and retry logic"""
        import time

        start_time = time.time()
        last_error = None

        for attempt in range(retry_count):
            try:
                with self.pool.get_connection() as conn:
                    # Adapt query for database type
                    if self.db_type == "postgresql":
                        query = query.replace("?", "%s")

                    # Execute query
                    if isinstance(conn, sqlite3.Connection) or hasattr(conn, "cursor"):
                        cursor = conn.cursor()
                        cursor.execute(query, params)
                        conn.commit()
                    else:  # SQLAlchemy connection
                        result = conn.execute(text(query), params)
                        conn.commit()
                        cursor = result

                    # Update statistics
                    elapsed = time.time() - start_time
                    self._query_stats["total_queries"] += 1
                    self._query_stats["total_time"] += elapsed

                    # Track slow queries
                    if elapsed > 1.0:  # Queries taking more than 1 second
                        self._query_stats["slow_queries"].append(
                            {
                                "query": query[:100],  # First 100 chars
                                "time": elapsed,
                                "timestamp": datetime.utcnow(),
                            }
                        )
                        # Keep only last 100 slow queries
                        self._query_stats["slow_queries"] = self._query_stats["slow_queries"][-100:]

                    return cursor

            except Exception as e:
                last_error = e
                if attempt < retry_count - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Query failed (attempt {attempt + 1}/{retry_count}), retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Query failed after {retry_count} attempts: {e}")

        raise last_error

    def _fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch single row with connection pooling"""
        cursor = self._execute(query, params)

        if hasattr(cursor, "fetchone"):
            row = cursor.fetchone()
            if row:
                if isinstance(row, sqlite3.Row):
                    return dict(row)
                elif isinstance(row, dict):
                    return row
                else:
                    # Handle other row types
                    return dict(zip([d[0] for d in cursor.description], row))
        return None

    def _fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows with connection pooling"""
        cursor = self._execute(query, params)

        if hasattr(cursor, "fetchall"):
            rows = cursor.fetchall()
            if self.db_type == "sqlite":
                return [dict(row) for row in rows]
            elif all(isinstance(row, dict) for row in rows):
                return rows
            else:
                # Handle other row types
                columns = [d[0] for d in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        return []

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool and query statistics"""
        stats = {
            "db_type": self.db_type,
            "query_stats": self._query_stats.copy(),
        }

        # Add pool-specific stats
        if isinstance(self.pool, PostgreSQLPool):
            stats["pool_info"] = {
                "min_connections": self.pool.min_connections,
                "max_connections": self.pool.max_connections,
            }
        elif isinstance(self.pool, SQLAlchemyPool):
            pool_status = self.pool.engine.pool.status()
            stats["pool_info"] = {
                "status": pool_status,
            }

        return stats

    def close(self):
        """Close all connections in the pool"""
        self.pool.close_all()
        logger.info("Storage adapter closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ========== Backwards Compatibility ==========
    # Include all the original methods from StorageAdapter
    # These would delegate to the pooled implementation

    async def create_knowledge(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        """Create knowledge entity using pooled connections"""
        try:
            query = """
            INSERT INTO knowledge_entities (
                id, name, category, classification, priority, content,
                metadata, source_uri, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                entity.id,
                entity.name,
                entity.category,
                entity.classification,
                entity.priority,
                json.dumps(entity.content) if entity.content else None,
                json.dumps(entity.metadata) if entity.metadata else None,
                entity.source_uri,
                entity.is_active,
                (
                    entity.created_at.isoformat()
                    if entity.created_at
                    else datetime.utcnow().isoformat()
                ),
                (
                    entity.updated_at.isoformat()
                    if entity.updated_at
                    else datetime.utcnow().isoformat()
                ),
            )

            self._execute(query, params)
            logger.info(f"Created knowledge entity: {entity.id}")
            return entity

        except Exception as e:
            logger.error(f"Failed to create knowledge entity {entity.id}: {e}")
            raise

    async def get_knowledge(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """Get knowledge entity using pooled connections"""
        try:
            query = "SELECT * FROM knowledge_entities WHERE id = ? AND is_active = true"
            row = self._fetchone(query, (entity_id,))

            if row:
                return KnowledgeEntity(
                    id=row["id"],
                    name=row["name"],
                    category=row["category"],
                    classification=row["classification"],
                    priority=row["priority"],
                    content=json.loads(row["content"]) if row["content"] else {},
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    source_uri=row["source_uri"],
                    is_active=row["is_active"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            return None

        except Exception as e:
            logger.error(f"Failed to get knowledge entity {entity_id}: {e}")
            return None

    async def update_knowledge(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        """Update knowledge entity using pooled connections"""
        try:
            entity.updated_at = datetime.utcnow()

            query = """
            UPDATE knowledge_entities
            SET name = ?, category = ?, classification = ?, priority = ?,
                content = ?, metadata = ?, source_uri = ?, is_active = ?,
                updated_at = ?
            WHERE id = ?
            """

            params = (
                entity.name,
                entity.category,
                entity.classification,
                entity.priority,
                json.dumps(entity.content) if entity.content else None,
                json.dumps(entity.metadata) if entity.metadata else None,
                entity.source_uri,
                entity.is_active,
                entity.updated_at.isoformat(),
                entity.id,
            )

            cursor = self._execute(query, params)
            if hasattr(cursor, "rowcount") and cursor.rowcount == 0:
                logger.warning(f"No rows updated for entity {entity.id}")
            else:
                logger.info(f"Updated knowledge entity: {entity.id}")

            return entity

        except Exception as e:
            logger.error(f"Failed to update knowledge entity {entity.id}: {e}")
            raise

    async def delete_knowledge(self, entity_id: str) -> bool:
        """Delete knowledge entity using pooled connections (soft delete)"""
        try:
            query = "UPDATE knowledge_entities SET is_active = false, updated_at = ? WHERE id = ?"
            params = (datetime.utcnow().isoformat(), entity_id)

            cursor = self._execute(query, params)
            success = hasattr(cursor, "rowcount") and cursor.rowcount > 0

            if success:
                logger.info(f"Deleted knowledge entity: {entity_id}")
            else:
                logger.warning(f"Entity not found for deletion: {entity_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete knowledge entity {entity_id}: {e}")
            return False

    async def list_knowledge(
        self,
        classification: Optional[str] = None,
        category: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[KnowledgeEntity]:
        """List knowledge entities using pooled connections with filtering"""
        try:
            # Build dynamic query based on filters
            query = "SELECT * FROM knowledge_entities WHERE is_active = ?"
            params = [is_active]

            if classification:
                query += " AND classification = ?"
                params.append(classification)

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = self._fetchall(query, tuple(params))

            entities = []
            for row in rows:
                entities.append(
                    KnowledgeEntity(
                        id=row["id"],
                        name=row["name"],
                        category=row["category"],
                        classification=row["classification"],
                        priority=row["priority"],
                        content=json.loads(row["content"]) if row["content"] else {},
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                        source_uri=row["source_uri"],
                        is_active=row["is_active"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                )

            logger.info(f"Listed {len(entities)} knowledge entities")
            return entities

        except Exception as e:
            logger.error(f"Failed to list knowledge entities: {e}")
            return []


# Export enhanced adapter as default if available
def get_storage_adapter(**kwargs) -> Union[StorageAdapter, PooledStorageAdapter]:
    """
    Get appropriate storage adapter based on configuration.

    Returns PooledStorageAdapter if dependencies are available,
    otherwise falls back to original StorageAdapter.
    """
    db_type = kwargs.get("db_type", os.getenv("DB_TYPE", "sqlite"))
    use_pooling = kwargs.get("use_pooling", True)

    # Check if pooling is available and desired
    if use_pooling:
        if db_type == "postgresql" and (PSYCOPG2_AVAILABLE or SQLALCHEMY_AVAILABLE):
            logger.info("Using PooledStorageAdapter with connection pooling")
            return PooledStorageAdapter(**kwargs)
        elif db_type == "sqlite":
            logger.info("Using PooledStorageAdapter with thread-safe SQLite")
            return PooledStorageAdapter(**kwargs)

    # Fall back to original adapter
    logger.info("Using standard StorageAdapter without pooling")
    from app.knowledge.storage_adapter import StorageAdapter

    return StorageAdapter()
