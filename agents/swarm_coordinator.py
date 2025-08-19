"""
SOPHIA Intel Swarm Coordinator
Phase 4 of V4 Mega Upgrade - Multi-Agent Orchestration

Coordinates multiple specialized agents for autonomous operations using Phidata 0.3.0+
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from phi.assistant import Assistant
from phi.llm.openai import OpenAIChat
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.shell import ShellTools
from phi.tools.file import FileTools

logger = logging.getLogger(__name__)

class SwarmCoordinator:
    """
    Coordinates multiple specialized agents for autonomous operations.
    Implements parallel task execution and result aggregation.
    """
    
    def __init__(self):
        self.agents = {}
        self.active_tasks = {}
        self.results_cache = {}
        self.initialize_agents()
    
    def initialize_agents(self):
        """Initialize specialized agents with Phidata 0.3.0+"""
        
        # Research Agent - Information gathering and analysis
        self.agents['research'] = Assistant(
            name="SOPHIA Research Agent",
            llm=OpenAIChat(model="gpt-4"),
            tools=[DuckDuckGo()],
            description="Expert research agent specializing in information gathering, analysis, and synthesis",
            instructions=[
                "Conduct thorough research on technical topics",
                "Provide accurate, up-to-date information",
                "Synthesize findings from multiple sources",
                "Focus on actionable insights and recommendations"
            ]
        )
        
        # Coding Agent - Software development and implementation
        self.agents['coding'] = Assistant(
            name="SOPHIA Coding Agent", 
            llm=OpenAIChat(model="gpt-4"),
            tools=[FileTools(), ShellTools()],
            description="Expert software developer specializing in Python, FastAPI, and modern development practices",
            instructions=[
                "Write clean, maintainable, and well-documented code",
                "Follow best practices and design patterns",
                "Implement proper error handling and logging",
                "Ensure code is production-ready and scalable"
            ]
        )
        
        # Deployment Agent - Infrastructure and deployment operations
        self.agents['deployment'] = Assistant(
            name="SOPHIA Deployment Agent",
            llm=OpenAIChat(model="gpt-4"),
            tools=[ShellTools()],
            description="Expert DevOps engineer specializing in Fly.io, Docker, and CI/CD",
            instructions=[
                "Manage deployment pipelines and infrastructure",
                "Ensure zero-downtime deployments",
                "Monitor system health and performance",
                "Implement proper security and scaling practices"
            ]
        )
        
        # Monitoring Agent - System monitoring and alerting
        self.agents['monitoring'] = Assistant(
            name="SOPHIA Monitoring Agent",
            llm=OpenAIChat(model="gpt-4"),
            tools=[ShellTools()],
            description="Expert monitoring specialist focusing on system health, metrics, and alerting",
            instructions=[
                "Monitor system performance and health",
                "Detect anomalies and potential issues",
                "Provide actionable alerts and recommendations",
                "Maintain comprehensive system observability"
            ]
        )
        
        logger.info(f"Initialized {len(self.agents)} specialized agents")
    
    async def execute_swarm_task(self, task: str, agents: List[str] = None, context: Dict = None) -> Dict[str, Any]:
        """
        Execute a task using multiple agents in parallel.
        
        Args:
            task: The task description
            agents: List of agent names to use (default: all agents)
            context: Additional context for the task
            
        Returns:
            Dict containing results from all agents
        """
        if agents is None:
            agents = list(self.agents.keys())
        
        if context is None:
            context = {}
        
        task_id = f"swarm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.active_tasks[task_id] = {
            'task': task,
            'agents': agents,
            'context': context,
            'started_at': datetime.now(),
            'status': 'running'
        }
        
        logger.info(f"Starting swarm task {task_id} with agents: {agents}")
        
        # Execute tasks in parallel
        tasks_to_run = []
        for agent_name in agents:
            if agent_name in self.agents:
                agent_task = self._execute_agent_task(agent_name, task, context)
                tasks_to_run.append((agent_name, agent_task))
        
        # Wait for all agents to complete
        results = {}
        for agent_name, agent_task in tasks_to_run:
            try:
                result = await agent_task
                results[agent_name] = {
                    'status': 'success',
                    'result': result,
                    'completed_at': datetime.now()
                }
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}")
                results[agent_name] = {
                    'status': 'error',
                    'error': str(e),
                    'completed_at': datetime.now()
                }
        
        # Update task status
        self.active_tasks[task_id]['status'] = 'completed'
        self.active_tasks[task_id]['completed_at'] = datetime.now()
        self.active_tasks[task_id]['results'] = results
        
        # Cache results
        self.results_cache[task_id] = results
        
        logger.info(f"Completed swarm task {task_id}")
        
        return {
            'task_id': task_id,
            'task': task,
            'agents_used': agents,
            'results': results,
            'summary': self._generate_summary(results)
        }
    
    async def _execute_agent_task(self, agent_name: str, task: str, context: Dict) -> str:
        """Execute a task with a specific agent"""
        agent = self.agents[agent_name]
        
        # Prepare agent-specific task prompt
        agent_prompt = f"""
        Task: {task}
        
        Context: {context}
        
        As the {agent_name} agent, provide your specialized perspective and recommendations.
        Focus on your area of expertise and provide actionable insights.
        """
        
        # Execute the task (simulated async execution)
        await asyncio.sleep(0.1)  # Simulate processing time
        result = agent.run(agent_prompt)
        
        return result
    
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate a summary of swarm execution results"""
        successful_agents = [name for name, result in results.items() if result['status'] == 'success']
        failed_agents = [name for name, result in results.items() if result['status'] == 'error']
        
        summary = f"Swarm execution completed. "
        summary += f"Successful agents: {len(successful_agents)}, Failed agents: {len(failed_agents)}"
        
        if failed_agents:
            summary += f". Failed agents: {', '.join(failed_agents)}"
        
        return summary
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a specific task"""
        return self.active_tasks.get(task_id)
    
    def get_active_tasks(self) -> Dict:
        """Get all active tasks"""
        return {k: v for k, v in self.active_tasks.items() if v['status'] == 'running'}
    
    def get_agent_capabilities(self) -> Dict[str, str]:
        """Get capabilities of all agents"""
        return {
            name: agent.description 
            for name, agent in self.agents.items()
        }

# Global swarm coordinator instance
swarm_coordinator = SwarmCoordinator()

