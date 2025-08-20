"""
SOPHIA Feedback Master
Collects and manages user and agent feedback for continuous learning.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
import asyncio
from datetime import datetime, timezone
import asyncpg
import json
from dataclasses import dataclass

from .api_manager import SOPHIAAPIManager

logger = logging.getLogger(__name__)

@dataclass
class FeedbackRecord:
    """Feedback record data structure."""
    id: Optional[int] = None
    task_id: str = ""
    source: str = "user"  # user, agent, system
    rating: Optional[int] = None
    comments: Optional[str] = None
    outcome: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

@dataclass
class FeedbackSummary:
    """Aggregated feedback summary."""
    total_feedback: int
    average_rating: float
    rating_distribution: Dict[int, int]
    common_issues: List[str]
    improvement_suggestions: List[str]
    time_period: str

class SOPHIAFeedbackMaster:
    """
    Master class for collecting and managing feedback for continuous learning.
    Stores feedback in PostgreSQL and provides analytics capabilities.
    """
    
    def __init__(self):
        """Initialize feedback master with database connection."""
        self.api_manager = SOPHIAAPIManager()
        self.db_pool = None
        self.redis_client = None
        
        # Database configuration
        self.postgres_dsn = os.getenv("NEON_POSTGRES_DSN")
        self.redis_url = os.getenv("REDIS_URL")
        
        logger.info("Initialized SOPHIAFeedbackMaster")
    
    async def _get_db_pool(self) -> asyncpg.Pool:
        """Get or create database connection pool."""
        if self.db_pool is None:
            if not self.postgres_dsn:
                raise ValueError("NEON_POSTGRES_DSN environment variable not set")
            
            self.db_pool = await asyncpg.create_pool(
                self.postgres_dsn,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            
            # Ensure feedback table exists
            await self._ensure_feedback_table()
        
        return self.db_pool
    
    async def _ensure_feedback_table(self):
        """Create feedback table if it doesn't exist."""
        try:
            pool = await self._get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        id SERIAL PRIMARY KEY,
                        task_id VARCHAR(255) NOT NULL,
                        source VARCHAR(50) NOT NULL DEFAULT 'user',
                        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                        comments TEXT,
                        outcome VARCHAR(255),
                        metadata JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                
                # Create indexes for better performance
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_feedback_task_id ON feedback(task_id);
                    CREATE INDEX IF NOT EXISTS idx_feedback_source ON feedback(source);
                    CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);
                    CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp);
                """)
                
                logger.info("Feedback table and indexes ensured")
                
        except Exception as e:
            logger.error(f"Failed to ensure feedback table: {e}")
            raise
    
    async def record_user_feedback(
        self,
        task_id: str,
        rating: int,
        comments: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record user feedback for a task.
        
        Args:
            task_id: Unique identifier for the task
            rating: User rating (1-5 scale)
            comments: Optional user comments
            metadata: Additional metadata
            
        Returns:
            Feedback record with ID
        """
        try:
            if not 1 <= rating <= 5:
                raise ValueError("Rating must be between 1 and 5")
            
            pool = await self._get_db_pool()
            async with pool.acquire() as conn:
                feedback_id = await conn.fetchval("""
                    INSERT INTO feedback (task_id, source, rating, comments, metadata, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                """, task_id, "user", rating, comments, json.dumps(metadata) if metadata else None, datetime.now(timezone.utc))
                
                result = {
                    "feedback_id": feedback_id,
                    "task_id": task_id,
                    "source": "user",
                    "rating": rating,
                    "comments": comments,
                    "metadata": metadata,
                    "status": "recorded"
                }
                
                logger.info(f"Recorded user feedback: {feedback_id} for task {task_id}")
                
                # Cache recent feedback in Redis if available
                await self._cache_feedback(result)
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to record user feedback: {e}")
            raise
    
    async def record_agent_feedback(
        self,
        task_id: str,
        outcome: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record agent feedback for a task outcome.
        
        Args:
            task_id: Unique identifier for the task
            outcome: Task outcome (success, failure, partial, etc.)
            metadata: Additional metadata (execution time, errors, etc.)
            
        Returns:
            Feedback record with ID
        """
        try:
            pool = await self._get_db_pool()
            async with pool.acquire() as conn:
                feedback_id = await conn.fetchval("""
                    INSERT INTO feedback (task_id, source, outcome, metadata, timestamp)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                """, task_id, "agent", outcome, json.dumps(metadata) if metadata else None, datetime.now(timezone.utc))
                
                result = {
                    "feedback_id": feedback_id,
                    "task_id": task_id,
                    "source": "agent",
                    "outcome": outcome,
                    "metadata": metadata,
                    "status": "recorded"
                }
                
                logger.info(f"Recorded agent feedback: {feedback_id} for task {task_id}")
                
                # Cache recent feedback in Redis if available
                await self._cache_feedback(result)
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to record agent feedback: {e}")
            raise
    
    async def get_feedback(
        self,
        task_id: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FeedbackRecord]:
        """
        Retrieve feedback records with optional filtering.
        
        Args:
            task_id: Filter by specific task ID
            source: Filter by feedback source (user, agent, system)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of feedback records
        """
        try:
            pool = await self._get_db_pool()
            async with pool.acquire() as conn:
                query = "SELECT * FROM feedback WHERE 1=1"
                params = []
                param_count = 0
                
                if task_id:
                    param_count += 1
                    query += f" AND task_id = ${param_count}"
                    params.append(task_id)
                
                if source:
                    param_count += 1
                    query += f" AND source = ${param_count}"
                    params.append(source)
                
                query += f" ORDER BY timestamp DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
                params.extend([limit, offset])
                
                rows = await conn.fetch(query, *params)
                
                feedback_records = []
                for row in rows:
                    metadata = json.loads(row['metadata']) if row['metadata'] else None
                    feedback_records.append(FeedbackRecord(
                        id=row['id'],
                        task_id=row['task_id'],
                        source=row['source'],
                        rating=row['rating'],
                        comments=row['comments'],
                        outcome=row['outcome'],
                        metadata=metadata,
                        timestamp=row['timestamp']
                    ))
                
                logger.info(f"Retrieved {len(feedback_records)} feedback records")
                return feedback_records
                
        except Exception as e:
            logger.error(f"Failed to retrieve feedback: {e}")
            raise
    
    async def aggregate_feedback(
        self,
        days: int = 30,
        source: Optional[str] = None
    ) -> FeedbackSummary:
        """
        Aggregate feedback metrics over a time period.
        
        Args:
            days: Number of days to look back
            source: Filter by feedback source
            
        Returns:
            Aggregated feedback summary
        """
        try:
            pool = await self._get_db_pool()
            async with pool.acquire() as conn:
                # Base query conditions
                query_conditions = "WHERE timestamp >= NOW() - INTERVAL '%s days'"
                params = [days]
                
                if source:
                    query_conditions += " AND source = $2"
                    params.append(source)
                
                # Get total feedback count
                total_query = f"SELECT COUNT(*) FROM feedback {query_conditions}"
                total_feedback = await conn.fetchval(total_query, *params)
                
                # Get average rating (only for user feedback with ratings)
                rating_query = f"""
                    SELECT AVG(rating)::FLOAT, COUNT(rating)
                    FROM feedback 
                    {query_conditions} AND rating IS NOT NULL
                """
                rating_result = await conn.fetchrow(rating_query, *params)
                average_rating = rating_result[0] or 0.0
                
                # Get rating distribution
                distribution_query = f"""
                    SELECT rating, COUNT(*) 
                    FROM feedback 
                    {query_conditions} AND rating IS NOT NULL
                    GROUP BY rating
                    ORDER BY rating
                """
                distribution_rows = await conn.fetch(distribution_query, *params)
                rating_distribution = {row[0]: row[1] for row in distribution_rows}
                
                # Get common issues from comments (simple keyword analysis)
                comments_query = f"""
                    SELECT comments 
                    FROM feedback 
                    {query_conditions} AND comments IS NOT NULL AND comments != ''
                """
                comments_rows = await conn.fetch(comments_query, *params)
                common_issues = self._extract_common_issues([row[0] for row in comments_rows])
                
                # Get improvement suggestions
                improvement_suggestions = self._generate_improvement_suggestions(
                    average_rating, rating_distribution, common_issues
                )
                
                summary = FeedbackSummary(
                    total_feedback=total_feedback,
                    average_rating=average_rating,
                    rating_distribution=rating_distribution,
                    common_issues=common_issues,
                    improvement_suggestions=improvement_suggestions,
                    time_period=f"Last {days} days"
                )
                
                logger.info(f"Generated feedback summary for {days} days: {total_feedback} records, avg rating {average_rating:.2f}")
                return summary
                
        except Exception as e:
            logger.error(f"Failed to aggregate feedback: {e}")
            raise
    
    async def get_task_feedback_summary(self, task_id: str) -> Dict[str, Any]:
        """
        Get feedback summary for a specific task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task-specific feedback summary
        """
        try:
            feedback_records = await self.get_feedback(task_id=task_id)
            
            if not feedback_records:
                return {
                    "task_id": task_id,
                    "total_feedback": 0,
                    "user_feedback": [],
                    "agent_feedback": [],
                    "average_rating": None
                }
            
            user_feedback = [r for r in feedback_records if r.source == "user"]
            agent_feedback = [r for r in feedback_records if r.source == "agent"]
            
            # Calculate average rating from user feedback
            ratings = [r.rating for r in user_feedback if r.rating is not None]
            average_rating = sum(ratings) / len(ratings) if ratings else None
            
            return {
                "task_id": task_id,
                "total_feedback": len(feedback_records),
                "user_feedback": len(user_feedback),
                "agent_feedback": len(agent_feedback),
                "average_rating": average_rating,
                "latest_feedback": feedback_records[0].timestamp if feedback_records else None,
                "user_comments": [r.comments for r in user_feedback if r.comments],
                "agent_outcomes": [r.outcome for r in agent_feedback if r.outcome]
            }
            
        except Exception as e:
            logger.error(f"Failed to get task feedback summary: {e}")
            raise
    
    def _extract_common_issues(self, comments: List[str]) -> List[str]:
        """Extract common issues from user comments using simple keyword analysis."""
        if not comments:
            return []
        
        # Simple keyword-based issue detection
        issue_keywords = {
            "slow": "Performance issues",
            "error": "Error handling",
            "confusing": "User experience",
            "wrong": "Accuracy issues",
            "incomplete": "Completeness issues",
            "timeout": "Timeout issues",
            "crash": "Stability issues"
        }
        
        issue_counts = {}
        for comment in comments:
            comment_lower = comment.lower()
            for keyword, issue_type in issue_keywords.items():
                if keyword in comment_lower:
                    issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        # Return top 5 most common issues
        return sorted(issue_counts.keys(), key=lambda x: issue_counts[x], reverse=True)[:5]
    
    def _generate_improvement_suggestions(
        self,
        average_rating: float,
        rating_distribution: Dict[int, int],
        common_issues: List[str]
    ) -> List[str]:
        """Generate improvement suggestions based on feedback analysis."""
        suggestions = []
        
        if average_rating < 3.0:
            suggestions.append("Focus on addressing fundamental issues - average rating is below acceptable threshold")
        elif average_rating < 4.0:
            suggestions.append("Good performance but room for improvement - target specific pain points")
        
        # Analyze rating distribution
        total_ratings = sum(rating_distribution.values())
        if total_ratings > 0:
            low_ratings = rating_distribution.get(1, 0) + rating_distribution.get(2, 0)
            if low_ratings / total_ratings > 0.2:
                suggestions.append("High percentage of low ratings - investigate root causes")
        
        # Address common issues
        for issue in common_issues[:3]:  # Top 3 issues
            if "Performance" in issue:
                suggestions.append("Optimize response times and system performance")
            elif "Error" in issue:
                suggestions.append("Improve error handling and user feedback")
            elif "User experience" in issue:
                suggestions.append("Enhance user interface and interaction design")
            elif "Accuracy" in issue:
                suggestions.append("Review and improve model accuracy and validation")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    async def _cache_feedback(self, feedback: Dict[str, Any]):
        """Cache recent feedback in Redis for quick access."""
        try:
            if not self.redis_url:
                return
            
            # Simple caching - store last 100 feedback items
            # In production, you might want to use a proper Redis client
            logger.debug(f"Would cache feedback {feedback['feedback_id']} in Redis")
            
        except Exception as e:
            logger.warning(f"Failed to cache feedback: {e}")
    
    async def export_feedback_data(
        self,
        format: str = "json",
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Export feedback data for analysis.
        
        Args:
            format: Export format (json, csv)
            days: Number of days to export
            
        Returns:
            Exported feedback data
        """
        try:
            feedback_records = await self.get_feedback(limit=10000)  # Large limit for export
            summary = await self.aggregate_feedback(days=days)
            
            export_data = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "time_period": f"Last {days} days",
                "summary": {
                    "total_feedback": summary.total_feedback,
                    "average_rating": summary.average_rating,
                    "rating_distribution": summary.rating_distribution,
                    "common_issues": summary.common_issues,
                    "improvement_suggestions": summary.improvement_suggestions
                },
                "records": []
            }
            
            for record in feedback_records:
                export_data["records"].append({
                    "id": record.id,
                    "task_id": record.task_id,
                    "source": record.source,
                    "rating": record.rating,
                    "comments": record.comments,
                    "outcome": record.outcome,
                    "metadata": record.metadata,
                    "timestamp": record.timestamp.isoformat() if record.timestamp else None
                })
            
            logger.info(f"Exported {len(feedback_records)} feedback records")
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export feedback data: {e}")
            raise
    
    async def close(self):
        """Close database connections."""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Closed feedback master database connections")

