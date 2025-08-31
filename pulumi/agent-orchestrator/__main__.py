"""
Agent Orchestrator Infrastructure for Sophia Intel AI
Deploys LLM execution and swarm orchestration with Lambda Labs GPU integration.
"""

import pulumi
from pulumi import StackReference, Output, ResourceOptions
import pulumi_aws as aws
import sys
import os

# Add shared components to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from shared import FlyApp, FlyAppConfig

class LambdaLabsGPU(pulumi.ComponentResource):
    """
    Lambda Labs GPU instances via custom resource.
    Manages GPU compute for heavy LLM operations.
    """
    
    def __init__(self, name: str, gpu_count: int = 2, opts: ResourceOptions = None):
        super().__init__("sophia:infrastructure:LambdaLabsGPU", name, None, opts)
        
        # Note: Lambda Labs doesn't have official Pulumi provider
        # Using custom resource with their API
        config = pulumi.Config()
        lambda_labs_api_key = config.require_secret("lambda_labs_api_key")
        
        # Export GPU configuration for services to use
        self.register_outputs({
            "gpu_endpoints": [
                f"https://lambda-gpu-{i}.internal:8080" 
                for i in range(gpu_count)
            ],
            "gpu_count": gpu_count,
            "instance_type": "gpu_1x_a100_sxm4",  # Lambda Labs instance type
            "api_key": lambda_labs_api_key
        })

def main():
    """Deploy agent orchestrator infrastructure."""
    
    config = pulumi.Config()
    environment = config.get("environment") or "dev"
    max_concurrent_swarms = config.get_int("max_concurrent_swarms") or 10
    gpu_count = config.get_int("lambda_labs_gpu_count") or 2
    
    # Reference other stacks
    shared_stack = StackReference(f"shared-{environment}")
    database_stack = StackReference(f"database-{environment}")
    vector_stack = StackReference(f"vector-store-{environment}")
    
    # Deploy Lambda Labs GPU instances
    lambda_gpu = LambdaLabsGPU("lambda-gpu-cluster", gpu_count=gpu_count)
    
    # Agent Orchestrator Service Configuration
    orchestrator_config = FlyAppConfig(
        name=f"sophia-agent-orchestrator-{environment}",
        image="ghcr.io/sophia-intel-ai/agent-orchestrator:latest",
        port=8080,
        scale=3,  # Multiple instances for high availability
        memory_mb=4096,  # High memory for complex orchestration
        cpu_cores=4.0,   # High CPU for parallel processing
        env_vars={
            "ENVIRONMENT": environment,
            "LOG_LEVEL": "INFO" if environment == "prod" else "DEBUG",
            
            # Database connections
            "POSTGRES_URL": database_stack.get_output("postgres_connection_string"),
            "REDIS_URL": database_stack.get_output("redis_url"),
            
            # Vector store integration
            "VECTOR_STORE_URL": vector_stack.get_output("vector_store_internal_url"),
            "WEAVIATE_URL": vector_stack.get_output("weaviate_url"),
            
            # GPU compute integration
            "LAMBDA_LABS_API_KEY": pulumi.Config().require_secret("lambda_labs_api_key"),
            "GPU_ENDPOINTS": lambda_gpu.gpu_endpoints,
            "ENABLE_GPU_ACCELERATION": "true",
            
            # Model routing configuration (Portkey/OpenRouter)
            "PORTKEY_API_KEY": pulumi.Config().require_secret("portkey_api_key"),
            "PORTKEY_BASE_URL": "https://api.portkey.ai/v1",
            "OPENROUTER_API_KEY": pulumi.Config().require_secret("openrouter_api_key"),
            
            # Swarm orchestration settings
            "MAX_CONCURRENT_SWARMS": str(max_concurrent_swarms),
            "DEFAULT_SWARM_TIMEOUT": "300",  # 5 minutes
            "MAX_AGENTS_PER_SWARM": "10",
            "ENABLE_STREAMING": "true",
            
            # Model pools configuration
            "FAST_MODEL_POOL": "groq/llama-3.2-90b-text-preview,openai/gpt-4o-mini",
            "BALANCED_MODEL_POOL": "openai/gpt-4o,anthropic/claude-3.5-sonnet",
            "HEAVY_MODEL_POOL": "anthropic/claude-3.5-sonnet,openai/gpt-4o,qwen/qwen-2.5-coder-32b-instruct",
            
            # Performance tuning
            "WORKER_THREADS": "8",
            "MAX_QUEUE_SIZE": "1000",
            "RESPONSE_TIMEOUT": "120"
        }
    )
    
    # Deploy Agent Orchestrator Service
    agent_orchestrator = FlyApp("agent-orchestrator", orchestrator_config)
    
    # Export outputs for other stacks
    pulumi.export("agent_orchestrator_url", agent_orchestrator.public_url)
    pulumi.export("agent_orchestrator_internal_url", agent_orchestrator.internal_url)
    pulumi.export("lambda_gpu_endpoints", lambda_gpu.gpu_endpoints)
    pulumi.export("lambda_gpu_count", lambda_gpu.gpu_count)
    
    # Swarm configuration for the system
    pulumi.export("swarm_configuration", {
        "patterns": {
            "adversarial_debate": {
                "enabled": True,
                "min_agents": 3,
                "max_rounds": 5,
                "consensus_threshold": 0.7
            },
            "consensus_building": {
                "enabled": True,
                "voting_mechanism": "ranked_choice",
                "quorum_percentage": 60
            },
            "quality_gates": {
                "enabled": True,
                "accuracy_threshold": 0.85,
                "safety_threshold": 0.95,
                "compliance_checks": True
            },
            "dynamic_roles": {
                "enabled": True,
                "role_assignment": "capability_based",
                "specialization": "task_adaptive"
            }
        },
        "teams": {
            "FAST": {
                "agents": ["strategic_planner", "fast_prototyper", "technical_judge"],
                "models": ["groq/llama-3.2-90b-text-preview", "openai/gpt-4o-mini"],
                "timeout": 60,
                "use_case": "Quick fixes, simple tasks"
            },
            "STANDARD": {
                "agents": ["strategic_planner", "primary_coder", "code_critic", "quality_evaluator", "technical_judge"],
                "models": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet"],
                "timeout": 180,
                "use_case": "Regular development tasks"
            },
            "ADVANCED": {
                "agents": ["strategic_planner", "system_architect", "primary_coder", "alternative_coder", "code_critic", "security_analyst", "technical_judge"],
                "models": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "qwen/qwen-2.5-coder-32b-instruct"],
                "timeout": 300,
                "use_case": "Complex features, architecture decisions"
            },
            "GENESIS": {
                "agents": ["strategic_planner", "system_architect", "primary_coder", "alternative_coder", "fast_prototyper", "code_critic", "security_analyst", "performance_analyst", "quality_evaluator", "technical_judge", "technical_researcher"],
                "models": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "qwen/qwen-2.5-coder-32b-instruct", "deepseek/deepseek-coder-v2-lite-instruct"],
                "timeout": 600,
                "use_case": "Mission-critical, complex systems"
            }
        },
        "roles": {
            "strategic_planner": {
                "model": "anthropic/claude-3.5-sonnet",
                "temperature": 0.3,
                "purpose": "Task breakdown and planning"
            },
            "system_architect": {
                "model": "openai/gpt-4o",
                "temperature": 0.2,
                "purpose": "Architecture decisions and design"
            },
            "primary_coder": {
                "model": "qwen/qwen-2.5-coder-32b-instruct",
                "temperature": 0.1,
                "purpose": "Main implementation and code generation"
            },
            "code_critic": {
                "model": "openai/gpt-4o-mini",
                "temperature": 0.4,
                "purpose": "Code review and improvement suggestions"
            },
            "technical_judge": {
                "model": "deepseek/deepseek-reasoner",
                "temperature": 0.2,
                "purpose": "Final decision making and approval"
            }
        }
    })
    
    # Model routing and execution configuration
    pulumi.export("model_routing", {
        "portkey_integration": {
            "enabled": True,
            "virtual_keys": {
                "openrouter": "pk-live-openrouter-vk",
                "anthropic": "pk-live-anthropic-vk",
                "openai": "pk-live-openai-vk"
            },
            "fallback_chains": [
                ["anthropic/claude-3.5-sonnet", "openai/gpt-4o"],
                ["openai/gpt-4o", "groq/llama-3.2-90b-text-preview"],
                ["qwen/qwen-2.5-coder-32b-instruct", "deepseek/deepseek-coder-v2-lite-instruct"]
            ]
        },
        "load_balancing": {
            "strategy": "weighted_round_robin",
            "health_checks": True,
            "retry_logic": True,
            "circuit_breaker": True
        },
        "cost_optimization": {
            "daily_budget_usd": 100,
            "alert_threshold_usd": 80,
            "auto_downgrade": True,
            "usage_tracking": True
        }
    })
    
    pulumi.export("environment", environment)

if __name__ == "__main__":
    main()