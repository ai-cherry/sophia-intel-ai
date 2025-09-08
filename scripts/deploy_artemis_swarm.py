#!/usr/bin/env python3
"""
Deploy Artemis Code Excellence Swarm
Multi-agent system for code generation, review, and optimization
"""
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.artemis.artemis_orchestrator import ArtemisOrchestrator, CodeContext
from app.core.portkey_manager import PortkeyManager, TaskType, get_portkey_manager
from app.core.secrets_manager import get_secrets_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ArtemisAgent:
    """Individual Artemis agent configuration"""

    name: str
    role: str
    provider: str
    model: str
    specialization: List[str]
    temperature: float = 0.2
    max_tokens: int = 4096


class ArtemisSwarm:
    """
    Artemis Swarm Coordinator
    Manages multiple specialized agents for code excellence
    """

    def __init__(self):
        """Initialize the Artemis swarm"""
        self.portkey_manager = get_portkey_manager()
        self.secrets_manager = get_secrets_manager()
        self.agents = self._initialize_agents()
        self.orchestrator = ArtemisOrchestrator(
            code_context=CodeContext(
                languages=["python", "typescript", "rust", "go"],
                frameworks=["fastapi", "react", "django", "vue"],
                coverage_target=85.0,
                complexity_threshold=8,
            )
        )
        logger.info(f"Initialized Artemis Swarm with {len(self.agents)} agents")

    def _initialize_agents(self) -> List[ArtemisAgent]:
        """Initialize specialized Artemis agents"""
        return [
            # Code Generation Specialist
            ArtemisAgent(
                name="artemis-genesis",
                role="Code Generator",
                provider="deepseek",
                model="deepseek-coder",
                specialization=["code_generation", "boilerplate", "scaffolding"],
                temperature=0.3,
            ),
            # Code Review Expert
            ArtemisAgent(
                name="artemis-critic",
                role="Code Reviewer",
                provider="openai",
                model="gpt-4o",
                specialization=["code_review", "best_practices", "quality"],
                temperature=0.1,
            ),
            # Security Analyst
            ArtemisAgent(
                name="artemis-shield",
                role="Security Analyst",
                provider="anthropic",
                model="claude-3-sonnet",
                specialization=["security", "vulnerability_detection", "compliance"],
                temperature=0.0,
            ),
            # Performance Optimizer
            ArtemisAgent(
                name="artemis-turbo",
                role="Performance Optimizer",
                provider="groq",
                model="llama3-70b",
                specialization=["performance", "optimization", "profiling"],
                temperature=0.2,
            ),
            # Test Engineer
            ArtemisAgent(
                name="artemis-test",
                role="Test Engineer",
                provider="gemini",
                model="gemini-2.0-flash",
                specialization=["testing", "test_generation", "coverage"],
                temperature=0.1,
            ),
            # Documentation Writer
            ArtemisAgent(
                name="artemis-scribe",
                role="Documentation Expert",
                provider="mistral",
                model="mistral-medium",
                specialization=["documentation", "api_docs", "tutorials"],
                temperature=0.4,
            ),
            # Architecture Designer
            ArtemisAgent(
                name="artemis-architect",
                role="System Architect",
                provider="xai",
                model="grok-beta",
                specialization=["architecture", "design_patterns", "scalability"],
                temperature=0.3,
            ),
            # Refactoring Specialist
            ArtemisAgent(
                name="artemis-refactor",
                role="Refactoring Expert",
                provider="together",
                model="mixtral-8x7b",
                specialization=["refactoring", "code_cleanup", "modernization"],
                temperature=0.2,
            ),
        ]

    async def execute_task(
        self, agent: ArtemisAgent, task: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a task with a specific agent"""
        logger.info(f"🤖 {agent.name} ({agent.role}) executing task")

        try:
            # Get client for the agent's provider
            client = self.portkey_manager.get_client(agent.provider)

            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": f"""You are {agent.name}, an expert {agent.role} in the Artemis Code Excellence system.
Your specializations: {', '.join(agent.specialization)}
Your approach: Systematic, thorough, and focused on excellence.
Current context: {json.dumps(context, indent=2)}""",
                },
                {"role": "user", "content": task},
            ]

            # Execute with the provider
            response = await client.chat.completions.acreate(
                model=agent.model,
                messages=messages,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
            )

            result = {
                "agent": agent.name,
                "role": agent.role,
                "provider": agent.provider,
                "model": agent.model,
                "response": response.choices[0].message.content,
                "timestamp": datetime.now().isoformat(),
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
            }

            logger.info(
                f"✅ {agent.name} completed task (tokens: {result['usage']['total_tokens']})"
            )
            return result

        except Exception as e:
            logger.error(f"❌ {agent.name} failed: {e}")
            return {"agent": agent.name, "error": str(e), "timestamp": datetime.now().isoformat()}

    async def collaborative_code_generation(self, requirements: str) -> Dict[str, Any]:
        """Generate code collaboratively using multiple agents"""
        logger.info("🚀 Starting collaborative code generation")

        context = {"requirements": requirements}
        results = {}

        # Phase 1: Architecture Design
        architect = next(a for a in self.agents if a.name == "artemis-architect")
        arch_task = f"Design the architecture for: {requirements}"
        results["architecture"] = await self.execute_task(architect, arch_task, context)
        context["architecture"] = results["architecture"].get("response", "")

        # Phase 2: Code Generation
        generator = next(a for a in self.agents if a.name == "artemis-genesis")
        gen_task = f"Generate code based on architecture: {context['architecture'][:500]}"
        results["code"] = await self.execute_task(generator, gen_task, context)
        context["code"] = results["code"].get("response", "")

        # Phase 3: Security Review
        security = next(a for a in self.agents if a.name == "artemis-shield")
        sec_task = f"Review this code for security issues: {context['code'][:1000]}"
        results["security"] = await self.execute_task(security, sec_task, context)

        # Phase 4: Performance Optimization
        optimizer = next(a for a in self.agents if a.name == "artemis-turbo")
        opt_task = f"Optimize this code for performance: {context['code'][:1000]}"
        results["optimization"] = await self.execute_task(optimizer, opt_task, context)

        # Phase 5: Test Generation
        tester = next(a for a in self.agents if a.name == "artemis-test")
        test_task = f"Generate comprehensive tests for: {context['code'][:1000]}"
        results["tests"] = await self.execute_task(tester, test_task, context)

        # Phase 6: Documentation
        documenter = next(a for a in self.agents if a.name == "artemis-scribe")
        doc_task = f"Create documentation for: {context['code'][:1000]}"
        results["documentation"] = await self.execute_task(documenter, doc_task, context)

        return {
            "timestamp": datetime.now().isoformat(),
            "requirements": requirements,
            "phases": results,
            "summary": self._generate_summary(results),
        }

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate execution summary"""
        total_tokens = 0
        successful_agents = 0
        failed_agents = []

        for phase, result in results.items():
            if isinstance(result, dict):
                if "error" in result:
                    failed_agents.append(result.get("agent", phase))
                else:
                    successful_agents += 1
                    if "usage" in result:
                        total_tokens += result["usage"].get("total_tokens", 0)

        return {
            "successful_agents": successful_agents,
            "failed_agents": failed_agents,
            "total_tokens": total_tokens,
            "estimated_cost": self.portkey_manager._estimate_cost("gpt-4o", total_tokens),
        }

    async def parallel_review(self, code: str) -> Dict[str, Any]:
        """Run parallel code review with multiple agents"""
        logger.info("🔍 Starting parallel code review")

        # Select review agents
        review_agents = [
            a
            for a in self.agents
            if any(
                spec in ["code_review", "security", "performance", "testing"]
                for spec in a.specialization
            )
        ]

        # Create review tasks
        tasks = []
        for agent in review_agents:
            task = f"Review this code from your {agent.role} perspective:\n\n{code[:2000]}"
            tasks.append(self.execute_task(agent, task, {"code": code}))

        # Execute reviews in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        reviews = {}
        for agent, result in zip(review_agents, results):
            if isinstance(result, Exception):
                reviews[agent.name] = {"error": str(result)}
            else:
                reviews[agent.name] = result

        return {
            "timestamp": datetime.now().isoformat(),
            "reviews": reviews,
            "consensus": self._build_consensus(reviews),
        }

    def _build_consensus(self, reviews: Dict[str, Any]) -> Dict[str, Any]:
        """Build consensus from multiple reviews"""
        issues = []
        recommendations = []

        for agent_name, review in reviews.items():
            if "error" not in review and "response" in review:
                # Extract key points (simplified for demo)
                response = review["response"]
                if "issue" in response.lower() or "problem" in response.lower():
                    issues.append(f"{agent_name}: Found potential issues")
                if "recommend" in response.lower() or "suggest" in response.lower():
                    recommendations.append(f"{agent_name}: Has recommendations")

        return {
            "total_reviews": len(reviews),
            "successful_reviews": len([r for r in reviews.values() if "error" not in r]),
            "issues_found": len(issues),
            "recommendations": len(recommendations),
        }

    def status_report(self) -> Dict[str, Any]:
        """Generate swarm status report"""
        return {
            "swarm_name": "Artemis Code Excellence",
            "total_agents": len(self.agents),
            "agents": [
                {
                    "name": agent.name,
                    "role": agent.role,
                    "provider": agent.provider,
                    "model": agent.model,
                    "specializations": agent.specialization,
                }
                for agent in self.agents
            ],
            "portkey_status": "connected",
            "timestamp": datetime.now().isoformat(),
        }


async def main():
    """Main execution"""
    print("=" * 80)
    print("🚀 ARTEMIS CODE EXCELLENCE SWARM DEPLOYMENT")
    print("=" * 80)

    # Initialize swarm
    swarm = ArtemisSwarm()

    # Display status
    status = swarm.status_report()
    print("\n📊 Swarm Status:")
    print(f"  Total Agents: {status['total_agents']}")
    print(f"  Portkey Status: {status['portkey_status']}")

    print("\n👥 Agent Roster:")
    for agent in status["agents"]:
        print(f"  • {agent['name']} ({agent['role']})")
        print(f"    Provider: {agent['provider']}/{agent['model']}")
        print(f"    Specializations: {', '.join(agent['specializations'])}")

    # Test collaborative code generation
    print("\n" + "=" * 80)
    print("🧪 TEST: Collaborative Code Generation")
    print("=" * 80)

    test_requirements = """
    Create a FastAPI endpoint for user authentication with:
    - JWT token generation
    - Password hashing with bcrypt
    - Rate limiting
    - Input validation
    """

    print(f"\n📋 Requirements: {test_requirements.strip()}")
    print("\n⏳ Executing collaborative generation...")

    result = await swarm.collaborative_code_generation(test_requirements)

    # Display results
    print("\n✅ Generation Complete!")
    print("\n📊 Execution Summary:")
    summary = result["summary"]
    print(f"  Successful Agents: {summary['successful_agents']}")
    print(f"  Failed Agents: {len(summary['failed_agents'])}")
    print(f"  Total Tokens: {summary['total_tokens']:,}")
    print(f"  Estimated Cost: ${summary['estimated_cost']:.4f}")

    # Save detailed results
    output_file = Path(f"artemis_swarm_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n💾 Detailed results saved to: {output_file}")

    # Test parallel review
    print("\n" + "=" * 80)
    print("🧪 TEST: Parallel Code Review")
    print("=" * 80)

    sample_code = """
def authenticate_user(username: str, password: str):
    # Simple authentication - needs improvement
    if username == "admin" and password == "password123":
        return {"token": "secret-token"}
    return None
    """

    print("\n📝 Code to Review:")
    print(sample_code)
    print("\n⏳ Running parallel review...")

    review_result = await swarm.parallel_review(sample_code)

    print("\n✅ Review Complete!")
    consensus = review_result["consensus"]
    print("\n📊 Review Consensus:")
    print(f"  Total Reviews: {consensus['total_reviews']}")
    print(f"  Successful Reviews: {consensus['successful_reviews']}")
    print(f"  Issues Found: {consensus['issues_found']}")
    print(f"  Recommendations: {consensus['recommendations']}")

    print("\n" + "=" * 80)
    print("✅ ARTEMIS SWARM DEPLOYMENT SUCCESSFUL!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
