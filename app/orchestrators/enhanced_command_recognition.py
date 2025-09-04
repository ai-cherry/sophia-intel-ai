"""
Enhanced Command Recognition System
====================================
Advanced intent classification and command routing for orchestrators.
Solves the problem of generic responses to specific commands.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass
from fuzzywuzzy import fuzz
import asyncio

logger = logging.getLogger(__name__)


class CommandIntent(Enum):
    """Enhanced command intents with specific categories"""
    
    # API Testing & Integration
    API_TEST = "api_test"
    API_CONNECT = "api_connect"
    API_STATUS = "api_status"
    API_CONFIGURE = "api_configure"
    
    # Business Operations (Sophia)
    SALES_ANALYSIS = "sales_analysis"
    PIPELINE_REVIEW = "pipeline_review"
    REVENUE_FORECAST = "revenue_forecast"
    CLIENT_HEALTH = "client_health"
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    
    # Technical Operations (Artemis)
    CODE_REVIEW = "code_review"
    SECURITY_SCAN = "security_scan"
    PERFORMANCE_PROFILE = "performance_profile"
    ARCHITECTURE_REVIEW = "architecture_review"
    TEST_EXECUTION = "test_execution"
    
    # System Operations
    SYSTEM_HEALTH = "system_health"
    SYSTEM_RESTART = "system_restart"
    SYSTEM_CONFIG = "system_config"
    SYSTEM_LOGS = "system_logs"
    
    # Data Operations
    DATA_QUERY = "data_query"
    DATA_EXPORT = "data_export"
    REPORT_GENERATION = "report_generation"
    
    # Learning & Feedback
    PROVIDE_FEEDBACK = "provide_feedback"
    LEARN_PATTERN = "learn_pattern"
    
    # General
    GENERAL_QUERY = "general_query"
    MULTI_STEP = "multi_step"
    UNKNOWN = "unknown"


@dataclass
class CommandPattern:
    """Pattern for matching commands"""
    intent: CommandIntent
    patterns: List[str]  # Regex patterns
    keywords: List[str]  # Keywords for fuzzy matching
    priority: int = 5  # 1 (highest) to 10 (lowest)
    context_required: bool = False


@dataclass
class ParsedCommand:
    """Result of command parsing"""
    intent: CommandIntent
    confidence: float
    parameters: Dict[str, Any]
    original_message: str
    requires_tool: Optional[str] = None
    suggested_handler: Optional[str] = None


class EnhancedCommandRecognizer:
    """
    Advanced command recognition with pattern matching, fuzzy logic, and context awareness
    """
    
    def __init__(self):
        self.command_patterns = self._initialize_patterns()
        self.context_history: List[ParsedCommand] = []
        self.tool_mappings = self._initialize_tool_mappings()
        
    def _initialize_patterns(self) -> List[CommandPattern]:
        """Initialize command patterns with specific recognition rules"""
        return [
            # API Testing Patterns (HIGH PRIORITY)
            CommandPattern(
                intent=CommandIntent.API_TEST,
                patterns=[
                    r"test\s+(\w+)\s+api(?:\s+connection)?",
                    r"check\s+(\w+)\s+(?:api\s+)?connection",
                    r"validate\s+(\w+)\s+integration",
                    r"verify\s+(\w+)\s+api",
                    r"test\s+connection\s+to\s+(\w+)",
                    r"audit\s+(?:our\s+)?(\w+)\s+integration",
                    r"examine\s+(\w+)\s+integration",
                    r"analyze\s+(\w+)\s+(?:api\s+)?connection",
                    r"test\s+(?:your\s+)?api\s+connections?\s+to\s+(\w+)"
                ],
                keywords=["test", "api", "connection", "validate", "verify", "check", "audit", "integration", "examine"],
                priority=1
            ),
            CommandPattern(
                intent=CommandIntent.API_CONNECT,
                patterns=[
                    r"connect\s+to\s+(\w+)",
                    r"integrate\s+(?:with\s+)?(\w+)",
                    r"setup\s+(\w+)\s+(?:api|integration)",
                    r"configure\s+(\w+)\s+connection"
                ],
                keywords=["connect", "integrate", "setup", "configure"],
                priority=2
            ),
            CommandPattern(
                intent=CommandIntent.API_STATUS,
                patterns=[
                    r"(?:api\s+)?status\s+(?:of\s+)?(\w+)",
                    r"(\w+)\s+api\s+status",
                    r"check\s+(\w+)\s+status",
                    r"is\s+(\w+)\s+(?:api\s+)?(?:connected|working|online)"
                ],
                keywords=["status", "connected", "working", "online"],
                priority=2
            ),
            
            # Sales & Business Patterns (Sophia)
            CommandPattern(
                intent=CommandIntent.SALES_ANALYSIS,
                patterns=[
                    r"analyze\s+(?:my\s+)?sales",
                    r"sales\s+(?:performance|analysis|report)",
                    r"show\s+(?:me\s+)?sales\s+(?:metrics|data|numbers)",
                    r"how\s+are\s+(?:my\s+)?sales"
                ],
                keywords=["sales", "revenue", "deals", "quota", "performance"],
                priority=3
            ),
            CommandPattern(
                intent=CommandIntent.PIPELINE_REVIEW,
                patterns=[
                    r"(?:review|analyze|show)\s+(?:the\s+)?pipeline",
                    r"pipeline\s+(?:health|status|review)",
                    r"deals\s+in\s+(?:the\s+)?pipeline",
                    r"opportunity\s+pipeline"
                ],
                keywords=["pipeline", "opportunities", "deals", "funnel"],
                priority=3
            ),
            
            # Technical Patterns (Artemis)
            CommandPattern(
                intent=CommandIntent.CODE_REVIEW,
                patterns=[
                    r"review\s+(?:this\s+)?code",
                    r"code\s+review\s+(?:for\s+)?(.+)",
                    r"analyze\s+(?:this\s+)?(?:code|function|class)",
                    r"check\s+code\s+quality"
                ],
                keywords=["review", "code", "analyze", "quality", "refactor"],
                priority=3
            ),
            CommandPattern(
                intent=CommandIntent.SECURITY_SCAN,
                patterns=[
                    r"(?:security\s+)?scan\s+(?:for\s+)?(.+)?",
                    r"check\s+(?:for\s+)?(?:security\s+)?vulnerabilities",
                    r"vulnerability\s+(?:scan|assessment)",
                    r"security\s+(?:audit|check|review)"
                ],
                keywords=["security", "vulnerability", "scan", "audit", "threat"],
                priority=2
            ),
            
            # System Operations
            CommandPattern(
                intent=CommandIntent.SYSTEM_HEALTH,
                patterns=[
                    r"(?:system\s+)?health\s+check",
                    r"check\s+system\s+(?:health|status)",
                    r"(?:service|system)\s+status",
                    r"is\s+everything\s+(?:working|ok|healthy)"
                ],
                keywords=["health", "status", "system", "service", "check"],
                priority=3
            ),
            
            # Data Operations
            CommandPattern(
                intent=CommandIntent.DATA_QUERY,
                patterns=[
                    r"(?:show|get|fetch)\s+(?:me\s+)?(.+)\s+(?:data|metrics|statistics)",
                    r"query\s+(.+)",
                    r"what\s+(?:is|are)\s+(?:the\s+)?(.+)\s+(?:metrics|numbers|data)"
                ],
                keywords=["show", "get", "fetch", "query", "data", "metrics"],
                priority=4
            ),
            
            # Feedback & Learning
            CommandPattern(
                intent=CommandIntent.PROVIDE_FEEDBACK,
                patterns=[
                    r"(?:that|this)\s+(?:was|is)\s+(?:not\s+)?(?:correct|right|wrong|helpful)",
                    r"feedback:?\s+(.+)",
                    r"(?:good|bad|great|terrible)\s+(?:response|answer|job)"
                ],
                keywords=["feedback", "correct", "wrong", "helpful", "good", "bad"],
                priority=5
            )
        ]
    
    def _initialize_tool_mappings(self) -> Dict[str, str]:
        """Map services/APIs to their tool identifiers"""
        return {
            "gong": "gong_api",
            "hubspot": "hubspot_api",
            "salesforce": "salesforce_api",
            "slack": "slack_api",
            "github": "github_api",
            "jira": "jira_api",
            "notion": "notion_api",
            "linear": "linear_api",
            "asana": "asana_api",
            "monday": "monday_api",
            "stripe": "stripe_api",
            "segment": "segment_api",
            "mixpanel": "mixpanel_api",
            "datadog": "datadog_api",
            "sentry": "sentry_api"
        }
    
    async def classify_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> ParsedCommand:
        """
        Classify the intent of a message with high accuracy
        """
        message_lower = message.lower().strip()
        
        # First, try exact pattern matching
        parsed = self._match_patterns(message_lower)
        
        # If no high-confidence match, try fuzzy matching
        if parsed.confidence < 0.7:
            fuzzy_parsed = self._fuzzy_match(message_lower)
            if fuzzy_parsed.confidence > parsed.confidence:
                parsed = fuzzy_parsed
        
        # Consider context if available
        if context and self.context_history:
            parsed = self._apply_context(parsed, context)
        
        # Extract parameters based on intent
        parsed.parameters = self._extract_parameters(message_lower, parsed.intent)
        
        # Determine required tool
        parsed.requires_tool = self._determine_required_tool(parsed)
        
        # Suggest handler
        parsed.suggested_handler = self._get_handler_for_intent(parsed.intent)
        
        # Store in context history
        self.context_history.append(parsed)
        if len(self.context_history) > 10:
            self.context_history.pop(0)
        
        logger.info(f"Classified intent: {parsed.intent} with confidence {parsed.confidence:.2f}")
        return parsed
    
    def _match_patterns(self, message: str) -> ParsedCommand:
        """Match message against defined patterns"""
        best_match = ParsedCommand(
            intent=CommandIntent.UNKNOWN,
            confidence=0.0,
            parameters={},
            original_message=message
        )
        
        for pattern in self.command_patterns:
            for regex_pattern in pattern.patterns:
                match = re.search(regex_pattern, message)
                if match:
                    # Calculate confidence based on pattern match and priority
                    base_confidence = 0.9
                    priority_bonus = (10 - pattern.priority) / 10 * 0.1
                    confidence = min(base_confidence + priority_bonus, 1.0)
                    
                    if confidence > best_match.confidence:
                        best_match = ParsedCommand(
                            intent=pattern.intent,
                            confidence=confidence,
                            parameters={"match_groups": match.groups()},
                            original_message=message
                        )
                        break
        
        return best_match
    
    def _fuzzy_match(self, message: str) -> ParsedCommand:
        """Use fuzzy matching for intent classification"""
        best_match = ParsedCommand(
            intent=CommandIntent.UNKNOWN,
            confidence=0.0,
            parameters={},
            original_message=message
        )
        
        for pattern in self.command_patterns:
            # Check keyword similarity
            for keyword in pattern.keywords:
                if keyword in message:
                    # Calculate fuzzy score
                    score = fuzz.partial_ratio(keyword, message) / 100
                    
                    # Adjust confidence based on priority
                    priority_factor = (10 - pattern.priority) / 10
                    confidence = score * 0.7 * (1 + priority_factor * 0.3)
                    
                    if confidence > best_match.confidence:
                        best_match = ParsedCommand(
                            intent=pattern.intent,
                            confidence=confidence,
                            parameters={"matched_keyword": keyword},
                            original_message=message
                        )
        
        return best_match
    
    def _extract_parameters(self, message: str, intent: CommandIntent) -> Dict[str, Any]:
        """Extract relevant parameters based on intent"""
        parameters = {}
        
        # Extract API/service names
        if intent in [CommandIntent.API_TEST, CommandIntent.API_CONNECT, CommandIntent.API_STATUS]:
            for service, tool_id in self.tool_mappings.items():
                if service in message:
                    parameters["service"] = service
                    parameters["tool_id"] = tool_id
                    break
        
        # Extract time periods
        time_patterns = {
            "today": "today",
            "yesterday": "yesterday",
            "this week": "current_week",
            "last week": "last_week",
            "this month": "current_month",
            "last month": "last_month",
            "this quarter": "current_quarter",
            "last quarter": "last_quarter"
        }
        for pattern, value in time_patterns.items():
            if pattern in message:
                parameters["time_period"] = value
                break
        
        # Extract numeric values
        numbers = re.findall(r'\d+', message)
        if numbers:
            parameters["numeric_values"] = numbers
        
        # Extract quoted strings
        quotes = re.findall(r'"([^"]*)"', message)
        if quotes:
            parameters["quoted_text"] = quotes
        
        return parameters
    
    def _apply_context(self, parsed: ParsedCommand, context: Dict[str, Any]) -> ParsedCommand:
        """Apply context to improve classification"""
        if not self.context_history:
            return parsed
        
        last_command = self.context_history[-1]
        
        # If current intent is uncertain, check if it's a follow-up
        if parsed.confidence < 0.5:
            # Check for pronouns indicating continuation
            pronouns = ["it", "that", "this", "them", "those"]
            if any(pronoun in parsed.original_message.lower() for pronoun in pronouns):
                # Likely a follow-up to previous command
                parsed.intent = last_command.intent
                parsed.confidence = min(parsed.confidence + 0.3, 0.8)
                parsed.parameters["is_followup"] = True
                parsed.parameters["previous_context"] = last_command.parameters
        
        return parsed
    
    def _determine_required_tool(self, parsed: ParsedCommand) -> Optional[str]:
        """Determine which tool/API is required for the command"""
        if "tool_id" in parsed.parameters:
            return parsed.parameters["tool_id"]
        
        # Map intents to default tools
        intent_tool_map = {
            CommandIntent.SALES_ANALYSIS: "salesforce_api",
            CommandIntent.PIPELINE_REVIEW: "hubspot_api",
            CommandIntent.CLIENT_HEALTH: "hubspot_api",
            CommandIntent.CODE_REVIEW: "github_api",
            CommandIntent.SECURITY_SCAN: "security_scanner",
            CommandIntent.SYSTEM_HEALTH: "system_monitor"
        }
        
        return intent_tool_map.get(parsed.intent)
    
    def _get_handler_for_intent(self, intent: CommandIntent) -> str:
        """Get the suggested handler method for an intent"""
        handler_map = {
            CommandIntent.API_TEST: "handle_api_test",
            CommandIntent.API_CONNECT: "handle_api_connect",
            CommandIntent.API_STATUS: "handle_api_status",
            CommandIntent.SALES_ANALYSIS: "handle_sales_analysis",
            CommandIntent.PIPELINE_REVIEW: "handle_pipeline_review",
            CommandIntent.CODE_REVIEW: "handle_code_review",
            CommandIntent.SECURITY_SCAN: "handle_security_scan",
            CommandIntent.SYSTEM_HEALTH: "handle_system_health",
            CommandIntent.DATA_QUERY: "handle_data_query",
            CommandIntent.PROVIDE_FEEDBACK: "handle_feedback",
            CommandIntent.GENERAL_QUERY: "handle_general_query"
        }
        
        return handler_map.get(intent, "handle_general_query")
    
    def get_intent_description(self, intent: CommandIntent) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            CommandIntent.API_TEST: "Test API connection",
            CommandIntent.API_CONNECT: "Connect to API",
            CommandIntent.API_STATUS: "Check API status",
            CommandIntent.SALES_ANALYSIS: "Analyze sales performance",
            CommandIntent.PIPELINE_REVIEW: "Review sales pipeline",
            CommandIntent.CODE_REVIEW: "Review code quality",
            CommandIntent.SECURITY_SCAN: "Scan for vulnerabilities",
            CommandIntent.SYSTEM_HEALTH: "Check system health",
            CommandIntent.DATA_QUERY: "Query data",
            CommandIntent.PROVIDE_FEEDBACK: "Process user feedback"
        }
        
        return descriptions.get(intent, "Process query")