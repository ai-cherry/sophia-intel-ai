"""
Linear Integration Client for Sophia Business Intelligence
Provides development project management and team productivity intelligence capabilities
This client provides comprehensive integration with Linear's GraphQL API, following the same
patterns as other integration clients in the Sophia platform. It includes:
CORE API METHODS:
- Team management: get_teams(), get_team_info()
- Issue operations: get_issues(), get_issue(), create_issue(), update_issue()
- Project management: get_projects(), get_project_info()
- User management: get_users(), get_user_info()
- Workflow states: get_workflow_states(), get_state_info()
BUSINESS INTELLIGENCE METHODS:
- analyze_development_velocity(): Comprehensive team velocity and throughput analysis
- get_issue_pattern_analysis(): Issue type, priority, and lifecycle analysis
- get_team_performance_metrics(): Team productivity and efficiency metrics
- get_project_health_dashboard(): Project status, timeline, and risk assessment
- create_intelligence_summary(): Complete BI summary for Sophia's development analysis
FEATURES:
- Async context management with resource manager integration
- GraphQL query optimization and batching
- Comprehensive error handling and authentication
- Business value calculation and scoring for development metrics
- Timezone-aware datetime handling with proper UTC conversion
- Structured logging throughout all operations
- Development velocity tracking and trend analysis
AUTHENTICATION:
Uses Bearer token authentication with API key from integrations_config.py
USAGE:
    async with LinearClient() as client:
        health = await client.get_integration_health()
        summary = await client.create_intelligence_summary()
        velocity = await client.analyze_development_velocity()
For Sophia's business intelligence analysis, use the create_intelligence_summary()
method which provides a complete overview of development health, team metrics,
and project status with business value scoring.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import aiohttp
from app.api.utils.http_client import get_async_client, with_retries
from app.orchestrators.resource_manager import ResourceType, resource_manager
from config.unified_manager import get_config_manager
logger = logging.getLogger(__name__)
 
class LinearClient:
    """
    Linear GraphQL API client for business intelligence and development project management
    """
    def __init__(self):
        cm = get_config_manager()
        cfg = cm.get_integration_config("linear")
        # Implicit enable for dev if token is provided
        if not cfg.get("enabled") and cfg.get("api_key"):
            cfg["enabled"] = True
        self.config = cfg
        if not self.config.get("enabled"):
            raise ValueError("Linear integration not enabled. Set LINEAR_ENABLED=true and provide LINEAR_API_KEY.")
        self.api_key = self.config.get("api_key")
        self.base_url = "https://api.linear.app/graphql"
        self.session: Optional[aiohttp.ClientSession] = None
        if not self.api_key:
            raise ValueError("Linear API key not configured (LINEAR_API_KEY)")
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        logger.info("🔧 Linear client initialized")
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize_session()
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()
    async def initialize_session(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
            # Register session for resource management
            try:
                await resource_manager.register_resource(
                    "linear_session",
                    ResourceType.API_CONNECTION,
                    self.session,
                    cleanup_func=self._cleanup_session,
                )
            except Exception as e:
                logger.warning(f"Failed to register session with resource manager: {e}")
                # Continue without resource manager if it fails
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    async def _cleanup_session(self, session):
        """Cleanup function for resource manager"""
        if session and not session.closed:
            await session.close()
    async def _make_graphql_request(self, query: str, variables: dict[str, Any] = None) -> dict[str, Any]:
        """Make authenticated GraphQL request to Linear API using shared HTTP client with retries."""
        payload = {"query": query, "variables": variables or {}}
        client = await get_async_client()

        async def _do():
            resp = await client.post(self.base_url, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp

        try:
            response = await with_retries(_do)
            result = response.json()
            if "errors" in result:
                msgs = "; ".join(err.get("message", "") for err in result["errors"])
                raise Exception(f"Linear GraphQL errors: {msgs}")
            return result.get("data", {})
        except Exception as e:
            logger.error(f"Linear GraphQL request failed: {e}")
            raise
    # Core API Methods
    async def get_viewer_info(self) -> dict[str, Any]:
        """Get current user (viewer) information"""
        query = """
        query {
            viewer {
                id
                name
                email
                displayName
                avatarUrl
                isMe
                active
                admin
                createdAt
                updatedAt
            }
        }
        """
        result = await self._make_graphql_request(query)
        return result.get("viewer", {})
    async def get_teams(self, first: int = 50) -> list[dict[str, Any]]:
        """Get all teams"""
        query = """
        query($first: Int!) {
            teams(first: $first) {
                nodes {
                    id
                    name
                    key
                    description
                    private
                    issueCount
                    cyclesEnabled
                    createdAt
                    updatedAt
                    members {
                        nodes {
                            id
                            name
                            displayName
                            email
                            active
                        }
                    }
                    states {
                        nodes {
                            id
                            name
                            type
                            color
                            position
                        }
                    }
                }
            }
        }
        """
        variables = {"first": first}
        result = await self._make_graphql_request(query, variables)
        return result.get("teams", {}).get("nodes", [])
    async def get_team_info(self, team_id: str) -> dict[str, Any]:
        """Get detailed team information"""
        query = """
        query($teamId: String!) {
            team(id: $teamId) {
                id
                name
                key
                description
                private
                issueCount
                cyclesEnabled
                createdAt
                updatedAt
                members {
                    nodes {
                        id
                        name
                        displayName
                        email
                        active
                        isMe
                        admin
                    }
                }
                states {
                    nodes {
                        id
                        name
                        type
                        color
                        position
                    }
                }
                projects {
                    nodes {
                        id
                        name
                        description
                        state
                        progress
                        createdAt
                        updatedAt
                    }
                }
            }
        }
        """
        variables = {"teamId": team_id}
        result = await self._make_graphql_request(query, variables)
        return result.get("team", {})
    async def get_issues(
        self, team_id: str = None, first: int = 100, filter_query: dict[str, Any] = None
    ) -> list[dict[str, Any]]:
        """Get issues with optional filtering"""
        query = """
        query($first: Int!, $filter: IssueFilter) {
            issues(first: $first, filter: $filter) {
                nodes {
                    id
                    identifier
                    title
                    description
                    priority
                    estimate
                    createdAt
                    updatedAt
                    completedAt
                    canceledAt
                    archivedAt
                    dueDate
                    assignee {
                        id
                        name
                        displayName
                        email
                    }
                    creator {
                        id
                        name
                        displayName
                    }
                    team {
                        id
                        name
                        key
                    }
                    state {
                        id
                        name
                        type
                        color
                    }
                    project {
                        id
                        name
                        state
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                    cycle {
                        id
                        name
                        number
                        startsAt
                        endsAt
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        filter_dict = {}
        if team_id:
            filter_dict["team"] = {"id": {"eq": team_id}}
        if filter_query:
            filter_dict.update(filter_query)
        variables = {"first": first, "filter": filter_dict if filter_dict else None}
        result = await self._make_graphql_request(query, variables)
        return result.get("issues", {}).get("nodes", [])
    async def get_issue(self, issue_id: str) -> dict[str, Any]:
        """Get detailed issue information"""
        query = """
        query($issueId: String!) {
            issue(id: $issueId) {
                id
                identifier
                title
                description
                priority
                estimate
                createdAt
                updatedAt
                completedAt
                canceledAt
                archivedAt
                dueDate
                url
                assignee {
                    id
                    name
                    displayName
                    email
                    active
                }
                creator {
                    id
                    name
                    displayName
                }
                team {
                    id
                    name
                    key
                }
                state {
                    id
                    name
                    type
                    color
                    position
                }
                project {
                    id
                    name
                    description
                    state
                    progress
                }
                labels {
                    nodes {
                        id
                        name
                        color
                        description
                    }
                }
                cycle {
                    id
                    name
                    number
                    startsAt
                    endsAt
                }
                comments {
                    nodes {
                        id
                        body
                        createdAt
                        updatedAt
                        user {
                            id
                            name
                            displayName
                        }
                    }
                }
                attachments {
                    nodes {
                        id
                        title
                        url
                        createdAt
                    }
                }
            }
        }
        """
        variables = {"issueId": issue_id}
        result = await self._make_graphql_request(query, variables)
        return result.get("issue", {})
    async def get_projects(
        self, team_id: str = None, first: int = 50
    ) -> list[dict[str, Any]]:
        """Get projects (simplified query to avoid complexity limits)"""
        query = """
        query($first: Int!, $filter: ProjectFilter) {
            projects(first: $first, filter: $filter) {
                nodes {
                    id
                    name
                    description
                    state
                    progress
                    url
                    createdAt
                    updatedAt
                    startedAt
                    completedAt
                    targetDate
                    creator {
                        id
                        name
                        displayName
                    }
                    lead {
                        id
                        name
                        displayName
                    }
                    teams {
                        nodes {
                            id
                            name
                            key
                        }
                    }
                }
            }
        }
        """
        filter_dict = {}
        # Note: Linear's ProjectFilter doesn't support team filtering directly
        # We'll filter projects client-side instead
        variables = {"first": first, "filter": filter_dict if filter_dict else None}
        result = await self._make_graphql_request(query, variables)
        projects = result.get("projects", {}).get("nodes", [])
        # Client-side filtering by team if specified
        if team_id:
            filtered_projects = []
            for project in projects:
                project_teams = project.get("teams", {}).get("nodes", [])
                if any(team.get("id") == team_id for team in project_teams):
                    filtered_projects.append(project)
            return filtered_projects
        return projects
    async def get_workflow_states(self, team_id: str) -> list[dict[str, Any]]:
        """Get workflow states for a team"""
        query = """
        query($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        type
                        color
                        description
                        position
                        createdAt
                        updatedAt
                    }
                }
            }
        }
        """
        variables = {"teamId": team_id}
        result = await self._make_graphql_request(query, variables)
        return result.get("team", {}).get("states", {}).get("nodes", [])
    async def get_users(self, first: int = 50) -> list[dict[str, Any]]:
        """Get all users"""
        query = """
        query($first: Int!) {
            users(first: $first) {
                nodes {
                    id
                    name
                    displayName
                    email
                    avatarUrl
                    active
                    admin
                    guest
                    createdAt
                    updatedAt
                    lastSeen
                    createdIssueCount
                }
            }
        }
        """
        variables = {"first": first}
        result = await self._make_graphql_request(query, variables)
        return result.get("users", {}).get("nodes", [])
    # Business Intelligence Methods
    async def analyze_development_velocity(
        self, team_id: str = None, days: int = 30
    ) -> dict[str, Any]:
        """Analyze development velocity and throughput metrics"""
        logger.info(f"📊 Analyzing development velocity for last {days} days...")
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()
        # Build filter for date range
        date_filter = {"updatedAt": {"gte": cutoff_iso}}
        if team_id:
            date_filter["team"] = {"id": {"eq": team_id}}
        issues = await self.get_issues(
            team_id=team_id, first=200, filter_query=date_filter
        )
        analysis = {
            "period_days": days,
            "team_id": team_id,
            "total_issues": len(issues),
            "completed_issues": 0,
            "in_progress_issues": 0,
            "todo_issues": 0,
            "canceled_issues": 0,
            "velocity_metrics": {
                "completion_rate": 0.0,
                "average_completion_time": 0.0,
                "throughput_per_week": 0.0,
                "cycle_time_distribution": [],
            },
            "priority_distribution": {
                "urgent": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "no_priority": 0,
            },
            "team_performance": {},
            "state_distribution": {},
            "estimate_accuracy": {
                "total_estimated": 0,
                "total_completed_estimated": 0,
                "average_estimate": 0.0,
                "estimate_vs_actual": [],
            },
            "health_score": 0.0,
            "recommendations": [],
        }
        completion_times = []
        estimates = []
        for issue in issues:
            # State analysis
            state = issue.get("state", {})
            state_type = state.get("type", "unknown")
            state_name = state.get("name", "Unknown")
            if state_name not in analysis["state_distribution"]:
                analysis["state_distribution"][state_name] = 0
            analysis["state_distribution"][state_name] += 1
            # Count by state type
            if state_type == "completed":
                analysis["completed_issues"] += 1
            elif state_type == "started":
                analysis["in_progress_issues"] += 1
            elif state_type == "unstarted":
                analysis["todo_issues"] += 1
            elif state_type == "canceled":
                analysis["canceled_issues"] += 1
            # Priority analysis
            priority = issue.get("priority", 0)
            if priority == 1:
                analysis["priority_distribution"]["urgent"] += 1
            elif priority == 2:
                analysis["priority_distribution"]["high"] += 1
            elif priority == 3:
                analysis["priority_distribution"]["medium"] += 1
            elif priority == 4:
                analysis["priority_distribution"]["low"] += 1
            else:
                analysis["priority_distribution"]["no_priority"] += 1
            # Team performance tracking
            assignee = issue.get("assignee", {})
            if assignee:
                assignee_name = assignee.get("displayName") or assignee.get(
                    "name", "Unknown"
                )
                if assignee_name not in analysis["team_performance"]:
                    analysis["team_performance"][assignee_name] = {
                        "total_issues": 0,
                        "completed_issues": 0,
                        "in_progress_issues": 0,
                        "completion_rate": 0.0,
                        "average_estimate": 0.0,
                    }
                analysis["team_performance"][assignee_name]["total_issues"] += 1
                if state_type == "completed":
                    analysis["team_performance"][assignee_name]["completed_issues"] += 1
                elif state_type == "started":
                    analysis["team_performance"][assignee_name][
                        "in_progress_issues"
                    ] += 1
            # Completion time analysis for completed issues
            if (
                state_type == "completed"
                and issue.get("completedAt")
                and issue.get("createdAt")
            ):
                created_at = datetime.fromisoformat(
                    issue["createdAt"].replace("Z", "+00:00")
                )
                completed_at = datetime.fromisoformat(
                    issue["completedAt"].replace("Z", "+00:00")
                )
                completion_time = (
                    completed_at - created_at
                ).total_seconds() / 86400  # Convert to days
                completion_times.append(completion_time)
                # Track estimate accuracy
                estimate = issue.get("estimate")
                if estimate and estimate > 0:
                    analysis["estimate_accuracy"]["estimate_vs_actual"].append(
                        {
                            "estimate": estimate,
                            "actual_days": completion_time,
                            "accuracy_ratio": estimate / max(completion_time, 0.1),
                        }
                    )
            # Estimate tracking
            estimate = issue.get("estimate")
            if estimate and estimate > 0:
                estimates.append(estimate)
                analysis["estimate_accuracy"]["total_estimated"] += 1
                if state_type == "completed":
                    analysis["estimate_accuracy"]["total_completed_estimated"] += 1
        # Calculate velocity metrics
        if analysis["total_issues"] > 0:
            analysis["velocity_metrics"]["completion_rate"] = (
                analysis["completed_issues"] / analysis["total_issues"]
            ) * 100
        if completion_times:
            analysis["velocity_metrics"]["average_completion_time"] = sum(
                completion_times
            ) / len(completion_times)
            analysis["velocity_metrics"]["cycle_time_distribution"] = sorted(
                completion_times
            )
        # Calculate throughput per week
        weeks_in_period = days / 7
        if weeks_in_period > 0:
            analysis["velocity_metrics"]["throughput_per_week"] = (
                analysis["completed_issues"] / weeks_in_period
            )
        # Calculate average estimate
        if estimates:
            analysis["estimate_accuracy"]["average_estimate"] = sum(estimates) / len(
                estimates
            )
        # Calculate team member completion rates
        for member_data in analysis["team_performance"].values():
            if member_data["total_issues"] > 0:
                member_data["completion_rate"] = (
                    member_data["completed_issues"] / member_data["total_issues"]
                ) * 100
        # Calculate health score (0-100)
        health_factors = []
        # Factor 1: Completion rate (40% weight)
        completion_score = min(analysis["velocity_metrics"]["completion_rate"], 40)
        health_factors.append(completion_score)
        # Factor 2: Work distribution (30% weight)
        if analysis["total_issues"] > 0:
            balanced_work = 1 - (analysis["todo_issues"] / analysis["total_issues"])
            distribution_score = balanced_work * 30
            health_factors.append(distribution_score)
        # Factor 3: Team engagement (20% weight)
        active_members = len(
            [m for m in analysis["team_performance"].values() if m["total_issues"] > 0]
        )
        engagement_score = min(
            active_members * 5, 20
        )  # 5 points per active member, cap at 20
        health_factors.append(engagement_score)
        # Factor 4: Velocity consistency (10% weight)
        if analysis["velocity_metrics"]["throughput_per_week"] > 0:
            velocity_score = min(
                analysis["velocity_metrics"]["throughput_per_week"] * 2, 10
            )
            health_factors.append(velocity_score)
        analysis["health_score"] = sum(health_factors)
        # Generate recommendations
        if analysis["velocity_metrics"]["completion_rate"] < 60:
            analysis["recommendations"].append(
                "Low completion rate - review workload and priorities"
            )
        if analysis["todo_issues"] > analysis["in_progress_issues"] * 2:
            analysis["recommendations"].append(
                "Large backlog detected - consider sprint planning improvements"
            )
        if (
            analysis["estimate_accuracy"]["total_estimated"]
            / max(analysis["total_issues"], 1)
            < 0.5
        ):
            analysis["recommendations"].append(
                "Low estimate coverage - encourage story point estimation"
            )
        if active_members < 2:
            analysis["recommendations"].append(
                "Low team engagement - review workload distribution"
            )
        return analysis
    async def get_issue_pattern_analysis(
        self, team_id: str = None, days: int = 90
    ) -> dict[str, Any]:
        """Analyze issue patterns, types, and lifecycle metrics"""
        logger.info(f"🔍 Analyzing issue patterns for last {days} days...")
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()
        date_filter = {"createdAt": {"gte": cutoff_iso}}
        if team_id:
            date_filter["team"] = {"id": {"eq": team_id}}
        issues = await self.get_issues(
            team_id=team_id, first=300, filter_query=date_filter
        )
        analysis = {
            "period_days": days,
            "team_id": team_id,
            "total_issues": len(issues),
            "label_patterns": {},
            "creator_patterns": {},
            "assignee_patterns": {},
            "priority_trends": {
                "urgent": {"count": 0, "avg_completion_time": 0},
                "high": {"count": 0, "avg_completion_time": 0},
                "medium": {"count": 0, "avg_completion_time": 0},
                "low": {"count": 0, "avg_completion_time": 0},
            },
            "lifecycle_metrics": {
                "average_time_to_start": 0.0,
                "average_time_in_progress": 0.0,
                "average_time_to_complete": 0.0,
                "bottleneck_states": {},
            },
            "project_distribution": {},
            "cycle_patterns": {},
            "issue_complexity": {
                "with_estimates": 0,
                "without_estimates": 0,
                "high_estimate_issues": 0,
                "avg_estimate": 0.0,
            },
            "collaboration_metrics": {
                "issues_with_comments": 0,
                "avg_comments_per_issue": 0.0,
                "issues_with_attachments": 0,
            },
            "insights": [],
        }
        priority_completion_times = {1: [], 2: [], 3: [], 4: []}
        time_to_complete_list = []
        estimates = []
        comment_counts = []
        for issue in issues:
            # Label analysis
            labels = issue.get("labels", {}).get("nodes", [])
            for label in labels:
                label_name = label.get("name", "Unknown")
                if label_name not in analysis["label_patterns"]:
                    analysis["label_patterns"][label_name] = {
                        "count": 0,
                        "completed": 0,
                        "avg_completion_time": 0.0,
                    }
                analysis["label_patterns"][label_name]["count"] += 1
                if issue.get("completedAt"):
                    analysis["label_patterns"][label_name]["completed"] += 1
            # Creator analysis
            creator = issue.get("creator", {})
            creator_name = creator.get("displayName") or creator.get("name", "Unknown")
            if creator_name not in analysis["creator_patterns"]:
                analysis["creator_patterns"][creator_name] = {
                    "created": 0,
                    "completed": 0,
                    "avg_priority": 0.0,
                }
            analysis["creator_patterns"][creator_name]["created"] += 1
            # Assignee analysis
            assignee = issue.get("assignee", {})
            if assignee:
                assignee_name = assignee.get("displayName") or assignee.get(
                    "name", "Unknown"
                )
                if assignee_name not in analysis["assignee_patterns"]:
                    analysis["assignee_patterns"][assignee_name] = {
                        "assigned": 0,
                        "completed": 0,
                        "avg_completion_time": 0.0,
                    }
                analysis["assignee_patterns"][assignee_name]["assigned"] += 1
            # Priority analysis
            priority = issue.get("priority", 0)
            priority_key = {1: "urgent", 2: "high", 3: "medium", 4: "low"}.get(
                priority, "low"
            )
            analysis["priority_trends"][priority_key]["count"] += 1
            # Completion time analysis by priority
            if issue.get("completedAt") and issue.get("createdAt"):
                created_at = datetime.fromisoformat(
                    issue["createdAt"].replace("Z", "+00:00")
                )
                completed_at = datetime.fromisoformat(
                    issue["completedAt"].replace("Z", "+00:00")
                )
                completion_time = (completed_at - created_at).total_seconds() / 86400
                priority_completion_times[priority].append(completion_time)
                time_to_complete_list.append(completion_time)
                if assignee:
                    assignee_name = assignee.get("displayName") or assignee.get(
                        "name", "Unknown"
                    )
                    if assignee_name in analysis["assignee_patterns"]:
                        analysis["assignee_patterns"][assignee_name]["completed"] += 1
                if creator_name in analysis["creator_patterns"]:
                    analysis["creator_patterns"][creator_name]["completed"] += 1
            # Project analysis
            project = issue.get("project", {})
            if project:
                project_name = project.get("name", "Unknown Project")
                if project_name not in analysis["project_distribution"]:
                    analysis["project_distribution"][project_name] = {
                        "total": 0,
                        "completed": 0,
                        "in_progress": 0,
                    }
                analysis["project_distribution"][project_name]["total"] += 1
                state_type = issue.get("state", {}).get("type", "unknown")
                if state_type == "completed":
                    analysis["project_distribution"][project_name]["completed"] += 1
                elif state_type == "started":
                    analysis["project_distribution"][project_name]["in_progress"] += 1
            # Cycle analysis
            cycle = issue.get("cycle", {})
            if cycle:
                cycle_name = cycle.get("name", "Unknown Cycle")
                if cycle_name not in analysis["cycle_patterns"]:
                    analysis["cycle_patterns"][cycle_name] = {
                        "total": 0,
                        "completed": 0,
                    }
                analysis["cycle_patterns"][cycle_name]["total"] += 1
                if issue.get("completedAt"):
                    analysis["cycle_patterns"][cycle_name]["completed"] += 1
            # Complexity analysis
            estimate = issue.get("estimate")
            if estimate and estimate > 0:
                analysis["issue_complexity"]["with_estimates"] += 1
                estimates.append(estimate)
                if estimate >= 5:  # Assuming 5+ is high complexity
                    analysis["issue_complexity"]["high_estimate_issues"] += 1
            else:
                analysis["issue_complexity"]["without_estimates"] += 1
            # Collaboration analysis
            comments = issue.get("comments", {}).get("nodes", [])
            if comments:
                analysis["collaboration_metrics"]["issues_with_comments"] += 1
                comment_counts.append(len(comments))
            attachments = issue.get("attachments", {}).get("nodes", [])
            if attachments:
                analysis["collaboration_metrics"]["issues_with_attachments"] += 1
        # Calculate averages
        for priority, times in priority_completion_times.items():
            if times:
                priority_key = {1: "urgent", 2: "high", 3: "medium", 4: "low"}[priority]
                analysis["priority_trends"][priority_key]["avg_completion_time"] = sum(
                    times
                ) / len(times)
        if estimates:
            analysis["issue_complexity"]["avg_estimate"] = sum(estimates) / len(
                estimates
            )
        if comment_counts:
            analysis["collaboration_metrics"]["avg_comments_per_issue"] = sum(
                comment_counts
            ) / len(comment_counts)
        if time_to_complete_list:
            analysis["lifecycle_metrics"]["average_time_to_complete"] = sum(
                time_to_complete_list
            ) / len(time_to_complete_list)
        # Generate insights
        if (
            analysis["issue_complexity"]["without_estimates"]
            > analysis["issue_complexity"]["with_estimates"]
        ):
            analysis["insights"].append(
                "Many issues lack estimates - consider improving sprint planning"
            )
        if analysis["collaboration_metrics"]["avg_comments_per_issue"] < 1:
            analysis["insights"].append(
                "Low comment activity - encourage team communication on issues"
            )
        most_active_creator = max(
            analysis["creator_patterns"].items(),
            key=lambda x: x[1]["created"],
            default=("None", {"created": 0}),
        )
        if most_active_creator[1]["created"] > 0:
            analysis["insights"].append(
                f"Most active issue creator: {most_active_creator[0]} ({most_active_creator[1]['created']} issues)"
            )
        return analysis
    async def get_team_performance_metrics(
        self, team_id: str, days: int = 30
    ) -> dict[str, Any]:
        """Get comprehensive team performance and efficiency metrics"""
        logger.info(f"📈 Analyzing team performance metrics for {days} days...")
        team_info = await self.get_team_info(team_id)
        velocity_analysis = await self.analyze_development_velocity(team_id, days)
        metrics = {
            "team_id": team_id,
            "team_name": team_info.get("name", "Unknown Team"),
            "team_key": team_info.get("key", ""),
            "period_days": days,
            "member_count": len(team_info.get("members", {}).get("nodes", [])),
            "total_issue_count": team_info.get("issueCount", 0),
            "performance_summary": {
                "health_score": velocity_analysis.get("health_score", 0),
                "completion_rate": velocity_analysis.get("velocity_metrics", {}).get(
                    "completion_rate", 0
                ),
                "throughput_per_week": velocity_analysis.get(
                    "velocity_metrics", {}
                ).get("throughput_per_week", 0),
                "avg_completion_time": velocity_analysis.get(
                    "velocity_metrics", {}
                ).get("average_completion_time", 0),
            },
            "member_performance": velocity_analysis.get("team_performance", {}),
            "workload_distribution": {
                "completed": velocity_analysis.get("completed_issues", 0),
                "in_progress": velocity_analysis.get("in_progress_issues", 0),
                "todo": velocity_analysis.get("todo_issues", 0),
                "canceled": velocity_analysis.get("canceled_issues", 0),
            },
            "priority_handling": velocity_analysis.get("priority_distribution", {}),
            "workflow_efficiency": {"states": [], "bottlenecks": []},
            "collaboration_score": 0.0,
            "recommendations": velocity_analysis.get("recommendations", []),
        }
        # Analyze workflow states
        states = team_info.get("states", {}).get("nodes", [])
        for state in states:
            state_info = {
                "name": state.get("name"),
                "type": state.get("type"),
                "color": state.get("color"),
                "position": state.get("position"),
            }
            metrics["workflow_efficiency"]["states"].append(state_info)
        # Calculate collaboration score based on member engagement
        active_members = len(
            [m for m in metrics["member_performance"].values() if m["total_issues"] > 0]
        )
        total_members = metrics["member_count"]
        if total_members > 0:
            engagement_ratio = active_members / total_members
            avg_completion_rate = sum(
                [m["completion_rate"] for m in metrics["member_performance"].values()]
            ) / max(len(metrics["member_performance"]), 1)
            metrics["collaboration_score"] = (engagement_ratio * 50) + (
                avg_completion_rate * 0.5
            )
        # Identify potential bottlenecks
        state_distribution = velocity_analysis.get("state_distribution", {})
        total_distributed = sum(state_distribution.values())
        for state_name, count in state_distribution.items():
            if (
                total_distributed > 0 and count / total_distributed > 0.4
            ):  # More than 40% in one state
                metrics["workflow_efficiency"]["bottlenecks"].append(
                    {
                        "state": state_name,
                        "issue_count": count,
                        "percentage": (count / total_distributed) * 100,
                    }
                )
        return metrics
    async def get_project_health_dashboard(self, team_id: str = None) -> dict[str, Any]:
        """Get project health dashboard with status, timeline, and risk assessment"""
        logger.info("🎯 Generating project health dashboard...")
        projects = await self.get_projects(team_id=team_id, first=50)
        dashboard = {
            "team_id": team_id,
            "total_projects": len(projects),
            "project_health": {"healthy": 0, "at_risk": 0, "critical": 0},
            "status_distribution": {
                "planned": 0,
                "started": 0,
                "paused": 0,
                "completed": 0,
                "canceled": 0,
            },
            "timeline_analysis": {
                "on_track": 0,
                "behind_schedule": 0,
                "ahead_of_schedule": 0,
                "no_timeline": 0,
            },
            "project_details": [],
            "resource_allocation": {},
            "risk_factors": [],
            "overall_health_score": 0.0,
            "recommendations": [],
        }
        now = datetime.now(timezone.utc)
        health_scores = []
        for project in projects:
            project_analysis = {
                "id": project.get("id"),
                "name": project.get("name", "Untitled Project"),
                "description": project.get("description", ""),
                "state": project.get("state", "unknown"),
                "progress": project.get("progress", 0),
                "url": project.get("url", ""),
                "created_at": project.get("createdAt"),
                "updated_at": project.get("updatedAt"),
                "started_at": project.get("startedAt"),
                "completed_at": project.get("completedAt"),
                "target_date": project.get("targetDate"),
                "health_status": "healthy",
                "risk_level": "low",
                "timeline_status": "on_track",
                "team_count": len(project.get("teams", {}).get("nodes", [])),
                "member_count": 0,  # Simplified query doesn't include member details
                "issue_count": 0,  # Simplified query doesn't include issues
                "completed_issues": 0,
                "in_progress_issues": 0,
            }
            # Note: Issue analysis removed due to query complexity limits
            # Use progress field instead of calculated completion rate
            completion_rate = project_analysis["progress"] or 0
            # Assess timeline status
            if project_analysis["target_date"]:
                target_date = datetime.fromisoformat(
                    project_analysis["target_date"].replace("Z", "+00:00")
                )
                days_until_target = (target_date - now).days
                if days_until_target < 0:
                    project_analysis["timeline_status"] = "behind_schedule"
                    dashboard["timeline_analysis"]["behind_schedule"] += 1
                elif days_until_target > 30 and completion_rate > 80:
                    project_analysis["timeline_status"] = "ahead_of_schedule"
                    dashboard["timeline_analysis"]["ahead_of_schedule"] += 1
                else:
                    dashboard["timeline_analysis"]["on_track"] += 1
            else:
                project_analysis["timeline_status"] = "no_timeline"
                dashboard["timeline_analysis"]["no_timeline"] += 1
            # Assess health status
            health_score = 100
            # Factor 1: Progress vs timeline
            if project_analysis["timeline_status"] == "behind_schedule":
                health_score -= 30
                project_analysis["risk_level"] = "high"
            elif project_analysis["timeline_status"] == "no_timeline":
                health_score -= 10
            # Factor 2: Completion rate
            if completion_rate < 20:
                health_score -= 20
            elif completion_rate < 50:
                health_score -= 10
            # Factor 3: Team engagement
            if project_analysis["member_count"] == 0:
                health_score -= 25
                project_analysis["risk_level"] = "high"
            elif project_analysis["member_count"] < 2:
                health_score -= 10
            # Factor 4: Recent activity
            if project_analysis["updated_at"]:
                last_update = datetime.fromisoformat(
                    project_analysis["updated_at"].replace("Z", "+00:00")
                )
                days_since_update = (now - last_update).days
                if days_since_update > 14:
                    health_score -= 15
                elif days_since_update > 7:
                    health_score -= 5
            # Determine health status
            if health_score >= 80:
                project_analysis["health_status"] = "healthy"
                dashboard["project_health"]["healthy"] += 1
            elif health_score >= 60:
                project_analysis["health_status"] = "at_risk"
                dashboard["project_health"]["at_risk"] += 1
                if project_analysis["risk_level"] == "low":
                    project_analysis["risk_level"] = "medium"
            else:
                project_analysis["health_status"] = "critical"
                dashboard["project_health"]["critical"] += 1
                project_analysis["risk_level"] = "high"
            health_scores.append(health_score)
            # Track status distribution
            state = project_analysis["state"].lower()
            if state in dashboard["status_distribution"]:
                dashboard["status_distribution"][state] += 1
            # Track resource allocation
            lead = project.get("lead", {})
            if lead:
                lead_name = lead.get("displayName") or lead.get("name", "Unknown")
                if lead_name not in dashboard["resource_allocation"]:
                    dashboard["resource_allocation"][lead_name] = {
                        "projects": 0,
                        "total_issues": 0,
                        "workload_score": 0,
                    }
                dashboard["resource_allocation"][lead_name]["projects"] += 1
                dashboard["resource_allocation"][lead_name][
                    "total_issues"
                ] += project_analysis["issue_count"]
            dashboard["project_details"].append(project_analysis)
        # Calculate overall health score
        if health_scores:
            dashboard["overall_health_score"] = sum(health_scores) / len(health_scores)
        # Calculate workload scores
        for lead_data in dashboard["resource_allocation"].values():
            # Simple workload score based on projects and issues
            lead_data["workload_score"] = (lead_data["projects"] * 20) + (
                lead_data["total_issues"] * 2
            )
        # Identify risk factors
        if dashboard["project_health"]["critical"] > 0:
            dashboard["risk_factors"].append(
                f"{dashboard['project_health']['critical']} projects in critical state"
            )
        if dashboard["timeline_analysis"]["behind_schedule"] > 0:
            dashboard["risk_factors"].append(
                f"{dashboard['timeline_analysis']['behind_schedule']} projects behind schedule"
            )
        if (
            dashboard["timeline_analysis"]["no_timeline"]
            > dashboard["total_projects"] / 2
        ):
            dashboard["risk_factors"].append(
                "Over 50% of projects lack defined timelines"
            )
        overloaded_leads = [
            name
            for name, data in dashboard["resource_allocation"].items()
            if data["workload_score"] > 100
        ]
        if overloaded_leads:
            dashboard["risk_factors"].append(
                f"High workload detected for: {', '.join(overloaded_leads)}"
            )
        # Generate recommendations
        if dashboard["overall_health_score"] < 70:
            dashboard["recommendations"].append(
                "Overall project health needs improvement - review resource allocation"
            )
        if dashboard["project_health"]["critical"] > 0:
            dashboard["recommendations"].append(
                "Address critical projects immediately to prevent further deterioration"
            )
        if dashboard["timeline_analysis"]["no_timeline"] > 2:
            dashboard["recommendations"].append(
                "Establish clear timelines for projects lacking target dates"
            )
        if len(overloaded_leads) > 0:
            dashboard["recommendations"].append(
                "Consider redistributing workload for overloaded project leads"
            )
        return dashboard
    async def create_issue(
        self,
        team_id: str,
        title: str,
        description: str = None,
        assignee_id: str = None,
        priority: int = None,
        project_id: str = None,
    ) -> dict[str, Any]:
        """Create a new issue"""
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    url
                    createdAt
                }
            }
        }
        """
        input_data = {"teamId": team_id, "title": title}
        if description:
            input_data["description"] = description
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if priority:
            input_data["priority"] = priority
        if project_id:
            input_data["projectId"] = project_id
        variables = {"input": input_data}
        result = await self._make_graphql_request(mutation, variables)
        return result.get("issueCreate", {})
    async def update_issue(
        self,
        issue_id: str,
        title: str = None,
        description: str = None,
        assignee_id: str = None,
        state_id: str = None,
        priority: int = None,
    ) -> dict[str, Any]:
        """Update an existing issue"""
        mutation = """
        mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    updatedAt
                }
            }
        }
        """
        input_data = {}
        if title:
            input_data["title"] = title
        if description:
            input_data["description"] = description
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if state_id:
            input_data["stateId"] = state_id
        if priority:
            input_data["priority"] = priority
        variables = {"id": issue_id, "input": input_data}
        result = await self._make_graphql_request(mutation, variables)
        return result.get("issueUpdate", {})
    async def get_integration_health(self) -> dict[str, Any]:
        """Check integration health and return status"""
        try:
            # Test basic API connectivity
            viewer_info = await self.get_viewer_info()
            # Get workspace stats
            teams = await self.get_teams(first=10)  # Small sample
            users = await self.get_users(first=10)  # Small sample
            return {
                "status": "healthy",
                "user_name": viewer_info.get("displayName") or viewer_info.get("name"),
                "user_email": viewer_info.get("email"),
                "is_admin": viewer_info.get("admin", False),
                "teams_sample": len(teams),
                "users_sample": len(users),
                "api_endpoint": self.base_url,
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }
    # Utility Methods for Sophia's Analysis
    async def create_intelligence_summary(self, team_id: str = None) -> dict[str, Any]:
        """Create a comprehensive intelligence summary for Sophia"""
        logger.info("🎯 Creating comprehensive Linear intelligence summary...")
        try:
            # Get all major metrics in parallel
            health_check = await self.get_integration_health()
            if health_check["status"] == "error":
                return {
                    "status": "error",
                    "error": health_check["error"],
                    "timestamp": datetime.now().isoformat(),
                }
            teams = await self.get_teams()
            # Use first team if none specified
            if not team_id and teams:
                team_id = teams[0]["id"]
            if team_id:
                velocity_analysis = await self.analyze_development_velocity(team_id)
                issue_patterns = await self.get_issue_pattern_analysis(team_id)
                team_performance = await self.get_team_performance_metrics(team_id)
                project_health = await self.get_project_health_dashboard(team_id)
            else:
                velocity_analysis = {"health_score": 0, "total_issues": 0}
                issue_patterns = {"total_issues": 0}
                team_performance = {"member_count": 0}
                project_health = {"total_projects": 0, "overall_health_score": 0}
            summary = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "health": health_check,
                "workspace_overview": {
                    "total_teams": len(teams),
                    "analyzed_team": team_id,
                    "team_names": [t.get("name") for t in teams[:5]],  # First 5 teams
                },
                "development_metrics": {
                    "velocity_health_score": velocity_analysis.get("health_score", 0),
                    "total_issues_analyzed": velocity_analysis.get("total_issues", 0),
                    "completion_rate": velocity_analysis.get(
                        "velocity_metrics", {}
                    ).get("completion_rate", 0),
                    "throughput_per_week": velocity_analysis.get(
                        "velocity_metrics", {}
                    ).get("throughput_per_week", 0),
                    "average_completion_time": velocity_analysis.get(
                        "velocity_metrics", {}
                    ).get("average_completion_time", 0),
                },
                "team_insights": {
                    "member_count": team_performance.get("member_count", 0),
                    "collaboration_score": team_performance.get(
                        "collaboration_score", 0
                    ),
                    "active_members": len(
                        [
                            m
                            for m in team_performance.get(
                                "member_performance", {}
                            ).values()
                            if m.get("total_issues", 0) > 0
                        ]
                    ),
                    "workload_balance": self._assess_workload_balance(
                        team_performance.get("member_performance", {})
                    ),
                },
                "project_portfolio": {
                    "total_projects": project_health.get("total_projects", 0),
                    "health_distribution": project_health.get("project_health", {}),
                    "overall_project_health": project_health.get(
                        "overall_health_score", 0
                    ),
                    "timeline_risks": len(project_health.get("risk_factors", [])),
                },
                "issue_intelligence": {
                    "pattern_analysis_period": issue_patterns.get("period_days", 0),
                    "total_patterns_analyzed": issue_patterns.get("total_issues", 0),
                    "collaboration_score": issue_patterns.get(
                        "collaboration_metrics", {}
                    ).get("avg_comments_per_issue", 0),
                    "estimate_coverage": self._calculate_estimate_coverage(
                        issue_patterns.get("issue_complexity", {})
                    ),
                },
                "key_recommendations": self._consolidate_recommendations(
                    [
                        velocity_analysis.get("recommendations", []),
                        team_performance.get("recommendations", []),
                        project_health.get("recommendations", []),
                    ]
                ),
                "business_value": self._calculate_development_business_value(
                    velocity_analysis, team_performance, project_health, issue_patterns
                ),
            }
            return summary
        except Exception as e:
            logger.error(f"Failed to create intelligence summary: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    def _assess_workload_balance(self, member_performance: dict[str, Any]) -> str:
        """Assess workload balance across team members"""
        if not member_performance:
            return "No data"
        issue_counts = [
            member.get("total_issues", 0) for member in member_performance.values()
        ]
        if not issue_counts:
            return "No data"
        avg_issues = sum(issue_counts) / len(issue_counts)
        max_issues = max(issue_counts)
        min_issues = min(issue_counts)
        if max_issues - min_issues <= 2:
            return "Well balanced"
        elif max_issues > avg_issues * 2:
            return "Highly imbalanced"
        else:
            return "Moderately imbalanced"
    def _calculate_estimate_coverage(self, complexity_data: dict[str, Any]) -> float:
        """Calculate percentage of issues with estimates"""
        with_estimates = complexity_data.get("with_estimates", 0)
        without_estimates = complexity_data.get("without_estimates", 0)
        total = with_estimates + without_estimates
        if total == 0:
            return 0.0
        return (with_estimates / total) * 100
    def _consolidate_recommendations(
        self, recommendation_lists: list[list[str]]
    ) -> list[str]:
        """Consolidate and prioritize recommendations from multiple sources"""
        all_recommendations = []
        for rec_list in recommendation_lists:
            all_recommendations.extend(rec_list)
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        # Return top 5 most important recommendations
        return unique_recommendations[:5]
    def _calculate_development_business_value(
        self,
        velocity: dict[str, Any],
        performance: dict[str, Any],
        projects: dict[str, Any],
        patterns: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate business value metrics for development operations"""
        # Development velocity value (25% weight)
        velocity_score = velocity.get("health_score", 0) * 0.25
        # Team productivity value (25% weight)
        productivity_score = performance.get("collaboration_score", 0) * 0.25
        # Project execution value (30% weight)
        project_score = projects.get("overall_health_score", 0) * 0.30
        # Process maturity value (20% weight)
        estimate_coverage = self._calculate_estimate_coverage(
            patterns.get("issue_complexity", {})
        )
        process_score = estimate_coverage * 0.20
        overall_value = (
            velocity_score + productivity_score + project_score + process_score
        )
        # Risk assessment
        risk_factors = len(projects.get("risk_factors", []))
        risk_level = (
            "High" if risk_factors >= 3 else "Medium" if risk_factors >= 1 else "Low"
        )
        return {
            "overall_score": round(overall_value, 2),
            "velocity_value": round(velocity_score / 0.25, 2),
            "productivity_value": round(productivity_score / 0.25, 2),
            "execution_value": round(project_score / 0.30, 2),
            "process_maturity": round(process_score / 0.20, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "value_tier": (
                "High"
                if overall_value >= 75
                else "Medium" if overall_value >= 50 else "Low"
            ),
            "development_readiness": (
                "Production Ready" if overall_value >= 80 else "Needs Improvement"
            ),
        }
