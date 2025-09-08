"""
Orchestrator Configuration with GPT-5 as Primary Model
Centralized configuration for all orchestrators
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from app.core.enhanced_llm_router import LLMProviderType, enhanced_router


class OrchestratorType(Enum):
    """Types of orchestrators"""

    ARTEMIS = "artemis"
    SOPHIA = "sophia"
    MASTER = "master"


@dataclass
class OrchestratorModelConfig:
    """Model configuration for orchestrators"""

    primary_model: str = "gpt-5"
    primary_provider: LLMProviderType = LLMProviderType.AIMLAPI
    fallback_model: str = "claude-opus-4.1"
    fallback_provider: LLMProviderType = LLMProviderType.AIMLAPI
    emergency_model: str = "gpt-4o"
    emergency_provider: LLMProviderType = LLMProviderType.PORTKEY
    temperature: float = 0.7
    max_tokens: int = 32768
    context_window: int = 256000


class OrchestratorConfigManager:
    """Centralized configuration manager for all orchestrators"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True

            # Orchestrator-specific configurations
            self.configs = {
                OrchestratorType.ARTEMIS: OrchestratorModelConfig(
                    primary_model="gpt-5",
                    primary_provider=LLMProviderType.AIMLAPI,
                    fallback_model="claude-opus-4.1",
                    fallback_provider=LLMProviderType.AIMLAPI,
                    emergency_model="deepseek-reasoner-v3.1",
                    emergency_provider=LLMProviderType.PORTKEY,
                    temperature=0.6,  # Lower for technical precision
                    max_tokens=65536,
                    context_window=256000,
                ),
                OrchestratorType.SOPHIA: OrchestratorModelConfig(
                    primary_model="gpt-5",
                    primary_provider=LLMProviderType.AIMLAPI,
                    fallback_model="claude-opus-4.1",
                    fallback_provider=LLMProviderType.AIMLAPI,
                    emergency_model="gemini-2.5-pro",
                    emergency_provider=LLMProviderType.PORTKEY,
                    temperature=0.7,  # Balanced for business
                    max_tokens=32768,
                    context_window=256000,
                ),
                OrchestratorType.MASTER: OrchestratorModelConfig(
                    primary_model="gpt-5",
                    primary_provider=LLMProviderType.AIMLAPI,
                    fallback_model="grok-4-heavy",
                    fallback_provider=LLMProviderType.AIMLAPI,
                    emergency_model="claude-opus-4.1",
                    emergency_provider=LLMProviderType.AIMLAPI,
                    temperature=0.5,  # Lower for coordination
                    max_tokens=100000,
                    context_window=256000,
                ),
            }

            # Specialized task routing
            self.task_routing = {
                "code_generation": {
                    "primary": "grok-code-fast-1",
                    "provider": LLMProviderType.AIMLAPI,
                    "reason": "92 tokens/sec, $0.20/$1.50 cost",
                },
                "large_context_analysis": {
                    "primary": "qwen3-coder-480b",
                    "provider": LLMProviderType.AIMLAPI,
                    "reason": "256K-1M token context",
                },
                "complex_reasoning": {
                    "primary": "grok-4-heavy",
                    "provider": LLMProviderType.AIMLAPI,
                    "reason": "5-10x compute, multi-agent reasoning",
                },
                "repository_scanning": {
                    "primary": "gemini-2.5-flash",
                    "provider": LLMProviderType.PORTKEY,
                    "reason": "Fast, efficient scanning",
                },
                "strategic_analysis": {
                    "primary": "claude-opus-4.1",
                    "provider": LLMProviderType.AIMLAPI,
                    "reason": "Nuanced understanding",
                },
            }

    def get_config(self, orchestrator_type: OrchestratorType) -> OrchestratorModelConfig:
        """Get configuration for specific orchestrator"""
        return self.configs.get(orchestrator_type, OrchestratorModelConfig())

    def get_model_for_task(self, task_type: str) -> dict[str, Any]:
        """Get optimal model for specific task type"""
        if task_type in self.task_routing:
            return self.task_routing[task_type]

        # Default to GPT-5 for unknown tasks
        return {
            "primary": "gpt-5",
            "provider": LLMProviderType.AIMLAPI,
            "reason": "General purpose, most capable",
        }

    def create_orchestrator_prompt(self, orchestrator_type: OrchestratorType) -> str:
        """Create system prompt for orchestrator"""
        prompts = {
            OrchestratorType.ARTEMIS: """You are ARTEMIS, the technical orchestrator powered by GPT-5.
You coordinate all technical operations including:
- Code generation and review
- System architecture decisions
- Performance optimization
- Security assessments
- Technical swarm coordination

You have access to specialized swarms:
- Coding Swarm: Grok Code Fast 1, Qwen3-Coder-480B, GLM-4.5-Air
- Analysis Team: DeepSeek Reasoner V3.1, Llama-4-Maverick
- Security Team: Claude Opus 4.1, specialized scanners

Prioritize efficiency and technical excellence. Use GPT-5's advanced capabilities for complex coordination.""",
            OrchestratorType.SOPHIA: """You are SOPHIA, the business intelligence orchestrator powered by GPT-5.
You coordinate all business operations including:
- Market analysis and research
- Sales pipeline management
- Revenue forecasting
- Competitive intelligence
- Strategic planning

You have access to specialized agents:
- Research Team: Perplexity Sonar Pro, Llama-4-Scout
- Analytics Team: Claude Opus 4.1, Gemini 2.5 Pro
- Strategy Council: Grok-4, DeepSeek Chat V3.1

Focus on business value and strategic insights. Leverage GPT-5's reasoning for complex business decisions.""",
            OrchestratorType.MASTER: """You are the MASTER ORCHESTRATOR powered by GPT-5.
You coordinate between all orchestrators and manage:
- Cross-domain operations
- Resource allocation
- Priority management
- Conflict resolution
- System-wide optimization

You can escalate to:
- Grok 4 Heavy for multi-agent complex problems
- Claude Opus 4.1 for nuanced strategic decisions
- Emergency fallbacks when needed

Maintain system harmony and optimize for overall performance.""",
        }

        return prompts.get(orchestrator_type, "You are an orchestrator powered by GPT-5.")

    def execute_with_orchestrator(
        self, orchestrator_type: OrchestratorType, messages: list, task_type: Optional[str] = None
    ) -> Any:
        """Execute task with orchestrator configuration"""
        config = self.get_config(orchestrator_type)

        # Add orchestrator prompt
        system_prompt = self.create_orchestrator_prompt(orchestrator_type)
        full_messages = [{"role": "system", "content": system_prompt}, *messages]

        # If specific task type, might use specialized model
        if task_type:
            task_config = self.get_model_for_task(task_type)
            model = task_config["primary"]
            provider = task_config["provider"]
        else:
            model = config.primary_model
            provider = config.primary_provider

        try:
            # Try primary model
            response = enhanced_router.create_completion(
                messages=full_messages,
                model=model,
                provider_type=provider,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            return response

        except Exception as e:
            print(f"Primary model failed: {e}, trying fallback...")

            # Try fallback
            try:
                response = enhanced_router.create_completion(
                    messages=full_messages,
                    model=config.fallback_model,
                    provider_type=config.fallback_provider,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )
                return response

            except Exception as e2:
                print(f"Fallback failed: {e2}, using emergency model...")

                # Emergency fallback
                response = enhanced_router.create_completion(
                    messages=full_messages,
                    model=config.emergency_model,
                    provider_type=config.emergency_provider,
                    temperature=config.temperature,
                    max_tokens=min(config.max_tokens, 16384),  # Reduce for emergency
                )
                return response

    def get_status(self) -> dict[str, Any]:
        """Get status of all orchestrators"""
        return {
            "orchestrators": {
                name.value: {
                    "primary": config.primary_model,
                    "fallback": config.fallback_model,
                    "emergency": config.emergency_model,
                    "context": config.context_window,
                }
                for name, config in self.configs.items()
            },
            "task_routing": self.task_routing,
            "gpt5_status": "Active as primary for all orchestrators",
        }


# Singleton instance
orchestrator_config = OrchestratorConfigManager()
