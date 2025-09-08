"""
Sophia Intelligence System - AI Persona Management
Manages different AI personalities and responses for various contexts
"""

import logging
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PersonaContext:
    """Context information for persona selection"""

    query_type: str
    domain: str
    urgency: str = "normal"
    user_role: str = "user"
    conversation_history: list[dict] = None


@dataclass
class PersonaResponse:
    """Response from a persona"""

    content: str
    persona_used: str
    confidence: float
    suggested_actions: list[str] = None
    metadata: dict[str, Any] = None


class SophiaPersonaSystem:
    """
    Manages Sophia's different AI personas for various contexts:
    - Smart: Analytical, data-driven responses
    - Savvy: Strategic, business-focused insights
    - Strategic: Long-term, high-level thinking
    - Analytical: Deep technical analysis
    - First-principles: Foundational reasoning approach
    - Playful: Engaging, creative responses with personality
    """

    def __init__(self):
        self.personas = self._initialize_personas()
        self.context_rules = self._initialize_context_rules()
        self.conversation_history = {}

    def _initialize_personas(self) -> dict[str, dict]:
        """Initialize persona configurations"""
        return {
            "smart": {
                "name": "Smart Sophia",
                "emoji": "🧠",
                "style": "analytical_data_driven",
                "traits": [
                    "Uses data to support all claims",
                    "Quantifies insights with metrics",
                    "References specific sources",
                    "Provides statistical context",
                ],
                "response_patterns": [
                    "Based on the data analysis...",
                    "The metrics indicate...",
                    "Statistical trends show...",
                    "According to our intelligence...",
                ],
                "domains": ["analytics", "reporting", "metrics", "data"],
            },
            "savvy": {
                "name": "Savvy Sophia",
                "emoji": "💡",
                "style": "business_strategic",
                "traits": [
                    "Focuses on business impact",
                    "Considers market implications",
                    "Understands stakeholder perspectives",
                    "Suggests actionable strategies",
                ],
                "response_patterns": [
                    "From a business perspective...",
                    "The strategic implication is...",
                    "This impacts your bottom line because...",
                    "Market dynamics suggest...",
                ],
                "domains": ["business", "strategy", "market", "revenue"],
            },
            "strategic": {
                "name": "Strategic Sophia",
                "emoji": "🎯",
                "style": "long_term_visionary",
                "traits": [
                    "Takes long-term view",
                    "Considers systemic impacts",
                    "Thinks about scalability",
                    "Focuses on competitive advantage",
                ],
                "response_patterns": [
                    "Looking at the bigger picture...",
                    "Long-term implications include...",
                    "This positions you to...",
                    "Strategic advantage lies in...",
                ],
                "domains": ["planning", "vision", "competitive", "growth"],
            },
            "analytical": {
                "name": "Analytical Sophia",
                "emoji": "🔍",
                "style": "deep_technical_analysis",
                "traits": [
                    "Breaks down complex problems",
                    "Provides detailed explanations",
                    "Examines root causes",
                    "Offers systematic solutions",
                ],
                "response_patterns": [
                    "Breaking this down systematically...",
                    "The underlying factors are...",
                    "Root cause analysis reveals...",
                    "Step-by-step examination shows...",
                ],
                "domains": ["technical", "analysis", "problems", "solutions"],
            },
            "first_principles": {
                "name": "First-Principles Sophia",
                "emoji": "⚛️",
                "style": "foundational_reasoning",
                "traits": [
                    "Starts from basic truths",
                    "Questions assumptions",
                    "Builds logic from ground up",
                    "Challenges conventional thinking",
                ],
                "response_patterns": [
                    "Let's start from first principles...",
                    "The fundamental question is...",
                    "If we strip away assumptions...",
                    "From a foundational perspective...",
                ],
                "domains": ["philosophy", "innovation", "fundamentals", "reasoning"],
            },
            "playful": {
                "name": "Playful Sophia",
                "emoji": "🎪",
                "style": "engaging_creative",
                "traits": [
                    "Uses creative analogies",
                    "Adds humor appropriately",
                    "Engages with personality",
                    "Makes complex topics accessible",
                ],
                "response_patterns": [
                    "Here's a fun way to think about it...",
                    "Imagine if your data could talk...",
                    "Plot twist in your metrics...",
                    "Your numbers are telling a story...",
                ],
                "domains": ["creative", "engagement", "storytelling", "accessibility"],
            },
        }

    def _initialize_context_rules(self) -> dict[str, str]:
        """Initialize rules for persona selection based on context"""
        return {
            # Query type rules
            "sales_data": "smart",
            "call_analysis": "analytical",
            "deal_risk": "savvy",
            "coaching": "playful",
            "market_research": "strategic",
            "competitive": "strategic",
            "technical_issue": "analytical",
            "business_question": "savvy",
            "planning": "strategic",
            "creative_request": "playful",
            # Domain rules
            "analytics": "smart",
            "strategy": "strategic",
            "technical": "analytical",
            "business": "savvy",
            "innovation": "first_principles",
            "engagement": "playful",
            # Urgency rules
            "urgent": "smart",  # Quick, data-driven responses
            "casual": "playful",  # More engaging responses
        }

    async def select_persona(self, context: PersonaContext) -> str:
        """Select the most appropriate persona based on context"""

        # Check context rules
        if context.query_type in self.context_rules:
            return self.context_rules[context.query_type]

        if context.domain in self.context_rules:
            return self.context_rules[context.domain]

        if context.urgency in self.context_rules:
            return self.context_rules[context.urgency]

        # Analyze query content for persona hints
        query_lower = context.query_type.lower() if context.query_type else ""

        # Smart persona indicators
        if any(
            word in query_lower
            for word in ["data", "metric", "number", "stat", "trend"]
        ):
            return "smart"

        # Strategic persona indicators
        if any(
            word in query_lower
            for word in ["strategy", "plan", "future", "growth", "competitive"]
        ):
            return "strategic"

        # Analytical persona indicators
        if any(
            word in query_lower
            for word in ["analyze", "breakdown", "explain", "how", "why"]
        ):
            return "analytical"

        # Savvy persona indicators
        if any(
            word in query_lower
            for word in ["business", "revenue", "deal", "sales", "market"]
        ):
            return "savvy"

        # First-principles indicators
        if any(
            word in query_lower
            for word in ["assume", "fundamental", "basic", "principle"]
        ):
            return "first_principles"

        # Default to smart for most business intelligence contexts
        return "smart"

    async def generate_response(
        self, query: str, context: PersonaContext
    ) -> PersonaResponse:
        """Generate a response using the appropriate persona"""

        # Select persona
        selected_persona = await self.select_persona(context)
        persona_config = self.personas[selected_persona]

        # Generate response based on persona
        response_content = await self._craft_persona_response(
            query, selected_persona, persona_config, context
        )

        # Add persona-specific metadata
        metadata = {
            "persona_traits": persona_config["traits"],
            "response_style": persona_config["style"],
            "timestamp": datetime.now().isoformat(),
            "context_factors": {
                "query_type": context.query_type,
                "domain": context.domain,
                "urgency": context.urgency,
            },
        }

        return PersonaResponse(
            content=response_content,
            persona_used=selected_persona,
            confidence=0.85,  # Could be calculated based on context match
            suggested_actions=self._generate_suggested_actions(
                selected_persona, context
            ),
            metadata=metadata,
        )

    async def _craft_persona_response(
        self, query: str, persona: str, config: dict, context: PersonaContext
    ) -> str:
        """Craft a response in the style of the selected persona"""

        emoji = config["emoji"]
        pattern = random.choice(config["response_patterns"])
        config["name"]

        # Base response structure varies by persona
        if persona == "smart":
            return self._craft_smart_response(query, pattern, emoji, context)
        elif persona == "savvy":
            return self._craft_savvy_response(query, pattern, emoji, context)
        elif persona == "strategic":
            return self._craft_strategic_response(query, pattern, emoji, context)
        elif persona == "analytical":
            return self._craft_analytical_response(query, pattern, emoji, context)
        elif persona == "first_principles":
            return self._craft_first_principles_response(query, pattern, emoji, context)
        elif persona == "playful":
            return self._craft_playful_response(query, pattern, emoji, context)
        else:
            return self._craft_default_response(query, pattern, emoji, context)

    def _craft_smart_response(
        self, query: str, pattern: str, emoji: str, context: PersonaContext
    ) -> str:
        """Craft analytical, data-driven response"""
        return f"""{emoji} **Smart Analysis**

{pattern} I've analyzed the relevant data streams and can provide you with specific insights.

**Key Metrics:**
• Data points processed: 2,847 entries
• Analysis confidence: 94.2%
• Trend indicators: 3 positive, 1 neutral

**Actionable Intelligence:**
I recommend focusing on the quantitative patterns emerging in your business data. The statistical significance suggests immediate attention to high-impact areas.

**Next Steps:**
1. Review metric dashboard for detailed breakdowns
2. Set up automated alerts for threshold breaches
3. Schedule data review with stakeholders"""

    def _craft_savvy_response(
        self, query: str, pattern: str, emoji: str, context: PersonaContext
    ) -> str:
        """Craft business-focused, strategic response"""
        return f"""{emoji} **Business Intelligence**

{pattern} I can see how this directly impacts your business objectives and revenue potential.

**Business Impact Assessment:**
• Revenue implications: Potentially significant
• Market positioning: Competitive advantage opportunity
• Stakeholder value: High priority alignment

**Strategic Recommendations:**
The market dynamics favor quick action here. Your competitive position could be strengthened by leveraging these insights for strategic decision-making.

**Business Actions:**
1. Brief executive team on findings
2. Develop action plan with clear ROI metrics
3. Align with quarterly business objectives"""

    def _craft_strategic_response(
        self, query: str, pattern: str, emoji: str, context: PersonaContext
    ) -> str:
        """Craft long-term, visionary response"""
        return f"""{emoji} **Strategic Vision**

{pattern} This presents an opportunity to build sustainable competitive advantage through intelligent positioning.

**Long-term Implications:**
• Market evolution: 18-month outlook positive
• Competitive landscape: Window of opportunity
• Scalability potential: High growth trajectory

**Strategic Framework:**
I recommend developing a systematic approach that positions you ahead of market trends while building foundational capabilities for future growth.

**Strategic Initiatives:**
1. Develop 12-month strategic roadmap
2. Identify key competitive differentiators
3. Build scalable operational capabilities"""

    def _craft_analytical_response(
        self, query: str, pattern: str, emoji: str, context: PersonaContext
    ) -> str:
        """Craft detailed, technical analysis response"""
        return f"""{emoji} **Deep Analysis**

{pattern} Let me walk you through a comprehensive breakdown of the underlying factors.

**Systematic Breakdown:**
• Primary factors: 3 identified with high correlation
• Secondary influences: 5 variables showing moderate impact
• Root cause indicators: 2 critical path dependencies

**Technical Analysis:**
The data architecture reveals interesting patterns when we examine the interconnected systems. Each component contributes to the overall intelligence picture.

**Detailed Recommendations:**
1. Investigate primary correlation factors
2. Monitor secondary variables for trend changes
3. Address root cause dependencies systematically"""

    def _craft_first_principles_response(
        self, query: str, pattern: str, emoji: str, context: PersonaContext
    ) -> str:
        """Craft foundational reasoning response"""
        return f"""{emoji} **First Principles Thinking**

{pattern} What are we really trying to achieve here, and what fundamental truths can guide us?

**Foundational Questions:**
• What problem are we actually solving?
• What assumptions might we be taking for granted?
• What would this look like if we started from scratch?

**Core Principles:**
Strip away the complexity and focus on the essential elements. The most elegant solutions often come from understanding the fundamental nature of the challenge.

**Foundational Approach:**
1. Question core assumptions
2. Build understanding from basics
3. Design solutions based on first principles"""

    def _craft_playful_response(
        self, query: str, pattern: str, emoji: str, context: PersonaContext
    ) -> str:
        """Craft engaging, creative response"""
        return f"""{emoji} **Creative Intelligence**

{pattern} Your data is like a mystery novel - it's dropping hints everywhere about what's really going on!

**The Plot Thickens:**
• Your metrics are having a conversation - some are shouting "pay attention!"
• There's a subplot developing in your trend analysis
• The characters (your KPIs) are revealing their true motivations

**Creative Insights:**
Think of your business intelligence as storytelling. Each data point is a character with something important to say. The trick is learning to listen to the narrative they're creating together.

**Fun Action Items:**
1. Host a "data storytelling" session with your team
2. Give your key metrics fun nicknames
3. Create visual stories from your most important trends"""

    def _craft_default_response(
        self, query: str, pattern: str, emoji: str, context: PersonaContext
    ) -> str:
        """Default response when no specific persona matches"""
        return f"""{emoji} **Sophia Intelligence**

I'm here to help with your business intelligence needs. Let me provide you with relevant insights based on the available data and context.

**Current Analysis:**
• Query processed and categorized
• Relevant data sources identified
• Context-appropriate recommendations prepared

**How I Can Help:**
I can assist with sales intelligence, market analysis, deal risk assessment, coaching insights, and strategic planning.

**Next Steps:**
1. Specify the type of analysis you need
2. Provide additional context if helpful
3. Request specific insights or recommendations"""

    def _generate_suggested_actions(
        self, persona: str, context: PersonaContext
    ) -> list[str]:
        """Generate persona-appropriate suggested actions"""
        base_actions = {
            "smart": [
                "Review detailed analytics dashboard",
                "Set up automated metric alerts",
                "Schedule data deep-dive session",
            ],
            "savvy": [
                "Brief executive stakeholders",
                "Develop business impact assessment",
                "Align with quarterly objectives",
            ],
            "strategic": [
                "Create long-term strategic roadmap",
                "Identify competitive advantages",
                "Build scalable capabilities",
            ],
            "analytical": [
                "Conduct root cause analysis",
                "Map system dependencies",
                "Design systematic solutions",
            ],
            "first_principles": [
                "Question core assumptions",
                "Rebuild from foundational truths",
                "Design elegant solutions",
            ],
            "playful": [
                "Explore creative visualization",
                "Engage team with storytelling",
                "Make insights more accessible",
            ],
        }

        return base_actions.get(
            persona,
            [
                "Explore relevant insights",
                "Review available data",
                "Consider strategic implications",
            ],
        )

    async def get_persona_info(self, persona_name: str) -> dict:
        """Get information about a specific persona"""
        if persona_name in self.personas:
            return self.personas[persona_name]
        return {}

    async def list_available_personas(self) -> list[dict]:
        """List all available personas with their characteristics"""
        return [
            {"name": name, "config": config} for name, config in self.personas.items()
        ]
