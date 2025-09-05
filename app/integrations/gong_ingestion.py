#!/usr/bin/env python3
"""
Gong Data Ingestion Pipeline for Sophia AI
Handles full ingestion from Gong API to Weaviate with chunking and embeddings
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

import openai
import requests
from requests.auth import HTTPBasicAuth
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GongCallData:
    """Structured Gong call data"""

    call_id: str
    title: str
    scheduled: str
    duration: int
    participants: list[str]
    account_name: str = ""
    deal_id: str = ""
    purpose: str = ""
    outcome: str = ""


@dataclass
class TranscriptChunk:
    """Structured transcript chunk for vectorization"""

    call_id: str
    chunk_id: str
    text: str
    speaker: str
    start_ms: int
    end_ms: int
    account_id: str = ""
    deal_id: str = ""
    chunk_index: int = 0
    total_chunks: int = 0


class GongIngestionPipeline:
    """
    Complete Gong ingestion pipeline for Sophia AI
    Fetches -> Chunks -> Embeds -> Stores in Weaviate
    """

    def __init__(self):
        # Load credentials from environment
        self.gong_key = os.getenv("GONG_ACCESS_KEY")
        self.gong_secret = os.getenv("GONG_ACCESS_SECRET")
        self.weaviate_endpoint = os.getenv("WEAVIATE_ENDPOINT")
        self.weaviate_key = os.getenv("WEAVIATE_API_KEY")
        openai.api_key = os.getenv("OPENAI_API_KEY")

        # Configuration
        self.chunk_size = 700  # tokens
        self.overlap = 100  # tokens
        self.batch_size = 50  # Weaviate batch size

        # Stats tracking
        self.stats = {
            "calls_processed": 0,
            "chunks_created": 0,
            "embeddings_created": 0,
            "objects_stored": 0,
            "errors": [],
        }

    def get_gong_calls(self, limit: int = 100, days_back: int = 90) -> list[dict]:
        """Fetch recent calls from Gong API"""
        logger.info(f"Fetching Gong calls (last {days_back} days, limit {limit})")

        url = "https://us-70092.api.gong.io/v2/calls"
        auth = HTTPBasicAuth(self.gong_key, self.gong_secret)

        # Calculate date range
        from_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        params = {"limit": limit, "fromDate": from_date}

        try:
            response = requests.get(url, auth=auth, params=params)
            if response.status_code == 200:
                data = response.json()
                calls = data.get("calls", [])
                logger.info(f"✅ Retrieved {len(calls)} calls")
                return calls
            else:
                logger.error(f"Gong API error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching calls: {e}")
            return []

    def get_call_transcript(self, call_id: str) -> list[dict]:
        """Fetch transcript for a specific call"""
        url = f"https://us-70092.api.gong.io/v2/calls/{call_id}/transcript"
        auth = HTTPBasicAuth(self.gong_key, self.gong_secret)

        try:
            response = requests.get(url, auth=auth)
            if response.status_code == 200:
                data = response.json()
                return data.get("transcript", [])
            else:
                logger.warning(f"No transcript for call {call_id}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching transcript: {e}")
            return []

    def chunk_transcript(self, transcript: list[dict], call_id: str) -> list[TranscriptChunk]:
        """
        Intelligent chunking of transcript by speaker turns and token limits
        Groups consecutive messages by same speaker within token limits
        """
        chunks = []
        current_chunk = []
        current_speaker = None
        current_tokens = 0
        chunk_index = 0

        for segment in transcript:
            speaker = segment.get("speakerName", "Unknown")
            text = segment.get("segment", "")
            start = segment.get("start", 0)
            segment.get("end", start + 1000)

            # Estimate tokens (rough: 1 token ≈ 4 chars)
            tokens = len(text) // 4

            # Check if we need a new chunk
            if (current_speaker and speaker != current_speaker) or (
                current_tokens + tokens > self.chunk_size
            ):
                # Save current chunk
                if current_chunk:
                    chunk_text = " ".join([s["segment"] for s in current_chunk])
                    chunk_id = hashlib.md5(f"{call_id}_{chunk_index}".encode()).hexdigest()

                    chunks.append(
                        TranscriptChunk(
                            call_id=call_id,
                            chunk_id=chunk_id,
                            text=chunk_text,
                            speaker=current_speaker,
                            start_ms=current_chunk[0].get("start", 0),
                            end_ms=current_chunk[-1].get("end", 0),
                            chunk_index=chunk_index,
                        )
                    )
                    chunk_index += 1

                # Start new chunk
                current_chunk = [segment]
                current_speaker = speaker
                current_tokens = tokens
            else:
                # Add to current chunk
                current_chunk.append(segment)
                current_tokens += tokens
                if not current_speaker:
                    current_speaker = speaker

        # Don't forget last chunk
        if current_chunk:
            chunk_text = " ".join([s["segment"] for s in current_chunk])
            chunk_id = hashlib.md5(f"{call_id}_{chunk_index}".encode()).hexdigest()

            chunks.append(
                TranscriptChunk(
                    call_id=call_id,
                    chunk_id=chunk_id,
                    text=chunk_text,
                    speaker=current_speaker,
                    start_ms=current_chunk[0].get("start", 0),
                    end_ms=current_chunk[-1].get("end", 0),
                    chunk_index=chunk_index,
                )
            )

        # Update total chunks count
        for chunk in chunks:
            chunk.total_chunks = len(chunks)

        logger.info(f"Created {len(chunks)} chunks for call {call_id}")
        return chunks

    @retry(wait=wait_exponential(multiplier=1, min=1, max=60), stop=stop_after_attempt(3))
    def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings using OpenAI API with retry logic"""
        try:
            response = openai.embeddings.create(model="text-embedding-3-small", input=texts)
            embeddings = [item.embedding for item in response.data]
            self.stats["embeddings_created"] += len(embeddings)
            return embeddings
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    def store_in_weaviate(
        self, chunks: list[TranscriptChunk], embeddings: list[list[float]], call_data: GongCallData
    ):
        """Store chunks with embeddings in Weaviate"""
        headers = {
            "Authorization": f"Bearer {self.weaviate_key}",
            "Content-Type": "application/json",
        }

        # Prepare batch
        objects = []
        for chunk, embedding in zip(chunks, embeddings):
            obj = {
                "class": "GongTranscriptChunk",
                "properties": {
                    "callId": chunk.call_id,
                    "chunkId": chunk.chunk_id,
                    "text": chunk.text,
                    "speaker": chunk.speaker,
                    "startMs": chunk.start_ms,
                    "endMs": chunk.end_ms,
                    "chunkIndex": chunk.chunk_index,
                    "totalChunks": chunk.total_chunks,
                    "callTitle": call_data.title,
                    "callDate": call_data.scheduled,
                    "participants": call_data.participants,
                    "accountName": call_data.account_name,
                },
                "vector": embedding,
            }
            objects.append(obj)

        # Batch insert
        batch_data = {"objects": objects}

        try:
            response = requests.post(
                f"{self.weaviate_endpoint}/v1/batch/objects", headers=headers, json=batch_data
            )

            if response.status_code in [200, 201]:
                self.stats["objects_stored"] += len(objects)
                logger.info(f"✅ Stored {len(objects)} chunks in Weaviate")
                return True
            else:
                logger.error(f"Weaviate error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Storage error: {e}")
            return False

    def ensure_weaviate_schema(self):
        """Ensure required Weaviate classes exist"""
        headers = {
            "Authorization": f"Bearer {self.weaviate_key}",
            "Content-Type": "application/json",
        }

        # Define schema for GongTranscriptChunk
        chunk_schema = {
            "class": "GongTranscriptChunk",
            "description": "Chunked and embedded Gong call transcripts",
            "vectorizer": "none",
            "properties": [
                {"name": "callId", "dataType": ["text"], "indexFilterable": True},
                {"name": "chunkId", "dataType": ["text"], "indexFilterable": True},
                {"name": "text", "dataType": ["text"], "indexSearchable": True},
                {"name": "speaker", "dataType": ["text"], "indexFilterable": True},
                {"name": "startMs", "dataType": ["int"], "indexFilterable": True},
                {"name": "endMs", "dataType": ["int"], "indexFilterable": True},
                {"name": "chunkIndex", "dataType": ["int"], "indexFilterable": True},
                {"name": "totalChunks", "dataType": ["int"]},
                {"name": "callTitle", "dataType": ["text"], "indexSearchable": True},
                {"name": "callDate", "dataType": ["date"], "indexFilterable": True},
                {"name": "participants", "dataType": ["text[]"]},
                {"name": "accountName", "dataType": ["text"], "indexFilterable": True},
            ],
            "vectorIndexConfig": {"efConstruction": 128, "maxConnections": 64},
        }

        # Check if class exists
        response = requests.get(f"{self.weaviate_endpoint}/v1/schema", headers=headers)
        if response.status_code == 200:
            schema = response.json()
            existing_classes = [c["class"] for c in schema.get("classes", [])]

            if "GongTranscriptChunk" not in existing_classes:
                logger.info("Creating GongTranscriptChunk class...")
                create_response = requests.post(
                    f"{self.weaviate_endpoint}/v1/schema", headers=headers, json=chunk_schema
                )
                if create_response.status_code in [200, 201]:
                    logger.info("✅ GongTranscriptChunk class created")
                else:
                    logger.error(f"Failed to create class: {create_response.text}")

    def process_call(self, call: dict) -> bool:
        """Process a single call: fetch transcript, chunk, embed, store"""
        call_id = call.get("id")
        if not call_id:
            return False

        logger.info(f"Processing call: {call.get('title', 'Unknown')}")

        # Create call data object
        call_data = GongCallData(
            call_id=call_id,
            title=call.get("title", ""),
            scheduled=call.get("scheduled", ""),
            duration=call.get("duration", 0),
            participants=[p.get("name", "") for p in call.get("parties", [])],
        )

        # Get transcript
        transcript = self.get_call_transcript(call_id)
        if not transcript:
            logger.warning(f"No transcript for call {call_id}")
            return False

        # Chunk transcript
        chunks = self.chunk_transcript(transcript, call_id)
        if not chunks:
            return False

        # Create embeddings in batches
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = []

        for i in range(0, len(chunk_texts), 20):  # Process 20 at a time
            batch = chunk_texts[i : i + 20]
            batch_embeddings = self.create_embeddings(batch)
            embeddings.extend(batch_embeddings)

        # Store in Weaviate
        success = self.store_in_weaviate(chunks, embeddings, call_data)

        if success:
            self.stats["calls_processed"] += 1
            self.stats["chunks_created"] += len(chunks)

        return success

    def run_full_ingestion(self, limit: int = 100, days_back: int = 90):
        """Run full ingestion pipeline"""
        logger.info("=" * 60)
        logger.info("🚀 STARTING GONG INGESTION PIPELINE")
        logger.info("=" * 60)

        # Ensure schema exists
        self.ensure_weaviate_schema()

        # Get calls
        calls = self.get_gong_calls(limit=limit, days_back=days_back)

        if not calls:
            logger.warning("No calls to process")
            return

        # Process each call
        for i, call in enumerate(calls, 1):
            logger.info(f"\nProcessing call {i}/{len(calls)}")
            try:
                self.process_call(call)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Error processing call: {e}")
                self.stats["errors"].append(str(e))

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 INGESTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Calls processed: {self.stats['calls_processed']}")
        logger.info(f"Chunks created: {self.stats['chunks_created']}")
        logger.info(f"Embeddings created: {self.stats['embeddings_created']}")
        logger.info(f"Objects stored: {self.stats['objects_stored']}")
        logger.info(f"Errors: {len(self.stats['errors'])}")

        return self.stats


def main():
    """Run ingestion from command line"""
    from dotenv import load_dotenv

    load_dotenv(".env.gong_pipeline")

    pipeline = GongIngestionPipeline()
    stats = pipeline.run_full_ingestion(limit=10, days_back=30)

    print("\n✅ Ingestion complete!")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
