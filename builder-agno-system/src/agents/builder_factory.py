"""
Builder Agno AI Agent Factory - Technical Code Generation System
This module provides a specialized factory for creating technical agents
focused on code generation, testing, deployment, and infrastructure.

CRITICAL DOMAIN SEPARATION:
- ALLOWED: Code generation, testing, deployment, infrastructure, technical docs
- FORBIDDEN: Business intelligence, client data, financial operations, sales

Key Features:
- Code generation agent templates (Generator, Reviewer, Refactorer)
- Testing and validation agents
- Infrastructure and deployment agents
- Multi-agent swarm coordination for complex technical tasks
- Integration with AGNO framework v2
- Strict technical domain enforcement
"""
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Try to import AGNO framework - fallback if not available
try:
    from agno import Agent, Team, Workflow
    from agno.models.portkey import Portkey as AGNOPortkey
    from agno.storage import PostgresDb, RedisDb
    from agno.memory import Knowledge
    AGNO_AVAILABLE = True
except ImportError:
    # Development fallback with strict warning
    import warnings
    warnings.warn("AGNO framework not available - using mock implementation for development only")
    
    class Agent:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "MockAgent")
            self.role = kwargs.get("role", "mock")
            self.instructions = kwargs.get("instructions", "")
            self._kwargs = kwargs
        
        def run(self, task):
            return f"Mock technical response for: {task}"
    
    class Team:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "MockTeam")
            self.members = kwargs.get("members", [])
        
        def run(self, task):
            return f"Mock team technical response for: {task}"
    
    class AGNOPortkey:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", "mock-model")
    
    AGNO_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BuilderAgentType(Enum):
    """Technical agent types for Builder domain"""
    CODE_GENERATOR = "code_generator"
    CODE_REVIEWER = "code_reviewer"
    TEST_WRITER = "test_writer"
    REFACTORER = "refactorer"
    DOCUMENTER = "documenter"
    DEPLOYER = "deployer"
    INFRASTRUCTURE = "infrastructure"
    SECURITY_SCANNER = "security_scanner"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"


@dataclass
class BuilderAgentConfig:
    """Configuration for Builder technical agents"""
    agent_type: BuilderAgentType
    name: str
    model: str = "anthropic/claude-3-sonnet-20240229"  # Default for code tasks
    temperature: float = 0.3  # Lower for code precision
    max_tokens: int = 4000
    instructions: Optional[str] = None
    tools: List[str] = None
    output_schema: Optional[Any] = None


class BuilderAgentFactory:
    """
    Factory for creating technical code generation agents.
    Strictly enforces technical domain boundaries.
    """
    
    # Domain enforcement
    ALLOWED_DOMAINS = [
        "code_generation", "testing", "deployment", 
        "infrastructure", "documentation", "security",
        "performance", "refactoring", "debugging"
    ]
    
    FORBIDDEN_DOMAINS = [
        "business_intelligence", "sales", "marketing",
        "client_data", "financial_operations", "crm"
    ]
    
    # Model preferences for technical tasks
    CODE_GENERATION_MODELS = [
        "anthropic/claude-3-sonnet-20240229",
        "openai/gpt-4-turbo-preview",
        "deepseek/deepseek-coder-33b"
    ]
    
    CODE_REVIEW_MODELS = [
        "anthropic/claude-3-opus-20240229",
        "openai/gpt-4",
        "google/gemini-pro"
    ]
    
    def __init__(self, db_url: Optional[str] = None):
        """Initialize Builder factory with optional database"""
        self.db_url = db_url or os.getenv("BUILDER_AGNO_DB_URL")
        self.agents: Dict[str, Agent] = {}
        self.teams: Dict[str, Team] = {}
        
        logger.info("Builder Agno AI Factory initialized - Technical operations only")
        
        if not AGNO_AVAILABLE:
            logger.warning("Running in mock mode - AGNO framework not available")
    
    def create_code_generator_agent(self, 
                                   language: str = "python",
                                   framework: Optional[str] = None) -> Agent:
        """Create an agent specialized in generating code"""
        
        instructions = f"""You are a senior {language} developer specialized in code generation.
        {"Framework: " + framework if framework else ""}
        
        Your responsibilities:
        1. Generate clean, efficient, and well-structured code
        2. Follow best practices and design patterns
        3. Include proper error handling
        4. Write self-documenting code with clear naming
        5. Consider performance and scalability
        
        CRITICAL: You handle ONLY technical code generation tasks.
        You do NOT handle business logic, client data, or financial operations.
        """
        
        agent = Agent(
            name=f"code_generator_{language}_{uuid4().hex[:8]}",
            role="Code Generator",
            model=self.CODE_GENERATION_MODELS[0],
            instructions=instructions,
            temperature=0.3,
            max_tokens=4000
        )
        
        self.agents[agent.name] = agent
        logger.info(f"Created code generator agent for {language}")
        return agent
    
    def create_code_reviewer_agent(self) -> Agent:
        """Create an agent specialized in code review"""
        
        instructions = """You are a senior software architect specialized in code review.
        
        Your responsibilities:
        1. Review code for correctness, efficiency, and maintainability
        2. Identify bugs, security vulnerabilities, and performance issues
        3. Suggest improvements and refactoring opportunities
        4. Ensure adherence to coding standards and best practices
        5. Provide constructive feedback with specific examples
        
        Focus areas:
        - Logic errors and edge cases
        - Security vulnerabilities (OWASP Top 10)
        - Performance bottlenecks
        - Code smells and anti-patterns
        - Test coverage gaps
        """
        
        agent = Agent(
            name=f"code_reviewer_{uuid4().hex[:8]}",
            role="Code Reviewer",
            model=self.CODE_REVIEW_MODELS[0],
            instructions=instructions,
            temperature=0.2,
            max_tokens=3000
        )
        
        self.agents[agent.name] = agent
        logger.info("Created code reviewer agent")
        return agent
    
    def create_test_writer_agent(self, test_framework: str = "pytest") -> Agent:
        """Create an agent specialized in writing tests"""
        
        instructions = f"""You are a QA engineer specialized in writing comprehensive tests.
        Test framework: {test_framework}
        
        Your responsibilities:
        1. Write unit tests with high coverage
        2. Create integration tests for system components
        3. Design edge case and boundary tests
        4. Implement performance and load tests
        5. Generate test data and fixtures
        
        Testing principles:
        - Arrange-Act-Assert pattern
        - Test isolation and independence
        - Clear test naming and documentation
        - Both positive and negative test cases
        - Mocking and stubbing where appropriate
        """
        
        agent = Agent(
            name=f"test_writer_{test_framework}_{uuid4().hex[:8]}",
            role="Test Writer",
            model=self.CODE_GENERATION_MODELS[0],
            instructions=instructions,
            temperature=0.3,
            max_tokens=3000
        )
        
        self.agents[agent.name] = agent
        logger.info(f"Created test writer agent for {test_framework}")
        return agent
    
    def create_refactoring_agent(self) -> Agent:
        """Create an agent specialized in code refactoring"""
        
        instructions = """You are a software engineer specialized in code refactoring.
        
        Your responsibilities:
        1. Identify and eliminate code duplication
        2. Improve code structure and organization
        3. Apply design patterns where appropriate
        4. Simplify complex logic
        5. Enhance code readability and maintainability
        
        Refactoring techniques:
        - Extract method/class
        - Rename for clarity
        - Remove dead code
        - Consolidate conditional expressions
        - Replace magic numbers with constants
        """
        
        agent = Agent(
            name=f"refactorer_{uuid4().hex[:8]}",
            role="Code Refactorer",
            model=self.CODE_GENERATION_MODELS[0],
            instructions=instructions,
            temperature=0.2,
            max_tokens=3000
        )
        
        self.agents[agent.name] = agent
        logger.info("Created refactoring agent")
        return agent
    
    def create_deployment_agent(self, platform: str = "kubernetes") -> Agent:
        """Create an agent specialized in deployment and DevOps"""
        
        instructions = f"""You are a DevOps engineer specialized in {platform} deployments.
        
        Your responsibilities:
        1. Create deployment configurations and manifests
        2. Set up CI/CD pipelines
        3. Configure monitoring and logging
        4. Implement security best practices
        5. Optimize resource allocation
        
        Platform: {platform}
        Focus on reliability, scalability, and security.
        """
        
        agent = Agent(
            name=f"deployer_{platform}_{uuid4().hex[:8]}",
            role="Deployment Specialist",
            model=self.CODE_GENERATION_MODELS[0],
            instructions=instructions,
            temperature=0.2,
            max_tokens=2000
        )
        
        self.agents[agent.name] = agent
        logger.info(f"Created deployment agent for {platform}")
        return agent
    
    def create_code_generation_team(self, project_type: str = "web_app") -> Team:
        """Create a coordinated team for complete code generation tasks"""
        
        # Create specialized agents for the team
        generator = self.create_code_generator_agent()
        reviewer = self.create_code_reviewer_agent()
        tester = self.create_test_writer_agent()
        
        team = Team(
            name=f"code_generation_team_{project_type}_{uuid4().hex[:8]}",
            members=[generator, reviewer, tester],
            description=f"Complete code generation team for {project_type} development"
        )
        
        self.teams[team.name] = team
        logger.info(f"Created code generation team for {project_type}")
        return team
    
    def create_refactoring_team(self) -> Team:
        """Create a team specialized in code refactoring and optimization"""
        
        refactorer = self.create_refactoring_agent()
        reviewer = self.create_code_reviewer_agent()
        tester = self.create_test_writer_agent()
        
        team = Team(
            name=f"refactoring_team_{uuid4().hex[:8]}",
            members=[refactorer, reviewer, tester],
            description="Code refactoring and optimization team"
        )
        
        self.teams[team.name] = team
        logger.info("Created refactoring team")
        return team
    
    def validate_domain(self, task: str) -> bool:
        """Validate that a task is within technical domain"""
        
        task_lower = task.lower()
        
        # Check for forbidden domains
        for forbidden in self.FORBIDDEN_DOMAINS:
            if forbidden in task_lower:
                logger.warning(f"Task rejected - forbidden domain: {forbidden}")
                raise ValueError(f"Task involves forbidden domain: {forbidden}")
        
        # Check for allowed domains
        for allowed in self.ALLOWED_DOMAINS:
            if allowed in task_lower:
                return True
        
        # Default allow for unspecified technical tasks
        logger.info("Task validated for technical domain")
        return True
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents and teams"""
        
        return {
            "factory": "BuilderAgentFactory",
            "domain": "technical_operations",
            "agno_available": AGNO_AVAILABLE,
            "active_agents": len(self.agents),
            "active_teams": len(self.teams),
            "agents": list(self.agents.keys()),
            "teams": list(self.teams.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    def cleanup(self):
        """Clean up resources"""
        
        self.agents.clear()
        self.teams.clear()
        logger.info("Builder factory cleaned up")


# Factory singleton instance
_builder_factory_instance: Optional[BuilderAgentFactory] = None


def get_builder_factory() -> BuilderAgentFactory:
    """Get or create the Builder factory singleton"""
    global _builder_factory_instance
    
    if _builder_factory_instance is None:
        _builder_factory_instance = BuilderAgentFactory()
    
    return _builder_factory_instance


# Example usage
if __name__ == "__main__":
    # Initialize factory
    factory = get_builder_factory()
    
    # Create individual agents
    code_gen = factory.create_code_generator_agent(language="python", framework="FastAPI")
    reviewer = factory.create_code_reviewer_agent()
    tester = factory.create_test_writer_agent(test_framework="pytest")
    
    # Create a team
    dev_team = factory.create_code_generation_team(project_type="api_service")
    
    # Get status
    status = factory.get_agent_status()
    print(f"Builder Factory Status: {status}")
    
    # Validate domain
    try:
        factory.validate_domain("Generate code for user authentication")  # OK
        factory.validate_domain("Analyze sales data")  # Would raise error
    except ValueError as e:
        print(f"Domain validation error: {e}")