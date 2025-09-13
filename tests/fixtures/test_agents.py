"""
Test Agent Fixtures
Provides pre-configured test agents for both  and Sophia domains
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
from swarm import Agent
@dataclass
class TestAgentConfig:
    """Configuration for test agents"""
    name: str
    domain: str
    personality: str
    capabilities: List[str]
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1000
    tools: Optional[List[Any]] = None
    metadata: Optional[Dict[str, Any]] = None
class MockAgent(Agent):
    """Mock agent for testing"""
    def __init__(self, config: TestAgentConfig):
        """Initialize mock agent with test configuration"""
        super().__init__(
            name=config.name,
            model=config.model,
            instructions=f"Test agent: {config.name} in {config.domain} domain",
            functions=config.tools or [],
        )
        self.config = config
        self.domain = config.domain
        self.personality = config.personality
        self.capabilities = config.capabilities
        self.metadata = config.metadata or {}
        # Mock response generation
        self.response_generator = AsyncMock()
        self.response_generator.return_value = {
            "content": f"Mock response from {config.name}",
            "role": "assistant",
            "agent": config.name,
        }
        # Track interactions
        self.interaction_count = 0
        self.messages_received: List[Dict[str, Any]] = []
        self.messages_sent: List[Dict[str, Any]] = []
        self.tool_calls: List[Dict[str, Any]] = []
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message and generate response"""
        self.interaction_count += 1
        self.messages_received.append(message)
        # Generate mock response
        response = await self.response_generator(message)
        self.messages_sent.append(response)
        return response
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool function"""
        tool_call = {
            "tool": tool_name,
            "arguments": arguments,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        self.tool_calls.append(tool_call)
        # Return mock tool result
        return {
            "success": True,
            "result": f"Mock result from {tool_name}",
            "agent": self.config.name,
        }
    def reset(self):
        """Reset agent state"""
        self.interaction_count = 0
        self.messages_received.clear()
        self.messages_sent.clear()
        self.tool_calls.clear()
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "name": self.config.name,
            "domain": self.config.domain,
            "interaction_count": self.interaction_count,
            "messages_received": len(self.messages_received),
            "messages_sent": len(self.messages_sent),
            "tool_calls": len(self.tool_calls),
            "capabilities": self.config.capabilities,
        }
#  Test Agents
def create__scout_agent() -> MockAgent:
    """Create a test  scout agent"""
    config = TestAgentConfig(
        name="Scout-Test",
        domain="",
        personality="tactical_observer",
        capabilities=[
            "repository_analysis",
            "vulnerability_scanning",
            "dependency_checking",
        ],
        tools=[
            MagicMock(name="scan_repository"),
            MagicMock(name="analyze_code"),
            MagicMock(name="check_vulnerabilities"),
        ],
        metadata={"squad": "recon", "rank": "specialist", "clearance": "secret"},
    )
    return MockAgent(config)
def create__engineer_agent() -> MockAgent:
    """Create a test  engineer agent"""
    config = TestAgentConfig(
        name="Engineer-Test",
        domain="",
        personality="technical_specialist",
        capabilities=["code_generation", "refactoring", "optimization", "testing"],
        tools=[
            MagicMock(name="generate_code"),
            MagicMock(name="refactor_code"),
            MagicMock(name="optimize_performance"),
            MagicMock(name="write_tests"),
        ],
        metadata={
            "squad": "engineering",
            "rank": "sergeant",
            "clearance": "confidential",
        },
    )
    return MockAgent(config)
def create__commander_agent() -> MockAgent:
    """Create a test  commander agent"""
    config = TestAgentConfig(
        name="Commander-Test",
        domain="",
        personality="strategic_leader",
        capabilities=[
            "mission_planning",
            "resource_allocation",
            "team_coordination",
            "decision_making",
        ],
        tools=[
            MagicMock(name="plan_mission"),
            MagicMock(name="allocate_resources"),
            MagicMock(name="coordinate_teams"),
            MagicMock(name="make_decision"),
        ],
        metadata={"squad": "command", "rank": "lieutenant", "clearance": "top_secret"},
    )
    return MockAgent(config)
def create__analyst_agent() -> MockAgent:
    """Create a test  analyst agent"""
    config = TestAgentConfig(
        name="Analyst-Test",
        domain="",
        personality="data_specialist",
        capabilities=[
            "pattern_recognition",
            "threat_assessment",
            "report_generation",
            "trend_analysis",
        ],
        tools=[
            MagicMock(name="analyze_patterns"),
            MagicMock(name="assess_threats"),
            MagicMock(name="generate_report"),
            MagicMock(name="analyze_trends"),
        ],
        metadata={"squad": "intelligence", "rank": "corporal", "clearance": "secret"},
    )
    return MockAgent(config)
# Sophia Test Agents
def create_sophia_athena_agent() -> MockAgent:
    """Create a test Sophia Athena (wisdom) agent"""
    config = TestAgentConfig(
        name="Athena-Test",
        domain="sophia",
        personality="wise_strategist",
        capabilities=[
            "strategic_planning",
            "knowledge_synthesis",
            "insight_generation",
            "wisdom_sharing",
        ],
        temperature=0.8,
        tools=[
            MagicMock(name="plan_strategy"),
            MagicMock(name="synthesize_knowledge"),
            MagicMock(name="generate_insights"),
            MagicMock(name="share_wisdom"),
        ],
        metadata={
            "council": "wisdom",
            "aspect": "strategic_wisdom",
            "domain_expertise": ["business", "technology", "leadership"],
        },
    )
    return MockAgent(config)
def create_sophia_hermes_agent() -> MockAgent:
    """Create a test Sophia Hermes (messenger) agent"""
    config = TestAgentConfig(
        name="Hermes-Test",
        domain="sophia",
        personality="swift_communicator",
        capabilities=[
            "message_routing",
            "information_gathering",
            "rapid_response",
            "cross_domain_liaison",
        ],
        temperature=0.6,
        tools=[
            MagicMock(name="route_message"),
            MagicMock(name="gather_information"),
            MagicMock(name="send_notification"),
            MagicMock(name="coordinate_domains"),
        ],
        metadata={
            "council": "communication",
            "aspect": "swift_messenger",
            "response_time": "immediate",
        },
    )
    return MockAgent(config)
def create_sophia_apollo_agent() -> MockAgent:
    """Create a test Sophia Apollo (prophecy) agent"""
    config = TestAgentConfig(
        name="Apollo-Test",
        domain="sophia",
        personality="visionary_prophet",
        capabilities=[
            "trend_prediction",
            "market_analysis",
            "risk_assessment",
            "opportunity_identification",
        ],
        temperature=0.9,
        tools=[
            MagicMock(name="predict_trends"),
            MagicMock(name="analyze_market"),
            MagicMock(name="assess_risks"),
            MagicMock(name="identify_opportunities"),
        ],
        metadata={
            "council": "prophecy",
            "aspect": "future_sight",
            "prediction_accuracy": 0.85,
        },
    )
    return MockAgent(config)
def create_sophia_demeter_agent() -> MockAgent:
    """Create a test Sophia Demeter (growth) agent"""
    config = TestAgentConfig(
        name="Demeter-Test",
        domain="sophia",
        personality="nurturing_cultivator",
        capabilities=[
            "business_growth",
            "resource_optimization",
            "sustainability_planning",
            "ecosystem_development",
        ],
        temperature=0.7,
        tools=[
            MagicMock(name="plan_growth"),
            MagicMock(name="optimize_resources"),
            MagicMock(name="ensure_sustainability"),
            MagicMock(name="develop_ecosystem"),
        ],
        metadata={
            "council": "growth",
            "aspect": "abundant_harvest",
            "growth_rate": 0.15,
        },
    )
    return MockAgent(config)
# Test Swarm Configurations
def create__test_swarm() -> List[MockAgent]:
    """Create a test  military swarm"""
    return [
        create__commander_agent(),
        create__scout_agent(),
        create__engineer_agent(),
        create__analyst_agent(),
    ]
def create_sophia_test_swarm() -> List[MockAgent]:
    """Create a test Sophia mythology swarm"""
    return [
        create_sophia_athena_agent(),
        create_sophia_hermes_agent(),
        create_sophia_apollo_agent(),
        create_sophia_demeter_agent(),
    ]
def create_mixed_test_swarm() -> List[MockAgent]:
    """Create a mixed domain test swarm (for cross-domain testing)"""
    return [
        create__commander_agent(),
        create__engineer_agent(),
        create_sophia_athena_agent(),
        create_sophia_hermes_agent(),
    ]
# Agent Factory Functions
def create_test_agent(
    name: str,
    domain: str,
    personality: str = "generic",
    capabilities: Optional[List[str]] = None,
    **kwargs,
) -> MockAgent:
    """
    Create a custom test agent
    Args:
        name: Agent name
        domain: Agent domain (/sophia)
        personality: Agent personality type
        capabilities: Agent capabilities
        **kwargs: Additional configuration
    Returns:
        Configured mock agent
    """
    config = TestAgentConfig(
        name=name,
        domain=domain,
        personality=personality,
        capabilities=capabilities or ["generic_capability"],
        **kwargs,
    )
    return MockAgent(config)
def create_test_agent_batch(
    count: int, domain: str, name_prefix: str = "TestAgent"
) -> List[MockAgent]:
    """
    Create a batch of test agents
    Args:
        count: Number of agents to create
        domain: Domain for all agents
        name_prefix: Prefix for agent names
    Returns:
        List of mock agents
    """
    agents = []
    for i in range(count):
        agent = create_test_agent(
            name=f"{name_prefix}-{i+1}",
            domain=domain,
            personality=f"personality_{i+1}",
            capabilities=[f"capability_{j}" for j in range(3)],
        )
        agents.append(agent)
    return agents
# Specialized Test Agents
def create_failing_agent() -> MockAgent:
    """Create an agent that always fails (for error testing)"""
    agent = create_test_agent(
        name="FailingAgent", domain="test", personality="error_prone"
    )
    # Override response generator to always fail
    agent.response_generator.side_effect = Exception("Simulated agent failure")
    return agent
def create_slow_agent(delay_seconds: float = 5.0) -> MockAgent:
    """Create an agent with slow responses (for timeout testing)"""
    import asyncio
    agent = create_test_agent(name="SlowAgent", domain="test", personality="deliberate")
    # Add delay to response
    async def slow_response(message):
        await asyncio.sleep(delay_seconds)
        return {"content": "Slow response", "role": "assistant", "agent": "SlowAgent"}
    agent.response_generator = slow_response
    return agent
def create_rate_limited_agent(max_requests: int = 5) -> MockAgent:
    """Create an agent with rate limiting (for rate limit testing)"""
    agent = create_test_agent(
        name="RateLimitedAgent", domain="test", personality="restricted"
    )
    request_count = 0
    async def rate_limited_response(message):
        nonlocal request_count
        request_count += 1
        if request_count > max_requests:
            raise Exception("Rate limit exceeded")
        return {
            "content": f"Response {request_count}/{max_requests}",
            "role": "assistant",
            "agent": "RateLimitedAgent",
        }
    agent.response_generator = rate_limited_response
    return agent
