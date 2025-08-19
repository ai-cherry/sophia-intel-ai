# agents/swarm_manager.py
from typing import List, Dict, Optional
from github import Github, GithubException
import os
import json
import time
import asyncio
import hashlib
from datetime import datetime

class SwarmManager:
    def __init__(self):
        self.github_client = Github(os.getenv("GH_FINE_GRAINED_TOKEN"))
        self.repo_name = "ai-cherry/sophia-intel"
        self.swarm_configs_path = "swarm_configs"
        
        # Available agent types and their capabilities
        self.agent_types = {
            "research": {
                "description": "Web research and information gathering",
                "capabilities": ["web_search", "content_analysis", "source_validation"],
                "deployment_time": 2.0
            },
            "analysis": {
                "description": "Data analysis and pattern recognition", 
                "capabilities": ["data_processing", "statistical_analysis", "trend_identification"],
                "deployment_time": 3.0
            },
            "coding": {
                "description": "Code generation and software development",
                "capabilities": ["code_generation", "debugging", "testing", "documentation"],
                "deployment_time": 4.0
            },
            "integration": {
                "description": "System integration and API management",
                "capabilities": ["api_integration", "workflow_automation", "system_monitoring"],
                "deployment_time": 3.5
            },
            "business": {
                "description": "Business intelligence and CRM operations",
                "capabilities": ["salesforce_ops", "hubspot_ops", "slack_integration", "reporting"],
                "deployment_time": 2.5
            }
        }
    
    async def trigger_swarm(self, task: str, agents: List[str], objective: str, user_id: str = "default") -> Dict:
        """Trigger a swarm of AI agents for a specific task"""
        try:
            # Generate unique task ID
            task_hash = hashlib.md5(f"{task}{objective}{time.time()}".encode()).hexdigest()[:8]
            coordinator_id = f"swarm_{task_hash}"
            task_id = f"task_{task_hash}"
            
            # Validate requested agents
            valid_agents = [agent for agent in agents if agent in self.agent_types]
            if not valid_agents:
                return {
                    "error": f"No valid agents specified. Available: {list(self.agent_types.keys())}",
                    "status": "failed"
                }
            
            # Create swarm configuration
            swarm_config = {
                "coordinator_id": coordinator_id,
                "task_id": task_id,
                "task": task,
                "objective": objective,
                "user_id": user_id,
                "agents": {},
                "created_at": datetime.now().isoformat(),
                "status": "initializing",
                "coordination_logs": []
            }
            
            # Deploy agents
            deployment_results = {}
            coordination_logs = [f"Task analyzed, {len(valid_agents)} agents required"]
            
            for agent_type in valid_agents:
                agent_id = f"{agent_type}_{hashlib.md5(f'{agent_type}{time.time()}'.encode()).hexdigest()[:8]}"
                
                # Simulate agent deployment
                await asyncio.sleep(0.1)  # Simulate deployment time
                
                agent_result = await self.deploy_agent(agent_type, agent_id, task, objective)
                deployment_results[agent_type] = agent_result
                
                swarm_config["agents"][agent_type] = {
                    "agent_id": agent_id,
                    "type": agent_type,
                    "status": agent_result["status"],
                    "capabilities": self.agent_types[agent_type]["capabilities"],
                    "deployed_at": datetime.now().isoformat(),
                    "result": agent_result.get("result", {})
                }
            
            coordination_logs.append(f"Agents initialized: {', '.join(valid_agents)}")
            
            # Execute parallel agent tasks
            execution_results = await self.execute_parallel_tasks(valid_agents, task, objective)
            
            # Update swarm config with results
            success_count = 0
            for agent_type, result in execution_results.items():
                if result["status"] == "success":
                    success_count += 1
                    swarm_config["agents"][agent_type]["result"] = result["result"]
                    swarm_config["agents"][agent_type]["status"] = "completed"
                else:
                    swarm_config["agents"][agent_type]["status"] = "failed"
                    swarm_config["agents"][agent_type]["error"] = result.get("error", "Unknown error")
            
            coordination_logs.append(f"Parallel execution completed with {success_count} successes")
            
            swarm_config["coordination_logs"] = coordination_logs
            swarm_config["status"] = "completed" if success_count > 0 else "failed"
            swarm_config["completed_at"] = datetime.now().isoformat()
            
            # Store swarm configuration in GitHub
            await self.store_swarm_config(coordinator_id, swarm_config)
            
            return {
                "coordinator_id": coordinator_id,
                "task_id": task_id,
                "task": task,
                "priority": "normal",
                "agents_used": valid_agents,
                "results": execution_results,
                "coordination_logs": coordination_logs,
                "timestamp": datetime.now().isoformat(),
                "status": swarm_config["status"]
            }
            
        except Exception as e:
            return {
                "error": f"Swarm deployment failed: {str(e)}",
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    async def deploy_agent(self, agent_type: str, agent_id: str, task: str, objective: str) -> Dict:
        """Deploy a specific agent type"""
        try:
            agent_info = self.agent_types.get(agent_type)
            if not agent_info:
                return {"status": "failed", "error": f"Unknown agent type: {agent_type}"}
            
            # Simulate agent deployment process
            await asyncio.sleep(agent_info["deployment_time"] * 0.1)  # Scaled down for demo
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "type": agent_type,
                "capabilities": agent_info["capabilities"],
                "deployed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def execute_parallel_tasks(self, agents: List[str], task: str, objective: str) -> Dict:
        """Execute tasks in parallel across deployed agents"""
        tasks = []
        
        for agent_type in agents:
            tasks.append(self.execute_agent_task(agent_type, task, objective))
        
        # Execute all agent tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        execution_results = {}
        for i, agent_type in enumerate(agents):
            if isinstance(results[i], Exception):
                execution_results[agent_type] = {
                    "status": "failed",
                    "error": str(results[i])
                }
            else:
                execution_results[agent_type] = results[i]
        
        return execution_results
    
    async def execute_agent_task(self, agent_type: str, task: str, objective: str) -> Dict:
        """Execute a specific task for an agent type"""
        try:
            agent_id = f"{agent_type}_{hashlib.md5(f'{agent_type}{time.time()}'.encode()).hexdigest()[:8]}"
            
            # Simulate different agent behaviors
            if agent_type == "research":
                result = await self.research_agent_task(task, objective)
            elif agent_type == "analysis":
                result = await self.analysis_agent_task(task, objective)
            elif agent_type == "coding":
                result = await self.coding_agent_task(task, objective)
            elif agent_type == "integration":
                result = await self.integration_agent_task(task, objective)
            elif agent_type == "business":
                result = await self.business_agent_task(task, objective)
            else:
                result = await self.generic_agent_task(agent_type, task, objective)
            
            return {
                "status": "success",
                "result": result,
                "agent_id": agent_id
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def research_agent_task(self, task: str, objective: str) -> Dict:
        """Research agent specific task execution"""
        await asyncio.sleep(0.5)  # Simulate research time
        
        # Simulate web search results
        sources = [
            {
                "title": f"Research on {task}",
                "url": f"https://example.com/research/{task.replace(' ', '-')}",
                "summary": f"Comprehensive analysis of {task} related to {objective}",
                "relevance_score": 0.85
            }
        ]
        
        return {
            "agent_id": f"research_{int(time.time()) % 100000:05d}",
            "task_id": f"research_{int(time.time()) % 100000:05d}",
            "query": task,
            "sources": sources,
            "summary": f"Found {len(sources)} sources related to '{task}'",
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
    
    async def analysis_agent_task(self, task: str, objective: str) -> Dict:
        """Analysis agent specific task execution"""
        await asyncio.sleep(0.7)  # Simulate analysis time
        
        return {
            "analysis_type": "trend_analysis",
            "findings": [
                f"Key trend identified in {task}",
                f"Correlation found with {objective}",
                "Statistical significance: 0.85"
            ],
            "confidence": 0.82,
            "recommendations": [
                f"Focus on {task} optimization",
                f"Monitor {objective} metrics"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    async def coding_agent_task(self, task: str, objective: str) -> Dict:
        """Coding agent specific task execution"""
        await asyncio.sleep(1.0)  # Simulate coding time
        
        return {
            "code_generated": f"# Code for {task}\n# Objective: {objective}\nprint('Hello from SOPHIA coding agent!')",
            "language": "python",
            "tests_created": True,
            "documentation": f"Documentation for {task} implementation",
            "timestamp": datetime.now().isoformat()
        }
    
    async def integration_agent_task(self, task: str, objective: str) -> Dict:
        """Integration agent specific task execution"""
        await asyncio.sleep(0.8)  # Simulate integration time
        
        return {
            "integrations_configured": [
                "API endpoints mapped",
                "Authentication configured",
                "Error handling implemented"
            ],
            "endpoints": [f"/api/v1/{task.lower().replace(' ', '_')}"],
            "status": "operational",
            "timestamp": datetime.now().isoformat()
        }
    
    async def business_agent_task(self, task: str, objective: str) -> Dict:
        """Business agent specific task execution"""
        await asyncio.sleep(0.6)  # Simulate business ops time
        
        return {
            "business_metrics": {
                "leads_processed": 25,
                "conversion_rate": 0.15,
                "revenue_impact": "$5,000"
            },
            "crm_updates": f"Updated records for {task}",
            "notifications_sent": 3,
            "timestamp": datetime.now().isoformat()
        }
    
    async def generic_agent_task(self, agent_type: str, task: str, objective: str) -> Dict:
        """Generic agent task execution"""
        await asyncio.sleep(0.5)
        
        return {
            "agent_type": agent_type,
            "task_completed": task,
            "objective_addressed": objective,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    
    async def store_swarm_config(self, coordinator_id: str, config: Dict):
        """Store swarm configuration in GitHub repository"""
        try:
            repo = self.github_client.get_repo(self.repo_name)
            config_path = f"{self.swarm_configs_path}/{coordinator_id}.json"
            commit_message = f"Deploy swarm {coordinator_id} for {config.get('objective', 'unknown objective')}"
            
            config_content = json.dumps(config, indent=2)
            
            try:
                # Try to update existing file
                contents = repo.get_contents(config_path, ref="main")
                repo.update_file(
                    config_path, 
                    commit_message, 
                    config_content, 
                    contents.sha, 
                    branch="main"
                )
            except GithubException:
                # File doesn't exist, create it
                repo.create_file(
                    config_path, 
                    commit_message, 
                    config_content, 
                    branch="main"
                )
            
        except Exception as e:
            print(f"Error storing swarm config: {str(e)}")
    
    async def get_swarm_status(self, coordinator_id: str) -> Optional[Dict]:
        """Get status of a specific swarm"""
        try:
            repo = self.github_client.get_repo(self.repo_name)
            config_path = f"{self.swarm_configs_path}/{coordinator_id}.json"
            
            contents = repo.get_contents(config_path, ref="main")
            config = json.loads(contents.decoded_content.decode())
            
            return config
            
        except Exception as e:
            print(f"Error getting swarm status: {str(e)}")
            return None
    
    async def list_active_swarms(self) -> List[Dict]:
        """List all active swarms"""
        try:
            repo = self.github_client.get_repo(self.repo_name)
            
            try:
                contents = repo.get_contents(self.swarm_configs_path, ref="main")
                swarms = []
                
                for item in contents:
                    if item.name.endswith('.json'):
                        config = json.loads(item.decoded_content.decode())
                        swarms.append({
                            "coordinator_id": config.get("coordinator_id"),
                            "status": config.get("status"),
                            "created_at": config.get("created_at"),
                            "task": config.get("task"),
                            "agents_count": len(config.get("agents", {}))
                        })
                
                return swarms
                
            except GithubException:
                # Directory doesn't exist yet
                return []
            
        except Exception as e:
            print(f"Error listing swarms: {str(e)}")
            return []

