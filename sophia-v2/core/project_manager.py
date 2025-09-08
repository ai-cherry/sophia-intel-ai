"""
Project Manager Module
======================

Handles project management, sprint planning, task tracking, and resource allocation.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class ProjectStatus(Enum):
    """Project status states"""

    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Task status states"""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    BLOCKED = "blocked"
    DONE = "done"


class TaskPriority(Enum):
    """Task priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SprintStatus(Enum):
    """Sprint status states"""

    PLANNING = "planning"
    ACTIVE = "active"
    REVIEW = "review"
    COMPLETED = "completed"


@dataclass
class Task:
    """Task model"""

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str] = None
    estimated_hours: float = 0
    actual_hours: float = 0
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    comments: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert task to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "assignee": self.assignee,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "dependencies": self.dependencies,
            "tags": self.tags,
            "comments": self.comments,
        }


@dataclass
class Sprint:
    """Sprint model"""

    id: str
    name: str
    goal: str
    start_date: datetime
    end_date: datetime
    status: SprintStatus
    tasks: List[str] = field(default_factory=list)
    team_members: List[str] = field(default_factory=list)
    velocity: float = 0

    def to_dict(self) -> Dict:
        """Convert sprint to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "goal": self.goal,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status.value,
            "tasks": self.tasks,
            "team_members": self.team_members,
            "velocity": self.velocity,
        }


@dataclass
class Project:
    """Project model"""

    id: str
    name: str
    description: str
    client: str
    status: ProjectStatus
    start_date: datetime
    end_date: datetime
    budget: float = 0
    team_members: List[str] = field(default_factory=list)
    sprints: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)
    milestones: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert project to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "client": self.client,
            "status": self.status.value,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "budget": self.budget,
            "team_members": self.team_members,
            "sprints": self.sprints,
            "tasks": self.tasks,
            "milestones": self.milestones,
        }


class ProjectManager:
    """
    Main project management engine for Sophia.
    Handles project planning, task tracking, and team coordination.
    """

    def __init__(self):
        """Initialize the project manager"""
        self.projects: Dict[str, Project] = {}
        self.tasks: Dict[str, Task] = {}
        self.sprints: Dict[str, Sprint] = {}
        self.team_members: Dict[str, Dict] = {}

    def create_project(
        self,
        name: str,
        description: str,
        client: str,
        start_date: datetime,
        end_date: datetime,
        budget: float = 0,
    ) -> Project:
        """
        Create a new project.

        Args:
            name: Project name
            description: Project description
            client: Client name
            start_date: Project start date
            end_date: Project end date
            budget: Project budget

        Returns:
            Created project
        """
        project_id = str(uuid.uuid4())

        project = Project(
            id=project_id,
            name=name,
            description=description,
            client=client,
            status=ProjectStatus.PLANNING,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
        )

        self.projects[project_id] = project
        return project

    def create_task(
        self,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        estimated_hours: float = 0,
        assignee: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> Task:
        """
        Create a new task.

        Args:
            title: Task title
            description: Task description
            priority: Task priority
            estimated_hours: Estimated hours
            assignee: Assigned team member
            due_date: Task due date

        Returns:
            Created task
        """
        task_id = str(uuid.uuid4())

        task = Task(
            id=task_id,
            title=title,
            description=description,
            status=TaskStatus.TODO,
            priority=priority,
            estimated_hours=estimated_hours,
            assignee=assignee,
            due_date=due_date,
        )

        self.tasks[task_id] = task
        return task

    def create_sprint(
        self, name: str, goal: str, start_date: datetime, duration_weeks: int = 2
    ) -> Sprint:
        """
        Create a new sprint.

        Args:
            name: Sprint name
            goal: Sprint goal
            start_date: Sprint start date
            duration_weeks: Sprint duration in weeks

        Returns:
            Created sprint
        """
        sprint_id = str(uuid.uuid4())
        end_date = start_date + timedelta(weeks=duration_weeks)

        sprint = Sprint(
            id=sprint_id,
            name=name,
            goal=goal,
            start_date=start_date,
            end_date=end_date,
            status=SprintStatus.PLANNING,
        )

        self.sprints[sprint_id] = sprint
        return sprint

    def assign_task(self, task_id: str, assignee: str) -> bool:
        """
        Assign a task to a team member.

        Args:
            task_id: Task ID
            assignee: Team member ID

        Returns:
            Success status
        """
        if task_id in self.tasks:
            self.tasks[task_id].assignee = assignee
            self.tasks[task_id].updated_at = datetime.now()
            return True
        return False

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status

        Returns:
            Success status
        """
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.tasks[task_id].updated_at = datetime.now()

            # Track actual hours when task is done
            if status == TaskStatus.DONE:
                # This would integrate with time tracking
                pass

            return True
        return False

    def add_task_to_sprint(self, task_id: str, sprint_id: str) -> bool:
        """
        Add a task to a sprint.

        Args:
            task_id: Task ID
            sprint_id: Sprint ID

        Returns:
            Success status
        """
        if task_id in self.tasks and sprint_id in self.sprints:
            if task_id not in self.sprints[sprint_id].tasks:
                self.sprints[sprint_id].tasks.append(task_id)
                return True
        return False

    def add_task_to_project(self, task_id: str, project_id: str) -> bool:
        """
        Add a task to a project.

        Args:
            task_id: Task ID
            project_id: Project ID

        Returns:
            Success status
        """
        if task_id in self.tasks and project_id in self.projects:
            if task_id not in self.projects[project_id].tasks:
                self.projects[project_id].tasks.append(task_id)
                return True
        return False

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """
        Get comprehensive project status.

        Args:
            project_id: Project ID

        Returns:
            Project status information
        """
        if project_id not in self.projects:
            return {"error": "Project not found"}

        project = self.projects[project_id]

        # Calculate task statistics
        task_stats = self._calculate_task_stats(project.tasks)

        # Calculate sprint progress
        sprint_progress = self._calculate_sprint_progress(project.sprints)

        # Calculate budget usage
        budget_usage = self._calculate_budget_usage(project)

        # Calculate timeline progress
        timeline_progress = self._calculate_timeline_progress(project)

        return {
            "project": project.to_dict(),
            "task_statistics": task_stats,
            "sprint_progress": sprint_progress,
            "budget_usage": budget_usage,
            "timeline_progress": timeline_progress,
            "risks": self._identify_risks(project),
            "recommendations": self._generate_recommendations(project),
        }

    def get_sprint_velocity(self, sprint_id: str) -> float:
        """
        Calculate sprint velocity.

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint velocity (story points per sprint)
        """
        if sprint_id not in self.sprints:
            return 0

        sprint = self.sprints[sprint_id]
        completed_points = 0

        for task_id in sprint.tasks:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status == TaskStatus.DONE:
                    completed_points += task.estimated_hours

        return completed_points

    def generate_burndown_chart(self, sprint_id: str) -> Dict[str, List]:
        """
        Generate burndown chart data for a sprint.

        Args:
            sprint_id: Sprint ID

        Returns:
            Burndown chart data
        """
        if sprint_id not in self.sprints:
            return {"error": "Sprint not found"}

        sprint = self.sprints[sprint_id]

        # Calculate total work
        total_work = sum(
            self.tasks[task_id].estimated_hours for task_id in sprint.tasks if task_id in self.tasks
        )

        # Generate ideal burndown line
        days = (sprint.end_date - sprint.start_date).days
        ideal_line = [total_work - (total_work / days * i) for i in range(days + 1)]

        # Generate actual burndown (simplified)
        # In production, this would track actual daily progress
        actual_line = [total_work] * (days + 1)

        return {
            "ideal": ideal_line,
            "actual": actual_line,
            "dates": [(sprint.start_date + timedelta(days=i)).isoformat() for i in range(days + 1)],
        }

    def estimate_completion(self, project_id: str) -> Dict[str, Any]:
        """
        Estimate project completion based on current progress.

        Args:
            project_id: Project ID

        Returns:
            Completion estimate
        """
        if project_id not in self.projects:
            return {"error": "Project not found"}

        project = self.projects[project_id]

        # Calculate completion percentage
        total_tasks = len(project.tasks)
        completed_tasks = sum(
            1
            for task_id in project.tasks
            if task_id in self.tasks and self.tasks[task_id].status == TaskStatus.DONE
        )

        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Estimate remaining time
        avg_velocity = self._calculate_average_velocity(project.sprints)
        remaining_work = self._calculate_remaining_work(project.tasks)

        if avg_velocity > 0:
            estimated_sprints = remaining_work / avg_velocity
            estimated_weeks = estimated_sprints * 2  # Assuming 2-week sprints
            estimated_completion = datetime.now() + timedelta(weeks=estimated_weeks)
        else:
            estimated_completion = project.end_date

        return {
            "completion_percentage": completion_percentage,
            "estimated_completion_date": estimated_completion.isoformat(),
            "on_track": estimated_completion <= project.end_date,
            "days_ahead_behind": (project.end_date - estimated_completion).days,
        }

    def generate_report(self, project_id: str, report_type: str = "status") -> str:
        """
        Generate project report.

        Args:
            project_id: Project ID
            report_type: Type of report (status, progress, risk)

        Returns:
            Report content
        """
        if project_id not in self.projects:
            return "Project not found"

        project = self.projects[project_id]
        status = self.get_project_status(project_id)

        if report_type == "status":
            return self._generate_status_report(project, status)
        elif report_type == "progress":
            return self._generate_progress_report(project, status)
        elif report_type == "risk":
            return self._generate_risk_report(project, status)
        else:
            return "Unknown report type"

    # Helper methods
    def _calculate_task_stats(self, task_ids: List[str]) -> Dict:
        """Calculate task statistics"""
        stats = {"total": len(task_ids), "todo": 0, "in_progress": 0, "done": 0, "blocked": 0}

        for task_id in task_ids:
            if task_id in self.tasks:
                status = self.tasks[task_id].status
                if status == TaskStatus.TODO:
                    stats["todo"] += 1
                elif status == TaskStatus.IN_PROGRESS:
                    stats["in_progress"] += 1
                elif status == TaskStatus.DONE:
                    stats["done"] += 1
                elif status == TaskStatus.BLOCKED:
                    stats["blocked"] += 1

        return stats

    def _calculate_sprint_progress(self, sprint_ids: List[str]) -> Dict:
        """Calculate sprint progress"""
        active_sprint = None
        completed_sprints = 0

        for sprint_id in sprint_ids:
            if sprint_id in self.sprints:
                sprint = self.sprints[sprint_id]
                if sprint.status == SprintStatus.ACTIVE:
                    active_sprint = sprint.to_dict()
                elif sprint.status == SprintStatus.COMPLETED:
                    completed_sprints += 1

        return {
            "active_sprint": active_sprint,
            "completed_sprints": completed_sprints,
            "total_sprints": len(sprint_ids),
        }

    def _calculate_budget_usage(self, project: Project) -> Dict:
        """Calculate budget usage"""
        # Simplified calculation
        spent = project.budget * 0.4  # Placeholder

        return {
            "total_budget": project.budget,
            "spent": spent,
            "remaining": project.budget - spent,
            "percentage_used": (spent / project.budget * 100) if project.budget > 0 else 0,
        }

    def _calculate_timeline_progress(self, project: Project) -> Dict:
        """Calculate timeline progress"""
        total_days = (project.end_date - project.start_date).days
        elapsed_days = (datetime.now() - project.start_date).days

        return {
            "elapsed_days": elapsed_days,
            "total_days": total_days,
            "percentage_complete": (elapsed_days / total_days * 100) if total_days > 0 else 0,
        }

    def _identify_risks(self, project: Project) -> List[str]:
        """Identify project risks"""
        risks = []

        # Check for blocked tasks
        blocked_count = sum(
            1
            for task_id in project.tasks
            if task_id in self.tasks and self.tasks[task_id].status == TaskStatus.BLOCKED
        )
        if blocked_count > 0:
            risks.append(f"{blocked_count} tasks are blocked")

        # Check timeline
        if datetime.now() > project.end_date:
            risks.append("Project is past due date")

        # Check budget (simplified)
        if project.budget > 0:
            spent = project.budget * 0.4
            if spent > project.budget * 0.8:
                risks.append("Budget usage is high")

        return risks

    def _generate_recommendations(self, project: Project) -> List[str]:
        """Generate project recommendations"""
        recommendations = []

        # Check task distribution
        unassigned = sum(
            1
            for task_id in project.tasks
            if task_id in self.tasks and self.tasks[task_id].assignee is None
        )
        if unassigned > 0:
            recommendations.append(f"Assign {unassigned} unassigned tasks")

        # Check sprint planning
        if not project.sprints:
            recommendations.append("Create sprints for better project organization")

        return recommendations

    def _calculate_average_velocity(self, sprint_ids: List[str]) -> float:
        """Calculate average sprint velocity"""
        if not sprint_ids:
            return 0

        total_velocity = sum(self.get_sprint_velocity(sprint_id) for sprint_id in sprint_ids)

        return total_velocity / len(sprint_ids)

    def _calculate_remaining_work(self, task_ids: List[str]) -> float:
        """Calculate remaining work in hours"""
        remaining = 0

        for task_id in task_ids:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status != TaskStatus.DONE:
                    remaining += task.estimated_hours

        return remaining

    def _generate_status_report(self, project: Project, status: Dict) -> str:
        """Generate status report"""
        report = f"""
# Project Status Report: {project.name}

## Overview
- **Client**: {project.client}
- **Status**: {project.status.value}
- **Timeline**: {project.start_date.date()} to {project.end_date.date()}

## Task Progress
- Total Tasks: {status['task_statistics']['total']}
- Completed: {status['task_statistics']['done']}
- In Progress: {status['task_statistics']['in_progress']}
- Blocked: {status['task_statistics']['blocked']}

## Timeline
- Progress: {status['timeline_progress']['percentage_complete']:.1f}%
- Days Elapsed: {status['timeline_progress']['elapsed_days']}
- Days Remaining: {status['timeline_progress']['total_days'] - status['timeline_progress']['elapsed_days']}

## Risks
{chr(10).join(f'- {risk}' for risk in status['risks']) if status['risks'] else '- No risks identified'}

## Recommendations
{chr(10).join(f'- {rec}' for rec in status['recommendations']) if status['recommendations'] else '- No recommendations'}
"""
        return report

    def _generate_progress_report(self, project: Project, status: Dict) -> str:
        """Generate progress report"""
        return f"Progress report for {project.name}"

    def _generate_risk_report(self, project: Project, status: Dict) -> str:
        """Generate risk report"""
        return f"Risk report for {project.name}"
