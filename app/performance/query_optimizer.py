import logging
import time
from typing import Any, Optional, Union

import asyncpg

from app.observability.prometheus_metrics import (
    db_connection_pool_size,
    db_query_duration_seconds,
    db_slow_queries_total,
)

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Advanced database performance optimization"""

    def __init__(self, connection_string: str, pool_size: int = 10):
        self.connection_string = connection_string
        self.pool = None
        self.pool_size = pool_size
        self.query_cache = {}
        self.performance_metrics = {
            "slow_queries": [],
            "query_analysis": {}
        }

    async def initialize_connection_pool(self) -> None:
        """Initialize asynchronous connection pool with performance tracking"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=self.pool_size,
                max_size=self.pool_size * 2,
                timeout=30.0
            )
            db_connection_pool_size.set(self.pool_size * 2)
            logger.info(f"Database connection pool initialized with size: {self.pool_size}")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {str(e)}")
            raise

    async def execute_with_timing(self, query: str, *args, **kwargs) -> Any:
        """Execute a database query with performance timing"""
        start_time = time.time()
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(query, *args, **kwargs)
            duration = time.time() - start_time
            db_query_duration_seconds.observe(duration)

            # Track slow queries
            if duration > 0.5:
                slow_query_info = {
                    "query": query,
                    "duration": duration,
                    "parameters": list(args) + list(kwargs.items())
                }
                self.performance_metrics["slow_queries"].append(slow_query_info)
                db_slow_queries_total.inc()
                logger.warning(f"Slow query detected: {duration} seconds - {query}")

            return result
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            raise

    async def analyze_slow_queries(self) -> dict[str, Any]:
        """Analyze historical slow queries and provide optimization suggestions"""
        slow_queries = self.performance_metrics["slow_queries"]

        if not slow_queries:
            logger.info("No slow queries detected for analysis")
            return {
                "has_slow_queries": False,
                "suggestions": []
            }

        # Analyze the slow queries
        analysis = {
            "has_slow_queries": True,
            "analysis_summary": {},
            "suggestions": []
        }

        # Count query types
        query_counts = {}
        for q in slow_queries:
            query_key = q["query"].split()[0].upper()
            query_counts[query_key] = query_counts.get(query_key, 0) + 1

        analysis["analysis_summary"]["query_type_distribution"] = query_counts

        # Create optimization suggestions based on patterns
        for i, q in enumerate(slow_queries[:5]):  # Top 5 slowest queries
            suggestion = self._generate_query_suggestion(q)
            if suggestion:
                analysis["suggestions"].append(suggestion)

        self.performance_metrics["query_analysis"] = analysis
        return analysis

    async def recommend_index_optimizations(self) -> list[dict[str, str]]:
        """Recommend specific database index optimizations based on slow queries"""
        # This would typically analyze actual query patterns and table schemas
        # For now, return mock suggestions based on query patterns
        recommendations = []

        for q in self.performance_metrics["slow_queries"]:
            query = q["query"].lower()

            if "select" in query and "where" in query and "id" in query:
                recommendations.append({
                    "query_pattern": "SELECT ... WHERE id = ?",
                    "suggestion": "Add index on 'id' column"
                })

            if "join" in query and "timestamp" in query:
                recommendations.append({
                    "query_pattern": "JOIN ... ON timestamp",
                    "suggestion": "Add composite index on timestamp and related columns"
                })

        return recommendations

    def _generate_query_suggestion(self, slow_query: dict[str, Any]) -> Optional[dict[str, str]]:
        """Generate a specific optimization suggestion for a slow query"""
        query = slow_query["query"].lower()
        duration = slow_query["duration"]

        # Analyze the query pattern for optimization opportunities
        if duration > 2.0:  # Very slow queries
            if "join" in query:
                return {
                    "issue": "Complex joins",
                    "suggestion": "Simplify or break down complex JOIN operations"
                }
            elif "order by" in query and "limit" not in query:
                return {
                    "issue": "Non-limited sorting",
                    "suggestion": "Add LIMIT clause to ORDER BY operations"
                }
            elif "distinct" in query and len(query) > 200:
                return {
                    "issue": "Large DISTINCT operations",
                    "suggestion": "Consider pre-aggregation or materialized views"
                }

        return None

