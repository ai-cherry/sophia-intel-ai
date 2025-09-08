"""
Enhanced Gong.io Connector with Corrected API Endpoints
Integrates with Gong for conversation intelligence and sales insights
Uses POST methods for transcript and extensive data endpoints
"""

import asyncio
import hashlib
import json
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import aiohttp
import asyncpg
import redis.asyncio as redis
import weaviate
from aiohttp import BasicAuth
from tenacity import retry, stop_after_attempt, wait_exponential
from weaviate.util import generate_uuid5

logger = logging.getLogger(__name__)


class GongEndpoint(Enum):
    """Gong API endpoints with corrected methods"""

    USERS_CURRENT = ("GET", "/v2/users/current")
    CALLS_LIST = ("POST", "/v2/calls/list")  # CORRECTED: Use POST
    CALLS_TRANSCRIPT = ("POST", "/v2/calls/transcript")  # CORRECTED: Use POST
    CALLS_EXTENSIVE = ("POST", "/v2/calls/extensive")  # CORRECTED: Use POST
    FLOWS_LIST = ("GET", "/v2/flows")
    DEALS_LIST = ("GET", "/v2/deals")
    STATS_USERS = ("GET", "/v2/stats/users")
    WEBHOOK_REGISTER = ("POST", "/v2/webhooks")


@dataclass
class CallFilter:
    """Filter for Gong API calls"""

    fromDateTime: Optional[str] = None
    toDateTime: Optional[str] = None
    callIds: Optional[list[str]] = None
    workspaceId: Optional[str] = None
    contentSelector: Optional[dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to API request format"""
        filter_dict = {}
        if self.fromDateTime:
            filter_dict["fromDateTime"] = self.fromDateTime
        if self.toDateTime:
            filter_dict["toDateTime"] = self.toDateTime
        if self.callIds:
            filter_dict["callIds"] = self.callIds
        if self.workspaceId:
            filter_dict["workspaceId"] = self.workspaceId
        return {"filter": filter_dict, **self.contentSelector}


@dataclass
class GongCall:
    """Structured Gong call data"""

    call_id: str
    title: str
    scheduled_at: datetime
    duration_seconds: int
    participants: list[dict[str, Any]]
    outcome: Optional[str] = None
    sentiment_score: Optional[float] = None
    talk_ratio: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptChunk:
    """Transcript chunk for vector storage"""

    call_id: str
    chunk_id: str
    text: str
    speaker: str
    start_ms: int
    end_ms: int
    sentiment: Optional[float] = None
    topics: list[str] = field(default_factory=list)
    embedding: Optional[list[float]] = None


class GongConnectorEnhanced:
    """
    Enhanced Gong.io integration connector with corrected API usage

    Key improvements:
    - Uses POST for transcript and extensive endpoints
    - Integrated with Neon Postgres, Redis, and Weaviate
    - Real-time webhook processing
    - Comprehensive error handling and retry logic
    """

    def __init__(
        self,
        access_key: str,
        client_secret: str,
        postgres_url: str,
        redis_url: str,
        weaviate_url: str,
        openai_api_key: Optional[str] = None,
    ):
        """Initialize enhanced Gong connector"""
        # API credentials
        self.access_key = access_key
        self.client_secret = client_secret
        self.base_url = "https://api.gong.io"

        # External services
        self.postgres_url = postgres_url
        self.redis_url = redis_url
        self.weaviate_url = weaviate_url
        self.openai_api_key = openai_api_key

        # Connection pools
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.weaviate_client: Optional[weaviate.Client] = None
        self.session: Optional[aiohttp.ClientSession] = None

        # Configuration
        self.rate_limit_calls = 100
        self.rate_limit_period = 60  # seconds
        self.cache_ttl = 3600  # 1 hour
        self.chunk_size = 500  # tokens
        self.batch_size = 50

        # Rate limiting state
        self.request_times: list[datetime] = []

    async def initialize(self):
        """Initialize all connections"""
        logger.info("Initializing Enhanced Gong Connector...")

        # PostgreSQL connection pool
        self.pg_pool = await asyncpg.create_pool(
            self.postgres_url, min_size=5, max_size=20, command_timeout=60
        )

        # Redis connection
        self.redis_client = await redis.from_url(
            self.redis_url, encoding="utf-8", decode_responses=True
        )

        # Weaviate client
        self.weaviate_client = weaviate.Client(
            url=self.weaviate_url,
            additional_headers=(
                {"X-OpenAI-Api-Key": self.openai_api_key} if self.openai_api_key else {}
            ),
        )

        # HTTP session
        auth = BasicAuth(self.access_key, self.client_secret)
        self.session = aiohttp.ClientSession(
            auth=auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

        # Ensure database schema exists
        await self._ensure_database_schema()

        # Ensure Weaviate schema exists
        self._ensure_weaviate_schema()

        logger.info("✅ Enhanced Gong Connector initialized successfully")

    async def cleanup(self):
        """Cleanup all connections"""
        if self.session:
            await self.session.close()
        if self.pg_pool:
            await self.pg_pool.close()
        if self.redis_client:
            await self.redis_client.close()

    async def _ensure_database_schema(self):
        """Create necessary database tables"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                """
                CREATE SCHEMA IF NOT EXISTS gong_data;

                CREATE TABLE IF NOT EXISTS gong_data.calls (
                    id VARCHAR(255) PRIMARY KEY,
                    gong_call_id VARCHAR(255) UNIQUE NOT NULL,
                    title TEXT,
                    scheduled_at TIMESTAMP WITH TIME ZONE,
                    actual_start TIMESTAMP WITH TIME ZONE,
                    duration_seconds INTEGER,
                    direction VARCHAR(50),
                    outcome VARCHAR(100),
                    deal_id VARCHAR(255),
                    account_id VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    sentiment_score DECIMAL(3,2),
                    talk_ratio DECIMAL(3,2),
                    question_count INTEGER,
                    metadata JSONB,
                    INDEX idx_calls_scheduled (scheduled_at),
                    INDEX idx_calls_sentiment (sentiment_score)
                );

                CREATE TABLE IF NOT EXISTS gong_data.call_participants (
                    id SERIAL PRIMARY KEY,
                    call_id VARCHAR(255) REFERENCES gong_data.calls(id) ON DELETE CASCADE,
                    gong_user_id VARCHAR(255),
                    name TEXT NOT NULL,
                    email VARCHAR(255),
                    role VARCHAR(100),
                    is_internal BOOLEAN DEFAULT FALSE,
                    speak_time_seconds INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS gong_data.transcript_chunks (
                    id SERIAL PRIMARY KEY,
                    call_id VARCHAR(255) REFERENCES gong_data.calls(id) ON DELETE CASCADE,
                    chunk_id VARCHAR(255) UNIQUE NOT NULL,
                    speaker_name TEXT,
                    start_ms INTEGER,
                    end_ms INTEGER,
                    chunk_index INTEGER,
                    total_chunks INTEGER,
                    content_preview TEXT,
                    key_topics TEXT[],
                    sentiment_score DECIMAL(3,2),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS gong_data.webhook_events (
                    id SERIAL PRIMARY KEY,
                    webhook_id VARCHAR(255) UNIQUE,
                    event_type VARCHAR(100) NOT NULL,
                    call_id VARCHAR(255),
                    payload JSONB NOT NULL,
                    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    processing_status VARCHAR(50) DEFAULT 'pending',
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS gong_data.api_cache (
                    id SERIAL PRIMARY KEY,
                    cache_key VARCHAR(500) UNIQUE NOT NULL,
                    endpoint VARCHAR(200) NOT NULL,
                    response_data JSONB NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """
            )
            logger.info("Database schema ensured")

    def _ensure_weaviate_schema(self):
        """Ensure Weaviate class exists for transcript chunks"""
        try:
            schema = {
                "class": "GongTranscriptChunk",
                "description": "Gong call transcript chunks with embeddings",
                "vectorizer": "text2vec-openai",
                "properties": [
                    {"name": "callId", "dataType": ["text"]},
                    {"name": "chunkId", "dataType": ["text"]},
                    {"name": "text", "dataType": ["text"]},
                    {"name": "speaker", "dataType": ["text"]},
                    {"name": "startMs", "dataType": ["int"]},
                    {"name": "endMs", "dataType": ["int"]},
                    {"name": "sentiment", "dataType": ["number"]},
                    {"name": "topics", "dataType": ["text[]"]},
                    {"name": "callTitle", "dataType": ["text"]},
                    {"name": "callDate", "dataType": ["date"]},
                ],
            }

            # Check if class exists
            existing_classes = [
                c["class"] for c in self.weaviate_client.schema.get()["classes"]
            ]
            if "GongTranscriptChunk" not in existing_classes:
                self.weaviate_client.schema.create_class(schema)
                logger.info("Weaviate schema created for GongTranscriptChunk")
        except Exception as e:
            logger.error(f"Error ensuring Weaviate schema: {e}")

    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.rate_limit_period)

        # Remove old requests
        self.request_times = [t for t in self.request_times if t > cutoff]

        # Check if we're at the limit
        if len(self.request_times) >= self.rate_limit_calls:
            sleep_time = (
                self.request_times[0] + timedelta(seconds=self.rate_limit_period) - now
            ).total_seconds()
            if sleep_time > 0:
                logger.info(
                    f"Rate limit reached, sleeping for {sleep_time:.2f} seconds"
                )
                await asyncio.sleep(sleep_time)

        # Record this request
        self.request_times.append(now)

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=60), stop=stop_after_attempt(3)
    )
    async def _make_request(
        self,
        endpoint: GongEndpoint,
        json_data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Make API request with retry logic"""
        await self._check_rate_limit()

        method, path = endpoint.value
        url = f"{self.base_url}{path}"

        logger.debug(f"Making {method} request to {url}")

        try:
            async with self.session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                response_text = await response.text()

                if response.status == 200:
                    return json.loads(response_text)
                else:
                    logger.error(f"API error {response.status}: {response_text}")
                    response.raise_for_status()

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    async def get_transcript(
        self, call_filter: CallFilter, use_cache: bool = True
    ) -> dict[str, Any]:
        """
        Get transcript using CORRECTED POST method

        This is the main fix - using POST with filter body instead of GET
        """
        cache_key = f"transcript:{json.dumps(call_filter.to_dict(), sort_keys=True)}"

        # Check cache
        if use_cache:
            cached = await self.redis_client.get(cache_key)
            if cached:
                logger.debug("Returning cached transcript")
                return json.loads(cached)

        # Make API request with POST method
        response = await self._make_request(
            endpoint=GongEndpoint.CALLS_TRANSCRIPT, json_data=call_filter.to_dict()
        )

        # Cache response
        if use_cache and response:
            await self.redis_client.setex(
                cache_key, self.cache_ttl, json.dumps(response)
            )

        return response

    async def get_extensive_calls(
        self, call_filter: CallFilter, use_cache: bool = True
    ) -> dict[str, Any]:
        """
        Get extensive call data using CORRECTED POST method

        This is another key fix - using POST with filter body
        """
        cache_key = f"extensive:{json.dumps(call_filter.to_dict(), sort_keys=True)}"

        # Check cache
        if use_cache:
            cached = await self.redis_client.get(cache_key)
            if cached:
                logger.debug("Returning cached extensive data")
                return json.loads(cached)

        # Ensure we request all needed data
        if "contentSelector" not in call_filter.to_dict():
            call_filter.contentSelector = {
                "contentSelector": {
                    "includeTranscript": False,  # We get this separately
                    "includeStats": True,
                    "includeMedia": False,
                    "includeTrackers": True,
                    "includeComments": True,
                    "includeStructure": True,
                }
            }

        # Make API request with POST method
        response = await self._make_request(
            endpoint=GongEndpoint.CALLS_EXTENSIVE, json_data=call_filter.to_dict()
        )

        # Cache response
        if use_cache and response:
            await self.redis_client.setex(
                cache_key, self.cache_ttl, json.dumps(response)
            )

        return response

    async def get_calls_list(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get list of calls using POST method"""
        if not from_date:
            from_date = datetime.now() - timedelta(days=7)
        if not to_date:
            to_date = datetime.now()

        call_filter = CallFilter(
            fromDateTime=from_date.isoformat(), toDateTime=to_date.isoformat()
        )

        request_body = {**call_filter.to_dict(), "cursor": None, "limit": limit}

        response = await self._make_request(
            endpoint=GongEndpoint.CALLS_LIST, json_data=request_body
        )

        return response.get("calls", [])

    async def process_transcript_to_chunks(
        self, call_id: str, transcript_data: dict[str, Any]
    ) -> list[TranscriptChunk]:
        """Process transcript into chunks for vector storage"""
        chunks = []

        call_transcripts = transcript_data.get("callTranscripts", [])
        if not call_transcripts:
            return chunks

        sentences = call_transcripts[0].get("sentences", [])

        # Group sentences into chunks
        current_chunk = []
        current_speaker = None
        current_text = []
        chunk_start = 0
        chunk_index = 0

        for sentence in sentences:
            speaker = sentence.get("speakerName", "Unknown")
            text = sentence.get("text", "")
            start = sentence.get("start", 0)
            end = sentence.get("end", start + 1000)

            # Check if we need a new chunk
            if current_speaker and speaker != current_speaker:
                # Save current chunk
                if current_text:
                    chunk_id = hashlib.md5(
                        f"{call_id}_{chunk_index}".encode()
                    ).hexdigest()
                    chunks.append(
                        TranscriptChunk(
                            call_id=call_id,
                            chunk_id=chunk_id,
                            text=" ".join(current_text),
                            speaker=current_speaker,
                            start_ms=chunk_start,
                            end_ms=end,
                            sentiment=None,  # To be calculated
                            topics=[],  # To be extracted
                        )
                    )
                    chunk_index += 1

                # Start new chunk
                current_chunk = [sentence]
                current_speaker = speaker
                current_text = [text]
                chunk_start = start
            else:
                # Add to current chunk
                current_chunk.append(sentence)
                current_text.append(text)
                if not current_speaker:
                    current_speaker = speaker
                    chunk_start = start

        # Don't forget last chunk
        if current_text:
            chunk_id = hashlib.md5(f"{call_id}_{chunk_index}".encode()).hexdigest()
            chunks.append(
                TranscriptChunk(
                    call_id=call_id,
                    chunk_id=chunk_id,
                    text=" ".join(current_text),
                    speaker=current_speaker,
                    start_ms=chunk_start,
                    end_ms=sentences[-1].get("end", 0),
                    sentiment=None,
                    topics=[],
                )
            )

        logger.info(f"Created {len(chunks)} chunks for call {call_id}")
        return chunks

    async def store_chunks_in_weaviate(
        self, chunks: list[TranscriptChunk], call_metadata: dict[str, Any]
    ):
        """Store transcript chunks in Weaviate for vector search"""
        batch = []

        for chunk in chunks:
            weaviate_object = {
                "callId": chunk.call_id,
                "chunkId": chunk.chunk_id,
                "text": chunk.text,
                "speaker": chunk.speaker,
                "startMs": chunk.start_ms,
                "endMs": chunk.end_ms,
                "sentiment": chunk.sentiment or 0.0,
                "topics": chunk.topics or [],
                "callTitle": call_metadata.get("title", ""),
                "callDate": call_metadata.get("scheduled", datetime.now().isoformat()),
            }

            batch.append(weaviate_object)

            # Batch insert when we reach batch size
            if len(batch) >= self.batch_size:
                self._insert_weaviate_batch(batch)
                batch = []

        # Insert remaining
        if batch:
            self._insert_weaviate_batch(batch)

        logger.info(f"Stored {len(chunks)} chunks in Weaviate")

    def _insert_weaviate_batch(self, batch: list[dict]):
        """Insert batch of objects into Weaviate"""
        with self.weaviate_client.batch as batch_context:
            for obj in batch:
                batch_context.add_data_object(
                    obj, "GongTranscriptChunk", uuid=generate_uuid5(obj["chunkId"])
                )

    async def store_call_in_postgres(
        self, call_data: dict[str, Any], extensive_data: Optional[dict] = None
    ):
        """Store call data in PostgreSQL"""
        async with self.pg_pool.acquire() as conn:
            # Extract stats if available
            stats = extensive_data.get("stats", {}) if extensive_data else {}

            # Insert or update call
            await conn.execute(
                """
                INSERT INTO gong_data.calls (
                    id, gong_call_id, title, scheduled_at, duration_seconds,
                    direction, outcome, sentiment_score, talk_ratio, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (gong_call_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    sentiment_score = EXCLUDED.sentiment_score,
                    talk_ratio = EXCLUDED.talk_ratio,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
            """,
                call_data.get("id"),
                call_data.get("id"),
                call_data.get("title", ""),
                datetime.fromisoformat(
                    call_data.get("scheduled", datetime.now().isoformat())
                ),
                call_data.get("duration", 0),
                call_data.get("direction", "unknown"),
                call_data.get("outcome", ""),
                stats.get("sentimentScore"),
                stats.get("talkRatio"),
                json.dumps(call_data),
            )

            # Insert participants
            for participant in call_data.get("parties", []):
                await conn.execute(
                    """
                    INSERT INTO gong_data.call_participants (
                        call_id, gong_user_id, name, email, role, is_internal
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT DO NOTHING
                """,
                    call_data.get("id"),
                    participant.get("userId"),
                    participant.get("name", "Unknown"),
                    participant.get("emailAddress"),
                    participant.get("affiliation", "unknown"),
                    participant.get("affiliation") == "internal",
                )

    async def process_webhook(self, event_type: str, payload: dict[str, Any]):
        """Process incoming webhook from Gong"""
        webhook_id = payload.get(
            "webhookId", hashlib.md5(json.dumps(payload).encode()).hexdigest()
        )
        call_id = payload.get("callId")

        async with self.pg_pool.acquire() as conn:
            # Log webhook event
            await conn.execute(
                """
                INSERT INTO gong_data.webhook_events (
                    webhook_id, event_type, call_id, payload, processing_status
                ) VALUES ($1, $2, $3, $4, 'processing')
                ON CONFLICT (webhook_id) DO NOTHING
            """,
                webhook_id,
                event_type,
                call_id,
                json.dumps(payload),
            )

            try:
                # Process based on event type
                if event_type == "call.ended":
                    await self._handle_call_ended(call_id)
                elif event_type == "transcript.ready":
                    await self._handle_transcript_ready(call_id)
                elif event_type == "deal.at_risk":
                    await self._handle_deal_risk(payload)

                # Mark as processed
                await conn.execute(
                    """
                    UPDATE gong_data.webhook_events
                    SET processing_status = 'completed'
                    WHERE webhook_id = $1
                """,
                    webhook_id,
                )

            except Exception as e:
                # Mark as failed
                await conn.execute(
                    """
                    UPDATE gong_data.webhook_events
                    SET processing_status = 'failed',
                        error_message = $2,
                        retry_count = retry_count + 1
                    WHERE webhook_id = $1
                """,
                    webhook_id,
                    str(e),
                )
                raise

    async def _handle_call_ended(self, call_id: str):
        """Handle call ended webhook"""
        logger.info(f"Processing ended call: {call_id}")

        # Fetch call data
        call_filter = CallFilter(callIds=[call_id])
        extensive_data = await self.get_extensive_calls(call_filter)

        if extensive_data and extensive_data.get("calls"):
            call_data = extensive_data["calls"][0]
            await self.store_call_in_postgres(call_data, extensive_data)

    async def _handle_transcript_ready(self, call_id: str):
        """Handle transcript ready webhook"""
        logger.info(f"Processing transcript for call: {call_id}")

        # Fetch transcript
        call_filter = CallFilter(callIds=[call_id])
        transcript_data = await self.get_transcript(call_filter)

        if transcript_data:
            # Process into chunks
            chunks = await self.process_transcript_to_chunks(call_id, transcript_data)

            # Get call metadata for context
            extensive_data = await self.get_extensive_calls(call_filter)
            call_metadata = (
                extensive_data.get("calls", [{}])[0] if extensive_data else {}
            )

            # Store in Weaviate
            await self.store_chunks_in_weaviate(chunks, call_metadata)

            # Store chunk references in PostgreSQL
            async with self.pg_pool.acquire() as conn:
                for chunk in chunks:
                    await conn.execute(
                        """
                        INSERT INTO gong_data.transcript_chunks (
                            call_id, chunk_id, speaker_name, start_ms, end_ms,
                            chunk_index, content_preview
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (chunk_id) DO NOTHING
                    """,
                        chunk.call_id,
                        chunk.chunk_id,
                        chunk.speaker,
                        chunk.start_ms,
                        chunk.end_ms,
                        chunks.index(chunk),
                        chunk.text[:200],
                    )

    async def _handle_deal_risk(self, payload: dict[str, Any]):
        """Handle deal at risk webhook"""
        logger.warning(f"Deal at risk: {payload}")
        # Additional processing for deal risks
        # Could trigger alerts, notifications, etc.

    async def batch_process_calls(
        self,
        call_ids: list[str],
        batch_size: int = 10,
        include_transcript: bool = True,
        include_extensive: bool = True,
    ) -> dict[str, Any]:
        """Batch process multiple calls efficiently"""
        results = {
            "processed": [],
            "failed": [],
            "transcripts": {},
            "extensive_data": {},
        }

        # Process in batches
        for i in range(0, len(call_ids), batch_size):
            batch_ids = call_ids[i : i + batch_size]

            try:
                # Fetch extensive data if requested
                if include_extensive:
                    call_filter = CallFilter(callIds=batch_ids)
                    extensive = await self.get_extensive_calls(call_filter)
                    results["extensive_data"].update(
                        {call["id"]: call for call in extensive.get("calls", [])}
                    )

                # Fetch transcripts if requested
                if include_transcript:
                    call_filter = CallFilter(callIds=batch_ids)
                    transcripts = await self.get_transcript(call_filter)

                    for transcript in transcripts.get("callTranscripts", []):
                        call_id = transcript.get("callId")
                        if call_id:
                            results["transcripts"][call_id] = transcript

                results["processed"].extend(batch_ids)

            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                results["failed"].extend(batch_ids)

            # Small delay between batches
            await asyncio.sleep(0.5)

        return results

    async def search_transcripts(
        self, query: str, limit: int = 10, filters: Optional[dict] = None
    ) -> list[dict[str, Any]]:
        """Search transcripts using Weaviate vector search"""
        where_filter = None
        if filters:
            # Build Weaviate where filter
            conditions = []
            if "speaker" in filters:
                conditions.append(
                    {
                        "path": ["speaker"],
                        "operator": "Equal",
                        "valueString": filters["speaker"],
                    }
                )
            if "call_id" in filters:
                conditions.append(
                    {
                        "path": ["callId"],
                        "operator": "Equal",
                        "valueString": filters["call_id"],
                    }
                )

            if conditions:
                where_filter = (
                    {"operator": "And", "operands": conditions}
                    if len(conditions) > 1
                    else conditions[0]
                )

        # Perform vector search
        result = (
            self.weaviate_client.query.get(
                "GongTranscriptChunk",
                ["text", "speaker", "callId", "startMs", "endMs", "sentiment"],
            )
            .with_near_text({"concepts": [query]})
            .with_limit(limit)
        )

        if where_filter:
            result = result.with_where(where_filter)

        response = result.do()

        return response.get("data", {}).get("Get", {}).get("GongTranscriptChunk", [])

    async def get_analytics(
        self, from_date: datetime, to_date: datetime, group_by: str = "day"
    ) -> dict[str, Any]:
        """Get analytics for a date range"""
        async with self.pg_pool.acquire() as conn:
            # Get call statistics
            call_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_calls,
                    AVG(duration_seconds) as avg_duration,
                    AVG(sentiment_score) as avg_sentiment,
                    AVG(talk_ratio) as avg_talk_ratio
                FROM gong_data.calls
                WHERE scheduled_at BETWEEN $1 AND $2
            """,
                from_date,
                to_date,
            )

            # Get top performers
            top_performers = await conn.fetch(
                """
                SELECT
                    p.name,
                    COUNT(DISTINCT c.id) as call_count,
                    AVG(c.sentiment_score) as avg_sentiment
                FROM gong_data.call_participants p
                JOIN gong_data.calls c ON p.call_id = c.id
                WHERE c.scheduled_at BETWEEN $1 AND $2
                    AND p.is_internal = true
                GROUP BY p.name
                ORDER BY avg_sentiment DESC
                LIMIT 10
            """,
                from_date,
                to_date,
            )

            return {
                "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
                "statistics": dict(call_stats) if call_stats else {},
                "top_performers": [dict(p) for p in top_performers],
            }

    async def health_check(self) -> dict[str, bool]:
        """Check health of all connections"""
        health = {
            "gong_api": False,
            "postgres": False,
            "redis": False,
            "weaviate": False,
        }

        # Check Gong API
        try:
            response = await self._make_request(GongEndpoint.USERS_CURRENT)
            health["gong_api"] = bool(response)
        except Exception:pass

        # Check PostgreSQL
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                health["postgres"] = True
        except Exception:pass

        # Check Redis
        try:
            await self.redis_client.ping()
            health["redis"] = True
        except Exception:pass

        # Check Weaviate
        try:
            self.weaviate_client.schema.get()
            health["weaviate"] = True
        except Exception:pass

        return health


@asynccontextmanager
async def create_gong_connector(
    postgres_url: Optional[str] = None,
    redis_url: Optional[str] = None,
    weaviate_url: Optional[str] = None,
):
    """Context manager for Gong connector"""
    connector = GongConnectorEnhanced(
        access_key=os.getenv("GONG_ACCESS_KEY", "TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N"),
        client_secret=os.getenv(
            "GONG_CLIENT_SECRET",
            "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tleSI6IlRWMzNCUFo1VU40NVFLWkNaMlVDQUtSWEhRNlEzTDVOIn0.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU",
        ),
        postgres_url=postgres_url
        or os.getenv("DATABASE_URL", "postgresql://localhost/sophia"),
        redis_url=redis_url or os.getenv("REDIS_URL", "redis://localhost:6379"),
        weaviate_url=weaviate_url or os.getenv("WEAVIATE_URL", "http://localhost:8080"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    await connector.initialize()

    try:
        yield connector
    finally:
        await connector.cleanup()


# Example usage
async def main():
    """Example usage of enhanced Gong connector"""
    async with create_gong_connector() as connector:
        # Check health
        health = await connector.health_check()
        print(f"System health: {health}")

        # Get recent calls
        calls = await connector.get_calls_list(limit=5)
        print(f"Found {len(calls)} recent calls")

        # Process first call if available
        if calls:
            call_id = calls[0]["id"]

            # Get transcript with CORRECTED POST method
            call_filter = CallFilter(callIds=[call_id])
            transcript = await connector.get_transcript(call_filter)
            print(f"Got transcript: {bool(transcript)}")

            # Get extensive data with CORRECTED POST method
            extensive = await connector.get_extensive_calls(call_filter)
            print(f"Got extensive data: {bool(extensive)}")

            # Search transcripts
            results = await connector.search_transcripts("objection")
            print(f"Found {len(results)} matches for 'objection'")


if __name__ == "__main__":
    asyncio.run(main())
