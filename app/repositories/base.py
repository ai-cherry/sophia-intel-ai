"""
Repository Pattern Base Classes
Provides abstraction layer for storage operations.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel
import logging

from app.core.logging_config import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

# Type variables for generic repository
T = TypeVar('T', bound=BaseModel)
ID = TypeVar('ID', str, int)

# ============================================
# Base Repository Interface
# ============================================

class IRepository(ABC, Generic[T, ID]):
    """Abstract base repository interface."""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def get(self, id: ID) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_many(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None
    ) -> List[T]:
        """Get multiple entities with filters."""
        pass
    
    @abstractmethod
    async def update(self, id: ID, entity: T) -> Optional[T]:
        """Update an entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Delete an entity."""
        pass
    
    @abstractmethod
    async def exists(self, id: ID) -> bool:
        """Check if entity exists."""
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with filters."""
        pass

# ============================================
# Transaction Support
# ============================================

class ITransactional(ABC):
    """Interface for transactional operations."""
    
    @abstractmethod
    async def begin_transaction(self):
        """Begin a transaction."""
        pass
    
    @abstractmethod
    async def commit(self):
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback(self):
        """Rollback the current transaction."""
        pass
    
    @abstractmethod
    async def in_transaction(self) -> bool:
        """Check if in a transaction."""
        pass

# ============================================
# Unit of Work Pattern
# ============================================

class IUnitOfWork(ABC):
    """Unit of Work pattern for managing repositories."""
    
    @abstractmethod
    async def __aenter__(self):
        """Enter context manager."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass
    
    @abstractmethod
    async def commit(self):
        """Commit all changes."""
        pass
    
    @abstractmethod
    async def rollback(self):
        """Rollback all changes."""
        pass

# ============================================
# Base Repository Implementation
# ============================================

class BaseRepository(IRepository[T, ID]):
    """Base repository with common functionality."""
    
    def __init__(self, model_class: type[T]):
        """
        Initialize repository.
        
        Args:
            model_class: Pydantic model class for entities
        """
        self.model_class = model_class
        self._cache: Dict[ID, T] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps: Dict[ID, datetime] = {}
    
    def _is_cache_valid(self, id: ID) -> bool:
        """Check if cached entry is still valid."""
        if id not in self._cache_timestamps:
            return False
        
        age = (datetime.utcnow() - self._cache_timestamps[id]).total_seconds()
        return age < self._cache_ttl
    
    def _cache_entity(self, id: ID, entity: T) -> None:
        """Cache an entity."""
        self._cache[id] = entity
        self._cache_timestamps[id] = datetime.utcnow()
    
    def _invalidate_cache(self, id: ID) -> None:
        """Invalidate cache for an entity."""
        self._cache.pop(id, None)
        self._cache_timestamps.pop(id, None)
    
    async def get_cached(self, id: ID) -> Optional[T]:
        """Get entity from cache if available."""
        if id in self._cache and self._is_cache_valid(id):
            logger.debug(f"Cache hit for {self.model_class.__name__}:{id}")
            return self._cache[id]
        return None
    
    def _validate_entity(self, entity: T) -> None:
        """
        Validate entity before storage.
        
        Args:
            entity: Entity to validate
            
        Raises:
            ValueError: If entity is invalid
        """
        if not isinstance(entity, self.model_class):
            raise ValueError(
                f"Entity must be instance of {self.model_class.__name__}, "
                f"got {type(entity).__name__}"
            )
    
    async def batch_create(self, entities: List[T]) -> List[T]:
        """
        Create multiple entities in batch.
        
        Args:
            entities: List of entities to create
            
        Returns:
            List of created entities
        """
        created = []
        for entity in entities:
            created.append(await self.create(entity))
        return created
    
    async def batch_delete(self, ids: List[ID]) -> int:
        """
        Delete multiple entities in batch.
        
        Args:
            ids: List of IDs to delete
            
        Returns:
            Number of deleted entities
        """
        deleted = 0
        for id in ids:
            if await self.delete(id):
                deleted += 1
        return deleted

# ============================================
# Query Builder
# ============================================

class QueryBuilder:
    """SQL query builder for repositories."""
    
    def __init__(self, table: str):
        """Initialize query builder."""
        self.table = table
        self.select_fields = ["*"]
        self.where_clauses = []
        self.order_clauses = []
        self.limit_value = None
        self.offset_value = None
        self.join_clauses = []
        self.group_by_fields = []
        self.having_clauses = []
    
    def select(self, *fields: str) -> 'QueryBuilder':
        """Set SELECT fields."""
        self.select_fields = list(fields) if fields else ["*"]
        return self
    
    def where(self, condition: str, value: Any = None) -> 'QueryBuilder':
        """Add WHERE clause."""
        self.where_clauses.append((condition, value))
        return self
    
    def order_by(self, field: str, direction: str = "ASC") -> 'QueryBuilder':
        """Add ORDER BY clause."""
        self.order_clauses.append(f"{field} {direction}")
        return self
    
    def limit(self, value: int) -> 'QueryBuilder':
        """Set LIMIT."""
        self.limit_value = value
        return self
    
    def offset(self, value: int) -> 'QueryBuilder':
        """Set OFFSET."""
        self.offset_value = value
        return self
    
    def join(
        self,
        table: str,
        on: str,
        join_type: str = "INNER"
    ) -> 'QueryBuilder':
        """Add JOIN clause."""
        self.join_clauses.append(f"{join_type} JOIN {table} ON {on}")
        return self
    
    def group_by(self, *fields: str) -> 'QueryBuilder':
        """Add GROUP BY."""
        self.group_by_fields.extend(fields)
        return self
    
    def having(self, condition: str) -> 'QueryBuilder':
        """Add HAVING clause."""
        self.having_clauses.append(condition)
        return self
    
    def build_select(self) -> tuple[str, List[Any]]:
        """Build SELECT query."""
        query_parts = [
            f"SELECT {', '.join(self.select_fields)}",
            f"FROM {self.table}"
        ]
        
        params = []
        
        # Add JOINs
        for join in self.join_clauses:
            query_parts.append(join)
        
        # Add WHERE
        if self.where_clauses:
            conditions = []
            for condition, value in self.where_clauses:
                if value is not None:
                    conditions.append(condition)
                    params.append(value)
                else:
                    conditions.append(condition)
            
            query_parts.append(f"WHERE {' AND '.join(conditions)}")
        
        # Add GROUP BY
        if self.group_by_fields:
            query_parts.append(f"GROUP BY {', '.join(self.group_by_fields)}")
        
        # Add HAVING
        if self.having_clauses:
            query_parts.append(f"HAVING {' AND '.join(self.having_clauses)}")
        
        # Add ORDER BY
        if self.order_clauses:
            query_parts.append(f"ORDER BY {', '.join(self.order_clauses)}")
        
        # Add LIMIT/OFFSET
        if self.limit_value is not None:
            query_parts.append(f"LIMIT {self.limit_value}")
        
        if self.offset_value is not None:
            query_parts.append(f"OFFSET {self.offset_value}")
        
        query = " ".join(query_parts)
        return query, params
    
    def build_insert(
        self,
        data: Dict[str, Any],
        returning: Optional[str] = None
    ) -> tuple[str, List[Any]]:
        """Build INSERT query."""
        fields = list(data.keys())
        placeholders = ["?" for _ in fields]
        values = list(data.values())
        
        query = f"""
            INSERT INTO {self.table} ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
        """
        
        if returning:
            query += f" RETURNING {returning}"
        
        return query.strip(), values
    
    def build_update(
        self,
        data: Dict[str, Any],
        where_id: Any
    ) -> tuple[str, List[Any]]:
        """Build UPDATE query."""
        set_clauses = [f"{k} = ?" for k in data.keys()]
        values = list(data.values())
        values.append(where_id)
        
        query = f"""
            UPDATE {self.table}
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """
        
        return query.strip(), values
    
    def build_delete(self, where_id: Any) -> tuple[str, List[Any]]:
        """Build DELETE query."""
        query = f"DELETE FROM {self.table} WHERE id = ?"
        return query, [where_id]

# ============================================
# Specification Pattern
# ============================================

class ISpecification(ABC, Generic[T]):
    """Specification pattern for complex queries."""
    
    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        """Check if entity satisfies specification."""
        pass
    
    def and_(self, other: 'ISpecification[T]') -> 'ISpecification[T]':
        """Combine with AND."""
        return AndSpecification(self, other)
    
    def or_(self, other: 'ISpecification[T]') -> 'ISpecification[T]':
        """Combine with OR."""
        return OrSpecification(self, other)
    
    def not_(self) -> 'ISpecification[T]':
        """Negate specification."""
        return NotSpecification(self)

class AndSpecification(ISpecification[T]):
    """AND combination of specifications."""
    
    def __init__(self, left: ISpecification[T], right: ISpecification[T]):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)

class OrSpecification(ISpecification[T]):
    """OR combination of specifications."""
    
    def __init__(self, left: ISpecification[T], right: ISpecification[T]):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) or self.right.is_satisfied_by(entity)

class NotSpecification(ISpecification[T]):
    """NOT specification."""
    
    def __init__(self, spec: ISpecification[T]):
        self.spec = spec
    
    def is_satisfied_by(self, entity: T) -> bool:
        return not self.spec.is_satisfied_by(entity)

# ============================================
# Export
# ============================================

__all__ = [
    "IRepository",
    "ITransactional",
    "IUnitOfWork",
    "BaseRepository",
    "QueryBuilder",
    "ISpecification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification"
]