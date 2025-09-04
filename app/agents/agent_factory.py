"""
Agent Factory - Comprehensive Agent and Swarm Management System

Production-ready agent factory for creating, managing, and orchestrating AI agents
and swarms. Integrated with Sophia Intel AI's existing infrastructure.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.agent_config import get_config, get_role_config, ModelConfig
from app.core.connections import get_connection_manager
from app.models.portkey_dynamic_client import DynamicPortkeyClient
from app.models.openrouter_latest import TaskType as ORTaskType, ModelTier

from .agent_catalog import get_catalog, AgentCatalog
from .models import (
    Base,
    AgentBlueprint,
    AgentInstance,
    AgentStatus,
    SwarmConfiguration,
    SwarmInstance,
    SwarmMembership,
    SwarmStatus,
    AgentTier,
    TaskType,
    AgentMetrics,
    SwarmMetrics,
    FactoryUsage,
    create_tables,
    get_model_config_dict,
    dict_to_model_config
)

logger = logging.getLogger(__name__)


class AgentFactoryError(Exception):
    """Base exception for Agent Factory operations"""
    pass


class AgentCreationError(AgentFactoryError):
    """Error during agent creation"""
    pass


class SwarmCreationError(AgentFactoryError):
    """Error during swarm creation"""
    pass


class ResourceLimitError(AgentFactoryError):
    """Error when resource limits are exceeded"""
    pass


class AgentFactory:
    """
    Comprehensive Agent Factory for creating, managing, and orchestrating AI agents and swarms.
    
    Features:
    - Agent lifecycle management (create, start, stop, monitor)
    - Swarm orchestration and coordination
    - Performance tracking and analytics
    - Resource management and optimization
    - Integration with Portkey and existing systems
    - Database persistence and state management
    """

    def __init__(self, 
                 database_url: str = "sqlite:///agent_factory.db",
                 portkey_api_key: Optional[str] = None,
                 openrouter_api_key: Optional[str] = None,
                 max_concurrent_agents: int = 50,
                 max_concurrent_swarms: int = 10):
        """
        Initialize the Agent Factory.
        
        Args:
            database_url: Database connection URL
            portkey_api_key: Portkey API key for model access
            openrouter_api_key: OpenRouter API key
            max_concurrent_agents: Maximum concurrent agent instances
            max_concurrent_swarms: Maximum concurrent swarm instances
        """
        self.database_url = database_url
        self.max_concurrent_agents = max_concurrent_agents
        self.max_concurrent_swarms = max_concurrent_swarms
        
        # Initialize database
        self.engine = create_engine(database_url, echo=False)
        create_tables(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize components
        self.catalog = get_catalog()
        self.config = get_config()
        
        # Initialize Portkey client if keys provided
        self.portkey_client = None
        if portkey_api_key and openrouter_api_key:
            self.portkey_client = DynamicPortkeyClient(
                portkey_api_key=portkey_api_key,
                openrouter_api_key=openrouter_api_key
            )
        
        # Runtime tracking
        self.active_agents: Dict[str, AgentInstance] = {}
        self.active_swarms: Dict[str, SwarmInstance] = {}
        self.performance_metrics: Dict[str, Any] = {
            "total_agents_created": 0,
            "total_swarms_created": 0,
            "total_tasks_completed": 0,
            "total_cost": 0.0,
            "avg_response_time_ms": 1000
        }
        
        logger.info("Agent Factory initialized successfully")

    # ==========================================================================
    # Database Operations
    # ==========================================================================

    def get_db_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def close_db_session(self, session: Session) -> None:
        """Close database session safely"""
        try:
            session.close()
        except Exception as e:
            logger.error(f"Error closing database session: {e}")

    # ==========================================================================
    # Blueprint Management
    # ==========================================================================

    def create_blueprint(self, blueprint_data: Dict[str, Any]) -> AgentBlueprint:
        """
        Create a new agent blueprint from configuration data.
        
        Args:
            blueprint_data: Blueprint configuration dictionary
            
        Returns:
            Created AgentBlueprint instance
            
        Raises:
            AgentCreationError: If blueprint creation fails
        """
        session = self.get_db_session()
        
        try:
            # Validate blueprint data
            errors = self.catalog.validate_blueprint(blueprint_data)
            if errors:
                raise AgentCreationError(f"Blueprint validation failed: {'; '.join(errors)}")
            
            # Create blueprint instance
            blueprint = AgentBlueprint(
                name=blueprint_data["name"],
                display_name=blueprint_data["display_name"],
                description=blueprint_data["description"],
                category=blueprint_data["category"],
                tier=AgentTier(blueprint_data.get("tier", "standard")),
                task_types=blueprint_data.get("task_types", []),
                capabilities=blueprint_data.get("capabilities", {}),
                tools=blueprint_data.get("tools", []),
                guardrails=blueprint_data.get("guardrails", []),
                model_config=blueprint_data["model_config"],
                system_prompt_template=blueprint_data.get("system_prompt_template"),
                memory_mb=blueprint_data.get("memory_mb", 512),
                cpu_cores=blueprint_data.get("cpu_cores", 0.5),
                gpu_required=blueprint_data.get("gpu_required", False),
                avg_response_time_ms=blueprint_data.get("avg_response_time_ms", 1000),
                cost_per_1k_tokens=blueprint_data.get("cost_per_1k_tokens", 0.01),
                quality_score=blueprint_data.get("quality_score", 7.5),
                version=blueprint_data.get("version", "1.0.0"),
                author=blueprint_data.get("author", "Agent Factory"),
                tags=blueprint_data.get("tags", [])
            )
            
            session.add(blueprint)
            session.commit()
            session.refresh(blueprint)
            
            logger.info(f"Created agent blueprint: {blueprint.name}")
            return blueprint
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error creating blueprint: {e}")
            raise AgentCreationError(f"Failed to create blueprint: {e}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating blueprint: {e}")
            raise AgentCreationError(f"Blueprint creation failed: {e}")
        finally:
            self.close_db_session(session)

    def get_blueprint(self, blueprint_id: Union[int, str]) -> Optional[AgentBlueprint]:
        """
        Get agent blueprint by ID or name.
        
        Args:
            blueprint_id: Blueprint ID (int) or name (str)
            
        Returns:
            AgentBlueprint instance or None if not found
        """
        session = self.get_db_session()
        
        try:
            if isinstance(blueprint_id, int):
                return session.query(AgentBlueprint).filter_by(id=blueprint_id).first()
            else:
                return session.query(AgentBlueprint).filter_by(name=blueprint_id).first()
        finally:
            self.close_db_session(session)

    def list_blueprints(self, 
                       category: Optional[str] = None,
                       tier: Optional[AgentTier] = None) -> List[AgentBlueprint]:
        """
        List agent blueprints with optional filtering.
        
        Args:
            category: Filter by category
            tier: Filter by tier
            
        Returns:
            List of AgentBlueprint instances
        """
        session = self.get_db_session()
        
        try:
            query = session.query(AgentBlueprint)
            
            if category:
                query = query.filter_by(category=category)
            if tier:
                query = query.filter_by(tier=tier)
                
            return query.order_by(AgentBlueprint.name).all()
        finally:
            self.close_db_session(session)

    def update_blueprint(self, blueprint_id: Union[int, str], 
                        updates: Dict[str, Any]) -> Optional[AgentBlueprint]:
        """
        Update an existing agent blueprint.
        
        Args:
            blueprint_id: Blueprint ID or name
            updates: Dictionary of fields to update
            
        Returns:
            Updated AgentBlueprint or None if not found
        """
        session = self.get_db_session()
        
        try:
            blueprint = self.get_blueprint(blueprint_id)
            if not blueprint:
                return None
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(blueprint, key):
                    setattr(blueprint, key, value)
            
            blueprint.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(blueprint)
            
            logger.info(f"Updated blueprint: {blueprint.name}")
            return blueprint
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating blueprint: {e}")
            return None
        finally:
            self.close_db_session(session)

    # ==========================================================================
    # Agent Instance Management
    # ==========================================================================

    async def create_agent(self, 
                          blueprint_name: str,
                          instance_name: Optional[str] = None,
                          config_overrides: Optional[Dict[str, Any]] = None,
                          context: Optional[Dict[str, Any]] = None) -> AgentInstance:
        """
        Create a new agent instance from a blueprint.
        
        Args:
            blueprint_name: Name of the blueprint to use
            instance_name: Custom name for the instance
            config_overrides: Configuration overrides
            context: Initial context for the agent
            
        Returns:
            Created AgentInstance
            
        Raises:
            AgentCreationError: If agent creation fails
            ResourceLimitError: If resource limits exceeded
        """
        # Check resource limits
        if len(self.active_agents) >= self.max_concurrent_agents:
            raise ResourceLimitError(f"Maximum concurrent agents ({self.max_concurrent_agents}) exceeded")
        
        session = self.get_db_session()
        
        try:
            # Get blueprint
            blueprint = self.get_blueprint(blueprint_name)
            if not blueprint:
                # Try to get from catalog
                catalog_blueprint = self.catalog.get_blueprint(blueprint_name)
                if catalog_blueprint:
                    blueprint = self.create_blueprint(catalog_blueprint)
                else:
                    raise AgentCreationError(f"Blueprint not found: {blueprint_name}")
            
            # Generate instance ID and name
            instance_id = f"agent_{uuid.uuid4().hex[:8]}"
            if not instance_name:
                instance_name = f"{blueprint.display_name} #{len(self.active_agents) + 1}"
            
            # Create agent instance
            agent = AgentInstance(
                instance_id=instance_id,
                name=instance_name,
                blueprint_id=blueprint.id,
                status=AgentStatus.ACTIVE,
                config_overrides=config_overrides or {},
                context=context or {}
            )
            
            session.add(agent)
            session.commit()
            session.refresh(agent)
            
            # Add to active agents
            self.active_agents[instance_id] = agent
            self.performance_metrics["total_agents_created"] += 1
            
            # Update blueprint usage
            blueprint.usage_count += 1
            session.commit()
            
            logger.info(f"Created agent instance: {instance_id} ({blueprint_name})")
            
            # Record usage
            await self._record_usage("create_agent", "agent", instance_id, 
                                   {"blueprint": blueprint_name})
            
            return agent
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error creating agent: {e}")
            raise AgentCreationError(f"Failed to create agent: {e}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating agent: {e}")
            raise AgentCreationError(f"Agent creation failed: {e}")
        finally:
            self.close_db_session(session)

    def get_agent(self, agent_id: str) -> Optional[AgentInstance]:
        """
        Get agent instance by ID.
        
        Args:
            agent_id: Agent instance ID
            
        Returns:
            AgentInstance or None if not found
        """
        # Check active agents first
        if agent_id in self.active_agents:
            return self.active_agents[agent_id]
        
        # Query database
        session = self.get_db_session()
        try:
            return session.query(AgentInstance).filter_by(instance_id=agent_id).first()
        finally:
            self.close_db_session(session)

    def list_agents(self, 
                   status: Optional[AgentStatus] = None,
                   blueprint_name: Optional[str] = None,
                   active_only: bool = False) -> List[AgentInstance]:
        """
        List agent instances with optional filtering.
        
        Args:
            status: Filter by status
            blueprint_name: Filter by blueprint name
            active_only: Only return currently active agents
            
        Returns:
            List of AgentInstance objects
        """
        if active_only:
            agents = list(self.active_agents.values())
            if status:
                agents = [a for a in agents if a.status == status]
            return agents
        
        session = self.get_db_session()
        
        try:
            query = session.query(AgentInstance)
            
            if status:
                query = query.filter_by(status=status)
            
            if blueprint_name:
                blueprint = self.get_blueprint(blueprint_name)
                if blueprint:
                    query = query.filter_by(blueprint_id=blueprint.id)
                else:
                    return []
            
            return query.order_by(desc(AgentInstance.created_at)).all()
        finally:
            self.close_db_session(session)

    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop an active agent instance.
        
        Args:
            agent_id: Agent instance ID
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_db_session()
        
        try:
            agent = self.get_agent(agent_id)
            if not agent:
                logger.warning(f"Agent not found: {agent_id}")
                return False
            
            # Update status
            agent.status = AgentStatus.INACTIVE
            agent.last_active = datetime.utcnow()
            session.commit()
            
            # Remove from active agents
            if agent_id in self.active_agents:
                del self.active_agents[agent_id]
            
            logger.info(f"Stopped agent: {agent_id}")
            
            # Record usage
            await self._record_usage("stop_agent", "agent", agent_id)
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error stopping agent {agent_id}: {e}")
            return False
        finally:
            self.close_db_session(session)

    async def restart_agent(self, agent_id: str) -> bool:
        """
        Restart an inactive agent instance.
        
        Args:
            agent_id: Agent instance ID
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_db_session()
        
        try:
            agent = self.get_agent(agent_id)
            if not agent:
                logger.warning(f"Agent not found: {agent_id}")
                return False
            
            if len(self.active_agents) >= self.max_concurrent_agents:
                raise ResourceLimitError("Maximum concurrent agents exceeded")
            
            # Update status
            agent.status = AgentStatus.ACTIVE
            agent.last_active = datetime.utcnow()
            session.commit()
            
            # Add to active agents
            self.active_agents[agent_id] = agent
            
            logger.info(f"Restarted agent: {agent_id}")
            
            # Record usage
            await self._record_usage("restart_agent", "agent", agent_id)
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error restarting agent {agent_id}: {e}")
            return False
        finally:
            self.close_db_session(session)

    async def execute_agent_task(self, 
                                agent_id: str,
                                task: str,
                                context: Optional[Dict[str, Any]] = None,
                                stream: bool = False) -> Dict[str, Any]:
        """
        Execute a task with a specific agent.
        
        Args:
            agent_id: Agent instance ID
            task: Task description
            context: Additional context
            stream: Enable streaming response
            
        Returns:
            Task execution result
            
        Raises:
            AgentFactoryError: If execution fails
        """
        agent = self.get_agent(agent_id)
        if not agent or agent.status != AgentStatus.ACTIVE:
            raise AgentFactoryError(f"Agent not available: {agent_id}")
        
        if not self.portkey_client:
            raise AgentFactoryError("Portkey client not configured")
        
        session = self.get_db_session()
        start_time = datetime.utcnow()
        
        try:
            # Get agent blueprint and configuration
            blueprint = session.query(AgentBlueprint).filter_by(id=agent.blueprint_id).first()
            if not blueprint:
                raise AgentFactoryError(f"Blueprint not found for agent: {agent_id}")
            
            # Merge configuration
            model_config = dict_to_model_config(blueprint.model_config)
            if agent.config_overrides:
                for key, value in agent.config_overrides.items():
                    if hasattr(model_config, key):
                        setattr(model_config, key, value)
            
            # Prepare messages
            system_prompt = blueprint.system_prompt_template
            if system_prompt and context:
                system_prompt = system_prompt.format(**context)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": task})
            
            # Add agent context
            if agent.context:
                messages.insert(-1, {
                    "role": "system", 
                    "content": f"Agent Context: {json.dumps(agent.context)}"
                })
            
            # Determine model and task type
            primary_task = blueprint.task_types[0] if blueprint.task_types else TaskType.GENERAL
            or_task = getattr(ORTaskType, primary_task.value.upper(), ORTaskType.GENERAL)
            
            tier_mapping = {
                AgentTier.BASIC: ModelTier.FREE,
                AgentTier.STANDARD: ModelTier.BALANCED,
                AgentTier.PREMIUM: ModelTier.PREMIUM,
                AgentTier.ENTERPRISE: ModelTier.PREMIUM
            }
            model_tier = tier_mapping.get(blueprint.tier, ModelTier.BALANCED)
            
            # Execute task
            agent.current_task_id = f"task_{uuid.uuid4().hex[:8]}"
            agent.last_active = datetime.utcnow()
            session.commit()
            
            if stream:
                # Stream response
                async def stream_generator():
                    async for chunk in self.portkey_client.stream_completion(
                        messages=messages,
                        task=or_task,
                        budget=model_tier,
                        **model_config.dict()
                    ):
                        yield chunk
                
                return {"stream": stream_generator(), "task_id": agent.current_task_id}
            
            else:
                # Regular response
                response = await self.portkey_client.create_completion(
                    messages=messages,
                    task=or_task,
                    budget=model_tier,
                    **model_config.dict()
                )
                
                # Update metrics
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if "usage" in response:
                    usage = response["usage"]
                    agent.total_tokens_used += usage.get("total_tokens", 0)
                    agent.total_cost += self.portkey_client.estimate_cost(
                        response.get("model", "unknown"),
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0)
                    )
                
                agent.tasks_completed += 1
                agent.avg_response_time_ms = int(
                    (agent.avg_response_time_ms + execution_time) / 2
                )
                agent.current_task_id = None
                session.commit()
                
                self.performance_metrics["total_tasks_completed"] += 1
                self.performance_metrics["total_cost"] += agent.total_cost
                
                # Record usage
                await self._record_usage("execute_task", "agent", agent_id, {
                    "task_length": len(task),
                    "execution_time_ms": execution_time,
                    "tokens_used": usage.get("total_tokens", 0) if "usage" in response else 0
                })
                
                return {
                    "result": response,
                    "agent_id": agent_id,
                    "task_id": agent.current_task_id,
                    "execution_time_ms": execution_time,
                    "tokens_used": usage.get("total_tokens", 0) if "usage" in response else 0
                }
            
        except Exception as e:
            # Handle failure
            agent.tasks_failed += 1
            agent.current_task_id = None
            session.commit()
            
            logger.error(f"Agent task execution failed: {e}")
            raise AgentFactoryError(f"Task execution failed: {e}")
        finally:
            self.close_db_session(session)

    # ==========================================================================
    # Swarm Management
    # ==========================================================================

    def create_swarm_configuration(self, config_data: Dict[str, Any]) -> SwarmConfiguration:
        """
        Create a new swarm configuration.
        
        Args:
            config_data: Swarm configuration dictionary
            
        Returns:
            Created SwarmConfiguration instance
            
        Raises:
            SwarmCreationError: If creation fails
        """
        session = self.get_db_session()
        
        try:
            # Validate configuration
            errors = self.catalog.validate_swarm_config(config_data)
            if errors:
                raise SwarmCreationError(f"Configuration validation failed: {'; '.join(errors)}")
            
            # Create configuration
            config = SwarmConfiguration(
                name=config_data["name"],
                display_name=config_data["display_name"],
                description=config_data["description"],
                category=config_data["category"],
                use_case=config_data.get("use_case", "general"),
                complexity_level=config_data.get("complexity_level", "medium"),
                agent_blueprints=config_data["agent_blueprints"],
                min_agents=config_data.get("min_agents", 2),
                max_agents=config_data.get("max_agents", 10),
                workflow_steps=config_data.get("workflow_steps", []),
                communication_pattern=config_data.get("communication_pattern", "broadcast"),
                orchestration_model=config_data.get("orchestration_model"),
                decision_strategy=config_data.get("decision_strategy", "consensus"),
                estimated_duration_minutes=config_data.get("estimated_duration_minutes", 30),
                estimated_cost=config_data.get("estimated_cost", 1.0),
                version=config_data.get("version", "1.0.0"),
                author=config_data.get("author", "Agent Factory"),
                tags=config_data.get("tags", [])
            )
            
            session.add(config)
            session.commit()
            session.refresh(config)
            
            logger.info(f"Created swarm configuration: {config.name}")
            return config
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error creating swarm config: {e}")
            raise SwarmCreationError(f"Failed to create swarm config: {e}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating swarm config: {e}")
            raise SwarmCreationError(f"Swarm config creation failed: {e}")
        finally:
            self.close_db_session(session)

    async def create_swarm(self, 
                          config_name: str,
                          instance_name: Optional[str] = None,
                          input_data: Optional[Dict[str, Any]] = None,
                          agent_overrides: Optional[Dict[str, Any]] = None) -> SwarmInstance:
        """
        Create a new swarm instance from a configuration.
        
        Args:
            config_name: Name of the swarm configuration
            instance_name: Custom name for the instance
            input_data: Initial input data
            agent_overrides: Agent-specific overrides
            
        Returns:
            Created SwarmInstance
            
        Raises:
            SwarmCreationError: If swarm creation fails
            ResourceLimitError: If resource limits exceeded
        """
        # Check resource limits
        if len(self.active_swarms) >= self.max_concurrent_swarms:
            raise ResourceLimitError(f"Maximum concurrent swarms ({self.max_concurrent_swarms}) exceeded")
        
        session = self.get_db_session()
        
        try:
            # Get configuration
            config = session.query(SwarmConfiguration).filter_by(name=config_name).first()
            if not config:
                # Try to get from catalog
                catalog_config = self.catalog.get_swarm_config(config_name)
                if catalog_config:
                    config = self.create_swarm_configuration(catalog_config)
                else:
                    raise SwarmCreationError(f"Swarm configuration not found: {config_name}")
            
            # Generate instance ID and name
            instance_id = f"swarm_{uuid.uuid4().hex[:8]}"
            if not instance_name:
                instance_name = f"{config.display_name} #{len(self.active_swarms) + 1}"
            
            # Create swarm instance
            swarm = SwarmInstance(
                instance_id=instance_id,
                name=instance_name,
                configuration_id=config.id,
                status=SwarmStatus.INITIALIZING,
                input_data=input_data or {},
                started_at=datetime.utcnow()
            )
            
            session.add(swarm)
            session.commit()
            session.refresh(swarm)
            
            # Create required agents
            agents_created = []
            for agent_req in config.agent_blueprints:
                if agent_req.get("required", True):
                    try:
                        # Apply overrides
                        agent_config_overrides = {}
                        if agent_overrides and agent_req["name"] in agent_overrides:
                            agent_config_overrides = agent_overrides[agent_req["name"]]
                        
                        agent = await self.create_agent(
                            blueprint_name=agent_req["name"],
                            instance_name=f"{instance_name} - {agent_req['role']}",
                            config_overrides=agent_config_overrides,
                            context={"swarm_id": instance_id, "role": agent_req["role"]}
                        )
                        
                        # Create membership
                        membership = SwarmMembership(
                            swarm_id=swarm.id,
                            agent_id=agent.id,
                            role=agent_req["role"],
                            priority=agent_req.get("priority", 1)
                        )
                        session.add(membership)
                        agents_created.append(agent)
                        
                    except Exception as e:
                        logger.error(f"Failed to create agent for swarm: {e}")
                        # Cleanup created agents
                        for created_agent in agents_created:
                            await self.stop_agent(created_agent.instance_id)
                        session.delete(swarm)
                        session.commit()
                        raise SwarmCreationError(f"Failed to create swarm agents: {e}")
            
            session.commit()
            
            # Update swarm status
            swarm.status = SwarmStatus.ACTIVE
            session.commit()
            
            # Add to active swarms
            self.active_swarms[instance_id] = swarm
            self.performance_metrics["total_swarms_created"] += 1
            
            # Update config usage
            config.usage_count += 1
            session.commit()
            
            logger.info(f"Created swarm instance: {instance_id} with {len(agents_created)} agents")
            
            # Record usage
            await self._record_usage("create_swarm", "swarm", instance_id, {
                "config": config_name,
                "agents": len(agents_created)
            })
            
            return swarm
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error creating swarm: {e}")
            raise SwarmCreationError(f"Failed to create swarm: {e}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating swarm: {e}")
            raise SwarmCreationError(f"Swarm creation failed: {e}")
        finally:
            self.close_db_session(session)

    def get_swarm(self, swarm_id: str) -> Optional[SwarmInstance]:
        """
        Get swarm instance by ID.
        
        Args:
            swarm_id: Swarm instance ID
            
        Returns:
            SwarmInstance or None if not found
        """
        # Check active swarms first
        if swarm_id in self.active_swarms:
            return self.active_swarms[swarm_id]
        
        # Query database
        session = self.get_db_session()
        try:
            return session.query(SwarmInstance).filter_by(instance_id=swarm_id).first()
        finally:
            self.close_db_session(session)

    def list_swarms(self, 
                   status: Optional[SwarmStatus] = None,
                   config_name: Optional[str] = None,
                   active_only: bool = False) -> List[SwarmInstance]:
        """
        List swarm instances with optional filtering.
        
        Args:
            status: Filter by status
            config_name: Filter by configuration name
            active_only: Only return currently active swarms
            
        Returns:
            List of SwarmInstance objects
        """
        if active_only:
            swarms = list(self.active_swarms.values())
            if status:
                swarms = [s for s in swarms if s.status == status]
            return swarms
        
        session = self.get_db_session()
        
        try:
            query = session.query(SwarmInstance)
            
            if status:
                query = query.filter_by(status=status)
            
            if config_name:
                config = session.query(SwarmConfiguration).filter_by(name=config_name).first()
                if config:
                    query = query.filter_by(configuration_id=config.id)
                else:
                    return []
            
            return query.order_by(desc(SwarmInstance.created_at)).all()
        finally:
            self.close_db_session(session)

    async def execute_swarm_task(self, 
                               swarm_id: str,
                               task: str,
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task with a swarm.
        
        Args:
            swarm_id: Swarm instance ID
            task: Task description
            context: Additional context
            
        Returns:
            Task execution result
            
        Raises:
            SwarmCreationError: If execution fails
        """
        swarm = self.get_swarm(swarm_id)
        if not swarm or swarm.status != SwarmStatus.ACTIVE:
            raise SwarmCreationError(f"Swarm not available: {swarm_id}")
        
        session = self.get_db_session()
        start_time = datetime.utcnow()
        
        try:
            # Get swarm members
            memberships = session.query(SwarmMembership).filter_by(
                swarm_id=swarm.id, is_active=True
            ).order_by(SwarmMembership.priority).all()
            
            if not memberships:
                raise SwarmCreationError("No active agents in swarm")
            
            # Update swarm state
            swarm.current_task = task
            swarm.last_activity = datetime.utcnow()
            session.commit()
            
            # Get orchestrator agent
            orchestrator = None
            for membership in memberships:
                if membership.role in ["orchestrator", "coordinator"]:
                    orchestrator = membership.agent
                    break
            
            if orchestrator:
                # Use orchestrator to manage workflow
                orchestrator_context = {
                    "swarm_id": swarm_id,
                    "task": task,
                    "members": [
                        {
                            "agent_id": m.agent.instance_id,
                            "role": m.role,
                            "capabilities": session.query(AgentBlueprint).filter_by(
                                id=m.agent.blueprint_id
                            ).first().capabilities
                        } for m in memberships
                    ]
                }
                
                result = await self.execute_agent_task(
                    orchestrator.instance_id,
                    f"Coordinate this swarm task: {task}",
                    orchestrator_context
                )
                
            else:
                # Simple parallel execution
                tasks = []
                for membership in memberships:
                    agent_context = {
                        "swarm_id": swarm_id,
                        "role": membership.role,
                        "task": task
                    }
                    
                    tasks.append(self.execute_agent_task(
                        membership.agent.instance_id,
                        task,
                        agent_context
                    ))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Combine results
                combined_result = {
                    "swarm_id": swarm_id,
                    "task": task,
                    "results": []
                }
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        combined_result["results"].append({
                            "agent_id": memberships[i].agent.instance_id,
                            "role": memberships[i].role,
                            "error": str(result)
                        })
                    else:
                        combined_result["results"].append({
                            "agent_id": memberships[i].agent.instance_id,
                            "role": memberships[i].role,
                            "result": result
                        })
                
                result = {"result": combined_result}
            
            # Update swarm metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            swarm.tasks_completed += 1
            swarm.execution_time_seconds += int(execution_time)
            swarm.current_task = None
            swarm.last_activity = datetime.utcnow()
            session.commit()
            
            # Record usage
            await self._record_usage("execute_swarm_task", "swarm", swarm_id, {
                "task_length": len(task),
                "execution_time_ms": execution_time * 1000,
                "agents_involved": len(memberships)
            })
            
            return result
            
        except Exception as e:
            swarm.current_task = None
            session.commit()
            logger.error(f"Swarm task execution failed: {e}")
            raise SwarmCreationError(f"Swarm task execution failed: {e}")
        finally:
            self.close_db_session(session)

    async def stop_swarm(self, swarm_id: str) -> bool:
        """
        Stop an active swarm and its agents.
        
        Args:
            swarm_id: Swarm instance ID
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_db_session()
        
        try:
            swarm = self.get_swarm(swarm_id)
            if not swarm:
                logger.warning(f"Swarm not found: {swarm_id}")
                return False
            
            # Stop all agents in swarm
            memberships = session.query(SwarmMembership).filter_by(
                swarm_id=swarm.id, is_active=True
            ).all()
            
            for membership in memberships:
                await self.stop_agent(membership.agent.instance_id)
                membership.is_active = False
                membership.left_at = datetime.utcnow()
            
            # Update swarm status
            swarm.status = SwarmStatus.STOPPED
            swarm.completed_at = datetime.utcnow()
            session.commit()
            
            # Remove from active swarms
            if swarm_id in self.active_swarms:
                del self.active_swarms[swarm_id]
            
            logger.info(f"Stopped swarm: {swarm_id}")
            
            # Record usage
            await self._record_usage("stop_swarm", "swarm", swarm_id)
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error stopping swarm {swarm_id}: {e}")
            return False
        finally:
            self.close_db_session(session)

    # ==========================================================================
    # Performance and Analytics
    # ==========================================================================

    def get_agent_metrics(self, agent_id: str, 
                         days: int = 7) -> Dict[str, Any]:
        """
        Get performance metrics for an agent.
        
        Args:
            agent_id: Agent instance ID
            days: Number of days to include in metrics
            
        Returns:
            Dictionary of metrics
        """
        session = self.get_db_session()
        
        try:
            agent = self.get_agent(agent_id)
            if not agent:
                return {}
            
            # Get recent metrics
            since_date = datetime.utcnow() - timedelta(days=days)
            metrics = session.query(AgentMetrics).filter(
                AgentMetrics.agent_id == agent.id,
                AgentMetrics.recorded_at >= since_date
            ).all()
            
            # Calculate aggregated metrics
            total_requests = sum(m.requests_handled for m in metrics) or agent.tasks_completed
            total_failures = sum(m.requests_failed for m in metrics) or agent.tasks_failed
            avg_response_time = (
                sum(m.avg_response_time_ms for m in metrics) / len(metrics)
                if metrics else agent.avg_response_time_ms
            )
            
            return {
                "agent_id": agent_id,
                "status": agent.status.value,
                "performance": {
                    "total_requests": total_requests,
                    "total_failures": total_failures,
                    "success_rate": agent.success_rate,
                    "avg_response_time_ms": avg_response_time,
                    "total_tokens_used": agent.total_tokens_used,
                    "total_cost": agent.total_cost
                },
                "resources": {
                    "cpu_usage_percent": agent.cpu_usage_percent,
                    "memory_usage_mb": agent.memory_usage_mb
                },
                "recent_metrics": [
                    {
                        "period": f"{m.period_start} - {m.period_end}",
                        "requests": m.requests_handled,
                        "failures": m.requests_failed,
                        "avg_response_ms": m.avg_response_time_ms,
                        "quality_score": m.quality_score
                    } for m in metrics
                ]
            }
            
        finally:
            self.close_db_session(session)

    def get_swarm_metrics(self, swarm_id: str,
                         days: int = 7) -> Dict[str, Any]:
        """
        Get performance metrics for a swarm.
        
        Args:
            swarm_id: Swarm instance ID
            days: Number of days to include in metrics
            
        Returns:
            Dictionary of metrics
        """
        session = self.get_db_session()
        
        try:
            swarm = self.get_swarm(swarm_id)
            if not swarm:
                return {}
            
            # Get recent metrics
            since_date = datetime.utcnow() - timedelta(days=days)
            metrics = session.query(SwarmMetrics).filter(
                SwarmMetrics.swarm_id == swarm.id,
                SwarmMetrics.recorded_at >= since_date
            ).all()
            
            # Get member metrics
            memberships = session.query(SwarmMembership).filter_by(swarm_id=swarm.id).all()
            member_metrics = []
            for membership in memberships:
                agent_metrics = self.get_agent_metrics(membership.agent.instance_id, days)
                if agent_metrics:
                    agent_metrics["role"] = membership.role
                    member_metrics.append(agent_metrics)
            
            return {
                "swarm_id": swarm_id,
                "status": swarm.status.value,
                "performance": {
                    "tasks_completed": swarm.tasks_completed,
                    "total_tokens_used": swarm.total_tokens_used,
                    "total_cost": swarm.total_cost,
                    "execution_time_seconds": swarm.execution_time_seconds
                },
                "composition": {
                    "total_agents": swarm.agent_count,
                    "active_agents": swarm.active_agents
                },
                "members": member_metrics,
                "recent_metrics": [
                    {
                        "period": f"{m.period_start} - {m.period_end}",
                        "tasks": m.tasks_completed,
                        "failures": m.tasks_failed,
                        "avg_execution_time": m.avg_execution_time_seconds,
                        "quality_score": m.output_quality_score
                    } for m in metrics
                ]
            }
            
        finally:
            self.close_db_session(session)

    def get_factory_metrics(self) -> Dict[str, Any]:
        """
        Get overall factory performance metrics.
        
        Returns:
            Dictionary of factory metrics
        """
        session = self.get_db_session()
        
        try:
            # Query database statistics
            total_blueprints = session.query(AgentBlueprint).count()
            total_configs = session.query(SwarmConfiguration).count()
            total_agents_ever = session.query(AgentInstance).count()
            total_swarms_ever = session.query(SwarmInstance).count()
            
            active_agents = len(self.active_agents)
            active_swarms = len(self.active_swarms)
            
            # Calculate aggregate costs and tokens
            total_cost = session.query(func.sum(AgentInstance.total_cost)).scalar() or 0.0
            total_tokens = session.query(func.sum(AgentInstance.total_tokens_used)).scalar() or 0
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "catalog": {
                    "total_blueprints": total_blueprints,
                    "total_swarm_configs": total_configs
                },
                "instances": {
                    "active_agents": active_agents,
                    "active_swarms": active_swarms,
                    "total_agents_created": total_agents_ever,
                    "total_swarms_created": total_swarms_ever
                },
                "performance": {
                    "total_tasks_completed": self.performance_metrics["total_tasks_completed"],
                    "total_cost": total_cost,
                    "total_tokens_used": total_tokens,
                    "avg_response_time_ms": self.performance_metrics["avg_response_time_ms"]
                },
                "capacity": {
                    "max_concurrent_agents": self.max_concurrent_agents,
                    "max_concurrent_swarms": self.max_concurrent_swarms,
                    "agent_utilization": active_agents / self.max_concurrent_agents,
                    "swarm_utilization": active_swarms / self.max_concurrent_swarms
                }
            }
            
        finally:
            self.close_db_session(session)

    # ==========================================================================
    # Utility Methods
    # ==========================================================================

    async def _record_usage(self, 
                           operation_type: str,
                           resource_type: str,
                           resource_id: str,
                           parameters: Optional[Dict[str, Any]] = None) -> None:
        """Record factory usage for analytics and billing"""
        session = self.get_db_session()
        
        try:
            usage = FactoryUsage(
                operation_type=operation_type,
                resource_type=resource_type,
                resource_id=resource_id,
                parameters=parameters or {},
                completed_at=datetime.utcnow()
            )
            
            session.add(usage)
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to record usage: {e}")
        finally:
            self.close_db_session(session)

    async def cleanup_inactive_resources(self, max_age_hours: int = 24) -> Dict[str, int]:
        """
        Clean up inactive agents and swarms.
        
        Args:
            max_age_hours: Maximum age for inactive resources
            
        Returns:
            Dictionary with cleanup counts
        """
        session = self.get_db_session()
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        try:
            # Find inactive agents
            inactive_agents = session.query(AgentInstance).filter(
                AgentInstance.status == AgentStatus.INACTIVE,
                AgentInstance.last_active < cutoff_time
            ).all()
            
            # Find stopped swarms
            stopped_swarms = session.query(SwarmInstance).filter(
                SwarmInstance.status == SwarmStatus.STOPPED,
                SwarmInstance.completed_at < cutoff_time
            ).all()
            
            agents_cleaned = 0
            swarms_cleaned = 0
            
            # Archive inactive agents
            for agent in inactive_agents:
                if agent.instance_id in self.active_agents:
                    del self.active_agents[agent.instance_id]
                agent.status = AgentStatus.MAINTENANCE
                agents_cleaned += 1
            
            # Archive stopped swarms
            for swarm in stopped_swarms:
                if swarm.instance_id in self.active_swarms:
                    del self.active_swarms[swarm.instance_id]
                swarms_cleaned += 1
            
            session.commit()
            
            logger.info(f"Cleaned up {agents_cleaned} agents and {swarms_cleaned} swarms")
            
            return {
                "agents_cleaned": agents_cleaned,
                "swarms_cleaned": swarms_cleaned
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error during cleanup: {e}")
            return {"agents_cleaned": 0, "swarms_cleaned": 0}
        finally:
            self.close_db_session(session)

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the factory and its components.
        
        Returns:
            Health check results
        """
        health = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "components": {},
            "issues": []
        }
        
        try:
            # Check database connectivity
            session = self.get_db_session()
            session.query(AgentBlueprint).count()
            health["components"]["database"] = {"status": "healthy"}
            self.close_db_session(session)
            
        except Exception as e:
            health["components"]["database"] = {"status": "unhealthy", "error": str(e)}
            health["issues"].append(f"Database connectivity issue: {e}")
            health["status"] = "degraded"
        
        # Check Portkey client
        if self.portkey_client:
            try:
                await self.portkey_client.get_available_models(max_cost=0.1)
                health["components"]["portkey"] = {"status": "healthy"}
            except Exception as e:
                health["components"]["portkey"] = {"status": "unhealthy", "error": str(e)}
                health["issues"].append(f"Portkey client issue: {e}")
                health["status"] = "degraded"
        else:
            health["components"]["portkey"] = {"status": "not_configured"}
        
        # Check resource utilization
        agent_utilization = len(self.active_agents) / self.max_concurrent_agents
        swarm_utilization = len(self.active_swarms) / self.max_concurrent_swarms
        
        if agent_utilization > 0.9:
            health["issues"].append("High agent utilization")
            health["status"] = "degraded"
        
        if swarm_utilization > 0.9:
            health["issues"].append("High swarm utilization")
            health["status"] = "degraded"
        
        health["components"]["resources"] = {
            "status": "healthy" if agent_utilization < 0.9 and swarm_utilization < 0.9 else "stressed",
            "agent_utilization": agent_utilization,
            "swarm_utilization": swarm_utilization
        }
        
        return health

    async def close(self):
        """Close the factory and cleanup resources"""
        logger.info("Shutting down Agent Factory")
        
        # Stop all active agents and swarms
        for agent_id in list(self.active_agents.keys()):
            await self.stop_agent(agent_id)
        
        for swarm_id in list(self.active_swarms.keys()):
            await self.stop_swarm(swarm_id)
        
        # Close database connections
        if hasattr(self, 'engine'):
            self.engine.dispose()
        
        logger.info("Agent Factory shutdown complete")


# Global factory instance
_agent_factory: Optional[AgentFactory] = None


async def get_factory(database_url: str = "sqlite:///agent_factory.db",
                     portkey_api_key: Optional[str] = None,
                     openrouter_api_key: Optional[str] = None) -> AgentFactory:
    """Get or create the global agent factory instance"""
    global _agent_factory
    if _agent_factory is None:
        _agent_factory = AgentFactory(
            database_url=database_url,
            portkey_api_key=portkey_api_key,
            openrouter_api_key=openrouter_api_key
        )
    return _agent_factory


# Convenience functions for quick operations
async def create_quick_agent(blueprint_name: str, **kwargs) -> AgentInstance:
    """Quick agent creation"""
    factory = await get_factory()
    return await factory.create_agent(blueprint_name, **kwargs)


async def create_quick_swarm(config_name: str, **kwargs) -> SwarmInstance:
    """Quick swarm creation"""
    factory = await get_factory()
    return await factory.create_swarm(config_name, **kwargs)


async def execute_quick_task(agent_id: str, task: str, **kwargs) -> Dict[str, Any]:
    """Quick task execution"""
    factory = await get_factory()
    return await factory.execute_agent_task(agent_id, task, **kwargs)