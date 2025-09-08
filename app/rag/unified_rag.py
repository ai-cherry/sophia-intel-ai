"""
Unified RAG (Retrieval-Augmented Generation) System
Consolidated retrieval-augmented generation with cross-store semantic search,
context synthesis, and integration with dual orchestrators (Artemis/Sophia)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.core.unified_memory import (
    MemoryContext,
    MemoryPriority,
    unified_memory,
)
from app.memory.unified.execution_store import ExecutionType, execution_store
from app.memory.unified.intelligence_store import IntelligenceType, intelligence_store
from app.memory.unified.knowledge_store import KnowledgeType, knowledge_store
from app.memory.unified.pattern_store import PatternType, pattern_store
from app.memory.unified.vector_store import VectorOperation, vector_store

logger = logging.getLogger(__name__)


class RAGStrategy(Enum):
    """RAG retrieval strategies"""

    SEMANTIC_ONLY = "semantic_only"  # Vector similarity only
    KEYWORD_ONLY = "keyword_only"  # Text matching only
    HYBRID = "hybrid"  # Combine semantic and keyword
    ADAPTIVE = "adaptive"  # AI-driven strategy selection
    SPECIALIZED = "specialized"  # Domain-specific optimization


class ContextSynthesisMode(Enum):
    """Context synthesis approaches"""

    CONCATENATION = "concatenation"  # Simple text concatenation
    SUMMARIZATION = "summarization"  # Extract key points
    STRUCTURED = "structured"  # Organize by type/relevance
    NARRATIVE = "narrative"  # Create coherent narrative
    ANALYTICAL = "analytical"  # Focus on insights/patterns


class RAGDomain(Enum):
    """RAG domain specializations"""

    ARTEMIS = "artemis"  # Technical intelligence domain
    SOPHIA = "sophia"  # Business intelligence domain
    SHARED = "shared"  # Cross-domain knowledge
    SPECIALIZED = "specialized"  # Domain-specific optimization


@dataclass
class RAGContext:
    """Comprehensive context for RAG operations"""

    query: str
    domain: RAGDomain
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Retrieval parameters
    max_results: int = 10
    similarity_threshold: float = 0.7
    include_contexts: set[MemoryContext] = field(
        default_factory=lambda: {
            MemoryContext.INTELLIGENCE,
            MemoryContext.KNOWLEDGE,
            MemoryContext.EXECUTION,
        }
    )

    # Strategy configuration
    strategy: RAGStrategy = RAGStrategy.ADAPTIVE
    synthesis_mode: ContextSynthesisMode = ContextSynthesisMode.STRUCTURED

    # Filtering
    time_range: Optional[tuple[datetime, datetime]] = None
    priority_threshold: MemoryPriority = MemoryPriority.LOW
    confidence_threshold: float = 0.0

    # Advanced options
    enable_cross_references: bool = True
    include_reasoning: bool = True
    personalize: bool = True


@dataclass
class RAGSource:
    """Source information for retrieved context"""

    memory_id: str
    source_type: str  # "intelligence", "knowledge", "execution", etc.
    title: str
    content: str
    relevance_score: float
    confidence: float
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGResult:
    """Comprehensive RAG result with synthesized context"""

    query: str
    domain: RAGDomain

    # Retrieved sources
    sources: list[RAGSource]
    total_sources_found: int

    # Synthesized context
    synthesized_context: str
    context_structure: dict[str, Any]

    # Insights and analysis
    key_insights: list[str] = field(default_factory=list)
    cross_references: list[dict[str, str]] = field(default_factory=list)
    reasoning_chain: list[str] = field(default_factory=list)

    # Metadata
    strategy_used: RAGStrategy = RAGStrategy.ADAPTIVE
    synthesis_mode: ContextSynthesisMode = ContextSynthesisMode.STRUCTURED
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class UnifiedRAGSystem:
    """
    Unified RAG System for intelligent context retrieval and synthesis
    Integrates across all memory stores with domain-aware optimization
    """

    def __init__(self):
        self.memory_interface = unified_memory
        self.intelligence_store = intelligence_store
        self.execution_store = execution_store
        self.pattern_store = pattern_store
        self.knowledge_store = knowledge_store
        self.vector_store = vector_store

        # RAG configuration by domain
        self.domain_configs = {
            RAGDomain.ARTEMIS: {
                "preferred_contexts": [MemoryContext.EXECUTION, MemoryContext.INTELLIGENCE],
                "weight_technical": 1.2,
                "weight_business": 0.8,
                "synthesis_style": "technical_analytical",
            },
            RAGDomain.SOPHIA: {
                "preferred_contexts": [MemoryContext.INTELLIGENCE, MemoryContext.PATTERN],
                "weight_business": 1.2,
                "weight_technical": 0.8,
                "synthesis_style": "business_strategic",
            },
            RAGDomain.SHARED: {
                "preferred_contexts": list(MemoryContext),
                "weight_technical": 1.0,
                "weight_business": 1.0,
                "synthesis_style": "balanced",
            },
        }

        # Performance metrics
        self.metrics = {
            "total_queries": 0,
            "avg_retrieval_time_ms": 0.0,
            "avg_sources_per_query": 0.0,
            "cache_hit_rate": 0.0,
            "by_domain": {domain.value: 0 for domain in RAGDomain},
            "by_strategy": {strategy.value: 0 for strategy in RAGStrategy},
        }

    async def retrieve_and_synthesize(self, context: RAGContext) -> RAGResult:
        """Main RAG pipeline: retrieve, rank, and synthesize context"""

        start_time = time.time()

        try:
            # Step 1: Determine optimal retrieval strategy
            strategy = await self._determine_strategy(context)
            context.strategy = strategy

            # Step 2: Multi-store retrieval with domain optimization
            sources = await self._retrieve_from_all_stores(context)

            # Step 3: Cross-store ranking and deduplication
            ranked_sources = await self._rank_and_deduplicate_sources(sources, context)

            # Step 4: Context synthesis
            synthesized_context, structure = await self._synthesize_context(ranked_sources, context)

            # Step 5: Generate insights and cross-references
            insights = await self._extract_insights(ranked_sources, context)
            cross_refs = await self._find_cross_references(ranked_sources, context)
            reasoning = await self._build_reasoning_chain(ranked_sources, context)

            # Create comprehensive result
            result = RAGResult(
                query=context.query,
                domain=context.domain,
                sources=ranked_sources[: context.max_results],
                total_sources_found=len(sources),
                synthesized_context=synthesized_context,
                context_structure=structure,
                key_insights=insights,
                cross_references=cross_refs,
                reasoning_chain=reasoning,
                strategy_used=strategy,
                synthesis_mode=context.synthesis_mode,
                processing_time_ms=(time.time() - start_time) * 1000,
            )

            # Update metrics
            await self._update_metrics(result, context)

            logger.debug(
                f"RAG query completed: {len(ranked_sources)} sources in {result.processing_time_ms:.2f}ms"
            )
            return result

        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}")
            return RAGResult(
                query=context.query,
                domain=context.domain,
                sources=[],
                total_sources_found=0,
                synthesized_context=f"Error retrieving context: {str(e)}",
                context_structure={"error": str(e)},
                processing_time_ms=(time.time() - start_time) * 1000,
            )

    async def query_intelligence(
        self,
        query: str,
        domain: RAGDomain = RAGDomain.SHARED,
        intelligence_types: Optional[list[IntelligenceType]] = None,
    ) -> RAGResult:
        """Query specifically for intelligence insights"""

        context = RAGContext(
            query=query,
            domain=domain,
            include_contexts={MemoryContext.INTELLIGENCE},
            max_results=8,
            synthesis_mode=ContextSynthesisMode.ANALYTICAL,
        )

        # Add intelligence type filtering
        if intelligence_types:
            context.metadata = {"intelligence_types": intelligence_types}

        return await self.retrieve_and_synthesize(context)

    async def query_execution_history(
        self,
        query: str,
        domain: RAGDomain = RAGDomain.ARTEMIS,
        execution_types: Optional[list[ExecutionType]] = None,
    ) -> RAGResult:
        """Query execution history and context"""

        context = RAGContext(
            query=query,
            domain=domain,
            include_contexts={MemoryContext.EXECUTION},
            max_results=15,
            synthesis_mode=ContextSynthesisMode.NARRATIVE,
        )

        if execution_types:
            context.metadata = {"execution_types": execution_types}

        return await self.retrieve_and_synthesize(context)

    async def query_patterns(
        self,
        query: str,
        domain: RAGDomain = RAGDomain.SHARED,
        pattern_types: Optional[list[PatternType]] = None,
    ) -> RAGResult:
        """Query behavioral patterns and trends"""

        context = RAGContext(
            query=query,
            domain=domain,
            include_contexts={MemoryContext.PATTERN},
            max_results=12,
            synthesis_mode=ContextSynthesisMode.ANALYTICAL,
        )

        if pattern_types:
            context.metadata = {"pattern_types": pattern_types}

        return await self.retrieve_and_synthesize(context)

    async def query_knowledge_base(
        self,
        query: str,
        domain: RAGDomain = RAGDomain.SHARED,
        knowledge_types: Optional[list[KnowledgeType]] = None,
    ) -> RAGResult:
        """Query structured knowledge and facts"""

        context = RAGContext(
            query=query,
            domain=domain,
            include_contexts={MemoryContext.KNOWLEDGE},
            max_results=10,
            synthesis_mode=ContextSynthesisMode.STRUCTURED,
        )

        if knowledge_types:
            context.metadata = {"knowledge_types": knowledge_types}

        return await self.retrieve_and_synthesize(context)

    async def get_conversation_context(
        self,
        user_id: str,
        session_id: str,
        query: str,
        domain: RAGDomain = RAGDomain.SHARED,
        lookback_hours: int = 24,
    ) -> RAGResult:
        """Get personalized conversation context"""

        # Set time range for recent context
        end_time = datetime.now(timezone.utc)
        start_time = end_time.replace(hour=end_time.hour - lookback_hours)

        context = RAGContext(
            query=query,
            domain=domain,
            user_id=user_id,
            session_id=session_id,
            time_range=(start_time, end_time),
            personalize=True,
            synthesis_mode=ContextSynthesisMode.NARRATIVE,
            max_results=8,
        )

        return await self.retrieve_and_synthesize(context)

    async def get_rag_analytics(self) -> dict[str, Any]:
        """Get RAG system analytics and performance metrics"""

        analytics = {
            "performance_metrics": self.metrics.copy(),
            "store_health": {},
            "query_patterns": await self._analyze_query_patterns(),
            "retrieval_effectiveness": await self._calculate_retrieval_effectiveness(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Get health status of each store
        analytics["store_health"][
            "unified_memory"
        ] = await self.memory_interface.get_health_status()

        return analytics

    # Private methods for RAG pipeline implementation

    async def _determine_strategy(self, context: RAGContext) -> RAGStrategy:
        """Determine optimal retrieval strategy based on context"""

        if context.strategy != RAGStrategy.ADAPTIVE:
            return context.strategy

        # Analyze query characteristics
        query_length = len(context.query.split())
        has_technical_terms = any(
            term in context.query.lower()
            for term in ["api", "code", "function", "database", "server", "algorithm", "system"]
        )
        has_business_terms = any(
            term in context.query.lower()
            for term in ["revenue", "cost", "customer", "market", "strategy", "business", "roi"]
        )

        # Strategy selection logic
        if query_length < 3:
            return RAGStrategy.KEYWORD_ONLY
        elif query_length > 15:
            return RAGStrategy.SEMANTIC_ONLY
        elif (
            has_technical_terms
            and context.domain == RAGDomain.ARTEMIS
            or has_business_terms
            and context.domain == RAGDomain.SOPHIA
        ):
            return RAGStrategy.SPECIALIZED
        else:
            return RAGStrategy.HYBRID

    async def _retrieve_from_all_stores(self, context: RAGContext) -> list[RAGSource]:
        """Retrieve context from all applicable memory stores"""

        all_sources = []

        # Parallel retrieval from all stores
        retrieval_tasks = []

        for memory_context in context.include_contexts:
            if memory_context == MemoryContext.INTELLIGENCE:
                retrieval_tasks.append(self._retrieve_from_intelligence_store(context))
            elif memory_context == MemoryContext.EXECUTION:
                retrieval_tasks.append(self._retrieve_from_execution_store(context))
            elif memory_context == MemoryContext.PATTERN:
                retrieval_tasks.append(self._retrieve_from_pattern_store(context))
            elif memory_context == MemoryContext.KNOWLEDGE:
                retrieval_tasks.append(self._retrieve_from_knowledge_store(context))

        # Always include vector search for semantic retrieval
        retrieval_tasks.append(self._retrieve_from_vector_store(context))

        # Execute all retrievals in parallel
        store_results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)

        # Aggregate results
        for results in store_results:
            if isinstance(results, Exception):
                logger.warning(f"Store retrieval failed: {results}")
                continue
            if isinstance(results, list):
                all_sources.extend(results)

        return all_sources

    async def _retrieve_from_intelligence_store(self, context: RAGContext) -> list[RAGSource]:
        """Retrieve from intelligence store"""

        try:
            intelligence_types = (
                context.metadata.get("intelligence_types") if hasattr(context, "metadata") else None
            )

            results = await self.intelligence_store.search_insights(
                query=context.query,
                intelligence_types=intelligence_types,
                max_results=context.max_results,
                domain=context.domain.value if context.domain != RAGDomain.SHARED else None,
            )

            sources = []
            for result in results:
                structured = result.get("structured_insight", {})
                sources.append(
                    RAGSource(
                        memory_id=result["memory_id"],
                        source_type="intelligence",
                        title=structured.get("title", "Intelligence Insight"),
                        content=result["content"],
                        relevance_score=result["relevance_score"],
                        confidence=structured.get("confidence_value", 0.8),
                        created_at=datetime.fromisoformat(
                            structured.get("created_at", datetime.now(timezone.utc).isoformat())
                        ),
                        metadata=structured,
                    )
                )

            return sources

        except Exception as e:
            logger.error(f"Intelligence store retrieval failed: {e}")
            return []

    async def _retrieve_from_execution_store(self, context: RAGContext) -> list[RAGSource]:
        """Retrieve from execution store"""

        try:
            execution_types = (
                context.metadata.get("execution_types") if hasattr(context, "metadata") else None
            )

            results = await self.execution_store.search_executions(
                query=context.query,
                execution_types=execution_types,
                max_results=context.max_results,
                domain=context.domain.value if context.domain != RAGDomain.SHARED else None,
            )

            sources = []
            for result in results:
                exec_context = result.get("execution_context", {})
                sources.append(
                    RAGSource(
                        memory_id=result["memory_id"],
                        source_type="execution",
                        title=exec_context.get("task_name", "Execution Record"),
                        content=result["content"],
                        relevance_score=result["relevance_score"],
                        confidence=0.9,  # Execution records are typically highly reliable
                        created_at=datetime.fromisoformat(
                            exec_context.get("start_time", datetime.now(timezone.utc).isoformat())
                        ),
                        metadata=exec_context,
                    )
                )

            return sources

        except Exception as e:
            logger.error(f"Execution store retrieval failed: {e}")
            return []

    async def _retrieve_from_pattern_store(self, context: RAGContext) -> list[RAGSource]:
        """Retrieve from pattern store"""

        try:
            pattern_types = (
                context.metadata.get("pattern_types") if hasattr(context, "metadata") else None
            )

            results = await self.pattern_store.search_patterns(
                query=context.query,
                pattern_types=pattern_types,
                max_results=context.max_results,
                domain=context.domain.value if context.domain != RAGDomain.SHARED else None,
            )

            sources = []
            for result in results:
                pattern_data = result.get("pattern_data", {})
                sources.append(
                    RAGSource(
                        memory_id=result["memory_id"],
                        source_type="pattern",
                        title=pattern_data.get("name", "Behavioral Pattern"),
                        content=result["content"],
                        relevance_score=result["relevance_score"],
                        confidence=pattern_data.get("strength_value", 0.7),
                        created_at=datetime.now(timezone.utc),  # Patterns are ongoing
                        metadata=pattern_data,
                    )
                )

            return sources

        except Exception as e:
            logger.error(f"Pattern store retrieval failed: {e}")
            return []

    async def _retrieve_from_knowledge_store(self, context: RAGContext) -> list[RAGSource]:
        """Retrieve from knowledge store"""

        try:
            knowledge_types = (
                context.metadata.get("knowledge_types") if hasattr(context, "metadata") else None
            )

            # Search both entities and facts
            entity_results = await self.knowledge_store.search_entities(
                query=context.query,
                max_results=context.max_results // 2,
                domain=context.domain.value if context.domain != RAGDomain.SHARED else None,
            )

            fact_results = await self.knowledge_store.search_facts(
                query=context.query,
                knowledge_types=knowledge_types,
                max_results=context.max_results // 2,
                domain=context.domain.value if context.domain != RAGDomain.SHARED else None,
            )

            sources = []

            # Process entity results
            for result in entity_results:
                entity_data = result.get("entity_data", {})
                sources.append(
                    RAGSource(
                        memory_id=result["memory_id"],
                        source_type="knowledge_entity",
                        title=entity_data.get("name", "Knowledge Entity"),
                        content=result["content"],
                        relevance_score=result["relevance_score"],
                        confidence=entity_data.get("confidence_score", 0.8),
                        created_at=datetime.fromisoformat(
                            entity_data.get("last_updated", datetime.now(timezone.utc).isoformat())
                        ),
                        metadata=entity_data,
                    )
                )

            # Process fact results
            for result in fact_results:
                fact_data = result.get("fact_data", {})
                sources.append(
                    RAGSource(
                        memory_id=result["memory_id"],
                        source_type="knowledge_fact",
                        title=fact_data.get("statement", "Knowledge Fact")[:50] + "...",
                        content=result["content"],
                        relevance_score=result["relevance_score"],
                        confidence=fact_data.get("confidence_score", 0.8),
                        created_at=datetime.fromisoformat(
                            fact_data.get("created_at", datetime.now(timezone.utc).isoformat())
                        ),
                        metadata=fact_data,
                    )
                )

            return sources

        except Exception as e:
            logger.error(f"Knowledge store retrieval failed: {e}")
            return []

    async def _retrieve_from_vector_store(self, context: RAGContext) -> list[RAGSource]:
        """Retrieve using semantic search from vector store"""

        try:
            from app.memory.unified.vector_store import SemanticQuery

            query = SemanticQuery(
                query_text=context.query,
                top_k=context.max_results,
                similarity_threshold=context.similarity_threshold,
                domains={context.domain.value} if context.domain != RAGDomain.SHARED else None,
            )

            results = await self.vector_store.semantic_search(
                query, VectorOperation.SIMILARITY_SEARCH
            )

            sources = []
            for result in results:
                sources.append(
                    RAGSource(
                        memory_id=result.vector_id,
                        source_type="vector_semantic",
                        title=(
                            result.content[:50] + "..."
                            if len(result.content) > 50
                            else result.content
                        ),
                        content=result.content,
                        relevance_score=result.similarity_score,
                        confidence=result.metadata.get("quality_score", 0.8),
                        created_at=datetime.fromisoformat(
                            result.metadata.get(
                                "created_at", datetime.now(timezone.utc).isoformat()
                            )
                        ),
                        metadata=result.metadata,
                    )
                )

            return sources

        except Exception as e:
            logger.error(f"Vector store retrieval failed: {e}")
            return []

    async def _rank_and_deduplicate_sources(
        self, sources: list[RAGSource], context: RAGContext
    ) -> list[RAGSource]:
        """Rank sources by relevance and remove duplicates"""

        # Deduplicate by memory_id and content similarity
        seen_ids = set()
        seen_content_hashes = set()
        unique_sources = []

        for source in sources:
            # Skip if we've seen this memory ID
            if source.memory_id in seen_ids:
                continue

            # Check content similarity (first 100 characters)
            content_hash = hash(source.content[:100])
            if content_hash in seen_content_hashes:
                continue

            seen_ids.add(source.memory_id)
            seen_content_hashes.add(content_hash)
            unique_sources.append(source)

        # Apply domain-specific ranking
        domain_config = self.domain_configs.get(
            context.domain, self.domain_configs[RAGDomain.SHARED]
        )

        def ranking_score(source: RAGSource) -> float:
            score = source.relevance_score

            # Apply confidence weighting
            score *= source.confidence

            # Apply domain-specific weighting
            if (
                source.source_type in ["intelligence", "pattern"]
                and context.domain == RAGDomain.SOPHIA
            ):
                score *= domain_config["weight_business"]
            elif (
                source.source_type in ["execution", "vector_semantic"]
                and context.domain == RAGDomain.ARTEMIS
            ):
                score *= domain_config["weight_technical"]

            # Recency factor
            hours_old = (datetime.now(timezone.utc) - source.created_at).total_seconds() / 3600
            if hours_old < 24:
                score *= 1.1  # Boost recent content
            elif hours_old > 168:  # > 1 week
                score *= 0.9  # Slight penalty for old content

            return score

        # Sort by ranking score
        ranked_sources = sorted(unique_sources, key=ranking_score, reverse=True)

        return ranked_sources

    async def _synthesize_context(
        self, sources: list[RAGSource], context: RAGContext
    ) -> tuple[str, dict[str, Any]]:
        """Synthesize retrieved sources into coherent context"""

        if not sources:
            return "No relevant context found.", {"sources_count": 0}

        synthesis_mode = context.synthesis_mode

        # Build context structure
        structure = {
            "sources_count": len(sources),
            "source_types": {},
            "confidence_range": [1.0, 0.0],
            "time_span": {"earliest": None, "latest": None},
        }

        # Analyze sources for structure
        for source in sources:
            # Count source types
            structure["source_types"][source.source_type] = (
                structure["source_types"].get(source.source_type, 0) + 1
            )

            # Update confidence range
            structure["confidence_range"][0] = min(
                structure["confidence_range"][0], source.confidence
            )
            structure["confidence_range"][1] = max(
                structure["confidence_range"][1], source.confidence
            )

            # Update time span
            if (
                structure["time_span"]["earliest"] is None
                or source.created_at < structure["time_span"]["earliest"]
            ):
                structure["time_span"]["earliest"] = source.created_at.isoformat()
            if (
                structure["time_span"]["latest"] is None
                or source.created_at > structure["time_span"]["latest"]
            ):
                structure["time_span"]["latest"] = source.created_at.isoformat()

        # Generate synthesized context based on mode
        if synthesis_mode == ContextSynthesisMode.CONCATENATION:
            synthesized = self._synthesize_concatenation(sources, context)
        elif synthesis_mode == ContextSynthesisMode.SUMMARIZATION:
            synthesized = await self._synthesize_summary(sources, context)
        elif synthesis_mode == ContextSynthesisMode.STRUCTURED:
            synthesized = self._synthesize_structured(sources, context)
        elif synthesis_mode == ContextSynthesisMode.NARRATIVE:
            synthesized = await self._synthesize_narrative(sources, context)
        else:  # ANALYTICAL
            synthesized = await self._synthesize_analytical(sources, context)

        return synthesized, structure

    def _synthesize_concatenation(self, sources: list[RAGSource], context: RAGContext) -> str:
        """Simple concatenation synthesis"""

        parts = [f"Context for query: {context.query}\n"]

        for i, source in enumerate(sources[: context.max_results], 1):
            confidence_indicator = (
                "🔴" if source.confidence < 0.5 else "🟡" if source.confidence < 0.8 else "🟢"
            )
            parts.append(f"\n{i}. {confidence_indicator} {source.title}")
            parts.append(
                f"   Source: {source.source_type} | Relevance: {source.relevance_score:.2f}"
            )
            parts.append(f"   {source.content[:300]}{'...' if len(source.content) > 300 else ''}")

        return "\n".join(parts)

    def _synthesize_structured(self, sources: list[RAGSource], context: RAGContext) -> str:
        """Structured synthesis organized by source type and relevance"""

        # Group sources by type
        grouped = {}
        for source in sources:
            if source.source_type not in grouped:
                grouped[source.source_type] = []
            grouped[source.source_type].append(source)

        # Sort groups by average relevance
        sorted_groups = sorted(
            grouped.items(),
            key=lambda x: sum(s.relevance_score for s in x[1]) / len(x[1]),
            reverse=True,
        )

        parts = [f"# Structured Context for: {context.query}\n"]

        type_names = {
            "intelligence": "📊 Intelligence Insights",
            "execution": "⚙️ Execution History",
            "pattern": "📈 Behavioral Patterns",
            "knowledge_entity": "🏛️ Knowledge Entities",
            "knowledge_fact": "📋 Factual Knowledge",
            "vector_semantic": "🔍 Semantic Matches",
        }

        for source_type, type_sources in sorted_groups:
            if not type_sources:
                continue

            parts.append(f"\n## {type_names.get(source_type, source_type.title())}")
            parts.append(f"Found {len(type_sources)} relevant items\n")

            for source in type_sources[:3]:  # Top 3 per category
                confidence_stars = "⭐" * int(source.confidence * 5)
                parts.append(f"### {source.title}")
                parts.append(f"**Confidence:** {confidence_stars} ({source.confidence:.2f})")
                parts.append(f"**Relevance:** {source.relevance_score:.2f}")
                parts.append(
                    f"{source.content[:200]}{'...' if len(source.content) > 200 else ''}\n"
                )

        return "\n".join(parts)

    async def _synthesize_summary(self, sources: list[RAGSource], context: RAGContext) -> str:
        """Summarization synthesis extracting key points"""

        # For now, provide a structured summary
        # In production, this would use an LLM for summarization

        parts = [f"Summary of context for: {context.query}\n"]

        # Extract key points from top sources
        key_points = []
        for source in sources[:5]:
            # Simple key point extraction (first sentence)
            first_sentence = (
                source.content.split(".")[0] + "."
                if "." in source.content
                else source.content[:100]
            )
            key_points.append(f"• {first_sentence}")

        parts.append("Key Points:")
        parts.extend(key_points)

        # Add source summary
        parts.append(
            f"\nBased on {len(sources)} sources from {len({s.source_type for s in sources})} different knowledge stores."
        )

        return "\n".join(parts)

    async def _synthesize_narrative(self, sources: list[RAGSource], context: RAGContext) -> str:
        """Narrative synthesis creating a coherent story"""

        # Sort sources chronologically
        chronological_sources = sorted(sources, key=lambda s: s.created_at)

        parts = [f"Narrative context for: {context.query}\n"]

        # Create timeline narrative
        if chronological_sources:
            parts.append("Timeline of relevant information:\n")

            for source in chronological_sources[: context.max_results]:
                time_str = source.created_at.strftime("%Y-%m-%d %H:%M")
                parts.append(f"**{time_str}** - {source.title}")
                parts.append(
                    f"{source.content[:150]}{'...' if len(source.content) > 150 else ''}\n"
                )

        return "\n".join(parts)

    async def _synthesize_analytical(self, sources: list[RAGSource], context: RAGContext) -> str:
        """Analytical synthesis focusing on insights and patterns"""

        parts = [f"Analytical context for: {context.query}\n"]

        # Analyze source composition
        source_analysis = {}
        confidence_levels = []

        for source in sources:
            source_analysis[source.source_type] = source_analysis.get(source.source_type, 0) + 1
            confidence_levels.append(source.confidence)

        # Overall analysis
        parts.append("## Analysis Summary")
        parts.append(f"- Sources analyzed: {len(sources)}")
        parts.append(f"- Average confidence: {sum(confidence_levels)/len(confidence_levels):.2f}")
        parts.append(f"- Source diversity: {len(source_analysis)} different types\n")

        # High-confidence insights
        high_conf_sources = [s for s in sources if s.confidence >= 0.8]
        if high_conf_sources:
            parts.append("## High-Confidence Insights")
            for source in high_conf_sources[:3]:
                parts.append(f"**{source.title}** (Confidence: {source.confidence:.2f})")
                parts.append(
                    f"{source.content[:200]}{'...' if len(source.content) > 200 else ''}\n"
                )

        # Pattern identification
        pattern_sources = [s for s in sources if s.source_type == "pattern"]
        if pattern_sources:
            parts.append("## Identified Patterns")
            for source in pattern_sources[:2]:
                parts.append(f"• {source.title}")

        return "\n".join(parts)

    async def _extract_insights(self, sources: list[RAGSource], context: RAGContext) -> list[str]:
        """Extract key insights from sources"""

        insights = []

        # Insight from high-relevance sources
        for source in sources[:3]:
            if source.relevance_score > 0.8:
                # Extract first meaningful sentence as insight
                sentences = source.content.split(".")
                for sentence in sentences:
                    if len(sentence.strip()) > 20:  # Meaningful length
                        insights.append(sentence.strip())
                        break

        # Domain-specific insights
        if context.domain == RAGDomain.SOPHIA:
            business_sources = [
                s
                for s in sources
                if "business" in s.content.lower() or "revenue" in s.content.lower()
            ]
            if business_sources:
                insights.append(
                    f"Found {len(business_sources)} business-related insights in the context"
                )

        elif context.domain == RAGDomain.ARTEMIS:
            technical_sources = [
                s
                for s in sources
                if "system" in s.content.lower() or "performance" in s.content.lower()
            ]
            if technical_sources:
                insights.append(
                    f"Identified {len(technical_sources)} technical insights relevant to the query"
                )

        return insights[:5]  # Limit to top 5 insights

    async def _find_cross_references(
        self, sources: list[RAGSource], context: RAGContext
    ) -> list[dict[str, str]]:
        """Find cross-references between sources"""

        cross_refs = []

        if not context.enable_cross_references or len(sources) < 2:
            return cross_refs

        # Simple cross-reference detection based on overlapping entities
        for i, source1 in enumerate(sources):
            for source2 in sources[i + 1 :]:
                # Look for common entities or topics
                content1_words = set(source1.content.lower().split())
                content2_words = set(source2.content.lower().split())

                # Find significant overlapping words (excluding common words)
                common_words = content1_words.intersection(content2_words)
                significant_words = common_words - {
                    "the",
                    "and",
                    "or",
                    "in",
                    "on",
                    "at",
                    "to",
                    "for",
                    "of",
                    "with",
                    "by",
                }

                if len(significant_words) >= 2:
                    cross_refs.append(
                        {
                            "source1_id": source1.memory_id,
                            "source1_title": source1.title,
                            "source2_id": source2.memory_id,
                            "source2_title": source2.title,
                            "connection": f"Common themes: {', '.join(list(significant_words)[:3])}",
                        }
                    )

        return cross_refs[:3]  # Limit to top 3 cross-references

    async def _build_reasoning_chain(
        self, sources: list[RAGSource], context: RAGContext
    ) -> list[str]:
        """Build reasoning chain from sources"""

        if not context.include_reasoning:
            return []

        reasoning = []

        # Step 1: Query analysis
        reasoning.append(f"Query analysis: '{context.query}' in {context.domain.value} domain")

        # Step 2: Source selection rationale
        reasoning.append(
            f"Retrieved {len(sources)} sources from {len({s.source_type for s in sources})} knowledge stores"
        )

        # Step 3: Relevance assessment
        high_rel_sources = len([s for s in sources if s.relevance_score > 0.8])
        reasoning.append(f"Found {high_rel_sources} highly relevant sources (>80% relevance)")

        # Step 4: Confidence assessment
        high_conf_sources = len([s for s in sources if s.confidence > 0.8])
        reasoning.append(
            f"Identified {high_conf_sources} high-confidence sources for reliable information"
        )

        return reasoning

    async def _update_metrics(self, result: RAGResult, context: RAGContext):
        """Update RAG system performance metrics"""

        self.metrics["total_queries"] += 1

        # Update averages
        total = self.metrics["total_queries"]
        current_time = result.processing_time_ms
        current_sources = len(result.sources)

        self.metrics["avg_retrieval_time_ms"] = (
            self.metrics["avg_retrieval_time_ms"] * (total - 1) + current_time
        ) / total
        self.metrics["avg_sources_per_query"] = (
            self.metrics["avg_sources_per_query"] * (total - 1) + current_sources
        ) / total

        # Update domain and strategy counters
        self.metrics["by_domain"][context.domain.value] += 1
        self.metrics["by_strategy"][result.strategy_used.value] += 1

    async def _analyze_query_patterns(self) -> dict[str, Any]:
        """Analyze query patterns and trends"""

        return {
            "most_common_domain": (
                max(self.metrics["by_domain"], key=self.metrics["by_domain"].get)
                if self.metrics["by_domain"]
                else "none"
            ),
            "most_effective_strategy": (
                max(self.metrics["by_strategy"], key=self.metrics["by_strategy"].get)
                if self.metrics["by_strategy"]
                else "none"
            ),
            "query_frequency": self.metrics["total_queries"],
        }

    async def _calculate_retrieval_effectiveness(self) -> dict[str, float]:
        """Calculate retrieval effectiveness metrics"""

        total_queries = self.metrics["total_queries"]

        if total_queries == 0:
            return {"effectiveness_score": 0.0, "avg_sources": 0.0}

        # Simple effectiveness calculation
        effectiveness_score = min(
            1.0, self.metrics["avg_sources_per_query"] / 5.0
        )  # Target 5 sources per query

        return {
            "effectiveness_score": effectiveness_score,
            "avg_sources": self.metrics["avg_sources_per_query"],
            "avg_response_time": self.metrics["avg_retrieval_time_ms"],
        }


# Global unified RAG system instance
unified_rag = UnifiedRAGSystem()
