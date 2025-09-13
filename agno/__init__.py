"""Agno stub module for compatibility"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Agent:
    """Stub Agent class"""
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', 'Agent')
        self.role = kwargs.get('role', '')
        self.instructions = kwargs.get('instructions', [])
        self.model = kwargs.get('model')
        self.tools = kwargs.get('tools', [])
    
    async def execute(self, task):
        """Mock execute - returns a simple response"""
        from builder_cli.lib.platinum import PlanSpec, Task as PlanTask, Milestone
        
        # Create a basic plan
        return PlanSpec(
            overview=f"Plan for: {task}",
            tasks=[
                PlanTask(
                    id="task-1",
                    description="Implement hello world function",
                    priority="high",
                    dependencies=[]
                )
            ],
            milestones=[
                Milestone(
                    name="MVP",
                    tasks=["task-1"],
                    deliverables=["Working hello world function"]
                )
            ],
            risks=[],
            constraints=[]
        )


class Team:
    """Stub Team class"""
    def __init__(self, *args, **kwargs):
        self.agents = kwargs.get('agents', [])
        self.name = kwargs.get('name', 'Team')


class Workflow:
    """Stub Workflow class"""
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', 'Workflow')
        self.steps = kwargs.get('steps', [])


class Tool:
    """Stub Tool class"""
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', 'Tool')


# Storage stubs
class storage:
    class PostgresDb:
        def __init__(self, *args, **kwargs):
            pass
    
    class RedisDb:
        def __init__(self, *args, **kwargs):
            pass


# Memory stubs  
class memory:
    class Knowledge:
        def __init__(self, *args, **kwargs):
            pass


# Tools stubs
class tools:
    Tool = Tool
    
    class Neo4jTools:
        def __init__(self, *args, **kwargs):
            pass