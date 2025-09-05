"""
Progressive Personality Analysis Agents

Four-phase personality analysis system:
- Phase A: Basic behavioral indicators from LinkedIn and email patterns
- Phase B: Comprehensive DISC profiling with psychological insights
- Phase C: Advanced predictive modeling with decision patterns
- Phase D: Full psychological assessment with relationship mapping
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    BehaviorPattern,
    CommunicationStyle,
    DecisionMakingStyle,
    PersonalityProfile,
    PersonalityType,
    ResearchSource,
)

logger = logging.getLogger(__name__)


class BasePersonalityAnalyzer(ABC):
    """Base class for all personality analysis agents"""

    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.confidence_threshold = config.get("confidence_threshold", 0.6) if config else 0.6

    @abstractmethod
    async def analyze_personality(
        self, prospect_id: str, data_sources: Dict[str, Any]
    ) -> PersonalityProfile:
        """Analyze personality from available data sources"""
        pass

    def _extract_text_patterns(self, text: str) -> Dict[str, Any]:
        """Extract linguistic and stylistic patterns from text"""
        patterns = {
            "word_count": len(text.split()),
            "sentence_count": len(re.findall(r"[.!?]+", text)),
            "avg_sentence_length": 0.0,
            "exclamation_usage": text.count("!"),
            "question_usage": text.count("?"),
            "caps_usage": sum(1 for c in text if c.isupper()),
            "formal_language": 0,
            "casual_language": 0,
            "technical_terms": 0,
            "emotional_words": 0,
            "action_words": 0,
        }

        # Calculate average sentence length
        if patterns["sentence_count"] > 0:
            patterns["avg_sentence_length"] = patterns["word_count"] / patterns["sentence_count"]

        # Analyze language style
        formal_indicators = [
            "therefore",
            "furthermore",
            "consequently",
            "accordingly",
            "regarding",
            "pursuant",
            "moreover",
            "nevertheless",
        ]
        casual_indicators = [
            "awesome",
            "cool",
            "great",
            "love",
            "hate",
            "super",
            "totally",
            "really",
            "pretty",
            "kinda",
        ]
        technical_indicators = [
            "implementation",
            "optimization",
            "integration",
            "scalability",
            "architecture",
            "framework",
            "methodology",
            "analytics",
        ]
        emotional_indicators = [
            "excited",
            "thrilled",
            "passionate",
            "frustrated",
            "concerned",
            "delighted",
            "disappointed",
            "enthusiastic",
            "worried",
        ]
        action_indicators = [
            "achieve",
            "accomplish",
            "execute",
            "deliver",
            "implement",
            "drive",
            "accelerate",
            "optimize",
            "transform",
            "innovate",
        ]

        text_lower = text.lower()

        patterns["formal_language"] = sum(1 for word in formal_indicators if word in text_lower)
        patterns["casual_language"] = sum(1 for word in casual_indicators if word in text_lower)
        patterns["technical_terms"] = sum(1 for word in technical_indicators if word in text_lower)
        patterns["emotional_words"] = sum(1 for word in emotional_indicators if word in text_lower)
        patterns["action_words"] = sum(1 for word in action_indicators if word in text_lower)

        return patterns


class BasicPersonalityAgent(BasePersonalityAnalyzer):
    """
    Phase A: Basic Behavioral Indicators

    Analyzes LinkedIn activity and email patterns to identify basic
    personality and communication style indicators.
    """

    def __init__(self, agent_id: str = "basic_personality", config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.analysis_version = "basic_v1.0"

    async def analyze_personality(
        self, prospect_id: str, data_sources: Dict[str, Any]
    ) -> PersonalityProfile:
        """Analyze basic personality indicators from available data"""
        profile = PersonalityProfile(
            prospect_id=prospect_id, analysis_version=self.analysis_version
        )

        # Analyze LinkedIn activity
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            await self._analyze_linkedin_activity(profile, linkedin_data)
            profile.data_sources.append(ResearchSource.LINKEDIN)
            profile.linkedin_data_points = len(linkedin_data.get("posts", [])) + len(
                linkedin_data.get("comments", [])
            )

        # Analyze email patterns
        email_data = data_sources.get("email", {})
        if email_data:
            await self._analyze_email_patterns(profile, email_data)
            profile.data_sources.append(ResearchSource.EMAIL_INTERACTIONS)
            profile.email_data_points = len(email_data.get("messages", []))

        # Analyze web behavior
        web_data = data_sources.get("web_behavior", {})
        if web_data:
            await self._analyze_web_behavior(profile, web_data)
            profile.data_sources.append(ResearchSource.WEB_BEHAVIOR)
            profile.web_behavior_data_points = len(web_data.get("sessions", []))

        # Generate basic DISC indicators
        await self._generate_basic_disc_scores(profile)

        # Update confidence scores
        profile.update_profile_confidence()

        logger.info(f"Basic personality analysis completed for {prospect_id}")
        return profile

    async def _analyze_linkedin_activity(
        self, profile: PersonalityProfile, linkedin_data: Dict[str, Any]
    ):
        """Analyze LinkedIn activity patterns"""
        posts = linkedin_data.get("posts", [])
        comments = linkedin_data.get("comments", [])
        connections = linkedin_data.get("connections", [])

        # Analyze posting frequency and style
        if posts:
            posting_patterns = await self._analyze_posting_patterns(posts)
            profile.activity_patterns["linkedin_posting"] = posting_patterns

            # Extract communication style from posts
            all_post_text = " ".join([post.get("content", "") for post in posts])
            text_patterns = self._extract_text_patterns(all_post_text)

            # Map text patterns to communication style
            if text_patterns["action_words"] > text_patterns["word_count"] * 0.05:
                profile.communication_style = CommunicationStyle.RESULTS_FOCUSED
            elif text_patterns["emotional_words"] > text_patterns["word_count"] * 0.03:
                profile.communication_style = CommunicationStyle.RELATIONSHIP_FOCUSED
            elif text_patterns["technical_terms"] > text_patterns["word_count"] * 0.04:
                profile.communication_style = CommunicationStyle.ANALYTICAL
            elif text_patterns["formal_language"] > text_patterns["casual_language"]:
                profile.communication_style = CommunicationStyle.DIRECT
            else:
                profile.communication_style = CommunicationStyle.COLLABORATIVE

        # Analyze engagement patterns
        if comments:
            engagement_patterns = await self._analyze_engagement_patterns(comments)
            profile.engagement_patterns["linkedin_engagement"] = engagement_patterns

        # Analyze network characteristics
        if connections:
            network_patterns = await self._analyze_network_patterns(connections)
            profile.activity_patterns["network_characteristics"] = network_patterns

    async def _analyze_posting_patterns(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze posting patterns and content themes"""
        patterns = {
            "posting_frequency": "low",
            "content_themes": [],
            "engagement_seeking": False,
            "thought_leadership": False,
            "personal_sharing": False,
        }

        if not posts:
            return patterns

        # Calculate posting frequency
        if len(posts) >= 20:
            patterns["posting_frequency"] = "high"
        elif len(posts) >= 10:
            patterns["posting_frequency"] = "medium"

        # Analyze content themes
        content_themes = {
            "industry_insights": 0,
            "company_updates": 0,
            "personal_achievements": 0,
            "thought_leadership": 0,
            "team_recognition": 0,
        }

        for post in posts:
            content = post.get("content", "").lower()

            # Categorize content
            if any(word in content for word in ["industry", "market", "trend", "insight"]):
                content_themes["industry_insights"] += 1
            if any(word in content for word in ["company", "team", "organization", "we"]):
                content_themes["company_updates"] += 1
            if any(word in content for word in ["achieved", "accomplished", "proud", "excited"]):
                content_themes["personal_achievements"] += 1
            if any(word in content for word in ["believe", "think", "perspective", "opinion"]):
                content_themes["thought_leadership"] += 1
            if any(
                word in content
                for word in ["congratulations", "thanks", "appreciate", "recognition"]
            ):
                content_themes["team_recognition"] += 1

        # Determine dominant themes
        patterns["content_themes"] = [
            theme for theme, count in content_themes.items() if count > len(posts) * 0.2
        ]

        # Assess engagement-seeking behavior
        patterns["engagement_seeking"] = any(
            post.get("likes", 0) > 10 or post.get("comments", 0) > 3 for post in posts
        )

        patterns["thought_leadership"] = content_themes["thought_leadership"] > len(posts) * 0.3
        patterns["personal_sharing"] = content_themes["personal_achievements"] > len(posts) * 0.2

        return patterns

    async def _analyze_engagement_patterns(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how prospect engages with others' content"""
        patterns = {
            "engagement_frequency": "low",
            "engagement_style": "supportive",
            "initiates_discussions": False,
            "asks_questions": False,
            "provides_value": False,
        }

        if not comments:
            return patterns

        # Calculate engagement frequency
        if len(comments) >= 50:
            patterns["engagement_frequency"] = "high"
        elif len(comments) >= 20:
            patterns["engagement_frequency"] = "medium"

        # Analyze engagement style
        question_count = 0
        value_providing_count = 0
        supportive_count = 0
        discussion_initiating_count = 0

        for comment in comments:
            content = comment.get("content", "")

            if "?" in content:
                question_count += 1

            if any(
                word in content.lower()
                for word in ["experience", "suggest", "recommend", "consider", "approach"]
            ):
                value_providing_count += 1

            if any(
                word in content.lower()
                for word in ["agree", "exactly", "great", "excellent", "congratulations"]
            ):
                supportive_count += 1

            if len(content) > 100:  # Longer comments suggest discussion initiation
                discussion_initiating_count += 1

        total_comments = len(comments)

        patterns["asks_questions"] = question_count > total_comments * 0.2
        patterns["provides_value"] = value_providing_count > total_comments * 0.3
        patterns["initiates_discussions"] = discussion_initiating_count > total_comments * 0.2

        # Determine dominant engagement style
        if value_providing_count > supportive_count:
            patterns["engagement_style"] = "value_focused"
        elif question_count > supportive_count:
            patterns["engagement_style"] = "inquisitive"
        elif discussion_initiating_count > supportive_count:
            patterns["engagement_style"] = "discussion_leader"
        else:
            patterns["engagement_style"] = "supportive"

        return patterns

    async def _analyze_network_patterns(self, connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze professional network characteristics"""
        patterns = {
            "network_size": len(connections),
            "industry_diversity": 0.0,
            "seniority_distribution": {},
            "company_diversity": 0.0,
            "networking_strategy": "quality",
        }

        if not connections:
            return patterns

        # Analyze industry distribution
        industries = {}
        for connection in connections:
            industry = connection.get("industry", "Other")
            industries[industry] = industries.get(industry, 0) + 1

        # Calculate diversity (0-1 scale)
        if len(industries) > 1:
            total = len(connections)
            patterns["industry_diversity"] = 1.0 - max(industries.values()) / total

        # Analyze seniority levels
        seniority_levels = {}
        for connection in connections:
            title = connection.get("title", "").lower()

            if any(word in title for word in ["ceo", "president", "founder", "owner"]):
                level = "c_level"
            elif any(word in title for word in ["vp", "vice president", "director"]):
                level = "executive"
            elif any(word in title for word in ["manager", "head", "lead"]):
                level = "manager"
            else:
                level = "individual_contributor"

            seniority_levels[level] = seniority_levels.get(level, 0) + 1

        patterns["seniority_distribution"] = seniority_levels

        # Determine networking strategy
        if len(connections) > 1000:
            patterns["networking_strategy"] = "broad"
        elif seniority_levels.get("c_level", 0) > len(connections) * 0.1:
            patterns["networking_strategy"] = "strategic"
        else:
            patterns["networking_strategy"] = "quality"

        return patterns

    async def _analyze_email_patterns(
        self, profile: PersonalityProfile, email_data: Dict[str, Any]
    ):
        """Analyze email communication patterns"""
        messages = email_data.get("messages", [])

        if not messages:
            return

        # Analyze response patterns
        response_patterns = await self._analyze_response_patterns(messages)
        profile.response_timing_patterns = response_patterns

        # Analyze communication style from email content
        all_email_text = " ".join([msg.get("content", "") for msg in messages])
        text_patterns = self._extract_text_patterns(all_email_text)

        # Create behavior pattern for email communication
        email_behavior = BehaviorPattern(
            pattern_type="communication",
            pattern_name="email_communication_style",
            description="Communication style observed in email interactions",
            frequency="ongoing",
            consistency_score=0.8,  # Mock score
            confidence_level=0.7,
            data_points=len(messages),
            source=ResearchSource.EMAIL_INTERACTIONS,
        )

        # Determine communication characteristics
        if text_patterns["avg_sentence_length"] > 20:
            email_behavior.add_evidence({"characteristic": "detailed_communicator"})
        if text_patterns["exclamation_usage"] > text_patterns["word_count"] * 0.01:
            email_behavior.add_evidence({"characteristic": "enthusiastic_tone"})
        if text_patterns["formal_language"] > text_patterns["casual_language"]:
            email_behavior.add_evidence({"characteristic": "formal_style"})

        profile.behavior_patterns.append(email_behavior)

    async def _analyze_response_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze email response timing and patterns"""
        patterns = {
            "avg_response_time_hours": 24.0,
            "response_consistency": 0.5,
            "preferred_times": [],
            "response_length_preference": "medium",
        }

        response_times = []
        response_lengths = []
        response_hours = []

        for i, message in enumerate(messages):
            if i > 0:  # Skip first message (no response time)
                prev_time = datetime.fromisoformat(messages[i - 1].get("timestamp", ""))
                curr_time = datetime.fromisoformat(message.get("timestamp", ""))
                response_time_hours = (curr_time - prev_time).total_seconds() / 3600

                if response_time_hours < 168:  # Within a week
                    response_times.append(response_time_hours)
                    response_hours.append(curr_time.hour)

            content_length = len(message.get("content", ""))
            response_lengths.append(content_length)

        # Calculate averages
        if response_times:
            patterns["avg_response_time_hours"] = sum(response_times) / len(response_times)

            # Determine consistency (lower standard deviation = higher consistency)
            import statistics

            if len(response_times) > 1:
                std_dev = statistics.stdev(response_times)
                patterns["response_consistency"] = max(
                    0, 1 - (std_dev / patterns["avg_response_time_hours"])
                )

        # Analyze preferred response times
        if response_hours:
            hour_counts = {}
            for hour in response_hours:
                hour_counts[hour] = hour_counts.get(hour, 0) + 1

            # Find peak hours
            sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
            patterns["preferred_times"] = [f"{hour}:00" for hour, _ in sorted_hours[:3]]

        # Analyze response length preference
        if response_lengths:
            avg_length = sum(response_lengths) / len(response_lengths)
            if avg_length > 500:
                patterns["response_length_preference"] = "long"
            elif avg_length > 200:
                patterns["response_length_preference"] = "medium"
            else:
                patterns["response_length_preference"] = "short"

        return patterns

    async def _analyze_web_behavior(self, profile: PersonalityProfile, web_data: Dict[str, Any]):
        """Analyze web behavior patterns"""
        sessions = web_data.get("sessions", [])

        if not sessions:
            return

        # Create behavior pattern for web activity
        web_behavior = BehaviorPattern(
            pattern_type="engagement",
            pattern_name="web_engagement_style",
            description="Engagement patterns from web behavior",
            frequency="variable",
            data_points=len(sessions),
            source=ResearchSource.WEB_BEHAVIOR,
        )

        # Analyze session characteristics
        total_time = sum(session.get("duration_seconds", 0) for session in sessions)
        avg_session_time = total_time / len(sessions) if sessions else 0

        # Analyze content preferences
        pages_visited = []
        for session in sessions:
            pages_visited.extend(session.get("pages", []))

        # Categorize page types
        content_interests = {"technical": 0, "business": 0, "educational": 0, "social": 0}

        for page in pages_visited:
            url = page.get("url", "").lower()
            if any(term in url for term in ["docs", "api", "technical", "developer"]):
                content_interests["technical"] += 1
            elif any(term in url for term in ["blog", "news", "article", "resource"]):
                content_interests["educational"] += 1
            elif any(term in url for term in ["pricing", "product", "solution", "business"]):
                content_interests["business"] += 1
            elif any(term in url for term in ["linkedin", "twitter", "facebook", "social"]):
                content_interests["social"] += 1

        # Determine engagement characteristics
        if avg_session_time > 300:  # 5+ minutes
            web_behavior.add_evidence({"characteristic": "deep_engagement"})
        if content_interests["technical"] > len(pages_visited) * 0.3:
            web_behavior.add_evidence({"characteristic": "technical_interest"})
        if content_interests["educational"] > len(pages_visited) * 0.4:
            web_behavior.add_evidence({"characteristic": "learning_oriented"})

        web_behavior.confidence_level = min(
            len(sessions) / 20, 1.0
        )  # More sessions = higher confidence
        profile.behavior_patterns.append(web_behavior)

    async def _generate_basic_disc_scores(self, profile: PersonalityProfile):
        """Generate basic DISC scores from observed patterns"""
        disc_scores = {"D": 0.0, "I": 0.0, "S": 0.0, "C": 0.0}

        # Score based on communication style
        comm_style_mapping = {
            CommunicationStyle.DIRECT: {"D": 0.7, "I": 0.2, "S": 0.1, "C": 0.3},
            CommunicationStyle.RESULTS_FOCUSED: {"D": 0.8, "I": 0.3, "S": 0.2, "C": 0.4},
            CommunicationStyle.RELATIONSHIP_FOCUSED: {"D": 0.2, "I": 0.8, "S": 0.7, "C": 0.1},
            CommunicationStyle.COLLABORATIVE: {"D": 0.3, "I": 0.7, "S": 0.6, "C": 0.3},
            CommunicationStyle.SUPPORTIVE: {"D": 0.1, "I": 0.4, "S": 0.8, "C": 0.3},
            CommunicationStyle.ANALYTICAL: {"D": 0.3, "I": 0.2, "S": 0.3, "C": 0.9},
        }

        if profile.communication_style in comm_style_mapping:
            for disc_type, score in comm_style_mapping[profile.communication_style].items():
                disc_scores[disc_type] += score * 0.4  # 40% weight from communication style

        # Score based on behavior patterns
        for pattern in profile.behavior_patterns:
            evidence = pattern.supporting_evidence

            for ev in evidence:
                characteristic = ev.get("characteristic", "")

                if characteristic == "detailed_communicator":
                    disc_scores["C"] += 0.2
                elif characteristic == "enthusiastic_tone":
                    disc_scores["I"] += 0.2
                elif characteristic == "formal_style":
                    disc_scores["C"] += 0.1
                    disc_scores["D"] += 0.1
                elif characteristic == "deep_engagement":
                    disc_scores["C"] += 0.1
                elif characteristic == "technical_interest":
                    disc_scores["C"] += 0.2
                elif characteristic == "learning_oriented":
                    disc_scores["C"] += 0.1
                    disc_scores["S"] += 0.1

        # Score based on activity patterns
        if "linkedin_posting" in profile.activity_patterns:
            posting = profile.activity_patterns["linkedin_posting"]

            if posting.get("thought_leadership"):
                disc_scores["I"] += 0.3
                disc_scores["D"] += 0.2
            if posting.get("posting_frequency") == "high":
                disc_scores["I"] += 0.2
            if posting.get("personal_sharing"):
                disc_scores["I"] += 0.2

        # Normalize scores to 0-1 range
        max_possible_score = 1.5  # Theoretical maximum from all sources
        for disc_type in disc_scores:
            disc_scores[disc_type] = min(disc_scores[disc_type] / max_possible_score, 1.0)

        profile.disc_scores = disc_scores

        # Determine primary and secondary types
        sorted_scores = sorted(disc_scores.items(), key=lambda x: x[1], reverse=True)

        if sorted_scores[0][1] > 0.4:  # Minimum threshold for primary type
            primary_mapping = {
                "D": PersonalityType.DOMINANT,
                "I": PersonalityType.INFLUENTIAL,
                "S": PersonalityType.STEADY,
                "C": PersonalityType.CONSCIENTIOUS,
            }
            profile.primary_disc_type = primary_mapping[sorted_scores[0][0]]

            if sorted_scores[1][1] > 0.3:  # Secondary type threshold
                profile.secondary_disc_type = primary_mapping[sorted_scores[1][0]]


class DISCProfileAnalyzer(BasePersonalityAnalyzer):
    """
    Phase B: Comprehensive DISC Profiling

    Advanced DISC analysis with psychological insights and behavioral predictions.
    """

    def __init__(self, agent_id: str = "disc_analyzer", config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.analysis_version = "disc_v2.0"

    async def analyze_personality(
        self,
        prospect_id: str,
        data_sources: Dict[str, Any],
        basic_profile: PersonalityProfile = None,
    ) -> PersonalityProfile:
        """Perform comprehensive DISC analysis"""
        # Start with basic profile if available, otherwise create new
        profile = basic_profile or PersonalityProfile(
            prospect_id=prospect_id, analysis_version=self.analysis_version
        )

        # Enhance with comprehensive DISC analysis
        await self._perform_comprehensive_disc_analysis(profile, data_sources)

        # Generate detailed behavioral predictions
        await self._generate_behavioral_predictions(profile)

        # Map communication preferences
        await self._map_communication_preferences(profile)

        # Identify decision-making patterns
        await self._analyze_decision_patterns(profile, data_sources)

        # Update confidence
        profile.update_profile_confidence()

        logger.info(f"Comprehensive DISC analysis completed for {prospect_id}")
        return profile

    async def _perform_comprehensive_disc_analysis(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Perform detailed DISC analysis with multiple data sources"""
        # Analyze leadership indicators for Dominance
        dominance_score = await self._analyze_dominance_indicators(data_sources)

        # Analyze social engagement for Influence
        influence_score = await self._analyze_influence_indicators(data_sources)

        # Analyze consistency patterns for Steadiness
        steadiness_score = await self._analyze_steadiness_indicators(data_sources)

        # Analyze detail orientation for Conscientiousness
        conscientiousness_score = await self._analyze_conscientiousness_indicators(data_sources)

        # Update DISC scores with enhanced analysis
        enhanced_scores = {
            "D": dominance_score,
            "I": influence_score,
            "S": steadiness_score,
            "C": conscientiousness_score,
        }

        # Blend with existing scores if available
        if profile.disc_scores:
            for disc_type, new_score in enhanced_scores.items():
                existing_score = profile.disc_scores.get(disc_type, 0.0)
                # Weighted average: 60% new analysis, 40% existing
                profile.disc_scores[disc_type] = (new_score * 0.6) + (existing_score * 0.4)
        else:
            profile.disc_scores = enhanced_scores

        # Update primary/secondary types
        self._update_disc_types(profile)

    async def _analyze_dominance_indicators(self, data_sources: Dict[str, Any]) -> float:
        """Analyze indicators of Dominance (D) traits"""
        dominance_score = 0.0
        indicators = []

        # LinkedIn indicators
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            posts = linkedin_data.get("posts", [])

            # Leadership language
            leadership_keywords = [
                "achieve",
                "drive",
                "results",
                "challenge",
                "overcome",
                "lead",
                "deliver",
                "execute",
                "win",
                "compete",
                "goal",
                "target",
            ]

            leadership_mentions = 0
            for post in posts:
                content = post.get("content", "").lower()
                leadership_mentions += sum(
                    1 for keyword in leadership_keywords if keyword in content
                )

            if posts and leadership_mentions > len(posts) * 0.3:
                dominance_score += 0.3
                indicators.append("frequent_leadership_language")

            # Direct communication style
            direct_indicators = ["need to", "must", "should", "will", "going to"]
            direct_count = 0
            for post in posts:
                content = post.get("content", "").lower()
                direct_count += sum(1 for indicator in direct_indicators if indicator in content)

            if posts and direct_count > len(posts) * 0.4:
                dominance_score += 0.2
                indicators.append("direct_communication")

            # Achievement focus
            achievement_keywords = [
                "accomplished",
                "achieved",
                "delivered",
                "exceeded",
                "successful",
            ]
            achievement_mentions = sum(
                1
                for post in posts
                for keyword in achievement_keywords
                if keyword in post.get("content", "").lower()
            )

            if achievement_mentions > 0:
                dominance_score += min(achievement_mentions * 0.1, 0.3)
                indicators.append("achievement_oriented")

        # Email indicators
        email_data = data_sources.get("email", {})
        if email_data:
            messages = email_data.get("messages", [])

            # Brief, direct messages
            avg_length = (
                sum(len(msg.get("content", "")) for msg in messages) / len(messages)
                if messages
                else 0
            )
            if avg_length < 150:  # Short messages indicate directness
                dominance_score += 0.2
                indicators.append("concise_communication")

            # Quick response times
            response_patterns = data_sources.get("response_timing", {})
            if response_patterns.get("avg_response_time_hours", 24) < 4:
                dominance_score += 0.2
                indicators.append("quick_responses")

        return min(dominance_score, 1.0)

    async def _analyze_influence_indicators(self, data_sources: Dict[str, Any]) -> float:
        """Analyze indicators of Influence (I) traits"""
        influence_score = 0.0

        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            posts = linkedin_data.get("posts", [])

            # Social engagement keywords
            social_keywords = [
                "excited",
                "thrilled",
                "amazing",
                "fantastic",
                "love",
                "team",
                "together",
                "collaborate",
                "share",
                "connect",
            ]

            social_mentions = sum(
                1
                for post in posts
                for keyword in social_keywords
                if keyword in post.get("content", "").lower()
            )

            if posts and social_mentions > len(posts) * 0.2:
                influence_score += 0.4

            # High engagement seeking
            avg_likes = sum(post.get("likes", 0) for post in posts) / len(posts) if posts else 0
            if avg_likes > 20:
                influence_score += 0.2

            # Storytelling and personal anecdotes
            storytelling_indicators = ["story", "experience", "remember", "happened", "learned"]
            storytelling_count = sum(
                1
                for post in posts
                for indicator in storytelling_indicators
                if indicator in post.get("content", "").lower()
            )

            if storytelling_count > 0:
                influence_score += min(storytelling_count * 0.1, 0.3)

            # Comments and interactions
            comments = linkedin_data.get("comments", [])
            if len(comments) > len(posts) * 2:  # High commenting ratio
                influence_score += 0.3

        return min(influence_score, 1.0)

    async def _analyze_steadiness_indicators(self, data_sources: Dict[str, Any]) -> float:
        """Analyze indicators of Steadiness (S) traits"""
        steadiness_score = 0.0

        # Consistency in communication
        email_data = data_sources.get("email", {})
        if email_data:
            response_patterns = data_sources.get("response_timing", {})
            consistency = response_patterns.get("response_consistency", 0.5)

            if consistency > 0.7:
                steadiness_score += 0.4

        # LinkedIn indicators
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            posts = linkedin_data.get("posts", [])

            # Team and support language
            team_keywords = [
                "team",
                "support",
                "help",
                "assist",
                "together",
                "reliable",
                "stable",
                "consistent",
                "patient",
            ]

            team_mentions = sum(
                1
                for post in posts
                for keyword in team_keywords
                if keyword in post.get("content", "").lower()
            )

            if posts and team_mentions > len(posts) * 0.2:
                steadiness_score += 0.3

            # Moderate posting frequency (not too high, not too low)
            posting_freq = len(posts)
            if 5 <= posting_freq <= 20:  # Moderate, consistent posting
                steadiness_score += 0.2

            # Supportive commenting
            comments = linkedin_data.get("comments", [])
            supportive_keywords = ["great", "excellent", "agree", "exactly", "well said"]
            supportive_comments = sum(
                1
                for comment in comments
                for keyword in supportive_keywords
                if keyword in comment.get("content", "").lower()
            )

            if comments and supportive_comments > len(comments) * 0.3:
                steadiness_score += 0.3

        return min(steadiness_score, 1.0)

    async def _analyze_conscientiousness_indicators(self, data_sources: Dict[str, Any]) -> float:
        """Analyze indicators of Conscientiousness (C) traits"""
        conscientiousness_score = 0.0

        # LinkedIn indicators
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            posts = linkedin_data.get("posts", [])

            # Technical and analytical language
            technical_keywords = [
                "analysis",
                "data",
                "research",
                "methodology",
                "process",
                "accurate",
                "precise",
                "detailed",
                "systematic",
                "quality",
            ]

            technical_mentions = sum(
                1
                for post in posts
                for keyword in technical_keywords
                if keyword in post.get("content", "").lower()
            )

            if posts and technical_mentions > len(posts) * 0.3:
                conscientiousness_score += 0.4

            # Longer, detailed posts
            avg_post_length = (
                sum(len(post.get("content", "")) for post in posts) / len(posts) if posts else 0
            )
            if avg_post_length > 300:
                conscientiousness_score += 0.3

            # Industry insights and analysis
            insight_keywords = ["insight", "trend", "analysis", "report", "finding"]
            insight_mentions = sum(
                1
                for post in posts
                for keyword in insight_keywords
                if keyword in post.get("content", "").lower()
            )

            if insight_mentions > 0:
                conscientiousness_score += min(insight_mentions * 0.1, 0.2)

        # Email indicators
        email_data = data_sources.get("email", {})
        if email_data:
            messages = email_data.get("messages", [])

            # Detailed, structured emails
            avg_length = (
                sum(len(msg.get("content", "")) for msg in messages) / len(messages)
                if messages
                else 0
            )
            if avg_length > 300:
                conscientiousness_score += 0.2

            # Formal language usage
            formal_indicators = ["furthermore", "however", "therefore", "regarding", "pursuant"]
            formal_count = sum(
                1
                for msg in messages
                for indicator in formal_indicators
                if indicator in msg.get("content", "").lower()
            )

            if formal_count > 0:
                conscientiousness_score += min(formal_count * 0.05, 0.2)

        return min(conscientiousness_score, 1.0)

    def _update_disc_types(self, profile: PersonalityProfile):
        """Update primary and secondary DISC types based on scores"""
        if not profile.disc_scores:
            return

        sorted_scores = sorted(profile.disc_scores.items(), key=lambda x: x[1], reverse=True)

        type_mapping = {
            "D": PersonalityType.DOMINANT,
            "I": PersonalityType.INFLUENTIAL,
            "S": PersonalityType.STEADY,
            "C": PersonalityType.CONSCIENTIOUS,
        }

        # Primary type (highest score above threshold)
        if sorted_scores[0][1] > 0.4:
            profile.primary_disc_type = type_mapping[sorted_scores[0][0]]

            # Secondary type (second highest above threshold)
            if len(sorted_scores) > 1 and sorted_scores[1][1] > 0.3:
                profile.secondary_disc_type = type_mapping[sorted_scores[1][0]]

    async def _generate_behavioral_predictions(self, profile: PersonalityProfile):
        """Generate behavioral predictions based on DISC profile"""
        if not profile.primary_disc_type:
            return

        predictions = {
            PersonalityType.DOMINANT: [
                "prefers_quick_decisions",
                "responds_to_results_focus",
                "appreciates_direct_communication",
                "motivated_by_challenges",
                "values_efficiency_over_process",
            ],
            PersonalityType.INFLUENTIAL: [
                "enjoys_collaborative_discussions",
                "responds_to_social_proof",
                "prefers_relationship_building",
                "motivated_by_recognition",
                "values_enthusiasm_and_optimism",
            ],
            PersonalityType.STEADY: [
                "prefers_gradual_change",
                "values_team_harmony",
                "responds_to_personal_attention",
                "motivated_by_security",
                "appreciates_consistent_communication",
            ],
            PersonalityType.CONSCIENTIOUS: [
                "requires_detailed_information",
                "prefers_data_driven_decisions",
                "values_accuracy_and_quality",
                "motivated_by_expertise",
                "appreciates_systematic_approach",
            ],
        }

        primary_predictions = predictions.get(profile.primary_disc_type, [])

        # Create behavior patterns for predictions
        for prediction in primary_predictions:
            pattern = BehaviorPattern(
                pattern_type="prediction",
                pattern_name=prediction,
                description=f"Predicted behavior based on {profile.primary_disc_type.value} profile",
                confidence_level=profile.profile_confidence,
                data_points=1,
                source=ResearchSource.LINKEDIN,
            )
            pattern.predicts = [prediction]
            profile.behavior_patterns.append(pattern)

    async def _map_communication_preferences(self, profile: PersonalityProfile):
        """Map detailed communication preferences based on DISC type"""
        if not profile.primary_disc_type:
            return

        pref_mapping = {
            PersonalityType.DOMINANT: {
                "contact_methods": ["email", "phone", "direct_message"],
                "message_style": "brief_and_direct",
                "timing": "business_hours_immediate",
                "follow_up_frequency": "weekly",
                "decision_factors": ["ROI", "efficiency", "results", "competitive_advantage"],
            },
            PersonalityType.INFLUENTIAL: {
                "contact_methods": ["linkedin", "phone", "video_call", "email"],
                "message_style": "enthusiastic_and_personal",
                "timing": "flexible_with_personal_touch",
                "follow_up_frequency": "bi_weekly",
                "decision_factors": ["innovation", "relationships", "recognition", "social_impact"],
            },
            PersonalityType.STEADY: {
                "contact_methods": ["email", "scheduled_calls", "referral"],
                "message_style": "supportive_and_reliable",
                "timing": "consistent_and_predictable",
                "follow_up_frequency": "monthly",
                "decision_factors": ["stability", "support", "team_impact", "long_term_benefits"],
            },
            PersonalityType.CONSCIENTIOUS: {
                "contact_methods": ["email", "documentation", "detailed_proposals"],
                "message_style": "detailed_and_analytical",
                "timing": "planned_and_structured",
                "follow_up_frequency": "bi_weekly",
                "decision_factors": ["accuracy", "quality", "methodology", "risk_mitigation"],
            },
        }

        preferences = pref_mapping.get(profile.primary_disc_type, {})
        profile.communication_preferences = preferences
        profile.preferred_contact_methods = preferences.get("contact_methods", [])
        profile.decision_factors = preferences.get("decision_factors", [])

    async def _analyze_decision_patterns(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Analyze decision-making patterns"""
        if not profile.primary_disc_type:
            return

        decision_mapping = {
            PersonalityType.DOMINANT: DecisionMakingStyle.QUICK_DECISIVE,
            PersonalityType.INFLUENTIAL: DecisionMakingStyle.CONSENSUS_BUILDING,
            PersonalityType.STEADY: DecisionMakingStyle.CONSENSUS_BUILDING,
            PersonalityType.CONSCIENTIOUS: DecisionMakingStyle.DATA_DRIVEN,
        }

        profile.decision_making_style = decision_mapping.get(
            profile.primary_disc_type, DecisionMakingStyle.DATA_DRIVEN
        )

        # Analyze influence network from LinkedIn connections
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            connections = linkedin_data.get("connections", [])

            # Identify potential influencers
            influencers = []
            for connection in connections:
                title = connection.get("title", "").lower()
                if any(term in title for term in ["ceo", "president", "vp", "director", "head"]):
                    influencers.append(connection.get("name", ""))

            profile.influence_network = influencers[:10]  # Top 10 potential influencers


class PredictivePersonalityEngine(BasePersonalityAnalyzer):
    """
    Phase C: Advanced Predictive Modeling

    Uses machine learning approaches to predict behavior patterns,
    optimal outreach timing, and decision-making preferences.
    """

    def __init__(self, agent_id: str = "predictive_personality", config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.analysis_version = "predictive_v1.0"
        self.historical_patterns = {}  # Would load from database

    async def analyze_personality(
        self,
        prospect_id: str,
        data_sources: Dict[str, Any],
        enhanced_profile: PersonalityProfile = None,
        historical_similar_profiles: List[Dict[str, Any]] = None,
    ) -> PersonalityProfile:
        """Generate predictive personality insights"""
        profile = enhanced_profile or PersonalityProfile(
            prospect_id=prospect_id, analysis_version=self.analysis_version
        )

        # Predict optimal outreach timing
        await self._predict_optimal_timing(profile, data_sources)

        # Predict content preferences
        await self._predict_content_resonance(profile, data_sources)

        # Predict decision timeline
        await self._predict_decision_timeline(profile, historical_similar_profiles or [])

        # Predict stakeholder influence
        await self._predict_stakeholder_dynamics(profile, data_sources)

        # Update confidence
        profile.update_profile_confidence()

        logger.info(f"Predictive personality analysis completed for {prospect_id}")
        return profile

    async def _predict_optimal_timing(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Predict optimal outreach timing windows"""
        timing_patterns = {}

        # Analyze email response patterns
        email_data = data_sources.get("email", {})
        if email_data:
            response_timing = data_sources.get("response_timing", {})
            preferred_times = response_timing.get("preferred_times", [])

            if preferred_times:
                timing_patterns["email_optimal_hours"] = preferred_times
                timing_patterns["email_confidence"] = 0.8

        # Analyze LinkedIn activity patterns
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            posts = linkedin_data.get("posts", [])
            post_times = []

            for post in posts:
                if "timestamp" in post:
                    try:
                        post_time = datetime.fromisoformat(post["timestamp"])
                        post_times.append(post_time.hour)
                    except:
                        continue

            if post_times:
                # Find peak activity hours
                hour_counts = {}
                for hour in post_times:
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1

                sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
                timing_patterns["linkedin_optimal_hours"] = [
                    f"{hour}:00" for hour, _ in sorted_hours[:3]
                ]
                timing_patterns["linkedin_confidence"] = min(len(post_times) / 20, 1.0)

        # Predict optimal windows based on personality type
        if profile.primary_disc_type:
            personality_timing = {
                PersonalityType.DOMINANT: {
                    "preferred_days": ["Tuesday", "Wednesday", "Thursday"],
                    "optimal_hours": ["08:00-10:00", "14:00-16:00"],
                    "avoid_times": ["Monday_morning", "Friday_afternoon"],
                },
                PersonalityType.INFLUENTIAL: {
                    "preferred_days": ["Tuesday", "Wednesday", "Thursday"],
                    "optimal_hours": ["10:00-12:00", "15:00-17:00"],
                    "avoid_times": ["early_morning", "late_evening"],
                },
                PersonalityType.STEADY: {
                    "preferred_days": ["Tuesday", "Wednesday", "Thursday"],
                    "optimal_hours": ["09:00-11:00", "13:00-15:00"],
                    "avoid_times": ["Monday", "Friday"],
                },
                PersonalityType.CONSCIENTIOUS: {
                    "preferred_days": ["Monday", "Tuesday", "Wednesday", "Thursday"],
                    "optimal_hours": ["08:00-10:00", "13:00-15:00"],
                    "avoid_times": ["Friday_afternoon", "end_of_month"],
                },
            }

            predicted_timing = personality_timing.get(profile.primary_disc_type, {})
            timing_patterns.update(predicted_timing)

        # Store timing predictions
        timing_pattern = BehaviorPattern(
            pattern_type="timing",
            pattern_name="optimal_outreach_timing",
            description="Predicted optimal times for outreach based on observed patterns",
            confidence_level=0.7,
            data_points=len(data_sources),
            source=ResearchSource.EMAIL_INTERACTIONS,
        )

        timing_pattern.add_evidence({"predicted_timing": timing_patterns})
        profile.behavior_patterns.append(timing_pattern)

    async def _predict_content_resonance(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Predict what types of content will resonate"""
        content_preferences = {}

        # Analyze LinkedIn engagement
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            posts = linkedin_data.get("posts", [])
            comments = linkedin_data.get("comments", [])

            # Analyze content themes that get engagement
            high_engagement_posts = [p for p in posts if p.get("likes", 0) > 10]

            if high_engagement_posts:
                themes = self._extract_content_themes(high_engagement_posts)
                content_preferences["high_resonance_themes"] = themes

            # Analyze commenting patterns
            if comments:
                comment_themes = self._extract_content_themes(comments)
                content_preferences["engagement_triggers"] = comment_themes

        # Predict based on personality type
        if profile.primary_disc_type:
            personality_content = {
                PersonalityType.DOMINANT: {
                    "preferred_formats": [
                        "executive_summary",
                        "roi_focused",
                        "competitive_analysis",
                    ],
                    "message_themes": [
                        "results",
                        "efficiency",
                        "competitive_advantage",
                        "leadership",
                    ],
                    "avoid_themes": [
                        "lengthy_explanations",
                        "emotional_appeals",
                        "process_details",
                    ],
                },
                PersonalityType.INFLUENTIAL: {
                    "preferred_formats": ["case_studies", "success_stories", "testimonials"],
                    "message_themes": ["innovation", "collaboration", "recognition", "vision"],
                    "avoid_themes": ["technical_details", "risk_analysis", "lengthy_data"],
                },
                PersonalityType.STEADY: {
                    "preferred_formats": ["step_by_step_guides", "testimonials", "support_stories"],
                    "message_themes": ["reliability", "support", "stability", "team_success"],
                    "avoid_themes": ["aggressive_sales", "urgent_pressure", "major_changes"],
                },
                PersonalityType.CONSCIENTIOUS: {
                    "preferred_formats": ["detailed_analysis", "white_papers", "methodology_docs"],
                    "message_themes": ["accuracy", "quality", "research", "methodology"],
                    "avoid_themes": ["emotional_appeals", "rushed_decisions", "incomplete_data"],
                },
            }

            predicted_content = personality_content.get(profile.primary_disc_type, {})
            content_preferences.update(predicted_content)

        # Store content predictions
        content_pattern = BehaviorPattern(
            pattern_type="content_preference",
            pattern_name="predicted_content_resonance",
            description="Predicted content preferences based on engagement patterns and personality",
            confidence_level=0.6,
            data_points=len(data_sources),
            source=ResearchSource.LINKEDIN,
        )

        content_pattern.add_evidence({"content_preferences": content_preferences})
        profile.behavior_patterns.append(content_pattern)

    def _extract_content_themes(self, content_items: List[Dict[str, Any]]) -> List[str]:
        """Extract themes from content items"""
        themes = {
            "leadership": 0,
            "innovation": 0,
            "teamwork": 0,
            "results": 0,
            "technology": 0,
            "industry_insights": 0,
            "personal_development": 0,
            "company_culture": 0,
        }

        theme_keywords = {
            "leadership": ["lead", "leadership", "manage", "direct", "guide", "inspire"],
            "innovation": ["innovation", "innovative", "new", "future", "transform", "disrupt"],
            "teamwork": ["team", "collaborate", "together", "partnership", "collective"],
            "results": ["results", "achieve", "accomplish", "deliver", "success", "goal"],
            "technology": ["technology", "digital", "software", "platform", "tech", "automation"],
            "industry_insights": ["industry", "market", "trend", "analysis", "insight", "outlook"],
            "personal_development": ["learning", "growth", "development", "skill", "career"],
            "company_culture": ["culture", "values", "mission", "vision", "purpose", "employee"],
        }

        for item in content_items:
            content = item.get("content", "").lower()

            for theme, keywords in theme_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        themes[theme] += 1
                        break

        # Return top themes
        sorted_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes[:3] if count > 0]

    async def _predict_decision_timeline(
        self, profile: PersonalityProfile, historical_similar_profiles: List[Dict[str, Any]]
    ):
        """Predict decision-making timeline based on similar profiles"""
        # Default timeline based on personality type
        timeline_mapping = {
            PersonalityType.DOMINANT: "1-3 months",
            PersonalityType.INFLUENTIAL: "2-4 months",
            PersonalityType.STEADY: "4-8 months",
            PersonalityType.CONSCIENTIOUS: "3-6 months",
        }

        predicted_timeline = timeline_mapping.get(profile.primary_disc_type, "3-6 months")

        # Adjust based on historical similar profiles
        if historical_similar_profiles:
            similar_timelines = []
            for similar_profile in historical_similar_profiles:
                if similar_profile.get("decision_timeline"):
                    similar_timelines.append(similar_profile["decision_timeline"])

            if similar_timelines:
                # Most common timeline among similar profiles
                timeline_counts = {}
                for timeline in similar_timelines:
                    timeline_counts[timeline] = timeline_counts.get(timeline, 0) + 1

                most_common = max(timeline_counts.items(), key=lambda x: x[1])
                if most_common[1] >= 2:  # At least 2 similar cases
                    predicted_timeline = most_common[0]

        # Store timeline prediction
        timeline_pattern = BehaviorPattern(
            pattern_type="decision_timing",
            pattern_name="predicted_decision_timeline",
            description="Predicted time from initial contact to decision",
            confidence_level=0.6,
            data_points=len(historical_similar_profiles),
            source=ResearchSource.LINKEDIN,
        )

        timeline_pattern.add_evidence({"predicted_timeline": predicted_timeline})
        timeline_pattern.predicts = ["decision_timeline", "buying_journey_length"]
        profile.behavior_patterns.append(timeline_pattern)

    async def _predict_stakeholder_dynamics(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Predict stakeholder influence patterns"""
        stakeholder_predictions = {}

        # Analyze network to predict influence patterns
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            connections = linkedin_data.get("connections", [])

            # Identify potential decision influencers
            internal_influencers = []
            external_influencers = []

            for connection in connections:
                title = connection.get("title", "").lower()
                company = connection.get("company", "")

                # Internal company connections (potential stakeholders)
                if company == profile.prospect_id:  # Same company
                    if any(role in title for role in ["ceo", "president", "vp", "director"]):
                        internal_influencers.append(connection.get("name", ""))

                # External influencers (consultants, advisors)
                elif any(role in title for role in ["consultant", "advisor", "partner"]):
                    external_influencers.append(connection.get("name", ""))

            stakeholder_predictions["internal_influencers"] = internal_influencers[:5]
            stakeholder_predictions["external_influencers"] = external_influencers[:3]

        # Predict based on personality type and role
        if profile.primary_disc_type:
            influence_patterns = {
                PersonalityType.DOMINANT: {
                    "decision_authority": "high",
                    "influences_others": True,
                    "seeks_input": False,
                    "key_concerns": ["results", "competitive_advantage", "efficiency"],
                },
                PersonalityType.INFLUENTIAL: {
                    "decision_authority": "medium",
                    "influences_others": True,
                    "seeks_input": True,
                    "key_concerns": ["team_impact", "innovation", "relationships"],
                },
                PersonalityType.STEADY: {
                    "decision_authority": "medium",
                    "influences_others": False,
                    "seeks_input": True,
                    "key_concerns": ["stability", "team_harmony", "support"],
                },
                PersonalityType.CONSCIENTIOUS: {
                    "decision_authority": "medium",
                    "influences_others": False,
                    "seeks_input": True,
                    "key_concerns": ["accuracy", "risk_mitigation", "quality"],
                },
            }

            predicted_patterns = influence_patterns.get(profile.primary_disc_type, {})
            stakeholder_predictions.update(predicted_patterns)

        # Store stakeholder predictions
        stakeholder_pattern = BehaviorPattern(
            pattern_type="stakeholder_dynamics",
            pattern_name="predicted_stakeholder_influence",
            description="Predicted stakeholder dynamics and decision-making influence",
            confidence_level=0.5,
            data_points=len(data_sources),
            source=ResearchSource.LINKEDIN,
        )

        stakeholder_pattern.add_evidence({"stakeholder_predictions": stakeholder_predictions})
        profile.behavior_patterns.append(stakeholder_pattern)


class AdvancedPsychProfileAgent(BasePersonalityAnalyzer):
    """
    Phase D: Full Psychological Assessment

    Comprehensive psychological profiling with advanced behavioral predictions,
    cognitive style analysis, and relationship mapping capabilities.
    """

    def __init__(self, agent_id: str = "advanced_psych_profile", config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.analysis_version = "advanced_v1.0"

    async def analyze_personality(
        self,
        prospect_id: str,
        data_sources: Dict[str, Any],
        predictive_profile: PersonalityProfile = None,
    ) -> PersonalityProfile:
        """Generate comprehensive psychological assessment"""
        profile = predictive_profile or PersonalityProfile(
            prospect_id=prospect_id, analysis_version=self.analysis_version
        )

        # Advanced psychological analysis
        await self._analyze_cognitive_style(profile, data_sources)
        await self._assess_risk_tolerance(profile, data_sources)
        await self._analyze_innovation_adoption(profile, data_sources)
        await self._assess_social_proof_sensitivity(profile, data_sources)
        await self._analyze_authority_responsiveness(profile, data_sources)
        await self._map_relationship_dynamics(profile, data_sources)
        await self._predict_negotiation_style(profile, data_sources)

        # Update confidence
        profile.update_profile_confidence()

        logger.info(f"Advanced psychological assessment completed for {prospect_id}")
        return profile

    async def _analyze_cognitive_style(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Analyze cognitive processing and problem-solving style"""
        cognitive_indicators = {
            "analytical": 0.0,
            "intuitive": 0.0,
            "systematic": 0.0,
            "creative": 0.0,
        }

        # Analyze from LinkedIn content
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            posts = linkedin_data.get("posts", [])

            for post in posts:
                content = post.get("content", "").lower()

                # Analytical indicators
                analytical_keywords = [
                    "analysis",
                    "data",
                    "metrics",
                    "research",
                    "study",
                    "findings",
                ]
                if any(keyword in content for keyword in analytical_keywords):
                    cognitive_indicators["analytical"] += 0.1

                # Intuitive indicators
                intuitive_keywords = ["feel", "sense", "believe", "instinct", "intuition", "gut"]
                if any(keyword in content for keyword in intuitive_keywords):
                    cognitive_indicators["intuitive"] += 0.1

                # Systematic indicators
                systematic_keywords = [
                    "process",
                    "method",
                    "step",
                    "framework",
                    "approach",
                    "system",
                ]
                if any(keyword in content for keyword in systematic_keywords):
                    cognitive_indicators["systematic"] += 0.1

                # Creative indicators
                creative_keywords = [
                    "creative",
                    "innovative",
                    "imagine",
                    "vision",
                    "idea",
                    "concept",
                ]
                if any(keyword in content for keyword in creative_keywords):
                    cognitive_indicators["creative"] += 0.1

        # Normalize scores
        max_score = max(cognitive_indicators.values()) if cognitive_indicators.values() else 0
        if max_score > 0:
            for style, score in cognitive_indicators.items():
                cognitive_indicators[style] = score / max_score

        # Store cognitive style analysis
        cognitive_pattern = BehaviorPattern(
            pattern_type="cognitive_style",
            pattern_name="problem_solving_approach",
            description="Cognitive processing and problem-solving style analysis",
            confidence_level=0.7,
            data_points=len(data_sources),
            source=ResearchSource.LINKEDIN,
        )

        cognitive_pattern.add_evidence({"cognitive_style": cognitive_indicators})
        profile.behavior_patterns.append(cognitive_pattern)

    async def _assess_risk_tolerance(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Assess risk tolerance and decision-making under uncertainty"""
        risk_score = 0.5  # Default neutral

        # Analyze from personality type
        if profile.primary_disc_type:
            risk_mapping = {
                PersonalityType.DOMINANT: 0.8,  # High risk tolerance
                PersonalityType.INFLUENTIAL: 0.7,  # Moderate-high risk tolerance
                PersonalityType.STEADY: 0.3,  # Low risk tolerance
                PersonalityType.CONSCIENTIOUS: 0.2,  # Very low risk tolerance
            }
            risk_score = risk_mapping.get(profile.primary_disc_type, 0.5)

        # Analyze from content and behavior
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            posts = linkedin_data.get("posts", [])

            risk_taking_indicators = 0
            risk_averse_indicators = 0

            for post in posts:
                content = post.get("content", "").lower()

                # Risk-taking language
                if any(
                    word in content
                    for word in ["bold", "venture", "pioneer", "experiment", "disrupt", "challenge"]
                ):
                    risk_taking_indicators += 1

                # Risk-averse language
                if any(
                    word in content
                    for word in ["careful", "cautious", "safe", "secure", "stable", "proven"]
                ):
                    risk_averse_indicators += 1

            # Adjust risk score based on language patterns
            if posts:
                risk_ratio = risk_taking_indicators / len(posts)
                averse_ratio = risk_averse_indicators / len(posts)

                if risk_ratio > averse_ratio:
                    risk_score = min(risk_score + 0.2, 1.0)
                elif averse_ratio > risk_ratio:
                    risk_score = max(risk_score - 0.2, 0.0)

        profile.risk_tolerance = risk_score

    async def _analyze_innovation_adoption(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Analyze innovation adoption patterns (Rogers' Diffusion of Innovation)"""
        adoption_score = 0.5

        # Analyze technology and innovation mentions
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            posts = linkedin_data.get("posts", [])

            innovation_mentions = 0
            early_adoption_indicators = 0

            for post in posts:
                content = post.get("content", "").lower()

                # Innovation keywords
                if any(
                    word in content
                    for word in [
                        "innovation",
                        "new technology",
                        "emerging",
                        "cutting-edge",
                        "breakthrough",
                    ]
                ):
                    innovation_mentions += 1

                # Early adoption indicators
                if any(
                    phrase in content
                    for phrase in [
                        "first to",
                        "early adopter",
                        "pilot program",
                        "beta test",
                        "new release",
                    ]
                ):
                    early_adoption_indicators += 1

            if posts:
                innovation_ratio = innovation_mentions / len(posts)
                early_ratio = early_adoption_indicators / len(posts)

                adoption_score = (innovation_ratio + early_ratio) * 2  # Scale to 0-1
                adoption_score = min(adoption_score, 1.0)

        # Map to adoption categories
        if adoption_score > 0.8:
            profile.innovation_adoption = "innovator"
        elif adoption_score > 0.6:
            profile.innovation_adoption = "early_adopter"
        elif adoption_score > 0.4:
            profile.innovation_adoption = "early_majority"
        elif adoption_score > 0.2:
            profile.innovation_adoption = "late_majority"
        else:
            profile.innovation_adoption = "laggard"

    async def _assess_social_proof_sensitivity(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Assess sensitivity to social proof and peer influence"""
        social_proof_score = 0.5

        # Analyze from personality type
        if profile.primary_disc_type:
            social_proof_mapping = {
                PersonalityType.DOMINANT: 0.3,  # Low sensitivity (independent)
                PersonalityType.INFLUENTIAL: 0.8,  # High sensitivity (social)
                PersonalityType.STEADY: 0.7,  # Moderate-high (consensus-seeking)
                PersonalityType.CONSCIENTIOUS: 0.4,  # Moderate (evidence-based)
            }
            social_proof_score = social_proof_mapping.get(profile.primary_disc_type, 0.5)

        # Analyze social proof indicators in content
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            posts = linkedin_data.get("posts", [])

            social_proof_indicators = 0
            for post in posts:
                content = post.get("content", "").lower()

                if any(
                    phrase in content
                    for phrase in [
                        "everyone is",
                        "most people",
                        "industry standard",
                        "best practice",
                        "peer review",
                        "testimonial",
                        "recommendation",
                        "others are",
                    ]
                ):
                    social_proof_indicators += 1

            if posts and social_proof_indicators > len(posts) * 0.2:
                social_proof_score = min(social_proof_score + 0.2, 1.0)

        profile.social_proof_sensitivity = social_proof_score

    async def _analyze_authority_responsiveness(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Analyze responsiveness to authority and expertise"""
        authority_score = 0.5

        # Analyze from personality type
        if profile.primary_disc_type:
            authority_mapping = {
                PersonalityType.DOMINANT: 0.2,  # Low (challenges authority)
                PersonalityType.INFLUENTIAL: 0.6,  # Moderate (respects charisma)
                PersonalityType.STEADY: 0.8,  # High (respects hierarchy)
                PersonalityType.CONSCIENTIOUS: 0.9,  # Very high (respects expertise)
            }
            authority_score = authority_mapping.get(profile.primary_disc_type, 0.5)

        # Analyze authority references in content
        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            posts = linkedin_data.get("posts", [])

            authority_references = 0
            for post in posts:
                content = post.get("content", "").lower()

                if any(
                    phrase in content
                    for phrase in [
                        "expert says",
                        "research shows",
                        "study finds",
                        "according to",
                        "ceo mentioned",
                        "industry leader",
                        "thought leader",
                    ]
                ):
                    authority_references += 1

            if posts and authority_references > len(posts) * 0.3:
                authority_score = min(authority_score + 0.1, 1.0)

        profile.authority_responsiveness = authority_score

    async def _map_relationship_dynamics(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Map relationship dynamics and networking patterns"""
        relationship_mapping = {}

        linkedin_data = data_sources.get("linkedin", {})
        if linkedin_data:
            connections = linkedin_data.get("connections", [])

            # Analyze relationship patterns
            relationship_mapping["network_size"] = len(connections)

            # Categorize relationships
            senior_connections = 0
            peer_connections = 0
            junior_connections = 0

            for connection in connections:
                title = connection.get("title", "").lower()

                if any(term in title for term in ["ceo", "president", "vp", "director", "head"]):
                    senior_connections += 1
                elif any(term in title for term in ["manager", "lead", "senior"]):
                    peer_connections += 1
                else:
                    junior_connections += 1

            total = senior_connections + peer_connections + junior_connections
            if total > 0:
                relationship_mapping["senior_ratio"] = senior_connections / total
                relationship_mapping["peer_ratio"] = peer_connections / total
                relationship_mapping["junior_ratio"] = junior_connections / total

            # Networking strategy assessment
            if relationship_mapping.get("senior_ratio", 0) > 0.3:
                relationship_mapping["networking_strategy"] = "upward_focused"
            elif relationship_mapping.get("peer_ratio", 0) > 0.5:
                relationship_mapping["networking_strategy"] = "peer_focused"
            else:
                relationship_mapping["networking_strategy"] = "broad_based"

        # Store relationship analysis
        relationship_pattern = BehaviorPattern(
            pattern_type="relationship_dynamics",
            pattern_name="networking_and_influence_patterns",
            description="Professional relationship and networking behavior patterns",
            confidence_level=0.6,
            data_points=len(data_sources),
            source=ResearchSource.LINKEDIN,
        )

        relationship_pattern.add_evidence({"relationship_mapping": relationship_mapping})
        profile.behavior_patterns.append(relationship_pattern)

    async def _predict_negotiation_style(
        self, profile: PersonalityProfile, data_sources: Dict[str, Any]
    ):
        """Predict negotiation style and approach"""
        negotiation_predictions = {}

        # Base predictions on personality type
        if profile.primary_disc_type:
            negotiation_mapping = {
                PersonalityType.DOMINANT: {
                    "style": "competitive",
                    "approach": "direct_assertive",
                    "decision_speed": "fast",
                    "key_motivators": ["winning", "control", "results"],
                    "concession_pattern": "reluctant_large_concessions",
                },
                PersonalityType.INFLUENTIAL: {
                    "style": "collaborative",
                    "approach": "relationship_focused",
                    "decision_speed": "moderate",
                    "key_motivators": ["relationship", "recognition", "mutual_benefit"],
                    "concession_pattern": "gradual_mutual_concessions",
                },
                PersonalityType.STEADY: {
                    "style": "accommodating",
                    "approach": "consensus_building",
                    "decision_speed": "slow",
                    "key_motivators": ["harmony", "security", "fairness"],
                    "concession_pattern": "early_reasonable_concessions",
                },
                PersonalityType.CONSCIENTIOUS: {
                    "style": "analytical",
                    "approach": "fact_based",
                    "decision_speed": "very_slow",
                    "key_motivators": ["accuracy", "quality", "value"],
                    "concession_pattern": "calculated_minimal_concessions",
                },
            }

            negotiation_predictions = negotiation_mapping.get(profile.primary_disc_type, {})

        # Enhance with risk tolerance
        if profile.risk_tolerance:
            if profile.risk_tolerance > 0.7:
                negotiation_predictions["risk_approach"] = "aggressive_terms"
            elif profile.risk_tolerance < 0.3:
                negotiation_predictions["risk_approach"] = "conservative_terms"
            else:
                negotiation_predictions["risk_approach"] = "balanced_terms"

        # Store negotiation predictions
        negotiation_pattern = BehaviorPattern(
            pattern_type="negotiation_style",
            pattern_name="predicted_negotiation_approach",
            description="Predicted negotiation style and decision-making approach",
            confidence_level=0.8,
            data_points=1,
            source=ResearchSource.LINKEDIN,
        )

        negotiation_pattern.add_evidence({"negotiation_predictions": negotiation_predictions})
        negotiation_pattern.predicts = [
            "negotiation_style",
            "concession_patterns",
            "decision_speed",
        ]
        profile.behavior_patterns.append(negotiation_pattern)
