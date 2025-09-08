"""
Comprehensive Swarm Factory Module
Integrates mythology agents, military swarms, model routing, and deployment automation
"""

from app.factory.comprehensive_swarm_factory import (
    ComprehensiveSwarmFactory,
    DeploymentSchedule,
    ExecutionContext,
    SwarmExecutionResult,
    SwarmFactoryConfig,
    SwarmType,
    create_business_intelligence_swarm,
    create_coding_strike_swarm,
    create_strategic_planning_swarm,
    create_tactical_recon_swarm,
    execute_quick_analysis,
    get_comprehensive_factory,
)
from app.factory.deployment_config import (
    DeploymentEnvironment,
    DeploymentManager,
    DeploymentRun,
    DeploymentStatus,
    DeploymentTemplate,
    ScheduleConfig,
    ScheduleType,
    get_deployment_manager,
    start_automated_deployments,
    stop_automated_deployments,
    trigger_emergency_response,
)
from app.factory.factory_bootstrap import (
    FactoryBootstrap,
    FactoryBootstrapError,
    development_bootstrap,
    get_bootstrap,
    minimal_bootstrap,
    production_bootstrap,
    quick_bootstrap,
)
from app.factory.model_routing_config import (
    ModelPerformanceTier,
    ModelRoutingEngine,
    ModelRoutingRule,
    SwarmModelProfile,
    create_cost_optimized_rule,
    create_quality_focused_rule,
    create_speed_optimized_rule,
    get_routing_engine,
)
from app.factory.slack_delivery_templates import (
    MessageTemplate,
    SlackChannelConfig,
    SlackDeliveryTemplateManager,
    format_executive_summary,
    format_strategic_analysis,
    format_technical_report,
    get_critical_alert_config,
    get_daily_intelligence_config,
    get_executive_delivery_config,
    get_strategic_delivery_config,
    get_technical_delivery_config,
    get_template_manager,
)

__version__ = "1.0.0"
__author__ = "Sophia-Artemis Intelligence Platform"

# Module metadata
__all__ = [
    # Core factory
    "ComprehensiveSwarmFactory",
    "SwarmFactoryConfig",
    "SwarmType",
    "DeploymentSchedule",
    "ExecutionContext",
    "SwarmExecutionResult",
    "get_comprehensive_factory",
    # Convenience functions
    "create_business_intelligence_swarm",
    "create_tactical_recon_swarm",
    "create_strategic_planning_swarm",
    "create_coding_strike_swarm",
    "execute_quick_analysis",
    # Model routing
    "ModelRoutingEngine",
    "ModelPerformanceTier",
    "SwarmModelProfile",
    "ModelRoutingRule",
    "get_routing_engine",
    "create_cost_optimized_rule",
    "create_quality_focused_rule",
    "create_speed_optimized_rule",
    # Deployment management
    "DeploymentManager",
    "DeploymentTemplate",
    "ScheduleConfig",
    "DeploymentRun",
    "DeploymentStatus",
    "DeploymentEnvironment",
    "ScheduleType",
    "get_deployment_manager",
    "start_automated_deployments",
    "stop_automated_deployments",
    "trigger_emergency_response",
    # Slack delivery
    "SlackDeliveryTemplateManager",
    "SlackChannelConfig",
    "MessageTemplate",
    "get_template_manager",
    "get_executive_delivery_config",
    "get_technical_delivery_config",
    "get_strategic_delivery_config",
    "get_daily_intelligence_config",
    "get_critical_alert_config",
    "format_executive_summary",
    "format_technical_report",
    "format_strategic_analysis",
    # Bootstrap system
    "FactoryBootstrap",
    "FactoryBootstrapError",
    "get_bootstrap",
    "quick_bootstrap",
    "production_bootstrap",
    "development_bootstrap",
    "minimal_bootstrap",
]

# Factory system information
FACTORY_INFO = {
    "name": "Sophia-Artemis Intelligent Swarm Factory",
    "version": __version__,
    "description": "Comprehensive AI swarm factory integrating mythology and military agents",
    "components": {
        "mythology_agents": ["Hermes", "Asclepius", "Athena", "Odin", "Minerva"],
        "military_units": [
            "Pathfinders",
            "Sentinels",
            "Architects",
            "Operators",
            "Guardians",
        ],
        "swarm_types": [
            "Business Intelligence",
            "Strategic Planning",
            "Technical Operations",
            "Code Quality",
            "Emergency Response",
        ],
        "features": [
            "Model Routing",
            "Cost Optimization",
            "Scheduled Deployments",
            "Slack Integration",
            "Performance Monitoring",
        ],
    },
    "supported_models": [
        "GPT-5",
        "GPT-4o",
        "Claude-3.5-Sonnet",
        "Claude-3-Opus",
        "Grok-5",
        "Gemini-2.0-Pro",
        "DeepSeek-Coder",
        "Qwen-3-70B",
        "Llama-3.1-70B",
    ],
    "integrations": ["Portkey", "Slack", "Memory Router", "Scheduler", "Cost Tracker"],
}


def get_factory_info():
    """Get comprehensive factory system information"""
    return FACTORY_INFO


def print_factory_banner():
    """Print factory banner with system information"""
    print("=" * 70)
    print("🏭 SOPHIA-ARTEMIS INTELLIGENT SWARM FACTORY")
    print("=" * 70)
    print(f"Version: {__version__}")
    print(f"Description: {FACTORY_INFO['description']}")
    print()
    print("🧠 Mythology Agents:")
    for agent in FACTORY_INFO["components"]["mythology_agents"]:
        print(f"   • {agent}")
    print()
    print("⚔️  Military Units:")
    for unit in FACTORY_INFO["components"]["military_units"]:
        print(f"   • {unit}")
    print()
    print("🚀 Key Features:")
    for feature in FACTORY_INFO["components"]["features"]:
        print(f"   • {feature}")
    print("=" * 70)


# Auto-display banner when module is imported in interactive mode
import sys

if hasattr(sys, "ps1"):  # Interactive mode
    print_factory_banner()
