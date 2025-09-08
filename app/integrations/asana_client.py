"""
Asana Integration Client for Sophia Business Intelligence
Provides project management and task intelligence capabilities
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import aiohttp

from app.orchestrators.resource_manager import ResourceType, resource_manager

logger = logging.getLogger(__name__)

# Provide a safe default for INTEGRATIONS if not imported from a central config
try:
    INTEGRATIONS  # type: ignore[name-defined]
except NameError:
    INTEGRATIONS = {}


class AsanaClient:
    """
    Asana API client for business intelligence and project management integration
    """

    def __init__(self):
        self.config = INTEGRATIONS.get("asana", {})
        self.api_token = self.config.get("pat_token")
        self.base_url = "https://app.asana.com/api/1.0"
        self.session: Optional[aiohttp.ClientSession] = None

        if not self.api_token:
            raise ValueError("Asana API token not configured")

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        logger.info("🎯 Asana client initialized")

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
            await resource_manager.register_resource(
                "asana_session",
                ResourceType.API_CONNECTION,
                self.session,
                cleanup_func=self._cleanup_session,
            )

    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _cleanup_session(self, session):
        """Cleanup function for resource manager"""
        if session and not session.closed:
            await session.close()

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> dict[str, Any]:
        """Make authenticated request to Asana API"""
        if not self.session:
            await self.initialize_session()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise Exception("Asana authentication failed - check API token")
                else:
                    error_text = await response.text()
                    raise Exception(f"Asana API error {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"Asana API request failed: {e}")
            raise

    # Core API Methods

    async def get_workspaces(self) -> list[dict[str, Any]]:
        """Get all accessible workspaces"""
        response = await self._make_request("GET", "/workspaces")
        return response.get("data", [])

    async def get_user_info(self) -> dict[str, Any]:
        """Get current user information"""
        response = await self._make_request("GET", "/users/me")
        return response.get("data", {})

    async def get_projects(
        self, workspace_gid: str, archived: bool = False
    ) -> list[dict[str, Any]]:
        """Get projects in workspace"""
        params = {
            "workspace": workspace_gid,
            "archived": archived,
            "opt_fields": "name,created_at,modified_at,owner,current_status,due_date,notes,team,members",
        }

        response = await self._make_request("GET", "/projects", params=params)
        return response.get("data", [])

    async def get_project_tasks(self, project_gid: str) -> list[dict[str, Any]]:
        """Get tasks for a project"""
        params = {
            "opt_fields": "name,assignee,completed,completed_at,created_at,modified_at,due_date,notes,tags,projects,parent,subtasks"
        }

        response = await self._make_request(
            "GET", f"/projects/{project_gid}/tasks", params=params
        )
        return response.get("data", [])

    async def get_task_details(self, task_gid: str) -> dict[str, Any]:
        """Get detailed task information"""
        params = {
            "opt_fields": "name,assignee,completed,completed_at,created_at,modified_at,due_date,notes,tags,projects,parent,subtasks,dependencies,dependents,attachments,followers,likes,num_likes"
        }

        response = await self._make_request("GET", f"/tasks/{task_gid}", params=params)
        return response.get("data", {})

    async def get_team_info(self, team_gid: str) -> dict[str, Any]:
        """Get team information"""
        params = {"opt_fields": "name,description,organization,permalink_url,members"}

        response = await self._make_request("GET", f"/teams/{team_gid}", params=params)
        return response.get("data", {})

    # Business Intelligence Methods

    async def analyze_project_health(self, workspace_gid: str) -> dict[str, Any]:
        """Analyze overall project health for business intelligence"""
        logger.info("📊 Analyzing Asana project health...")

        projects = await self.get_projects(workspace_gid)

        analysis = {
            "workspace_gid": workspace_gid,
            "total_projects": len(projects),
            "active_projects": 0,
            "overdue_projects": 0,
            "completed_projects": 0,
            "projects_without_owner": 0,
            "project_details": [],
            "health_score": 0.0,
            "recommendations": [],
        }

        now = datetime.now()

        for project in projects:
            project_analysis = {
                "gid": project.get("gid"),
                "name": project.get("name"),
                "owner": (
                    project.get("owner", {}).get("name")
                    if project.get("owner")
                    else None
                ),
                "status": (
                    project.get("current_status", {}).get("text")
                    if project.get("current_status")
                    else "No status"
                ),
                "due_date": project.get("due_date"),
                "is_overdue": False,
                "member_count": len(project.get("members", [])),
                "created_at": project.get("created_at"),
            }

            # Check if project is overdue
            if project_analysis["due_date"]:
                due_date = datetime.fromisoformat(
                    project_analysis["due_date"].replace("Z", "+00:00")
                )
                if due_date < now:
                    project_analysis["is_overdue"] = True
                    analysis["overdue_projects"] += 1

            # Count active projects
            if project.get("current_status", {}).get("color") not in [
                "complete",
                "green",
            ]:
                analysis["active_projects"] += 1
            else:
                analysis["completed_projects"] += 1

            # Check for projects without owners
            if not project_analysis["owner"]:
                analysis["projects_without_owner"] += 1

            analysis["project_details"].append(project_analysis)

        # Calculate health score (0-100)
        if analysis["total_projects"] > 0:
            health_factors = []

            # Factor 1: Project ownership (40% weight)
            ownership_score = (
                (analysis["total_projects"] - analysis["projects_without_owner"])
                / analysis["total_projects"]
            ) * 40
            health_factors.append(ownership_score)

            # Factor 2: On-time delivery (35% weight)
            ontime_score = (
                (analysis["total_projects"] - analysis["overdue_projects"])
                / analysis["total_projects"]
            ) * 35
            health_factors.append(ontime_score)

            # Factor 3: Active project ratio (25% weight)
            active_ratio = (
                analysis["active_projects"] / analysis["total_projects"]
                if analysis["total_projects"] > 0
                else 0
            )
            active_score = min(active_ratio * 25, 25)  # Cap at 25 points
            health_factors.append(active_score)

            analysis["health_score"] = sum(health_factors)

        # Generate recommendations
        if analysis["projects_without_owner"] > 0:
            analysis["recommendations"].append(
                f"Assign owners to {analysis['projects_without_owner']} unassigned projects"
            )

        if analysis["overdue_projects"] > 0:
            analysis["recommendations"].append(
                f"Address {analysis['overdue_projects']} overdue projects"
            )

        if analysis["health_score"] < 70:
            analysis["recommendations"].append(
                "Overall project health needs improvement - consider process review"
            )

        return analysis

    async def get_team_productivity_metrics(
        self, workspace_gid: str, days: int = 30
    ) -> dict[str, Any]:
        """Get team productivity metrics for the last N days"""
        logger.info(f"📈 Analyzing team productivity for last {days} days...")

        projects = await self.get_projects(workspace_gid)

        # Get tasks from all projects
        all_tasks = []
        for project in projects:
            tasks = await self.get_project_tasks(project["gid"])
            for task in tasks:
                task["project_name"] = project["name"]
                all_tasks.append(task)

        # Analyze tasks
        cutoff_date = datetime.now() - timedelta(days=days)

        metrics = {
            "period_days": days,
            "total_tasks": len(all_tasks),
            "completed_tasks": 0,
            "overdue_tasks": 0,
            "tasks_created": 0,
            "completion_rate": 0.0,
            "average_completion_time": 0.0,
            "assignee_productivity": {},
            "project_activity": {},
        }

        completion_times = []

        for task in all_tasks:
            # Tasks created in period
            if task.get("created_at"):
                created_date = datetime.fromisoformat(
                    task["created_at"].replace("Z", "+00:00")
                )
                if created_date >= cutoff_date:
                    metrics["tasks_created"] += 1

            # Completed tasks
            if task.get("completed"):
                metrics["completed_tasks"] += 1

                # Calculate completion time
                if task.get("created_at") and task.get("completed_at"):
                    created = datetime.fromisoformat(
                        task["created_at"].replace("Z", "+00:00")
                    )
                    completed = datetime.fromisoformat(
                        task["completed_at"].replace("Z", "+00:00")
                    )
                    completion_time = (completed - created).days
                    completion_times.append(completion_time)

            # Overdue tasks
            if task.get("due_date") and not task.get("completed"):
                due_date = datetime.fromisoformat(
                    task["due_date"].replace("Z", "+00:00")
                )
                if due_date < datetime.now():
                    metrics["overdue_tasks"] += 1

            # Assignee productivity
            assignee = task.get("assignee", {})
            if assignee:
                assignee_name = assignee.get("name", "Unknown")
                if assignee_name not in metrics["assignee_productivity"]:
                    metrics["assignee_productivity"][assignee_name] = {
                        "total_tasks": 0,
                        "completed_tasks": 0,
                        "completion_rate": 0.0,
                    }

                metrics["assignee_productivity"][assignee_name]["total_tasks"] += 1
                if task.get("completed"):
                    metrics["assignee_productivity"][assignee_name][
                        "completed_tasks"
                    ] += 1

            # Project activity
            project_name = task.get("project_name", "Unknown")
            if project_name not in metrics["project_activity"]:
                metrics["project_activity"][project_name] = {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                }

            metrics["project_activity"][project_name]["total_tasks"] += 1
            if task.get("completed"):
                metrics["project_activity"][project_name]["completed_tasks"] += 1

        # Calculate completion rate
        if metrics["total_tasks"] > 0:
            metrics["completion_rate"] = (
                metrics["completed_tasks"] / metrics["total_tasks"]
            ) * 100

        # Calculate average completion time
        if completion_times:
            metrics["average_completion_time"] = sum(completion_times) / len(
                completion_times
            )

        # Calculate assignee completion rates
        for assignee_data in metrics["assignee_productivity"].values():
            if assignee_data["total_tasks"] > 0:
                assignee_data["completion_rate"] = (
                    assignee_data["completed_tasks"] / assignee_data["total_tasks"]
                ) * 100

        return metrics

    async def create_task(
        self, project_gid: str, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new task"""
        data = {"data": task_data}
        response = await self._make_request("POST", "/tasks", json=data)
        return response.get("data", {})

    async def update_task(
        self, task_gid: str, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing task"""
        data = {"data": task_data}
        response = await self._make_request("PUT", f"/tasks/{task_gid}", json=data)
        return response.get("data", {})

    async def get_integration_health(self) -> dict[str, Any]:
        """Check integration health and return status"""
        try:
            user_info = await self.get_user_info()
            workspaces = await self.get_workspaces()

            return {
                "status": "healthy",
                "user": user_info.get("name"),
                "email": user_info.get("email"),
                "workspaces": len(workspaces),
                "workspace_names": [w.get("name") for w in workspaces],
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }
