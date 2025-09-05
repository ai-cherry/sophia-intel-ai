#!/usr/bin/env python3
"""
Lattice HR Platform Integration
Provides access to performance reviews, goals, feedback, and employee development data
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class LatticeReview:
    """Performance review data"""

    id: str
    employee_id: str
    employee_name: str
    reviewer_id: str
    reviewer_name: str
    review_cycle: str
    status: str
    rating: Optional[float]
    feedback: str
    goals_achieved: list[str]
    areas_for_improvement: list[str]
    created_at: datetime
    completed_at: Optional[datetime]


@dataclass
class LatticeGoal:
    """OKR/Goal data"""

    id: str
    owner_id: str
    owner_name: str
    title: str
    description: str
    status: str  # not_started, in_progress, completed, cancelled
    progress: float  # 0-100
    key_results: list[dict[str, Any]]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class LatticeFeedback:
    """360 Feedback data"""

    id: str
    recipient_id: str
    recipient_name: str
    giver_id: str
    giver_name: str
    feedback_type: str  # praise, constructive, request
    content: str
    tags: list[str]
    visibility: str  # private, manager, public
    created_at: datetime


@dataclass
class LatticeOneOnOne:
    """1:1 meeting data"""

    id: str
    manager_id: str
    employee_id: str
    date: datetime
    agenda: list[str]
    notes: str
    action_items: list[dict[str, Any]]
    sentiment: Optional[str]  # positive, neutral, needs_attention
    duration_minutes: int


class LatticeConnector:
    """
    Lattice HR Platform Connector
    Provides comprehensive access to performance management and employee development data
    """

    def __init__(self, api_key: str = None):
        """
        Initialize Lattice connector

        Args:
            api_key: Lattice API key (or use LATTICE_API_KEY env var)
        """
        self.api_key = api_key or get_config().get(
            "LATTICE_API_KEY", "8aea9524-1849-418f-bec4-eb2d1153449f"
        )
        self.base_url = "https://api.latticehq.com/v1"  # Correct Lattice API endpoint
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.session = None

        # Cache for frequently accessed data
        self._cache = {"users": {}, "reviews": {}, "goals": {}, "last_refresh": None}

        logger.info("Lattice connector initialized")

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def test_connection(self) -> dict[str, Any]:
        """
        Test Lattice API connection

        Returns:
            Connection status and user info
        """
        try:
            async with aiohttp.ClientSession() as session, session.get(
                f"{self.base_url}/users/me", headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "connected",
                        "user": data.get("data", {}),
                        "message": "Successfully connected to Lattice",
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Connection failed: {response.status}",
                        "details": await response.text(),
                    }
        except Exception as e:
            logger.error(f"Lattice connection test failed: {e}")
            return {"status": "error", "message": str(e)}

    async def get_performance_reviews(
        self, employee_id: Optional[str] = None, cycle: Optional[str] = None
    ) -> list[LatticeReview]:
        """
        Get performance reviews

        Args:
            employee_id: Filter by specific employee
            cycle: Filter by review cycle

        Returns:
            List of performance reviews
        """
        params = {}
        if employee_id:
            params["employee_id"] = employee_id
        if cycle:
            params["cycle"] = cycle

        try:
            async with aiohttp.ClientSession() as session, session.get(
                f"{self.base_url}/reviews", headers=self.headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    reviews = []
                    for item in data.get("data", []):
                        review = LatticeReview(
                            id=item["id"],
                            employee_id=item["employee_id"],
                            employee_name=item.get("employee_name", "Unknown"),
                            reviewer_id=item["reviewer_id"],
                            reviewer_name=item.get("reviewer_name", "Unknown"),
                            review_cycle=item["cycle"],
                            status=item["status"],
                            rating=item.get("rating"),
                            feedback=item.get("feedback", ""),
                            goals_achieved=item.get("goals_achieved", []),
                            areas_for_improvement=item.get("areas_for_improvement", []),
                            created_at=datetime.fromisoformat(item["created_at"]),
                            completed_at=datetime.fromisoformat(item["completed_at"])
                            if item.get("completed_at")
                            else None,
                        )
                        reviews.append(review)
                    return reviews
                else:
                    logger.error(f"Failed to get reviews: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching performance reviews: {e}")
            return []

    async def get_goals(
        self, owner_id: Optional[str] = None, status: Optional[str] = None
    ) -> list[LatticeGoal]:
        """
        Get OKRs and goals

        Args:
            owner_id: Filter by goal owner
            status: Filter by status (not_started, in_progress, completed)

        Returns:
            List of goals
        """
        params = {}
        if owner_id:
            params["owner_id"] = owner_id
        if status:
            params["status"] = status

        try:
            async with aiohttp.ClientSession() as session, session.get(
                f"{self.base_url}/goals", headers=self.headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    goals = []
                    for item in data.get("data", []):
                        goal = LatticeGoal(
                            id=item["id"],
                            owner_id=item["owner_id"],
                            owner_name=item.get("owner_name", "Unknown"),
                            title=item["title"],
                            description=item.get("description", ""),
                            status=item["status"],
                            progress=item.get("progress", 0),
                            key_results=item.get("key_results", []),
                            due_date=datetime.fromisoformat(item["due_date"])
                            if item.get("due_date")
                            else None,
                            created_at=datetime.fromisoformat(item["created_at"]),
                            updated_at=datetime.fromisoformat(item["updated_at"]),
                        )
                        goals.append(goal)
                    return goals
                else:
                    logger.error(f"Failed to get goals: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching goals: {e}")
            return []

    async def get_feedback(
        self,
        recipient_id: Optional[str] = None,
        giver_id: Optional[str] = None,
        feedback_type: Optional[str] = None,
    ) -> list[LatticeFeedback]:
        """
        Get 360 feedback

        Args:
            recipient_id: Filter by feedback recipient
            giver_id: Filter by feedback giver
            feedback_type: Filter by type (praise, constructive, request)

        Returns:
            List of feedback entries
        """
        params = {}
        if recipient_id:
            params["recipient_id"] = recipient_id
        if giver_id:
            params["giver_id"] = giver_id
        if feedback_type:
            params["type"] = feedback_type

        try:
            async with aiohttp.ClientSession() as session, session.get(
                f"{self.base_url}/feedback", headers=self.headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    feedback_list = []
                    for item in data.get("data", []):
                        feedback = LatticeFeedback(
                            id=item["id"],
                            recipient_id=item["recipient_id"],
                            recipient_name=item.get("recipient_name", "Unknown"),
                            giver_id=item["giver_id"],
                            giver_name=item.get("giver_name", "Unknown"),
                            feedback_type=item["type"],
                            content=item["content"],
                            tags=item.get("tags", []),
                            visibility=item.get("visibility", "private"),
                            created_at=datetime.fromisoformat(item["created_at"]),
                        )
                        feedback_list.append(feedback)
                    return feedback_list
                else:
                    logger.error(f"Failed to get feedback: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching feedback: {e}")
            return []

    async def get_one_on_ones(
        self,
        manager_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[LatticeOneOnOne]:
        """
        Get 1:1 meeting data

        Args:
            manager_id: Filter by manager
            employee_id: Filter by employee
            start_date: Filter by date range start
            end_date: Filter by date range end

        Returns:
            List of 1:1 meetings
        """
        params = {}
        if manager_id:
            params["manager_id"] = manager_id
        if employee_id:
            params["employee_id"] = employee_id
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        try:
            async with aiohttp.ClientSession() as session, session.get(
                f"{self.base_url}/one-on-ones", headers=self.headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    meetings = []
                    for item in data.get("data", []):
                        meeting = LatticeOneOnOne(
                            id=item["id"],
                            manager_id=item["manager_id"],
                            employee_id=item["employee_id"],
                            date=datetime.fromisoformat(item["date"]),
                            agenda=item.get("agenda", []),
                            notes=item.get("notes", ""),
                            action_items=item.get("action_items", []),
                            sentiment=item.get("sentiment"),
                            duration_minutes=item.get("duration_minutes", 30),
                        )
                        meetings.append(meeting)
                    return meetings
                else:
                    logger.error(f"Failed to get 1:1s: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching 1:1 meetings: {e}")
            return []

    async def get_engagement_scores(self) -> dict[str, Any]:
        """
        Get employee engagement survey scores and insights

        Returns:
            Engagement metrics and trends
        """
        try:
            async with aiohttp.ClientSession() as session, session.get(
                f"{self.base_url}/engagement/scores", headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "overall_score": data.get("overall_score"),
                        "participation_rate": data.get("participation_rate"),
                        "trends": data.get("trends", []),
                        "top_drivers": data.get("top_drivers", []),
                        "areas_for_improvement": data.get("areas_for_improvement", []),
                    }
                else:
                    logger.error(f"Failed to get engagement scores: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching engagement scores: {e}")
            return {}

    async def get_team_insights(self, team_id: Optional[str] = None) -> dict[str, Any]:
        """
        Get aggregated team performance insights

        Args:
            team_id: Specific team to analyze

        Returns:
            Team performance metrics and insights
        """
        # Aggregate data from multiple sources
        reviews = await self.get_performance_reviews()
        goals = await self.get_goals()
        feedback = await self.get_feedback()

        # Calculate team metrics
        avg_rating = (
            sum(r.rating for r in reviews if r.rating) / len([r for r in reviews if r.rating])
            if reviews
            else 0
        )
        goal_completion_rate = (
            len([g for g in goals if g.status == "completed"]) / len(goals) * 100 if goals else 0
        )
        feedback_sentiment = self._analyze_feedback_sentiment(feedback)

        return {
            "team_id": team_id,
            "performance_metrics": {
                "average_rating": avg_rating,
                "total_reviews": len(reviews),
                "goal_completion_rate": goal_completion_rate,
                "active_goals": len([g for g in goals if g.status == "in_progress"]),
            },
            "feedback_insights": {
                "total_feedback": len(feedback),
                "praise_count": len([f for f in feedback if f.feedback_type == "praise"]),
                "constructive_count": len(
                    [f for f in feedback if f.feedback_type == "constructive"]
                ),
                "sentiment": feedback_sentiment,
            },
            "top_performers": self._identify_top_performers(reviews, goals, feedback),
            "development_areas": self._identify_development_areas(reviews),
        }

    def _analyze_feedback_sentiment(self, feedback: list[LatticeFeedback]) -> str:
        """
        Analyze overall feedback sentiment
        """
        if not feedback:
            return "neutral"

        praise_count = len([f for f in feedback if f.feedback_type == "praise"])
        constructive_count = len([f for f in feedback if f.feedback_type == "constructive"])

        if praise_count > constructive_count * 2:
            return "very_positive"
        elif praise_count > constructive_count:
            return "positive"
        elif constructive_count > praise_count * 2:
            return "needs_attention"
        else:
            return "balanced"

    def _identify_top_performers(
        self,
        reviews: list[LatticeReview],
        goals: list[LatticeGoal],
        feedback: list[LatticeFeedback],
    ) -> list[dict[str, Any]]:
        """
        Identify top performing employees based on multiple metrics
        """
        employee_scores = {}

        # Score based on reviews
        for review in reviews:
            if review.rating:
                if review.employee_id not in employee_scores:
                    employee_scores[review.employee_id] = {
                        "name": review.employee_name,
                        "score": 0,
                        "metrics": {},
                    }
                employee_scores[review.employee_id]["score"] += review.rating
                employee_scores[review.employee_id]["metrics"]["review_rating"] = review.rating

        # Score based on goal completion
        for goal in goals:
            if goal.status == "completed":
                if goal.owner_id not in employee_scores:
                    employee_scores[goal.owner_id] = {
                        "name": goal.owner_name,
                        "score": 0,
                        "metrics": {},
                    }
                employee_scores[goal.owner_id]["score"] += 1
                employee_scores[goal.owner_id]["metrics"]["goals_completed"] = (
                    employee_scores[goal.owner_id]["metrics"].get("goals_completed", 0) + 1
                )

        # Score based on positive feedback
        for f in feedback:
            if f.feedback_type == "praise":
                if f.recipient_id not in employee_scores:
                    employee_scores[f.recipient_id] = {
                        "name": f.recipient_name,
                        "score": 0,
                        "metrics": {},
                    }
                employee_scores[f.recipient_id]["score"] += 0.5
                employee_scores[f.recipient_id]["metrics"]["praise_received"] = (
                    employee_scores[f.recipient_id]["metrics"].get("praise_received", 0) + 1
                )

        # Sort and return top performers
        sorted_performers = sorted(
            employee_scores.items(), key=lambda x: x[1]["score"], reverse=True
        )

        return [
            {
                "employee_id": emp_id,
                "name": data["name"],
                "performance_score": data["score"],
                "metrics": data["metrics"],
            }
            for emp_id, data in sorted_performers[:5]
        ]

    def _identify_development_areas(self, reviews: list[LatticeReview]) -> list[str]:
        """
        Identify common areas for improvement across reviews
        """
        all_areas = []
        for review in reviews:
            all_areas.extend(review.areas_for_improvement)

        # Count frequency of each area
        area_counts = {}
        for area in all_areas:
            area_counts[area] = area_counts.get(area, 0) + 1

        # Sort by frequency and return top areas
        sorted_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)
        return [area for area, _ in sorted_areas[:5]]

    async def export_for_brain_training(self) -> dict[str, Any]:
        """
        Export all Lattice data formatted for Sophia's brain training

        Returns:
            Formatted data for ingestion
        """
        logger.info("Exporting Lattice data for brain training")

        # Gather all data
        reviews = await self.get_performance_reviews()
        goals = await self.get_goals()
        feedback = await self.get_feedback()
        one_on_ones = await self.get_one_on_ones()
        engagement = await self.get_engagement_scores()
        team_insights = await self.get_team_insights()

        return {
            "source": "lattice",
            "type": "hr_performance_data",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "performance_reviews": [
                    {
                        "id": r.id,
                        "employee": r.employee_name,
                        "rating": r.rating,
                        "feedback": r.feedback,
                        "goals_achieved": r.goals_achieved,
                        "areas_for_improvement": r.areas_for_improvement,
                    }
                    for r in reviews
                ],
                "goals": [
                    {
                        "id": g.id,
                        "owner": g.owner_name,
                        "title": g.title,
                        "progress": g.progress,
                        "status": g.status,
                        "key_results": g.key_results,
                    }
                    for g in goals
                ],
                "feedback_360": [
                    {
                        "recipient": f.recipient_name,
                        "giver": f.giver_name,
                        "type": f.feedback_type,
                        "content": f.content,
                        "tags": f.tags,
                    }
                    for f in feedback
                ],
                "one_on_ones": [
                    {
                        "date": m.date.isoformat(),
                        "agenda": m.agenda,
                        "action_items": m.action_items,
                        "sentiment": m.sentiment,
                    }
                    for m in one_on_ones
                ],
                "engagement_metrics": engagement,
                "team_performance": team_insights,
            },
            "summary": {
                "total_reviews": len(reviews),
                "total_goals": len(goals),
                "total_feedback": len(feedback),
                "total_meetings": len(one_on_ones),
                "engagement_score": engagement.get("overall_score", 0),
            },
        }


# Export main class
__all__ = ["LatticeConnector", "LatticeReview", "LatticeGoal", "LatticeFeedback", "LatticeOneOnOne"]
