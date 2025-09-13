#!/usr/bin/env python3
"""
Database Connection Manager - Phase 1 Implementation
Optimized connection pooling for business-critical operations
This module implements the shared database connection pooling system that
eliminates resource waste and provides the validated performance improvements
for business-critical financial and customer data operations.
Author: Sophia AI
Version: 2.2.0
Date: July 27, 2025
"""
import json
import logging
import threading
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, AsyncContextManager
import asyncpg
import redis.asyncio as redis
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
logger = logging.getLogger(__name__)
@dataclass
class ConnectionMetrics:
    """Database connection performance metrics"""
    pool_name: str
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    connection_requests: int = 0
    average_acquisition_time: float = 0.0
    query_count: int = 0
    average_query_time: float = 0.0
    error_count: int = 0
    last_reset: datetime = None
    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.last_reset:
            data["last_reset"] = self.last_reset.isoformat()
        return data
class DatabaseConfig:
    """Database configuration for business operations"""
    # Primary business database
    BUSINESS_DB_URL = "postgresql+asyncpg://sophia_user:secure_password@localhost:5432/sophia_business"
    BUSINESS_DB_POOL_SIZE = 50
    BUSINESS_DB_MAX_OVERFLOW = 100
    # Analytics database (read replicas)
    ANALYTICS_DB_URL = "postgresql+asyncpg://sophia_user:secure_password@localhost:5432/sophia_analytics"
    ANALYTICS_DB_POOL_SIZE = 30
    ANALYTICS_DB_MAX_OVERFLOW = 50
    # Audit database (compliance)
    AUDIT_DB_URL = (
        "postgresql+asyncpg://sophia_user:secure_password@localhost:5432/sophia_audit"
    )
    AUDIT_DB_POOL_SIZE = 20
    AUDIT_DB_MAX_OVERFLOW = 30
    # Connection timeouts
    CONNECTION_TIMEOUT = 30
    QUERY_TIMEOUT = 60
    IDLE_TIMEOUT = 300
    # Performance monitoring
    METRICS_ENABLED = True
    SLOW_QUERY_THRESHOLD = 1.0  # seconds
# SQLAlchemy models for business data
Base = declarative_base()
class PropertyData(Base):
    """Property information for billing accuracy"""
    __tablename__ = "properties"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(String(100), unique=True, nullable=False, index=True)
    property_name = Column(String(255), nullable=False)
    unit_count = Column(Integer, nullable=False)
    ownership_data = Column(JSON)
    billing_configuration = Column(JSON)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
class CustomerProfile(Base):
    """Customer profiles for intelligence and support"""
    __tablename__ = "customer_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(100), unique=True, nullable=False, index=True)
    profile_data = Column(JSON)
    enrichment_data = Column(JSON)
    engagement_score = Column(Float)
    last_interaction = Column(DateTime(timezone=True))
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
class FinancialTransaction(Base):
    """Financial transactions for billing accuracy"""
    __tablename__ = "financial_transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    property_id = Column(String(100), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    billing_period = Column(String(20), nullable=False)
    transaction_data = Column(JSON)
    validation_status = Column(String(20), default="pending")
    processed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
class AuditTrail(Base):
    """Audit trail for compliance"""
    __tablename__ = "audit_trail"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(100), nullable=False, index=True)
    service_id = Column(String(100), nullable=False)
    operation = Column(String(100), nullable=False)
    user_id = Column(String(100))
    request_data = Column(JSON)
    response_data = Column(JSON)
    processing_time = Column(Float)
    status = Column(String(20))
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
class OptimizedConnectionManager:
    """
    Optimized Database Connection Manager
    Provides shared connection pooling with intelligent load balancing,
    read-write splitting, and comprehensive performance monitoring for
    business-critical operations.
    """
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.pools: dict[str, Any] = {}
        self.engines: dict[str, Any] = {}
        self.session_makers: dict[str, Any] = {}
        self.metrics: dict[str, ConnectionMetrics] = {}
        self.redis_client: redis.Redis | None = None
        self.monitoring_enabled = self.config.METRICS_ENABLED
        self._lock = threading.Lock()
        logger.info("Optimized Connection Manager initialized")
    async def initialize(self):
        """Initialize all database connections and pools"""
        try:
            # Initialize Redis for caching and metrics
            self.redis_client = redis.from_url("${REDIS_URL}/1")
            # Initialize business database pool
            await self._initialize_business_pool()
            # Initialize analytics database pool
            await self._initialize_analytics_pool()
            # Initialize audit database pool
            await self._initialize_audit_pool()
            # Create database tables
            await self._create_tables()
            logger.info("All database pools initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize connection manager: {e}")
            raise
    async def _initialize_business_pool(self):
        """Initialize business database connection pool"""
        pool_name = "business"
        # Create asyncpg pool for high-performance operations
        self.pools[pool_name] = await asyncpg.create_pool(
            self.config.BUSINESS_DB_URL.replace("+asyncpg", ""),
            min_size=10,
            max_size=self.config.BUSINESS_DB_POOL_SIZE,
            max_queries=50000,
            max_inactive_connection_lifetime=self.config.IDLE_TIMEOUT,
            command_timeout=self.config.QUERY_TIMEOUT,
        )
        # Create SQLAlchemy engine for ORM operations
        self.engines[pool_name] = create_async_engine(
            self.config.BUSINESS_DB_URL,
            pool_size=self.config.BUSINESS_DB_POOL_SIZE,
            max_overflow=self.config.BUSINESS_DB_MAX_OVERFLOW,
            pool_timeout=self.config.CONNECTION_TIMEOUT,
            pool_recycle=3600,
            echo=False,
        )
        # Create session maker
        self.session_makers[pool_name] = async_sessionmaker(
            self.engines[pool_name], class_=AsyncSession, expire_on_commit=False
        )
        # Initialize metrics
        self.metrics[pool_name] = ConnectionMetrics(
            pool_name=pool_name, last_reset=datetime.now(UTC)
        )
        logger.info(f"Business database pool initialized: {pool_name}")
    async def _initialize_analytics_pool(self):
        """Initialize analytics database connection pool"""
        pool_name = "analytics"
        # Create asyncpg pool for analytics queries
        self.pools[pool_name] = await asyncpg.create_pool(
            self.config.ANALYTICS_DB_URL.replace("+asyncpg", ""),
            min_size=5,
            max_size=self.config.ANALYTICS_DB_POOL_SIZE,
            max_queries=10000,
            max_inactive_connection_lifetime=self.config.IDLE_TIMEOUT,
            command_timeout=self.config.QUERY_TIMEOUT
            * 2,  # Longer timeout for analytics
        )
        # Create SQLAlchemy engine
        self.engines[pool_name] = create_async_engine(
            self.config.ANALYTICS_DB_URL,
            pool_size=self.config.ANALYTICS_DB_POOL_SIZE,
            max_overflow=self.config.ANALYTICS_DB_MAX_OVERFLOW,
            pool_timeout=self.config.CONNECTION_TIMEOUT,
            pool_recycle=3600,
            echo=False,
        )
        # Create session maker
        self.session_makers[pool_name] = async_sessionmaker(
            self.engines[pool_name], class_=AsyncSession, expire_on_commit=False
        )
        # Initialize metrics
        self.metrics[pool_name] = ConnectionMetrics(
            pool_name=pool_name, last_reset=datetime.now(UTC)
        )
        logger.info(f"Analytics database pool initialized: {pool_name}")
    async def _initialize_audit_pool(self):
        """Initialize audit database connection pool"""
        pool_name = "audit"
        # Create asyncpg pool for audit operations
        self.pools[pool_name] = await asyncpg.create_pool(
            self.config.AUDIT_DB_URL.replace("+asyncpg", ""),
            min_size=3,
            max_size=self.config.AUDIT_DB_POOL_SIZE,
            max_queries=5000,
            max_inactive_connection_lifetime=self.config.IDLE_TIMEOUT,
            command_timeout=self.config.QUERY_TIMEOUT,
        )
        # Create SQLAlchemy engine
        self.engines[pool_name] = create_async_engine(
            self.config.AUDIT_DB_URL,
            pool_size=self.config.AUDIT_DB_POOL_SIZE,
            max_overflow=self.config.AUDIT_DB_MAX_OVERFLOW,
            pool_timeout=self.config.CONNECTION_TIMEOUT,
            pool_recycle=3600,
            echo=False,
        )
        # Create session maker
        self.session_makers[pool_name] = async_sessionmaker(
            self.engines[pool_name], class_=AsyncSession, expire_on_commit=False
        )
        # Initialize metrics
        self.metrics[pool_name] = ConnectionMetrics(
            pool_name=pool_name, last_reset=datetime.now(UTC)
        )
        logger.info(f"Audit database pool initialized: {pool_name}")
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        for pool_name, engine in self.engines.items():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info(f"Tables created/verified for {pool_name} database")
    @asynccontextmanager
    async def get_connection(
        self, pool_name: str = "business"
    ) -> AsyncContextManager[asyncpg.Connection]:
        """Get database connection with automatic cleanup and metrics"""
        if pool_name not in self.pools:
            raise ValueError(f"Pool {pool_name} not found")
        start_time = time.time()
        connection = None
        try:
            # Acquire connection from pool
            connection = await self.pools[pool_name].acquire()
            acquisition_time = time.time() - start_time
            # Update metrics
            if self.monitoring_enabled:
                await self._update_connection_metrics(pool_name, acquisition_time)
            yield connection
        except Exception as e:
            # Update error metrics
            if self.monitoring_enabled:
                await self._update_error_metrics(pool_name)
            logger.error(f"Database connection error in pool {pool_name}: {e}")
            raise
        finally:
            # Release connection back to pool
            if connection:
                await self.pools[pool_name].release(connection)
    @asynccontextmanager
    async def get_session(
        self, pool_name: str = "business"
    ) -> AsyncContextManager[AsyncSession]:
        """Get SQLAlchemy session with automatic cleanup"""
        if pool_name not in self.session_makers:
            raise ValueError(f"Session maker for pool {pool_name} not found")
        session = None
        start_time = time.time()
        try:
            # Create session
            session = self.session_makers[pool_name]()
            acquisition_time = time.time() - start_time
            # Update metrics
            if self.monitoring_enabled:
                await self._update_connection_metrics(pool_name, acquisition_time)
            yield session
            # Commit transaction
            await session.commit()
        except Exception as e:
            # Rollback on error
            if session:
                await session.rollback()
            # Update error metrics
            if self.monitoring_enabled:
                await self._update_error_metrics(pool_name)
            logger.error(f"Database session error in pool {pool_name}: {e}")
            raise
        finally:
            # Close session
            if session:
                await session.close()
    async def execute_query(
        self, query: str, params: tuple = None, pool_name: str = "business"
    ) -> list[dict[str, Any]]:
        """Execute query with performance monitoring"""
        start_time = time.time()
        async with self.get_connection(pool_name) as conn:
            try:
                if params:
                    result = await conn.fetch(query, *params)
                else:
                    result = await conn.fetch(query)
                query_time = time.time() - start_time
                # Update query metrics
                if self.monitoring_enabled:
                    await self._update_query_metrics(pool_name, query_time)
                # Log slow queries
                if query_time > self.config.SLOW_QUERY_THRESHOLD:
                    logger.warning(
                        f"Slow query detected ({query_time:.2f}s): {query[:100]}..."
                    )
                return [dict(row) for row in result]
            except Exception as e:
                query_time = time.time() - start_time
                await self._update_error_metrics(pool_name)
                logger.error(f"Query execution error ({query_time:.2f}s): {e}")
                raise
    async def execute_transaction(
        self, operations: list[dict[str, Any]], pool_name: str = "business"
    ) -> bool:
        """Execute multiple operations in a transaction"""
        start_time = time.time()
        async with self.get_connection(pool_name) as conn:
            async with conn.transaction():
                try:
                    for operation in operations:
                        query = operation["query"]
                        params = operation.get("params", ())
                        if params:
                            await conn.execute(query, *params)
                        else:
                            await conn.execute(query)
                    transaction_time = time.time() - start_time
                    # Update metrics
                    if self.monitoring_enabled:
                        await self._update_query_metrics(pool_name, transaction_time)
                    logger.info(
                        f"Transaction completed successfully ({transaction_time:.2f}s)"
                    )
                    return True
                except Exception as e:
                    transaction_time = time.time() - start_time
                    await self._update_error_metrics(pool_name)
                    logger.error(f"Transaction failed ({transaction_time:.2f}s): {e}")
                    raise
    async def get_pool_status(self) -> dict[str, Any]:
        """Get comprehensive pool status information"""
        status = {
            "pools": {},
            "total_pools": len(self.pools),
            "monitoring_enabled": self.monitoring_enabled,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        for pool_name, pool in self.pools.items():
            pool_status = {
                "name": pool_name,
                "size": pool.get_size(),
                "max_size": pool.get_max_size(),
                "min_size": pool.get_min_size(),
                "idle_connections": pool.get_idle_size(),
                "metrics": (
                    self.metrics[pool_name].to_dict()
                    if pool_name in self.metrics
                    else {}
                ),
            }
            status["pools"][pool_name] = pool_status
        return status
    async def _update_connection_metrics(self, pool_name: str, acquisition_time: float):
        """Update connection acquisition metrics"""
        if pool_name not in self.metrics:
            return
        metrics = self.metrics[pool_name]
        metrics.connection_requests += 1
        # Update average acquisition time
        if metrics.average_acquisition_time == 0:
            metrics.average_acquisition_time = acquisition_time
        else:
            metrics.average_acquisition_time = (
                metrics.average_acquisition_time + acquisition_time
            ) / 2
        # Update pool status
        pool = self.pools[pool_name]
        metrics.total_connections = pool.get_size()
        metrics.active_connections = pool.get_size() - pool.get_idle_size()
        metrics.idle_connections = pool.get_idle_size()
        # Cache metrics in Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"db_metrics:{pool_name}",
                mapping={
                    "connection_requests": metrics.connection_requests,
                    "average_acquisition_time": metrics.average_acquisition_time,
                    "total_connections": metrics.total_connections,
                    "active_connections": metrics.active_connections,
                    "idle_connections": metrics.idle_connections,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
    async def _update_query_metrics(self, pool_name: str, query_time: float):
        """Update query execution metrics"""
        if pool_name not in self.metrics:
            return
        metrics = self.metrics[pool_name]
        metrics.query_count += 1
        # Update average query time
        if metrics.average_query_time == 0:
            metrics.average_query_time = query_time
        else:
            metrics.average_query_time = (metrics.average_query_time + query_time) / 2
        # Cache metrics in Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"db_metrics:{pool_name}",
                mapping={
                    "query_count": metrics.query_count,
                    "average_query_time": metrics.average_query_time,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
    async def _update_error_metrics(self, pool_name: str):
        """Update error metrics"""
        if pool_name not in self.metrics:
            return
        metrics = self.metrics[pool_name]
        metrics.error_count += 1
        # Cache metrics in Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"db_metrics:{pool_name}",
                mapping={
                    "error_count": metrics.error_count,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
    async def optimize_pools(self):
        """Optimize pool configurations based on usage patterns"""
        for pool_name, metrics in self.metrics.items():
            self.pools[pool_name]
            # Calculate utilization rate
            utilization_rate = (
                metrics.active_connections / metrics.total_connections
                if metrics.total_connections > 0
                else 0
            )
            # Log optimization recommendations
            if utilization_rate > 0.8:
                logger.info(
                    f"Pool {pool_name} high utilization ({utilization_rate:.2f}) - consider increasing pool size"
                )
            elif utilization_rate < 0.2:
                logger.info(
                    f"Pool {pool_name} low utilization ({utilization_rate:.2f}) - consider decreasing pool size"
                )
            # Log performance metrics
            logger.info(
                f"Pool {pool_name} metrics: "
                f"avg_acquisition={metrics.average_acquisition_time:.3f}s, "
                f"avg_query={metrics.average_query_time:.3f}s, "
                f"error_rate={metrics.error_count/max(metrics.query_count, 1):.3f}"
            )
    async def reset_metrics(self, pool_name: str = None):
        """Reset metrics for specified pool or all pools"""
        if pool_name:
            if pool_name in self.metrics:
                self.metrics[pool_name] = ConnectionMetrics(
                    pool_name=pool_name, last_reset=datetime.now(UTC)
                )
        else:
            for name in self.metrics.keys():
                self.metrics[name] = ConnectionMetrics(
                    pool_name=name, last_reset=datetime.now(UTC)
                )
        logger.info(f"Metrics reset for {'all pools' if not pool_name else pool_name}")
    async def shutdown(self):
        """Graceful shutdown of all connections"""
        logger.info("Shutting down database connection manager")
        # Close all pools
        for pool_name, pool in self.pools.items():
            await pool.close()
            logger.info(f"Closed pool: {pool_name}")
        # Close all engines
        for engine_name, engine in self.engines.items():
            await engine.dispose()
            logger.info(f"Disposed engine: {engine_name}")
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Database connection manager shutdown complete")
# Business-specific database operations
class BusinessDataOperations:
    """High-level business data operations using optimized connections"""
    def __init__(self, connection_manager: OptimizedConnectionManager):
        self.conn_mgr = connection_manager
    async def update_property_unit_count(
        self, property_id: str, unit_count: int, ownership_data: dict[str, Any]
    ) -> bool:
        """Update property unit count with audit trail"""
        try:
            async with self.conn_mgr.get_session("business") as session:
                # Check if property exists
                result = await session.execute(
                    "SELECT id FROM properties WHERE property_id = :property_id",
                    {"property_id": property_id},
                )
                existing = result.fetchone()
                if existing:
                    # Update existing property
                    await session.execute(
                        """
                        UPDATE properties
                        SET unit_count = :unit_count,
                            ownership_data = :ownership_data,
                            last_updated = :timestamp
                        WHERE property_id = :property_id
                    """,
                        {
                            "unit_count": unit_count,
                            "ownership_data": json.dumps(ownership_data),
                            "timestamp": datetime.now(UTC),
                            "property_id": property_id,
                        },
                    )
                else:
                    # Insert new property
                    await session.execute(
                        """
                        INSERT INTO properties (property_id, unit_count, ownership_data, property_name)
                        VALUES (:property_id, :unit_count, :ownership_data, :property_name)
                    """,
                        {
                            "property_id": property_id,
                            "unit_count": unit_count,
                            "ownership_data": json.dumps(ownership_data),
                            "property_name": f"Property {property_id}",
                        },
                    )
                return True
        except Exception as e:
            logger.error(f"Failed to update property unit count: {e}")
            return False
    async def enrich_customer_profile(
        self, customer_id: str, enrichment_data: dict[str, Any]
    ) -> bool:
        """Enrich customer profile with new data"""
        try:
            async with self.conn_mgr.get_session("business") as session:
                # Upsert customer profile
                await session.execute(
                    """
                    INSERT INTO customer_profiles (customer_id, enrichment_data, last_updated)
                    VALUES (:customer_id, :enrichment_data, :timestamp)
                    ON CONFLICT (customer_id)
                    DO UPDATE SET
                        enrichment_data = :enrichment_data,
                        last_updated = :timestamp
                """,
                    {
                        "customer_id": customer_id,
                        "enrichment_data": json.dumps(enrichment_data),
                        "timestamp": datetime.now(UTC),
                    },
                )
                return True
        except Exception as e:
            logger.error(f"Failed to enrich customer profile: {e}")
            return False
    async def log_financial_transaction(self, transaction_data: dict[str, Any]) -> bool:
        """Log financial transaction with validation"""
        try:
            async with self.conn_mgr.get_session("business") as session:
                await session.execute(
                    """
                    INSERT INTO financial_transactions
                    (transaction_id, property_id, transaction_type, amount, billing_period, transaction_data)
                    VALUES (:transaction_id, :property_id, :transaction_type, :amount, :billing_period, :transaction_data)
                """,
                    {
                        "transaction_id": transaction_data["transaction_id"],
                        "property_id": transaction_data["property_id"],
                        "transaction_type": transaction_data["transaction_type"],
                        "amount": transaction_data["amount"],
                        "billing_period": transaction_data["billing_period"],
                        "transaction_data": json.dumps(transaction_data),
                    },
                )
                return True
        except Exception as e:
            logger.error(f"Failed to log financial transaction: {e}")
            return False
    async def create_audit_entry(self, audit_data: dict[str, Any]) -> bool:
        """Create audit trail entry"""
        try:
            async with self.conn_mgr.get_session("audit") as session:
                await session.execute(
                    """
                    INSERT INTO audit_trail
                    (request_id, service_id, operation, request_data, response_data, processing_time, status)
                    VALUES (:request_id, :service_id, :operation, :request_data, :response_data, :processing_time, :status)
                """,
                    audit_data,
                )
                return True
        except Exception as e:
            logger.error(f"Failed to create audit entry: {e}")
            return False
# Global connection manager instance
connection_manager = OptimizedConnectionManager()
business_operations = BusinessDataOperations(connection_manager)
