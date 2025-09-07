"""
Natural Language Interface for Micro-Swarms
Conversational AI interface that interprets natural language requests and orchestrates appropriate swarm executions
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.core.portkey_manager import get_portkey_manager
from app.memory.unified_memory_router import MemoryDomain
from app.swarms.core.swarm_integration import get_artemis_orchestrator, get_sophia_orchestrator

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of user intents"""

    ANALYZE = "analyze"  # Request analysis
    COMPARE = "compare"  # Compare options/scenarios
    RECOMMEND = "recommend"  # Get recommendations
    EVALUATE = "evaluate"  # Assess/evaluate something
    PREDICT = "predict"  # Forecast/predict outcomes
    SUMMARIZE = "summarize"  # Summarize information
    MONITOR = "monitor"  # Set up monitoring
    SCHEDULE = "schedule"  # Schedule recurring tasks
    EXPLAIN = "explain"  # Explain concepts/results
    TROUBLESHOOT = "troubleshoot"  # Diagnose problems
    OPTIMIZE = "optimize"  # Improve performance/efficiency
    VALIDATE = "validate"  # Check/verify something
    CREATE = "create"  # Generate new content/solutions
    UPDATE = "update"  # Modify existing information
    SEARCH = "search"  # Find information


class DomainType(Enum):
    """Business domains for routing"""

    BUSINESS = "business"  # Business intelligence, strategy
    TECHNICAL = "technical"  # Code, architecture, systems
    SALES = "sales"  # Sales operations, CRM
    MARKETING = "marketing"  # Marketing campaigns, analytics
    FINANCE = "finance"  # Financial analysis, forecasting
    OPERATIONS = "operations"  # Operational efficiency
    PRODUCT = "product"  # Product development, roadmap
    MIXED = "mixed"  # Cross-domain analysis


@dataclass
class ParsedRequest:
    """Parsed natural language request"""

    original_text: str
    intent: IntentType
    domain: DomainType
    entities: list[dict[str, Any]] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    time_references: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0

    # Swarm selection
    suggested_swarm_type: str = ""
    suggested_agents: list[str] = field(default_factory=list)
    coordination_pattern: str = "sequential"

    # Execution parameters
    priority: str = "normal"
    urgency: str = "normal"
    complexity: str = "medium"

    # Context and constraints
    constraints: dict[str, Any] = field(default_factory=dict)
    context_requirements: list[str] = field(default_factory=list)


@dataclass
class ConversationContext:
    """Context for ongoing conversation"""

    conversation_id: str
    user_id: Optional[str] = None
    channel_id: Optional[str] = None

    # Message history
    messages: list[dict[str, Any]] = field(default_factory=list)

    # Domain affinity (learns user preferences)
    domain_preferences: dict[str, float] = field(default_factory=dict)

    # Ongoing tasks
    active_tasks: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)

    # Context state
    current_topic: Optional[str] = None
    last_domain: Optional[str] = None
    last_intent: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class NaturalLanguageInterface:
    """
    Advanced natural language interface for micro-swarm orchestration
    """

    def __init__(self):
        self.portkey = get_portkey_manager()

        # Orchestrators
        self.sophia_orchestrator = get_sophia_orchestrator()
        self.artemis_orchestrator = get_artemis_orchestrator()

        # Conversation management
        self.conversations: dict[str, ConversationContext] = {}

        # Intent and entity patterns
        self.intent_patterns = self._initialize_intent_patterns()
        self.domain_patterns = self._initialize_domain_patterns()
        self.entity_patterns = self._initialize_entity_patterns()

        # Swarm mapping
        self.swarm_mappings = self._initialize_swarm_mappings()

        logger.info("Natural language interface initialized")

    def _initialize_intent_patterns(self) -> dict[IntentType, list[str]]:
        """Initialize intent recognition patterns"""
        return {
            IntentType.ANALYZE: [
                r"analy[sz]e",
                r"examine",
                r"investigate",
                r"study",
                r"look into",
                r"assess",
                r"what.*about",
                r"tell me about",
                r"insights? on",
                r"breakdown",
                r"deep dive",
            ],
            IntentType.COMPARE: [
                r"compare",
                r"versus",
                r"vs\.?",
                r"difference",
                r"contrast",
                r"which is better",
                r"pros and cons",
                r"evaluation",
                r"side by side",
                r"alternative",
            ],
            IntentType.RECOMMEND: [
                r"recommend",
                r"suggest",
                r"advice",
                r"what should",
                r"best option",
                r"guidance",
                r"propose",
                r"advise",
                r"opinion on",
            ],
            IntentType.EVALUATE: [
                r"evaluate",
                r"rate",
                r"score",
                r"judge",
                r"assess",
                r"review",
                r"how good",
                r"quality of",
                r"performance",
                r"effectiveness",
            ],
            IntentType.PREDICT: [
                r"predict",
                r"forecast",
                r"project",
                r"estimate",
                r"expect",
                r"anticipate",
                r"future",
                r"trend",
                r"outlook",
                r"what will happen",
                r"likely to",
            ],
            IntentType.SUMMARIZE: [
                r"summar[iy]ze",
                r"overview",
                r"brief",
                r"recap",
                r"highlights",
                r"key points",
                r"tldr",
                r"main points",
                r"executive summary",
            ],
            IntentType.MONITOR: [
                r"monitor",
                r"track",
                r"watch",
                r"observe",
                r"keep eye on",
                r"alert",
                r"notify",
                r"surveillance",
                r"dashboard",
            ],
            IntentType.SCHEDULE: [
                r"schedule",
                r"recurring",
                r"regular",
                r"periodic",
                r"daily",
                r"weekly",
                r"monthly",
                r"automate",
                r"set up.*regular",
                r"routine",
            ],
            IntentType.EXPLAIN: [
                r"explain",
                r"clarify",
                r"help understand",
                r"what does.*mean",
                r"how does.*work",
                r"why",
                r"definition",
                r"interpret",
            ],
            IntentType.TROUBLESHOOT: [
                r"troubleshoot",
                r"debug",
                r"fix",
                r"problem",
                r"issue",
                r"error",
                r"not working",
                r"broken",
                r"diagnose",
                r"resolve",
            ],
            IntentType.OPTIMIZE: [
                r"optimi[sz]e",
                r"improve",
                r"enhance",
                r"better",
                r"efficiency",
                r"performance",
                r"speed up",
                r"reduce cost",
                r"streamline",
            ],
            IntentType.VALIDATE: [
                r"validate",
                r"verify",
                r"check",
                r"confirm",
                r"audit",
                r"review",
                r"ensure",
                r"test",
                r"quality check",
                r"compliance",
            ],
            IntentType.CREATE: [
                r"create",
                r"generate",
                r"build",
                r"make",
                r"develop",
                r"design",
                r"construct",
                r"produce",
                r"new",
                r"draft",
            ],
            IntentType.UPDATE: [
                r"update",
                r"modify",
                r"change",
                r"edit",
                r"revise",
                r"refresh",
                r"sync",
                r"latest",
                r"current",
            ],
            IntentType.SEARCH: [
                r"search",
                r"find",
                r"locate",
                r"lookup",
                r"query",
                r"discover",
                r"where is",
                r"show me",
                r"retrieve",
            ],
        }

    def _initialize_domain_patterns(self) -> dict[DomainType, list[str]]:
        """Initialize domain recognition patterns"""
        return {
            DomainType.BUSINESS: [
                r"business",
                r"revenue",
                r"profit",
                r"market",
                r"competitive",
                r"strategy",
                r"customer",
                r"growth",
                r"roi",
                r"kpi",
                r"metrics",
                r"intelligence",
            ],
            DomainType.TECHNICAL: [
                r"code",
                r"architecture",
                r"system",
                r"technical",
                r"development",
                r"software",
                r"api",
                r"database",
                r"infrastructure",
                r"deployment",
            ],
            DomainType.SALES: [
                r"sales",
                r"deal",
                r"prospect",
                r"lead",
                r"pipeline",
                r"quota",
                r"crm",
                r"opportunity",
                r"close",
                r"conversion",
            ],
            DomainType.MARKETING: [
                r"marketing",
                r"campaign",
                r"brand",
                r"advertising",
                r"promotion",
                r"content",
                r"social media",
                r"engagement",
                r"awareness",
            ],
            DomainType.FINANCE: [
                r"finance",
                r"financial",
                r"budget",
                r"cost",
                r"expense",
                r"investment",
                r"cash flow",
                r"accounting",
                r"fiscal",
                r"spending",
            ],
            DomainType.OPERATIONS: [
                r"operations",
                r"process",
                r"workflow",
                r"efficiency",
                r"productivity",
                r"logistics",
                r"supply chain",
                r"manufacturing",
            ],
            DomainType.PRODUCT: [
                r"product",
                r"feature",
                r"roadmap",
                r"development",
                r"release",
                r"user experience",
                r"requirements",
                r"specs",
            ],
        }

    def _initialize_entity_patterns(self) -> dict[str, str]:
        """Initialize entity recognition patterns"""
        return {
            "timeframe": r"(today|yesterday|tomorrow|this week|last week|next week|this month|last month|next month|this quarter|last quarter|next quarter|this year|last year|next year|\d+\s+(day|week|month|quarter|year)s?\s+(ago|from now))",
            "percentage": r"(\d+(?:\.\d+)?%)",
            "currency": r"(\$\d+(?:,\d{3})*(?:\.\d{2})?[kmb]?)",
            "number": r"(\d+(?:,\d{3})*(?:\.\d+)?)",
            "email": r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            "url": r"(https?://[^\s]+)",
            "company": r"([A-Z][a-zA-Z0-9\s&\.]+(?:Inc|LLC|Corp|Ltd|Co\.?))",
            "priority": r"(urgent|high priority|asap|critical|low priority|when possible)",
        }

    def _initialize_swarm_mappings(self) -> dict[str, dict[str, Any]]:
        """Initialize intent/domain to swarm mappings"""
        return {
            "business_analysis": {
                "domain": "sophia",
                "swarm_type": "business_intelligence",
                "agents": ["hermes", "athena", "minerva"],
                "coordination": "sequential",
            },
            "strategic_planning": {
                "domain": "sophia",
                "swarm_type": "strategic_planning",
                "agents": ["athena", "odin", "minerva"],
                "coordination": "debate",
            },
            "technical_analysis": {
                "domain": "artemis",
                "swarm_type": "code_review",
                "agents": ["code_analyst", "quality_engineer", "security"],
                "coordination": "parallel",
            },
            "architecture_review": {
                "domain": "artemis",
                "swarm_type": "architecture_review",
                "agents": ["architect", "quality_engineer", "security"],
                "coordination": "sequential",
            },
            "business_health": {
                "domain": "sophia",
                "swarm_type": "business_health",
                "agents": ["asclepius", "hermes", "minerva"],
                "coordination": "hierarchical",
            },
        }

    async def process_request(
        self,
        text: str,
        conversation_id: str,
        user_id: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Process natural language request and orchestrate swarm execution

        Args:
            text: Natural language request
            conversation_id: Unique conversation identifier
            user_id: User making the request
            channel_id: Channel/thread identifier

        Returns:
            Execution result with swarm output and metadata
        """

        try:
            # Get or create conversation context
            context = self._get_conversation_context(conversation_id, user_id, channel_id)

            # Parse the request
            parsed_request = await self._parse_request(text, context)

            # Update conversation context
            context.messages.append(
                {
                    "type": "user",
                    "content": text,
                    "timestamp": datetime.now().isoformat(),
                    "parsed": parsed_request,
                }
            )

            # Route to appropriate orchestrator
            result = await self._route_and_execute(parsed_request, context)

            # Update conversation with result
            context.messages.append(
                {
                    "type": "assistant",
                    "content": result.get("content", ""),
                    "timestamp": datetime.now().isoformat(),
                    "metadata": result.get("metadata", {}),
                }
            )

            # Update conversation state
            self._update_conversation_state(context, parsed_request, result)

            return {
                "success": True,
                "parsed_request": {
                    "intent": parsed_request.intent.value,
                    "domain": parsed_request.domain.value,
                    "confidence": parsed_request.confidence,
                    "suggested_swarm": parsed_request.suggested_swarm_type,
                },
                "execution_result": result,
                "conversation_id": conversation_id,
            }

        except Exception as e:
            logger.error(f"Failed to process request: {e}")
            return {"success": False, "error": str(e), "conversation_id": conversation_id}

    async def _parse_request(self, text: str, context: ConversationContext) -> ParsedRequest:
        """Parse natural language request into structured format"""

        # Basic cleaning
        text_clean = text.strip().lower()

        # Detect intent
        intent, intent_confidence = self._detect_intent(text_clean)

        # Detect domain
        domain, domain_confidence = self._detect_domain(text_clean, context)

        # Extract entities
        entities = self._extract_entities(text)

        # Extract keywords
        keywords = self._extract_keywords(text_clean)

        # Determine swarm configuration
        swarm_config = await self._determine_swarm_config(intent, domain, text_clean, context)

        # Calculate overall confidence
        overall_confidence = (intent_confidence + domain_confidence) / 2

        parsed = ParsedRequest(
            original_text=text,
            intent=intent,
            domain=domain,
            entities=entities,
            keywords=keywords,
            confidence=overall_confidence,
            suggested_swarm_type=swarm_config["swarm_type"],
            suggested_agents=swarm_config["agents"],
            coordination_pattern=swarm_config["coordination"],
            priority=self._determine_priority(text_clean, entities),
            urgency=self._determine_urgency(text_clean, entities),
            complexity=self._determine_complexity(text_clean, intent, domain),
        )

        return parsed

    def _detect_intent(self, text: str) -> tuple[IntentType, float]:
        """Detect user intent from text"""

        intent_scores = {}

        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches * 0.2

            if score > 0:
                intent_scores[intent_type] = min(score, 1.0)

        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
            return best_intent, confidence
        else:
            # Default intent
            return IntentType.ANALYZE, 0.3

    def _detect_domain(self, text: str, context: ConversationContext) -> tuple[DomainType, float]:
        """Detect business domain from text and context"""

        domain_scores = {}

        # Pattern-based detection
        for domain_type, patterns in self.domain_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches * 0.3

            if score > 0:
                domain_scores[domain_type] = min(score, 1.0)

        # Context-based boost
        if context.domain_preferences:
            for domain_str, preference in context.domain_preferences.items():
                try:
                    domain_type = DomainType(domain_str)
                    if domain_type in domain_scores:
                        domain_scores[domain_type] += preference * 0.2
                    else:
                        domain_scores[domain_type] = preference * 0.1
                except ValueError:
                    continue

        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            confidence = min(domain_scores[best_domain], 1.0)
            return best_domain, confidence
        else:
            # Default domain
            return DomainType.BUSINESS, 0.3

    def _extract_entities(self, text: str) -> list[dict[str, Any]]:
        """Extract structured entities from text"""

        entities = []

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({"type": entity_type, "value": match, "position": text.find(match)})

        return entities

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract important keywords from text"""

        # Simple keyword extraction (could be enhanced with NLP libraries)
        stop_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "this",
            "that",
            "these",
            "those",
        }

        words = re.findall(r"\b\w+\b", text.lower())
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]

        # Get top keywords by frequency (simplified)
        from collections import Counter

        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]

    async def _determine_swarm_config(
        self, intent: IntentType, domain: DomainType, text: str, context: ConversationContext
    ) -> dict[str, Any]:
        """Determine appropriate swarm configuration"""

        # Map intent/domain combination to swarm type

        # Check for specific mappings
        if intent in [IntentType.ANALYZE, IntentType.EVALUATE] and domain == DomainType.BUSINESS:
            return self.swarm_mappings["business_analysis"]
        elif intent in [IntentType.RECOMMEND, IntentType.PREDICT] and domain == DomainType.BUSINESS:
            return self.swarm_mappings["strategic_planning"]
        elif intent in [IntentType.ANALYZE, IntentType.VALIDATE] and domain == DomainType.TECHNICAL:
            return self.swarm_mappings["technical_analysis"]
        elif intent == IntentType.OPTIMIZE and domain == DomainType.TECHNICAL:
            return self.swarm_mappings["architecture_review"]
        elif intent == IntentType.TROUBLESHOOT:
            return self.swarm_mappings["business_health"]
        else:
            # Default configuration based on domain
            if domain == DomainType.TECHNICAL:
                return self.swarm_mappings["technical_analysis"]
            else:
                return self.swarm_mappings["business_analysis"]

    def _determine_priority(self, text: str, entities: list[dict[str, Any]]) -> str:
        """Determine request priority"""

        high_priority_words = ["urgent", "asap", "critical", "emergency", "immediate"]
        low_priority_words = ["when possible", "low priority", "no rush", "eventually"]

        for word in high_priority_words:
            if word in text:
                return "high"

        for word in low_priority_words:
            if word in text:
                return "low"

        # Check entities for priority indicators
        for entity in entities:
            if entity["type"] == "priority":
                if any(word in entity["value"].lower() for word in high_priority_words):
                    return "high"

        return "normal"

    def _determine_urgency(self, text: str, entities: list[dict[str, Any]]) -> str:
        """Determine request urgency based on time references"""

        urgent_time_words = ["now", "today", "immediately", "asap"]

        for word in urgent_time_words:
            if word in text:
                return "high"

        # Check time entities
        for entity in entities:
            if entity["type"] == "timeframe":
                timeframe = entity["value"].lower()
                if any(word in timeframe for word in urgent_time_words):
                    return "high"
                elif "week" in timeframe or "month" in timeframe:
                    return "low"

        return "normal"

    def _determine_complexity(self, text: str, intent: IntentType, domain: DomainType) -> str:
        """Determine request complexity"""

        complex_indicators = [
            "comprehensive",
            "detailed",
            "thorough",
            "complete",
            "full analysis",
            "deep dive",
            "multiple",
            "various",
            "all aspects",
            "end-to-end",
        ]

        simple_indicators = ["quick", "brief", "simple", "basic", "summary", "overview", "just"]

        for indicator in complex_indicators:
            if indicator in text:
                return "high"

        for indicator in simple_indicators:
            if indicator in text:
                return "low"

        # Intent-based complexity
        if intent in [IntentType.PREDICT, IntentType.OPTIMIZE, IntentType.COMPARE]:
            return "high"
        elif intent in [IntentType.SUMMARIZE, IntentType.SEARCH]:
            return "low"

        return "medium"

    async def _route_and_execute(
        self, parsed_request: ParsedRequest, context: ConversationContext
    ) -> dict[str, Any]:
        """Route request to appropriate orchestrator and execute"""

        # Determine target domain for routing
        if parsed_request.domain in [
            DomainType.BUSINESS,
            DomainType.SALES,
            DomainType.MARKETING,
            DomainType.FINANCE,
        ]:
            orchestrator = self.sophia_orchestrator
            memory_domain = MemoryDomain.SOPHIA
        elif parsed_request.domain in [DomainType.TECHNICAL]:
            orchestrator = self.artemis_orchestrator
            memory_domain = MemoryDomain.ARTEMIS
        else:
            # Default to Sophia for mixed/unknown domains
            orchestrator = self.sophia_orchestrator
            memory_domain = MemoryDomain.SOPHIA

        # Prepare execution context
        execution_context = {
            "conversation_id": context.conversation_id,
            "user_id": context.user_id,
            "channel_id": context.channel_id,
            "parsed_request": parsed_request,
            "domain_preferences": context.domain_preferences,
            "priority": parsed_request.priority,
            "urgency": parsed_request.urgency,
            "complexity": parsed_request.complexity,
        }

        # Execute swarm
        result = await orchestrator.execute_swarm(
            content=parsed_request.original_text,
            swarm_type=parsed_request.suggested_swarm_type,
            context=execution_context,
            user_id=context.user_id,
            channel_id=context.channel_id,
        )

        return {
            "success": result.success,
            "content": result.content,
            "confidence": result.confidence,
            "cost": result.cost,
            "execution_time_ms": result.execution_time_ms,
            "metadata": result.metadata,
            "orchestrator_used": orchestrator.config.name,
            "memory_domain": memory_domain.value,
        }

    def _get_conversation_context(
        self, conversation_id: str, user_id: Optional[str], channel_id: Optional[str]
    ) -> ConversationContext:
        """Get or create conversation context"""

        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationContext(
                conversation_id=conversation_id, user_id=user_id, channel_id=channel_id
            )
        else:
            # Update context
            context = self.conversations[conversation_id]
            context.user_id = user_id or context.user_id
            context.channel_id = channel_id or context.channel_id
            context.updated_at = datetime.now()

        return self.conversations[conversation_id]

    def _update_conversation_state(
        self, context: ConversationContext, parsed_request: ParsedRequest, result: dict[str, Any]
    ):
        """Update conversation state based on interaction"""

        # Update domain preferences (simple learning)
        domain_key = parsed_request.domain.value
        if domain_key not in context.domain_preferences:
            context.domain_preferences[domain_key] = 0.1
        else:
            context.domain_preferences[domain_key] += 0.05

        # Decay other preferences slightly
        for key in context.domain_preferences:
            if key != domain_key:
                context.domain_preferences[key] *= 0.95

        # Update current state
        context.current_topic = parsed_request.keywords[0] if parsed_request.keywords else None
        context.last_domain = domain_key
        context.last_intent = parsed_request.intent.value
        context.updated_at = datetime.now()

        # Track task if successful
        if result.get("success"):
            execution_id = result.get("metadata", {}).get("execution_id")
            if execution_id:
                context.completed_tasks.append(execution_id)

    # Public API methods

    async def chat(
        self,
        message: str,
        conversation_id: str,
        user_id: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> str:
        """Simple chat interface that returns formatted response"""

        result = await self.process_request(message, conversation_id, user_id, channel_id)

        if result["success"]:
            execution_result = result["execution_result"]
            confidence_pct = int(execution_result.get("confidence", 0) * 100)

            response = f"""**Analysis Complete** (Confidence: {confidence_pct}%)

{execution_result.get("content", "No content available")}

*Processed by {execution_result.get("orchestrator_used", "Unknown orchestrator")} in {execution_result.get("execution_time_ms", 0) / 1000:.1f}s*"""
        else:
            response = f"Sorry, I encountered an error: {result.get('error', 'Unknown error')}"

        return response

    def get_conversation_summary(self, conversation_id: str) -> Optional[dict[str, Any]]:
        """Get summary of conversation"""

        if conversation_id not in self.conversations:
            return None

        context = self.conversations[conversation_id]

        return {
            "conversation_id": conversation_id,
            "user_id": context.user_id,
            "channel_id": context.channel_id,
            "message_count": len(context.messages),
            "domain_preferences": dict(context.domain_preferences),
            "current_topic": context.current_topic,
            "last_domain": context.last_domain,
            "last_intent": context.last_intent,
            "completed_tasks": len(context.completed_tasks),
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
        }

    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history"""

        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False

    async def schedule_recurring_analysis(
        self, message: str, interval_hours: int = 24, conversation_id: str = "scheduled"
    ) -> dict[str, Any]:
        """Schedule recurring analysis based on natural language description"""

        # Parse the request to understand what to schedule
        context = self._get_conversation_context(conversation_id, None, None)
        parsed_request = await self._parse_request(message, context)

        # Determine orchestrator
        if parsed_request.domain in [DomainType.TECHNICAL]:
            orchestrator = self.artemis_orchestrator
        else:
            orchestrator = self.sophia_orchestrator

        # Schedule recurring task
        task_id = await orchestrator.schedule_recurring_swarm(
            content=message,
            swarm_type=parsed_request.suggested_swarm_type,
            interval_hours=interval_hours,
            priority=parsed_request.priority,
            context={"scheduled_by": "natural_language_interface"},
        )

        return {
            "success": True,
            "task_id": task_id,
            "scheduled_content": message,
            "interval_hours": interval_hours,
            "swarm_type": parsed_request.suggested_swarm_type,
            "orchestrator": orchestrator.config.name,
        }

    def get_interface_statistics(self) -> dict[str, Any]:
        """Get interface usage statistics"""

        total_conversations = len(self.conversations)
        total_messages = sum(len(ctx.messages) for ctx in self.conversations.values())

        # Domain distribution
        domain_counts = {}
        for context in self.conversations.values():
            for domain, _preference in context.domain_preferences.items():
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Intent distribution (simplified)
        intent_counts = {}
        for context in self.conversations.values():
            if context.last_intent:
                intent_counts[context.last_intent] = intent_counts.get(context.last_intent, 0) + 1

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "active_conversations": len(
                [
                    ctx
                    for ctx in self.conversations.values()
                    if (datetime.now() - ctx.updated_at).total_seconds() < 3600
                ]
            ),
            "domain_distribution": domain_counts,
            "intent_distribution": intent_counts,
            "average_messages_per_conversation": (
                total_messages / total_conversations if total_conversations > 0 else 0
            ),
        }


# Global interface instance
_natural_language_interface = None


def get_natural_language_interface() -> NaturalLanguageInterface:
    """Get global natural language interface instance"""
    global _natural_language_interface
    if _natural_language_interface is None:
        _natural_language_interface = NaturalLanguageInterface()
    return _natural_language_interface


# Convenience functions for different interfaces


async def process_natural_language_request(message: str, user_id: str = "default") -> str:
    """Process natural language request and return formatted response"""
    interface = get_natural_language_interface()
    return await interface.chat(message, f"user_{user_id}", user_id)


async def schedule_natural_language_task(message: str, interval_hours: int = 24) -> dict[str, Any]:
    """Schedule recurring task from natural language description"""
    interface = get_natural_language_interface()
    return await interface.schedule_recurring_analysis(message, interval_hours)
