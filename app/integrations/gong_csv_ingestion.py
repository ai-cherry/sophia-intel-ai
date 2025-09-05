#!/usr/bin/env python3
"""
Gong CSV Export Ingestion Pipeline
Processes manually exported Gong data and merges with existing Weaviate database
"""

import builtins
import contextlib
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import openai
import pandas as pd
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GongCSVRecord:
    """Structured Gong CSV data"""

    call_id: str
    title: str
    date: str
    duration: int
    participants: list[str]
    transcript: str
    account_name: str = ""
    deal_stage: str = ""
    call_outcome: str = ""
    topics_discussed: list[str] = None
    action_items: list[str] = None

    def __post_init__(self):
        if self.topics_discussed is None:
            self.topics_discussed = []
        if self.action_items is None:
            self.action_items = []


class GongCSVIngestionPipeline:
    """
    Ingests Gong CSV exports into Sophia's Weaviate vector database
    Handles deduplication, chunking, embedding, and merging with existing data
    """

    def __init__(self):
        # Load credentials
        self.weaviate_endpoint = os.getenv("WEAVIATE_ENDPOINT")
        self.weaviate_key = os.getenv("WEAVIATE_API_KEY")
        openai.api_key = os.getenv("OPENAI_API_KEY")

        # Configuration
        self.chunk_size = 700  # tokens
        self.overlap = 100
        self.batch_size = 50

        # Track processing
        self.stats = {
            "files_processed": 0,
            "records_imported": 0,
            "chunks_created": 0,
            "duplicates_skipped": 0,
            "errors": [],
        }

        # Cache for deduplication
        self.existing_call_ids = set()
        self._load_existing_calls()

    def _load_existing_calls(self):
        """Load existing call IDs from Weaviate to avoid duplicates"""
        headers = {
            "Authorization": f"Bearer {self.weaviate_key}",
            "Content-Type": "application/json",
        }

        # Query for existing call IDs
        query = {
            "query": """
            {
                Get {
                    GongTranscriptChunk(limit: 10000) {
                        callId
                    }
                }
            }
            """
        }

        try:
            response = requests.post(
                f"{self.weaviate_endpoint}/v1/graphql", headers=headers, json=query
            )

            if response.status_code == 200:
                data = response.json()
                chunks = data.get("data", {}).get("Get", {}).get("GongTranscriptChunk", [])
                self.existing_call_ids = {
                    chunk["callId"] for chunk in chunks if chunk.get("callId")
                }
                logger.info(f"Loaded {len(self.existing_call_ids)} existing call IDs")
        except Exception as e:
            logger.warning(f"Could not load existing calls: {e}")

    def process_csv_file(self, csv_path: str, format_type: str = "auto") -> dict[str, Any]:
        """
        Process a Gong CSV export file

        Args:
            csv_path: Path to CSV file
            format_type: 'calls', 'transcripts', or 'auto' to detect

        Returns:
            Processing statistics
        """
        logger.info(f"Processing CSV file: {csv_path}")

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Read CSV and detect format
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from CSV")

        # Detect format if auto
        if format_type == "auto":
            format_type = self._detect_csv_format(df)
            logger.info(f"Detected format: {format_type}")

        # Process based on format
        if format_type == "calls":
            records = self._process_calls_csv(df)
        elif format_type == "transcripts":
            records = self._process_transcripts_csv(df)
        elif format_type == "detailed":
            records = self._process_detailed_csv(df)
        else:
            raise ValueError(f"Unknown format type: {format_type}")

        # Process each record
        processed_count = 0
        for record in records:
            if record.call_id in self.existing_call_ids:
                logger.info(f"Skipping duplicate call: {record.call_id}")
                self.stats["duplicates_skipped"] += 1
                continue

            try:
                self._process_record(record)
                processed_count += 1
                self.existing_call_ids.add(record.call_id)
            except Exception as e:
                logger.error(f"Error processing record {record.call_id}: {e}")
                self.stats["errors"].append(str(e))

        self.stats["files_processed"] += 1
        self.stats["records_imported"] += processed_count

        return self.stats

    def _detect_csv_format(self, df: pd.DataFrame) -> str:
        """Detect CSV format based on columns"""
        columns = df.columns.tolist()
        columns_lower = [col.lower() for col in columns]

        # Check for common column patterns
        if "transcript" in columns_lower or "transcription" in columns_lower:
            if "speaker" in columns_lower:
                return "detailed"
            return "transcripts"
        elif "call id" in columns_lower or "call_id" in columns_lower:
            return "calls"
        else:
            # Default to calls format
            return "calls"

    def _process_calls_csv(self, df: pd.DataFrame) -> list[GongCSVRecord]:
        """Process calls summary CSV"""
        records = []

        # Normalize column names
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        for _, row in df.iterrows():
            # Extract fields (handle various column name variations)
            call_id = str(row.get("call_id", row.get("id", row.get("gong_call_id", ""))))

            if not call_id:
                continue

            record = GongCSVRecord(
                call_id=call_id,
                title=row.get("title", row.get("call_title", "Unknown")),
                date=str(row.get("date", row.get("scheduled", row.get("call_date", "")))),
                duration=int(row.get("duration", row.get("duration_minutes", 0)) or 0),
                participants=self._parse_participants(row),
                transcript=row.get("notes", row.get("summary", "")),  # May not have full transcript
                account_name=row.get("account", row.get("account_name", row.get("company", ""))),
                deal_stage=row.get("deal_stage", row.get("stage", "")),
                call_outcome=row.get("outcome", row.get("result", "")),
            )

            records.append(record)

        return records

    def _process_transcripts_csv(self, df: pd.DataFrame) -> list[GongCSVRecord]:
        """Process transcripts CSV with full text"""
        records = []

        # Normalize column names
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        # Group by call ID if transcript is split across rows
        if "call_id" in df.columns:
            grouped = df.groupby("call_id")

            for call_id, group in grouped:
                # Combine transcript segments
                transcript_parts = []
                participants = set()

                for _, row in group.iterrows():
                    speaker = row.get("speaker", row.get("speaker_name", "Unknown"))
                    text = row.get("transcript", row.get("text", row.get("segment", "")))

                    if speaker and text:
                        transcript_parts.append(f"{speaker}: {text}")
                        participants.add(speaker)

                full_transcript = "\n".join(transcript_parts)

                # Get call metadata from first row
                first_row = group.iloc[0]

                record = GongCSVRecord(
                    call_id=str(call_id),
                    title=first_row.get("title", first_row.get("call_title", f"Call {call_id}")),
                    date=str(first_row.get("date", first_row.get("call_date", ""))),
                    duration=int(first_row.get("duration", 0) or 0),
                    participants=list(participants),
                    transcript=full_transcript,
                    account_name=first_row.get("account", first_row.get("account_name", "")),
                )

                records.append(record)
        else:
            # Process as single records
            for _, row in df.iterrows():
                record = GongCSVRecord(
                    call_id=str(
                        row.get(
                            "id", row.get("call_id", hashlib.md5(str(row).encode()).hexdigest())
                        )
                    ),
                    title=row.get("title", "Unknown"),
                    date=str(row.get("date", "")),
                    duration=int(row.get("duration", 0) or 0),
                    participants=self._parse_participants(row),
                    transcript=row.get("transcript", row.get("transcription", "")),
                    account_name=row.get("account", ""),
                )

                if record.transcript:  # Only add if has transcript
                    records.append(record)

        return records

    def _process_detailed_csv(self, df: pd.DataFrame) -> list[GongCSVRecord]:
        """Process detailed export with all fields"""
        records = []

        # This format has the most complete data
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        # Group by call ID
        if "call_id" in df.columns:
            grouped = df.groupby("call_id")

            for call_id, group in grouped:
                # Extract all available data
                transcript_segments = []
                speakers = set()
                topics = set()
                action_items = []

                for _, row in group.iterrows():
                    # Build transcript
                    speaker = row.get("speaker", "Unknown")
                    segment = row.get("segment", row.get("text", ""))

                    if segment:
                        transcript_segments.append(f"{speaker}: {segment}")
                        speakers.add(speaker)

                    # Extract topics if available
                    if pd.notna(row.get("topics")):
                        topics.update(str(row["topics"]).split(","))

                    # Extract action items if available
                    if pd.notna(row.get("action_items")):
                        action_items.extend(str(row["action_items"]).split(";"))

                # Combine all data
                first_row = group.iloc[0]

                record = GongCSVRecord(
                    call_id=str(call_id),
                    title=first_row.get("title", f"Call {call_id}"),
                    date=str(first_row.get("date", first_row.get("scheduled", ""))),
                    duration=int(first_row.get("duration", 0) or 0),
                    participants=list(speakers),
                    transcript="\n".join(transcript_segments),
                    account_name=first_row.get("account", ""),
                    deal_stage=first_row.get("deal_stage", ""),
                    call_outcome=first_row.get("outcome", ""),
                    topics_discussed=list(topics),
                    action_items=action_items[:10],  # Limit to 10 items
                )

                records.append(record)

        return records

    def _parse_participants(self, row: pd.Series) -> list[str]:
        """Extract participants from various column formats"""
        participants = []

        # Try different column names
        for col in ["participants", "attendees", "speakers"]:
            if col in row and pd.notna(row[col]):
                # Handle comma-separated, semicolon-separated, or JSON
                value = str(row[col])
                if value.startswith("["):
                    # JSON array
                    with contextlib.suppress(builtins.BaseException):
                        participants = json.loads(value)
                else:
                    # Delimited string
                    participants = [p.strip() for p in value.replace(";", ",").split(",")]
                break

        return participants

    def _process_record(self, record: GongCSVRecord):
        """Process a single record: chunk, embed, and store"""
        logger.info(f"Processing record: {record.title}")

        if not record.transcript:
            logger.warning(f"No transcript for call {record.call_id}")
            return

        # Chunk the transcript
        chunks = self._chunk_transcript(record.transcript, record.call_id)

        # Create embeddings
        embeddings = []
        for i in range(0, len(chunks), 20):  # Process in batches
            batch = chunks[i : i + 20]
            batch_texts = [c["text"] for c in batch]
            batch_embeddings = self._create_embeddings(batch_texts)
            embeddings.extend(batch_embeddings)

        # Store in Weaviate
        self._store_in_weaviate(chunks, embeddings, record)

        self.stats["chunks_created"] += len(chunks)

    def _chunk_transcript(self, transcript: str, call_id: str) -> list[dict]:
        """Chunk transcript into segments"""
        chunks = []

        # Simple chunking by character count (roughly 700 tokens = 2800 chars)
        chunk_size_chars = 2800
        overlap_chars = 400

        lines = transcript.split("\n")
        current_chunk = []
        current_size = 0
        chunk_index = 0

        for line in lines:
            line_size = len(line)

            if current_size + line_size > chunk_size_chars and current_chunk:
                # Save current chunk
                chunk_text = "\n".join(current_chunk)
                chunks.append(
                    {
                        "chunk_id": hashlib.md5(f"{call_id}_{chunk_index}".encode()).hexdigest(),
                        "text": chunk_text,
                        "index": chunk_index,
                    }
                )
                chunk_index += 1

                # Start new chunk with overlap
                overlap_lines = []
                overlap_size = 0
                for prev_line in reversed(current_chunk):
                    if overlap_size < overlap_chars:
                        overlap_lines.insert(0, prev_line)
                        overlap_size += len(prev_line)
                    else:
                        break

                current_chunk = overlap_lines + [line]
                current_size = overlap_size + line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        # Don't forget last chunk
        if current_chunk:
            chunk_text = "\n".join(current_chunk)
            chunks.append(
                {
                    "chunk_id": hashlib.md5(f"{call_id}_{chunk_index}".encode()).hexdigest(),
                    "text": chunk_text,
                    "index": chunk_index,
                }
            )

        return chunks

    def _create_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings using OpenAI"""
        try:
            response = openai.embeddings.create(model="text-embedding-3-small", input=texts)
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return [[0.0] * 1536 for _ in texts]  # Return zero vectors on error

    def _store_in_weaviate(
        self, chunks: list[dict], embeddings: list[list[float]], record: GongCSVRecord
    ):
        """Store chunks in Weaviate"""
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
                    "callId": record.call_id,
                    "chunkId": chunk["chunk_id"],
                    "text": chunk["text"],
                    "speaker": "Multiple"
                    if len(record.participants) > 1
                    else record.participants[0]
                    if record.participants
                    else "Unknown",
                    "chunkIndex": chunk["index"],
                    "callTitle": record.title,
                    "callDate": record.date,
                    "participants": record.participants,
                    "accountName": record.account_name,
                    "dealStage": record.deal_stage,
                    "callOutcome": record.call_outcome,
                    "topicsDiscussed": ", ".join(record.topics_discussed),
                    "source": "csv_import",
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
                logger.info(f"✅ Stored {len(objects)} chunks for call {record.call_id}")
            else:
                logger.error(f"Storage error: {response.status_code}")
        except Exception as e:
            logger.error(f"Storage exception: {e}")

    def process_directory(self, directory_path: str) -> dict[str, Any]:
        """Process all CSV files in a directory"""
        csv_files = list(Path(directory_path).glob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files to process")

        for csv_file in csv_files:
            logger.info(f"Processing: {csv_file}")
            try:
                self.process_csv_file(str(csv_file))
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}")
                self.stats["errors"].append(f"{csv_file}: {e}")

        return self.stats


def main():
    """Command-line interface for CSV ingestion"""
    import argparse

    from dotenv import load_dotenv

    load_dotenv(".env.gong_pipeline")

    parser = argparse.ArgumentParser(description="Ingest Gong CSV exports into Sophia")
    parser.add_argument("path", help="Path to CSV file or directory")
    parser.add_argument(
        "--format",
        choices=["auto", "calls", "transcripts", "detailed"],
        default="auto",
        help="CSV format type",
    )

    args = parser.parse_args()

    pipeline = GongCSVIngestionPipeline()

    if os.path.isdir(args.path):
        stats = pipeline.process_directory(args.path)
    else:
        stats = pipeline.process_csv_file(args.path, args.format)

    print("\n📊 INGESTION COMPLETE")
    print("=" * 60)
    print(f"Files processed: {stats['files_processed']}")
    print(f"Records imported: {stats['records_imported']}")
    print(f"Chunks created: {stats['chunks_created']}")
    print(f"Duplicates skipped: {stats['duplicates_skipped']}")

    if stats["errors"]:
        print(f"\n⚠️  Errors ({len(stats['errors'])}):")
        for error in stats["errors"][:5]:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
