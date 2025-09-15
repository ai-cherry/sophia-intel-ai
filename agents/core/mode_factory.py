#!/usr/bin/env python3
"""
Mode Factory - Generates and configures custom Roo modes
Handles mode creation, configuration generation, and validation
"""

import json
import os
from typing import Dict, Any, List, Optional

from agents.core.mode_framework import ModeConfig, ModeFramework
from agents.core.evolutionary_components import OptimizationTarget
from agents.specialized.genetic_algorithm_agent import GeneticAlgorithmMode
from agents.specialized.prophecy_agent import ProphecyMode  # Will be created next
from agents.specialized.socratic_agent import SocraticMode  # Will be created next
from agents.specialized.cascade_agent import CascadeMode  # Will be created next

class ModeFactory:
    """
    Factory for creating, configuring, and managing custom modes
    Provides methods for generating configs, creating agents, and mode orchestration
    """
    
    # Default model recommendations by phase
    PHASE_MODEL_RECOMMENDATIONS = {
        "initialization": ["claude-opus-4.1", "chatgpt-5"],
        "analysis": ["llama-scout-4", "deepseek-v3"],
        "generation": ["grok-5", "grok-code-fast-1"],
        "evaluation": ["deepseek-v3", "google-flash-2.5"],
        "optimization": ["google-flash-2.5", "grok-5"],
        "synthesis": ["claude-opus-4.1", "chatgpt-5"],
        "validation": ["deepseek-v3"],
        "documentation": ["claude-opus-4.1"]
    }
    
    # Mode templates
    MODE_TEMPLATES = {
        "genetic-algorithm": {
            "mode_id": "genetic-algorithm",
            "mode_name": "Genetic Algorithm Mode",
            "category": "optimization",
            "workflow_steps": [
                "initialization",
                "evaluation",
                "evolution",
                "optimization",
                "synthesis"
            ],
            "default_parameters": {
                "default_population_size": 50,
                "default_generations": 100,
                "mutation_rate": 0.1,
                "crossover_rate": 0.7
            },
            "mcp_hooks": [
                "store_evolution_history",
                "retrieve_populations",
                "read_code",
                "write_optimized_code"
            ]
        },
        "prophecy": {
            "mode_id": "prophecy",
            "mode_name": "Prophecy Mode",
            "category": "prediction",
            "workflow_steps": [
                "trend_analysis",
                "pattern_recognition",
                "prediction_generation",
                "scenario_simulation",
                "recommendation_synthesis"
            ],
            "default_parameters": {
                "prediction_horizon": 30,
                "scenario_count": 5,
                "confidence_threshold": 0.7
            },
            "mcp_hooks": [
                "retrieve_historical_data",
                "store_predictions",
                "search_patterns"
            ]
        },
        "socratic": {
            "mode_id": "socratic",
            "mode_name": "Socratic Mode",
            "category": "refinement",
            "workflow_steps": [
                "question_generation",
                "dialogue_simulation",
                "response_analysis",
                "refinement_iteration",
                "validation_synthesis"
            ],
            "default_parameters": {
                "max_iterations": 5,
                "question_depth": 3,
                "response_complexity": "medium"
            },
            "mcp_hooks": [
                "store_dialogue_history",
                "retrieve_context",
                "search_knowledge_base"
            ]
        },
        "cascade": {
            "mode_id": "cascade",
            "mode_name": "Cascade Mode",
            "category": "refinement",
            "workflow_steps": [
                "coarse_analysis",
                "fine_grained_refinement",
                "ultra_fine_tuning",
                "cross_layer_validation",
                "integrated_synthesis"
            ],
            "default_parameters": {
                "layers": 3,
                "refinement_depth": 4,
                "validation_threshold": 0.8
            },
            "mcp_hooks": [
                "store_layer_results",
                "retrieve_previous_layers",
                "validate_integrity"
            ]
        }
    }

    @staticmethod
    def generate_config(
        mode_id: str,
        mode_name: str,
        workflow_steps: Optional[List[str]] = None,
        model_phases: Optional[Dict[str, str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        mcp_hooks: Optional[List[str]] = None,
        category: str = "custom"
    ) -> ModeConfig:
        """
        Generate mode configuration from template or custom parameters
        """
        # Get template if available
        template = ModeFactory.MODE_TEMPLATES.get(mode_id)
        if template:
            config = ModeConfig(
                mode_id=template["mode_id"],
                mode_name=template["mode_name"],
                version="1.0.0",
                description=f"{mode_name} - {template.get('description', '')}",
                category=template.get("category", category),
                workflow_steps=workflow_steps or template["workflow_steps"],
                model_phases=model_phases or ModeFactory._generate_default_model_phases(
                    workflow_steps or template["workflow_steps"]
                ),
                mcp_hooks=mcp_hooks or template.get("mcp_hooks", []),
                parameters=parameters or template.get("default_parameters", {}),
                dependencies=[ "agents.core.mode_framework" ]
            )
        else:
            # Custom mode config
            config = ModeConfig(
                mode_id=mode_id,
                mode_name=mode_name,
                version="1.0.0",
                description="Custom mode generated by factory",
                category=category,
                workflow_steps=workflow_steps or ["analysis", "generation", "synthesis"],
                model_phases=model_phases or ModeFactory._generate_default_model_phases(
                    workflow_steps or ["analysis", "generation", "synthesis"]
                ),
                mcp_hooks=mcp_hooks or ["store_results", "retrieve_context"],
                parameters=parameters or {},
                dependencies=[ "agents.core.mode_framework" ]
            )
        
        return config

    @staticmethod
    def _generate_default_model_phases(workflow_steps: List[str]) -> Dict[str, str]:
        """
        Generate default model phases for workflow steps
        """
        phases = {}
        for step in workflow_steps:
            # Map step to recommended model
            if "init" in step or "analysis" in step:
                phases[step] = "claude-opus-4.1"
            elif "generate" in step or "evolution" in step:
                phases[step] = "grok-5"
            elif "evaluate" in step or "validate" in step:
                phases[step] = "deepseek-v3"
            elif "optimize" in step:
                phases[step] = "google-flash-2.5"
            else:
                phases[step] = "claude-opus-4.1"  # Default to Claude for synthesis
        
        return phases

    @staticmethod
    def create_mode_agent(mode_config: ModeConfig) -> ModeFramework:
        """
        Create mode agent instance from configuration
        """
        mode_id = mode_config.mode_id
        
        if mode_id == "genetic-algorithm":
            return GeneticAlgorithmMode()
        elif mode_id == "prophecy":
            return ProphecyMode()  # Will be implemented
        elif mode_id == "socratic":
            return SocraticMode()  # Will be implemented
        elif mode_id == "cascade":
            return CascadeMode()  # Will be implemented
        else:
            raise ValueError(f"Mode {mode_id} not implemented yet. Available modes: {list(ModeFactory.MODE_TEMPLATES.keys())}")

    @staticmethod
    def create_from_json(config_path: str) -> ModeFramework:
        """
        Create mode from JSON configuration file
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        mode_config = ModeConfig(**config_dict)
        return ModeFactory.create_mode_agent(mode_config)

    @staticmethod
    def generate_config_json(
        mode_id: str,
        output_path: str,
        workflow_steps: Optional[List[str]] = None,
        model_phases: Optional[Dict[str, str]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate and save mode configuration as JSON file
        """
        config = ModeFactory.generate_config(
            mode_id=mode_id,
            mode_name=f"{mode_id.replace('-', ' ').title()} Mode",
            workflow_steps=workflow_steps,
            model_phases=model_phases,
            parameters=parameters
        )
        
        config_json = json.dumps(config.__dict__, indent=2)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(config_json)
        
        return config_json

    @staticmethod
    def validate_config(mode_config: ModeConfig) -> Dict[str, Any]:
        """
        Validate mode configuration
        """
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check required fields
        required_fields = ["mode_id", "mode_name", "workflow_steps"]
        for field in required_fields:
            if not hasattr(mode_config, field) or not getattr(mode_config, field):
                validation_result["valid"] = False
                validation_result["issues"].append(f"Missing required field: {field}")
        
        # Validate workflow steps
        for step in mode_config.workflow_steps:
            if step not in mode_config.model_phases:
                validation_result["warnings"].append(f"No model specified for step '{step}'")
        
        # Validate parameters
        for param, value in mode_config.parameters.items():
            if isinstance(value, (int, float)) and value < 0:
                validation_result["warnings"].append(f"Parameter '{param}' has negative value: {value}")
        
        return validation_result

    @staticmethod
    def list_available_modes() -> List[str]:
        """List all available mode templates"""
        return list(ModeFactory.MODE_TEMPLATES.keys())

    @staticmethod
    def get_mode_template(mode_id: str) -> Dict[str, Any]:
        """Get mode template by ID"""
        return ModeFactory.MODE_TEMPLATES.get(mode_id, {})

    @staticmethod
    def orchestrate_modes(
        primary_mode_id: str,
        secondary_modes: List[str],
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Orchestrate multiple modes for complex workflows
        Example: Socratic → Prophecy → Genetic Algorithm
        """
        results = {}
        
        # Create primary mode
        primary_config = ModeFactory.generate_config(primary_mode_id, f"{primary_mode_id} Mode")
        primary_agent = ModeFactory.create_mode_agent(primary_config)
        
        # Execute primary mode
        primary_result = asyncio.run(primary_agent._process_task_impl("primary", task_data))
        results["primary"] = primary_result
        
        # Execute secondary modes
        for secondary_id in secondary_modes:
            secondary_config = ModeFactory.generate_config(secondary_id, f"{secondary_id} Mode")
            secondary_agent = ModeFactory.create_mode_agent(secondary_config)
            
            # Pass primary result as input
            secondary_input = {**task_data, **primary_result}
            secondary_result = asyncio.run(
                secondary_agent._process_task_impl(f"secondary_{secondary_id}", secondary_input)
            )
            results[secondary_id] = secondary_result
        
        return {
            "orchestration": {
                "primary_mode": primary_mode_id,
                "secondary_modes": secondary_modes,
                "overall_result": results
            }
        }

# Example usage
if __name__ == "__main__":
    # Generate config for new mode
    config_json = ModeFactory.generate_config_json(
        mode_id="prophecy",
        output_path="modes/prophecy_mode.json",
        workflow_steps=[
            "trend_analysis",
            "pattern_recognition",
            "prediction_generation",
            "scenario_simulation",
            "recommendation_synthesis"
        ],
        model_phases={
            "trend_analysis": "llama-scout-4",
            "pattern_recognition": "deepseek-v3",
            "prediction_generation": "grok-5",
            "scenario_simulation": "google-flash-2.5",
            "recommendation_synthesis": "claude-opus-4.1"
        },
        parameters={
            "prediction_horizon": 30,
            "scenario_count": 5,
            "confidence_threshold": 0.7
        }
    )
    print("Generated config:")
    print(config_json)
    
    # Validate config
    validation = ModeFactory.validate_config(ModeConfig(**json.loads(config_json)))
    print(f"Validation: {validation}")
    
    # Create agent from config
    agent = ModeFactory.create_from_json("modes/prophecy_mode.json")
    print(f"Created agent: {agent.mode_config.mode_name}")