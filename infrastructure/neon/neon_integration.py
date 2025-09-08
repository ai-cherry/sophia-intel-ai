#!/usr/bin/env python3
"""
Badass Neon.tech PostgreSQL Integration
Leverages Scale Plan: 50GB storage, 750 compute hours, 8 CU, 5 branches, 14-day restore
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import asyncpg
import psycopg2
import requests
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NeonConfig:
    """Neon.tech configuration with Scale plan optimization"""

    api_token: str
    api_key: str
    project_id: str
    host: str
    database: str
    username: str
    password: str

    # Scale plan features
    max_storage_gb: int = 50
    max_compute_hours: int = 750
    max_compute_units: int = 8
    max_branches: int = 5
    backup_retention_days: int = 14

    @classmethod
    def from_env(cls) -> "NeonConfig":
        """Load configuration from environment variables"""
        return cls(
            api_token=os.getenv("NEON_API_TOKEN", ""),
            api_key=os.getenv("NEON_API_KEY", ""),
            project_id=os.getenv("NEON_PROJECT_ID", ""),
            host=os.getenv("NEON_HOST", ""),
            database=os.getenv("NEON_DATABASE", "sophia_ai"),
            username=os.getenv("NEON_USERNAME", ""),
            password=os.getenv("NEON_PASSWORD", ""),
        )

class NeonAPIClient:
    """Neon.tech API client for Scale plan management"""

    def __init__(self, config: NeonConfig):
        self.config = config
        self.base_url = "https://console.neon.tech/api/v2"
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json",
        }

    async def get_project_info(self) -> dict[str, Any]:
        """Get project information and usage stats"""
        try:
            response = requests.get(
                f"{self.base_url}/projects/{self.config.project_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get project info: {e}")
            return {}

    async def create_branch(
        self, branch_name: str, parent_branch: str = "main"
    ) -> dict[str, Any]:
        """Create a new database branch (Scale plan: up to 5 branches)"""
        try:
            payload = {"branch": {"name": branch_name, "parent_id": parent_branch}}

            response = requests.post(
                f"{self.base_url}/projects/{self.config.project_id}/branches",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()

            branch_info = response.json()
            logger.info(f"Created branch: {branch_name}")
            return branch_info

        except Exception as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return {}

    async def delete_branch(self, branch_id: str) -> bool:
        """Delete a database branch"""
        try:
            response = requests.delete(
                f"{self.base_url}/projects/{self.config.project_id}/branches/{branch_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            logger.info(f"Deleted branch: {branch_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete branch {branch_id}: {e}")
            return False

    async def get_usage_metrics(self) -> dict[str, Any]:
        """Get current usage metrics for Scale plan monitoring"""
        try:
            response = requests.get(
                f"{self.base_url}/projects/{self.config.project_id}/consumption",
                headers=self.headers,
            )
            response.raise_for_status()

            usage = response.json()

            # Calculate usage percentages
            storage_usage_pct = (
                usage.get("storage_gb", 0) / self.config.max_storage_gb
            ) * 100
            compute_usage_pct = (
                usage.get("compute_hours", 0) / self.config.max_compute_hours
            ) * 100

            return {
                "storage_gb": usage.get("storage_gb", 0),
                "storage_usage_percent": storage_usage_pct,
                "compute_hours": usage.get("compute_hours", 0),
                "compute_usage_percent": compute_usage_pct,
                "active_branches": usage.get("branches", 0),
                "max_branches": self.config.max_branches,
                "scale_plan_status": (
                    "optimal"
                    if storage_usage_pct < 80 and compute_usage_pct < 80
                    else "warning"
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get usage metrics: {e}")
            return {}

class NeonDatabaseManager:
    """High-performance database manager optimized for Sophia AI workloads"""

    def __init__(self, config: NeonConfig):
        self.config = config
        self.api_client = NeonAPIClient(config)
        self._connection_pool = None

    @property
    def connection_string(self) -> str:
        """Get optimized connection string with pooling"""
        return (
            f"postgresql://{self.config.username}:{self.config.password}"
            f"@{self.config.host}/{self.config.database}"
            f"?sslmode=require&application_name=sophia_ai&connect_timeout=10"
            f"&command_timeout=30&server_side_binding=true"
        )

    @property
    def pooled_connection_string(self) -> str:
        """Get pooled connection string for high-concurrency workloads"""
        return self.connection_string + "&pgbouncer=true&pool_mode=transaction"

    async def initialize_connection_pool(self, min_size: int = 5, max_size: int = 20):
        """Initialize async connection pool for high performance"""
        try:
            self._connection_pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=min_size,
                max_size=max_size,
                command_timeout=30,
                server_settings={
                    "application_name": "sophia_ai_pool",
                    "jit": "off",  # Disable JIT for faster startup
                },
            )
            logger.info(
                f"Initialized connection pool: {min_size}-{max_size} connections"
            )

        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    async def execute_query(self, query: str, params: tuple = None) -> list[dict]:
        """Execute query with connection pooling"""
        if not self._connection_pool:
            await self.initialize_connection_pool()

        try:
            async with self._connection_pool.acquire() as conn:
                if params:
                    result = await conn.fetch(query, *params)
                else:
                    result = await conn.fetch(query)

                return [dict(row) for row in result]

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def execute_transaction(self, queries: list[tuple]) -> bool:
        """Execute multiple queries in a transaction"""
        if not self._connection_pool:
            await self.initialize_connection_pool()

        try:
            async with self._connection_pool.acquire() as conn:
                async with conn.transaction():
                    for query, params in queries:
                        if params:
                            await conn.execute(query, *params)
                        else:
                            await conn.execute(query)

                logger.info(f"Transaction completed: {len(queries)} queries")
                return True

        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False

class SophiaAISchemaManager:
    """Schema manager for Sophia AI platform with optimized tables"""

    def __init__(self, db_manager: NeonDatabaseManager):
        self.db = db_manager

    async def create_sophia_schemas(self):
        """Create optimized schemas for Sophia AI platform"""

        schemas = [
            # Core platform schema
            """
            CREATE SCHEMA IF NOT EXISTS sophia_core;
            """,
            # Artemis development schema
            """
            CREATE SCHEMA IF NOT EXISTS artemis_dev;
            """,
            # Sophia business schema
            """
            CREATE SCHEMA IF NOT EXISTS sophia_business;
            """,
            # Shared resources schema
            """
            CREATE SCHEMA IF NOT EXISTS shared_resources;
            """,
            # Analytics and metrics schema
            """
            CREATE SCHEMA IF NOT EXISTS analytics;
            """,
        ]

        for schema in schemas:
            await self.db.execute_query(schema)

        logger.info("Created Sophia AI schemas")

    async def create_core_tables(self):
        """Create core tables optimized for Scale plan performance"""

        tables = [
            # Agent registry and performance tracking
            """
            CREATE TABLE IF NOT EXISTS sophia_core.agents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL UNIQUE,
                type VARCHAR(50) NOT NULL,
                platform VARCHAR(20) NOT NULL CHECK (platform IN ('artemis', 'sophia', 'shared')),
                status VARCHAR(20) DEFAULT 'active',
                capabilities JSONB NOT NULL,
                performance_metrics JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_agents_platform ON sophia_core.agents(platform);
            CREATE INDEX IF NOT EXISTS idx_agents_type ON sophia_core.agents(type);
            CREATE INDEX IF NOT EXISTS idx_agents_status ON sophia_core.agents(status);
            """,
            # Task execution and orchestration
            """
            CREATE TABLE IF NOT EXISTS sophia_core.tasks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id UUID REFERENCES sophia_core.agents(id),
                task_type VARCHAR(100) NOT NULL,
                priority INTEGER DEFAULT 5,
                status VARCHAR(20) DEFAULT 'pending',
                input_data JSONB NOT NULL,
                output_data JSONB DEFAULT '{}',
                execution_time_ms INTEGER,
                error_message TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON sophia_core.tasks(agent_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON sophia_core.tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON sophia_core.tasks(created_at);
            """,
            # Memory and context storage
            """
            CREATE TABLE IF NOT EXISTS shared_resources.memory_contexts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                context_type VARCHAR(50) NOT NULL,
                context_key VARCHAR(200) NOT NULL,
                content JSONB NOT NULL,
                embedding VECTOR(1536), -- OpenAI embedding dimension
                metadata JSONB DEFAULT '{}',
                expires_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_memory_context_type ON shared_resources.memory_contexts(context_type);
            CREATE INDEX IF NOT EXISTS idx_memory_context_key ON shared_resources.memory_contexts(context_key);
            CREATE INDEX IF NOT EXISTS idx_memory_expires_at ON shared_resources.memory_contexts(expires_at);
            """,
            # Business intelligence data (Sophia)
            """
            CREATE TABLE IF NOT EXISTS sophia_business.customer_insights (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                customer_id VARCHAR(100) NOT NULL,
                insight_type VARCHAR(50) NOT NULL,
                insight_data JSONB NOT NULL,
                confidence_score DECIMAL(3,2),
                source_system VARCHAR(50),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_customer_insights_customer_id ON sophia_business.customer_insights(customer_id);
            CREATE INDEX IF NOT EXISTS idx_customer_insights_type ON sophia_business.customer_insights(insight_type);
            """,
            # Development metrics (Artemis)
            """
            CREATE TABLE IF NOT EXISTS artemis_dev.code_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                repository VARCHAR(200) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                metric_type VARCHAR(50) NOT NULL,
                metric_value DECIMAL(10,2),
                metadata JSONB DEFAULT '{}',
                measured_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_code_metrics_repo ON artemis_dev.code_metrics(repository);
            CREATE INDEX IF NOT EXISTS idx_code_metrics_type ON artemis_dev.code_metrics(metric_type);
            """,
            # Analytics and performance tracking
            """
            CREATE TABLE IF NOT EXISTS analytics.platform_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                metric_name VARCHAR(100) NOT NULL,
                metric_value DECIMAL(15,4),
                dimensions JSONB DEFAULT '{}',
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_platform_metrics_name ON analytics.platform_metrics(metric_name);
            CREATE INDEX IF NOT EXISTS idx_platform_metrics_timestamp ON analytics.platform_metrics(timestamp);
            """,
        ]

        for table_sql in tables:
            await self.db.execute_query(table_sql)

        logger.info("Created Sophia AI core tables")

    async def create_vector_extensions(self):
        """Enable vector extensions for AI workloads"""

        extensions = [
            "CREATE EXTENSION IF NOT EXISTS vector;",
            "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;",
            "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            "CREATE EXTENSION IF NOT EXISTS btree_gin;",
            "CREATE EXTENSION IF NOT EXISTS uuid-ossp;",
        ]

        for ext in extensions:
            try:
                await self.db.execute_query(ext)
            except Exception as e:
                logger.warning(f"Extension creation failed (may already exist): {e}")

        logger.info("Enabled PostgreSQL extensions for AI workloads")

class NeonOptimizer:
    """Performance optimizer for Neon Scale plan"""

    def __init__(self, db_manager: NeonDatabaseManager):
        self.db = db_manager
        self.api_client = db_manager.api_client

    async def optimize_for_scale_plan(self):
        """Apply optimizations specific to Neon Scale plan"""

        optimizations = [
            # Connection pooling settings
            "ALTER SYSTEM SET max_connections = 200;",
            "ALTER SYSTEM SET shared_buffers = '256MB';",
            "ALTER SYSTEM SET effective_cache_size = '1GB';",
            "ALTER SYSTEM SET work_mem = '16MB';",
            "ALTER SYSTEM SET maintenance_work_mem = '128MB';",
            # Query optimization
            "ALTER SYSTEM SET random_page_cost = 1.1;",
            "ALTER SYSTEM SET seq_page_cost = 1.0;",
            "ALTER SYSTEM SET cpu_tuple_cost = 0.01;",
            # Autovacuum tuning for AI workloads
            "ALTER SYSTEM SET autovacuum_max_workers = 4;",
            "ALTER SYSTEM SET autovacuum_naptime = '30s';",
            "ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;",
            "ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;",
            # Logging for monitoring
            "ALTER SYSTEM SET log_min_duration_statement = 1000;",
            "ALTER SYSTEM SET log_checkpoints = on;",
            "ALTER SYSTEM SET log_connections = on;",
            "ALTER SYSTEM SET log_disconnections = on;",
        ]

        for optimization in optimizations:
            try:
                await self.db.execute_query(optimization)
            except Exception as e:
                logger.warning(f"Optimization failed: {e}")

        # Reload configuration
        await self.db.execute_query("SELECT pg_reload_conf();")
        logger.info("Applied Neon Scale plan optimizations")

    async def monitor_usage(self) -> dict[str, Any]:
        """Monitor usage against Scale plan limits"""

        usage_metrics = await self.api_client.get_usage_metrics()

        # Database-level metrics
        db_metrics = await self.db.execute_query(
            """
            SELECT
                pg_size_pretty(pg_database_size(current_database())) as database_size,
                (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                (SELECT count(*) FROM pg_stat_activity) as total_connections
        """
        )

        # Combine metrics
        combined_metrics = {
            **usage_metrics,
            "database_metrics": db_metrics[0] if db_metrics else {},
            "optimization_recommendations": [],
        }

        # Generate recommendations
        if usage_metrics.get("storage_usage_percent", 0) > 80:
            combined_metrics["optimization_recommendations"].append(
                "Storage usage >80%. Consider data archival or cleanup."
            )

        if usage_metrics.get("compute_usage_percent", 0) > 80:
            combined_metrics["optimization_recommendations"].append(
                "Compute usage >80%. Consider query optimization or scaling."
            )

        return combined_metrics

async def main():
    """Main function for testing Neon integration"""

    # Load configuration
    config = NeonConfig.from_env()

    if not all([config.api_token, config.project_id, config.host]):
        logger.error(
            "Missing required Neon configuration. Check environment variables."
        )
        return

    # Initialize database manager
    db_manager = NeonDatabaseManager(config)

    try:
        # Initialize connection pool
        await db_manager.initialize_connection_pool()

        # Initialize schema manager
        schema_manager = SophiaAISchemaManager(db_manager)

        # Create schemas and tables
        await schema_manager.create_vector_extensions()
        await schema_manager.create_sophia_schemas()
        await schema_manager.create_core_tables()

        # Apply optimizations
        optimizer = NeonOptimizer(db_manager)
        await optimizer.optimize_for_scale_plan()

        # Monitor usage
        usage = await optimizer.monitor_usage()
        logger.info(f"Neon usage: {usage}")

        logger.info("🎉 Neon.tech integration completed successfully!")

    except Exception as e:
        logger.error(f"Neon integration failed: {e}")
        raise

    finally:
        if db_manager._connection_pool:
            await db_manager._connection_pool.close()

if __name__ == "__main__":
    asyncio.run(main())
