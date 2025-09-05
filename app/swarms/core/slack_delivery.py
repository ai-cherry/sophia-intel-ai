"""
Slack Delivery System for Micro-Swarms
Advanced Slack integration for delivering swarm results with rich formatting,
interactive elements, and intelligent routing
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from app.integrations.slack_integration import SlackIntegration
from app.swarms.core.micro_swarm_base import AgentRole, SwarmResult
from app.swarms.core.scheduler import ScheduledTask

logger = logging.getLogger(__name__)


class DeliveryFormat(Enum):
    """Formats for Slack delivery"""

    SUMMARY = "summary"  # Brief summary with key points
    DETAILED = "detailed"  # Full detailed report
    EXECUTIVE = "executive"  # Executive summary for leadership
    TECHNICAL = "technical"  # Technical deep dive
    INTERACTIVE = "interactive"  # Interactive with buttons/actions


class DeliveryPriority(Enum):
    """Priority levels for delivery"""

    URGENT = "urgent"  # Immediate delivery with @channel
    HIGH = "high"  # High priority with mentions
    NORMAL = "normal"  # Standard delivery
    LOW = "low"  # Quiet delivery, no notifications


class ChannelType(Enum):
    """Types of Slack channels"""

    GENERAL = "general"
    ALERTS = "alerts"
    REPORTS = "reports"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"
    CUSTOM = "custom"


@dataclass
class DeliveryConfig:
    """Configuration for Slack delivery"""

    channel: str
    format: DeliveryFormat = DeliveryFormat.SUMMARY
    priority: DeliveryPriority = DeliveryPriority.NORMAL
    include_reasoning: bool = True
    include_confidence: bool = True
    include_cost: bool = False
    max_length: int = 4000  # Slack message limit
    mention_users: List[str] = field(default_factory=list)
    mention_roles: List[str] = field(default_factory=list)
    custom_template: Optional[str] = None
    enable_threading: bool = True
    auto_summarize_long_content: bool = True


@dataclass
class DeliveryRule:
    """Rule for automatic delivery routing"""

    rule_id: str
    name: str
    description: str

    # Matching criteria
    swarm_types: List[str] = field(default_factory=list)
    agent_roles: List[AgentRole] = field(default_factory=list)
    confidence_threshold: float = 0.0
    cost_threshold: float = 0.0
    keywords: List[str] = field(default_factory=list)
    time_ranges: List[Dict[str, Any]] = field(default_factory=list)  # Business hours, etc.

    # Delivery configuration
    delivery_config: DeliveryConfig = field(
        default_factory=lambda: DeliveryConfig(channel="#general")
    )

    # Conditions
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DeliveryResult:
    """Result of a delivery attempt"""

    delivery_id: str
    success: bool
    channel: str
    message_ts: str  # Slack timestamp
    thread_ts: Optional[str] = None
    error_message: Optional[str] = None
    delivered_at: datetime = field(default_factory=datetime.now)
    format_used: DeliveryFormat = DeliveryFormat.SUMMARY
    character_count: int = 0
    user_mentions: List[str] = field(default_factory=list)


class SlackDeliveryEngine:
    """
    Advanced Slack delivery engine for micro-swarm results
    """

    def __init__(self):
        self.slack = SlackIntegration()

        # Delivery rules and routing
        self.delivery_rules: Dict[str, DeliveryRule] = {}
        self.channel_mappings = self._initialize_channel_mappings()

        # Delivery tracking
        self.delivery_history: List[DeliveryResult] = []

        # Message templates
        self.templates = self._initialize_templates()

        # Rate limiting
        self.last_delivery_times: Dict[str, datetime] = {}
        self.delivery_counts: Dict[str, int] = {}

        logger.info("Slack delivery engine initialized")

    def _initialize_channel_mappings(self) -> Dict[ChannelType, str]:
        """Initialize default channel mappings"""
        return {
            ChannelType.GENERAL: "#general",
            ChannelType.ALERTS: "#alerts",
            ChannelType.REPORTS: "#reports",
            ChannelType.TECHNICAL: "#technical",
            ChannelType.EXECUTIVE: "#executive",
        }

    def _initialize_templates(self) -> Dict[DeliveryFormat, str]:
        """Initialize message templates"""
        return {
            DeliveryFormat.SUMMARY: """
🤖 **{swarm_name}** Analysis Complete

📊 **Key Findings:**
{summary}

💡 **Confidence:** {confidence}%
⏱️ **Duration:** {duration} minutes
{mentions}
            """.strip(),
            DeliveryFormat.DETAILED: """
🔍 **Detailed Analysis Report**

**Swarm:** {swarm_name}
**Task:** {task_description}

**🎯 Results:**
{detailed_results}

**🧠 Agent Contributions:**
{agent_contributions}

**📈 Performance Metrics:**
• Confidence: {confidence}%
• Duration: {duration} minutes
• Cost: ${cost:.3f}
• Consensus: {'✅' if consensus else '❌'}

{mentions}
            """.strip(),
            DeliveryFormat.EXECUTIVE: """
📋 **Executive Summary**

**Business Impact:** {business_impact}

**Key Recommendations:**
{recommendations}

**Risk Assessment:**
{risk_assessment}

**Next Steps:**
{next_steps}

*Analysis powered by {swarm_name} | Confidence: {confidence}%*
{mentions}
            """.strip(),
            DeliveryFormat.TECHNICAL: """
🛠️ **Technical Analysis Report**

**System:** {swarm_name}
**Coordination Pattern:** {coordination_pattern}

**Technical Findings:**
{technical_findings}

**Architecture Insights:**
{architecture_insights}

**Quality Metrics:**
{quality_metrics}

**Performance Data:**
• Execution Time: {duration} minutes
• Model Routing: {model_info}
• Memory Usage: {memory_usage}

{mentions}
            """.strip(),
        }

    async def deliver_result(
        self,
        swarm_result: SwarmResult,
        config: DeliveryConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        """
        Deliver swarm result to Slack

        Args:
            swarm_result: Result from swarm execution
            config: Delivery configuration
            context: Additional context for formatting

        Returns:
            Delivery result with success status and metadata
        """

        delivery_id = f"delivery_{int(datetime.now().timestamp())}"
        context = context or {}

        try:
            # Check rate limits
            if not self._check_rate_limits(config.channel):
                return DeliveryResult(
                    delivery_id=delivery_id,
                    success=False,
                    channel=config.channel,
                    message_ts="",
                    error_message="Rate limit exceeded for channel",
                )

            # Format message
            formatted_message = await self._format_message(swarm_result, config, context)

            # Add mentions
            formatted_message = self._add_mentions(formatted_message, config)

            # Deliver to Slack
            response = await self.slack.send_message(
                channel=config.channel,
                message=formatted_message,
                thread_ts=context.get("thread_ts"),
            )

            # Create delivery result
            result = DeliveryResult(
                delivery_id=delivery_id,
                success=True,
                channel=config.channel,
                message_ts=response.get("ts", ""),
                thread_ts=response.get("thread_ts"),
                format_used=config.format,
                character_count=len(formatted_message),
                user_mentions=config.mention_users,
            )

            # Track delivery
            self._record_delivery(config.channel)
            self.delivery_history.append(result)

            # Send follow-up interactive elements if needed
            if config.format == DeliveryFormat.INTERACTIVE:
                await self._send_interactive_elements(
                    config.channel, response.get("ts"), swarm_result
                )

            logger.info(f"Successfully delivered result to {config.channel}")
            return result

        except Exception as e:
            logger.error(f"Failed to deliver result: {e}")
            return DeliveryResult(
                delivery_id=delivery_id,
                success=False,
                channel=config.channel,
                message_ts="",
                error_message=str(e),
            )

    async def _format_message(
        self, swarm_result: SwarmResult, config: DeliveryConfig, context: Dict[str, Any]
    ) -> str:
        """Format swarm result into Slack message"""

        # Get base template
        template = config.custom_template or self.templates.get(
            config.format, self.templates[DeliveryFormat.SUMMARY]
        )

        # Prepare context variables
        format_context = {
            "swarm_name": context.get("swarm_name", "Micro-Swarm"),
            "task_description": context.get("task_description", "Analysis Task"),
            "confidence": int(swarm_result.confidence * 100),
            "duration": f"{swarm_result.execution_time_ms / 60000:.1f}",
            "cost": swarm_result.total_cost,
            "consensus": swarm_result.consensus_achieved,
            "coordination_pattern": context.get("coordination_pattern", "Unknown"),
            "mentions": "",  # Will be added later
        }

        # Format-specific content
        if config.format == DeliveryFormat.SUMMARY:
            format_context.update({"summary": self._create_summary(swarm_result, max_length=500)})

        elif config.format == DeliveryFormat.DETAILED:
            format_context.update(
                {
                    "detailed_results": self._format_detailed_results(swarm_result),
                    "agent_contributions": self._format_agent_contributions(swarm_result),
                }
            )

        elif config.format == DeliveryFormat.EXECUTIVE:
            format_context.update(
                {
                    "business_impact": self._extract_business_impact(swarm_result),
                    "recommendations": self._extract_recommendations(swarm_result),
                    "risk_assessment": self._extract_risk_assessment(swarm_result),
                    "next_steps": self._extract_next_steps(swarm_result),
                }
            )

        elif config.format == DeliveryFormat.TECHNICAL:
            format_context.update(
                {
                    "technical_findings": self._extract_technical_findings(swarm_result),
                    "architecture_insights": self._extract_architecture_insights(swarm_result),
                    "quality_metrics": self._format_quality_metrics(swarm_result),
                    "model_info": self._format_model_info(swarm_result),
                    "memory_usage": context.get("memory_usage", "N/A"),
                }
            )

        # Apply template
        try:
            formatted_message = template.format(**format_context)
        except KeyError as e:
            logger.warning(f"Template formatting error: {e}")
            # Fallback to simple format
            formatted_message = (
                f"**{format_context['swarm_name']}** - {swarm_result.final_output[:500]}..."
            )

        # Truncate if too long
        if len(formatted_message) > config.max_length:
            if config.auto_summarize_long_content:
                formatted_message = self._auto_summarize(formatted_message, config.max_length)
            else:
                formatted_message = (
                    formatted_message[: config.max_length - 50] + "\n\n*[Content truncated]*"
                )

        return formatted_message

    def _create_summary(self, swarm_result: SwarmResult, max_length: int = 500) -> str:
        """Create a concise summary of the swarm result"""

        content = swarm_result.final_output

        if len(content) <= max_length:
            return content

        # Extract key sentences (simple approach)
        sentences = content.split(". ")
        summary_sentences = []
        current_length = 0

        for sentence in sentences:
            if current_length + len(sentence) + 2 <= max_length:
                summary_sentences.append(sentence)
                current_length += len(sentence) + 2
            else:
                break

        summary = ". ".join(summary_sentences)
        if summary and not summary.endswith("."):
            summary += "."

        return summary or content[: max_length - 10] + "..."

    def _format_detailed_results(self, swarm_result: SwarmResult) -> str:
        """Format detailed results section"""

        content = swarm_result.final_output

        # Break into structured sections
        sections = []

        # Look for common markers
        if "ANALYSIS:" in content or "Analysis:" in content:
            sections.append("📊 **Analysis Results**")
        if "RECOMMENDATIONS:" in content or "Recommendations:" in content:
            sections.append("💡 **Recommendations**")
        if "CONCLUSION:" in content or "Conclusion:" in content:
            sections.append("🎯 **Conclusions**")

        # If no clear structure, format as bullets
        if not sections:
            lines = content.split("\n")
            key_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) > 20]
            return "\n".join(f"• {line}" for line in key_lines[:5])

        return content[:1000] + ("..." if len(content) > 1000 else "")

    def _format_agent_contributions(self, swarm_result: SwarmResult) -> str:
        """Format agent contributions section"""

        contributions = []

        for agent_role, messages in swarm_result.agent_contributions.items():
            if messages:
                message_count = len(messages)
                last_message = messages[-1]

                emoji_map = {
                    AgentRole.ANALYST: "🔍",
                    AgentRole.STRATEGIST: "🎯",
                    AgentRole.VALIDATOR: "✅",
                }

                emoji = emoji_map.get(agent_role, "🤖")
                contribution_text = (
                    f"{emoji} **{agent_role.value.title()}**: {message_count} messages"
                )

                if hasattr(last_message, "confidence"):
                    contribution_text += f" (Confidence: {last_message.confidence:.2f})"

                contributions.append(contribution_text)

        return "\n".join(contributions) if contributions else "No agent contribution data available"

    def _extract_business_impact(self, swarm_result: SwarmResult) -> str:
        """Extract business impact information"""

        content = swarm_result.final_output.lower()
        impact_keywords = [
            "revenue",
            "cost",
            "savings",
            "efficiency",
            "productivity",
            "customer",
            "market",
            "competitive",
            "growth",
            "roi",
        ]

        # Find sentences containing business keywords
        sentences = swarm_result.final_output.split(". ")
        impact_sentences = []

        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in impact_keywords):
                impact_sentences.append(sentence.strip())

        if impact_sentences:
            return ". ".join(impact_sentences[:3]) + "."

        return "Business impact analysis not explicitly provided in the results."

    def _extract_recommendations(self, swarm_result: SwarmResult) -> str:
        """Extract recommendations from swarm result"""

        content = swarm_result.final_output

        # Look for recommendation sections
        recommendation_markers = [
            "recommend",
            "suggest",
            "should",
            "action",
            "next step",
            "consider",
            "propose",
            "advise",
        ]

        lines = content.split("\n")
        recommendation_lines = []

        for line in lines:
            if any(marker in line.lower() for marker in recommendation_markers):
                recommendation_lines.append(f"• {line.strip()}")

        return (
            "\n".join(recommendation_lines[:5])
            if recommendation_lines
            else "No specific recommendations identified."
        )

    def _extract_risk_assessment(self, swarm_result: SwarmResult) -> str:
        """Extract risk assessment information"""

        content = swarm_result.final_output.lower()
        risk_keywords = [
            "risk",
            "threat",
            "concern",
            "issue",
            "problem",
            "challenge",
            "vulnerability",
        ]

        sentences = swarm_result.final_output.split(". ")
        risk_sentences = []

        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in risk_keywords):
                risk_sentences.append(sentence.strip())

        if risk_sentences:
            return ". ".join(risk_sentences[:2]) + "."

        # Check confidence level for risk indication
        if swarm_result.confidence < 0.7:
            return f"⚠️ Low confidence level ({swarm_result.confidence:.2f}) suggests uncertainty in analysis."

        return "No significant risks identified in the analysis."

    def _extract_next_steps(self, swarm_result: SwarmResult) -> str:
        """Extract next steps from swarm result"""

        content = swarm_result.final_output

        # Look for action-oriented language
        action_markers = [
            "next",
            "should",
            "will",
            "must",
            "action",
            "implement",
            "execute",
            "follow up",
            "continue",
            "proceed",
        ]

        lines = content.split("\n")
        action_lines = []

        for line in lines:
            if any(marker in line.lower() for marker in action_markers) and len(line.strip()) > 10:
                action_lines.append(f"1. {line.strip()}")

        return "\n".join(action_lines[:3]) if action_lines else "No explicit next steps provided."

    def _extract_technical_findings(self, swarm_result: SwarmResult) -> str:
        """Extract technical findings"""

        content = swarm_result.final_output

        # Look for technical keywords
        tech_keywords = [
            "architecture",
            "code",
            "system",
            "performance",
            "security",
            "database",
            "api",
            "infrastructure",
            "scalability",
            "design",
        ]

        sentences = content.split(". ")
        tech_sentences = []

        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in tech_keywords):
                tech_sentences.append(f"• {sentence.strip()}")

        return (
            "\n".join(tech_sentences[:4])
            if tech_sentences
            else "No specific technical findings identified."
        )

    def _extract_architecture_insights(self, swarm_result: SwarmResult) -> str:
        """Extract architecture insights"""

        content = swarm_result.final_output

        # Look for architecture-specific content
        arch_keywords = [
            "pattern",
            "design",
            "structure",
            "component",
            "service",
            "integration",
            "interface",
            "dependency",
            "coupling",
        ]

        lines = content.split("\n")
        arch_lines = []

        for line in lines:
            if any(keyword in line.lower() for keyword in arch_keywords) and len(line.strip()) > 15:
                arch_lines.append(f"• {line.strip()}")

        return (
            "\n".join(arch_lines[:3])
            if arch_lines
            else "No specific architecture insights provided."
        )

    def _format_quality_metrics(self, swarm_result: SwarmResult) -> str:
        """Format quality metrics"""

        metrics = []

        # Consensus achievement
        consensus_icon = "✅" if swarm_result.consensus_achieved else "❌"
        metrics.append(f"• Consensus: {consensus_icon}")

        # Confidence level
        confidence_pct = int(swarm_result.confidence * 100)
        if confidence_pct >= 90:
            conf_icon = "🟢"
        elif confidence_pct >= 70:
            conf_icon = "🟡"
        else:
            conf_icon = "🔴"
        metrics.append(f"• Confidence: {conf_icon} {confidence_pct}%")

        # Iteration efficiency
        if hasattr(swarm_result, "iterations_used"):
            metrics.append(f"• Iterations: {swarm_result.iterations_used}")

        return "\n".join(metrics)

    def _format_model_info(self, swarm_result: SwarmResult) -> str:
        """Format model routing information"""

        # Extract model info from metadata if available
        if hasattr(swarm_result, "metadata") and swarm_result.metadata:
            models_used = swarm_result.metadata.get("models_used", [])
            if models_used:
                return f"Models: {', '.join(models_used)}"

        return "Model routing information not available"

    def _auto_summarize(self, content: str, max_length: int) -> str:
        """Auto-summarize content to fit within length limit"""

        if len(content) <= max_length:
            return content

        # Simple summarization - keep first part and last part
        first_part_length = int(max_length * 0.7)
        last_part_length = int(max_length * 0.2)

        first_part = content[:first_part_length]
        last_part = content[-last_part_length:]

        # Find good break points
        first_break = first_part.rfind(". ")
        if first_break > first_part_length * 0.8:
            first_part = first_part[: first_break + 1]

        last_break = last_part.find(". ")
        if last_break != -1 and last_break < last_part_length * 0.2:
            last_part = last_part[last_break + 2 :]

        return f"{first_part}\n\n*[Content summarized]*\n\n{last_part}"

    def _add_mentions(self, message: str, config: DeliveryConfig) -> str:
        """Add user and role mentions to message"""

        mentions = []

        # Add user mentions
        for user in config.mention_users:
            mentions.append(f"<@{user}>")

        # Add role mentions
        for role in config.mention_roles:
            mentions.append(f"<!{role}>")

        # Add priority-based mentions
        if config.priority == DeliveryPriority.URGENT:
            mentions.append("<!channel>")
        elif config.priority == DeliveryPriority.HIGH:
            mentions.append("<!here>")

        if mentions:
            mention_string = " ".join(mentions)
            message = message.replace("{mentions}", f"\n\n{mention_string}")
        else:
            message = message.replace("{mentions}", "")

        return message

    async def _send_interactive_elements(
        self, channel: str, message_ts: str, swarm_result: SwarmResult
    ):
        """Send interactive elements (buttons, etc.) for the result"""

        # Create interactive blocks
        blocks = [
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "👍 Approve"},
                        "style": "primary",
                        "action_id": f"approve_result_{message_ts}",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔄 Request Revision"},
                        "action_id": f"revise_result_{message_ts}",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 View Details"},
                        "action_id": f"details_result_{message_ts}",
                    },
                ],
            }
        ]

        try:
            await self.slack.send_message(
                channel=channel, message="Choose an action:", blocks=blocks, thread_ts=message_ts
            )
        except Exception as e:
            logger.error(f"Failed to send interactive elements: {e}")

    def _check_rate_limits(self, channel: str) -> bool:
        """Check if delivery is within rate limits"""

        now = datetime.now()

        # Check if we've delivered to this channel recently
        last_delivery = self.last_delivery_times.get(channel)
        if last_delivery and (now - last_delivery).total_seconds() < 60:  # 1 minute minimum
            return False

        # Check daily delivery count
        today_key = f"{channel}_{now.date()}"
        today_count = self.delivery_counts.get(today_key, 0)
        if today_count >= 50:  # Max 50 deliveries per channel per day
            return False

        return True

    def _record_delivery(self, channel: str):
        """Record delivery for rate limiting"""

        now = datetime.now()
        self.last_delivery_times[channel] = now

        today_key = f"{channel}_{now.date()}"
        self.delivery_counts[today_key] = self.delivery_counts.get(today_key, 0) + 1

    def add_delivery_rule(self, rule: DeliveryRule):
        """Add a delivery rule for automatic routing"""
        self.delivery_rules[rule.rule_id] = rule
        logger.info(f"Added delivery rule: {rule.name}")

    def remove_delivery_rule(self, rule_id: str) -> bool:
        """Remove a delivery rule"""
        if rule_id in self.delivery_rules:
            del self.delivery_rules[rule_id]
            logger.info(f"Removed delivery rule: {rule_id}")
            return True
        return False

    async def auto_deliver(
        self, swarm_result: SwarmResult, context: Dict[str, Any]
    ) -> List[DeliveryResult]:
        """Automatically deliver result based on configured rules"""

        results = []

        for rule in self.delivery_rules.values():
            if not rule.enabled:
                continue

            # Check if result matches rule criteria
            if self._matches_delivery_rule(swarm_result, context, rule):
                delivery_result = await self.deliver_result(
                    swarm_result=swarm_result, config=rule.delivery_config, context=context
                )
                results.append(delivery_result)

                logger.info(f"Auto-delivered result using rule: {rule.name}")

        return results

    def _matches_delivery_rule(
        self, swarm_result: SwarmResult, context: Dict[str, Any], rule: DeliveryRule
    ) -> bool:
        """Check if result matches delivery rule criteria"""

        # Check swarm type
        swarm_type = context.get("swarm_type", "")
        if rule.swarm_types and swarm_type not in rule.swarm_types:
            return False

        # Check confidence threshold
        if swarm_result.confidence < rule.confidence_threshold:
            return False

        # Check cost threshold
        if rule.cost_threshold > 0 and swarm_result.total_cost > rule.cost_threshold:
            return False

        # Check keywords in content
        if rule.keywords:
            content_lower = swarm_result.final_output.lower()
            if not any(keyword.lower() in content_lower for keyword in rule.keywords):
                return False

        # Check time ranges (simplified - could be enhanced)
        now = datetime.now()
        if rule.time_ranges:
            in_time_range = False
            for time_range in rule.time_ranges:
                start_hour = time_range.get("start_hour", 0)
                end_hour = time_range.get("end_hour", 23)
                if start_hour <= now.hour <= end_hour:
                    in_time_range = True
                    break

            if not in_time_range:
                return False

        return True

    def get_delivery_statistics(self) -> Dict[str, Any]:
        """Get delivery statistics"""

        total_deliveries = len(self.delivery_history)
        successful_deliveries = len([d for d in self.delivery_history if d.success])

        # Channel distribution
        channel_counts = {}
        for delivery in self.delivery_history:
            channel_counts[delivery.channel] = channel_counts.get(delivery.channel, 0) + 1

        # Format distribution
        format_counts = {}
        for delivery in self.delivery_history:
            format_name = delivery.format_used.value
            format_counts[format_name] = format_counts.get(format_name, 0) + 1

        return {
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful_deliveries,
            "success_rate": successful_deliveries / total_deliveries if total_deliveries > 0 else 0,
            "channel_distribution": channel_counts,
            "format_distribution": format_counts,
            "active_rules": len([r for r in self.delivery_rules.values() if r.enabled]),
            "total_rules": len(self.delivery_rules),
            "recent_deliveries": len(
                [
                    d
                    for d in self.delivery_history
                    if (datetime.now() - d.delivered_at).total_seconds() < 86400
                ]
            ),  # Last 24 hours
        }


# Factory functions for common delivery configurations
def create_executive_delivery_config(channel: str = "#executive") -> DeliveryConfig:
    """Create delivery config for executive summaries"""
    return DeliveryConfig(
        channel=channel,
        format=DeliveryFormat.EXECUTIVE,
        priority=DeliveryPriority.HIGH,
        include_reasoning=False,
        include_confidence=True,
        include_cost=False,
        mention_roles=["executives"],
        max_length=2000,
    )


def create_technical_delivery_config(channel: str = "#technical") -> DeliveryConfig:
    """Create delivery config for technical reports"""
    return DeliveryConfig(
        channel=channel,
        format=DeliveryFormat.TECHNICAL,
        priority=DeliveryPriority.NORMAL,
        include_reasoning=True,
        include_confidence=True,
        include_cost=True,
        max_length=4000,
    )


def create_alert_delivery_config(channel: str = "#alerts") -> DeliveryConfig:
    """Create delivery config for urgent alerts"""
    return DeliveryConfig(
        channel=channel,
        format=DeliveryFormat.SUMMARY,
        priority=DeliveryPriority.URGENT,
        include_reasoning=False,
        include_confidence=True,
        include_cost=False,
        max_length=1000,
    )


# Global delivery engine instance
_delivery_engine = None


def get_delivery_engine() -> SlackDeliveryEngine:
    """Get global delivery engine instance"""
    global _delivery_engine
    if _delivery_engine is None:
        _delivery_engine = SlackDeliveryEngine()
    return _delivery_engine
