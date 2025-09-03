"""
Planner Agent - Specialized for Strategic Planning

Optimized for breaking down complex problems into structured, executable steps.
Focuses on resource allocation, dependencies, and timeline management.
"""

from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent, AgentRole
from app.tools.basic_tools import PlanningToolkit


class PlannerAgent(BaseAgent):
    """
    Specialized agent for strategic planning and task decomposition.
    
    Features:
    - Enhanced reasoning for step-by-step planning
    - Timeline and dependency analysis tools
    - Resource allocation optimization
    - Risk assessment and mitigation planning
    """
    
    def __init__(
        self,
        agent_id: str = "planner-001",
        enable_reasoning: bool = True,
        max_reasoning_steps: int = 15,  # Planners need more steps
        **kwargs
    ):
        # Custom tools for planning
        planning_tools = [
            PlanningToolkit.create_timeline,
            PlanningToolkit.analyze_dependencies,
            PlanningToolkit.estimate_resources,
            PlanningToolkit.assess_risks
        ]
        
        # Initialize with planner-specific configuration
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.PLANNER,
            enable_reasoning=enable_reasoning,
            max_reasoning_steps=max_reasoning_steps,
            tools=planning_tools,
            model_config={
                "temperature": 0.2,  # Lower temperature for structured planning
                "cost_limit_per_request": 0.75  # Higher limit for complex planning
            },
            **kwargs
        )
    
    async def create_project_plan(self, project_description: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a comprehensive project plan with timeline and milestones.
        
        Args:
            project_description: Details about the project requirements
            
        Returns:
            Structured project plan with tasks, timeline, and dependencies
        """
        
        planning_problem = {
            "query": f"""Create a detailed project plan for: {project_description.get('title', 'Untitled Project')}
            
            Requirements: {project_description.get('requirements', 'No specific requirements')}
            Constraints: {project_description.get('constraints', 'No specific constraints')}
            Timeline: {project_description.get('timeline', 'Flexible')}
            
            Please provide:
            1. Task breakdown with clear deliverables
            2. Timeline with milestones and dependencies  
            3. Resource requirements and allocation
            4. Risk assessment and mitigation strategies
            5. Success criteria and metrics
            """,
            "context": "project_planning",
            "priority": "high"
        }
        
        result = await self.execute(planning_problem)
        
        return {
            "project_plan": result["result"],
            "reasoning_trace": result.get("reasoning_trace", []),
            "confidence": "high" if result["success"] else "low",
            "planner_id": self.agent_id,
            "planning_metadata": {
                "execution_time": result.get("execution_time", 0),
                "context_used": result.get("context_used", 0)
            }
        }
    
    async def analyze_task_dependencies(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze dependencies between tasks and optimize execution order.
        
        Args:
            tasks: List of tasks with descriptions and requirements
            
        Returns:
            Dependency analysis with optimized execution sequence
        """
        
        dependency_problem = {
            "query": f"""Analyze dependencies between these {len(tasks)} tasks and create an optimal execution sequence:
            
            Tasks:
            {chr(10).join([f"{i+1}. {task.get('name', f'Task {i+1}')}: {task.get('description', 'No description')}" for i, task in enumerate(tasks)])}
            
            Please provide:
            1. Dependency graph showing task relationships
            2. Critical path analysis
            3. Parallel execution opportunities  
            4. Risk factors and bottlenecks
            5. Recommended execution sequence
            """,
            "context": "dependency_analysis"
        }
        
        result = await self.execute(dependency_problem)
        
        return {
            "dependency_analysis": result["result"],
            "critical_path": "Extracted from analysis",  # Would be parsed from result
            "parallel_tasks": "Identified opportunities",  # Would be parsed from result
            "execution_sequence": "Optimized order",  # Would be parsed from result
            "success": result["success"]
        }