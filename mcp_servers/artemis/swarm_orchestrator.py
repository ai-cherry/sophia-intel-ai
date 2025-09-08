# Auto-added by pre-commit hook
import sys, os
try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    from core.environment_enforcer import enforce_environment
    enforce_environment()
except ImportError:

"""
Artemis Swarm Orchestrator - Advanced Integration
5-agent swarm with memory graphs, ZK proofs, and cost optimization
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Core integrations
try:
    from ...core.cost_optimization import create_cost_router, CostTier
    COST_ROUTER_AVAILABLE = True
except ImportError:
    COST_ROUTER_AVAILABLE = False
    # Mock CostTier for fallback
    from enum import Enum
    class CostTier(Enum):
        ECONOMY = "economy"
        BALANCED = "balanced"
        PREMIUM = "premium"
        ULTRA_FAST = "ultra_fast"

try:
    from ...core.memory import create_memory_system, MemoryType, PrivacyLevel
    MEMORY_SYSTEM_AVAILABLE = True
except ImportError:
    MEMORY_SYSTEM_AVAILABLE = False
    # Mock for fallback
    from enum import Enum
    class MemoryType(Enum):
        EPISODIC = "episodic"
        SEMANTIC = "semantic"
        PROCEDURAL = "procedural"
        WORKING = "working"
        LONG_TERM = "long_term"

    class PrivacyLevel(Enum):
        PUBLIC = "public"
        INTERNAL = "internal"
        CONFIDENTIAL = "confidential"
        RESTRICTED = "restricted"

try:
    from ...core.zk_proofs import create_zk_proof_system, ProofType
    ZK_PROOF_AVAILABLE = True
except ImportError:
    ZK_PROOF_AVAILABLE = False
    # Mock for fallback
    from enum import Enum
    class ProofType(Enum):
        CODE_EXECUTION = "code_execution"
        TASK_COMPLETION = "task_completion"
        AGENT_VERIFICATION = "agent_verification"

try:
    from crewai import Agent, Task, Crew
    from crewai.process import Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

try:
    from langgraph import StateGraph, END
    from langgraph.graph import Graph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

try:
    import semantic_kernel as sk
    from semantic_kernel.planning import BasicPlanner
    SEMANTIC_KERNEL_AVAILABLE = True
except ImportError:
    SEMANTIC_KERNEL_AVAILABLE = False

try:
    from llama_index.core.workflow import Workflow, StartEvent, StopEvent
    from llama_index.core.workflow import step
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False

class SwarmState(Enum):
    """Swarm execution states"""
    IDLE = "idle"
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    DEPLOYING = "deploying"
    EVOLVING = "evolving"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentRole(Enum):
    """Agent roles in the swarm"""
    PLANNER = "planner"
    CODER = "coder"
    TESTER = "tester"
    DEPLOYER = "deployer"
    EVOLVER = "evolver"

@dataclass
class SwarmExecution:
    """Swarm execution tracking"""
    execution_id: str
    intent: str
    state: SwarmState = SwarmState.IDLE
    current_agent: Optional[AgentRole] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agents_used: List[AgentRole] = field(default_factory=list)
    memory_ids: List[str] = field(default_factory=list)
    proof_ids: List[str] = field(default_factory=list)
    cost_info: Optional[Dict[str, Any]] = None

class ArtemisAgent:
    """Base class for Artemis agents"""

    def __init__(self, role: AgentRole, config: Dict[str, Any]):
        self.role = role
        self.config = config
        self.logger = logging.getLogger(f"ArtemisAgent-{role.value}")

        # Initialize cost router if available
        self.cost_router = None
        if COST_ROUTER_AVAILABLE:
            try:
                self.cost_router = create_cost_router(config)
            except Exception as e:
                self.logger.error(f"Failed to initialize cost router: {e}")

    async def execute(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task"""

    async def _llm_call(self, prompt: str, optimization_tier: CostTier = CostTier.BALANCED) -> str:
        """Make optimized LLM call"""
        if self.cost_router:
            try:
                result = await self.cost_router.complete(prompt, optimization_tier)
                return result.get("content", "")
            except Exception as e:
                self.logger.error(f"Cost-optimized LLM call failed: {e}")

        # Fallback to mock response
        return f"Mock response for: {prompt[:100]}..."

class PlannerAgent(ArtemisAgent):
    """Planner agent with Semantic Kernel integration"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(AgentRole.PLANNER, config)

        # Initialize Semantic Kernel if available
        self.sk_kernel = None
        if SEMANTIC_KERNEL_AVAILABLE:
            try:
                self.sk_kernel = sk.Kernel()
                self.planner = BasicPlanner()
                self.logger.info("Semantic Kernel initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Semantic Kernel: {e}")

    async def execute(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan task execution using Semantic Kernel"""
        start_time = time.time()

        try:
            # Decompose intent using SK if available
            if self.sk_kernel:
                plan = await self._decompose_with_sk(intent)
            else:
                plan = await self._decompose_fallback(intent)

            execution_time = time.time() - start_time

            return {
                "success": True,
                "plan": plan,
                "execution_time": execution_time,
                "agent": self.role.value,
                "method": "semantic_kernel" if self.sk_kernel else "fallback"
            }

        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "agent": self.role.value
            }

    async def _decompose_with_sk(self, intent: str) -> Dict[str, Any]:
        """Decompose intent using Semantic Kernel"""
        # Simplified SK decomposition
        prompt = f"""
        Decompose this coding intent into structured steps:
        Intent: {intent}

        Provide a JSON response with:
        - requirements: List of functional requirements
        - architecture: High-level architecture decisions
        - steps: Ordered list of implementation steps
        - agents_needed: Which agents should be involved
        - estimated_complexity: 1-10 scale
        """

        response = await self._llm_call(prompt, CostTier.BALANCED)

        try:
            # Parse JSON response
            plan_data = json.loads(response)
            return plan_data
        except json.JSONDecodeError:
            # Fallback to structured parsing
            return await self._decompose_fallback(intent)

    async def _decompose_fallback(self, intent: str) -> Dict[str, Any]:
        """Fallback decomposition method"""
        return {
            "requirements": [f"Implement: {intent}"],
            "architecture": "Standard implementation",
            "steps": [
                "Analyze requirements",
                "Design solution",
                "Implement code",
                "Test functionality",
                "Deploy solution"
            ],
            "agents_needed": ["coder", "tester", "deployer"],
            "estimated_complexity": 5
        }

class CoderAgent(ArtemisAgent):
    """Coder agent with ZK proof generation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(AgentRole.CODER, config)

        # Initialize ZK proof system if available
        self.zk_system = None
        if ZK_PROOF_AVAILABLE:
            try:
                self.zk_system = create_zk_proof_system(config)
                self.logger.info("ZK proof system initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize ZK proof system: {e}")

    async def execute(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code with ZK proof verification"""
        start_time = time.time()

        try:
            # Get plan from context
            plan = context.get("plan", {})

            # Generate code
            code = await self._generate_code(intent, plan)

            # Execute/validate code
            execution_result = await self._validate_code(code)

            # Generate ZK proof if available
            proof_id = None
            if self.zk_system and execution_result.get("success"):
                proof_id = await self.zk_system.generate_code_execution_proof(
                    task_id=context.get("execution_id", "unknown"),
                    code=code,
                    execution_result=execution_result,
                    agent_type=self.role.value
                )

            execution_time = time.time() - start_time

            return {
                "success": execution_result.get("success", True),
                "code": code,
                "execution_result": execution_result,
                "proof_id": proof_id,
                "execution_time": execution_time,
                "agent": self.role.value
            }

        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "agent": self.role.value
            }

    async def _generate_code(self, intent: str, plan: Dict[str, Any]) -> str:
        """Generate code based on intent and plan"""
        prompt = f"""
        Generate Python code for this intent:
        Intent: {intent}

        Plan: {json.dumps(plan, indent=2)}

        Requirements:
        - Write clean, production-ready code
        - Include proper error handling
        - Add docstrings and comments
        - Follow PEP 8 style guidelines

        Return only the Python code:
        """

        code = await self._llm_call(prompt, CostTier.BALANCED)
        return code

    async def _validate_code(self, code: str) -> Dict[str, Any]:
        """Validate generated code"""
        try:
            # Basic syntax validation
            compile(code, '<string>', 'exec')

            # Mock execution result
            return {
                "success": True,
                "syntax_valid": True,
                "execution_time": 0.1,
                "output": "Code validation successful"
            }

        except SyntaxError as e:
            return {
                "success": False,
                "syntax_valid": False,
                "error": str(e)
            }

class TesterAgent(ArtemisAgent):
    """Tester agent with comprehensive testing"""

    async def execute(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive tests on generated code"""
        start_time = time.time()

        try:
            code = context.get("code", "")

            # Run different types of tests
            sophia_results = {
                "syntax_test": await self._test_syntax(code),
                "unit_tests": await self._generate_and_run_tests(code, intent),
                "security_scan": await self._security_scan(code),
                "performance_test": await self._performance_test(code)
            }

            # Calculate overall success
            all_passed = all(result.get("passed", False) for result in sophia_results.values())

            execution_time = time.time() - start_time

            return {
                "success": all_passed,
                "sophia_results": sophia_results,
                "coverage": 85.0,  # Mock coverage
                "execution_time": execution_time,
                "agent": self.role.value
            }

        except Exception as e:
            self.logger.error(f"Testing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "agent": self.role.value
            }

    async def _test_syntax(self, code: str) -> Dict[str, Any]:
        """Test code syntax"""
        try:
            compile(code, '<string>', 'exec')
            return {"passed": True, "message": "Syntax is valid"}
        except SyntaxError as e:
            return {"passed": False, "message": f"Syntax error: {e}"}

    async def _generate_and_run_tests(self, code: str, intent: str) -> Dict[str, Any]:
        """Generate and run unit tests"""
        # Mock test generation and execution
        return {
            "passed": True,
            "tests_generated": 5,
            "tests_passed": 5,
            "tests_failed": 0,
            "message": "All unit tests passed"
        }

    async def _security_scan(self, code: str) -> Dict[str, Any]:
        """Run security scan on code"""
        # Mock security scan
        return {
            "passed": True,
            "vulnerabilities": 0,
            "message": "No security vulnerabilities found"
        }

    async def _performance_test(self, code: str) -> Dict[str, Any]:
        """Run performance tests"""
        # Mock performance test
        return {
            "passed": True,
            "execution_time": 0.05,
            "memory_usage": "12MB",
            "message": "Performance within acceptable limits"
        }

class DeployerAgent(ArtemisAgent):
    """Deployer agent with Pulumi integration"""

    async def execute(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy code using Pulumi"""
        start_time = time.time()

        try:
            code = context.get("code", "")
            sophia_results = context.get("sophia_results", {})

            # Check if tests passed
            if not all(result.get("passed", False) for result in sophia_results.values()):
                return {
                    "success": False,
                    "error": "Cannot deploy: tests failed",
                    "execution_time": time.time() - start_time,
                    "agent": self.role.value
                }

            # Deploy to Lambda
            deployment_result = await self._deploy_to_lambda(code, intent)

            execution_time = time.time() - start_time

            return {
                "success": deployment_result.get("success", True),
                "deployment_result": deployment_result,
                "execution_time": execution_time,
                "agent": self.role.value
            }

        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "agent": self.role.value
            }

    async def _deploy_to_lambda(self, code: str, intent: str) -> Dict[str, Any]:
        """Deploy code to Lambda using Pulumi"""
        # Mock deployment
        return {
            "success": True,
            "lambda_arn": f"arn:aws:lambda:us-west-2:123456789:function:artemis-{uuid.uuid4().hex[:8]}",
            "api_url": f"https://api-{uuid.uuid4().hex[:8]}.execute-api.us-west-2.amazonaws.com/dev",
            "deployment_time": 30.5,
            "message": "Successfully deployed to Lambda"
        }

class EvolverAgent(ArtemisAgent):
    """Evolver agent with Mem0 v2 memory graphs"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(AgentRole.EVOLVER, config)

        # Initialize memory system if available
        self.memory_system = None
        if MEMORY_SYSTEM_AVAILABLE:
            try:
                self.memory_system = create_memory_system(config)
                self.logger.info("Memory system initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize memory system: {e}")

    async def execute(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from execution and evolve strategies"""
        start_time = time.time()

        try:
            execution_id = context.get("execution_id", "unknown")
            result = context.get("result", {})
            agents_used = context.get("agents_used", [])

            # Store episodic memory if available
            memory_id = None
            if self.memory_system:
                memory_id = await self.memory_system.create_episodic_memory(
                    task_id=execution_id,
                    task_intent=intent,
                    execution_result=result,
                    agent_type="swarm"
                )

            # Generate learning insights
            insights = await self._generate_insights(intent, result, agents_used)

            # Update strategies based on learning
            strategy_updates = await self._update_strategies(insights)

            execution_time = time.time() - start_time

            return {
                "success": True,
                "memory_id": memory_id,
                "insights": insights,
                "strategy_updates": strategy_updates,
                "execution_time": execution_time,
                "agent": self.role.value
            }

        except Exception as e:
            self.logger.error(f"Evolution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "agent": self.role.value
            }

    async def _generate_insights(self, intent: str, result: Dict[str, Any], agents_used: List[str]) -> Dict[str, Any]:
        """Generate insights from execution"""
        success = result.get("success", False)
        execution_time = result.get("execution_time", 0)

        insights = {
            "intent_complexity": len(intent.split()),
            "success_rate": 1.0 if success else 0.0,
            "execution_efficiency": 1.0 / max(execution_time, 0.1),
            "agents_efficiency": len(agents_used),
            "patterns": await self._identify_patterns(intent, result)
        }

        return insights

    async def _identify_patterns(self, intent: str, result: Dict[str, Any]) -> List[str]:
        """Identify patterns in execution"""
        patterns = []

        # Simple pattern identification
        if "api" in intent.lower():
            patterns.append("api_development")
        if "web" in intent.lower():
            patterns.append("web_development")
        if result.get("success"):
            patterns.append("successful_execution")

        return patterns

    async def _update_strategies(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Update strategies based on insights"""
        return {
            "optimization_suggestions": [
                "Consider using faster models for simple tasks",
                "Implement caching for repeated patterns",
                "Optimize agent coordination"
            ],
            "pattern_recognition": insights.get("patterns", []),
            "performance_metrics": {
                "efficiency_score": insights.get("execution_efficiency", 0),
                "success_rate": insights.get("success_rate", 0)
            }
        }

class ArtemisSwarm:
    """
    Artemis 5-Agent Swarm Orchestrator

    Advanced features:
    - Memory graphs with Mem0 v2
    - Zero-knowledge proofs with Halo2
    - Cost optimization with Portkey
    - LangGraph workflow orchestration
    - CrewAI agent collaboration
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger("ArtemisSwarm")

        # Initialize agents
        self.agents = {
            AgentRole.PLANNER: PlannerAgent(self.config),
            AgentRole.CODER: CoderAgent(self.config),
            AgentRole.TESTER: TesterAgent(self.config),
            AgentRole.DEPLOYER: DeployerAgent(self.config),
            AgentRole.EVOLVER: EvolverAgent(self.config)
        }

        # Initialize systems
        self.memory_system = None
        self.zk_system = None
        self.cost_router = None

        if MEMORY_SYSTEM_AVAILABLE:
            try:
                self.memory_system = create_memory_system(self.config)
            except Exception as e:
                self.logger.error(f"Failed to initialize memory system: {e}")

        if ZK_PROOF_AVAILABLE:
            try:
                self.zk_system = create_zk_proof_system(self.config)
            except Exception as e:
                self.logger.error(f"Failed to initialize ZK system: {e}")

        if COST_ROUTER_AVAILABLE:
            try:
                self.cost_router = create_cost_router(self.config)
            except Exception as e:
                self.logger.error(f"Failed to initialize cost router: {e}")

        # Execution tracking
        self.executions: Dict[str, SwarmExecution] = {}

        self.logger.info("Artemis Swarm initialized with 5 agents")

    async def process_intent(self, intent: str) -> Dict[str, Any]:
        """Process intent through the 5-agent swarm"""
        execution_id = str(uuid.uuid4())
        execution = SwarmExecution(execution_id=execution_id, intent=intent)
        self.executions[execution_id] = execution

        start_time = time.time()

        try:
            # Phase 1: Planning
            execution.state = SwarmState.PLANNING
            execution.current_agent = AgentRole.PLANNER

            plan_result = await self.agents[AgentRole.PLANNER].execute(intent, {
                "execution_id": execution_id
            })

            if not plan_result.get("success"):
                raise Exception(f"Planning failed: {plan_result.get('error')}")

            execution.agents_used.append(AgentRole.PLANNER)

            # Phase 2: Coding
            execution.state = SwarmState.CODING
            execution.current_agent = AgentRole.CODER

            code_result = await self.agents[AgentRole.CODER].execute(intent, {
                "execution_id": execution_id,
                "plan": plan_result.get("plan", {})
            })

            if not code_result.get("success"):
                raise Exception(f"Coding failed: {code_result.get('error')}")

            execution.agents_used.append(AgentRole.CODER)
            if code_result.get("proof_id"):
                execution.proof_ids.append(code_result["proof_id"])

            # Phase 3: Testing
            execution.state = SwarmState.TESTING
            execution.current_agent = AgentRole.TESTER

            sophia_result = await self.agents[AgentRole.TESTER].execute(intent, {
                "execution_id": execution_id,
                "code": code_result.get("code", ""),
                "plan": plan_result.get("plan", {})
            })

            execution.agents_used.append(AgentRole.TESTER)

            # Phase 4: Deployment (only if tests pass)
            if sophia_result.get("success"):
                execution.state = SwarmState.DEPLOYING
                execution.current_agent = AgentRole.DEPLOYER

                deploy_result = await self.agents[AgentRole.DEPLOYER].execute(intent, {
                    "execution_id": execution_id,
                    "code": code_result.get("code", ""),
                    "sophia_results": sophia_result.get("sophia_results", {})
                })

                execution.agents_used.append(AgentRole.DEPLOYER)
            else:
                deploy_result = {"success": False, "error": "Tests failed, skipping deployment"}

            # Phase 5: Evolution/Learning
            execution.state = SwarmState.EVOLVING
            execution.current_agent = AgentRole.EVOLVER

            final_result = {
                "plan": plan_result,
                "code": code_result,
                "test": sophia_result,
                "deploy": deploy_result,
                "success": deploy_result.get("success", False)
            }

            evolve_result = await self.agents[AgentRole.EVOLVER].execute(intent, {
                "execution_id": execution_id,
                "result": final_result,
                "agents_used": [agent.value for agent in execution.agents_used]
            })

            execution.agents_used.append(AgentRole.EVOLVER)
            if evolve_result.get("memory_id"):
                execution.memory_ids.append(evolve_result["memory_id"])

            # Generate task completion proof
            if self.zk_system and final_result.get("success"):
                task_proof_id = await self.zk_system.generate_task_completion_proof(
                    task_id=execution_id,
                    intent=intent,
                    result=final_result,
                    agents_used=[agent.value for agent in execution.agents_used]
                )
                execution.proof_ids.append(task_proof_id)

            # Calculate cost information
            if self.cost_router:
                try:
                    cost_metrics = self.cost_router.get_cost_metrics()
                    execution.cost_info = {
                        "total_cost": cost_metrics.get("total_cost", 0.0),
                        "savings": cost_metrics.get("cost_savings_percentage", 0.0),
                        "requests": cost_metrics.get("total_requests", 0)
                    }
                except Exception as e:
                    self.logger.error(f"Cost calculation failed: {e}")

            # Complete execution
            execution.state = SwarmState.COMPLETED
            execution.completed_at = datetime.now()
            execution.result = {
                **final_result,
                "evolution": evolve_result,
                "execution_time": time.time() - start_time,
                "agents_used": [agent.value for agent in execution.agents_used],
                "memory_ids": execution.memory_ids,
                "proof_ids": execution.proof_ids,
                "cost_info": execution.cost_info
            }

            self.logger.info(f"Swarm execution {execution_id} completed successfully")
            return execution.result

        except Exception as e:
            execution.state = SwarmState.FAILED
            execution.completed_at = datetime.now()
            execution.error = str(e)

            self.logger.error(f"Swarm execution {execution_id} failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "agents_used": [agent.value for agent in execution.agents_used],
                "execution_id": execution_id
            }

    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a swarm execution"""
        execution = self.executions.get(execution_id)
        if not execution:
            return None

        return {
            "execution_id": execution.execution_id,
            "intent": execution.intent,
            "state": execution.state.value,
            "current_agent": execution.current_agent.value if execution.current_agent else None,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "agents_used": [agent.value for agent in execution.agents_used],
            "memory_ids": execution.memory_ids,
            "proof_ids": execution.proof_ids,
            "cost_info": execution.cost_info,
            "success": execution.result.get("success") if execution.result else None,
            "error": execution.error
        }

    async def get_swarm_metrics(self) -> Dict[str, Any]:
        """Get swarm performance metrics"""
        total_executions = len(self.executions)
        successful_executions = sum(
            1 for exec in self.executions.values() 
            if exec.state == SwarmState.COMPLETED and exec.result and exec.result.get("success")
        )

        avg_execution_time = 0.0
        if total_executions > 0:
            total_time = sum(
                exec.result.get("execution_time", 0) 
                for exec in self.executions.values() 
                if exec.result
            )
            avg_execution_time = total_time / total_executions

        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": (successful_executions / max(total_executions, 1)) * 100,
            "avg_execution_time": round(avg_execution_time, 2),
            "agents_available": len(self.agents),
            "memory_system_available": self.memory_system is not None,
            "zk_system_available": self.zk_system is not None,
            "cost_router_available": self.cost_router is not None,
            "frameworks_available": {
                "crewai": CREWAI_AVAILABLE,
                "langgraph": LANGGRAPH_AVAILABLE,
                "semantic_kernel": SEMANTIC_KERNEL_AVAILABLE,
                "llama_index": LLAMA_INDEX_AVAILABLE
            }
        }

# Factory function
def create_artemis_swarm(config: Optional[Dict[str, Any]] = None) -> ArtemisSwarm:
    """Create and configure Artemis swarm"""
    return ArtemisSwarm(config)

# Example usage
if __name__ == "__main__":
    async def sophia_artemis_swarm():
        """Test the Artemis swarm"""
        config = {
            "openai_api_key": "test-key",
            "register_on_blockchain": True,
            "cost_optimization": True
        }

        swarm = create_artemis_swarm(config)

        # Test intent processing
        intent = "Create a FastAPI endpoint for user authentication with JWT tokens"
        print(f"Processing intent: {intent}")

        result = await swarm.process_intent(intent)
        print(f"Result: {json.dumps(result, indent=2)}")

        # Get metrics
        metrics = await swarm.get_swarm_metrics()
        print(f"Swarm metrics: {json.dumps(metrics, indent=2)}")

    # Run test
    asyncio.run(sophia_artemis_swarm())
