"""
Lightweight RAG Service for Gong Data with Proper Citations
Provides semantic search and retrieval with source attribution for calls, transcripts, and emails
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from app.integrations.gong_pipeline.chunking_service import OpenAIEmbeddingService
from app.memory.unified_memory_router import get_memory_router, MemoryDomain
logger = logging.getLogger(__name__)
class SearchType(str, Enum):
    """Types of search operations"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    TEMPORAL = "temporal"
    SPEAKER = "speaker"
    EMAIL_THREAD = "email_thread"
class ContentSource(str, Enum):
    """Content sources for citations"""
    CALL_TRANSCRIPT = "call_transcript"
    CALL_SUMMARY = "call_summary"
    EMAIL = "email"
    MEETING_NOTES = "meeting_notes"
@dataclass
class CitationSource:
    """Source information for citations"""
    source_id: str  # call_id, email_id, etc.
    source_type: ContentSource
    title: str
    url: Optional[str] = None
    date: Optional[datetime] = None
    # Specific source details
    speaker_name: Optional[str] = None
    speaker_role: Optional[str] = None
    email_from: Optional[str] = None
    email_to: list[str] = None
    # Content location
    chunk_index: Optional[int] = None
    start_time: Optional[float] = None  # For calls
    end_time: Optional[float] = None
    def __post_init__(self):
        if self.email_to is None:
            self.email_to = []
@dataclass
class SearchResult:
    """Enhanced search result with citation information"""
    content: str
    relevance_score: float
    citation: CitationSource
    metadata: dict[str, Any]
    # Context information
    surrounding_context: Optional[str] = None
    related_chunks: list[str] = None
    def __post_init__(self):
        if self.related_chunks is None:
            self.related_chunks = []
@dataclass
class RAGResponse:
    """Complete RAG response with generated answer and citations"""
    query: str
    answer: str
    sources: list[SearchResult]
    confidence_score: float
    search_metadata: dict[str, Any]
    generated_at: datetime
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()
class GongRAGService:
    """RAG service for Gong data with comprehensive search and citation"""
    def __init__(
        self,
        embedding_service: OpenAIEmbeddingService,
        max_results: int = 10,
        min_relevance_score: float = 0.7,
    ):
        # Use unified memory router for retrieval
        self.memory = get_memory_router()
        self.embedding_service = embedding_service
        self.max_results = max_results
        self.min_relevance_score = min_relevance_score
        # Collection names for different data types
        self.collections = {
            "calls": "GongCall",
            "transcripts": "GongTranscriptChunk",
            "emails": "GongEmail",
        }
    async def semantic_search(
        self,
        query: str,
        collections: list[str] = None,
        filters: dict[str, Any] = None,
        date_range: tuple[datetime, datetime] = None,
    ) -> list[SearchResult]:
        """Perform semantic search across Gong data"""
        if collections is None:
            collections = list(self.collections.keys())
        # Use unified memory: hybrid search by text in SOPHIA domain
        all_results = []
        try:
            hits = await self.memory.search(
                query=query, domain=MemoryDomain.SOPHIA, k=self.max_results
            )
            for hit in hits:
                # Basic thresholding
                if hit.score < self.min_relevance_score:
                    continue
                meta = hit.metadata or {}
                # Build citation as best-effort from metadata
                citation = CitationSource(
                    source_id=str(meta.get("source_id") or meta.get("file_path") or hit.source_uri),
                    source_type=ContentSource.CALL_TRANSCRIPT
                    if "call" in hit.source_uri.lower()
                    else ContentSource.MEETING_NOTES,
                    title=str(meta.get("title") or meta.get("file_path") or "Gong Document"),
                    url=meta.get("url"),
                    date=None,
                )
                all_results.append(
                    SearchResult(
                        content=hit.content,
                        relevance_score=float(hit.score),
                        citation=citation,
                        metadata=meta,
                    )
                )
        except Exception as e:
            logger.error(f"Unified memory search failed: {e}")
        # Sort by relevance score
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        # Add surrounding context
        await self._add_surrounding_context(all_results)
        return all_results[: self.max_results]
    async def hybrid_search(
        self,
        query: str,
        collections: list[str] = None,
        filters: dict[str, Any] = None,
        date_range: tuple[datetime, datetime] = None,
        semantic_weight: float = 0.7,
    ) -> list[SearchResult]:
        """Perform hybrid search combining semantic and keyword search"""
        # Get semantic results
        semantic_results = await self.semantic_search(
            query, collections, filters, date_range
        )
        # Get keyword results
        keyword_results = await self.keyword_search(
            query, collections, filters, date_range
        )
        # Combine and re-rank results
        combined_results = self._combine_search_results(
            semantic_results, keyword_results, semantic_weight
        )
        return combined_results[: self.max_results]
    async def keyword_search(
        self,
        query: str,
        collections: list[str] = None,
        filters: dict[str, Any] = None,
        date_range: tuple[datetime, datetime] = None,
    ) -> list[SearchResult]:
        """Perform keyword-based search"""
        if collections is None:
            collections = list(self.collections.keys())
        all_results = []
        # Search each collection
        for collection_key in collections:
            collection_name = self.collections.get(collection_key)
            if not collection_name:
                continue
            try:
                # Build filters
                where_filter = self._build_where_filter(filters, date_range)
                # Perform text search
                text_results = await self.weaviate.search(
                    collection=collection_name,
                    query=query,
                    limit=self.max_results,
                    where_filter=where_filter,
                )
                # Convert to SearchResult objects
                for result in text_results:
                    search_result = self._convert_to_search_result(
                        result, collection_key
                    )
                    if (
                        search_result
                        and search_result.relevance_score >= self.min_relevance_score
                    ):
                        all_results.append(search_result)
            except Exception as e:
                logger.error(f"Error searching collection {collection_name}: {e}")
                continue
        # Sort by relevance score
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return all_results[: self.max_results]
    async def search_by_speaker(
        self,
        speaker_name: str,
        query: Optional[str] = None,
        date_range: tuple[datetime, datetime] = None,
    ) -> list[SearchResult]:
        """Search for content by specific speaker"""
        filters = {"speaker_name": speaker_name}
        if query:
            return await self.hybrid_search(
                query=query,
                collections=["transcripts"],
                filters=filters,
                date_range=date_range,
            )
        else:
            # Return all content from this speaker
            return await self.keyword_search(
                query="*",  # Match all
                collections=["transcripts"],
                filters=filters,
                date_range=date_range,
            )
    async def search_email_thread(
        self, thread_id: str, query: Optional[str] = None
    ) -> list[SearchResult]:
        """Search within a specific email thread"""
        filters = {"thread_id": thread_id}
        if query:
            return await self.hybrid_search(
                query=query, collections=["emails"], filters=filters
            )
        else:
            # Return all emails in thread
            return await self.keyword_search(
                query="*", collections=["emails"], filters=filters
            )
    async def temporal_search(
        self,
        query: str,
        start_date: datetime,
        end_date: datetime,
        collections: list[str] = None,
    ) -> list[SearchResult]:
        """Search within a specific time range"""
        return await self.hybrid_search(
            query=query, collections=collections, date_range=(start_date, end_date)
        )
    async def find_related_content(
        self, content_id: str, content_type: str, similarity_threshold: float = 0.8
    ) -> list[SearchResult]:
        """Find content related to a specific piece of content"""
        # Get the original content
        original_content = await self._get_content_by_id(content_id, content_type)
        if not original_content:
            return []
        # Use the content itself as the search query
        query = original_content.get("content", "") or original_content.get(
            "summary", ""
        )
        # Perform semantic search
        results = await self.semantic_search(
            query, min_relevance_score=similarity_threshold
        )
        # Filter out the original content
        filtered_results = [r for r in results if r.citation.source_id != content_id]
        return filtered_results
    def _build_where_filter(
        self,
        filters: dict[str, Any] = None,
        date_range: tuple[datetime, datetime] = None,
    ) -> dict[str, Any]:
        """Build Weaviate where filter from parameters"""
        where_conditions = []
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    # Array contains any of these values
                    where_conditions.append(
                        {
                            "path": [field],
                            "operator": "ContainsAny",
                            "valueTextArray": value,
                        }
                    )
                else:
                    # Exact match
                    where_conditions.append(
                        {"path": [field], "operator": "Equal", "valueText": str(value)}
                    )
        if date_range:
            start_date, end_date = date_range
            where_conditions.append(
                {
                    "operator": "And",
                    "operands": [
                        {
                            "path": ["createdAt"],
                            "operator": "GreaterThanEqual",
                            "valueDate": start_date.isoformat(),
                        },
                        {
                            "path": ["createdAt"],
                            "operator": "LessThanEqual",
                            "valueDate": end_date.isoformat(),
                        },
                    ],
                }
            )
        if len(where_conditions) == 1:
            return where_conditions[0]
        elif len(where_conditions) > 1:
            return {"operator": "And", "operands": where_conditions}
        return {}
    def _convert_to_search_result(
        self, vector_result: Any, collection_key: str
    ) -> Optional[SearchResult]:
        """Convert vector result to SearchResult with proper citation"""
        try:
            metadata = vector_result.metadata
            # Create citation based on collection type
            if collection_key == "calls":
                citation = CitationSource(
                    source_id=metadata.get("callId", ""),
                    source_type=ContentSource.CALL_SUMMARY,
                    title=metadata.get("title", "Untitled Call"),
                    url=metadata.get("callUrl"),
                    date=datetime.fromisoformat(
                        metadata.get("actualStart", datetime.now().isoformat())
                    ),
                    speaker_name=metadata.get("primarySpeaker"),
                    start_time=metadata.get("durationSeconds", 0),
                )
            elif collection_key == "transcripts":
                citation = CitationSource(
                    source_id=metadata.get("callId", ""),
                    source_type=ContentSource.CALL_TRANSCRIPT,
                    title=metadata.get("callTitle", "Call Transcript"),
                    url=None,  # Could construct call URL if needed
                    date=datetime.fromisoformat(
                        metadata.get("callDate", datetime.now().isoformat())
                    ),
                    speaker_name=metadata.get("speakerName"),
                    speaker_role=metadata.get("speakerRole"),
                    chunk_index=metadata.get("chunkIndex"),
                    start_time=metadata.get("startTime"),
                    end_time=metadata.get("endTime"),
                )
            elif collection_key == "emails":
                citation = CitationSource(
                    source_id=metadata.get("emailId", ""),
                    source_type=ContentSource.EMAIL,
                    title=metadata.get("subject", "Email"),
                    url=None,
                    date=datetime.fromisoformat(
                        metadata.get("sentAt", datetime.now().isoformat())
                    ),
                    email_from=metadata.get("fromEmail"),
                    email_to=metadata.get("toEmails", []),
                )
            else:
                logger.warning(f"Unknown collection key: {collection_key}")
                return None
            return SearchResult(
                content=vector_result.content,
                relevance_score=vector_result.score,
                citation=citation,
                metadata=metadata,
                surrounding_context=None,  # Will be populated later if needed
                related_chunks=[],
            )
        except Exception as e:
            logger.error(f"Error converting search result: {e}")
            return None
    def _combine_search_results(
        self,
        semantic_results: list[SearchResult],
        keyword_results: list[SearchResult],
        semantic_weight: float,
    ) -> list[SearchResult]:
        """Combine and re-rank semantic and keyword search results"""
        # Create a map of results by source_id to avoid duplicates
        result_map = {}
        # Add semantic results with weighted scores
        for result in semantic_results:
            key = f"{result.citation.source_id}_{result.citation.chunk_index}"
            if key not in result_map:
                result.relevance_score = result.relevance_score * semantic_weight
                result_map[key] = result
        # Add keyword results with weighted scores
        keyword_weight = 1.0 - semantic_weight
        for result in keyword_results:
            key = f"{result.citation.source_id}_{result.citation.chunk_index}"
            if key in result_map:
                # Combine scores
                existing_result = result_map[key]
                combined_score = existing_result.relevance_score + (
                    result.relevance_score * keyword_weight
                )
                existing_result.relevance_score = min(combined_score, 1.0)
            else:
                result.relevance_score = result.relevance_score * keyword_weight
                result_map[key] = result
        # Sort by combined relevance score
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return combined_results
    async def _add_surrounding_context(self, results: list[SearchResult]):
        """Add surrounding context to search results"""
        for result in results:
            try:
                # For transcript chunks, try to get adjacent chunks
                if result.citation.source_type == ContentSource.CALL_TRANSCRIPT:
                    context = await self._get_surrounding_transcript_context(result)
                    result.surrounding_context = context
                # For emails, context might be thread context
                elif result.citation.source_type == ContentSource.EMAIL:
                    context = await self._get_email_thread_context(result)
                    result.surrounding_context = context
            except Exception as e:
                logger.error(f"Error adding context to result: {e}")
                continue
    async def _get_surrounding_transcript_context(
        self, result: SearchResult
    ) -> Optional[str]:
        """Get surrounding context for transcript chunks"""
        try:
            call_id = result.citation.source_id
            current_chunk_index = result.citation.chunk_index
            if current_chunk_index is None:
                return None
            # Get adjacent chunks
            context_chunks = []
            # Get previous chunk
            if current_chunk_index > 0:
                prev_chunk = await self._get_transcript_chunk(
                    call_id, current_chunk_index - 1
                )
                if prev_chunk:
                    context_chunks.append(f"[Previous] {prev_chunk}")
            # Add current chunk
            context_chunks.append(f"[Current] {result.content}")
            # Get next chunk
            next_chunk = await self._get_transcript_chunk(
                call_id, current_chunk_index + 1
            )
            if next_chunk:
                context_chunks.append(f"[Next] {next_chunk}")
            return "\n\n".join(context_chunks)
        except Exception as e:
            logger.error(f"Error getting transcript context: {e}")
            return None
    async def _get_transcript_chunk(
        self, call_id: str, chunk_index: int
    ) -> Optional[str]:
        """Get a specific transcript chunk"""
        try:
            filters = {"callId": call_id, "chunkIndex": chunk_index}
            results = await self.weaviate.search(
                collection=self.collections["transcripts"],
                query="*",
                limit=1,
                where_filter=self._build_where_filter(filters),
            )
            if results:
                return results[0].content
        except Exception as e:
            logger.error(f"Error getting transcript chunk: {e}")
        return None
    async def _get_email_thread_context(self, result: SearchResult) -> Optional[str]:
        """Get email thread context"""
        # This would fetch related emails in the thread
        # For now, return None as it requires more complex logic
        return None
    async def _get_content_by_id(
        self, content_id: str, content_type: str
    ) -> Optional[dict[str, Any]]:
        """Get content by ID and type"""
        collection_name = self.collections.get(content_type)
        if not collection_name:
            return None
        try:
            # This would need to be implemented based on Weaviate client capabilities
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"Error getting content by ID: {e}")
            return None
    def format_citations(self, results: list[SearchResult]) -> str:
        """Format citations for display"""
        citations = []
        for i, result in enumerate(results, 1):
            citation = result.citation
            if citation.source_type == ContentSource.CALL_TRANSCRIPT:
                cite_text = f"[{i}] {citation.title}"
                if citation.speaker_name:
                    cite_text += f" - {citation.speaker_name}"
                if citation.start_time is not None:
                    cite_text += f" ({citation.start_time:.1f}s)"
                if citation.date:
                    cite_text += f" ({citation.date.strftime('%Y-%m-%d')})"
            elif citation.source_type == ContentSource.EMAIL:
                cite_text = f"[{i}] Email: {citation.title}"
                if citation.email_from:
                    cite_text += f" from {citation.email_from}"
                if citation.date:
                    cite_text += f" ({citation.date.strftime('%Y-%m-%d')})"
            elif citation.source_type == ContentSource.CALL_SUMMARY:
                cite_text = f"[{i}] Call: {citation.title}"
                if citation.date:
                    cite_text += f" ({citation.date.strftime('%Y-%m-%d')})"
            else:
                cite_text = f"[{i}] {citation.title}"
                if citation.date:
                    cite_text += f" ({citation.date.strftime('%Y-%m-%d')})"
            citations.append(cite_text)
        return "\n".join(citations)
# Factory function
async def create_gong_rag_service(
    weaviate_endpoint: str,
    weaviate_api_key: str = None,
    openai_api_key: str = None,
    max_results: int = 10,
    min_relevance_score: float = 0.7,
) -> GongRAGService:
    """Create a fully configured Gong RAG service"""
    # Create Weaviate client
    weaviate_client = WeaviateClient(url=weaviate_endpoint, api_key=weaviate_api_key)
    await weaviate_client.connect()
    # Create embedding service
    embedding_service = OpenAIEmbeddingService(api_key=openai_api_key)
    # Create RAG service
    return GongRAGService(
        weaviate_client=weaviate_client,
        embedding_service=embedding_service,
        max_results=max_results,
        min_relevance_score=min_relevance_score,
    )
# Example usage and testing
async def main():
    """Example usage of the RAG service"""
    try:
        # Create RAG service
        rag_service = await create_gong_rag_service(
            weaviate_endpoint="https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud",
            weaviate_api_key="VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf",
        )
        # Example searches
        logger.info("Testing semantic search...")
        results = await rag_service.semantic_search(
            query="pricing and contract discussions",
            collections=["transcripts", "emails"],
        )
        logger.info(f"Found {len(results)} results for pricing query")
        for result in results[:3]:
            logger.info(
                f"- {result.citation.title} (score: {result.relevance_score:.2f})"
            )
        # Test speaker search
        logger.info("Testing speaker search...")
        speaker_results = await rag_service.search_by_speaker(
            speaker_name="John Sales", query="product features"
        )
        logger.info(f"Found {len(speaker_results)} results from John Sales")
        # Format citations
        if results:
            citations = rag_service.format_citations(results[:5])
            logger.info(f"Formatted citations:\n{citations}")
    except Exception as e:
        logger.error(f"RAG service test failed: {e}")
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
