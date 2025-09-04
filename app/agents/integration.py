"""
Agent Factory Integration with Sophia Intel AI

Seamless integration layer connecting the Agent Factory with existing
Sophia Intel AI infrastructure and services.
"""

import logging
import os
from typing import Dict, Any, Optional

from app.core.connections import get_connection_manager
from app.core.agent_config import get_config
from app.observability.prometheus_metrics import track_operation

from .agent_factory import get_factory, AgentFactory

logger = logging.getLogger(__name__)


class SophiaAgentFactory:
    """
    Integrated Agent Factory for Sophia Intel AI.
    Provides seamless integration with existing infrastructure.
    """

    def __init__(self):
        self.factory: Optional[AgentFactory] = None
        self._initialized = False

    async def initialize(self):
        """Initialize the factory with Sophia Intel AI configuration"""
        if self._initialized:
            return

        try:
            # Get Sophia configuration
            sophia_config = get_config()
            
            # Get database URL from environment or use SQLite
            database_url = os.getenv(
                "AGENT_FACTORY_DB_URL", 
                "sqlite:///sophia_agent_factory.db"
            )
            
            # Get API keys from environment
            portkey_key = os.getenv("PORTKEY_API_KEY")
            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            
            if not portkey_key or not openrouter_key:
                logger.warning(
                    "Agent Factory: API keys not configured. "
                    "Some features will be limited. Set PORTKEY_API_KEY and OPENROUTER_API_KEY."
                )
            
            # Initialize factory with Sophia configuration
            self.factory = await get_factory(
                database_url=database_url,
                portkey_api_key=portkey_key,
                openrouter_api_key=openrouter_key
            )
            
            # Ensure connection manager is initialized
            await get_connection_manager()
            
            self._initialized = True
            logger.info("Sophia Agent Factory initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Sophia Agent Factory: {e}")
            raise

    @track_operation("agent_factory_create_agent")
    async def create_agent(self, blueprint_name: str, **kwargs) -> Dict[str, Any]:
        """Create agent with Sophia metrics tracking"""
        if not self._initialized:
            await self.initialize()
        
        agent = await self.factory.create_agent(blueprint_name, **kwargs)
        
        return {
            "agent_id": agent.instance_id,
            "name": agent.name,
            "blueprint": blueprint_name,
            "status": agent.status.value,
            "created_at": agent.created_at.isoformat()
        }

    @track_operation("agent_factory_create_swarm")
    async def create_swarm(self, config_name: str, **kwargs) -> Dict[str, Any]:
        """Create swarm with Sophia metrics tracking"""
        if not self._initialized:
            await self.initialize()
        
        swarm = await self.factory.create_swarm(config_name, **kwargs)
        
        return {
            "swarm_id": swarm.instance_id,
            "name": swarm.name,
            "configuration": config_name,
            "status": swarm.status.value,
            "agent_count": swarm.agent_count,
            "created_at": swarm.created_at.isoformat()
        }

    @track_operation("agent_factory_execute_task")
    async def execute_agent_task(self, agent_id: str, task: str, **kwargs) -> Dict[str, Any]:
        """Execute agent task with Sophia metrics tracking"""
        if not self._initialized:
            await self.initialize()
        
        return await self.factory.execute_agent_task(agent_id, task, **kwargs)

    @track_operation("agent_factory_execute_swarm_task")
    async def execute_swarm_task(self, swarm_id: str, task: str, **kwargs) -> Dict[str, Any]:
        """Execute swarm task with Sophia metrics tracking"""
        if not self._initialized:
            await self.initialize()
        
        return await self.factory.execute_swarm_task(swarm_id, task, **kwargs)

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status for Sophia dashboards"""
        if not self._initialized:
            await self.initialize()
        
        # Get factory metrics
        factory_metrics = self.factory.get_factory_metrics()
        
        # Get health status
        health = await self.factory.health_check()
        
        # Get active resources
        active_agents = self.factory.list_agents(active_only=True)
        active_swarms = self.factory.list_swarms(active_only=True)
        
        return {
            "status": health["status"],
            "timestamp": factory_metrics["timestamp"],
            "agents": {
                "active": len(active_agents),
                "total_created": factory_metrics["instances"]["total_agents_created"],
                "utilization": factory_metrics["capacity"]["agent_utilization"]
            },
            "swarms": {
                "active": len(active_swarms),
                "total_created": factory_metrics["instances"]["total_swarms_created"],
                "utilization": factory_metrics["capacity"]["swarm_utilization"]
            },
            "performance": factory_metrics["performance"],
            "health_issues": health.get("issues", []),
            "catalog": factory_metrics["catalog"]
        }

    async def cleanup_and_optimize(self) -> Dict[str, Any]:
        """Cleanup inactive resources and optimize performance"""
        if not self._initialized:
            await self.initialize()
        
        # Perform cleanup
        cleanup_result = await self.factory.cleanup_inactive_resources()
        
        # Get updated metrics
        metrics = self.factory.get_factory_metrics()
        
        return {
            "cleanup": cleanup_result,
            "current_utilization": {
                "agents": metrics["capacity"]["agent_utilization"],
                "swarms": metrics["capacity"]["swarm_utilization"]
            },
            "timestamp": metrics["timestamp"]
        }

    async def close(self):
        """Gracefully shutdown the factory"""
        if self.factory:
            await self.factory.close()
            self._initialized = False
            logger.info("Sophia Agent Factory shutdown complete")


# Global instance for Sophia integration
_sophia_factory: Optional[SophiaAgentFactory] = None


async def get_sophia_factory() -> SophiaAgentFactory:
    """Get or create the global Sophia Agent Factory instance"""
    global _sophia_factory
    if _sophia_factory is None:
        _sophia_factory = SophiaAgentFactory()
    return _sophia_factory


# FastAPI integration helpers
def create_agent_factory_routes():
    """Create FastAPI routes for the Agent Factory"""
    from fastapi import APIRouter, HTTPException, BackgroundTasks
    from pydantic import BaseModel
    
    router = APIRouter(prefix="/agent-factory", tags=["Agent Factory"])
    
    class CreateAgentRequest(BaseModel):
        blueprint_name: str
        instance_name: Optional[str] = None
        config_overrides: Optional[Dict[str, Any]] = None
        context: Optional[Dict[str, Any]] = None
    
    class CreateSwarmRequest(BaseModel):
        config_name: str
        instance_name: Optional[str] = None
        input_data: Optional[Dict[str, Any]] = None
        agent_overrides: Optional[Dict[str, Any]] = None
    
    class ExecuteTaskRequest(BaseModel):
        task: str
        context: Optional[Dict[str, Any]] = None
        stream: bool = False
    
    @router.get("/status")
    async def get_factory_status():
        """Get Agent Factory system status"""
        try:
            factory = await get_sophia_factory()
            return await factory.get_system_status()
        except Exception as e:
            logger.error(f"Failed to get factory status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/catalog/blueprints")
    async def list_agent_blueprints(category: Optional[str] = None):
        """List available agent blueprints"""
        from . import get_catalog
        catalog = get_catalog()
        return catalog.list_blueprints(category=category)
    
    @router.get("/catalog/swarms")
    async def list_swarm_configs(category: Optional[str] = None):
        """List available swarm configurations"""
        from . import get_catalog
        catalog = get_catalog()
        return catalog.list_swarm_configs(category=category)
    
    @router.post("/agents")
    async def create_agent(request: CreateAgentRequest):
        """Create a new agent instance"""
        try:
            factory = await get_sophia_factory()
            return await factory.create_agent(
                blueprint_name=request.blueprint_name,
                instance_name=request.instance_name,
                config_overrides=request.config_overrides,
                context=request.context
            )
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/swarms")
    async def create_swarm(request: CreateSwarmRequest):
        """Create a new swarm instance"""
        try:
            factory = await get_sophia_factory()
            return await factory.create_swarm(
                config_name=request.config_name,
                instance_name=request.instance_name,
                input_data=request.input_data,
                agent_overrides=request.agent_overrides
            )
        except Exception as e:
            logger.error(f"Failed to create swarm: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/agents/{agent_id}/tasks")
    async def execute_agent_task(agent_id: str, request: ExecuteTaskRequest):
        """Execute a task with a specific agent"""
        try:
            factory = await get_sophia_factory()
            return await factory.execute_agent_task(
                agent_id=agent_id,
                task=request.task,
                context=request.context,
                stream=request.stream
            )
        except Exception as e:
            logger.error(f"Failed to execute agent task: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/swarms/{swarm_id}/tasks")
    async def execute_swarm_task(swarm_id: str, request: ExecuteTaskRequest):
        """Execute a task with a swarm"""
        try:
            factory = await get_sophia_factory()
            return await factory.execute_swarm_task(
                swarm_id=swarm_id,
                task=request.task,
                context=request.context
            )
        except Exception as e:
            logger.error(f"Failed to execute swarm task: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/agents")
    async def list_agents(status: Optional[str] = None, active_only: bool = False):
        """List agent instances"""
        try:
            factory = await get_sophia_factory()
            agents = factory.factory.list_agents(active_only=active_only)
            return [agent.to_dict() for agent in agents]
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/swarms")
    async def list_swarms(status: Optional[str] = None, active_only: bool = False):
        """List swarm instances"""
        try:
            factory = await get_sophia_factory()
            swarms = factory.factory.list_swarms(active_only=active_only)
            return [swarm.to_dict() for swarm in swarms]
        except Exception as e:
            logger.error(f"Failed to list swarms: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/maintenance/cleanup")
    async def cleanup_resources(background_tasks: BackgroundTasks):
        """Cleanup inactive resources"""
        try:
            factory = await get_sophia_factory()
            result = await factory.cleanup_and_optimize()
            return result
        except Exception as e:
            logger.error(f"Failed to cleanup resources: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/agents/{agent_id}/metrics")
    async def get_agent_metrics(agent_id: str, days: int = 7):
        """Get metrics for a specific agent"""
        try:
            factory = await get_sophia_factory()
            return factory.factory.get_agent_metrics(agent_id, days)
        except Exception as e:
            logger.error(f"Failed to get agent metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/swarms/{swarm_id}/metrics")
    async def get_swarm_metrics(swarm_id: str, days: int = 7):
        """Get metrics for a specific swarm"""
        try:
            factory = await get_sophia_factory()
            return factory.factory.get_swarm_metrics(swarm_id, days)
        except Exception as e:
            logger.error(f"Failed to get swarm metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router


# WebSocket integration for real-time updates
def create_agent_factory_websocket():
    """Create WebSocket endpoint for real-time Agent Factory updates"""
    from fastapi import WebSocket
    import json
    import asyncio
    
    async def agent_factory_websocket(websocket: WebSocket):
        """WebSocket endpoint for real-time factory updates"""
        await websocket.accept()
        
        try:
            factory = await get_sophia_factory()
            
            # Send initial status
            status = await factory.get_system_status()
            await websocket.send_text(json.dumps({
                "type": "status",
                "data": status
            }))
            
            # Send periodic updates
            while True:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                try:
                    status = await factory.get_system_status()
                    await websocket.send_text(json.dumps({
                        "type": "status_update",
                        "data": status
                    }))
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.close()
    
    return agent_factory_websocket


# CLI integration
def create_agent_factory_cli():
    """Create CLI commands for Agent Factory management"""
    import click
    import asyncio
    
    @click.group()
    def agent_factory():
        """Agent Factory management commands"""
        pass
    
    @agent_factory.command()
    def status():
        """Get factory status"""
        async def _status():
            factory = await get_sophia_factory()
            status = await factory.get_system_status()
            click.echo(json.dumps(status, indent=2))
        
        asyncio.run(_status())
    
    @agent_factory.command()
    @click.argument('blueprint_name')
    @click.option('--name', help='Instance name')
    def create_agent(blueprint_name, name):
        """Create a new agent"""
        async def _create():
            factory = await get_sophia_factory()
            result = await factory.create_agent(blueprint_name, instance_name=name)
            click.echo(f"Created agent: {result['agent_id']}")
        
        asyncio.run(_create())
    
    @agent_factory.command()
    @click.argument('config_name')
    @click.option('--name', help='Instance name')
    def create_swarm(config_name, name):
        """Create a new swarm"""
        async def _create():
            factory = await get_sophia_factory()
            result = await factory.create_swarm(config_name, instance_name=name)
            click.echo(f"Created swarm: {result['swarm_id']} with {result['agent_count']} agents")
        
        asyncio.run(_create())
    
    @agent_factory.command()
    def cleanup():
        """Cleanup inactive resources"""
        async def _cleanup():
            factory = await get_sophia_factory()
            result = await factory.cleanup_and_optimize()
            click.echo(f"Cleaned up {result['cleanup']['agents_cleaned']} agents and {result['cleanup']['swarms_cleaned']} swarms")
        
        asyncio.run(_cleanup())
    
    return agent_factory