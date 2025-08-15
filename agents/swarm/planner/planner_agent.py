"""
Planner Agent for SOPHIA Intel Agent Swarm

Responsible for:
- Breaking down complex development tasks into manageable subtasks
- Creating execution strategies and workflows
- Coordinating task dependencies and sequencing
- Resource allocation and timeline estimation
"""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..base_agent import (
    AgentCapability, AgentTask, AgentType, BaseAgent, Priority, TaskStatus
)


class PlannerAgent(BaseAgent):
    """
    Planner Agent specializes in task decomposition and strategic planning.
    
    Capabilities:
    - Complex task breakdown
    - Dependency analysis
    - Resource estimation
    - Timeline planning
    - Risk assessment
    """
    
    def __init__(self, ai_router_url: str = "http://localhost:5000/api/ai/route"):
        capabilities = [
            AgentCapability(
                name="task_decomposition",
                description="Break complex tasks into manageable subtasks",
                input_types=["mission", "complex_task", "project_request"],
                output_types=["task_plan", "subtask_list", "workflow"],
                estimated_duration=300,  # 5 minutes
                confidence_score=0.95
            ),
            AgentCapability(
                name="dependency_analysis",
                description="Analyze task dependencies and sequencing",
                input_types=["task_list", "project_plan"],
                output_types=["dependency_graph", "execution_order"],
                estimated_duration=180,  # 3 minutes
                confidence_score=0.90
            ),
            AgentCapability(
                name="resource_estimation",
                description="Estimate resources and timeline for tasks",
                input_types=["task_plan", "project_scope"],
                output_types=["resource_plan", "timeline", "cost_estimate"],
                estimated_duration=240,  # 4 minutes
                confidence_score=0.85
            ),
            AgentCapability(
                name="strategy_formulation",
                description="Create execution strategies and approaches",
                input_types=["requirements", "constraints", "objectives"],
                output_types=["strategy", "approach", "methodology"],
                estimated_duration=360,  # 6 minutes
                confidence_score=0.88
            )
        ]
        
        super().__init__(
            agent_type=AgentType.PLANNER,
            name="Strategic Planner",
            description="Breaks down complex tasks and creates execution strategies",
            capabilities=capabilities,
            ai_router_url=ai_router_url
        )
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a planning task"""
        self.logger.info(f"Executing planning task: {task.type}")
        
        if task.type == "mission":
            return await self._plan_mission(task)
        elif task.type == "complex_task":
            return await self._decompose_complex_task(task)
        elif task.type == "project_request":
            return await self._plan_project(task)
        elif task.type == "dependency_analysis":
            return await self._analyze_dependencies(task)
        elif task.type == "resource_estimation":
            return await self._estimate_resources(task)
        else:
            raise ValueError(f"Unknown task type: {task.type}")
    
    async def _plan_mission(self, task: AgentTask) -> Dict[str, Any]:
        """Plan a complete development mission"""
        mission_description = task.description
        requirements = task.requirements
        
        # Create comprehensive planning prompt
        planning_prompt = f"""
        As a strategic planner for a development mission, create a comprehensive plan for:
        
        Mission: {mission_description}
        
        Requirements:
        {json.dumps(requirements, indent=2)}
        
        Please provide a detailed plan including:
        
        1. MISSION ANALYSIS
        - Objective breakdown
        - Success criteria
        - Key deliverables
        - Potential challenges
        
        2. TASK DECOMPOSITION
        - Break into 5-8 main phases
        - Each phase should have 2-4 specific tasks
        - Include task descriptions and acceptance criteria
        
        3. DEPENDENCY MAPPING
        - Identify task dependencies
        - Determine critical path
        - Highlight parallel execution opportunities
        
        4. RESOURCE ALLOCATION
        - Assign appropriate agent types to each task
        - Estimate effort and duration
        - Identify required tools and technologies
        
        5. RISK ASSESSMENT
        - Identify potential risks and blockers
        - Mitigation strategies
        - Contingency plans
        
        6. TIMELINE
        - Estimated completion time
        - Key milestones
        - Buffer time for unexpected issues
        
        Format the response as structured JSON with clear sections.
        """
        
        # Get AI-generated plan
        ai_response = await self.communicate_with_ai(
            prompt=planning_prompt,
            task_type="reasoning",
            context={"mission": mission_description, "requirements": requirements}
        )
        
        # Parse and structure the plan
        try:
            # Extract JSON from AI response if it's embedded in text
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                # Fallback: create structured plan from text response
                plan_data = await self._structure_text_plan(ai_response)
            
            # Generate subtasks
            subtasks = await self._generate_subtasks(plan_data)
            
            # Create execution timeline
            timeline = await self._create_timeline(subtasks)
            
            return {
                "plan_type": "mission",
                "mission": mission_description,
                "plan_data": plan_data,
                "subtasks": subtasks,
                "timeline": timeline,
                "estimated_duration_hours": self._calculate_total_duration(subtasks),
                "critical_path": self._identify_critical_path(subtasks),
                "resource_requirements": self._analyze_resource_needs(subtasks),
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse planning response: {e}")
            # Fallback to basic plan structure
            return await self._create_fallback_plan(mission_description, requirements)
    
    async def _decompose_complex_task(self, task: AgentTask) -> Dict[str, Any]:
        """Decompose a complex task into subtasks"""
        task_description = task.description
        context = task.context
        
        decomposition_prompt = f"""
        Break down this complex development task into manageable subtasks:
        
        Task: {task_description}
        Context: {json.dumps(context, indent=2)}
        
        Provide:
        1. 3-6 specific subtasks with clear descriptions
        2. Dependencies between subtasks
        3. Estimated effort for each subtask (in hours)
        4. Required skills/agent types for each subtask
        5. Acceptance criteria for each subtask
        
        Format as JSON with subtasks array.
        """
        
        ai_response = await self.communicate_with_ai(
            prompt=decomposition_prompt,
            task_type="analysis",
            context=context
        )
        
        # Parse subtasks
        subtasks = await self._parse_subtasks(ai_response)
        
        return {
            "decomposition_type": "complex_task",
            "original_task": task_description,
            "subtasks": subtasks,
            "total_estimated_hours": sum(st.get("estimated_hours", 1) for st in subtasks),
            "parallelizable_tasks": self._identify_parallel_tasks(subtasks),
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _plan_project(self, task: AgentTask) -> Dict[str, Any]:
        """Plan a complete project"""
        project_description = task.description
        requirements = task.requirements
        
        project_prompt = f"""
        Create a comprehensive project plan for:
        
        Project: {project_description}
        Requirements: {json.dumps(requirements, indent=2)}
        
        Include:
        1. Project phases (Planning, Development, Testing, Deployment)
        2. Detailed tasks for each phase
        3. Resource allocation
        4. Timeline with milestones
        5. Quality gates and checkpoints
        6. Risk mitigation strategies
        
        Focus on practical, actionable tasks that can be executed by specialized agents.
        """
        
        ai_response = await self.communicate_with_ai(
            prompt=project_prompt,
            task_type="reasoning",
            context={"project": project_description, "requirements": requirements}
        )
        
        project_plan = await self._structure_project_plan(ai_response)
        
        return {
            "plan_type": "project",
            "project": project_description,
            "phases": project_plan.get("phases", []),
            "milestones": project_plan.get("milestones", []),
            "resource_plan": project_plan.get("resources", {}),
            "timeline": project_plan.get("timeline", {}),
            "risks": project_plan.get("risks", []),
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _analyze_dependencies(self, task: AgentTask) -> Dict[str, Any]:
        """Analyze task dependencies"""
        tasks = task.context.get("tasks", [])
        
        dependency_prompt = f"""
        Analyze dependencies between these tasks:
        
        {json.dumps(tasks, indent=2)}
        
        Identify:
        1. Which tasks depend on others
        2. Critical path through the tasks
        3. Tasks that can run in parallel
        4. Potential bottlenecks
        5. Recommended execution order
        """
        
        ai_response = await self.communicate_with_ai(
            prompt=dependency_prompt,
            task_type="analysis",
            context={"tasks": tasks}
        )
        
        return {
            "analysis_type": "dependencies",
            "tasks": tasks,
            "dependencies": await self._parse_dependencies(ai_response),
            "critical_path": await self._extract_critical_path(ai_response),
            "parallel_groups": await self._identify_parallel_groups(ai_response),
            "execution_order": await self._determine_execution_order(tasks),
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _estimate_resources(self, task: AgentTask) -> Dict[str, Any]:
        """Estimate resources needed for tasks"""
        tasks = task.context.get("tasks", [])
        
        estimation_prompt = f"""
        Estimate resources needed for these tasks:
        
        {json.dumps(tasks, indent=2)}
        
        For each task, estimate:
        1. Time required (hours)
        2. Agent type needed (planner, coder, reviewer, etc.)
        3. Complexity level (1-5)
        4. Required tools/technologies
        5. Potential blockers or challenges
        
        Also provide overall project estimates.
        """
        
        ai_response = await self.communicate_with_ai(
            prompt=estimation_prompt,
            task_type="analysis",
            context={"tasks": tasks}
        )
        
        return {
            "estimation_type": "resources",
            "task_estimates": await self._parse_task_estimates(ai_response),
            "total_hours": await self._calculate_total_hours(ai_response),
            "agent_requirements": await self._extract_agent_requirements(ai_response),
            "technology_stack": await self._identify_technologies(ai_response),
            "risk_factors": await self._identify_risk_factors(ai_response),
            "created_at": datetime.utcnow().isoformat()
        }
    
    # Helper methods for plan processing
    
    async def _structure_text_plan(self, text_response: str) -> Dict[str, Any]:
        """Structure a text response into a plan format"""
        # Basic structure extraction from text
        return {
            "objective": "Development mission",
            "phases": [],
            "tasks": [],
            "raw_response": text_response
        }
    
    async def _generate_subtasks(self, plan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate subtasks from plan data"""
        subtasks = []
        
        # Extract tasks from plan structure
        phases = plan_data.get("phases", [])
        for i, phase in enumerate(phases):
            phase_tasks = phase.get("tasks", [])
            for j, task in enumerate(phase_tasks):
                subtasks.append({
                    "id": f"task_{i}_{j}",
                    "name": task.get("name", f"Task {i}.{j}"),
                    "description": task.get("description", ""),
                    "phase": phase.get("name", f"Phase {i}"),
                    "estimated_hours": task.get("estimated_hours", 2),
                    "agent_type": task.get("agent_type", "coder"),
                    "dependencies": task.get("dependencies", []),
                    "priority": task.get("priority", "medium")
                })
        
        return subtasks
    
    async def _create_timeline(self, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create execution timeline"""
        start_date = datetime.utcnow()
        current_date = start_date
        
        timeline = {
            "start_date": start_date.isoformat(),
            "phases": [],
            "milestones": []
        }
        
        # Group tasks by phase
        phases = {}
        for task in subtasks:
            phase_name = task.get("phase", "Default")
            if phase_name not in phases:
                phases[phase_name] = []
            phases[phase_name].append(task)
        
        # Calculate phase timelines
        for phase_name, tasks in phases.items():
            phase_duration = sum(task.get("estimated_hours", 2) for task in tasks)
            phase_end = current_date + timedelta(hours=phase_duration)
            
            timeline["phases"].append({
                "name": phase_name,
                "start_date": current_date.isoformat(),
                "end_date": phase_end.isoformat(),
                "duration_hours": phase_duration,
                "tasks": len(tasks)
            })
            
            current_date = phase_end
        
        timeline["end_date"] = current_date.isoformat()
        timeline["total_duration_hours"] = (current_date - start_date).total_seconds() / 3600
        
        return timeline
    
    def _calculate_total_duration(self, subtasks: List[Dict[str, Any]]) -> float:
        """Calculate total estimated duration"""
        return sum(task.get("estimated_hours", 2) for task in subtasks)
    
    def _identify_critical_path(self, subtasks: List[Dict[str, Any]]) -> List[str]:
        """Identify critical path through tasks"""
        # Simplified critical path identification
        critical_tasks = [
            task["id"] for task in subtasks
            if task.get("priority") == "high" or len(task.get("dependencies", [])) > 0
        ]
        return critical_tasks
    
    def _analyze_resource_needs(self, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze resource requirements"""
        agent_hours = {}
        technologies = set()
        
        for task in subtasks:
            agent_type = task.get("agent_type", "coder")
            hours = task.get("estimated_hours", 2)
            
            if agent_type not in agent_hours:
                agent_hours[agent_type] = 0
            agent_hours[agent_type] += hours
            
            # Extract technologies
            tech = task.get("technologies", [])
            technologies.update(tech)
        
        return {
            "agent_hours": agent_hours,
            "technologies": list(technologies),
            "total_hours": sum(agent_hours.values())
        }
    
    async def _create_fallback_plan(
        self, 
        mission: str, 
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a basic fallback plan when AI parsing fails"""
        return {
            "plan_type": "mission",
            "mission": mission,
            "plan_data": {
                "objective": mission,
                "phases": [
                    {"name": "Planning", "tasks": ["Analyze requirements", "Create detailed plan"]},
                    {"name": "Development", "tasks": ["Implement core features", "Write tests"]},
                    {"name": "Testing", "tasks": ["Run tests", "Fix issues"]},
                    {"name": "Deployment", "tasks": ["Deploy to production", "Verify deployment"]}
                ]
            },
            "subtasks": [
                {
                    "id": "task_0_0",
                    "name": "Analyze requirements",
                    "description": "Analyze and understand the requirements",
                    "phase": "Planning",
                    "estimated_hours": 2,
                    "agent_type": "planner",
                    "dependencies": [],
                    "priority": "high"
                },
                {
                    "id": "task_1_0",
                    "name": "Implement core features",
                    "description": "Implement the main functionality",
                    "phase": "Development",
                    "estimated_hours": 8,
                    "agent_type": "coder",
                    "dependencies": ["task_0_0"],
                    "priority": "high"
                }
            ],
            "estimated_duration_hours": 12,
            "created_at": datetime.utcnow().isoformat()
        }
    
    # Additional helper methods for parsing AI responses
    
    async def _parse_subtasks(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse subtasks from AI response"""
        # Implementation for parsing subtasks
        return []
    
    async def _structure_project_plan(self, ai_response: str) -> Dict[str, Any]:
        """Structure project plan from AI response"""
        # Implementation for structuring project plan
        return {}
    
    async def _parse_dependencies(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse dependencies from AI response"""
        # Implementation for parsing dependencies
        return []
    
    async def _extract_critical_path(self, ai_response: str) -> List[str]:
        """Extract critical path from AI response"""
        # Implementation for extracting critical path
        return []
    
    async def _identify_parallel_groups(self, ai_response: str) -> List[List[str]]:
        """Identify parallel task groups from AI response"""
        # Implementation for identifying parallel groups
        return []
    
    async def _determine_execution_order(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Determine optimal execution order"""
        # Implementation for determining execution order
        return []
    
    async def _parse_task_estimates(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse task estimates from AI response"""
        # Implementation for parsing task estimates
        return []
    
    async def _calculate_total_hours(self, ai_response: str) -> float:
        """Calculate total hours from AI response"""
        # Implementation for calculating total hours
        return 0.0
    
    async def _extract_agent_requirements(self, ai_response: str) -> Dict[str, int]:
        """Extract agent requirements from AI response"""
        # Implementation for extracting agent requirements
        return {}
    
    async def _identify_technologies(self, ai_response: str) -> List[str]:
        """Identify required technologies from AI response"""
        # Implementation for identifying technologies
        return []
    
    async def _identify_risk_factors(self, ai_response: str) -> List[Dict[str, Any]]:
        """Identify risk factors from AI response"""
        # Implementation for identifying risk factors
        return []
    
    def _identify_parallel_tasks(self, subtasks: List[Dict[str, Any]]) -> List[List[str]]:
        """Identify tasks that can run in parallel"""
        # Implementation for identifying parallel tasks
        return []

