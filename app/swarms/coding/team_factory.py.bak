"""
Team Factory for constructing Coding Swarm teams.

This module handles the creation and configuration of coding teams with
various agent compositions based on requirements and resource pools.
"""

import logging
from typing import List
from agno.team import Team
from agno.agent import Agent

from app.swarms.coding.agents import (
    make_lead,
    make_generator,
    make_critic,
    make_judge,
    make_runner
)
from app.swarms.coding.models import SwarmConfiguration, PoolType
from app.swarms.coding.pools import POOLS
from app.tools.basic_tools import (
    CodeSearch, ReadFile, WriteFile, GitStatus, GitDiff, RunTests
)
from app.tools.list_directory import ListDirectory
from app.models.simple_router import agno_chat_model

logger = logging.getLogger(__name__)


class TeamFactory:
    """
    Factory for creating and configuring coding swarm teams.
    
    This class encapsulates the logic for building teams with different
    compositions, tool sets, and execution modes based on configuration.
    """
    
    @staticmethod
    def create_team(config: SwarmConfiguration) -> Team:
        """
        Create a coding team based on the provided configuration.
        
        Args:
            config: SwarmConfiguration specifying team composition and settings
            
        Returns:
            Configured Team instance ready for execution
            
        Raises:
            ValueError: If configuration is invalid
        """
        logger.info(f"Creating coding team with pool: {config.pool}, "
                   f"max_generators: {config.max_generators}")
        
        # Create core agents
        lead = TeamFactory._create_lead_agent(config)
        critic = make_critic()
        judge = make_judge()
        
        # Build team members list
        members = [lead]
        
        # Add generators based on configuration
        generators = TeamFactory._build_generators(config)
        if len(generators) > config.max_generators:
            logger.warning(f"Limiting generators from {len(generators)} to {config.max_generators}")
            generators = generators[:config.max_generators]
        members.extend(generators)
        
        # Add critic and judge
        members.extend([critic, judge])
        
        # Optionally add runner
        if config.include_runner:
            runner = TeamFactory._create_runner_agent(config)
            members.append(runner)
            logger.info("Runner agent included in team")
        
        # Create the team
        team = Team(
            name=f"Coding Swarm ({config.pool.value})",
            mode="coordinate",
            members=members,
            markdown=True,
            show_members_responses=config.stream_responses,
            instructions=TeamFactory._get_team_instructions(config)
        )
        
        # Set the lead as manager for coordination
        team.set_manager(lead)
        
        logger.info(f"Team created with {len(members)} members")
        return team
    
    @staticmethod
    def _create_lead_agent(config: SwarmConfiguration) -> Agent:
        """
        Create a lead agent with appropriate tools based on configuration.
        
        Args:
            config: SwarmConfiguration for tool access settings
            
        Returns:
            Configured lead Agent
        """
        tools = [
            CodeSearch(),
            ListDirectory(),
            GitStatus()
        ]
        
        # Add additional tools based on configuration
        if config.enable_file_write:
            tools.extend([ReadFile(), WriteFile()])
            logger.info("Lead agent granted file write access")
        
        if config.enable_test_execution:
            tools.append(RunTests())
            logger.info("Lead agent granted test execution access")
        
        if config.enable_git_operations:
            tools.append(GitDiff())
            logger.info("Lead agent granted git operations access")
        
        # Create lead with enhanced tools
        lead = make_lead()
        lead.tools = tools
        
        return lead
    
    @staticmethod
    def _build_generators(config: SwarmConfiguration) -> List[Agent]:
        """
        Build generator agents based on configuration.
        
        Args:
            config: SwarmConfiguration specifying generator settings
            
        Returns:
            List of configured generator Agents
        """
        generators = []
        
        # Add default pair if requested
        if config.include_default_pair:
            generators.extend(TeamFactory._build_default_generators())
        
        # Add pool-based generators
        if config.pool in POOLS:
            pool_models = POOLS[config.pool]
            generators.extend(TeamFactory._build_pool_generators(pool_models))
        
        # Add custom concurrent models
        if config.concurrent_models:
            generators.extend(
                TeamFactory._build_custom_generators(config.concurrent_models)
            )
        
        return generators
    
    @staticmethod
    def _build_default_generators() -> List[Agent]:
        """Build the default Coder-A and Coder-B pair."""
        return [
            make_generator(
                name="Coder-A",
                model_name="coderA",
                tools=[CodeSearch()],
                role_note="Implement approach A with comprehensive tests"
            ),
            make_generator(
                name="Coder-B",
                model_name="coderB",
                tools=[CodeSearch()],
                role_note="Implement approach B with minimal changes"
            )
        ]
    
    @staticmethod
    def _build_pool_generators(model_ids: List[str]) -> List[Agent]:
        """
        Build generators from a pool of model IDs.
        
        Args:
            model_ids: List of OpenRouter model IDs
            
        Returns:
            List of generator Agents
        """
        generators = []
        for i, model_id in enumerate(model_ids, start=1):
            agent = Agent(
                name=f"Generator-{i}",
                role=f"Implement solution {i} with tests and documentation",
                model=agno_chat_model(model_id),
                tools=[CodeSearch()],
                markdown=True,
                show_tool_calls=True
            )
            generators.append(agent)
        
        return generators
    
    @staticmethod
    def _build_custom_generators(model_names: List[str]) -> List[Agent]:
        """
        Build generators from custom model names.
        
        Args:
            model_names: List of model names or IDs
            
        Returns:
            List of generator Agents
        """
        generators = []
        for i, model_name in enumerate(model_names, start=1):
            generators.append(
                make_generator(
                    name=f"Custom-{i}",
                    model_name=model_name,
                    tools=[CodeSearch()],
                    role_note=f"Implement custom approach {i}"
                )
            )
        
        return generators
    
    @staticmethod
    def _create_runner_agent(config: SwarmConfiguration) -> Agent:
        """
        Create a runner agent with appropriate permissions.
        
        Args:
            config: SwarmConfiguration for runner settings
            
        Returns:
            Configured runner Agent
        """
        runner = make_runner()
        
        # Restrict tools based on configuration
        if not config.enable_file_write:
            # Remove write tools from runner if disabled
            runner.tools = [t for t in runner.tools 
                          if not isinstance(t, WriteFile)]
        
        return runner
    
    @staticmethod
    def _get_team_instructions(config: SwarmConfiguration) -> str:
        """
        Generate team instructions based on configuration.
        
        Args:
            config: SwarmConfiguration for team settings
            
        Returns:
            Formatted instruction string
        """
        instructions = f"""
        Advanced Coding Swarm Configuration:
        - Pool: {config.pool.value}
        - Max Generators: {config.max_generators}
        - Max Rounds: {config.max_rounds}
        - Accuracy Threshold: {config.accuracy_threshold}
        - Auto-approve Low Risk: {config.auto_approve_low_risk}
        
        Workflow:
        1. Lead analyzes task and coordinates generators
        2. Generators propose competing implementations
        3. Critic reviews with structured JSON output
        4. Judge makes final decision with runner instructions
        """
        
        if config.include_runner:
            instructions += "\n5. Runner executes approved changes"
        
        instructions += """
        
        Quality Standards:
        - Comprehensive testing required
        - Minimal code changes preferred
        - Security-first approach
        - Clear documentation mandatory
        - Follow project conventions
        """
        
        return instructions
    
    @staticmethod
    def validate_configuration(config: SwarmConfiguration) -> None:
        """
        Validate a swarm configuration for consistency.
        
        Args:
            config: SwarmConfiguration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        if config.max_generators < 1:
            raise ValueError("max_generators must be at least 1")
        
        if config.pool not in PoolType:
            raise ValueError(f"Invalid pool type: {config.pool}")
        
        if config.accuracy_threshold < 0 or config.accuracy_threshold > 10:
            raise ValueError("accuracy_threshold must be between 0 and 10")
        
        if config.include_runner and not config.enable_file_write:
            logger.warning("Runner included but file write disabled - runner will be limited")
        
        if config.timeout_seconds < 30:
            raise ValueError("timeout_seconds must be at least 30")