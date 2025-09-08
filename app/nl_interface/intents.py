"""
Intent definitions and patterns for Natural Language Interface
"""

from dataclasses import dataclass


@dataclass
class IntentPattern:
    """Definition of an intent pattern"""

    name: str
    description: str
    patterns: list[str]
    entities: list[str]
    examples: list[str]
    workflow_id: str
    response_template: str


# Intent pattern definitions
INTENT_PATTERNS = {
    "system_status": IntentPattern(
        name="system_status",
        description="Check the status of the system and services",
        patterns=[
            "show system status",
            "get system status",
            "system status",
            "how is the system",
            "check system health",
            "status report",
        ],
        entities=[],
        examples=[
            "Show me the system status",
            "How is the system doing?",
            "Get current system health",
        ],
        workflow_id="system-status-workflow",
        response_template="System Status:\n{status_details}",
    ),
    "run_agent": IntentPattern(
        name="run_agent",
        description="Execute a specific agent",
        patterns=[
            "run agent {agent_name}",
            "start agent {agent_name}",
            "execute {agent_name} agent",
            "launch {agent_name}",
            "activate agent {agent_name}",
        ],
        entities=["agent_name"],
        examples=["run agent researcher", "start the coding agent", "execute reviewer agent"],
        workflow_id="agent-execution-workflow",
        response_template="Starting agent '{agent_name}'...\n{execution_result}",
    ),
    "scale_service": IntentPattern(
        name="scale_service",
        description="Scale a service to specific number of instances",
        patterns=[
            "scale {service} to {count}",
            "scale service {service} to {count}",
            "set {service} replicas to {count}",
            "increase {service} instances",
            "decrease {service} instances",
        ],
        entities=["service", "count"],
        examples=["scale ollama to 3", "set redis replicas to 2", "increase weaviate instances"],
        workflow_id="service-scaling-workflow",
        response_template="Scaling {service} to {count} instance(s)...\n{scaling_result}",
    ),
    "execute_workflow": IntentPattern(
        name="execute_workflow",
        description="Trigger a specific workflow",
        patterns=[
            "run workflow {workflow_name}",
            "execute workflow {workflow_name}",
            "trigger {workflow_name} workflow",
            "start {workflow_name} process",
        ],
        entities=["workflow_name"],
        examples=[
            "run workflow data-pipeline",
            "execute backup workflow",
            "trigger cleanup workflow",
        ],
        workflow_id="custom-workflow",
        response_template="Executing workflow '{workflow_name}'...\n{workflow_result}",
    ),
    "query_data": IntentPattern(
        name="query_data",
        description="Query data from vector store or database",
        patterns=[
            "search for {query}",
            "find {query}",
            "query {query}",
            "get data about {query}",
            "lookup {query}",
        ],
        entities=["query"],
        examples=["search for user documents", "find recent logs", "query performance metrics"],
        workflow_id="data-query-workflow",
        response_template="Query Results for '{query}':\n{query_results}",
    ),
    "stop_service": IntentPattern(
        name="stop_service",
        description="Stop a running service",
        patterns=[
            "stop {service}",
            "stop service {service}",
            "shutdown {service}",
            "halt {service}",
            "terminate {service}",
        ],
        entities=["service"],
        examples=["stop redis", "shutdown ollama service", "halt weaviate"],
        workflow_id="service-control-workflow",
        response_template="Stopping service '{service}'...\n{stop_result}",
    ),
    "list_agents": IntentPattern(
        name="list_agents",
        description="List all available agents",
        patterns=[
            "list agents",
            "show agents",
            "display all agents",
            "what agents are available",
            "get agent list",
        ],
        entities=[],
        examples=["list all agents", "show available agents", "what agents can I run?"],
        workflow_id="agent-listing-workflow",
        response_template="Available Agents:\n{agents_list}",
    ),
    "get_metrics": IntentPattern(
        name="get_metrics",
        description="Get performance metrics",
        patterns=[
            "show metrics",
            "get metrics",
            "display metrics for {target}",
            "metrics for {target}",
            "performance stats",
            "show performance",
        ],
        entities=["target"],
        examples=["show metrics", "get metrics for ollama", "display redis performance"],
        workflow_id="metrics-collection-workflow",
        response_template="Metrics for {target}:\n{metrics_data}",
    ),
    "help": IntentPattern(
        name="help",
        description="Show help and available commands",
        patterns=["help", "what can you do", "show commands", "list commands", "how to use"],
        entities=[],
        examples=["help", "what commands are available?", "show me what you can do"],
        workflow_id="help-workflow",
        response_template="Available Commands:\n{help_text}",
    ),
}


def get_intent_pattern(intent_name: str) -> IntentPattern:
    """Get intent pattern by name"""
    return INTENT_PATTERNS.get(intent_name)


def get_all_intents() -> dict[str, IntentPattern]:
    """Get all available intent patterns"""
    return INTENT_PATTERNS


def get_intent_examples() -> dict[str, list[str]]:
    """Get examples for all intents"""
    return {name: pattern.examples for name, pattern in INTENT_PATTERNS.items()}


def format_help_text() -> str:
    """Format help text with all available commands"""
    lines = ["Here are the available commands:\n"]

    for _name, pattern in INTENT_PATTERNS.items():
        lines.append(f"• {pattern.description}")
        lines.append("  Examples:")
        for example in pattern.examples[:2]:  # Show max 2 examples
            lines.append(f"    - {example}")
        lines.append("")

    return "\n".join(lines)
