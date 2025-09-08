"""
Specialized Agents for Sales Intelligence Swarm

This module contains all the specialized agents for real-time call analysis:
- TranscriptionAgent: Real-time speech-to-text
- SentimentAgent: Emotion and engagement analysis
- CompetitiveAgent: Competitor mention tracking
- RiskAssessmentAgent: Deal risk evaluation
- CoachingAgent: Sales technique feedback
- SummaryAgent: Call outcome synthesis
"""

import asyncio
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from .gong_realtime import RealtimeCallData, TranscriptSegment

logger = logging.getLogger(__name__)


class AgentPriority(str, Enum):
    """Priority levels for agent processing"""

    CRITICAL = "critical"  # Immediate alerts, deal risks
    HIGH = "high"  # Important insights, coaching
    MEDIUM = "medium"  # Analysis, patterns
    LOW = "low"  # Background processing, summaries


class ConfidenceLevel(str, Enum):
    """Confidence levels for agent outputs"""

    HIGH = "high"  # 90%+ confidence
    MEDIUM = "medium"  # 70-90% confidence
    LOW = "low"  # 50-70% confidence
    UNCERTAIN = "uncertain"  # <50% confidence


@dataclass
class AgentOutput:
    """Base output structure for all agents"""

    agent_id: str
    agent_type: str
    call_id: str
    timestamp: datetime
    priority: AgentPriority
    confidence: ConfidenceLevel
    data: dict[str, Any]
    requires_action: bool = False
    expiry_time: Optional[datetime] = None


@dataclass
class AgentContext:
    """Context available to all agents"""

    call_data: RealtimeCallData
    historical_data: dict[str, Any]
    user_preferences: dict[str, Any]
    team_settings: dict[str, Any]


class BaseSalesAgent(ABC):
    """Base class for all sales intelligence agents"""

    def __init__(self, agent_id: str, config: dict[str, Any] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.is_active = False
        self.processing_queue = asyncio.Queue()
        self.output_callbacks: list[callable] = []

    @abstractmethod
    async def process(self, context: AgentContext) -> AgentOutput:
        """Process context and return analysis"""
        pass

    @abstractmethod
    def get_agent_type(self) -> str:
        """Return the agent type identifier"""
        pass

    def register_output_callback(self, callback: callable):
        """Register callback for agent outputs"""
        self.output_callbacks.append(callback)

    async def emit_output(self, output: AgentOutput):
        """Emit output to registered callbacks"""
        for callback in self.output_callbacks:
            try:
                await callback(output)
            except Exception as e:
                logger.error(f"Error in output callback for {self.agent_id}: {e}")

    async def start(self):
        """Start the agent processing loop"""
        self.is_active = True
        while self.is_active:
            try:
                context = await asyncio.wait_for(
                    self.processing_queue.get(), timeout=1.0
                )
                output = await self.process(context)
                await self.emit_output(output)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in agent {self.agent_id}: {e}")

    async def stop(self):
        """Stop the agent"""
        self.is_active = False

    async def enqueue_context(self, context: AgentContext):
        """Add context to processing queue"""
        await self.processing_queue.put(context)


class TranscriptionAgent(BaseSalesAgent):
    """Real-time speech-to-text with conversation tracking"""

    def __init__(self, agent_id: str = "transcription", config: dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.speaker_profiles: dict[str, dict] = {}
        self.conversation_flow: list[str] = []

    def get_agent_type(self) -> str:
        return "transcription"

    async def process(self, context: AgentContext) -> AgentOutput:
        """Process audio and transcript data"""
        call_data = context.call_data
        latest_segments = self._get_latest_segments(call_data.transcripts)

        analysis = {
            "new_segments": len(latest_segments),
            "speaker_changes": self._detect_speaker_changes(latest_segments),
            "speaking_pace": self._analyze_speaking_pace(latest_segments),
            "clarity_issues": self._detect_clarity_issues(latest_segments),
            "conversation_flow": self._update_conversation_flow(latest_segments),
        }

        # Determine priority based on clarity issues or important keywords
        priority = AgentPriority.MEDIUM
        if analysis["clarity_issues"] > 0.3:
            priority = AgentPriority.HIGH

        return AgentOutput(
            agent_id=self.agent_id,
            agent_type=self.get_agent_type(),
            call_id=call_data.metadata.call_id,
            timestamp=datetime.now(),
            priority=priority,
            confidence=ConfidenceLevel.HIGH,
            data=analysis,
            requires_action=analysis["clarity_issues"] > 0.5,
        )

    def _get_latest_segments(
        self, transcripts: list[TranscriptSegment], since_seconds: int = 30
    ) -> list[TranscriptSegment]:
        """Get transcript segments from last N seconds"""
        cutoff = time.time() - since_seconds
        return [seg for seg in transcripts if seg.start_time > cutoff]

    def _detect_speaker_changes(self, segments: list[TranscriptSegment]) -> int:
        """Count speaker changes in recent segments"""
        if len(segments) < 2:
            return 0

        changes = 0
        for i in range(1, len(segments)):
            if segments[i].speaker_id != segments[i - 1].speaker_id:
                changes += 1
        return changes

    def _analyze_speaking_pace(
        self, segments: list[TranscriptSegment]
    ) -> dict[str, float]:
        """Analyze speaking pace for each participant"""
        pace_analysis = {}

        for segment in segments:
            if segment.speaker_id not in pace_analysis:
                pace_analysis[segment.speaker_id] = {"words": 0, "duration": 0.0}

            word_count = len(segment.text.split())
            duration = segment.end_time - segment.start_time

            pace_analysis[segment.speaker_id]["words"] += word_count
            pace_analysis[segment.speaker_id]["duration"] += duration

        # Calculate words per minute
        for speaker in pace_analysis:
            total_words = pace_analysis[speaker]["words"]
            total_duration = pace_analysis[speaker]["duration"]
            if total_duration > 0:
                pace_analysis[speaker]["wpm"] = (total_words / total_duration) * 60
            else:
                pace_analysis[speaker]["wpm"] = 0

        return pace_analysis

    def _detect_clarity_issues(self, segments: list[TranscriptSegment]) -> float:
        """Detect potential clarity or transcription issues"""
        if not segments:
            return 0.0

        total_confidence = sum(seg.confidence for seg in segments)
        avg_confidence = total_confidence / len(segments)

        # Return clarity issue score (1 - confidence)
        return 1.0 - avg_confidence

    def _update_conversation_flow(self, segments: list[TranscriptSegment]) -> list[str]:
        """Track conversation flow and turn-taking"""
        flow = []
        current_speaker = None

        for segment in segments:
            if segment.speaker_id != current_speaker:
                flow.append(segment.speaker_id)
                current_speaker = segment.speaker_id

        return flow


class SentimentAgent(BaseSalesAgent):
    """Multi-modal emotion and engagement analysis"""

    def __init__(self, agent_id: str = "sentiment", config: dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.emotion_history: dict[str, list] = {}
        self.engagement_patterns: dict[str, float] = {}

    def get_agent_type(self) -> str:
        return "sentiment"

    async def process(self, context: AgentContext) -> AgentOutput:
        """Analyze sentiment and emotional state"""
        call_data = context.call_data
        recent_transcripts = self._get_recent_transcripts(call_data.transcripts)

        analysis = {
            "overall_sentiment": self._analyze_overall_sentiment(recent_transcripts),
            "speaker_emotions": self._analyze_speaker_emotions(recent_transcripts),
            "engagement_level": self._calculate_engagement_level(recent_transcripts),
            "stress_indicators": self._detect_stress_indicators(recent_transcripts),
            "rapport_score": self._calculate_rapport_score(recent_transcripts),
            "emotional_trajectory": self._track_emotional_trajectory(
                recent_transcripts
            ),
        }

        # Determine priority based on negative sentiment or stress
        priority = AgentPriority.MEDIUM
        if analysis["overall_sentiment"] < -0.3 or analysis["stress_indicators"] > 0.7:
            priority = AgentPriority.HIGH

        # High confidence for established patterns, lower for single data points
        confidence = (
            ConfidenceLevel.HIGH
            if len(recent_transcripts) > 5
            else ConfidenceLevel.MEDIUM
        )

        return AgentOutput(
            agent_id=self.agent_id,
            agent_type=self.get_agent_type(),
            call_id=call_data.metadata.call_id,
            timestamp=datetime.now(),
            priority=priority,
            confidence=confidence,
            data=analysis,
            requires_action=analysis["stress_indicators"] > 0.8,
        )

    def _get_recent_transcripts(
        self, transcripts: list[TranscriptSegment], seconds: int = 60
    ) -> list[TranscriptSegment]:
        """Get recent transcript segments"""
        cutoff = time.time() - seconds
        return [seg for seg in transcripts if seg.start_time > cutoff]

    def _analyze_overall_sentiment(self, segments: list[TranscriptSegment]) -> float:
        """Calculate overall sentiment score (-1 to 1)"""
        if not segments:
            return 0.0

        positive_keywords = {
            "great",
            "excellent",
            "perfect",
            "love",
            "amazing",
            "wonderful",
            "fantastic",
            "outstanding",
            "brilliant",
            "excited",
            "interested",
        }

        negative_keywords = {
            "terrible",
            "awful",
            "hate",
            "horrible",
            "disappointed",
            "frustrated",
            "concerned",
            "worried",
            "problem",
            "issue",
            "difficult",
            "impossible",
        }

        total_score = 0
        for segment in segments:
            words = segment.text.lower().split()
            segment_score = 0

            for word in words:
                if word in positive_keywords:
                    segment_score += 1
                elif word in negative_keywords:
                    segment_score -= 1

            total_score += segment_score

        # Normalize by number of segments
        return max(-1.0, min(1.0, total_score / len(segments)))

    def _analyze_speaker_emotions(
        self, segments: list[TranscriptSegment]
    ) -> dict[str, dict]:
        """Analyze emotions for each speaker"""
        speaker_emotions = {}

        for segment in segments:
            if segment.speaker_id not in speaker_emotions:
                speaker_emotions[segment.speaker_id] = {
                    "excitement": 0.0,
                    "concern": 0.0,
                    "confidence": 0.0,
                    "hesitation": 0.0,
                }

            text = segment.text.lower()

            # Simple keyword-based emotion detection
            if any(word in text for word in ["excited", "thrilled", "love", "amazing"]):
                speaker_emotions[segment.speaker_id]["excitement"] += 0.1

            if any(
                word in text for word in ["concerned", "worried", "issue", "problem"]
            ):
                speaker_emotions[segment.speaker_id]["concern"] += 0.1

            if any(word in text for word in ["definitely", "absolutely", "certainly"]):
                speaker_emotions[segment.speaker_id]["confidence"] += 0.1

            if any(word in text for word in ["maybe", "perhaps", "might", "possibly"]):
                speaker_emotions[segment.speaker_id]["hesitation"] += 0.1

        # Normalize scores
        for speaker in speaker_emotions:
            for emotion in speaker_emotions[speaker]:
                speaker_emotions[speaker][emotion] = min(
                    1.0, speaker_emotions[speaker][emotion]
                )

        return speaker_emotions

    def _calculate_engagement_level(self, segments: list[TranscriptSegment]) -> float:
        """Calculate overall engagement level (0 to 1)"""
        if not segments:
            return 0.5

        engagement_indicators = {
            "questions": ["?", "what", "how", "when", "where", "why"],
            "agreements": ["yes", "absolutely", "definitely", "agree", "exactly"],
            "elaborations": ["specifically", "for example", "such as", "including"],
        }

        total_indicators = 0
        total_words = 0

        for segment in segments:
            words = segment.text.lower().split()
            total_words += len(words)

            for _category, keywords in engagement_indicators.items():
                for keyword in keywords:
                    if keyword in segment.text.lower():
                        total_indicators += 1

        if total_words == 0:
            return 0.5

        return min(1.0, total_indicators / (total_words / 10))  # Normalize

    def _detect_stress_indicators(self, segments: list[TranscriptSegment]) -> float:
        """Detect stress indicators in speech (0 to 1)"""
        stress_keywords = {
            "pressure",
            "stress",
            "urgent",
            "deadline",
            "rush",
            "busy",
            "overwhelming",
            "difficult",
            "challenging",
            "struggle",
        }

        stress_score = 0
        for segment in segments:
            for keyword in stress_keywords:
                if keyword in segment.text.lower():
                    stress_score += 0.1

        return min(1.0, stress_score)

    def _calculate_rapport_score(self, segments: list[TranscriptSegment]) -> float:
        """Calculate rapport between speakers (0 to 1)"""
        if len(segments) < 2:
            return 0.5

        rapport_indicators = 0
        total_interactions = 0

        for i in range(1, len(segments)):
            if segments[i].speaker_id != segments[i - 1].speaker_id:
                total_interactions += 1

                # Check for mirroring language
                current_words = set(segments[i].text.lower().split())
                previous_words = set(segments[i - 1].text.lower().split())

                if current_words & previous_words:  # Common words indicate mirroring
                    rapport_indicators += 1

        if total_interactions == 0:
            return 0.5

        return rapport_indicators / total_interactions

    def _track_emotional_trajectory(
        self, segments: list[TranscriptSegment]
    ) -> list[dict]:
        """Track how emotions change over time"""
        trajectory = []
        window_size = 5  # Analyze in windows of 5 segments

        for i in range(0, len(segments), window_size):
            window = segments[i : i + window_size]
            sentiment = self._analyze_overall_sentiment(window)

            trajectory.append(
                {
                    "timestamp": window[0].start_time if window else time.time(),
                    "sentiment": sentiment,
                    "segment_count": len(window),
                }
            )

        return trajectory


class CompetitiveAgent(BaseSalesAgent):
    """Real-time competitor mention and positioning analysis"""

    def __init__(self, agent_id: str = "competitive", config: dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.competitor_database = self._load_competitor_database()
        self.mention_history: list[dict] = []

    def get_agent_type(self) -> str:
        return "competitive"

    def _load_competitor_database(self) -> dict[str, dict]:
        """Load competitor information and keywords"""
        # In real implementation, this would load from a database
        return {
            "salesforce": {
                "aliases": ["salesforce", "sfdc", "sf"],
                "products": ["sales cloud", "service cloud", "marketing cloud"],
                "keywords": ["crm", "customer relationship"],
            },
            "hubspot": {
                "aliases": ["hubspot", "hub spot"],
                "products": ["hubspot crm", "marketing hub", "sales hub"],
                "keywords": ["inbound", "marketing automation"],
            },
            "pipedrive": {
                "aliases": ["pipedrive", "pipe drive"],
                "products": ["pipedrive crm"],
                "keywords": ["pipeline", "deal management"],
            },
        }

    async def process(self, context: AgentContext) -> AgentOutput:
        """Detect and analyze competitor mentions"""
        call_data = context.call_data
        recent_transcripts = self._get_recent_transcripts(call_data.transcripts)

        analysis = {
            "competitor_mentions": self._detect_competitor_mentions(recent_transcripts),
            "comparison_statements": self._find_comparison_statements(
                recent_transcripts
            ),
            "feature_discussions": self._analyze_feature_discussions(
                recent_transcripts
            ),
            "pricing_mentions": self._detect_pricing_discussions(recent_transcripts),
            "competitive_positioning": self._analyze_positioning(recent_transcripts),
            "threat_level": self._assess_competitive_threat(recent_transcripts),
        }

        # High priority for direct competitor mentions
        priority = AgentPriority.MEDIUM
        if analysis["competitor_mentions"] or analysis["threat_level"] > 0.7:
            priority = AgentPriority.HIGH

        return AgentOutput(
            agent_id=self.agent_id,
            agent_type=self.get_agent_type(),
            call_id=call_data.metadata.call_id,
            timestamp=datetime.now(),
            priority=priority,
            confidence=ConfidenceLevel.HIGH,
            data=analysis,
            requires_action=analysis["threat_level"] > 0.8,
        )

    def _get_recent_transcripts(
        self, transcripts: list[TranscriptSegment], seconds: int = 120
    ) -> list[TranscriptSegment]:
        """Get recent transcript segments for competitive analysis"""
        cutoff = time.time() - seconds
        return [seg for seg in transcripts if seg.start_time > cutoff]

    def _detect_competitor_mentions(
        self, segments: list[TranscriptSegment]
    ) -> list[dict]:
        """Detect explicit competitor mentions"""
        mentions = []

        for segment in segments:
            text = segment.text.lower()

            for competitor, data in self.competitor_database.items():
                # Check aliases and products
                all_terms = data["aliases"] + data["products"] + data["keywords"]

                for term in all_terms:
                    if term.lower() in text:
                        mentions.append(
                            {
                                "competitor": competitor,
                                "term": term,
                                "context": segment.text,
                                "speaker": segment.speaker_name,
                                "timestamp": segment.start_time,
                                "confidence": self._calculate_mention_confidence(
                                    text, term
                                ),
                            }
                        )

        return mentions

    def _calculate_mention_confidence(self, text: str, term: str) -> float:
        """Calculate confidence that a mention is actually about the competitor"""
        # Simple confidence based on context
        confidence = 0.7  # Base confidence

        # Higher confidence if mentioned with specific context
        competitive_context = [
            "versus",
            "compared to",
            "better than",
            "instead of",
            "alternative",
        ]
        if any(ctx in text.lower() for ctx in competitive_context):
            confidence += 0.2

        # Lower confidence if it might be ambiguous
        ambiguous_terms = ["cloud", "crm", "sales"]
        if term.lower() in ambiguous_terms:
            confidence -= 0.1

        return max(0.1, min(1.0, confidence))

    def _find_comparison_statements(
        self, segments: list[TranscriptSegment]
    ) -> list[dict]:
        """Find statements that compare products or features"""
        comparison_patterns = [
            r"(better than|worse than|compared to|versus|vs\.?)\s+(\w+)",
            r"(\w+)\s+(is|has)\s+(more|less|better|worse)",
            r"(unlike|like|similar to)\s+(\w+)",
        ]

        comparisons = []

        for segment in segments:
            text = segment.text.lower()

            for pattern in comparison_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    comparisons.append(
                        {
                            "statement": match.group(0),
                            "full_context": segment.text,
                            "speaker": segment.speaker_name,
                            "timestamp": segment.start_time,
                        }
                    )

        return comparisons

    def _analyze_feature_discussions(
        self, segments: list[TranscriptSegment]
    ) -> dict[str, list]:
        """Analyze discussions about specific features"""
        feature_keywords = {
            "integration": ["api", "integration", "connect", "sync"],
            "reporting": ["report", "analytics", "dashboard", "metrics"],
            "automation": ["automate", "workflow", "trigger", "rule"],
            "customization": ["custom", "configure", "personalize", "tailor"],
        }

        feature_discussions = {}

        for feature, keywords in feature_keywords.items():
            feature_discussions[feature] = []

            for segment in segments:
                text = segment.text.lower()
                if any(keyword in text for keyword in keywords):
                    feature_discussions[feature].append(
                        {
                            "context": segment.text,
                            "speaker": segment.speaker_name,
                            "timestamp": segment.start_time,
                        }
                    )

        return feature_discussions

    def _detect_pricing_discussions(
        self, segments: list[TranscriptSegment]
    ) -> list[dict]:
        """Detect discussions about pricing and costs"""
        pricing_keywords = [
            "price",
            "cost",
            "expensive",
            "cheap",
            "budget",
            "$",
            "dollar",
        ]
        pricing_discussions = []

        for segment in segments:
            text = segment.text.lower()
            if any(keyword in text for keyword in pricing_keywords):
                pricing_discussions.append(
                    {
                        "context": segment.text,
                        "speaker": segment.speaker_name,
                        "timestamp": segment.start_time,
                        "type": self._classify_pricing_discussion(text),
                    }
                )

        return pricing_discussions

    def _classify_pricing_discussion(self, text: str) -> str:
        """Classify the type of pricing discussion"""
        if any(word in text for word in ["expensive", "costly", "high"]):
            return "price_concern"
        elif any(word in text for word in ["budget", "afford", "cost"]):
            return "budget_discussion"
        elif any(word in text for word in ["cheap", "lower", "discount"]):
            return "price_comparison"
        else:
            return "general_pricing"

    def _analyze_positioning(self, segments: list[TranscriptSegment]) -> dict[str, Any]:
        """Analyze how our solution is positioned vs competitors"""
        positioning = {
            "strengths_mentioned": [],
            "weaknesses_mentioned": [],
            "differentiation_points": [],
            "positioning_strategy": "unknown",
        }

        strength_indicators = ["better", "superior", "advantage", "strength", "unique"]
        weakness_indicators = ["limitation", "weakness", "lacks", "missing", "cannot"]

        for segment in segments:
            text = segment.text.lower()

            for indicator in strength_indicators:
                if indicator in text:
                    positioning["strengths_mentioned"].append(
                        {"context": segment.text, "timestamp": segment.start_time}
                    )

            for indicator in weakness_indicators:
                if indicator in text:
                    positioning["weaknesses_mentioned"].append(
                        {"context": segment.text, "timestamp": segment.start_time}
                    )

        return positioning

    def _assess_competitive_threat(self, segments: list[TranscriptSegment]) -> float:
        """Assess the level of competitive threat (0 to 1)"""
        threat_level = 0.0

        for segment in segments:
            text = segment.text.lower()

            # High threat indicators
            if any(
                phrase in text
                for phrase in ["already using", "current vendor", "satisfied with"]
            ):
                threat_level += 0.3

            # Medium threat indicators
            if any(
                phrase in text for phrase in ["looking at", "considering", "evaluating"]
            ):
                threat_level += 0.2

            # Positive indicators (reduce threat)
            if any(
                phrase in text
                for phrase in [
                    "not satisfied",
                    "problems with",
                    "looking for alternative",
                ]
            ):
                threat_level -= 0.1

        return max(0.0, min(1.0, threat_level))


class RiskAssessmentAgent(BaseSalesAgent):
    """Predictive deal outcome and risk scoring"""

    def __init__(
        self, agent_id: str = "risk_assessment", config: dict[str, Any] = None
    ):
        super().__init__(agent_id, config)
        self.risk_indicators = self._load_risk_indicators()
        self.historical_patterns: dict[str, float] = {}

    def get_agent_type(self) -> str:
        return "risk_assessment"

    def _load_risk_indicators(self) -> dict[str, dict]:
        """Load risk assessment indicators and patterns"""
        return {
            "positive_signals": {
                "keywords": [
                    "interested",
                    "excited",
                    "perfect",
                    "exactly",
                    "love",
                    "need",
                ],
                "weight": 0.8,
            },
            "negative_signals": {
                "keywords": ["concerned", "expensive", "complicated", "busy", "later"],
                "weight": -0.6,
            },
            "buying_signals": {
                "keywords": [
                    "when can",
                    "how soon",
                    "next steps",
                    "contract",
                    "timeline",
                ],
                "weight": 1.0,
            },
            "stall_signals": {
                "keywords": ["think about", "discuss internally", "not ready", "maybe"],
                "weight": -0.4,
            },
        }

    async def process(self, context: AgentContext) -> AgentOutput:
        """Assess deal risk and probability"""
        call_data = context.call_data
        recent_transcripts = self._get_recent_transcripts(call_data.transcripts)

        analysis = {
            "overall_risk_score": self._calculate_overall_risk(recent_transcripts),
            "buying_signals": self._detect_buying_signals(recent_transcripts),
            "red_flags": self._identify_red_flags(recent_transcripts),
            "engagement_quality": self._assess_engagement_quality(recent_transcripts),
            "decision_maker_involvement": self._assess_decision_maker_involvement(
                recent_transcripts, context
            ),
            "timeline_indicators": self._analyze_timeline_indicators(
                recent_transcripts
            ),
            "probability_score": self._calculate_win_probability(
                recent_transcripts, context
            ),
        }

        # High priority for high-risk situations
        priority = AgentPriority.MEDIUM
        if analysis["overall_risk_score"] > 0.7 or analysis["probability_score"] < 0.3:
            priority = AgentPriority.HIGH

        return AgentOutput(
            agent_id=self.agent_id,
            agent_type=self.get_agent_type(),
            call_id=call_data.metadata.call_id,
            timestamp=datetime.now(),
            priority=priority,
            confidence=ConfidenceLevel.HIGH,
            data=analysis,
            requires_action=analysis["overall_risk_score"] > 0.8,
        )

    def _get_recent_transcripts(
        self, transcripts: list[TranscriptSegment], seconds: int = 300
    ) -> list[TranscriptSegment]:
        """Get recent transcript segments for risk analysis"""
        cutoff = time.time() - seconds
        return [seg for seg in transcripts if seg.start_time > cutoff]

    def _calculate_overall_risk(self, segments: list[TranscriptSegment]) -> float:
        """Calculate overall deal risk score (0 to 1)"""
        if not segments:
            return 0.5  # Neutral risk for no data

        total_score = 0.0
        total_weight = 0.0

        for segment in segments:
            text = segment.text.lower()

            for _category, data in self.risk_indicators.items():
                for keyword in data["keywords"]:
                    if keyword in text:
                        total_score += data["weight"]
                        total_weight += abs(data["weight"])

        if total_weight == 0:
            return 0.5

        # Normalize to 0-1 scale where 0 is low risk, 1 is high risk
        normalized_score = 0.5 - (total_score / total_weight) * 0.5
        return max(0.0, min(1.0, normalized_score))

    def _detect_buying_signals(self, segments: list[TranscriptSegment]) -> list[dict]:
        """Detect explicit buying signals"""
        buying_patterns = [
            r"when (can|do|will)",
            r"how (soon|quickly|fast)",
            r"next steps?",
            r"move forward",
            r"get started",
            r"implementation",
            r"contract|agreement",
            r"pricing|price",
        ]

        signals = []

        for segment in segments:
            text = segment.text.lower()

            for pattern in buying_patterns:
                if re.search(pattern, text):
                    signals.append(
                        {
                            "signal": pattern,
                            "context": segment.text,
                            "speaker": segment.speaker_name,
                            "timestamp": segment.start_time,
                            "strength": self._assess_signal_strength(text, pattern),
                        }
                    )

        return signals

    def _assess_signal_strength(self, text: str, pattern: str) -> float:
        """Assess the strength of a buying signal"""
        # Strong signals
        if any(
            phrase in text for phrase in ["definitely", "absolutely", "immediately"]
        ):
            return 1.0

        # Medium signals
        if any(phrase in text for phrase in ["probably", "likely", "soon"]):
            return 0.7

        # Weak signals
        if any(phrase in text for phrase in ["maybe", "possibly", "eventually"]):
            return 0.3

        return 0.5  # Default medium strength

    def _identify_red_flags(self, segments: list[TranscriptSegment]) -> list[dict]:
        """Identify potential deal red flags"""
        red_flag_patterns = {
            "budget_concerns": ["too expensive", "over budget", "can't afford"],
            "timing_issues": ["not ready", "too busy", "maybe later"],
            "authority_issues": ["need to check", "ask my boss", "team decision"],
            "competition": ["other vendors", "comparing", "already have"],
            "feature_gaps": ["missing", "doesn't have", "can't do"],
        }

        red_flags = []

        for segment in segments:
            text = segment.text.lower()

            for flag_type, patterns in red_flag_patterns.items():
                for pattern in patterns:
                    if pattern in text:
                        red_flags.append(
                            {
                                "type": flag_type,
                                "indicator": pattern,
                                "context": segment.text,
                                "speaker": segment.speaker_name,
                                "timestamp": segment.start_time,
                                "severity": self._assess_red_flag_severity(flag_type),
                            }
                        )

        return red_flags

    def _assess_red_flag_severity(self, flag_type: str) -> float:
        """Assess severity of different red flag types"""
        severity_map = {
            "budget_concerns": 0.8,
            "timing_issues": 0.6,
            "authority_issues": 0.7,
            "competition": 0.5,
            "feature_gaps": 0.9,
        }
        return severity_map.get(flag_type, 0.5)

    def _assess_engagement_quality(self, segments: list[TranscriptSegment]) -> float:
        """Assess quality of prospect engagement (0 to 1)"""
        if not segments:
            return 0.5

        engagement_score = 0.0

        # Count questions from prospects
        prospect_questions = 0
        total_prospect_segments = 0

        for segment in segments:
            if not self._is_internal_speaker(segment.speaker_name):
                total_prospect_segments += 1
                if "?" in segment.text:
                    prospect_questions += 1
                    engagement_score += 0.2

                # Detailed responses indicate engagement
                if len(segment.text.split()) > 10:
                    engagement_score += 0.1

        # Normalize by prospect participation
        if total_prospect_segments > 0:
            engagement_score /= total_prospect_segments

        return min(1.0, engagement_score)

    def _is_internal_speaker(self, speaker_name: str) -> bool:
        """Determine if speaker is internal team member"""
        # Simple heuristic - in real implementation, use participant data
        internal_indicators = ["sales", "account", "manager", "@company.com"]
        return any(
            indicator in speaker_name.lower() for indicator in internal_indicators
        )

    def _assess_decision_maker_involvement(
        self, segments: list[TranscriptSegment], context: AgentContext
    ) -> dict[str, Any]:
        """Assess decision maker participation and engagement"""
        # In real implementation, use participant metadata to identify decision makers
        decision_maker_analysis = {
            "identified_decision_makers": [],
            "participation_level": 0.5,
            "decision_authority_signals": [],
            "involvement_quality": 0.5,
        }

        authority_signals = [
            "my decision",
            "I decide",
            "I choose",
            "my budget",
            "I approve",
        ]

        for segment in segments:
            text = segment.text.lower()

            for signal in authority_signals:
                if signal in text:
                    decision_maker_analysis["decision_authority_signals"].append(
                        {
                            "signal": signal,
                            "speaker": segment.speaker_name,
                            "context": segment.text,
                        }
                    )

        return decision_maker_analysis

    def _analyze_timeline_indicators(
        self, segments: list[TranscriptSegment]
    ) -> dict[str, Any]:
        """Analyze timeline and urgency indicators"""
        timeline_patterns = {
            "urgent": ["asap", "immediately", "urgent", "right away"],
            "short_term": ["this month", "this quarter", "soon", "quickly"],
            "medium_term": ["next quarter", "few months", "end of year"],
            "long_term": ["next year", "eventually", "future", "someday"],
        }

        timeline_analysis = {
            "urgency_level": 0.5,
            "timeline_mentions": [],
            "urgency_indicators": [],
        }

        for segment in segments:
            text = segment.text.lower()

            for timeline_type, patterns in timeline_patterns.items():
                for pattern in patterns:
                    if pattern in text:
                        timeline_analysis["timeline_mentions"].append(
                            {
                                "type": timeline_type,
                                "pattern": pattern,
                                "context": segment.text,
                                "speaker": segment.speaker_name,
                            }
                        )

        # Calculate urgency level based on mentions
        urgency_weights = {
            "urgent": 1.0,
            "short_term": 0.8,
            "medium_term": 0.5,
            "long_term": 0.2,
        }
        total_urgency = sum(
            urgency_weights.get(mention["type"], 0.5)
            for mention in timeline_analysis["timeline_mentions"]
        )

        if timeline_analysis["timeline_mentions"]:
            timeline_analysis["urgency_level"] = total_urgency / len(
                timeline_analysis["timeline_mentions"]
            )

        return timeline_analysis

    def _calculate_win_probability(
        self, segments: list[TranscriptSegment], context: AgentContext
    ) -> float:
        """Calculate overall win probability (0 to 1)"""
        factors = {
            "engagement": self._assess_engagement_quality(segments) * 0.3,
            "buying_signals": len(self._detect_buying_signals(segments)) * 0.05,
            "red_flags": -len(self._identify_red_flags(segments)) * 0.1,
            "sentiment": 0.5,  # Would integrate with sentiment agent
            "timeline": self._analyze_timeline_indicators(segments)["urgency_level"]
            * 0.2,
        }

        total_score = sum(factors.values()) + 0.5  # Base probability
        return max(0.1, min(0.95, total_score))


class CoachingAgent(BaseSalesAgent):
    """Real-time sales technique feedback and guidance"""

    def __init__(self, agent_id: str = "coaching", config: dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.coaching_framework = self._load_coaching_framework()
        self.performance_history: dict[str, list] = {}

    def get_agent_type(self) -> str:
        return "coaching"

    def _load_coaching_framework(self) -> dict[str, dict]:
        """Load sales coaching framework and best practices"""
        return {
            "questioning_techniques": {
                "open_questions": ["what", "how", "why", "when", "where", "which"],
                "discovery_questions": [
                    "tell me about",
                    "help me understand",
                    "walk me through",
                ],
                "pain_questions": ["what challenges", "biggest problem", "frustration"],
                "impact_questions": ["what happens if", "cost of", "impact on"],
            },
            "active_listening": {
                "acknowledgments": ["I understand", "that makes sense", "I see"],
                "clarifications": [
                    "let me make sure",
                    "so what I'm hearing",
                    "confirm",
                ],
                "summaries": ["so to summarize", "what I understand", "key points"],
            },
            "objection_handling": {
                "acknowledge": ["I understand your concern", "that's a fair point"],
                "clarify": ["help me understand", "when you say", "specifically"],
                "respond": ["what if", "consider this", "many clients"],
            },
            "closing_techniques": {
                "trial_close": [
                    "how does that sound",
                    "what do you think",
                    "make sense",
                ],
                "assumption": ["when we", "after we", "once you"],
                "direct": ["are you ready", "shall we", "let's move forward"],
            },
        }

    async def process(self, context: AgentContext) -> AgentOutput:
        """Provide real-time sales coaching feedback"""
        call_data = context.call_data
        recent_transcripts = self._get_recent_transcripts(call_data.transcripts)

        analysis = {
            "questioning_analysis": self._analyze_questioning_techniques(
                recent_transcripts
            ),
            "listening_score": self._assess_active_listening(recent_transcripts),
            "talk_time_balance": self._analyze_talk_time(recent_transcripts),
            "objection_handling": self._evaluate_objection_handling(recent_transcripts),
            "closing_opportunities": self._identify_closing_opportunities(
                recent_transcripts
            ),
            "coaching_recommendations": self._generate_coaching_recommendations(
                recent_transcripts
            ),
            "performance_score": self._calculate_performance_score(recent_transcripts),
        }

        # High priority for coaching opportunities or performance issues
        priority = AgentPriority.MEDIUM
        if (
            analysis["performance_score"] < 0.6
            or len(analysis["coaching_recommendations"]) > 2
        ):
            priority = AgentPriority.HIGH

        return AgentOutput(
            agent_id=self.agent_id,
            agent_type=self.get_agent_type(),
            call_id=call_data.metadata.call_id,
            timestamp=datetime.now(),
            priority=priority,
            confidence=ConfidenceLevel.HIGH,
            data=analysis,
            requires_action=len(analysis["coaching_recommendations"]) > 0,
        )

    def _get_recent_transcripts(
        self, transcripts: list[TranscriptSegment], seconds: int = 180
    ) -> list[TranscriptSegment]:
        """Get recent transcript segments for coaching analysis"""
        cutoff = time.time() - seconds
        return [seg for seg in transcripts if seg.start_time > cutoff]

    def _analyze_questioning_techniques(
        self, segments: list[TranscriptSegment]
    ) -> dict[str, Any]:
        """Analyze the quality and types of questions asked"""
        analysis = {
            "total_questions": 0,
            "open_questions": 0,
            "closed_questions": 0,
            "discovery_questions": 0,
            "question_quality": 0.0,
            "question_examples": [],
        }

        for segment in segments:
            if self._is_internal_speaker(segment.speaker_name) and "?" in segment.text:
                analysis["total_questions"] += 1
                text = segment.text.lower()

                # Classify question types
                if any(
                    word in text
                    for word in self.coaching_framework["questioning_techniques"][
                        "open_questions"
                    ]
                ):
                    analysis["open_questions"] += 1
                else:
                    analysis["closed_questions"] += 1

                if any(
                    phrase in text
                    for phrase in self.coaching_framework["questioning_techniques"][
                        "discovery_questions"
                    ]
                ):
                    analysis["discovery_questions"] += 1

                analysis["question_examples"].append(
                    {
                        "question": segment.text,
                        "timestamp": segment.start_time,
                        "type": self._classify_question_type(text),
                    }
                )

        # Calculate question quality score
        if analysis["total_questions"] > 0:
            open_ratio = analysis["open_questions"] / analysis["total_questions"]
            discovery_ratio = (
                analysis["discovery_questions"] / analysis["total_questions"]
            )
            analysis["question_quality"] = (open_ratio * 0.6) + (discovery_ratio * 0.4)

        return analysis

    def _classify_question_type(self, text: str) -> str:
        """Classify the type of question"""
        framework = self.coaching_framework["questioning_techniques"]

        if any(phrase in text for phrase in framework["pain_questions"]):
            return "pain_question"
        elif any(phrase in text for phrase in framework["impact_questions"]):
            return "impact_question"
        elif any(phrase in text for phrase in framework["discovery_questions"]):
            return "discovery_question"
        elif any(word in text for word in framework["open_questions"]):
            return "open_question"
        else:
            return "closed_question"

    def _assess_active_listening(self, segments: list[TranscriptSegment]) -> float:
        """Assess active listening techniques (0 to 1)"""
        listening_score = 0.0
        internal_segments = [
            seg for seg in segments if self._is_internal_speaker(seg.speaker_name)
        ]

        if not internal_segments:
            return 0.5

        for segment in internal_segments:
            text = segment.text.lower()

            # Check for acknowledgments
            if any(
                ack in text
                for ack in self.coaching_framework["active_listening"][
                    "acknowledgments"
                ]
            ):
                listening_score += 0.2

            # Check for clarifications
            if any(
                clar in text
                for clar in self.coaching_framework["active_listening"][
                    "clarifications"
                ]
            ):
                listening_score += 0.3

            # Check for summaries
            if any(
                summ in text
                for summ in self.coaching_framework["active_listening"]["summaries"]
            ):
                listening_score += 0.4

        return min(1.0, listening_score / len(internal_segments))

    def _analyze_talk_time(self, segments: list[TranscriptSegment]) -> dict[str, float]:
        """Analyze talk time balance between internal and external speakers"""
        internal_time = 0.0
        external_time = 0.0

        for segment in segments:
            duration = segment.end_time - segment.start_time

            if self._is_internal_speaker(segment.speaker_name):
                internal_time += duration
            else:
                external_time += duration

        total_time = internal_time + external_time

        if total_time == 0:
            return {"internal_ratio": 0.5, "external_ratio": 0.5, "balance_score": 0.5}

        internal_ratio = internal_time / total_time
        external_ratio = external_time / total_time

        # Optimal ratio is around 30-40% internal, 60-70% external
        optimal_internal = 0.35
        balance_score = 1.0 - abs(internal_ratio - optimal_internal) / optimal_internal

        return {
            "internal_ratio": internal_ratio,
            "external_ratio": external_ratio,
            "balance_score": max(0.0, balance_score),
        }

    def _evaluate_objection_handling(
        self, segments: list[TranscriptSegment]
    ) -> dict[str, Any]:
        """Evaluate objection handling techniques"""
        objection_indicators = [
            "but",
            "however",
            "concerned",
            "worried",
            "expensive",
            "difficult",
        ]
        objection_analysis = {
            "objections_detected": [],
            "handling_quality": 0.0,
            "techniques_used": [],
        }

        for i, segment in enumerate(segments):
            if not self._is_internal_speaker(segment.speaker_name):
                text = segment.text.lower()

                # Detect potential objections
                if any(indicator in text for indicator in objection_indicators):
                    objection = {
                        "objection": segment.text,
                        "timestamp": segment.start_time,
                        "response_quality": 0.0,
                        "response": None,
                    }

                    # Look for response in next few segments
                    for j in range(i + 1, min(i + 3, len(segments))):
                        if self._is_internal_speaker(segments[j].speaker_name):
                            response_text = segments[j].text.lower()
                            objection["response"] = segments[j].text

                            # Evaluate response using objection handling framework
                            framework = self.coaching_framework["objection_handling"]
                            response_score = 0.0

                            if any(
                                ack in response_text for ack in framework["acknowledge"]
                            ):
                                response_score += 0.3
                            if any(
                                clar in response_text for clar in framework["clarify"]
                            ):
                                response_score += 0.4
                            if any(
                                resp in response_text for resp in framework["respond"]
                            ):
                                response_score += 0.3

                            objection["response_quality"] = response_score
                            break

                    objection_analysis["objections_detected"].append(objection)

        # Calculate overall handling quality
        if objection_analysis["objections_detected"]:
            total_quality = sum(
                obj["response_quality"]
                for obj in objection_analysis["objections_detected"]
            )
            objection_analysis["handling_quality"] = total_quality / len(
                objection_analysis["objections_detected"]
            )

        return objection_analysis

    def _identify_closing_opportunities(
        self, segments: list[TranscriptSegment]
    ) -> list[dict]:
        """Identify missed or potential closing opportunities"""
        buying_signals = ["interested", "sounds good", "how much", "when", "next steps"]
        closing_opportunities = []

        for i, segment in enumerate(segments):
            if not self._is_internal_speaker(segment.speaker_name):
                text = segment.text.lower()

                # Check for buying signals
                if any(signal in text for signal in buying_signals):
                    # Check if followed up with closing attempt
                    closing_attempted = False

                    for j in range(i + 1, min(i + 3, len(segments))):
                        if self._is_internal_speaker(segments[j].speaker_name):
                            response = segments[j].text.lower()
                            framework = self.coaching_framework["closing_techniques"]

                            if (
                                any(
                                    trial in response
                                    for trial in framework["trial_close"]
                                )
                                or any(
                                    assume in response
                                    for assume in framework["assumption"]
                                )
                                or any(
                                    direct in response for direct in framework["direct"]
                                )
                            ):
                                closing_attempted = True
                                break

                    closing_opportunities.append(
                        {
                            "signal": segment.text,
                            "timestamp": segment.start_time,
                            "closing_attempted": closing_attempted,
                            "opportunity_strength": self._assess_opportunity_strength(
                                text
                            ),
                        }
                    )

        return closing_opportunities

    def _assess_opportunity_strength(self, text: str) -> float:
        """Assess the strength of a closing opportunity"""
        strong_signals = ["ready", "definitely", "yes", "absolutely"]
        medium_signals = ["probably", "likely", "interested"]
        weak_signals = ["maybe", "possibly", "thinking"]

        if any(signal in text for signal in strong_signals):
            return 1.0
        elif any(signal in text for signal in medium_signals):
            return 0.7
        elif any(signal in text for signal in weak_signals):
            return 0.3
        else:
            return 0.5

    def _generate_coaching_recommendations(
        self, segments: list[TranscriptSegment]
    ) -> list[dict]:
        """Generate specific coaching recommendations"""
        recommendations = []

        # Analyze recent performance
        talk_time = self._analyze_talk_time(segments)
        questioning = self._analyze_questioning_techniques(segments)
        listening = self._assess_active_listening(segments)

        # Talk time recommendations
        if talk_time["internal_ratio"] > 0.6:
            recommendations.append(
                {
                    "type": "talk_time",
                    "priority": "high",
                    "message": "You're talking too much. Try to ask more questions and listen more.",
                    "specific_action": "Aim for 70/30 prospect/sales rep talk time ratio",
                }
            )

        # Questioning recommendations
        if questioning["question_quality"] < 0.5:
            recommendations.append(
                {
                    "type": "questioning",
                    "priority": "medium",
                    "message": "Focus on asking more open-ended discovery questions.",
                    "specific_action": "Use 'What', 'How', and 'Why' questions to uncover needs",
                }
            )

        # Active listening recommendations
        if listening < 0.4:
            recommendations.append(
                {
                    "type": "listening",
                    "priority": "high",
                    "message": "Improve active listening with acknowledgments and clarifications.",
                    "specific_action": "Use phrases like 'I understand' and 'Help me clarify'",
                }
            )

        return recommendations

    def _calculate_performance_score(self, segments: list[TranscriptSegment]) -> float:
        """Calculate overall performance score (0 to 1)"""
        talk_time_score = self._analyze_talk_time(segments)["balance_score"]
        questioning_score = self._analyze_questioning_techniques(segments)[
            "question_quality"
        ]
        listening_score = self._assess_active_listening(segments)

        # Weighted average
        performance_score = (
            talk_time_score * 0.3 + questioning_score * 0.4 + listening_score * 0.3
        )

        return performance_score

    def _is_internal_speaker(self, speaker_name: str) -> bool:
        """Determine if speaker is internal team member"""
        # Simple heuristic - in real implementation, use participant data
        internal_indicators = ["sales", "account", "manager", "@company.com"]
        return any(
            indicator in speaker_name.lower() for indicator in internal_indicators
        )


class SummaryAgent(BaseSalesAgent):
    """Call outcome synthesis and action item generation"""

    def __init__(self, agent_id: str = "summary", config: dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.summary_templates = self._load_summary_templates()

    def get_agent_type(self) -> str:
        return "summary"

    def _load_summary_templates(self) -> dict[str, str]:
        """Load summary templates for different call types"""
        return {
            "discovery": "Discovery call focused on understanding {prospect} needs in {area}",
            "demo": "Product demonstration highlighting {features} for {prospect}",
            "closing": "Closing call addressing final concerns and next steps",
            "follow_up": "Follow-up call to continue discussion from {previous_date}",
        }

    async def process(self, context: AgentContext) -> AgentOutput:
        """Generate comprehensive call summary and action items"""
        call_data = context.call_data

        # Only process if call is ending or ended
        if call_data.is_active and len(call_data.transcripts) < 10:
            return AgentOutput(
                agent_id=self.agent_id,
                agent_type=self.get_agent_type(),
                call_id=call_data.metadata.call_id,
                timestamp=datetime.now(),
                priority=AgentPriority.LOW,
                confidence=ConfidenceLevel.LOW,
                data={
                    "status": "call_in_progress",
                    "summary": "Call still in progress",
                },
            )

        analysis = {
            "call_summary": self._generate_call_summary(call_data),
            "key_topics": self._extract_key_topics(call_data.transcripts),
            "action_items": self._generate_action_items(call_data.transcripts),
            "next_steps": self._identify_next_steps(call_data.transcripts),
            "call_outcome": self._determine_call_outcome(call_data.transcripts),
            "follow_up_recommendations": self._generate_follow_up_recommendations(
                call_data
            ),
        }

        return AgentOutput(
            agent_id=self.agent_id,
            agent_type=self.get_agent_type(),
            call_id=call_data.metadata.call_id,
            timestamp=datetime.now(),
            priority=AgentPriority.MEDIUM,
            confidence=ConfidenceLevel.HIGH,
            data=analysis,
            requires_action=True,  # Always requires follow-up actions
        )

    def _generate_call_summary(self, call_data: RealtimeCallData) -> str:
        """Generate a comprehensive call summary"""
        metadata = call_data.metadata
        transcripts = call_data.transcripts

        # Basic call information
        duration = metadata.duration_seconds or 0
        participant_count = len(metadata.participants)

        # Identify key themes
        themes = self._identify_themes(transcripts)

        summary = f"Call with {participant_count} participants lasting {duration//60} minutes. "

        if themes:
            summary += f"Discussion focused on {', '.join(themes[:3])}. "

        # Add outcome
        outcome = self._determine_call_outcome(transcripts)
        summary += f"Call outcome: {outcome}."

        return summary

    def _identify_themes(self, transcripts: list[TranscriptSegment]) -> list[str]:
        """Identify key themes discussed in the call"""
        # Simple keyword-based theme identification
        theme_keywords = {
            "pricing": ["price", "cost", "budget", "expensive", "affordable"],
            "features": ["feature", "functionality", "capability", "can it"],
            "implementation": ["implement", "setup", "install", "deploy", "rollout"],
            "integration": ["integrate", "connect", "api", "sync", "import"],
            "timeline": ["when", "timeline", "schedule", "deadline", "launch"],
            "competition": ["competitor", "alternative", "versus", "compared"],
        }

        themes = []
        text_content = " ".join(seg.text.lower() for seg in transcripts)

        for theme, keywords in theme_keywords.items():
            if any(keyword in text_content for keyword in keywords):
                themes.append(theme)

        return themes

    def _extract_key_topics(self, transcripts: list[TranscriptSegment]) -> list[dict]:
        """Extract key topics and discussion points"""
        topics = []
        current_topic = None
        topic_segments = []

        # Simple topic detection based on speaker changes and content
        for segment in transcripts:
            # New topic detection (simplified)
            if self._is_topic_change(segment, current_topic):
                if current_topic and topic_segments:
                    topics.append(
                        {
                            "topic": current_topic,
                            "duration": len(topic_segments),
                            "key_points": [seg.text for seg in topic_segments[:3]],
                        }
                    )

                current_topic = self._infer_topic(segment)
                topic_segments = [segment]
            else:
                topic_segments.append(segment)

        # Add final topic
        if current_topic and topic_segments:
            topics.append(
                {
                    "topic": current_topic,
                    "duration": len(topic_segments),
                    "key_points": [seg.text for seg in topic_segments[:3]],
                }
            )

        return topics

    def _is_topic_change(self, segment: TranscriptSegment, current_topic: str) -> bool:
        """Detect if this segment represents a topic change"""
        topic_change_indicators = [
            "let's talk about",
            "moving on to",
            "next question",
            "regarding",
            "about the",
        ]

        return any(
            indicator in segment.text.lower() for indicator in topic_change_indicators
        )

    def _infer_topic(self, segment: TranscriptSegment) -> str:
        """Infer topic from segment content"""
        text = segment.text.lower()

        if any(word in text for word in ["price", "cost", "budget"]):
            return "Pricing Discussion"
        elif any(word in text for word in ["feature", "functionality"]):
            return "Feature Overview"
        elif any(word in text for word in ["implement", "setup"]):
            return "Implementation Planning"
        elif any(word in text for word in ["integrate", "api"]):
            return "Integration Requirements"
        else:
            return "General Discussion"

    def _generate_action_items(
        self, transcripts: list[TranscriptSegment]
    ) -> list[dict]:
        """Generate action items from call discussion"""
        action_patterns = [
            r"i will (.*?)(?:\.|$)",
            r"i'll (.*?)(?:\.|$)",
            r"let me (.*?)(?:\.|$)",
            r"i can (.*?)(?:\.|$)",
            r"follow up (.*?)(?:\.|$)",
            r"send (.*?)(?:\.|$)",
        ]

        action_items = []

        for segment in transcripts:
            text = segment.text.lower()

            for pattern in action_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    action_items.append(
                        {
                            "action": match.group(1).strip(),
                            "owner": segment.speaker_name,
                            "source": segment.text,
                            "priority": self._determine_action_priority(match.group(1)),
                            "due_date": self._infer_due_date(text),
                        }
                    )

        return action_items

    def _determine_action_priority(self, action: str) -> str:
        """Determine priority level for an action item"""
        high_priority_keywords = ["urgent", "asap", "immediately", "today", "important"]
        medium_priority_keywords = ["soon", "this week", "by friday"]

        action_lower = action.lower()

        if any(keyword in action_lower for keyword in high_priority_keywords):
            return "high"
        elif any(keyword in action_lower for keyword in medium_priority_keywords):
            return "medium"
        else:
            return "low"

    def _infer_due_date(self, text: str) -> Optional[str]:
        """Infer due date from text context"""
        date_patterns = {
            "today": datetime.now().strftime("%Y-%m-%d"),
            "tomorrow": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "this week": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "next week": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        }

        for pattern, date in date_patterns.items():
            if pattern in text.lower():
                return date

        return None

    def _identify_next_steps(self, transcripts: list[TranscriptSegment]) -> list[str]:
        """Identify explicitly mentioned next steps"""
        next_step_indicators = [
            "next step",
            "moving forward",
            "what we need to do",
            "follow up with",
            "schedule a",
        ]

        next_steps = []

        for segment in transcripts:
            text = segment.text.lower()

            for indicator in next_step_indicators:
                if indicator in text:
                    # Extract the context around the indicator
                    sentences = segment.text.split(".")
                    for sentence in sentences:
                        if indicator in sentence.lower():
                            next_steps.append(sentence.strip())

        return next_steps[:5]  # Limit to top 5 next steps

    def _determine_call_outcome(self, transcripts: list[TranscriptSegment]) -> str:
        """Determine the overall outcome of the call"""
        positive_outcomes = [
            "interested",
            "move forward",
            "next steps",
            "schedule",
            "contract",
        ]
        negative_outcomes = ["not interested", "not ready", "concerns", "issues"]
        neutral_outcomes = ["think about", "discuss", "consider", "review"]

        text_content = " ".join(
            seg.text.lower() for seg in transcripts[-10:]
        )  # Last 10 segments

        positive_score = sum(
            1 for outcome in positive_outcomes if outcome in text_content
        )
        negative_score = sum(
            1 for outcome in negative_outcomes if outcome in text_content
        )
        neutral_score = sum(
            1 for outcome in neutral_outcomes if outcome in text_content
        )

        if positive_score > negative_score and positive_score > neutral_score:
            return "Positive - Prospect interested in moving forward"
        elif negative_score > positive_score:
            return "Negative - Prospect not ready or interested"
        elif neutral_score > 0:
            return "Neutral - Prospect needs time to consider"
        else:
            return "Unclear - Follow-up needed for clarity"

    def _generate_follow_up_recommendations(
        self, call_data: RealtimeCallData
    ) -> list[dict]:
        """Generate specific follow-up recommendations"""
        recommendations = []
        transcripts = call_data.transcripts

        # Check for promised follow-ups
        if any("follow up" in seg.text.lower() for seg in transcripts):
            recommendations.append(
                {
                    "type": "promised_follow_up",
                    "action": "Complete promised follow-up actions",
                    "timeline": "within 24 hours",
                }
            )

        # Check for information requests
        if any("send" in seg.text.lower() for seg in transcripts):
            recommendations.append(
                {
                    "type": "information_sharing",
                    "action": "Send requested materials and information",
                    "timeline": "within 2 business days",
                }
            )

        # Check for scheduling needs
        if any(
            "schedule" in seg.text.lower() or "meeting" in seg.text.lower()
            for seg in transcripts
        ):
            recommendations.append(
                {
                    "type": "scheduling",
                    "action": "Schedule follow-up meeting",
                    "timeline": "within 1 week",
                }
            )

        return recommendations


# Agent Orchestrator for coordinating all sales intelligence agents
class SalesAgentOrchestrator:
    """Orchestrates all sales intelligence agents"""

    def __init__(self):
        self.agents: dict[str, BaseSalesAgent] = {}
        self.output_buffer: list[AgentOutput] = []
        self.is_running = False

    def register_agent(self, agent: BaseSalesAgent):
        """Register a new agent"""
        self.agents[agent.agent_id] = agent
        agent.register_output_callback(self._handle_agent_output)

    async def _handle_agent_output(self, output: AgentOutput):
        """Handle output from any agent"""
        self.output_buffer.append(output)

        # Process high-priority outputs immediately
        if output.priority == AgentPriority.CRITICAL:
            await self._process_critical_output(output)

    async def _process_critical_output(self, output: AgentOutput):
        """Process critical outputs immediately"""
        logger.warning(f"Critical output from {output.agent_type}: {output.data}")
        # In real implementation, send immediate notifications

    async def start_all_agents(self):
        """Start all registered agents"""
        self.is_running = True
        tasks = []

        for agent in self.agents.values():
            tasks.append(asyncio.create_task(agent.start()))

        await asyncio.gather(*tasks)

    async def stop_all_agents(self):
        """Stop all agents"""
        self.is_running = False
        for agent in self.agents.values():
            await agent.stop()

    async def process_call_data(
        self, call_data: RealtimeCallData, context: dict[str, Any] = None
    ):
        """Process call data through all agents"""
        agent_context = AgentContext(
            call_data=call_data,
            historical_data=context.get("historical_data", {}) if context else {},
            user_preferences=context.get("user_preferences", {}) if context else {},
            team_settings=context.get("team_settings", {}) if context else {},
        )

        # Enqueue context to all agents
        for agent in self.agents.values():
            await agent.enqueue_context(agent_context)

    def get_recent_outputs(
        self, agent_type: str = None, priority: AgentPriority = None
    ) -> list[AgentOutput]:
        """Get recent agent outputs with optional filtering"""
        outputs = self.output_buffer

        if agent_type:
            outputs = [o for o in outputs if o.agent_type == agent_type]

        if priority:
            outputs = [o for o in outputs if o.priority == priority]

        return sorted(outputs, key=lambda x: x.timestamp, reverse=True)


# Factory function to create a complete sales intelligence swarm
def create_sales_intelligence_swarm() -> SalesAgentOrchestrator:
    """Create a complete sales intelligence swarm with all agents"""
    orchestrator = SalesAgentOrchestrator()

    # Create and register all agents
    agents = [
        TranscriptionAgent(),
        SentimentAgent(),
        CompetitiveAgent(),
        RiskAssessmentAgent(),
        CoachingAgent(),
        SummaryAgent(),
    ]

    for agent in agents:
        orchestrator.register_agent(agent)

    return orchestrator


# Example usage
async def example_sales_intelligence_usage():
    """Example of how to use the sales intelligence swarm"""

    # Create the swarm
    swarm = create_sales_intelligence_swarm()

    # Start all agents
    await swarm.start_all_agents()

    # Simulate call data processing
    from .gong_realtime import CallMetadata, RealtimeCallData, TranscriptSegment

    # Create sample call data
    call_data = RealtimeCallData(
        metadata=CallMetadata(
            call_id="sample-call-123",
            call_url="https://gong.io/call/123",
            title="Discovery Call - Acme Corp",
            scheduled_start=datetime.now(),
            actual_start=datetime.now(),
            duration_seconds=1800,
            participants=[],
            meeting_platform="zoom",
            recording_status="recording",
            tags=["discovery", "enterprise"],
        ),
        transcripts=[
            TranscriptSegment(
                speaker_id="rep_1",
                speaker_name="John Sales",
                text="Thanks for taking the time to meet with us today. Can you tell me about your current challenges with customer data?",
                start_time=time.time(),
                end_time=time.time() + 5,
                confidence=0.95,
            ),
            TranscriptSegment(
                speaker_id="prospect_1",
                speaker_name="Jane Smith",
                text="Well, we're really struggling with our current CRM. It's expensive and doesn't integrate well with our other tools.",
                start_time=time.time() + 5,
                end_time=time.time() + 10,
                confidence=0.92,
            ),
        ],
        last_update=datetime.now(),
        is_active=True,
    )

    # Process the call data
    await swarm.process_call_data(call_data)

    # Get outputs from different agents
    sentiment_outputs = swarm.get_recent_outputs(agent_type="sentiment")
    risk_outputs = swarm.get_recent_outputs(agent_type="risk_assessment")
    coaching_outputs = swarm.get_recent_outputs(agent_type="coaching")

    print(f"Generated {len(sentiment_outputs)} sentiment insights")
    print(f"Generated {len(risk_outputs)} risk assessments")
    print(f"Generated {len(coaching_outputs)} coaching recommendations")

    # Stop the swarm
    await swarm.stop_all_agents()


if __name__ == "__main__":
    asyncio.run(example_sales_intelligence_usage())
