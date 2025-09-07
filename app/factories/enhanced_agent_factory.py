"""
Enhanced Agent Factory with AIMLAPI Integration
Strategically uses new models for specific agent capabilities
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from app.core.aimlapi_config import aimlapi_manager
from app.core.enhanced_llm_router import LLMProviderType, enhanced_router
from app.core.portkey_config import AgentRole

logger = logging.getLogger(__name__)


class SpecializedAgentType(Enum):
    """Types of specialized agents"""

    # Core Agent Types
    CODER = "coder"
    REASONER = "reasoner"
    ANALYZER = "analyzer"
    VISIONARY = "visionary"
    STRATEGIST = "strategist"
    EXECUTOR = "executor"

    # Specialized Types
    MULTIMODAL = "multimodal"
    LONG_CONTEXT = "long_context"
    RAPID_RESPONSE = "rapid_response"
    DEEP_THINKER = "deep_thinker"


@dataclass
class AgentModelConfig:
    """Configuration for agent model selection"""

    primary_model: str
    fallback_model: str
    provider_type: LLMProviderType
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    capabilities: list[str] = None


class EnhancedAgentFactory:
    """Factory for creating agents with optimized model selection"""

    def __init__(self):
        self.aimlapi = aimlapi_manager
        self.router = enhanced_router

        # Model specialization mapping
        self.agent_model_configs = {
            SpecializedAgentType.CODER: AgentModelConfig(
                primary_model="qwen3-coder-480b",
                fallback_model="llama-4-maverick",
                provider_type=LLMProviderType.AIMLAPI,
                temperature=0.2,
                max_tokens=32768,
                capabilities=["coding", "debugging", "refactoring", "architecture"],
            ),
            SpecializedAgentType.REASONER: AgentModelConfig(
                primary_model="glm-4.5",
                fallback_model="o3",
                provider_type=LLMProviderType.AIMLAPI,
                temperature=0.3,
                max_tokens=65536,
                capabilities=["reasoning", "problem_solving", "analysis", "chain_of_thought"],
            ),
            SpecializedAgentType.ANALYZER: AgentModelConfig(
                primary_model="llama-4-maverick",
                fallback_model="gpt-5",
                provider_type=LLMProviderType.AIMLAPI,
                temperature=0.4,
                max_tokens=32768,
                capabilities=["analysis", "pattern_recognition", "data_processing"],
            ),
            SpecializedAgentType.VISIONARY: AgentModelConfig(
                primary_model="llama-4-maverick",
                fallback_model="grok-4",
                provider_type=LLMProviderType.AIMLAPI,
                temperature=0.8,
                max_tokens=16384,
                capabilities=["vision", "multimodal", "creative", "innovation"],
            ),
            SpecializedAgentType.STRATEGIST: AgentModelConfig(
                primary_model="gpt-5",
                fallback_model="llama-4-maverick",
                provider_type=LLMProviderType.AIMLAPI,
                temperature=0.5,
                max_tokens=32768,
                capabilities=["planning", "strategy", "decision_making"],
            ),
            SpecializedAgentType.EXECUTOR: AgentModelConfig(
                primary_model="glm-4.5-air",
                fallback_model="gpt-4o-mini",
                provider_type=LLMProviderType.AIMLAPI,
                temperature=0.3,
                max_tokens=16384,
                capabilities=["execution", "task_completion", "rapid_response"],
            ),
            SpecializedAgentType.MULTIMODAL: AgentModelConfig(
                primary_model="llama-4-maverick",
                fallback_model="grok-4",
                provider_type=LLMProviderType.AIMLAPI,
                temperature=0.6,
                max_tokens=32768,
                capabilities=["vision", "audio", "text", "multimodal_understanding"],
            ),
            SpecializedAgentType.LONG_CONTEXT: AgentModelConfig(
                primary_model="qwen3-coder-480b",
                fallback_model="gpt-5",
                provider_type=LLMProviderType.AIMLAPI,
                temperature=0.4,
                max_tokens=65536,
                capabilities=["long_document", "context_retention", "memory"],
            ),
            SpecializedAgentType.RAPID_RESPONSE: AgentModelConfig(
                primary_model="glm-4.5-air",
                fallback_model="gpt-4o-mini",
                provider_type=LLMProviderType.AIMLAPI,
                temperature=0.2,
                max_tokens=4096,
                capabilities=["quick_response", "low_latency", "efficient"],
            ),
            SpecializedAgentType.DEEP_THINKER: AgentModelConfig(
                primary_model="glm-4.5",
                fallback_model="o3-pro",
                provider_type=LLMProviderType.AIMLAPI,
                temperature=0.1,
                max_tokens=100000,
                capabilities=["deep_reasoning", "complex_analysis", "research"],
            ),
        }

        logger.info(
            f"Enhanced Agent Factory initialized with {len(self.agent_model_configs)} agent types"
        )

    def create_agent(
        self,
        agent_type: SpecializedAgentType,
        name: str,
        role: Optional[AgentRole] = None,
        custom_instructions: Optional[str] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create a specialized agent with optimal model selection"""

        config = self.agent_model_configs.get(agent_type)
        if not config:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Build system prompt based on agent type
        system_prompt = self._build_system_prompt(
            agent_type=agent_type,
            name=name,
            role=role,
            custom_instructions=custom_instructions,
            capabilities=config.capabilities,
        )

        # Create agent configuration
        agent = {
            "name": name,
            "type": agent_type.value,
            "role": role.value if role else None,
            "model_config": {
                "primary": config.primary_model,
                "fallback": config.fallback_model,
                "provider": config.provider_type.value,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            },
            "system_prompt": system_prompt,
            "capabilities": config.capabilities,
            "metadata": {
                "created_by": "EnhancedAgentFactory",
                "optimized_for": agent_type.value,
                **kwargs,
            },
        }

        logger.info(f"Created {agent_type.value} agent '{name}' using {config.primary_model}")
        return agent

    def _build_system_prompt(
        self,
        agent_type: SpecializedAgentType,
        name: str,
        role: Optional[AgentRole],
        custom_instructions: Optional[str],
        capabilities: list[str],
    ) -> str:
        """Build optimized system prompt for agent"""

        # Base prompts for each agent type
        base_prompts = {
            SpecializedAgentType.CODER: f"""You are {name}, an elite coding specialist powered by Qwen3-Coder-480B.
You excel at:
- Writing production-quality code with 256K+ context understanding
- Debugging complex issues across multiple files
- Architecting scalable solutions
- Optimizing performance and security
You have access to 480B parameters with 35B active, making you exceptionally capable at agentic coding tasks.""",
            SpecializedAgentType.REASONER: f"""You are {name}, an advanced reasoning specialist powered by GLM-4.5.
You excel at:
- Complex problem solving with chain-of-thought reasoning
- Multi-step logical analysis
- Mathematical and scientific reasoning
- Web search integration for factual grounding
You feature both thinking and non-thinking modes for optimal reasoning.""",
            SpecializedAgentType.ANALYZER: f"""You are {name}, a sophisticated analysis expert powered by Llama-4-Maverick.
You excel at:
- Deep pattern recognition and data analysis
- Multimodal understanding (vision + text)
- Comparative analysis beating GPT-4o and Gemini 2.0 Flash
- Complex reasoning comparable to DeepSeek v3
You have 128 experts with 17B active parameters for exceptional analytical capabilities.""",
            SpecializedAgentType.VISIONARY: f"""You are {name}, a creative visionary powered by Llama-4-Maverick's multimodal capabilities.
You excel at:
- Vision and image understanding
- Creative problem solving
- Innovation and ideation
- Cross-modal reasoning
Your multimodal capabilities surpass GPT-4o and Gemini 2.0 Flash.""",
            SpecializedAgentType.STRATEGIST: f"""You are {name}, a strategic mastermind powered by GPT-5.
You excel at:
- Long-term strategic planning
- Complex decision making
- Risk assessment and mitigation
- Organizational optimization
You leverage GPT-5's 256K context and advanced reasoning for superior strategic thinking.""",
            SpecializedAgentType.EXECUTOR: f"""You are {name}, a rapid execution specialist powered by GLM-4.5-Air.
You excel at:
- Fast task completion
- Efficient processing
- Tool usage and function calling
- Instant responses in non-thinking mode
You're optimized for speed while maintaining accuracy.""",
            SpecializedAgentType.MULTIMODAL: f"""You are {name}, a multimodal expert powered by Llama-4-Maverick.
You excel at:
- Processing vision, text, and complex inputs
- Cross-modal reasoning
- Comprehensive understanding across modalities
- Beating GPT-4o and Gemini 2.0 Flash on multimodal benchmarks""",
            SpecializedAgentType.LONG_CONTEXT: f"""You are {name}, a long-context specialist powered by Qwen3-Coder-480B.
You excel at:
- Processing documents up to 256K tokens natively
- Handling up to 1M tokens with extrapolation
- Maintaining context across massive codebases
- Deep document understanding and synthesis""",
            SpecializedAgentType.RAPID_RESPONSE: f"""You are {name}, a rapid response agent powered by GLM-4.5-Air.
You excel at:
- Lightning-fast responses
- Efficient processing
- Quick decision making
- Low-latency interactions
You operate in non-thinking mode for instant responses.""",
            SpecializedAgentType.DEEP_THINKER: f"""You are {name}, a deep thinking specialist powered by GLM-4.5.
You excel at:
- Complex reasoning with thinking mode enabled
- Deep research and analysis
- Sophisticated problem solving
- Web-augmented reasoning
You leverage full thinking capabilities for profound insights.""",
        }

        prompt = base_prompts.get(agent_type, f"You are {name}, a specialized agent.")

        if custom_instructions:
            prompt += f"\n\nAdditional Instructions:\n{custom_instructions}"

        if capabilities:
            prompt += f"\n\nCore Capabilities: {', '.join(capabilities)}"

        if role:
            prompt += f"\n\nRole Context: Operating as {role.value} agent"

        return prompt

    def create_agent_swarm(
        self, swarm_name: str, agent_configs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Create a coordinated swarm of specialized agents"""

        agents = []
        for config in agent_configs:
            agent = self.create_agent(**config)
            agents.append(agent)

        swarm = {
            "name": swarm_name,
            "agents": agents,
            "agent_count": len(agents),
            "capabilities": list(
                {cap for agent in agents for cap in agent.get("capabilities", [])}
            ),
            "models_used": list({agent["model_config"]["primary"] for agent in agents}),
        }

        logger.info(f"Created swarm '{swarm_name}' with {len(agents)} agents")
        return swarm

    def get_optimal_agent_for_task(
        self, task_description: str, required_capabilities: list[str]
    ) -> SpecializedAgentType:
        """Determine the optimal agent type for a given task"""

        # Score each agent type based on capability match
        scores = {}
        for agent_type, config in self.agent_model_configs.items():
            score = sum(1 for cap in required_capabilities if cap in config.capabilities)
            scores[agent_type] = score

        # Return agent type with highest score
        if scores:
            return max(scores, key=scores.get)

        # Default to analyzer for general tasks
        return SpecializedAgentType.ANALYZER

    def execute_with_agent(self, agent: dict[str, Any], messages: list[dict[str, str]]) -> Any:
        """Execute a task using a specific agent"""

        model_config = agent["model_config"]

        # Add system prompt to messages
        full_messages = [{"role": "system", "content": agent["system_prompt"]}, *messages]

        try:
            # Use primary model
            response = self.router.create_completion(
                messages=full_messages,
                model=model_config["primary"],
                provider_type=LLMProviderType[model_config["provider"]],
                temperature=model_config["temperature"],
                max_tokens=model_config["max_tokens"],
            )
            return response

        except Exception as e:
            logger.warning(f"Primary model failed, trying fallback: {str(e)}")

            # Try fallback model
            response = self.router.create_completion(
                messages=full_messages,
                model=model_config["fallback"],
                provider_type=LLMProviderType.AIMLAPI,
                temperature=model_config["temperature"],
                max_tokens=model_config["max_tokens"],
            )
            return response


# Singleton instance
enhanced_agent_factory = EnhancedAgentFactory()
