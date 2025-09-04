"""
Agent Factory Demonstration Script

Shows how to use the Agent Factory system with various scenarios.
Run this to see the system in action with comprehensive examples.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any

from dotenv import load_dotenv

from . import (
    get_factory, 
    get_catalog,
    create_quick_agent,
    create_quick_swarm,
    AgentFactory
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentFactoryDemo:
    """Comprehensive demonstration of Agent Factory capabilities"""

    def __init__(self):
        self.factory: AgentFactory = None
        self.demo_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "scenarios": {},
            "performance": {},
            "errors": []
        }

    async def setup(self):
        """Initialize the factory and load environment"""
        load_dotenv('.env.local')
        
        # Get API keys from environment
        portkey_key = os.getenv("PORTKEY_API_KEY")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        
        if not portkey_key or not openrouter_key:
            logger.warning("API keys not found in environment. Some features will be limited.")
        
        # Initialize factory
        self.factory = await get_factory(
            database_url="sqlite:///demo_agent_factory.db",
            portkey_api_key=portkey_key,
            openrouter_api_key=openrouter_key
        )
        
        logger.info("Agent Factory Demo initialized successfully")

    async def demo_catalog_exploration(self):
        """Demonstrate catalog exploration capabilities"""
        logger.info("=== DEMO: Catalog Exploration ===")
        
        try:
            catalog = get_catalog()
            
            # Get catalog statistics
            stats = catalog.get_catalog_stats()
            logger.info(f"Catalog Statistics: {json.dumps(stats, indent=2)}")
            
            # List all blueprints
            blueprints = catalog.list_blueprints()
            logger.info(f"Available Blueprints ({len(blueprints)}):")
            for bp in blueprints[:5]:  # Show first 5
                logger.info(f"  - {bp['name']}: {bp['description'][:80]}...")
            
            # List swarm configurations
            swarm_configs = catalog.list_swarm_configs()
            logger.info(f"Available Swarm Configs ({len(swarm_configs)}):")
            for sc in swarm_configs:
                logger.info(f"  - {sc['name']}: {sc['description'][:80]}...")
            
            # Search functionality
            search_results = catalog.search_blueprints("developer")
            logger.info(f"Search results for 'developer': {len(search_results)} found")
            
            self.demo_results["scenarios"]["catalog"] = {
                "status": "success",
                "stats": stats,
                "blueprint_count": len(blueprints),
                "swarm_config_count": len(swarm_configs)
            }
            
        except Exception as e:
            logger.error(f"Catalog demo failed: {e}")
            self.demo_results["errors"].append(f"catalog_demo: {str(e)}")

    async def demo_single_agent_creation(self):
        """Demonstrate single agent creation and execution"""
        logger.info("=== DEMO: Single Agent Creation ===")
        
        try:
            # Create a senior developer agent
            agent = await create_quick_agent(
                "senior_developer",
                instance_name="Demo Developer",
                context={"project": "agent_factory_demo"}
            )
            
            logger.info(f"Created agent: {agent.instance_id} ({agent.name})")
            
            # Get agent details
            agent_details = agent.to_dict()
            logger.info(f"Agent status: {agent_details['status']}")
            
            # Execute a simple task (only if API keys available)
            task_result = None
            if self.factory.portkey_client:
                try:
                    task_result = await self.factory.execute_agent_task(
                        agent.instance_id,
                        "Write a simple Python function to validate an email address using regex. Include proper error handling and documentation.",
                        context={"format": "production_ready"}
                    )
                    logger.info("Task executed successfully")
                    
                except Exception as e:
                    logger.warning(f"Task execution failed (API keys might be invalid): {e}")
            
            # Get agent metrics
            metrics = self.factory.get_agent_metrics(agent.instance_id)
            logger.info(f"Agent metrics: {json.dumps(metrics, indent=2)}")
            
            # Stop the agent
            stopped = await self.factory.stop_agent(agent.instance_id)
            logger.info(f"Agent stopped: {stopped}")
            
            self.demo_results["scenarios"]["single_agent"] = {
                "status": "success",
                "agent_id": agent.instance_id,
                "task_executed": task_result is not None,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Single agent demo failed: {e}")
            self.demo_results["errors"].append(f"single_agent_demo: {str(e)}")

    async def demo_swarm_creation(self):
        """Demonstrate swarm creation and coordination"""
        logger.info("=== DEMO: Swarm Creation ===")
        
        try:
            # Create a research analysis swarm
            swarm = await create_quick_swarm(
                "research_analysis",
                instance_name="Demo Research Team",
                input_data={"topic": "AI agent architectures", "depth": "comprehensive"}
            )
            
            logger.info(f"Created swarm: {swarm.instance_id} ({swarm.name})")
            logger.info(f"Swarm has {swarm.agent_count} agents")
            
            # Get swarm details
            swarm_details = swarm.to_dict()
            logger.info(f"Swarm status: {swarm_details['status']}")
            
            # List swarm members
            members = self.factory.list_agents(active_only=True)
            swarm_members = [a for a in members if 'swarm' in (a.context or {})]
            logger.info(f"Swarm members: {[m.name for m in swarm_members]}")
            
            # Execute a swarm task (only if API keys available)
            swarm_result = None
            if self.factory.portkey_client:
                try:
                    swarm_result = await self.factory.execute_swarm_task(
                        swarm.instance_id,
                        "Research and analyze the current state of multi-agent AI systems, focusing on coordination mechanisms and real-world applications."
                    )
                    logger.info("Swarm task executed successfully")
                    
                except Exception as e:
                    logger.warning(f"Swarm task execution failed: {e}")
            
            # Get swarm metrics
            metrics = self.factory.get_swarm_metrics(swarm.instance_id)
            logger.info(f"Swarm metrics: {json.dumps(metrics, indent=2)}")
            
            # Stop the swarm
            stopped = await self.factory.stop_swarm(swarm.instance_id)
            logger.info(f"Swarm stopped: {stopped}")
            
            self.demo_results["scenarios"]["swarm"] = {
                "status": "success",
                "swarm_id": swarm.instance_id,
                "agent_count": swarm.agent_count,
                "task_executed": swarm_result is not None,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Swarm demo failed: {e}")
            self.demo_results["errors"].append(f"swarm_demo: {str(e)}")

    async def demo_performance_monitoring(self):
        """Demonstrate performance monitoring and analytics"""
        logger.info("=== DEMO: Performance Monitoring ===")
        
        try:
            # Get factory-wide metrics
            factory_metrics = self.factory.get_factory_metrics()
            logger.info(f"Factory Metrics: {json.dumps(factory_metrics, indent=2)}")
            
            # Perform health check
            health = await self.factory.health_check()
            logger.info(f"Health Check: {json.dumps(health, indent=2)}")
            
            # Test cleanup functionality
            cleanup_result = await self.factory.cleanup_inactive_resources(max_age_hours=0)
            logger.info(f"Cleanup Results: {cleanup_result}")
            
            self.demo_results["scenarios"]["monitoring"] = {
                "status": "success",
                "factory_metrics": factory_metrics,
                "health_status": health["status"],
                "cleanup_results": cleanup_result
            }
            
        except Exception as e:
            logger.error(f"Performance monitoring demo failed: {e}")
            self.demo_results["errors"].append(f"monitoring_demo: {str(e)}")

    async def demo_advanced_scenarios(self):
        """Demonstrate advanced usage scenarios"""
        logger.info("=== DEMO: Advanced Scenarios ===")
        
        try:
            # Scenario 1: Custom agent with overrides
            custom_agent = await self.factory.create_agent(
                "generalist",
                instance_name="Custom Generalist",
                config_overrides={
                    "temperature": 0.8,
                    "max_tokens": 2048
                },
                context={
                    "role": "creative_assistant",
                    "personality": "enthusiastic",
                    "expertise": ["writing", "brainstorming"]
                }
            )
            logger.info(f"Created custom agent: {custom_agent.instance_id}")
            
            # Scenario 2: Multi-agent collaboration simulation
            agents = []
            for i in range(3):
                agent = await create_quick_agent(
                    "generalist",
                    instance_name=f"Collaborator {i+1}",
                    context={"team": "demo_collaboration", "role": f"member_{i+1}"}
                )
                agents.append(agent)
            
            logger.info(f"Created collaboration team with {len(agents)} agents")
            
            # Stop all demo agents
            for agent in agents + [custom_agent]:
                await self.factory.stop_agent(agent.instance_id)
            
            self.demo_results["scenarios"]["advanced"] = {
                "status": "success",
                "custom_agent_created": True,
                "collaboration_team_size": len(agents)
            }
            
        except Exception as e:
            logger.error(f"Advanced scenarios demo failed: {e}")
            self.demo_results["errors"].append(f"advanced_demo: {str(e)}")

    async def demo_blueprint_management(self):
        """Demonstrate blueprint management capabilities"""
        logger.info("=== DEMO: Blueprint Management ===")
        
        try:
            # Create a custom blueprint
            custom_blueprint_data = {
                "name": "demo_specialist",
                "display_name": "Demo Specialist Agent",
                "description": "A specialized agent created for demonstration purposes",
                "category": "demo",
                "tier": "standard",
                "task_types": ["general", "analysis"],
                "capabilities": {
                    "problem_solving": 8.0,
                    "communication": 7.5,
                    "demo_tasks": 9.0
                },
                "tools": ["calculator", "text_processor"],
                "guardrails": ["accurate_responses_only"],
                "model_config": {
                    "temperature": 0.5,
                    "max_tokens": 4096,
                    "cost_limit_per_request": 0.5,
                    "timeout_seconds": 120,
                    "retry_attempts": 3,
                    "enable_fallback": True,
                    "enable_emergency_fallback": True,
                    "top_p": 1.0,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0
                },
                "system_prompt_template": "You are a Demo Specialist Agent. Help with demonstration tasks effectively. Context: {context}, Task: {task}",
                "version": "1.0.0",
                "author": "Agent Factory Demo",
                "tags": ["demo", "test", "custom"]
            }
            
            # Create the blueprint
            blueprint = self.factory.create_blueprint(custom_blueprint_data)
            logger.info(f"Created custom blueprint: {blueprint.name}")
            
            # Create an agent from the custom blueprint
            demo_agent = await self.factory.create_agent(
                "demo_specialist",
                instance_name="Demo Specialist Instance"
            )
            logger.info(f"Created agent from custom blueprint: {demo_agent.instance_id}")
            
            # Clean up
            await self.factory.stop_agent(demo_agent.instance_id)
            
            self.demo_results["scenarios"]["blueprint_management"] = {
                "status": "success",
                "custom_blueprint_created": blueprint.name,
                "agent_from_custom_blueprint": demo_agent.instance_id
            }
            
        except Exception as e:
            logger.error(f"Blueprint management demo failed: {e}")
            self.demo_results["errors"].append(f"blueprint_demo: {str(e)}")

    async def run_all_demos(self):
        """Run all demonstration scenarios"""
        logger.info("Starting Agent Factory Comprehensive Demo")
        logger.info("=" * 60)
        
        start_time = datetime.utcnow()
        
        # Setup
        await self.setup()
        
        # Run all demo scenarios
        demo_scenarios = [
            self.demo_catalog_exploration,
            self.demo_single_agent_creation,
            self.demo_swarm_creation,
            self.demo_performance_monitoring,
            self.demo_advanced_scenarios,
            self.demo_blueprint_management
        ]
        
        for scenario in demo_scenarios:
            try:
                await scenario()
            except Exception as e:
                logger.error(f"Demo scenario failed: {e}")
                self.demo_results["errors"].append(f"{scenario.__name__}: {str(e)}")
        
        # Final metrics
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        self.demo_results["performance"] = {
            "total_execution_time_seconds": execution_time,
            "scenarios_run": len(demo_scenarios),
            "scenarios_successful": len(self.demo_results["scenarios"]),
            "errors_encountered": len(self.demo_results["errors"])
        }
        
        # Cleanup
        await self.factory.cleanup_inactive_resources(max_age_hours=0)
        await self.factory.close()
        
        # Print summary
        logger.info("=" * 60)
        logger.info("DEMO COMPLETE - Summary:")
        logger.info(f"Execution Time: {execution_time:.2f} seconds")
        logger.info(f"Scenarios Run: {len(demo_scenarios)}")
        logger.info(f"Successful: {len(self.demo_results['scenarios'])}")
        logger.info(f"Errors: {len(self.demo_results['errors'])}")
        
        if self.demo_results["errors"]:
            logger.info("Errors encountered:")
            for error in self.demo_results["errors"]:
                logger.info(f"  - {error}")
        
        logger.info("Demo results saved to demo_results.json")
        
        # Save results
        with open("demo_results.json", "w") as f:
            json.dump(self.demo_results, f, indent=2, default=str)
        
        return self.demo_results


async def run_quick_demo():
    """Run a quick demonstration of core features"""
    logger.info("Running Quick Agent Factory Demo")
    
    try:
        # Initialize factory
        factory = await get_factory()
        
        # Create a simple agent
        agent = await create_quick_agent("generalist")
        logger.info(f"Created agent: {agent.instance_id}")
        
        # Get factory metrics
        metrics = factory.get_factory_metrics()
        logger.info(f"Factory has {metrics['instances']['active_agents']} active agents")
        
        # Stop agent
        await factory.stop_agent(agent.instance_id)
        logger.info("Agent stopped successfully")
        
        # Health check
        health = await factory.health_check()
        logger.info(f"Factory health: {health['status']}")
        
        await factory.close()
        logger.info("Quick demo completed successfully")
        
    except Exception as e:
        logger.error(f"Quick demo failed: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    # Choose demo type
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(run_quick_demo())
    else:
        demo = AgentFactoryDemo()
        asyncio.run(demo.run_all_demos())