"""
Model Approval Dashboard - Centralized Control for AI Model Usage
Allows enabling/disabling specific models per orchestrator and agent
"""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
class ApprovalStatus(Enum):
    """Model approval status"""
    APPROVED = "approved"
    RESTRICTED = "restricted"  # Needs special permission
    DISABLED = "disabled"
    TESTING = "testing"
@dataclass
class ModelApproval:
    """Model approval configuration"""
    model_id: str
    status: ApprovalStatus
    allowed_orchestrators: set[str] = field(default_factory=set)
    allowed_agents: set[str] = field(default_factory=set)
    cost_tier: str = "standard"
    max_tokens_per_request: int = 32768
    requires_approval_above: int = 100000  # Token threshold
    notes: str = ""
    last_updated: str = ""
class ModelApprovalDashboard:
    """Dashboard for managing model approvals across the system"""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.config_file = "model_approvals.json"
            self.approvals = self._initialize_approvals()
            self.usage_tracking = {}
            self.cost_tracking = {}
    def _initialize_approvals(self) -> dict[str, ModelApproval]:
        """Initialize model approval configurations"""
        # Default approval configuration based on your priorities
        default_approvals = {
            # GPT-5 Series - RESTRICTED (Orchestrators only)
            "gpt-5": ModelApproval(
                model_id="gpt-5",
                status=ApprovalStatus.RESTRICTED,
                allowed_orchestrators={"", "sophia", "master"},
                allowed_agents=set(),
                cost_tier="premium",
                max_tokens_per_request=65536,
                notes="Primary orchestrator model - use sparingly",
            ),
            # Grok Series - APPROVED with restrictions
            "grok-4-heavy": ModelApproval(
                model_id="grok-4-heavy",
                status=ApprovalStatus.RESTRICTED,
                allowed_orchestrators={"master", "", "sophia"},
                allowed_agents={"reasoning_council", "complex_solver"},
                cost_tier="premium",
                max_tokens_per_request=100000,
                notes="5-10x compute - only for complex multi-agent problems",
            ),
            "grok-4": ModelApproval(
                model_id="grok-4",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={"", "sophia"},
                allowed_agents={"analyzer", "researcher"},
                cost_tier="standard",
                max_tokens_per_request=32768,
            ),
            "grok-code-fast-1": ModelApproval(
                model_id="grok-code-fast-1",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={""},
                allowed_agents={"coder", "speed_coder", "code_reviewer"},
                cost_tier="economy",
                max_tokens_per_request=32768,
                notes="92 tokens/sec - primary for all coding tasks",
            ),
            "grok-3-mini": ModelApproval(
                model_id="grok-3-mini",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={"", "sophia"},
                allowed_agents={"quick_responder", "simple_tasks"},
                cost_tier="economy",
                max_tokens_per_request=8192,
                notes="Cost-effective for simple tasks",
            ),
            # Claude 4 Series - APPROVED
            "claude-opus-4.1": ModelApproval(
                model_id="claude-opus-4.1",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={"", "sophia", "master"},
                allowed_agents={"strategist", "business_analyst", "strategic_thinker"},
                cost_tier="premium",
                max_tokens_per_request=65536,
                notes="Strategic reasoning and business analysis",
            ),
            "claude-sonnet-4": ModelApproval(
                model_id="claude-sonnet-4",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={"", "sophia"},
                allowed_agents={"general"},
                cost_tier="standard",
                max_tokens_per_request=32768,
            ),
            # Qwen3-Coder - APPROVED for large context
            "qwen3-coder-480b": ModelApproval(
                model_id="qwen3-coder-480b",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={""},
                allowed_agents={"context_master", "large_codebase_analyzer"},
                cost_tier="standard",
                max_tokens_per_request=256000,
                requires_approval_above=100000,
                notes="Use for >100K token contexts only",
            ),
            # GLM Series - APPROVED
            "glm-4.5": ModelApproval(
                model_id="glm-4.5",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={"", "sophia"},
                allowed_agents={"reasoner", "deep_thinker"},
                cost_tier="standard",
                max_tokens_per_request=65536,
            ),
            "glm-4.5-air": ModelApproval(
                model_id="glm-4.5-air",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={""},
                allowed_agents={"quick_fixer", "rapid_response"},
                cost_tier="economy",
                max_tokens_per_request=16384,
            ),
            # Llama-4 Series - APPROVED
            "llama-4-maverick": ModelApproval(
                model_id="llama-4-maverick",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={"", "sophia"},
                allowed_agents={"deep_analyzer", "multimodal"},
                cost_tier="standard",
                max_tokens_per_request=32768,
            ),
            "llama-4-scout": ModelApproval(
                model_id="llama-4-scout",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={""},
                allowed_agents={"pattern_scout", "repo_scanner"},
                cost_tier="standard",
                max_tokens_per_request=16384,
            ),
            # Gemini 2.5 Series - APPROVED
            "gemini-2.5-pro": ModelApproval(
                model_id="gemini-2.5-pro",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={"sophia"},
                allowed_agents={"analyst", "researcher"},
                cost_tier="standard",
                max_tokens_per_request=32768,
            ),
            "gemini-2.5-flash": ModelApproval(
                model_id="gemini-2.5-flash",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={""},
                allowed_agents={"quick_scanner", "repo_scout"},
                cost_tier="economy",
                max_tokens_per_request=16384,
                notes="Fast repository scanning",
            ),
            # DeepSeek V3.1 - APPROVED
            "deepseek-reasoner-v3.1": ModelApproval(
                model_id="deepseek-reasoner-v3.1",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={""},
                allowed_agents={"reasoner", "code_analyst"},
                cost_tier="standard",
                max_tokens_per_request=32768,
            ),
            "deepseek-r1": ModelApproval(
                model_id="deepseek-r1",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={"sophia"},
                allowed_agents={"researcher", "analyst"},
                cost_tier="standard",
                max_tokens_per_request=32768,
            ),
            # Perplexity - APPROVED
            "sonar-pro": ModelApproval(
                model_id="sonar-pro",
                status=ApprovalStatus.APPROVED,
                allowed_orchestrators={"sophia"},
                allowed_agents={"researcher", "market_analyst"},
                cost_tier="standard",
                max_tokens_per_request=16384,
                notes="Web search with 2x citations",
            ),
            # DISABLED Models (Removed from system)
            "claude-3.5-sonnet": ModelApproval(
                model_id="claude-3.5-sonnet",
                status=ApprovalStatus.DISABLED,
                allowed_orchestrators=set(),
                allowed_agents=set(),
                notes="DEPRECATED - Use Claude Opus 4.1 instead",
            ),
            "grok-2": ModelApproval(
                model_id="grok-2",
                status=ApprovalStatus.DISABLED,
                allowed_orchestrators=set(),
                allowed_agents=set(),
                notes="DEPRECATED - Use Grok-4 series instead",
            ),
        }
        # Load from file if exists
        if os.path.exists(self.config_file):
            return self._load_approvals()
        # Set timestamps
        timestamp = datetime.now().isoformat()
        for approval in default_approvals.values():
            approval.last_updated = timestamp
        return default_approvals
    def is_model_approved(
        self,
        model_id: str,
        orchestrator: Optional[str] = None,
        agent: Optional[str] = None,
        token_count: int = 0,
    ) -> bool:
        """Check if a model is approved for use"""
        if model_id not in self.approvals:
            return False
        approval = self.approvals[model_id]
        # Check if disabled
        if approval.status == ApprovalStatus.DISABLED:
            return False
        # Check orchestrator permission
        if orchestrator and orchestrator not in approval.allowed_orchestrators:
            return False
        # Check agent permission
        if agent and agent not in approval.allowed_agents:
            return False
        # Check token limit
        if token_count > approval.requires_approval_above:
            return False  # Would need special approval
        return True
    def get_approved_models(
        self,
        orchestrator: Optional[str] = None,
        agent: Optional[str] = None,
        cost_tier: Optional[str] = None,
    ) -> list[str]:
        """Get list of approved models for specific context"""
        approved = []
        for model_id, approval in self.approvals.items():
            if approval.status == ApprovalStatus.DISABLED:
                continue
            if orchestrator and orchestrator not in approval.allowed_orchestrators:
                continue
            if agent and agent not in approval.allowed_agents:
                continue
            if cost_tier and approval.cost_tier != cost_tier:
                continue
            approved.append(model_id)
        return approved
    def update_approval(
        self,
        model_id: str,
        status: Optional[ApprovalStatus] = None,
        add_orchestrator: Optional[str] = None,
        remove_orchestrator: Optional[str] = None,
        add_agent: Optional[str] = None,
        remove_agent: Optional[str] = None,
    ) -> bool:
        """Update model approval settings"""
        if model_id not in self.approvals:
            return False
        approval = self.approvals[model_id]
        if status:
            approval.status = status
        if add_orchestrator:
            approval.allowed_orchestrators.add(add_orchestrator)
        if (
            remove_orchestrator
            and remove_orchestrator in approval.allowed_orchestrators
        ):
            approval.allowed_orchestrators.remove(remove_orchestrator)
        if add_agent:
            approval.allowed_agents.add(add_agent)
        if remove_agent and remove_agent in approval.allowed_agents:
            approval.allowed_agents.remove(remove_agent)
        approval.last_updated = datetime.now().isoformat()
        # Save to file
        self._save_approvals()
        return True
    def track_usage(self, model_id: str, tokens: int, cost: float):
        """Track model usage for monitoring"""
        if model_id not in self.usage_tracking:
            self.usage_tracking[model_id] = {
                "total_tokens": 0,
                "total_requests": 0,
                "total_cost": 0.0,
            }
        self.usage_tracking[model_id]["total_tokens"] += tokens
        self.usage_tracking[model_id]["total_requests"] += 1
        self.usage_tracking[model_id]["total_cost"] += cost
    def get_usage_report(self) -> dict[str, Any]:
        """Get usage report for all models"""
        report = {
            "by_model": self.usage_tracking,
            "by_cost_tier": {},
            "total_cost": sum(m["total_cost"] for m in self.usage_tracking.values()),
            "total_tokens": sum(
                m["total_tokens"] for m in self.usage_tracking.values()
            ),
        }
        # Group by cost tier
        for model_id, usage in self.usage_tracking.items():
            if model_id in self.approvals:
                tier = self.approvals[model_id].cost_tier
                if tier not in report["by_cost_tier"]:
                    report["by_cost_tier"][tier] = {"cost": 0, "tokens": 0}
                report["by_cost_tier"][tier]["cost"] += usage["total_cost"]
                report["by_cost_tier"][tier]["tokens"] += usage["total_tokens"]
        return report
    def get_dashboard_summary(self) -> dict[str, Any]:
        """Get dashboard summary"""
        summary = {
            "total_models": len(self.approvals),
            "approved": len(
                [
                    a
                    for a in self.approvals.values()
                    if a.status == ApprovalStatus.APPROVED
                ]
            ),
            "restricted": len(
                [
                    a
                    for a in self.approvals.values()
                    if a.status == ApprovalStatus.RESTRICTED
                ]
            ),
            "disabled": len(
                [
                    a
                    for a in self.approvals.values()
                    if a.status == ApprovalStatus.DISABLED
                ]
            ),
            "cost_tiers": {"economy": [], "standard": [], "premium": []},
            "orchestrator_access": {},
            "recommendations": [],
        }
        # Group by cost tier
        for model_id, approval in self.approvals.items():
            if approval.status != ApprovalStatus.DISABLED:
                summary["cost_tiers"][approval.cost_tier].append(model_id)
        # Orchestrator access
        for orch in ["", "sophia", "master"]:
            summary["orchestrator_access"][orch] = self.get_approved_models(
                orchestrator=orch
            )
        # Recommendations
        if "grok-code-fast-1" in self.approvals:
            summary["recommendations"].append(
                "Use Grok Code Fast 1 for all simple coding tasks (90% cost savings)"
            )
        if "gpt-5" in self.approvals:
            summary["recommendations"].append("Reserve GPT-5 for orchestration only")
        if "grok-4-heavy" in self.approvals:
            summary["recommendations"].append(
                "Use Grok 4 Heavy only for problems requiring multi-agent reasoning"
            )
        return summary
    def _save_approvals(self):
        """Save approvals to file"""
        data = {
            model_id: {
                "status": approval.status.value,
                "allowed_orchestrators": list(approval.allowed_orchestrators),
                "allowed_agents": list(approval.allowed_agents),
                "cost_tier": approval.cost_tier,
                "max_tokens_per_request": approval.max_tokens_per_request,
                "requires_approval_above": approval.requires_approval_above,
                "notes": approval.notes,
                "last_updated": approval.last_updated,
            }
            for model_id, approval in self.approvals.items()
        }
        with open(self.config_file, "w") as f:
            json.dump(data, f, indent=2)
    def _load_approvals(self) -> dict[str, ModelApproval]:
        """Load approvals from file"""
        with open(self.config_file) as f:
            data = json.load(f)
        approvals = {}
        for model_id, config in data.items():
            approvals[model_id] = ModelApproval(
                model_id=model_id,
                status=ApprovalStatus(config["status"]),
                allowed_orchestrators=set(config["allowed_orchestrators"]),
                allowed_agents=set(config["allowed_agents"]),
                cost_tier=config["cost_tier"],
                max_tokens_per_request=config["max_tokens_per_request"],
                requires_approval_above=config["requires_approval_above"],
                notes=config["notes"],
                last_updated=config["last_updated"],
            )
        return approvals
# Singleton instance
model_dashboard = ModelApprovalDashboard()
