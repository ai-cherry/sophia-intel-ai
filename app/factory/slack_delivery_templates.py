"""
Advanced Slack Delivery Templates and Configurations
Pre-configured delivery templates for different swarm types and business contexts
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from app.swarms.core.micro_swarm_base import AgentRole
from app.swarms.core.slack_delivery import (
    DeliveryConfig,
    DeliveryFormat,
    DeliveryPriority,
    DeliveryRule,
)

logger = logging.getLogger(__name__)


@dataclass
class SlackChannelConfig:
    """Configuration for Slack channels"""

    channel_id: str
    channel_name: str
    description: str
    primary_purpose: str
    audience: list[str]
    notification_level: DeliveryPriority
    business_hours_only: bool = True
    auto_thread: bool = True
    max_messages_per_day: int = 20


@dataclass
class MessageTemplate:
    """Template for formatted Slack messages"""

    template_id: str
    name: str
    description: str
    format_string: str
    required_variables: list[str]
    optional_variables: list[str] = field(default_factory=list)
    default_values: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


class SlackDeliveryTemplateManager:
    """
    Manages pre-configured Slack delivery templates for different contexts
    """

    def __init__(self):
        self.channel_configs: dict[str, SlackChannelConfig] = {}
        self.message_templates: dict[str, MessageTemplate] = {}
        self.delivery_configs: dict[str, DeliveryConfig] = {}

        # Initialize default configurations
        self._initialize_channel_configs()
        self._initialize_message_templates()
        self._initialize_delivery_configs()

        logger.info("Slack delivery template manager initialized")

    def _initialize_channel_configs(self):
        """Initialize Slack channel configurations"""

        # Executive channels
        self.channel_configs["executive-reports"] = SlackChannelConfig(
            channel_id="#executive-reports",
            channel_name="Executive Reports",
            description="High-level business intelligence and strategic reports for executives",
            primary_purpose="executive_briefing",
            audience=["ceo", "cto", "executives", "board_members"],
            notification_level=DeliveryPriority.HIGH,
            business_hours_only=False,  # Executives may want early morning reports
            max_messages_per_day=5,
        )

        self.channel_configs["strategy-insights"] = SlackChannelConfig(
            channel_id="#strategy-insights",
            channel_name="Strategy Insights",
            description="Strategic analysis, market insights, and competitive intelligence",
            primary_purpose="strategic_analysis",
            audience=["strategy_team", "product_managers", "executives"],
            notification_level=DeliveryPriority.HIGH,
            business_hours_only=True,
            max_messages_per_day=8,
        )

        # Technical channels
        self.channel_configs["artemis-command"] = SlackChannelConfig(
            channel_id="#artemis-command",
            channel_name="Artemis Command Center",
            description="Technical operations, code analysis, and system status updates",
            primary_purpose="technical_operations",
            audience=["developers", "devops", "tech_leads"],
            notification_level=DeliveryPriority.NORMAL,
            business_hours_only=True,
            auto_thread=True,
            max_messages_per_day=15,
        )

        self.channel_configs["code-quality"] = SlackChannelConfig(
            channel_id="#code-quality",
            channel_name="Code Quality Alerts",
            description="Automated code quality assessments and improvement recommendations",
            primary_purpose="quality_monitoring",
            audience=["developers", "code_reviewers", "tech_leads"],
            notification_level=DeliveryPriority.NORMAL,
            business_hours_only=True,
            max_messages_per_day=12,
        )

        # Business operations channels
        self.channel_configs["daily-intelligence"] = SlackChannelConfig(
            channel_id="#daily-intelligence",
            channel_name="Daily Business Intelligence",
            description="Daily business metrics, trends, and operational insights",
            primary_purpose="daily_operations",
            audience=["business_analysts", "operations", "managers"],
            notification_level=DeliveryPriority.NORMAL,
            business_hours_only=True,
            max_messages_per_day=3,
        )

        self.channel_configs["market-watch"] = SlackChannelConfig(
            channel_id="#market-watch",
            channel_name="Market Intelligence",
            description="Market trends, competitive analysis, and industry insights",
            primary_purpose="market_intelligence",
            audience=["business_development", "sales", "marketing"],
            notification_level=DeliveryPriority.NORMAL,
            business_hours_only=True,
            max_messages_per_day=6,
        )

        # Alert channels
        self.channel_configs["critical-alerts"] = SlackChannelConfig(
            channel_id="#critical-alerts",
            channel_name="Critical System Alerts",
            description="Critical issues requiring immediate attention",
            primary_purpose="emergency_alerts",
            audience=["oncall", "sre", "tech_leads", "executives"],
            notification_level=DeliveryPriority.URGENT,
            business_hours_only=False,
            max_messages_per_day=50,  # High limit for alerts
        )

        self.channel_configs["cost-monitoring"] = SlackChannelConfig(
            channel_id="#cost-monitoring",
            channel_name="Cost Monitoring",
            description="Cost tracking, budget alerts, and resource utilization",
            primary_purpose="cost_management",
            audience=["finance", "operations", "executives"],
            notification_level=DeliveryPriority.HIGH,
            business_hours_only=True,
            max_messages_per_day=10,
        )

    def _initialize_message_templates(self):
        """Initialize message templates for different contexts"""

        # Executive Summary Template
        self.message_templates["executive_summary"] = MessageTemplate(
            template_id="executive_summary",
            name="Executive Business Summary",
            description="Concise business summary for executive consumption",
            format_string="""📊 **Executive Brief - {date}**

🎯 **Key Insights:**
{key_insights}

📈 **Business Impact:**
{business_impact}

⚠️ **Critical Issues:** {critical_issues}
✅ **Opportunities:** {opportunities}

💡 **Recommended Actions:**
{recommended_actions}

*Analysis by {swarm_name} | Confidence: {confidence}% | Cost: ${cost}*
{mentions}""",
            required_variables=[
                "date",
                "key_insights",
                "business_impact",
                "swarm_name",
                "confidence",
                "cost",
            ],
            optional_variables=[
                "critical_issues",
                "opportunities",
                "recommended_actions",
                "mentions",
            ],
            default_values={
                "critical_issues": "None identified",
                "opportunities": "See analysis for details",
                "recommended_actions": "Review analysis and take appropriate action",
                "mentions": "",
            },
            tags=["executive", "summary", "business"],
        )

        # Daily Intelligence Template
        self.message_templates["daily_intelligence"] = MessageTemplate(
            template_id="daily_intelligence",
            name="Daily Intelligence Report",
            description="Daily business intelligence and operational insights",
            format_string="""🌅 **Daily Intelligence - {date}**

📊 **Today's Metrics:**
{daily_metrics}

📈 **Trends & Patterns:**
{trends}

🎯 **Focus Areas:**
{focus_areas}

🚨 **Watch Items:**
{watch_items}

*Generated by {swarm_name} at {timestamp}*
*Confidence: {confidence}% | Analysis Cost: ${cost}*""",
            required_variables=[
                "date",
                "daily_metrics",
                "trends",
                "focus_areas",
                "swarm_name",
                "timestamp",
                "confidence",
                "cost",
            ],
            optional_variables=["watch_items"],
            default_values={"watch_items": "No critical items flagged"},
            tags=["daily", "intelligence", "operations"],
        )

        # Technical Operations Template
        self.message_templates["technical_ops"] = MessageTemplate(
            template_id="technical_ops",
            name="Technical Operations Report",
            description="Technical analysis and operational status report",
            format_string="""⚙️ **{operation_type} - {timestamp}**

🔍 **Analysis Results:**
{analysis_results}

🛠️ **Technical Findings:**
{technical_findings}

📊 **Quality Metrics:**
{quality_metrics}

🎯 **Action Items:**
{action_items}

**System Performance:**
• Execution Time: {execution_time}ms
• Models Used: {models_used}
• Token Usage: {token_usage}
• Cost: ${cost}

*Operated by {swarm_name} | Unit: {unit_designation}*""",
            required_variables=[
                "operation_type",
                "timestamp",
                "analysis_results",
                "technical_findings",
                "quality_metrics",
                "action_items",
                "execution_time",
                "models_used",
                "token_usage",
                "cost",
                "swarm_name",
            ],
            optional_variables=["unit_designation"],
            default_values={"unit_designation": "Artemis Operations"},
            tags=["technical", "operations", "analysis"],
        )

        # Strategic Analysis Template
        self.message_templates["strategic_analysis"] = MessageTemplate(
            template_id="strategic_analysis",
            name="Strategic Analysis Report",
            description="Deep strategic analysis with recommendations",
            format_string="""🧠 **Strategic Analysis - {analysis_type}**

🎯 **Strategic Context:**
{strategic_context}

🔮 **Future Outlook:**
{future_outlook}

⚖️ **Risk Assessment:**
{risk_assessment}

🚀 **Strategic Recommendations:**
{strategic_recommendations}

📋 **Implementation Priorities:**
{implementation_priorities}

---
*Analysis conducted by {analyst_agents}*
*Strategic oversight by {strategist_agents}*
*Validation by {validator_agents}*

**Analysis Metrics:**
• Confidence Level: {confidence}%
• Consensus Achieved: {consensus_status}
• Analysis Depth: {analysis_depth}
• Total Cost: ${cost}*""",
            required_variables=[
                "analysis_type",
                "strategic_context",
                "future_outlook",
                "risk_assessment",
                "strategic_recommendations",
                "implementation_priorities",
                "analyst_agents",
                "strategist_agents",
                "validator_agents",
                "confidence",
                "consensus_status",
                "analysis_depth",
                "cost",
            ],
            optional_variables=[],
            default_values={},
            tags=["strategic", "analysis", "planning"],
        )

        # Alert Template
        self.message_templates["critical_alert"] = MessageTemplate(
            template_id="critical_alert",
            name="Critical Alert Notification",
            description="Critical issue alert requiring immediate attention",
            format_string="""🚨 **CRITICAL ALERT** 🚨

**Issue:** {issue_title}
**Severity:** {severity_level}
**Detected:** {detection_time}

**Impact:**
{impact_description}

**Immediate Actions Required:**
{immediate_actions}

**Analysis:**
{analysis_summary}

**Confidence:** {confidence}% | **Response Time:** {response_time}ms

<!channel> - Immediate attention required
{oncall_mentions}""",
            required_variables=[
                "issue_title",
                "severity_level",
                "detection_time",
                "impact_description",
                "immediate_actions",
                "analysis_summary",
                "confidence",
                "response_time",
            ],
            optional_variables=["oncall_mentions"],
            default_values={"oncall_mentions": ""},
            tags=["alert", "critical", "emergency"],
        )

        # Cost Monitoring Template
        self.message_templates["cost_monitoring"] = MessageTemplate(
            template_id="cost_monitoring",
            name="Cost Monitoring Report",
            description="Cost tracking and budget monitoring report",
            format_string="""💰 **Cost Monitoring Report - {period}**

📊 **Current Usage:**
• Daily Spend: ${daily_cost}
• Monthly Spend: ${monthly_cost}
• Budget Utilization: {budget_utilization}%

📈 **Trends:**
{cost_trends}

🎯 **Top Cost Drivers:**
{top_cost_drivers}

⚠️ **Budget Alerts:**
{budget_alerts}

💡 **Cost Optimization Opportunities:**
{optimization_opportunities}

*Report generated at {timestamp}*
*Next report: {next_report_time}*""",
            required_variables=[
                "period",
                "daily_cost",
                "monthly_cost",
                "budget_utilization",
                "cost_trends",
                "top_cost_drivers",
                "budget_alerts",
                "optimization_opportunities",
                "timestamp",
                "next_report_time",
            ],
            optional_variables=[],
            default_values={},
            tags=["cost", "monitoring", "budget"],
        )

    def _initialize_delivery_configs(self):
        """Initialize delivery configurations for different purposes"""

        # Executive Reports Configuration
        self.delivery_configs["executive_reports"] = DeliveryConfig(
            channel="#executive-reports",
            format=DeliveryFormat.EXECUTIVE,
            priority=DeliveryPriority.HIGH,
            include_reasoning=False,
            include_confidence=True,
            include_cost=False,  # Hide costs from executives
            max_length=2000,
            mention_roles=["executives"],
            custom_template=self.message_templates["executive_summary"].format_string,
            enable_threading=True,
            auto_summarize_long_content=True,
        )

        # Daily Intelligence Configuration
        self.delivery_configs["daily_intelligence"] = DeliveryConfig(
            channel="#daily-intelligence",
            format=DeliveryFormat.SUMMARY,
            priority=DeliveryPriority.NORMAL,
            include_reasoning=False,
            include_confidence=True,
            include_cost=True,
            max_length=3000,
            custom_template=self.message_templates["daily_intelligence"].format_string,
            enable_threading=True,
            auto_summarize_long_content=True,
        )

        # Technical Operations Configuration
        self.delivery_configs["technical_operations"] = DeliveryConfig(
            channel="#artemis-command",
            format=DeliveryFormat.TECHNICAL,
            priority=DeliveryPriority.NORMAL,
            include_reasoning=True,
            include_confidence=True,
            include_cost=True,
            max_length=4000,
            mention_users=["tech-leads"],
            custom_template=self.message_templates["technical_ops"].format_string,
            enable_threading=True,
        )

        # Strategic Analysis Configuration
        self.delivery_configs["strategic_analysis"] = DeliveryConfig(
            channel="#strategy-insights",
            format=DeliveryFormat.DETAILED,
            priority=DeliveryPriority.HIGH,
            include_reasoning=True,
            include_confidence=True,
            include_cost=False,
            max_length=5000,
            mention_roles=["strategy-team"],
            custom_template=self.message_templates["strategic_analysis"].format_string,
            enable_threading=True,
            auto_summarize_long_content=True,
        )

        # Critical Alerts Configuration
        self.delivery_configs["critical_alerts"] = DeliveryConfig(
            channel="#critical-alerts",
            format=DeliveryFormat.SUMMARY,
            priority=DeliveryPriority.URGENT,
            include_reasoning=True,
            include_confidence=True,
            include_cost=False,
            max_length=2000,
            mention_roles=["oncall", "sre"],
            custom_template=self.message_templates["critical_alert"].format_string,
            enable_threading=False,  # Don't thread urgent alerts
            auto_summarize_long_content=False,  # Keep full context for alerts
        )

        # Cost Monitoring Configuration
        self.delivery_configs["cost_monitoring"] = DeliveryConfig(
            channel="#cost-monitoring",
            format=DeliveryFormat.DETAILED,
            priority=DeliveryPriority.HIGH,
            include_reasoning=False,
            include_confidence=False,
            include_cost=True,  # Cost reports should show costs
            max_length=3000,
            mention_roles=["finance"],
            custom_template=self.message_templates["cost_monitoring"].format_string,
            enable_threading=True,
        )

        # Code Quality Configuration
        self.delivery_configs["code_quality"] = DeliveryConfig(
            channel="#code-quality",
            format=DeliveryFormat.TECHNICAL,
            priority=DeliveryPriority.NORMAL,
            include_reasoning=True,
            include_confidence=True,
            include_cost=True,
            max_length=3500,
            mention_users=["code-reviewers"],
            enable_threading=True,
            auto_summarize_long_content=True,
        )

    def get_delivery_config(self, config_name: str) -> Optional[DeliveryConfig]:
        """Get a delivery configuration by name"""
        return self.delivery_configs.get(config_name)

    def get_message_template(self, template_id: str) -> Optional[MessageTemplate]:
        """Get a message template by ID"""
        return self.message_templates.get(template_id)

    def get_channel_config(self, channel_id: str) -> Optional[SlackChannelConfig]:
        """Get channel configuration"""
        return self.channel_configs.get(channel_id)

    def create_delivery_rules(self) -> list[DeliveryRule]:
        """Create delivery rules based on configurations"""

        rules = []

        # Executive reports rule
        rules.append(
            DeliveryRule(
                rule_id="executive_intelligence",
                name="Executive Intelligence Delivery",
                description="Deliver high-confidence business intelligence to executives",
                swarm_types=[
                    "mythology_business",
                    "mythology_strategic",
                    "mythology_comprehensive",
                ],
                agent_roles=[AgentRole.STRATEGIST],
                confidence_threshold=0.85,
                keywords=["business", "strategic", "executive", "leadership"],
                time_ranges=[
                    {"start_hour": 7, "end_hour": 9},
                    {"start_hour": 17, "end_hour": 19},
                ],
                delivery_config=self.delivery_configs["executive_reports"],
                enabled=True,
            )
        )

        # Daily operations rule
        rules.append(
            DeliveryRule(
                rule_id="daily_operations",
                name="Daily Operations Intelligence",
                description="Daily business intelligence for operations teams",
                swarm_types=["mythology_business", "hybrid_tactical"],
                confidence_threshold=0.75,
                keywords=["daily", "operations", "business", "metrics"],
                time_ranges=[{"start_hour": 8, "end_hour": 10}],
                delivery_config=self.delivery_configs["daily_intelligence"],
                enabled=True,
            )
        )

        # Technical operations rule
        rules.append(
            DeliveryRule(
                rule_id="technical_operations",
                name="Technical Operations Updates",
                description="Technical analysis and operations updates",
                swarm_types=["military_recon", "military_strike", "military_qc"],
                agent_roles=[AgentRole.ANALYST, AgentRole.VALIDATOR],
                confidence_threshold=0.70,
                keywords=["code", "technical", "system", "quality"],
                time_ranges=[{"start_hour": 9, "end_hour": 17}],
                delivery_config=self.delivery_configs["technical_operations"],
                enabled=True,
            )
        )

        # Strategic analysis rule
        rules.append(
            DeliveryRule(
                rule_id="strategic_insights",
                name="Strategic Insights Delivery",
                description="Strategic analysis and insights for planning teams",
                swarm_types=["mythology_strategic", "hybrid_tactical"],
                agent_roles=[AgentRole.STRATEGIST],
                confidence_threshold=0.80,
                cost_threshold=5.0,  # Only for significant analyses
                keywords=["strategy", "strategic", "planning", "competitive"],
                time_ranges=[{"start_hour": 9, "end_hour": 18}],
                delivery_config=self.delivery_configs["strategic_analysis"],
                enabled=True,
            )
        )

        # Critical alerts rule
        rules.append(
            DeliveryRule(
                rule_id="critical_alerts",
                name="Critical System Alerts",
                description="Immediate alerts for critical issues",
                keywords=["critical", "urgent", "alert", "failure", "error", "breach"],
                confidence_threshold=0.9,  # High confidence required for alerts
                delivery_config=self.delivery_configs["critical_alerts"],
                enabled=True,
            )
        )

        # Code quality rule
        rules.append(
            DeliveryRule(
                rule_id="code_quality_updates",
                name="Code Quality Updates",
                description="Regular code quality assessments and recommendations",
                swarm_types=["military_recon", "military_qc", "military_review"],
                agent_roles=[AgentRole.ANALYST, AgentRole.VALIDATOR],
                confidence_threshold=0.70,
                keywords=["code", "quality", "review", "scan", "analysis"],
                time_ranges=[{"start_hour": 9, "end_hour": 17}],
                delivery_config=self.delivery_configs["code_quality"],
                enabled=True,
            )
        )

        return rules

    def format_message_with_template(
        self, template_id: str, variables: dict[str, Any]
    ) -> str:
        """Format a message using a template"""

        template = self.message_templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Merge with default values
        format_vars = {**template.default_values, **variables}

        # Check required variables
        missing_vars = [
            var for var in template.required_variables if var not in format_vars
        ]
        if missing_vars:
            raise ValueError(
                f"Missing required variables for template {template_id}: {missing_vars}"
            )

        try:
            return template.format_string.format(**format_vars)
        except KeyError as e:
            raise ValueError(f"Template formatting error for {template_id}: {e}")

    def get_appropriate_delivery_config(
        self, swarm_type: str, context: dict[str, Any]
    ) -> DeliveryConfig:
        """Get appropriate delivery config based on swarm type and context"""

        # Map swarm types to delivery configs
        swarm_mappings = {
            "mythology_business": "daily_intelligence",
            "mythology_strategic": "strategic_analysis",
            "mythology_health": "executive_reports",
            "mythology_comprehensive": "executive_reports",
            "military_recon": "technical_operations",
            "military_qc": "code_quality",
            "military_planning": "strategic_analysis",
            "military_strike": "technical_operations",
            "military_review": "code_quality",
            "hybrid_tactical": "strategic_analysis",
        }

        config_name = swarm_mappings.get(swarm_type, "daily_intelligence")

        # Check context for overrides
        if context.get("executive_audience"):
            config_name = "executive_reports"
        elif context.get("critical_alert"):
            config_name = "critical_alerts"
        elif context.get("technical_focus"):
            config_name = "technical_operations"

        return self.delivery_configs.get(
            config_name, self.delivery_configs["daily_intelligence"]
        )


# Global template manager instance
_template_manager = None


def get_template_manager() -> SlackDeliveryTemplateManager:
    """Get global template manager instance"""
    global _template_manager
    if _template_manager is None:
        _template_manager = SlackDeliveryTemplateManager()
    return _template_manager


# Convenience functions
def get_executive_delivery_config() -> DeliveryConfig:
    """Get executive delivery configuration"""
    manager = get_template_manager()
    return manager.get_delivery_config("executive_reports")


def get_technical_delivery_config() -> DeliveryConfig:
    """Get technical delivery configuration"""
    manager = get_template_manager()
    return manager.get_delivery_config("technical_operations")


def get_strategic_delivery_config() -> DeliveryConfig:
    """Get strategic analysis delivery configuration"""
    manager = get_template_manager()
    return manager.get_delivery_config("strategic_analysis")


def get_daily_intelligence_config() -> DeliveryConfig:
    """Get daily intelligence delivery configuration"""
    manager = get_template_manager()
    return manager.get_delivery_config("daily_intelligence")


def get_critical_alert_config() -> DeliveryConfig:
    """Get critical alert delivery configuration"""
    manager = get_template_manager()
    return manager.get_delivery_config("critical_alerts")


def format_executive_summary(variables: dict[str, Any]) -> str:
    """Format executive summary message"""
    manager = get_template_manager()
    return manager.format_message_with_template("executive_summary", variables)


def format_technical_report(variables: dict[str, Any]) -> str:
    """Format technical operations report"""
    manager = get_template_manager()
    return manager.format_message_with_template("technical_ops", variables)


def format_strategic_analysis(variables: dict[str, Any]) -> str:
    """Format strategic analysis report"""
    manager = get_template_manager()
    return manager.format_message_with_template("strategic_analysis", variables)
