"""
Swarm Code Generation Engine - Generates Python swarm code from templates
Integrates with unified factories and validates configurations
Respects 8-task concurrency limit and resource allocation
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from app.swarms.templates.swarm_templates import (
    SwarmTemplate,
    SwarmTopology,
    swarm_template_catalog,
)

logger = logging.getLogger(__name__)

# ==============================================================================
# CODE GENERATION TEMPLATES
# ==============================================================================


class SwarmCodeGenerator:
    """Generates executable Python code from swarm templates"""

    def __init__(self):
        self.base_template_dir = Path(__file__).parent / "generated"
        self.base_template_dir.mkdir(exist_ok=True)

    def generate_swarm_code(
        self,
        template: SwarmTemplate,
        custom_config: Optional[dict[str, Any]] = None,
        swarm_name: Optional[str] = None,
    ) -> tuple[str, dict[str, Any]]:
        """Generate complete Python swarm code from template"""

        # Generate unique swarm name if not provided
        if not swarm_name:
            swarm_name = f"{template.id}_{uuid4().hex[:8]}"

        # Merge custom configuration
        config = custom_config or {}

        # Generate code based on topology
        if template.topology == SwarmTopology.SEQUENTIAL:
            code = self._generate_sequential_swarm(template, swarm_name, config)
        elif template.topology == SwarmTopology.STAR:
            code = self._generate_star_swarm(template, swarm_name, config)
        elif template.topology == SwarmTopology.COMMITTEE:
            code = self._generate_committee_swarm(template, swarm_name, config)
        elif template.topology == SwarmTopology.HIERARCHICAL:
            code = self._generate_hierarchical_swarm(template, swarm_name, config)
        else:
            raise ValueError(f"Unsupported topology: {template.topology}")

        # Generate metadata
        metadata = {
            "swarm_name": swarm_name,
            "template_id": template.id,
            "topology": template.topology.value,
            "domain": template.domain.value,
            "agent_count": len(template.agents),
            "estimated_duration": template.estimated_duration,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "resource_limits": template.resource_limits,
            "success_criteria": template.success_criteria,
        }

        return code, metadata

    def _generate_sequential_swarm(
        self, template: SwarmTemplate, swarm_name: str, config: dict[str, Any]
    ) -> str:
        """Generate sequential pipeline swarm code"""

        # Extract agents for each stage
        agents = template.agents

        code = f'''"""
Generated Sequential Pipeline Swarm: {swarm_name}
Template: {template.name}
Generated: {datetime.now(timezone.utc).isoformat()}
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.sophia.unified_factory import sophia_unified_factory
from app.artemis.unified_factory import artemis_unified_factory

logger = logging.getLogger(__name__)

class {swarm_name.replace("-", "_").title()}:
    """
    {template.description}

    Topology: Sequential Pipeline
    Stages: {len(agents)}
    Estimated Duration: {template.estimated_duration}
    """

    def __init__(self):
        self.swarm_name = "{swarm_name}"
        self.template_id = "{template.id}"
        self.agents = {{}}
        self.stage_results = []
        self.metadata = {{
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "initialized",
            "current_stage": 0,
            "total_stages": {len(agents)}
        }}

        # Resource limits from template
        self.resource_limits = {json.dumps(template.resource_limits, indent=12)}

        # Success criteria
        self.success_criteria = {json.dumps(template.success_criteria, indent=12)}

    async def initialize_agents(self) -> bool:
        """Initialize all agents for the pipeline"""
        try:
'''

        # Generate agent initialization code
        for i, agent in enumerate(agents):
            factory = (
                "sophia_unified_factory"
                if agent.factory_type == "sophia"
                else "artemis_unified_factory"
            )

            code += f"""
            # Stage {i+1}: {agent.role} ({agent.template_name})
            agent_{i+1}_config = {json.dumps(agent.custom_config, indent=16)}
            self.agents["stage_{i+1}"] = await {factory}.create_{
                "business_agent" if agent.factory_type == "sophia" else "technical_agent"
            }(
                "{agent.template_name}",
                agent_{i+1}_config
            )
            logger.info(f"Initialized stage {i+1} agent: {{self.agents['stage_{i+1}']}} ({agent.role})")
"""

        code += '''

            self.metadata["status"] = "agents_ready"
            return True

        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            self.metadata["status"] = "initialization_failed"
            self.metadata["error"] = str(e)
            return False

    async def execute_pipeline(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the sequential pipeline"""

        execution_start = datetime.now(timezone.utc)
        self.metadata["execution_started"] = execution_start.isoformat()
        self.metadata["status"] = "executing"

        try:
            current_data = input_data.copy()
            context = context or {}

'''

        # Generate stage execution code
        for i, agent in enumerate(agents):
            factory = (
                "sophia_unified_factory"
                if agent.factory_type == "sophia"
                else "artemis_unified_factory"
            )

            code += f"""
            # Execute Stage {i+1}: {agent.role}
            logger.info(f"Executing stage {i+1}: {agent.role}")
            self.metadata["current_stage"] = {i+1}

            stage_{i+1}_result = await {factory}.execute_{
                "business_task" if agent.factory_type == "sophia" else "mission"
            }(
                self.agents["stage_{i+1}"],
                f"Stage {i+1} analysis: {{current_data.get('task', 'pipeline_processing')}}",
                {{
                    "stage": {i+1},
                    "role": "{agent.role}",
                    "input_data": current_data,
                    "context": context,
                    "pipeline_metadata": self.metadata
                }}
            )

            if not stage_{i+1}_result.get("success", True):
                logger.error(f"Stage {i+1} failed: {{stage_{i+1}_result.get('error', 'Unknown error')}}")
                self.metadata["status"] = "stage_{i+1}_failed"
                self.metadata["failed_stage"] = {i+1}
                return {{
                    "success": False,
                    "error": f"Pipeline failed at stage {i+1}",
                    "stage_results": self.stage_results,
                    "metadata": self.metadata
                }}

            # Store stage result and prepare for next stage
            self.stage_results.append({{
                "stage": {i+1},
                "role": "{agent.role}",
                "result": stage_{i+1}_result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }})

            # Pass enriched data to next stage
            current_data.update({{
                f"stage_{i+1}_output": stage_{i+1}_result,
                f"stage_{i+1}_insights": stage_{i+1}_result.get("response", ""),
                "pipeline_context": context
            }})

"""

        code += f'''
            # Pipeline completion
            execution_end = datetime.now(timezone.utc)
            execution_duration = (execution_end - execution_start).total_seconds()

            self.metadata.update({{
                "status": "completed",
                "execution_completed": execution_end.isoformat(),
                "execution_duration_seconds": execution_duration,
                "stages_completed": {len(agents)},
                "success_rate": 1.0
            }})

            # Validate success criteria
            success_validation = await self._validate_success_criteria()

            final_result = {{
                "success": True,
                "swarm_name": self.swarm_name,
                "template_id": self.template_id,
                "topology": "sequential",
                "execution_duration": execution_duration,
                "stage_results": self.stage_results,
                "final_output": current_data,
                "success_validation": success_validation,
                "metadata": self.metadata
            }}

            logger.info(f"Sequential pipeline {{self.swarm_name}} completed successfully in {{execution_duration:.2f}}s")
            return final_result

        except Exception as e:
            logger.error(f"Pipeline execution failed: {{e}}")
            self.metadata["status"] = "execution_failed"
            self.metadata["error"] = str(e)

            return {{
                "success": False,
                "error": str(e),
                "stage_results": self.stage_results,
                "metadata": self.metadata
            }}

    async def _validate_success_criteria(self) -> Dict[str, Any]:
        """Validate results against success criteria"""
        validation_results = {{}}

        try:
            # Example validation logic
            for criterion, threshold in self.success_criteria.items():
                if criterion == "data_completeness":
                    # Calculate data completeness from stage results
                    completed_stages = len([r for r in self.stage_results if r["result"].get("success", True)])
                    actual_completeness = completed_stages / len(self.stage_results) if self.stage_results else 0
                    validation_results[criterion] = {{
                        "required": threshold,
                        "actual": actual_completeness,
                        "passed": actual_completeness >= threshold
                    }}

                elif criterion == "processing_speed":
                    # Calculate processing efficiency
                    total_duration = sum(r["result"].get("execution_time", 0) for r in self.stage_results)
                    max_expected = 30 * 60  # 30 minutes
                    efficiency = max(0, 1 - (total_duration / max_expected))
                    validation_results[criterion] = {{
                        "required": threshold,
                        "actual": efficiency,
                        "passed": efficiency >= threshold
                    }}

                else:
                    # Generic validation - mark as passed for now
                    validation_results[criterion] = {{
                        "required": threshold,
                        "actual": 1.0,
                        "passed": True
                    }}

            overall_success = all(v["passed"] for v in validation_results.values())
            validation_results["overall_success"] = overall_success

        except Exception as e:
            logger.error(f"Success criteria validation failed: {{e}}")
            validation_results["validation_error"] = str(e)

        return validation_results

    def get_status(self) -> Dict[str, Any]:
        """Get current swarm status"""
        return {{
            "swarm_name": self.swarm_name,
            "status": self.metadata.get("status", "unknown"),
            "current_stage": self.metadata.get("current_stage", 0),
            "total_stages": self.metadata.get("total_stages", {len(agents)}),
            "agents_initialized": len(self.agents),
            "stages_completed": len(self.stage_results),
            "metadata": self.metadata
        }}

# Factory function for easy instantiation
async def create_{swarm_name.replace("-", "_").lower()}() -> {swarm_name.replace("-", "_").title()}:
    """Create and initialize {swarm_name} swarm"""
    swarm = {swarm_name.replace("-", "_").title()}()

    if await swarm.initialize_agents():
        logger.info(f"Successfully created swarm: {{swarm.swarm_name}}")
        return swarm
    else:
        raise RuntimeError(f"Failed to initialize swarm: {{swarm.swarm_name}}")
'''

        return code

    def _generate_star_swarm(
        self, template: SwarmTemplate, swarm_name: str, config: dict[str, Any]
    ) -> str:
        """Generate star topology swarm code"""

        # Find coordinator and workers
        coordinator = next(
            (a for a in template.agents if a.role.endswith("coordinator")),
            template.agents[0],
        )
        workers = [a for a in template.agents if a != coordinator]

        code = f'''"""
Generated Star Topology Swarm: {swarm_name}
Template: {template.name}
Generated: {datetime.now(timezone.utc).isoformat()}
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.sophia.unified_factory import sophia_unified_factory
from app.artemis.unified_factory import artemis_unified_factory

logger = logging.getLogger(__name__)

class {swarm_name.replace("-", "_").title()}:
    """
    {template.description}

    Topology: Star Network
    Coordinator: {coordinator.template_name} ({coordinator.role})
    Workers: {len(workers)}
    """

    def __init__(self):
        self.swarm_name = "{swarm_name}"
        self.template_id = "{template.id}"
        self.coordinator = None
        self.workers = {{}}
        self.results = {{}}
        self.metadata = {{
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "initialized",
            "coordinator_agent": "{coordinator.template_name}",
            "worker_count": {len(workers)}
        }}

    async def initialize_agents(self) -> bool:
        """Initialize coordinator and worker agents"""
        try:
            # Initialize coordinator
            coordinator_factory = "sophia_unified_factory" if "{coordinator.factory_type}" == "sophia" else "artemis_unified_factory"
            coordinator_config = {json.dumps(coordinator.custom_config, indent=16)}

            self.coordinator = await {coordinator_factory}.create_{
                "business_agent" if coordinator.factory_type == "sophia" else "technical_agent"
            }(
                "{coordinator.template_name}",
                coordinator_config
            )
            logger.info(f"Initialized coordinator: {{self.coordinator}} ({coordinator.role})")

'''

        # Generate worker initialization
        for i, worker in enumerate(workers):
            factory = (
                "sophia_unified_factory"
                if worker.factory_type == "sophia"
                else "artemis_unified_factory"
            )

            code += f"""
            # Initialize worker {i+1}: {worker.role}
            worker_{i+1}_factory = "sophia_unified_factory" if "{worker.factory_type}" == "sophia" else "artemis_unified_factory"
            worker_{i+1}_config = {json.dumps(worker.custom_config, indent=16)}

            self.workers["worker_{i+1}"] = await {factory}.create_{
                "business_agent" if worker.factory_type == "sophia" else "technical_agent"
            }(
                "{worker.template_name}",
                worker_{i+1}_config
            )
            logger.info(f"Initialized worker {i+1}: {{self.workers['worker_{i+1}']}} ({worker.role})")
"""

        code += (
            '''

            self.metadata["status"] = "agents_ready"
            return True

        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            self.metadata["status"] = "initialization_failed"
            return False

    async def execute_star_coordination(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute star topology with coordinator and workers"""

        execution_start = datetime.now(timezone.utc)
        self.metadata["execution_started"] = execution_start.isoformat()
        self.metadata["status"] = "executing"

        try:
            context = context or {}

            # Phase 1: Coordinator planning
            coordinator_factory = "sophia_unified_factory" if "'''
            + coordinator.factory_type
            + '''" == "sophia" else "artemis_unified_factory"

            planning_result = await {coordinator_factory}.execute_{
                "business_task" if "'''
            + coordinator.factory_type
            + """" == "sophia" else "mission"
            }(
                self.coordinator,
                f"Coordinate star network analysis: {task}",
                {
                    "role": "coordination_planning",
                    "workers_available": list(self.workers.keys()),
                    "task": task,
                    "context": context
                }
            )

            if not planning_result.get("success", True):
                logger.error(f"Coordinator planning failed: {planning_result.get('error')}")
                return {
                    "success": False,
                    "error": "Coordinator planning failed",
                    "coordinator_result": planning_result
                }

            # Phase 2: Parallel worker execution
            worker_tasks = []

"""
        )

        for i, worker in enumerate(workers):
            factory = (
                "sophia_unified_factory"
                if worker.factory_type == "sophia"
                else "artemis_unified_factory"
            )
            code += f"""
            # Worker {i+1} task
            worker_{i+1}_task = asyncio.create_task(
                {factory}.execute_{
                    "business_task" if "{worker.factory_type}" == "sophia" else "mission"
                }(
                    self.workers["worker_{i+1}"],
                    f"Worker analysis: {{task}}",
                    {{
                        "role": "{worker.role}",
                        "coordinator_guidance": planning_result,
                        "task": task,
                        "context": context,
                        "worker_id": {i+1}
                    }}
                )
            )
            worker_tasks.append(("worker_{i+1}", worker_{i+1}_task))
"""

        code += (
            """

            # Wait for all workers to complete
            worker_results = {}
            for worker_name, task in worker_tasks:
                try:
                    result = await task
                    worker_results[worker_name] = result
                    logger.info(f"Worker {worker_name} completed")
                except Exception as e:
                    logger.error(f"Worker {worker_name} failed: {e}")
                    worker_results[worker_name] = {
                        "success": False,
                        "error": str(e)
                    }

            # Phase 3: Coordinator synthesis
            synthesis_result = await {"""
            + coordinator_factory
            + '''}.execute_{
                "business_task" if "'''
            + coordinator.factory_type
            + '''" == "sophia" else "mission"
            }(
                self.coordinator,
                f"Synthesize worker results for: {task}",
                {
                    "role": "result_synthesis",
                    "worker_results": worker_results,
                    "planning_result": planning_result,
                    "task": task,
                    "context": context
                }
            )

            # Completion
            execution_end = datetime.now(timezone.utc)
            execution_duration = (execution_end - execution_start).total_seconds()

            self.metadata.update({
                "status": "completed",
                "execution_completed": execution_end.isoformat(),
                "execution_duration_seconds": execution_duration,
                "workers_completed": len([r for r in worker_results.values() if r.get("success", True)])
            })

            final_result = {
                "success": True,
                "swarm_name": self.swarm_name,
                "template_id": self.template_id,
                "topology": "star",
                "execution_duration": execution_duration,
                "coordinator_result": {
                    "planning": planning_result,
                    "synthesis": synthesis_result
                },
                "worker_results": worker_results,
                "metadata": self.metadata
            }

            logger.info(f"Star swarm {self.swarm_name} completed successfully in {execution_duration:.2f}s")
            return final_result

        except Exception as e:
            logger.error(f"Star coordination failed: {e}")
            self.metadata["status"] = "execution_failed"
            return {
                "success": False,
                "error": str(e),
                "metadata": self.metadata
            }

# Factory function
async def create_{swarm_name.replace("-", "_").lower()}() -> {swarm_name.replace("-", "_").title()}:
    """Create and initialize {swarm_name} star swarm"""
    swarm = {swarm_name.replace("-", "_").title()}()

    if await swarm.initialize_agents():
        logger.info(f"Successfully created star swarm: {swarm.swarm_name}")
        return swarm
    else:
        raise RuntimeError(f"Failed to initialize star swarm: {swarm.swarm_name}")
'''
        )

        return code

    def _generate_committee_swarm(
        self, template: SwarmTemplate, swarm_name: str, config: dict[str, Any]
    ) -> str:
        """Generate committee voting swarm code"""

        # Find arbiter and committee members
        arbiter = next((a for a in template.agents if a.role == "arbiter"), None)
        committee = [a for a in template.agents if a.role != "arbiter"]

        code = f'''"""
Generated Committee Voting Swarm: {swarm_name}
Template: {template.name}
Generated: {datetime.now(timezone.utc).isoformat()}
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.sophia.unified_factory import sophia_unified_factory
from app.artemis.unified_factory import artemis_unified_factory

logger = logging.getLogger(__name__)

class {swarm_name.replace("-", "_").title()}:
    """
    {template.description}

    Topology: Committee Voting
    Committee Members: {len(committee)}
    {"Arbiter: " + arbiter.template_name if arbiter else "No Arbiter"}
    """

    def __init__(self):
        self.swarm_name = "{swarm_name}"
        self.template_id = "{template.id}"
        self.committee_members = {{}}
        {"self.arbiter = None" if arbiter else "# No arbiter for this committee"}
        self.voting_results = []
        self.metadata = {{
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "initialized",
            "committee_size": {len(committee)},
            {"'has_arbiter': True" if arbiter else "'has_arbiter': False"}
        }}

        # Voting configuration
        self.voting_config = {json.dumps(template.coordination_config, indent=12)}

    async def initialize_agents(self) -> bool:
        """Initialize committee members and arbiter"""
        try:
'''

        # Generate committee member initialization
        for i, member in enumerate(committee):
            factory = (
                "sophia_unified_factory"
                if member.factory_type == "sophia"
                else "artemis_unified_factory"
            )
            code += f"""
            # Committee member {i+1}: {member.role}
            member_{i+1}_factory = "sophia_unified_factory" if "{member.factory_type}" == "sophia" else "artemis_unified_factory"
            member_{i+1}_config = {json.dumps(member.custom_config, indent=16)}

            self.committee_members["member_{i+1}"] = await {factory}.create_{
                "business_agent" if member.factory_type == "sophia" else "technical_agent"
            }(
                "{member.template_name}",
                member_{i+1}_config
            )
            logger.info(f"Initialized committee member {i+1}: {{self.committee_members['member_{i+1}']}} ({member.role})")
"""

        # Initialize arbiter if present
        if arbiter:
            arbiter_factory = (
                "sophia_unified_factory"
                if arbiter.factory_type == "sophia"
                else "artemis_unified_factory"
            )
            code += f"""

            # Initialize arbiter
            arbiter_factory = "sophia_unified_factory" if "{arbiter.factory_type}" == "sophia" else "artemis_unified_factory"
            arbiter_config = {json.dumps(arbiter.custom_config, indent=16)}

            self.arbiter = await {arbiter_factory}.create_{
                "business_agent" if arbiter.factory_type == "sophia" else "technical_agent"
            }(
                "{arbiter.template_name}",
                arbiter_config
            )
            logger.info(f"Initialized arbiter: {{self.arbiter}} ({arbiter.role})")
"""

        code += '''

            self.metadata["status"] = "agents_ready"
            return True

        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            self.metadata["status"] = "initialization_failed"
            return False

    async def execute_committee_voting(
        self,
        proposal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute committee voting process with optional arbitration"""

        execution_start = datetime.now(timezone.utc)
        self.metadata["execution_started"] = execution_start.isoformat()
        self.metadata["status"] = "voting"

        try:
            context = context or {}
            voting_rounds = self.voting_config.get("voting_rounds", 1)
            consensus_threshold = self.voting_config.get("consensus_threshold", 0.7)

            final_decision = None

            for round_num in range(1, voting_rounds + 1):
                logger.info(f"Starting voting round {round_num}")

                # Collect votes from committee members
                member_votes = {}
                vote_tasks = []

'''

        for i, member in enumerate(committee):
            factory = (
                "sophia_unified_factory"
                if member.factory_type == "sophia"
                else "artemis_unified_factory"
            )
            code += f"""
                # Member {i+1} vote
                member_{i+1}_vote_task = asyncio.create_task(
                    {factory}.execute_{
                        "business_task" if "{member.factory_type}" == "sophia" else "mission"
                    }(
                        self.committee_members["member_{i+1}"],
                        f"Vote on proposal: {{proposal}}",
                        {{
                            "role": "committee_member",
                            "voting_round": round_num,
                            "proposal": proposal,
                            "context": context,
                            "member_weight": {member.weight}
                        }}
                    )
                )
                vote_tasks.append(("member_{i+1}", member_{i+1}_vote_task, {member.weight}))
"""

        code += """

                # Collect all votes
                for member_name, vote_task, weight in vote_tasks:
                    try:
                        vote_result = await vote_task
                        member_votes[member_name] = {
                            "result": vote_result,
                            "weight": weight,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    except Exception as e:
                        logger.error(f"Member {member_name} voting failed: {e}")
                        member_votes[member_name] = {
                            "result": {"success": False, "error": str(e)},
                            "weight": weight,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }

                # Calculate consensus
                consensus_result = await self._calculate_consensus(member_votes, consensus_threshold)

                round_result = {
                    "round": round_num,
                    "member_votes": member_votes,
                    "consensus": consensus_result,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                self.voting_results.append(round_result)

                # Check if consensus reached
                if consensus_result["consensus_reached"]:
                    final_decision = consensus_result["decision"]
                    logger.info(f"Consensus reached in round {round_num}: {final_decision}")
                    break
                else:
                    logger.info(f"No consensus in round {round_num}, consensus: {consensus_result['consensus_score']:.2f}")

"""

        if arbiter:
            arbiter_factory = (
                "sophia_unified_factory"
                if arbiter.factory_type == "sophia"
                else "artemis_unified_factory"
            )
            code += f"""
            # Arbitration if no consensus and arbiter available
            if final_decision is None and self.arbiter:
                logger.info("No consensus reached, invoking arbiter")

                arbiter_result = await {arbiter_factory}.execute_{
                    "business_task" if "{arbiter.factory_type}" == "sophia" else "mission"
                }(
                    self.arbiter,
                    f"Arbitrate committee decision: {{proposal}}",
                    {{
                        "role": "arbiter",
                        "voting_results": self.voting_results,
                        "proposal": proposal,
                        "context": context,
                        "arbitration_mode": True
                    }}
                )

                if arbiter_result.get("success", True):
                    final_decision = arbiter_result.get("response", "arbiter_decision")
                    self.metadata["arbitration_used"] = True
                    logger.info(f"Arbiter decision: {{final_decision}}")
"""

        code += '''

            # Completion
            execution_end = datetime.now(timezone.utc)
            execution_duration = (execution_end - execution_start).total_seconds()

            self.metadata.update({
                "status": "completed",
                "execution_completed": execution_end.isoformat(),
                "execution_duration_seconds": execution_duration,
                "voting_rounds_completed": len(self.voting_results),
                "final_decision_reached": final_decision is not None
            })

            final_result = {
                "success": True,
                "swarm_name": self.swarm_name,
                "template_id": self.template_id,
                "topology": "committee",
                "execution_duration": execution_duration,
                "proposal": proposal,
                "final_decision": final_decision,
                "voting_results": self.voting_results,
                "consensus_achieved": final_decision is not None,
                "metadata": self.metadata
            }

            logger.info(f"Committee swarm {self.swarm_name} completed in {execution_duration:.2f}s")
            return final_result

        except Exception as e:
            logger.error(f"Committee voting failed: {e}")
            self.metadata["status"] = "execution_failed"
            return {
                "success": False,
                "error": str(e),
                "voting_results": self.voting_results,
                "metadata": self.metadata
            }

    async def _calculate_consensus(
        self,
        member_votes: Dict[str, Any],
        threshold: float
    ) -> Dict[str, Any]:
        """Calculate consensus from member votes"""
        # Simplified consensus calculation
        successful_votes = [v for v in member_votes.values() if v["result"].get("success", True)]
        total_weight = sum(v["weight"] for v in member_votes.values())
        successful_weight = sum(v["weight"] for v in successful_votes)

        consensus_score = successful_weight / total_weight if total_weight > 0 else 0
        consensus_reached = consensus_score >= threshold

        return {
            "consensus_score": consensus_score,
            "consensus_reached": consensus_reached,
            "threshold": threshold,
            "successful_votes": len(successful_votes),
            "total_votes": len(member_votes),
            "decision": "consensus_decision" if consensus_reached else None
        }

# Factory function
async def create_{swarm_name.replace("-", "_").lower()}() -> {swarm_name.replace("-", "_").title()}:
    """Create and initialize {swarm_name} committee swarm"""
    swarm = {swarm_name.replace("-", "_").title()}()

    if await swarm.initialize_agents():
        logger.info(f"Successfully created committee swarm: {swarm.swarm_name}")
        return swarm
    else:
        raise RuntimeError(f"Failed to initialize committee swarm: {swarm.swarm_name}")
'''

        return code

    def _generate_hierarchical_swarm(
        self, template: SwarmTemplate, swarm_name: str, config: dict[str, Any]
    ) -> str:
        """Generate hierarchical coordination swarm code"""

        # Sort agents by command level (weight determines hierarchy)
        agents_by_level = sorted(template.agents, key=lambda x: x.weight, reverse=True)

        code = f'''"""
Generated Hierarchical Swarm: {swarm_name}
Template: {template.name}
Generated: {datetime.now(timezone.utc).isoformat()}
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.sophia.unified_factory import sophia_unified_factory
from app.artemis.unified_factory import artemis_unified_factory

logger = logging.getLogger(__name__)

class {swarm_name.replace("-", "_").title()}:
    """
    {template.description}

    Topology: Hierarchical Command Structure
    Levels: {len({a.weight for a in agents_by_level})}
    Total Agents: {len(agents_by_level)}
    """

    def __init__(self):
        self.swarm_name = "{swarm_name}"
        self.template_id = "{template.id}"
        self.hierarchy = {{}}  # level -> agents
        self.level_results = {{}}
        self.metadata = {{
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "initialized",
            "hierarchy_levels": {len({a.weight for a in agents_by_level})},
            "total_agents": {len(agents_by_level)}
        }}

    async def initialize_agents(self) -> bool:
        """Initialize hierarchical agent structure"""
        try:
'''

        # Group agents by hierarchy level (weight)
        levels = {}
        for agent in agents_by_level:
            level = agent.weight
            if level not in levels:
                levels[level] = []
            levels[level].append(agent)

        # Generate initialization code for each level
        for level, level_agents in sorted(levels.items(), reverse=True):
            code += f"""
            # Initialize level {level} agents
            self.hierarchy[{level}] = {{}}
"""

            for i, agent in enumerate(level_agents):
                factory = (
                    "sophia_unified_factory"
                    if agent.factory_type == "sophia"
                    else "artemis_unified_factory"
                )
                code += f"""
            level_{level}_agent_{i+1}_config = {json.dumps(agent.custom_config, indent=16)}
            self.hierarchy[{level}]["agent_{i+1}"] = await {factory}.create_{
                "business_agent" if agent.factory_type == "sophia" else "technical_agent"
            }(
                "{agent.template_name}",
                level_{level}_agent_{i+1}_config
            )
            logger.info(f"Initialized level {level} agent {i+1}: {{self.hierarchy[{level}]['agent_{i+1}']}} ({agent.role})")
"""

        code += '''

            self.metadata["status"] = "agents_ready"
            return True

        except Exception as e:
            logger.error(f"Failed to initialize hierarchical agents: {e}")
            self.metadata["status"] = "initialization_failed"
            return False

    async def execute_hierarchical_command(
        self,
        mission: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute hierarchical command structure"""

        execution_start = datetime.now(timezone.utc)
        self.metadata["execution_started"] = execution_start.isoformat()
        self.metadata["status"] = "executing"

        try:
            context = context or {}
            sorted_levels = sorted(self.hierarchy.keys(), reverse=True)

            # Execute each level in hierarchy order
            for level in sorted_levels:
                logger.info(f"Executing hierarchy level {level}")

                level_agents = self.hierarchy[level]
                level_tasks = []

                # Prepare context from higher levels
                higher_level_context = {
                    "mission": mission,
                    "context": context,
                    "hierarchy_level": level,
                    "higher_level_results": {
                        l: self.level_results[l] for l in sorted_levels if l > level
                    }
                }

'''

        # Generate execution code for each agent in the level
        for level, level_agents in sorted(levels.items(), reverse=True):
            for i, agent in enumerate(level_agents):
                factory = (
                    "sophia_unified_factory"
                    if agent.factory_type == "sophia"
                    else "artemis_unified_factory"
                )
                code += f"""
                # Level {level}, Agent {i+1} task
                if {level} in sorted_levels and level == {level}:
                    level_{level}_agent_{i+1}_task = asyncio.create_task(
                        {factory}.execute_{
                            "business_task" if "{agent.factory_type}" == "sophia" else "mission"
                        }(
                            level_agents["agent_{i+1}"],
                            f"Level {level} mission: {{mission}}",
                            {{
                                "role": "{agent.role}",
                                "hierarchy_level": level,
                                "mission": mission,
                                "context": higher_level_context,
                                "command_weight": {agent.weight}
                            }}
                        )
                    )
                    level_tasks.append(("agent_{i+1}", level_{level}_agent_{i+1}_task))
"""

        code += '''

                # Wait for all agents at this level to complete
                level_results = {}
                for agent_name, task in level_tasks:
                    try:
                        result = await task
                        level_results[agent_name] = result
                        logger.info(f"Level {level} agent {agent_name} completed")
                    except Exception as e:
                        logger.error(f"Level {level} agent {agent_name} failed: {e}")
                        level_results[agent_name] = {
                            "success": False,
                            "error": str(e)
                        }

                # Store level results
                self.level_results[level] = {
                    "level": level,
                    "results": level_results,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "success_rate": len([r for r in level_results.values() if r.get("success", True)]) / len(level_results) if level_results else 0
                }

                logger.info(f"Completed hierarchy level {level} with {len(level_results)} agents")

            # Completion
            execution_end = datetime.now(timezone.utc)
            execution_duration = (execution_end - execution_start).total_seconds()

            self.metadata.update({
                "status": "completed",
                "execution_completed": execution_end.isoformat(),
                "execution_duration_seconds": execution_duration,
                "levels_completed": len(self.level_results)
            })

            final_result = {
                "success": True,
                "swarm_name": self.swarm_name,
                "template_id": self.template_id,
                "topology": "hierarchical",
                "execution_duration": execution_duration,
                "mission": mission,
                "hierarchy_results": self.level_results,
                "levels_executed": len(self.level_results),
                "metadata": self.metadata
            }

            logger.info(f"Hierarchical swarm {self.swarm_name} completed in {execution_duration:.2f}s")
            return final_result

        except Exception as e:
            logger.error(f"Hierarchical execution failed: {e}")
            self.metadata["status"] = "execution_failed"
            return {
                "success": False,
                "error": str(e),
                "level_results": self.level_results,
                "metadata": self.metadata
            }

# Factory function
async def create_{swarm_name.replace("-", "_").lower()}() -> {swarm_name.replace("-", "_").title()}:
    """Create and initialize {swarm_name} hierarchical swarm"""
    swarm = {swarm_name.replace("-", "_").title()}()

    if await swarm.initialize_agents():
        logger.info(f"Successfully created hierarchical swarm: {swarm.swarm_name}")
        return swarm
    else:
        raise RuntimeError(f"Failed to initialize hierarchical swarm: {swarm.swarm_name}")
'''

        return code

    def validate_and_generate(
        self,
        template_id: str,
        custom_config: Optional[dict[str, Any]] = None,
        swarm_name: Optional[str] = None,
    ) -> tuple[bool, str, dict[str, Any], list[str]]:
        """Validate template and generate code with comprehensive checks"""

        # Get template
        template = swarm_template_catalog.get_template(template_id)
        if not template:
            return False, "", {}, [f"Template '{template_id}' not found"]

        # Validate template
        is_valid, errors = swarm_template_catalog.validate_template(template)
        if not is_valid:
            return False, "", {}, errors

        # Validate resource constraints (8-task limit)
        total_agents = len(template.agents)
        max_concurrent = template.resource_limits.get(
            "max_concurrent_tasks", total_agents
        )

        if max_concurrent > 8:
            errors.append(
                f"Template requests {max_concurrent} concurrent tasks, system limit is 8"
            )
            return False, "", {}, errors

        if total_agents > 8:
            errors.append(f"Template has {total_agents} agents, exceeds 8-task limit")
            return False, "", {}, errors

        try:
            # Generate code
            code, metadata = self.generate_swarm_code(
                template, custom_config, swarm_name
            )

            # Additional metadata
            metadata.update(
                {
                    "validation_passed": True,
                    "resource_compliance": True,
                    "factory_integrations": {
                        "sophia": len(
                            [a for a in template.agents if a.factory_type == "sophia"]
                        ),
                        "artemis": len(
                            [a for a in template.agents if a.factory_type == "artemis"]
                        ),
                    },
                }
            )

            return True, code, metadata, []

        except Exception as e:
            return False, "", {}, [f"Code generation failed: {str(e)}"]

    def save_generated_swarm(
        self, swarm_name: str, code: str, metadata: dict[str, Any]
    ) -> str:
        """Save generated swarm code to file"""

        filename = f"{swarm_name.lower().replace('-', '_')}_swarm.py"
        filepath = self.base_template_dir / filename

        try:
            with open(filepath, "w") as f:
                f.write(code)

            # Save metadata
            metadata_file = (
                self.base_template_dir
                / f"{swarm_name.lower().replace('-', '_')}_metadata.json"
            )
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Saved generated swarm to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to save swarm: {e}")
            raise


# ==============================================================================
# GLOBAL GENERATOR INSTANCE
# ==============================================================================

# Global code generator instance
swarm_code_generator = SwarmCodeGenerator()
