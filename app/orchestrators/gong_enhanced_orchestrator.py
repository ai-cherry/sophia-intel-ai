"""
Gong-Enhanced Sophia AI Orchestrator
Integrates Gong sales intelligence with Sophia's existing capabilities
"""

import json
import logging
import os
from typing import Any, Optional

import openai
import requests

from app.integrations.gong_ingestion import GongIngestionPipeline

logger = logging.getLogger(__name__)


class GongEnhancedOrchestrator(SophiaAGNOOrchestrator):
    """
    Enhanced Sophia orchestrator with Gong sales intelligence
    Provides unified access to Gong transcripts, emails, and insights
    """

    def __init__(self):
        super().__init__()

        # Initialize Gong components
        self.gong_pipeline = GongIngestionPipeline()
        self.weaviate_endpoint = os.getenv("WEAVIATE_ENDPOINT")
        self.weaviate_key = os.getenv("WEAVIATE_API_KEY")
        openai.api_key = os.getenv("OPENAI_API_KEY")

        # Cache for recent queries
        self.query_cache = {}

        # Enhanced capabilities
        self.capabilities.update(
            {
                "gong_search": True,
                "sales_intelligence": True,
                "call_analysis": True,
                "email_tracking": True,
                "deal_insights": True,
            }
        )

    async def search_gong_transcripts(
        self, query: str, filters: Optional[dict] = None, limit: int = 5
    ) -> list[dict]:
        """
        Search Gong transcripts using semantic search

        Args:
            query: Search query
            filters: Optional filters (account, date range, speaker)
            limit: Number of results

        Returns:
            List of relevant transcript chunks with metadata
        """
        logger.info(f"Searching Gong transcripts: {query}")

        # Create query embedding
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small", input=query
            )
            query_vector = response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return []

        # Build Weaviate query
        headers = {
            "Authorization": f"Bearer {self.weaviate_key}",
            "Content-Type": "application/json",
        }

        # GraphQL query for vector search
        where_clause = ""
        if filters:
            conditions = []
            if filters.get("account"):
                conditions.append(
                    f'path: ["accountName"], operator: Equal, valueString: "{filters["account"]}"'
                )
            if filters.get("speaker"):
                conditions.append(
                    f'path: ["speaker"], operator: Equal, valueString: "{filters["speaker"]}"'
                )
            if filters.get("date_from"):
                conditions.append(
                    f'path: ["callDate"], operator: GreaterThan, valueDate: "{filters["date_from"]}"'
                )

            if conditions:
                where_clause = (
                    f"where: {{operator: And, operands: [{{{', '.join(conditions)}}}]}}"
                )

        graphql_query = {
            "query": f"""
            {{
                Get {{
                    GongTranscriptChunk(
                        nearVector: {{vector: {json.dumps(query_vector)}, certainty: 0.7}}
                        {where_clause}
                        limit: {limit}
                    ) {{
                        callId
                        chunkId
                        text
                        speaker
                        startMs
                        endMs
                        chunkIndex
                        totalChunks
                        callTitle
                        callDate
                        participants
                        accountName
                        _additional {{
                            id
                            distance
                            certainty
                        }}
                    }}
                }}
            }}
            """
        }

        try:
            response = requests.post(
                f"{self.weaviate_endpoint}/v1/graphql",
                headers=headers,
                json=graphql_query,
            )

            if response.status_code == 200:
                data = response.json()
                chunks = (
                    data.get("data", {}).get("Get", {}).get("GongTranscriptChunk", [])
                )

                # Format results
                results = []
                for chunk in chunks:
                    results.append(
                        {
                            "call_id": chunk.get("callId"),
                            "text": chunk.get("text"),
                            "speaker": chunk.get("speaker"),
                            "call_title": chunk.get("callTitle"),
                            "timestamp": f"{chunk.get('startMs', 0) / 1000:.1f}s",
                            "relevance": chunk.get("_additional", {}).get(
                                "certainty", 0
                            ),
                            "account": chunk.get("accountName"),
                            "participants": chunk.get("participants", []),
                        }
                    )

                logger.info(f"Found {len(results)} relevant chunks")
                return results
            else:
                logger.error(f"Weaviate search error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def analyze_sales_call(self, call_id: str) -> dict[str, Any]:
        """
        Comprehensive analysis of a sales call

        Returns:
            Analysis including sentiment, topics, action items, objections
        """
        logger.info(f"Analyzing call {call_id}")

        # Get all chunks for this call
        filters = {"call_id": call_id}
        chunks = await self.search_gong_transcripts("", filters=filters, limit=100)

        if not chunks:
            return {"error": "Call not found"}

        # Combine transcript text
        full_transcript = "\n".join([f"{c['speaker']}: {c['text']}" for c in chunks])

        # Analyze with GPT
        analysis_prompt = f"""
        Analyze this sales call transcript and provide:
        1. Key Topics Discussed (bullet points)
        2. Customer Objections/Concerns
        3. Action Items/Next Steps
        4. Overall Sentiment (positive/neutral/negative)
        5. Deal Stage Assessment

        Transcript:
        {full_transcript[:8000]}  # Limit for token count

        Provide structured JSON response.
        """

        try:
            response = await self._query_llm(analysis_prompt)
            analysis = json.loads(response)

            return {
                "call_id": call_id,
                "title": chunks[0].get("call_title"),
                "participants": chunks[0].get("participants"),
                "analysis": analysis,
                "chunk_count": len(chunks),
            }
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {"error": str(e)}

    async def get_account_insights(self, account_name: str) -> dict[str, Any]:
        """
        Get comprehensive insights for a specific account

        Returns:
            Account history, recent interactions, sentiment trends
        """
        logger.info(f"Getting insights for account: {account_name}")

        # Search for all interactions with this account
        results = await self.search_gong_transcripts(
            query="", filters={"account": account_name}, limit=20
        )

        if not results:
            return {"error": "No data found for account"}

        # Group by calls
        calls = {}
        for result in results:
            call_id = result["call_id"]
            if call_id not in calls:
                calls[call_id] = {"title": result["call_title"], "chunks": []}
            calls[call_id]["chunks"].append(result)

        # Analyze trends
        insights = {
            "account_name": account_name,
            "total_calls": len(calls),
            "recent_calls": list(calls.values())[:5],
            "key_topics": self._extract_topics(results),
            "engagement_level": self._calculate_engagement(results),
        }

        return insights

    async def generate_sales_brief(self, query: str) -> str:
        """
        Generate a sales intelligence brief based on Gong data

        Args:
            query: What to research (e.g., "pricing objections in Q4")

        Returns:
            Formatted brief with insights and recommendations
        """
        logger.info(f"Generating sales brief: {query}")

        # Search relevant transcripts
        results = await self.search_gong_transcripts(query, limit=10)

        if not results:
            return "No relevant sales data found for your query."

        # Format context
        context = "\n\n".join(
            [
                f"From {r['call_title']} ({r['account']}):\n"
                f"{r['speaker']}: {r['text']}"
                for r in results[:5]
            ]
        )

        # Generate brief
        brief_prompt = f"""
        Based on these sales conversation excerpts, create a brief on: {query}

        Context:
        {context}

        Include:
        1. Key Findings
        2. Patterns/Trends
        3. Recommendations
        4. Specific Examples (with call references)

        Format as executive brief.
        """

        try:
            brief = await self._query_llm(brief_prompt)

            # Add citations
            citations = "\n\nSource Calls:\n"
            for r in results[:5]:
                citations += f"- {r['call_title']} ({r['account']})\n"

            return brief + citations

        except Exception as e:
            logger.error(f"Brief generation error: {e}")
            return f"Error generating brief: {e}"

    async def _query_llm(self, prompt: str) -> str:
        """Query LLM for analysis"""
        try:
            response = await openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sales intelligence analyst.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return ""

    def _extract_topics(self, results: list[dict]) -> list[str]:
        """Extract key topics from results"""
        # Simple keyword extraction (can be enhanced)
        text = " ".join([r["text"] for r in results])
        topics = []

        keywords = [
            "pricing",
            "implementation",
            "integration",
            "support",
            "contract",
            "timeline",
            "budget",
            "features",
            "training",
        ]

        for keyword in keywords:
            if keyword.lower() in text.lower():
                topics.append(keyword.capitalize())

        return topics[:5]

    def _calculate_engagement(self, results: list[dict]) -> str:
        """Calculate engagement level from interaction data"""
        if len(results) > 15:
            return "High"
        elif len(results) > 5:
            return "Medium"
        else:
            return "Low"

    async def sync_gong_data(self, days_back: int = 7):
        """
        Sync recent Gong data to Weaviate
        Can be called periodically for updates
        """
        logger.info(f"Syncing Gong data from last {days_back} days")

        try:
            stats = self.gong_pipeline.run_full_ingestion(limit=50, days_back=days_back)
            return {"status": "success", "stats": stats}
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return {"status": "error", "error": str(e)}

    # Override parent orchestration method to include Gong
    async def orchestrate(self, task: str, context: dict = None) -> dict[str, Any]:
        """
        Enhanced orchestration with Gong intelligence
        """
        # Check if task involves sales/customer data
        sales_keywords = [
            "sales",
            "customer",
            "call",
            "meeting",
            "deal",
            "account",
            "gong",
        ]

        if any(keyword in task.lower() for keyword in sales_keywords):
            logger.info("Routing to Gong-enhanced processing")

            # Search Gong data first
            gong_results = await self.search_gong_transcripts(task, limit=3)

            # Add to context
            if context is None:
                context = {}
            context["gong_insights"] = gong_results

        # Continue with parent orchestration
        result = await super().orchestrate(task, context)

        # Enhance result with Gong data if relevant
        if context and "gong_insights" in context:
            result["gong_data"] = context["gong_insights"]

        return result
