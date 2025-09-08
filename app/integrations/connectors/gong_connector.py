"""
Gong.io Connector
Integrates with Gong for conversation intelligence and sales insights
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from app.integrations.connectors.base_connector import (
    BaseConnector,
    ConnectorConfig,
    RateLimitStrategy,
)
from app.memory.unified_memory_router import DocChunk, MemoryDomain

logger = logging.getLogger(__name__)


class GongConnector(BaseConnector):
    """
    Gong.io integration connector

    Provides access to:
    - Call recordings and transcripts
    - Meeting insights
    - Deal intelligence
    - Coaching opportunities
    - Customer sentiment analysis
    """

    def __init__(self, config: Optional[ConnectorConfig] = None):
        """Initialize Gong connector"""
        if not config:
            config = ConnectorConfig(
                name="gong",
                base_url="https://api.gong.io",
                api_version="v2",
                timeout_seconds=60,
                rate_limit_calls=100,
                rate_limit_period=60,
                rate_limit_strategy=RateLimitStrategy.SLIDING_WINDOW,
                cache_ttl=600,
                sync_interval=7200,  # 2 hours
            )

        super().__init__(config)

        # Gong-specific configuration
        self.workspace_id = self.credentials.get("workspace_id")
        self.include_transcripts = True
        self.include_stats = True

    async def test_connection(self) -> bool:
        """Test Gong API connection"""
        try:
            response = await self.make_request(method="GET", endpoint="users/current")
            return "user" in response
        except Exception as e:
            logger.error(f"Gong connection test failed: {e}")
            return False

    async def fetch_data(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Fetch data from Gong

        Args:
            params: Query parameters

        Returns:
            Fetched data including calls, transcripts, and insights
        """
        data = {"calls": [], "transcripts": {}, "stats": {}, "insights": {}}

        # Fetch calls
        calls = await self.get_calls(params)
        data["calls"] = calls

        # Fetch transcripts for calls
        if self.include_transcripts and calls:
            transcript_tasks = []
            for call in calls[:10]:  # Limit to avoid rate limiting
                call_id = call.get("id")
                if call_id:
                    transcript_tasks.append(self.get_transcript(call_id))

            if transcript_tasks:
                transcripts = await asyncio.gather(
                    *transcript_tasks, return_exceptions=True
                )
                for call, transcript in zip(calls[:10], transcripts):
                    if not isinstance(transcript, Exception):
                        data["transcripts"][call["id"]] = transcript

        # Fetch stats
        if self.include_stats:
            data["stats"] = await self.get_stats(params)

        # Fetch insights
        data["insights"] = await self.get_insights(params)

        return data

    async def get_calls(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Get list of calls

        Args:
            params: Query parameters

        Returns:
            List of call records
        """
        try:
            # Build query parameters
            query_params = {
                "fromDateTime": params.get(
                    "modified_since", (datetime.now() - timedelta(days=7)).isoformat()
                ),
                "toDateTime": params.get("to_date", datetime.now().isoformat()),
                "limit": params.get("limit", 100),
            }

            response = await self.make_request(
                method="GET", endpoint="calls", params=query_params
            )

            return response.get("calls", [])

        except Exception as e:
            logger.error(f"Failed to fetch Gong calls: {e}")
            return []

    async def get_transcript(self, call_id: str) -> dict[str, Any]:
        """
        Get transcript for a specific call

        Args:
            call_id: Call ID

        Returns:
            Transcript data
        """
        try:
            response = await self.make_request(
                method="GET", endpoint=f"calls/{call_id}/transcript"
            )

            return {
                "call_id": call_id,
                "transcript": response.get("transcript", ""),
                "sentences": response.get("sentences", []),
                "topics": response.get("topics", []),
                "action_items": response.get("actionItems", []),
            }

        except Exception as e:
            logger.error(f"Failed to fetch transcript for call {call_id}: {e}")
            return {}

    async def get_stats(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Get aggregate statistics

        Args:
            params: Query parameters

        Returns:
            Statistics data
        """
        try:
            response = await self.make_request(
                method="GET",
                endpoint="stats/users",
                params={
                    "fromDateTime": params.get(
                        "modified_since",
                        (datetime.now() - timedelta(days=30)).isoformat(),
                    ),
                    "toDateTime": params.get("to_date", datetime.now().isoformat()),
                },
            )

            return {
                "user_stats": response.get("userStats", []),
                "team_stats": response.get("teamStats", {}),
                "call_patterns": self._analyze_call_patterns(response),
            }

        except Exception as e:
            logger.error(f"Failed to fetch Gong stats: {e}")
            return {}

    async def get_insights(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Get AI-generated insights

        Args:
            params: Query parameters

        Returns:
            Insights data
        """
        insights = {
            "deal_risks": [],
            "coaching_opportunities": [],
            "customer_sentiment": {},
            "competitive_mentions": [],
        }

        try:
            # Get deal warnings
            deal_response = await self.make_request(
                method="GET", endpoint="deals/warnings", params={"limit": 50}
            )
            insights["deal_risks"] = deal_response.get("warnings", [])

            # Get coaching opportunities
            coaching_response = await self.make_request(
                method="GET", endpoint="coaching/opportunities", params={"limit": 50}
            )
            insights["coaching_opportunities"] = coaching_response.get(
                "opportunities", []
            )

        except Exception as e:
            logger.error(f"Failed to fetch Gong insights: {e}")

        return insights

    def _analyze_call_patterns(self, stats_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze patterns in call data"""
        patterns = {
            "peak_hours": [],
            "average_duration": 0,
            "talk_ratio": 0,
            "question_rate": 0,
        }

        # Analysis logic would go here

        return patterns

    async def _transform_to_chunks(self, data: dict[str, Any]) -> list[DocChunk]:
        """Transform Gong data to document chunks"""
        chunks = []

        # Transform calls
        for call in data.get("calls", []):
            call_id = call.get("id", "unknown")

            # Create chunk for call metadata
            call_chunk = DocChunk(
                content=f"Call {call.get('title', 'Untitled')} on {call.get('startTime', 'Unknown date')}\n"
                f"Duration: {call.get('duration', 0)} minutes\n"
                f"Participants: {', '.join(call.get('participants', []))}\n"
                f"Purpose: {call.get('purpose', 'Not specified')}",
                source_uri=f"gong://calls/{call_id}",
                domain=MemoryDomain.SOPHIA,
                metadata={
                    "connector": "gong",
                    "type": "call_metadata",
                    "call_id": call_id,
                    "timestamp": call.get("startTime", datetime.now().isoformat()),
                },
            )
            chunks.append(call_chunk)

            # Create chunk for transcript if available
            if call_id in data.get("transcripts", {}):
                transcript_data = data["transcripts"][call_id]
                if transcript_data.get("transcript"):
                    transcript_chunk = DocChunk(
                        content=transcript_data["transcript"],
                        source_uri=f"gong://transcripts/{call_id}",
                        domain=MemoryDomain.SOPHIA,
                        metadata={
                            "connector": "gong",
                            "type": "transcript",
                            "call_id": call_id,
                            "topics": transcript_data.get("topics", []),
                            "action_items": transcript_data.get("action_items", []),
                        },
                    )
                    chunks.append(transcript_chunk)

        # Transform insights
        insights = data.get("insights", {})

        # Deal risks
        for risk in insights.get("deal_risks", []):
            risk_chunk = DocChunk(
                content=f"Deal Risk: {risk.get('deal_name', 'Unknown')}\n"
                f"Risk Type: {risk.get('risk_type', 'Unknown')}\n"
                f"Severity: {risk.get('severity', 'Unknown')}\n"
                f"Description: {risk.get('description', '')}",
                source_uri=f"gong://risks/{risk.get('id', 'unknown')}",
                domain=MemoryDomain.SOPHIA,
                metadata={
                    "connector": "gong",
                    "type": "deal_risk",
                    "severity": risk.get("severity"),
                    "deal_id": risk.get("deal_id"),
                },
                confidence=0.85,
            )
            chunks.append(risk_chunk)

        # Coaching opportunities
        for opp in insights.get("coaching_opportunities", []):
            coaching_chunk = DocChunk(
                content=f"Coaching Opportunity: {opp.get('rep_name', 'Unknown')}\n"
                f"Area: {opp.get('area', 'Unknown')}\n"
                f"Recommendation: {opp.get('recommendation', '')}",
                source_uri=f"gong://coaching/{opp.get('id', 'unknown')}",
                domain=MemoryDomain.SOPHIA,
                metadata={
                    "connector": "gong",
                    "type": "coaching",
                    "rep_id": opp.get("rep_id"),
                    "area": opp.get("area"),
                },
                confidence=0.80,
            )
            chunks.append(coaching_chunk)

        return chunks

    async def _process_webhook(self, payload: dict[str, Any]) -> None:
        """Process Gong webhook"""
        webhook_type = payload.get("type")

        if webhook_type == "call.completed":
            # New call completed - fetch and store
            call_id = payload.get("callId")
            if call_id:
                call_data = await self.get_calls({"call_id": call_id})
                chunks = await self._transform_to_chunks({"calls": call_data})
                if chunks:
                    await self.memory.upsert_chunks(chunks, MemoryDomain.SOPHIA)

        elif webhook_type == "transcript.ready":
            # Transcript available - fetch and store
            call_id = payload.get("callId")
            if call_id:
                transcript = await self.get_transcript(call_id)
                chunks = await self._transform_to_chunks(
                    {"transcripts": {call_id: transcript}}
                )
                if chunks:
                    await self.memory.upsert_chunks(chunks, MemoryDomain.SOPHIA)

        elif webhook_type == "deal.at_risk":
            # Deal at risk alert
            logger.warning(f"Deal at risk alert: {payload}")
            # Could trigger immediate analysis

    # ========== Specialized Gong Methods ==========

    async def search_calls(
        self,
        query: str,
        date_range: Optional[tuple] = None,
        participants: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Search for specific calls"""
        params = {"q": query}

        if date_range:
            params["fromDateTime"] = date_range[0].isoformat()
            params["toDateTime"] = date_range[1].isoformat()

        if participants:
            params["participants"] = ",".join(participants)

        response = await self.make_request(
            method="GET", endpoint="calls/search", params=params
        )

        return response.get("calls", [])

    async def get_deal_activity(self, deal_id: str) -> dict[str, Any]:
        """Get activity for a specific deal"""
        response = await self.make_request(
            method="GET", endpoint=f"deals/{deal_id}/activity"
        )

        return {
            "deal_id": deal_id,
            "calls": response.get("calls", []),
            "emails": response.get("emails", []),
            "last_activity": response.get("lastActivity"),
            "engagement_score": response.get("engagementScore"),
        }

    async def get_competitor_mentions(
        self, competitors: list[str], date_range: Optional[tuple] = None
    ) -> list[dict[str, Any]]:
        """Get mentions of competitors in calls"""
        mentions = []

        for competitor in competitors:
            results = await self.search_calls(query=competitor, date_range=date_range)

            for call in results:
                mentions.append(
                    {
                        "competitor": competitor,
                        "call_id": call.get("id"),
                        "date": call.get("startTime"),
                        "context": call.get("snippet", ""),
                    }
                )

        return mentions
