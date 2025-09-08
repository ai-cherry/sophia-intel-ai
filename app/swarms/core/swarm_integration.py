"""
Swarm Integration Layer
Bridges micro-swarms with existing swarm infrastructure, orchestrators, and integrations
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.core.portkey_manager import TaskType
from app.integrations.gong_brain_training_adapter import GongBrainTrainingAdapter
from app.integrations.gong_csv_ingestion import GongCSVIngestionPipeline
from app.integrations.linear_client import LinearClient
from app.mcp.clients.stdio_client import detect_stdio_mcp
from app.memory.unified_memory_router import DocChunk, MemoryDomain
from app.orchestrators.base_orchestrator import (
    BaseOrchestrator,
    ExecutionPriority,
    OrchestratorConfig,
    Result,
    Task,
)
from app.swarms.artemis.technical_agents import ArtemisSwarmFactory
from app.swarms.core.intelligent_router import get_intelligent_router
from app.swarms.core.message_braider import create_message_braider
from app.swarms.core.micro_swarm_base import MicroSwarmCoordinator, SwarmResult
from app.swarms.core.scheduler import get_scheduler
from app.swarms.core.slack_delivery import get_delivery_engine
from app.swarms.sophia.mythology_agents import SophiaMythologySwarmFactory

logger = logging.getLogger(__name__)


class IntegrationType(Enum):
    """Types of integrations"""

    DATA_SOURCE = "data_source"  # External data inputs
    NOTIFICATION = "notification"  # Output delivery
    ORCHESTRATION = "orchestration"  # Workflow management
    STORAGE = "storage"  # Data persistence
    MONITORING = "monitoring"  # Performance tracking


@dataclass
class IntegrationConfig:
    """Configuration for an integration"""

    integration_id: str
    name: str
    integration_type: IntegrationType
    enabled: bool = True
    auto_sync: bool = False
    sync_interval_minutes: int = 60
    config_params: dict[str, Any] = field(default_factory=dict)
    error_handling: dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmExecutionContext:
    """Context for swarm execution within the integrated environment"""

    execution_id: str
    request_source: str  # "api", "slack", "scheduled", "integration"
    user_id: Optional[str] = None
    channel_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    integration_context: dict[str, Any] = field(default_factory=dict)

    # Resource constraints
    max_cost_usd: float = 2.0
    timeout_minutes: int = 10
    priority: ExecutionPriority = ExecutionPriority.NORMAL

    # Integration flags
    store_in_memory: bool = True
    notify_completion: bool = True
    update_integrations: bool = True


class IntegratedSwarmOrchestrator(BaseOrchestrator):
    """
    Orchestrator that integrates micro-swarms with existing infrastructure
    """

    def __init__(self, domain: MemoryDomain):
        config = OrchestratorConfig(
            domain=domain,
            name=f"Integrated {domain.value.title()} Swarm Orchestrator",
            description=f"Orchestrates micro-swarms for {domain.value} domain with full integration support",
            max_concurrent_tasks=5,
            enable_memory=True,
            enable_monitoring=True,
            enable_caching=True,
        )
        super().__init__(config)

        # Micro-swarm factories
        self.sophia_factory = SophiaMythologySwarmFactory()
        self.artemis_factory = ArtemisSwarmFactory()

        # Core services
        self.intelligent_router = get_intelligent_router()
        self.scheduler = get_scheduler()
        # Slack delivery: only enabled for Sophia domain
        self.delivery_engine = get_delivery_engine() if domain == MemoryDomain.SOPHIA else None

        # External integrations
        self.integrations: dict[str, Any] = {}
        self._initialize_integrations()

        # Execution tracking
        self.active_swarms: dict[str, MicroSwarmCoordinator] = {}

        # Prefer local stdio MCP for memory/FS/git if available
        try:
            self.mcp_stdio = detect_stdio_mcp()
            if self.mcp_stdio:
                logger.info(
                    "Stdio MCP detected and will be used for memory/FS/git ops where applicable"
                )
        except Exception as e:
            self.mcp_stdio = None
            logger.warning(f"Stdio MCP not available: {e}")

        logger.info(f"Initialized integrated swarm orchestrator for {domain.value}")

    def _initialize_integrations(self):
        """Initialize external integrations"""

        try:
            # Slack integration available only for Sophia domain
            if self.domain == MemoryDomain.SOPHIA:
                try:
                    from app.integrations.slack_integration import SlackClient

                    self.integrations["slack"] = SlackClient()
                except Exception as e:
                    logger.warning(f"Slack integration unavailable: {e}")

            # Linear integration
            self.integrations["linear"] = LinearClient()

            # Gong integrations
            self.integrations["gong_training"] = GongBrainTrainingAdapter()
            self.integrations["gong_csv"] = GongCSVIngestionPipeline()

            logger.info("Initialized external integrations")
        except Exception as e:
            logger.warning(f"Some integrations failed to initialize: {e}")

    async def _execute_core(self, task: Task, routing: Any) -> Result:
        """Core execution logic for integrated swarms"""

        try:
            # Parse swarm request from task content
            swarm_request = await self._parse_swarm_request(task)

            # Create execution context
            context = SwarmExecutionContext(
                execution_id=task.id,
                request_source=task.metadata.get("source", "api"),
                user_id=task.metadata.get("user_id"),
                channel_id=task.metadata.get("channel_id"),
                max_cost_usd=task.budget.get("cost_usd", 2.0),
                timeout_minutes=task.metadata.get("timeout_minutes", 10),
                priority=task.priority,
            )

            # Collaboration context (pending tasks and active proposals)
            try:
                mcp = detect_stdio_mcp()
                if mcp:
                    # Pending tasks for this domain's primary agent
                    agent = "codex" if self.domain == MemoryDomain.ARTEMIS else "claude"
                    pending_q = f"collab AND pending AND for:{agent}"
                    proposals_q = "collab AND pending_review"
                    pending = mcp.memory_search(pending_q, limit=20).get("results", [])
                    proposals = mcp.memory_search(proposals_q, limit=20).get("results", [])
                    context.integration_context["collab"] = {
                        "pending_tasks": [
                            {
                                "topic": it.get("topic"),
                                "tags": it.get("tags"),
                                "ts": it.get("timestamp"),
                            }
                            for it in pending
                        ],
                        "active_proposals": [
                            {
                                "topic": it.get("topic"),
                                "tags": it.get("tags"),
                                "ts": it.get("timestamp"),
                            }
                            for it in proposals
                        ],
                    }
            except Exception:
                pass

            # Execute swarm with full integration
            swarm_result = await self._execute_integrated_swarm(
                swarm_request=swarm_request, context=context
            )

            # Process results
            result = await self._process_swarm_result(swarm_result, context)

            return result

        except Exception as e:
            logger.error(f"Integrated swarm execution failed: {e}")
            return Result(
                success=False, content=f"Swarm execution failed: {str(e)}", errors=[str(e)]
            )

    async def _parse_swarm_request(self, task: Task) -> dict[str, Any]:
        """Parse task content into swarm request"""

        # Try to parse as JSON first
        try:
            if task.content.startswith("{"):
                return json.loads(task.content)
        except json.JSONDecodeError:
            pass

        # Parse natural language request
        return {
            "content": task.content,
            "type": task.metadata.get("swarm_type", "auto_detect"),
            "domain": self.domain.value,
            "coordination_pattern": task.metadata.get("coordination_pattern", "sequential"),
            "agents": task.metadata.get("agents", []),
            "context": task.metadata.get("context", {}),
        }

    async def _execute_integrated_swarm(
        self, swarm_request: dict[str, Any], context: SwarmExecutionContext
    ) -> SwarmResult:
        """Execute swarm with full integration support"""

        # Determine swarm type and create coordinator
        coordinator = await self._create_swarm_coordinator(swarm_request)

        # Register active swarm
        self.active_swarms[context.execution_id] = coordinator

        # Pre-execution integration tasks
        # Record swarm_type and task in integration context for downstream tagging
        try:
            context.integration_context["swarm_type"] = swarm_request.get("type")
            context.integration_context["task"] = swarm_request.get("content", "")[:200]
        except Exception:
            pass
        await self._pre_execution_integration(swarm_request, context)

        try:
            # Create message braider for this execution
            create_message_braider(
                swarm_id=context.execution_id,
                coordination_pattern=swarm_request.get("coordination_pattern", "sequential"),
            )

            # Execute swarm
            swarm_result = await coordinator.execute(
                task=swarm_request["content"], context=swarm_request.get("context", {})
            )

            # Post-execution integration tasks
            await self._post_execution_integration(swarm_result, context)

            return swarm_result

        finally:
            # Cleanup
            if context.execution_id in self.active_swarms:
                del self.active_swarms[context.execution_id]

    async def _create_swarm_coordinator(
        self, swarm_request: dict[str, Any]
    ) -> MicroSwarmCoordinator:
        """Create appropriate swarm coordinator based on request"""

        domain = swarm_request.get("domain", self.domain.value)
        swarm_type = swarm_request.get("type", "auto_detect")

        # Auto-detect swarm type if needed
        if swarm_type == "auto_detect":
            swarm_type = await self._auto_detect_swarm_type(swarm_request["content"])

        # Create coordinator based on domain and type
        if domain == "sophia":
            return await self._create_sophia_swarm(swarm_type, swarm_request)
        elif domain == "artemis":
            return await self._create_artemis_swarm(swarm_type, swarm_request)
        else:
            # Default to Sophia business intelligence
            return self.sophia_factory.create_business_intelligence_swarm()

    async def _auto_detect_swarm_type(self, content: str) -> str:
        """Auto-detect appropriate swarm type based on content"""

        content_lower = content.lower()

        # Business intelligence keywords
        bi_keywords = [
            "market",
            "sales",
            "revenue",
            "customers",
            "business",
            "competitive",
            "analysis",
        ]
        if any(keyword in content_lower for keyword in bi_keywords):
            return "business_intelligence"

        # Technical keywords
        tech_keywords = ["code", "architecture", "system", "technical", "development", "security"]
        if any(keyword in content_lower for keyword in tech_keywords):
            return "technical_analysis"

        # Strategic keywords
        strategy_keywords = ["strategy", "planning", "roadmap", "objectives", "goals"]
        if any(keyword in content_lower for keyword in strategy_keywords):
            return "strategic_planning"

        # Default
        return "business_intelligence"

    async def _create_sophia_swarm(
        self, swarm_type: str, request: dict[str, Any]
    ) -> MicroSwarmCoordinator:
        """Create Sophia domain swarm"""

        if swarm_type == "business_intelligence":
            return self.sophia_factory.create_business_intelligence_swarm()
        elif swarm_type == "strategic_planning":
            return self.sophia_factory.create_strategic_planning_swarm()
        elif swarm_type == "business_health":
            return self.sophia_factory.create_business_health_swarm()
        elif swarm_type == "comprehensive_analysis":
            return self.sophia_factory.create_comprehensive_analysis_swarm()
        elif swarm_type == "custom":
            agents = request.get("agents", ["hermes", "athena", "minerva"])
            return self.sophia_factory.create_custom_swarm(agents)
        else:
            return self.sophia_factory.create_business_intelligence_swarm()

    async def _create_artemis_swarm(
        self, swarm_type: str, request: dict[str, Any]
    ) -> MicroSwarmCoordinator:
        """Create Artemis domain swarm"""

        if swarm_type == "technical_analysis" or swarm_type == "code_review":
            return self.artemis_factory.create_code_review_swarm()
        elif swarm_type == "architecture_review":
            return self.artemis_factory.create_architecture_review_swarm()
        elif swarm_type == "security_assessment":
            return self.artemis_factory.create_security_assessment_swarm()
        elif swarm_type == "technical_strategy":
            return self.artemis_factory.create_technical_strategy_swarm()
        elif swarm_type == "full_technical":
            return self.artemis_factory.create_full_technical_swarm()
        elif swarm_type == "repository_scout":
            coord = self.artemis_factory.create_repository_scout_swarm()
            # Fire-and-forget prefetch to prime memory context for scouts
            try:
                import asyncio

                from app.swarms.scout.delta_index import delta_index
                from app.swarms.scout.prefetch import prefetch_and_index

                # Limit: 10 files x 50KB each (~500KB total)
                loop = asyncio.get_event_loop()
                loop.create_task(
                    prefetch_and_index(repo_root=".", max_files=10, max_bytes_per_file=50_000)
                )
                # Also schedule delta indexing (feature-flagged)
                loop.create_task(
                    delta_index(repo_root=".", max_total_bytes=500_000, max_bytes_per_file=50_000)
                )
            except Exception:
                # Non-blocking: ignore any prefetch scheduling errors
                pass
            return coord
        elif swarm_type == "code_planning":
            return self.artemis_factory.create_code_planning_swarm()
        elif swarm_type == "code_review_micro":
            return self.artemis_factory.create_code_review_micro_swarm()
        elif swarm_type == "security_micro":
            return self.artemis_factory.create_security_micro_swarm()
        elif swarm_type == "custom":
            agents = request.get("agents", ["architect", "code_analyst", "quality_engineer"])
            return self.artemis_factory.create_custom_swarm(agents)
        else:
            return self.artemis_factory.create_code_review_swarm()

    async def _pre_execution_integration(
        self, swarm_request: dict[str, Any], context: SwarmExecutionContext
    ):
        """Perform pre-execution integration tasks"""

        # Load relevant data from integrations
        integration_data = {}

        try:
            # Load context from Linear if task-related
            if "linear" in self.integrations and any(
                keyword in swarm_request["content"].lower()
                for keyword in ["task", "issue", "ticket", "bug"]
            ):
                linear_context = await self._load_linear_context(swarm_request["content"])
                if linear_context:
                    integration_data["linear"] = linear_context

            # Load context from Gong if sales-related
            if "gong_training" in self.integrations and any(
                keyword in swarm_request["content"].lower()
                for keyword in ["sales", "deal", "prospect", "customer"]
            ):
                gong_context = await self._load_gong_context(swarm_request["content"])
                if gong_context:
                    integration_data["gong"] = gong_context

            # Update swarm request with integration data
            swarm_request.setdefault("context", {}).update(integration_data)

        except Exception as e:
            logger.warning(f"Failed to load integration context: {e}")

    async def _post_execution_integration(
        self, swarm_result: SwarmResult, context: SwarmExecutionContext
    ):
        """Perform post-execution integration tasks"""

        try:
            # Store results in memory if requested
            if context.store_in_memory:
                await self._store_swarm_results(swarm_result, context)

            # Send notifications if requested
            if context.notify_completion:
                await self._send_completion_notifications(swarm_result, context)

            # Update external integrations if requested
            if context.update_integrations:
                await self._update_external_integrations(swarm_result, context)

        except Exception as e:
            logger.error(f"Post-execution integration failed: {e}")

    async def _load_linear_context(self, content: str) -> Optional[dict[str, Any]]:
        """Load relevant context from Linear"""

        try:
            linear_client = self.integrations.get("linear")
            if not linear_client:
                return None

            # Search for relevant issues
            search_results = await linear_client.search_issues(query=content[:100])

            if search_results:
                return {
                    "relevant_issues": search_results[:5],  # Top 5 results
                    "loaded_at": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Failed to load Linear context: {e}")

        return None

    async def _load_gong_context(self, content: str) -> Optional[dict[str, Any]]:
        """Load relevant context from Gong"""

        try:
            gong_adapter = self.integrations.get("gong_training")
            if not gong_adapter:
                return None

            # Get relevant sales insights
            insights = await gong_adapter.get_sales_insights(query=content[:100])

            if insights:
                return {"sales_insights": insights, "loaded_at": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Failed to load Gong context: {e}")

        return None

    async def _store_swarm_results(self, swarm_result: SwarmResult, context: SwarmExecutionContext):
        """Store swarm results in unified memory"""

        try:
            # Create document chunk
            chunk = DocChunk(
                content=json.dumps(
                    {
                        "execution_id": context.execution_id,
                        "final_output": swarm_result.final_output,
                        "confidence": swarm_result.confidence,
                        "consensus_achieved": swarm_result.consensus_achieved,
                        "total_cost": swarm_result.total_cost,
                        "execution_time_ms": swarm_result.execution_time_ms,
                        "request_source": context.request_source,
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
                source_uri=f"swarm_execution://{context.execution_id}",
                domain=self.domain,
                metadata={
                    "execution_id": context.execution_id,
                    "swarm_domain": self.domain.value,
                    "request_source": context.request_source,
                    "user_id": context.user_id,
                    "success": swarm_result.success,
                    "cost_usd": swarm_result.total_cost,
                },
                confidence=swarm_result.confidence,
            )

            # Store in memory (Unified router)
            await self.memory.upsert_chunks([chunk], self.domain)

            logger.info(f"Stored swarm result in memory: {context.execution_id}")

            # Also store in stdio MCP memory for shared retrieval (Claude/Codex)
            try:
                if getattr(self, "mcp_stdio", None):
                    preview = chunk.content[:6000]
                    swarm_type = (
                        context.integration_context.get("swarm_type")
                        if context.integration_context
                        else None
                    )
                    (
                        context.integration_context.get("task")
                        if context.integration_context
                        else None
                    )
                    base_tags = [
                        "artemis",
                        f"domain:{self.domain.value}",
                        f"swarm:{swarm_type or 'unknown'}",
                        f"execution:{context.execution_id}",
                        "completed",
                    ]
                    # Final result entry
                    self.mcp_stdio.memory_add(
                        topic=f"Swarm Result: {swarm_type or self.domain.value}",
                        content=preview,
                        source="artemis.orchestrator",
                        tags=base_tags,
                        memory_type="semantic",
                    )
                    # Per-role contributions
                    if swarm_result.agent_contributions:
                        for role, msgs in swarm_result.agent_contributions.items():
                            if not msgs:
                                continue
                            role_preview = (
                                msgs[-1].content if hasattr(msgs[-1], "content") else str(msgs[-1])
                            )[:4000]
                            self.mcp_stdio.memory_add(
                                topic=f"Swarm Contribution: {swarm_type or 'unknown'} [{getattr(role, 'value', str(role))}]",
                                content=role_preview,
                                source="artemis.orchestrator",
                                tags=base_tags + [f"role:{getattr(role, 'value', str(role))}"],
                                memory_type="semantic",
                            )
                    # Proposal entry for review-centric swarms
                    if swarm_type and "review" in str(swarm_type):
                        import json as _json

                        proposal_entry = {
                            "proposal_id": f"{context.execution_id}",
                            "swarm_type": swarm_type,
                            "findings": "see contributions entries",
                            "recommendations": swarm_result.final_output[:4000],
                            "confidence": swarm_result.confidence,
                            "status": "pending_review",
                            "files_analyzed": [],
                        }
                        self.mcp_stdio.memory_add(
                            topic=f"Proposal: {swarm_type}",
                            content=_json.dumps(proposal_entry),
                            source="artemis.orchestrator",
                            tags=[
                                "artemis",
                                f"swarm:{swarm_type}",
                                "proposal",
                                "pending_review",
                                f"execution:{context.execution_id}",
                            ],
                            memory_type="procedural",
                        )
                    logger.info("Mirrored swarm result into stdio MCP memory")
            except Exception as e:
                logger.warning(f"Failed to mirror result into stdio MCP memory: {e}")

        except Exception as e:
            logger.error(f"Failed to store swarm results: {e}")

    async def _send_completion_notifications(
        self, swarm_result: SwarmResult, context: SwarmExecutionContext
    ):
        """Send completion notifications"""

        try:
            # Determine notification context
            notification_context = {
                "execution_id": context.execution_id,
                "swarm_domain": self.domain.value,
                "request_source": context.request_source,
                "user_id": context.user_id,
                "channel_id": context.channel_id,
            }

            # Slack delivery only for Sophia
            if self.domain == MemoryDomain.SOPHIA and self.delivery_engine:
                await self.delivery_engine.auto_deliver(swarm_result, notification_context)

            # Direct Slack notification only if source is Slack and Sophia domain
            if (
                self.domain == MemoryDomain.SOPHIA
                and context.request_source == "slack"
                and context.channel_id
            ):
                await self._send_slack_notification(swarm_result, context)

        except Exception as e:
            logger.error(f"Failed to send completion notifications: {e}")

    async def _send_slack_notification(
        self, swarm_result: SwarmResult, context: SwarmExecutionContext
    ):
        """Send direct Slack notification (Sophia only)."""
        try:
            slack_client = self.integrations.get("slack")
            if not slack_client or not context.channel_id:
                return

            emoji = "✅" if swarm_result.success else "❌"
            confidence_pct = int(swarm_result.confidence * 100)
            message = f"""{emoji} Swarm Analysis Complete

Domain: {self.domain.value.title()}
Confidence: {confidence_pct}%
Duration: {swarm_result.execution_time_ms / 60000:.1f} minutes

Results:
{swarm_result.final_output[:500]}{'...' if len(swarm_result.final_output) > 500 else ''}

Execution ID: {context.execution_id}"""

            await slack_client.send_message(channel=context.channel_id, message=message)
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    async def _update_external_integrations(
        self, swarm_result: SwarmResult, context: SwarmExecutionContext
    ):
        """Update external integrations with results"""

        try:
            # Update Linear if task-related and successful
            if (
                swarm_result.success
                and "linear" in context.integration_context
                and "linear" in self.integrations
            ):
                await self._update_linear_integration(swarm_result, context)

            # Update Gong training data if sales-related
            if (
                swarm_result.success
                and self.domain == MemoryDomain.SOPHIA
                and "gong_training" in self.integrations
            ):
                await self._update_gong_integration(swarm_result, context)

        except Exception as e:
            logger.error(f"Failed to update external integrations: {e}")

    async def _update_linear_integration(
        self, swarm_result: SwarmResult, context: SwarmExecutionContext
    ):
        """Update Linear with swarm results"""

        try:
            linear_client = self.integrations.get("linear")
            linear_context = context.integration_context.get("linear", {})

            if not linear_client or not linear_context.get("relevant_issues"):
                return

            # Add comment to relevant issues
            for issue in linear_context["relevant_issues"][:2]:  # Top 2 issues
                comment = f"""🤖 **AI Swarm Analysis**

{swarm_result.final_output[:1000]}

*Confidence: {int(swarm_result.confidence * 100)}% | Execution ID: {context.execution_id}*"""

                await linear_client.add_comment(issue_id=issue["id"], comment=comment)

        except Exception as e:
            logger.error(f"Failed to update Linear integration: {e}")

    async def _update_gong_integration(
        self, swarm_result: SwarmResult, context: SwarmExecutionContext
    ):
        """Update Gong with swarm insights"""

        try:
            gong_adapter = self.integrations.get("gong_training")
            if not gong_adapter:
                return

            # Extract sales insights from swarm result
            insights = {
                "content": swarm_result.final_output,
                "confidence": swarm_result.confidence,
                "execution_id": context.execution_id,
                "generated_at": datetime.now().isoformat(),
                "domain": "business_intelligence",
            }

            await gong_adapter.store_ai_insights(insights)

        except Exception as e:
            logger.error(f"Failed to update Gong integration: {e}")

    async def _process_swarm_result(
        self, swarm_result: SwarmResult, context: SwarmExecutionContext
    ) -> Result:
        """Process swarm result into orchestrator result format"""

        return Result(
            success=swarm_result.success,
            content=swarm_result.final_output,
            metadata={
                "execution_id": context.execution_id,
                "swarm_domain": self.domain.value,
                "confidence": swarm_result.confidence,
                "consensus_achieved": swarm_result.consensus_achieved,
                "iterations_used": swarm_result.iterations_used,
                "agent_contributions": len(swarm_result.agent_contributions),
                "reasoning_chain_length": len(swarm_result.reasoning_chain),
            },
            confidence=swarm_result.confidence,
            cost=swarm_result.total_cost,
            execution_time_ms=swarm_result.execution_time_ms,
            errors=swarm_result.errors if hasattr(swarm_result, "errors") else [],
        )

    # Public API methods

    async def execute_swarm(
        self,
        content: str,
        swarm_type: str = "auto_detect",
        context: Optional[dict[str, Any]] = None,
        user_id: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> Result:
        """Execute swarm with full integration support"""

        task = Task(
            id=f"integrated_swarm_{int(datetime.now().timestamp())}",
            type=TaskType.ORCHESTRATION,
            content=content,
            metadata={
                "swarm_type": swarm_type,
                "source": "api",
                "user_id": user_id,
                "channel_id": channel_id,
                "context": context or {},
            },
        )

        return await self.execute(task)

    async def schedule_recurring_swarm(
        self, content: str, swarm_type: str, interval_hours: int = 24, **kwargs
    ) -> str:
        """Schedule recurring swarm execution"""

        from app.swarms.core.scheduler import Priority, ScheduledTask, ScheduleType

        task = ScheduledTask(
            task_id=f"recurring_swarm_{int(datetime.now().timestamp())}",
            name=f"Recurring {self.domain.value.title()} Analysis",
            description=f"Recurring {swarm_type} analysis for {self.domain.value} domain",
            swarm_type=f"{self.domain.value}.{swarm_type}",
            task_content=content,
            schedule_type=ScheduleType.RECURRING,
            interval_minutes=interval_hours * 60,
            priority=kwargs.get("priority", Priority.NORMAL),
            max_cost_usd=kwargs.get("max_cost", 3.0),
            timeout_minutes=kwargs.get("timeout_minutes", 15),
            context=kwargs.get("context", {}),
        )

        return self.scheduler.schedule_task(task)

    def get_integration_status(self) -> dict[str, Any]:
        """Get status of all integrations"""

        status = {
            "orchestrator": {
                "domain": self.domain.value,
                "active_swarms": len(self.active_swarms),
                "total_processed": len(self._task_history),
            },
            "integrations": {},
        }

        # Check integration health
        for name, integration in self.integrations.items():
            try:
                # Simple health check (could be enhanced)
                status["integrations"][name] = {
                    "available": integration is not None,
                    "type": type(integration).__name__,
                    "last_checked": datetime.now().isoformat(),
                }
            except Exception as e:
                status["integrations"][name] = {"available": False, "error": str(e)}

        return status


# Factory functions for creating integrated orchestrators


def create_sophia_orchestrator() -> IntegratedSwarmOrchestrator:
    """Create integrated Sophia orchestrator"""
    return IntegratedSwarmOrchestrator(MemoryDomain.SOPHIA)


def create_artemis_orchestrator() -> IntegratedSwarmOrchestrator:
    """Create integrated Artemis orchestrator"""
    return IntegratedSwarmOrchestrator(MemoryDomain.ARTEMIS)


# Global orchestrator instances
_sophia_orchestrator = None
_artemis_orchestrator = None


def get_sophia_orchestrator() -> IntegratedSwarmOrchestrator:
    """Get global Sophia orchestrator instance"""
    global _sophia_orchestrator
    if _sophia_orchestrator is None:
        _sophia_orchestrator = create_sophia_orchestrator()
    return _sophia_orchestrator


def get_artemis_orchestrator() -> IntegratedSwarmOrchestrator:
    """Get global Artemis orchestrator instance"""
    global _artemis_orchestrator
    if _artemis_orchestrator is None:
        _artemis_orchestrator = create_artemis_orchestrator()
    return _artemis_orchestrator
