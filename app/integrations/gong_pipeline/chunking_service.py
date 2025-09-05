"""
Intelligent Chunking and Embedding Service for Gong Data
Uses OpenAI for embeddings and advanced chunking strategies for calls, transcripts, and emails
"""

import asyncio
import hashlib
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import backoff
import openai
import tiktoken
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class ChunkType(str, Enum):
    """Types of chunks based on content"""

    CALL_SUMMARY = "call_summary"
    TRANSCRIPT_SEGMENT = "transcript_segment"
    EMAIL_CONTENT = "email_content"
    SPEAKER_TURN = "speaker_turn"
    TOPIC_SECTION = "topic_section"


class ContentType(str, Enum):
    """Source content types"""

    CALL_TRANSCRIPT = "call_transcript"
    EMAIL_BODY = "email_body"
    CALL_SUMMARY = "call_summary"
    MEETING_NOTES = "meeting_notes"


@dataclass
class ChunkMetadata:
    """Metadata for content chunks"""

    chunk_id: str
    source_id: str  # call_id, email_id, etc.
    source_type: ContentType
    chunk_type: ChunkType
    chunk_index: int
    total_chunks: int
    start_position: int
    end_position: int
    token_count: int
    character_count: int

    # Content-specific metadata
    speaker_id: Optional[str] = None
    speaker_name: Optional[str] = None
    speaker_role: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    confidence: Optional[float] = None
    sentiment: Optional[str] = None
    topics: list[str] = None
    keywords: list[str] = None
    entities: list[str] = None

    # Email-specific
    email_type: Optional[str] = None
    from_email: Optional[str] = None
    to_emails: list[str] = None

    # General
    created_at: datetime = None

    def __post_init__(self):
        if self.topics is None:
            self.topics = []
        if self.keywords is None:
            self.keywords = []
        if self.entities is None:
            self.entities = []
        if self.to_emails is None:
            self.to_emails = []
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ContentChunk:
    """Individual content chunk with embedding"""

    content: str
    metadata: ChunkMetadata
    embedding: Optional[list[float]] = None
    embedding_model: str = "text-embedding-3-small"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "content": self.content,
            "metadata": asdict(self.metadata),
            "embedding": self.embedding,
            "embedding_model": self.embedding_model,
        }


class OpenAIEmbeddingService:
    """Service for generating embeddings using OpenAI"""

    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Rate limiting and batch processing
        self.max_batch_size = 100
        self.max_tokens_per_request = 8000

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

    @backoff.on_exception(backoff.expo, openai.RateLimitError, max_tries=3)
    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for multiple texts with batching"""
        if not texts:
            return []

        # Process in batches to handle rate limits
        all_embeddings = []

        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i : i + self.max_batch_size]

            # Filter out overly long texts
            batch_filtered = []
            for text in batch:
                if self.count_tokens(text) <= self.max_tokens_per_request:
                    batch_filtered.append(text)
                else:
                    # Truncate if too long
                    tokens = self.encoding.encode(text)[: self.max_tokens_per_request]
                    batch_filtered.append(self.encoding.decode(tokens))

            try:
                response = await self.client.embeddings.create(
                    input=batch_filtered, model=self.model
                )

                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.debug(f"Generated embeddings for batch of {len(batch_filtered)} texts")

            except Exception as e:
                logger.error(f"Failed to get embeddings for batch: {e}")
                # Add empty embeddings for failed batch
                all_embeddings.extend([[] for _ in batch_filtered])

        return all_embeddings

    async def get_single_embedding(self, text: str) -> list[float]:
        """Get embedding for single text"""
        embeddings = await self.get_embeddings([text])
        return embeddings[0] if embeddings else []


class IntelligentChunker:
    """Advanced chunking service for different content types"""

    def __init__(
        self,
        embedding_service: OpenAIEmbeddingService,
        max_chunk_tokens: int = 512,
        overlap_tokens: int = 50,
    ):
        self.embedding_service = embedding_service
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Sentence boundary patterns
        self.sentence_endings = re.compile(r"[.!?]+\s+")
        self.speaker_pattern = re.compile(r"^([^:]+):\s+(.+)$", re.MULTILINE)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

    async def chunk_call_transcript(
        self, call_data: dict[str, Any], transcript_segments: list[dict[str, Any]]
    ) -> list[ContentChunk]:
        """Chunk call transcript into meaningful segments"""
        chunks = []

        # Strategy 1: Chunk by speaker turns
        speaker_chunks = await self._chunk_by_speaker_turns(call_data, transcript_segments)
        chunks.extend(speaker_chunks)

        # Strategy 2: Create topic-based chunks if we have long segments
        if len(speaker_chunks) > 10:
            topic_chunks = await self._chunk_by_topics(call_data, transcript_segments)
            chunks.extend(topic_chunks)

        # Strategy 3: Create summary chunk
        if call_data.get("summary"):
            summary_chunk = await self._create_summary_chunk(call_data)
            chunks.append(summary_chunk)

        return chunks

    async def _chunk_by_speaker_turns(
        self, call_data: dict[str, Any], transcript_segments: list[dict[str, Any]]
    ) -> list[ContentChunk]:
        """Chunk transcript by speaker turns with smart grouping"""
        chunks = []
        current_speaker = None
        current_content = []
        current_metadata_list = []

        for segment in transcript_segments:
            speaker_id = segment.get("speaker_id", "unknown")
            content = segment.get("content", "").strip()

            if not content:
                continue

            # Start new chunk if speaker changes or chunk gets too long
            if (
                speaker_id != current_speaker
                or self.count_tokens(" ".join(current_content + [content])) > self.max_chunk_tokens
            ):
                # Save current chunk if we have content
                if current_content:
                    chunk = await self._create_speaker_chunk(
                        call_data,
                        current_content,
                        current_metadata_list,
                        len(chunks),
                        current_speaker,
                    )
                    chunks.append(chunk)

                # Start new chunk
                current_speaker = speaker_id
                current_content = [content]
                segment.get("start_time")
                current_metadata_list = [segment]
            else:
                # Add to current chunk
                current_content.append(content)
                current_metadata_list.append(segment)

        # Handle final chunk
        if current_content:
            chunk = await self._create_speaker_chunk(
                call_data, current_content, current_metadata_list, len(chunks), current_speaker
            )
            chunks.append(chunk)

        return chunks

    async def _create_speaker_chunk(
        self,
        call_data: dict[str, Any],
        content_list: list[str],
        segments: list[dict[str, Any]],
        chunk_index: int,
        speaker_id: str,
    ) -> ContentChunk:
        """Create a speaker turn chunk"""
        content = " ".join(content_list)

        # Get speaker info from first segment
        first_segment = segments[0]
        last_segment = segments[-1]

        # Generate unique chunk ID
        chunk_id = hashlib.md5(
            f"{call_data.get('id', '')}_{speaker_id}_{chunk_index}_{content[:50]}".encode()
        ).hexdigest()[:16]

        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            source_id=call_data.get("id", ""),
            source_type=ContentType.CALL_TRANSCRIPT,
            chunk_type=ChunkType.SPEAKER_TURN,
            chunk_index=chunk_index,
            total_chunks=0,  # Will be updated later
            start_position=first_segment.get("start_time", 0),
            end_position=last_segment.get("end_time", 0),
            token_count=self.count_tokens(content),
            character_count=len(content),
            speaker_id=speaker_id,
            speaker_name=first_segment.get("speaker_name", ""),
            speaker_role=first_segment.get("speaker_role", ""),
            start_time=first_segment.get("start_time"),
            end_time=last_segment.get("end_time"),
            confidence=sum(s.get("confidence", 0) for s in segments) / len(segments),
            topics=self._extract_topics(content),
            keywords=self._extract_keywords(content),
            entities=self._extract_entities(content),
        )

        # Generate embedding
        embedding = await self.embedding_service.get_single_embedding(content)

        return ContentChunk(content=content, metadata=metadata, embedding=embedding)

    async def _chunk_by_topics(
        self, call_data: dict[str, Any], transcript_segments: list[dict[str, Any]]
    ) -> list[ContentChunk]:
        """Create topic-based chunks for long conversations"""
        # This is a simplified implementation
        # In production, you might use topic modeling or NLP libraries

        full_text = " ".join(segment.get("content", "") for segment in transcript_segments)

        # Split into sentences and group by topics (simplified)
        sentences = self.sentence_endings.split(full_text)

        chunks = []
        current_chunk = []
        current_tokens = 0

        for _i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_tokens = self.count_tokens(sentence)

            if current_tokens + sentence_tokens > self.max_chunk_tokens and current_chunk:
                # Create chunk
                chunk_content = " ".join(current_chunk)
                chunk = await self._create_topic_chunk(call_data, chunk_content, len(chunks))
                chunks.append(chunk)

                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) > 2 else []
                current_chunk = overlap_sentences + [sentence]
                current_tokens = sum(self.count_tokens(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        # Handle final chunk
        if current_chunk:
            chunk_content = " ".join(current_chunk)
            chunk = await self._create_topic_chunk(call_data, chunk_content, len(chunks))
            chunks.append(chunk)

        return chunks

    async def _create_topic_chunk(
        self, call_data: dict[str, Any], content: str, chunk_index: int
    ) -> ContentChunk:
        """Create a topic-based chunk"""
        chunk_id = hashlib.md5(
            f"{call_data.get('id', '')}_topic_{chunk_index}_{content[:50]}".encode()
        ).hexdigest()[:16]

        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            source_id=call_data.get("id", ""),
            source_type=ContentType.CALL_TRANSCRIPT,
            chunk_type=ChunkType.TOPIC_SECTION,
            chunk_index=chunk_index,
            total_chunks=0,
            start_position=0,
            end_position=len(content),
            token_count=self.count_tokens(content),
            character_count=len(content),
            topics=self._extract_topics(content),
            keywords=self._extract_keywords(content),
            entities=self._extract_entities(content),
        )

        embedding = await self.embedding_service.get_single_embedding(content)

        return ContentChunk(content=content, metadata=metadata, embedding=embedding)

    async def _create_summary_chunk(self, call_data: dict[str, Any]) -> ContentChunk:
        """Create a summary chunk for the call"""
        summary = call_data.get("summary", "")

        chunk_id = hashlib.md5(
            f"{call_data.get('id', '')}_summary_{summary[:50]}".encode()
        ).hexdigest()[:16]

        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            source_id=call_data.get("id", ""),
            source_type=ContentType.CALL_SUMMARY,
            chunk_type=ChunkType.CALL_SUMMARY,
            chunk_index=0,
            total_chunks=1,
            start_position=0,
            end_position=len(summary),
            token_count=self.count_tokens(summary),
            character_count=len(summary),
            topics=self._extract_topics(summary),
            keywords=self._extract_keywords(summary),
        )

        embedding = await self.embedding_service.get_single_embedding(summary)

        return ContentChunk(content=summary, metadata=metadata, embedding=embedding)

    async def chunk_email(self, email_data: dict[str, Any]) -> list[ContentChunk]:
        """Chunk email content intelligently"""
        chunks = []

        # Subject + body for context
        subject = email_data.get("subject", "")
        body_plain = email_data.get("body_plain", "") or email_data.get("body_html", "")

        if not body_plain:
            return chunks

        # For emails, we typically create one chunk unless it's very long
        full_content = f"Subject: {subject}\n\n{body_plain}"

        if self.count_tokens(full_content) <= self.max_chunk_tokens:
            # Single chunk
            chunk = await self._create_email_chunk(email_data, full_content, 0, 1)
            chunks.append(chunk)
        else:
            # Split into multiple chunks
            content_chunks = self._split_text_with_overlap(body_plain)

            for i, chunk_content in enumerate(content_chunks):
                # Add subject to each chunk for context
                full_chunk_content = f"Subject: {subject}\n\n{chunk_content}"
                chunk = await self._create_email_chunk(
                    email_data, full_chunk_content, i, len(content_chunks)
                )
                chunks.append(chunk)

        return chunks

    async def _create_email_chunk(
        self, email_data: dict[str, Any], content: str, chunk_index: int, total_chunks: int
    ) -> ContentChunk:
        """Create an email content chunk"""
        chunk_id = hashlib.md5(
            f"{email_data.get('id', '')}_email_{chunk_index}_{content[:50]}".encode()
        ).hexdigest()[:16]

        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            source_id=email_data.get("id", ""),
            source_type=ContentType.EMAIL_BODY,
            chunk_type=ChunkType.EMAIL_CONTENT,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            start_position=chunk_index * self.max_chunk_tokens,
            end_position=(chunk_index + 1) * self.max_chunk_tokens,
            token_count=self.count_tokens(content),
            character_count=len(content),
            email_type=email_data.get("email_type", ""),
            from_email=email_data.get("from_email", ""),
            to_emails=email_data.get("to_emails", []),
            topics=self._extract_topics(content),
            keywords=self._extract_keywords(content),
            entities=self._extract_entities(content),
        )

        embedding = await self.embedding_service.get_single_embedding(content)

        return ContentChunk(content=content, metadata=metadata, embedding=embedding)

    def _split_text_with_overlap(self, text: str) -> list[str]:
        """Split text into chunks with overlap"""
        sentences = self.sentence_endings.split(text)

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_tokens = self.count_tokens(sentence)

            if current_tokens + sentence_tokens > self.max_chunk_tokens and current_chunk:
                # Create chunk
                chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap
                overlap_size = min(self.overlap_tokens, len(current_chunk) // 2)
                if overlap_size > 0:
                    current_chunk = current_chunk[-overlap_size:] + [sentence]
                    current_tokens = sum(self.count_tokens(s) for s in current_chunk)
                else:
                    current_chunk = [sentence]
                    current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _extract_topics(self, text: str) -> list[str]:
        """Extract topics from text (simplified implementation)"""
        # This is a placeholder - in production you'd use proper NLP
        topics = []

        # Simple keyword-based topic detection
        topic_keywords = {
            "sales": ["deal", "price", "contract", "proposal", "quote", "revenue", "purchase"],
            "technical": [
                "system",
                "implementation",
                "integration",
                "API",
                "database",
                "architecture",
            ],
            "support": ["issue", "problem", "bug", "error", "troubleshoot", "help", "fix"],
            "meeting": ["schedule", "agenda", "follow-up", "action items", "next steps"],
            "product": ["feature", "functionality", "requirements", "specification", "demo"],
        }

        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)

        return topics

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract important keywords (simplified implementation)"""
        # This is a placeholder - in production you'd use proper NLP
        import re

        # Remove common stop words and extract meaningful terms
        stop_words = {
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
            "must",
            "shall",
            "can",
            "cannot",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "its",
            "our",
            "their",
            "this",
            "that",
            "these",
            "those",
            "a",
            "an",
        }

        # Extract words that are not stop words and have length > 3
        words = re.findall(r"\b\w+\b", text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 3]

        # Return most frequent keywords (up to 10)
        from collections import Counter

        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]

    def _extract_entities(self, text: str) -> list[str]:
        """Extract named entities (simplified implementation)"""
        # This is a placeholder - in production you'd use spaCy or similar
        entities = []

        # Simple email detection
        import re

        emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        entities.extend(emails)

        # Simple phone number detection
        phones = re.findall(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", text)
        entities.extend(phones)

        # Simple URL detection
        urls = re.findall(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            text,
        )
        entities.extend(urls)

        return list(set(entities))

    async def process_batch(
        self, items: list[dict[str, Any]], item_type: str
    ) -> list[ContentChunk]:
        """Process a batch of items (calls, emails, etc.) and return all chunks"""
        all_chunks = []

        for item in items:
            try:
                if item_type == "call":
                    transcript_segments = item.get("transcript_segments", [])
                    chunks = await self.chunk_call_transcript(item, transcript_segments)
                elif item_type == "email":
                    chunks = await self.chunk_email(item)
                else:
                    logger.warning(f"Unknown item type: {item_type}")
                    continue

                # Update total_chunks for all chunks
                for chunk in chunks:
                    chunk.metadata.total_chunks = len(chunks)

                all_chunks.extend(chunks)

            except Exception as e:
                logger.error(f"Failed to chunk {item_type} {item.get('id', 'unknown')}: {e}")
                continue

        logger.info(f"Generated {len(all_chunks)} chunks from {len(items)} {item_type}s")
        return all_chunks


# Factory function for easy initialization
def create_chunking_service(
    openai_api_key: str = None,
    max_chunk_tokens: int = 512,
    overlap_tokens: int = 50,
    embedding_model: str = "text-embedding-3-small",
) -> IntelligentChunker:
    """Create a fully configured chunking service"""

    embedding_service = OpenAIEmbeddingService(api_key=openai_api_key, model=embedding_model)

    return IntelligentChunker(
        embedding_service=embedding_service,
        max_chunk_tokens=max_chunk_tokens,
        overlap_tokens=overlap_tokens,
    )


# Example usage and testing
async def main():
    """Example usage of the chunking service"""

    # Create service (will use OPENAI_API_KEY from environment)
    chunker = create_chunking_service()

    # Example call data
    sample_call = {
        "id": "test-call-123",
        "title": "Product Demo Call",
        "summary": "Discussed product features and pricing with potential customer",
        "transcript_segments": [
            {
                "speaker_id": "speaker_1",
                "speaker_name": "John Sales",
                "speaker_role": "host",
                "content": "Welcome to our product demo today. I'm excited to show you our new features.",
                "start_time": 0.0,
                "end_time": 5.0,
                "confidence": 0.95,
            },
            {
                "speaker_id": "speaker_2",
                "speaker_name": "Jane Customer",
                "speaker_role": "participant",
                "content": "Thank you, we're very interested in learning more about your platform.",
                "start_time": 5.0,
                "end_time": 10.0,
                "confidence": 0.92,
            },
        ],
    }

    # Example email data
    sample_email = {
        "id": "test-email-456",
        "subject": "Follow-up on Product Demo",
        "body_plain": "Hi Jane, Thank you for taking the time to join our product demo today. Based on our conversation, I believe our platform would be a great fit for your needs. I've attached the pricing information we discussed. Please let me know if you have any questions or would like to schedule a follow-up call to discuss implementation details.",
        "from_email": "john@company.com",
        "to_emails": ["jane@customer.com"],
        "email_type": "outbound",
    }

    # Process call
    logger.info("Processing call transcript...")
    call_chunks = await chunker.process_batch([sample_call], "call")

    for chunk in call_chunks:
        logger.info(
            f"Call chunk: {chunk.metadata.chunk_type} - {len(chunk.content)} chars - {chunk.metadata.token_count} tokens"
        )

    # Process email
    logger.info("Processing email...")
    email_chunks = await chunker.process_batch([sample_email], "email")

    for chunk in email_chunks:
        logger.info(
            f"Email chunk: {chunk.metadata.chunk_type} - {len(chunk.content)} chars - {chunk.metadata.token_count} tokens"
        )

    logger.info(f"Total chunks generated: {len(call_chunks) + len(email_chunks)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
