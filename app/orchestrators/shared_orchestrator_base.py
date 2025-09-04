"""
Shared Base Orchestrator Infrastructure
Eliminates code duplication between Sophia and Artemis orchestrators
while maintaining clear ecosystem separation
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from app.orchestrators.enhanced_orchestrator_mixin import EnhancedOrchestratorMixin
from app.swarms.shared_resources import PersonalityType

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationConfig:
    """Shared configuration for orchestrators"""
    project_path: str = None
    enable_memory: bool = True
    enable_api_integrations: bool = True
    parallel_initialization: bool = True
    memory_session_prefix: str = "agno"
    
    def __post_init__(self):
        if self.project_path is None:
            self.project_path = os.getenv('PROJECT_PATH', str(Path.cwd()))


class BaseAGNOOrchestrator(EnhancedOrchestratorMixin, ABC):
    """
    Abstract base class for AGNO orchestrators
    Provides shared functionality while maintaining ecosystem separation
    """
    
    def __init__(self, config: Optional[OrchestrationConfig] = None):
        super().__init__()
        self.config = config or OrchestrationConfig()
        self.teams: Dict[str, Any] = {}
        self.initialization_start_time: Optional[datetime] = None
        self.initialization_complete: bool = False
        
    @property
    @abstractmethod
    def orchestrator_name(self) -> str:
        """Name of the orchestrator (sophia/artemis)"""
        pass
    
    @property
    @abstractmethod
    def personality_type(self) -> PersonalityType:
        """Personality type for this orchestrator"""
        pass
    
    @abstractmethod
    async def _initialize_domain_teams(self) -> Dict[str, Any]:
        """Initialize domain-specific teams - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def _get_team_initialization_tasks(self) -> List[Callable]:
        """Get list of team initialization tasks"""
        pass
    
    async def initialize(self) -> bool:
        """Shared initialization logic with personality-specific team setup"""
        try:
            self.initialization_start_time = datetime.now()
            logger.info(f"🚀 Initializing {self.orchestrator_name.title()} AGNO Teams...")
            
            # Initialize domain-specific teams concurrently
            if self.config.parallel_initialization:
                team_tasks = self._get_team_initialization_tasks()
                await asyncio.gather(*team_tasks, return_exceptions=True)
            else:
                self.teams = await self._initialize_domain_teams()
            
            # Initialize shared memory system
            if self.config.enable_memory:
                await self._initialize_shared_memory()
            
            # Initialize API integrations if enabled
            if self.config.enable_api_integrations:
                await self._initialize_api_integrations()
            
            self.initialization_complete = True
            duration = (datetime.now() - self.initialization_start_time).total_seconds()
            
            logger.info(f"✅ {self.orchestrator_name.title()} AGNO Orchestrator fully operational "
                       f"with {len(self.teams)} specialized teams (initialized in {duration:.2f}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ {self.orchestrator_name.title()} orchestrator initialization failed: {e}")
            return False
    
    async def _initialize_shared_memory(self):
        """Shared memory system initialization"""
        try:
            memory_session = f"{self.orchestrator_name}-global"
            await self.initialize_memory(memory_session, self.config.project_path)
            logger.info(f"🧠 Memory system initialized for session {memory_session}")
        except Exception as e:
            logger.error(f"❌ Memory system initialization failed: {e}")
            raise
    
    async def _initialize_api_integrations(self):
        """Shared API integration initialization"""
        try:
            # This method can be overridden by subclasses for specific integrations
            logger.info(f"🎆 Initializing API integrations for {self.orchestrator_name}...")
            # Base implementation - subclasses can extend
        except Exception as e:
            logger.warning(f"⚠️ API integration initialization had issues: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Shared health check functionality"""
        health_status = {
            "orchestrator": self.orchestrator_name,
            "personality": self.personality_type.value,
            "initialized": self.initialization_complete,
            "teams_count": len(self.teams),
            "teams_status": {},
            "memory_system": hasattr(self, 'memory') and self.memory is not None,
            "uptime_seconds": None
        }
        
        if self.initialization_start_time:
            health_status["uptime_seconds"] = (datetime.now() - self.initialization_start_time).total_seconds()
        
        # Check team health
        for team_name, team in self.teams.items():
            health_status["teams_status"][team_name] = {
                "initialized": hasattr(team, 'team') and team.team is not None,
                "agents_count": len(getattr(team, 'agents', []))
            }
        
        return health_status
    
    def get_orchestration_stats(self) -> Dict[str, Any]:
        """Get orchestration statistics"""
        return {
            "orchestrator_type": self.orchestrator_name,
            "personality_type": self.personality_type.value,
            "total_teams": len(self.teams),
            "team_names": list(self.teams.keys()),
            "initialization_time": self.initialization_start_time.isoformat() if self.initialization_start_time else None,
            "is_operational": self.initialization_complete
        }


class SharedOrchestrationUtils:
    """Utility functions shared between orchestrators"""
    
    @staticmethod
    async def safe_team_initialization(team_factory_func: Callable, team_name: str, 
                                     custom_config: Optional[Any] = None) -> tuple[str, Any]:
        """Safely initialize a team with error handling"""
        try:
            team = await team_factory_func(custom_config) if custom_config else await team_factory_func()
            logger.info(f"✅ {team_name} ready")
            return team_name, team
        except Exception as e:
            logger.error(f"❌ {team_name} initialization failed: {e}")
            return team_name, None
    
    @staticmethod
    def enhance_response_with_personality(result: Dict[str, Any], 
                                        personality_type: PersonalityType,
                                        analysis_type: str,
                                        custom_insights: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """Generic personality enhancement for responses"""
        
        personality_config = {
            PersonalityType.SOPHIA_STRATEGIC: {
                "style": "strategic_professional",
                "focus": "business_outcomes",
                "tone": "confident_insightful"
            },
            PersonalityType.ARTEMIS_TACTICAL: {
                "style": "tactical_direct", 
                "focus": "technical_excellence",
                "tone": "confident_passionate_with_edge"
            }
        }
        
        config = personality_config.get(personality_type, personality_config[PersonalityType.SOPHIA_STRATEGIC])
        
        # Add personality context
        result[f"{personality_type.value.split('_')[0].lower()}_personality"] = {
            "communication_style": config["style"],
            "focus_area": config["focus"], 
            "response_tone": config["tone"],
            "analysis_summary": f"{personality_type.value.split('_')[0].title()} analysis complete with {config['focus'].replace('_', ' ')} insights"
        }
        
        # Add custom insights if provided
        if custom_insights and analysis_type in custom_insights:
            result[f"{personality_type.value.split('_')[0].lower()}_insights"] = custom_insights[analysis_type]
        
        return result
    
    @staticmethod
    def validate_orchestrator_config(config: OrchestrationConfig) -> List[str]:
        """Validate orchestrator configuration"""
        issues = []
        
        if not os.path.exists(config.project_path):
            issues.append(f"Project path does not exist: {config.project_path}")
        
        if config.enable_memory and not config.memory_session_prefix:
            issues.append("Memory session prefix is required when memory is enabled")
        
        return issues