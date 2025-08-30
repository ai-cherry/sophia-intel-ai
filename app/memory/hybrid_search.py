"""
Enhanced Hybrid Search with BM25 + Vector + Cross-Encoder Re-ranking.
Combines multiple retrieval methods for optimal results.
"""

import os
import json
import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from collections import Counter, defaultdict
import re

from app.memory.dual_tier_embeddings import DualTierEmbedder, cosine_similarity
from app.portkey_config import gateway, Role

# ============================================
# Configuration
# ============================================

@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search."""
    
    # Search weights
    semantic_weight: float = 0.65
    bm25_weight: float = 0.35
    
    # BM25 parameters
    bm25_k1: float = 1.2  # Term frequency saturation
    bm25_b: float = 0.75  # Length normalization
    
    # Re-ranking
    use_reranker: bool = True
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_top_k: int = 20
    
    # Results
    max_results: int = 50
    min_score: float = 0.3
    
    # Citations
    include_citations: bool = True
    citation_format: str = "{path}:{start_line}-{end_line}"

# ============================================
# BM25 Implementation
# ============================================

class BM25Index:
    """
    BM25 (Best Matching 25) implementation for text retrieval.
    """
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = []
        self.doc_ids = []
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.doc_freqs = {}
        self.idf = {}
        self.total_docs = 0
    
    def tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def index_documents(
        self,
        documents: List[str],
        doc_ids: List[str]
    ):
        """
        Index documents for BM25 search.
        
        Args:
            documents: List of document texts
            doc_ids: List of document IDs
        """
        self.documents = documents
        self.doc_ids = doc_ids
        self.total_docs = len(documents)
        
        # Tokenize all documents
        tokenized_docs = []
        for doc in documents:
            tokens = self.tokenize(doc)
            tokenized_docs.append(tokens)
            self.doc_lengths.append(len(tokens))
        
        # Calculate average document length
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
        
        # Calculate document frequencies
        self.doc_freqs = defaultdict(int)
        for tokens in tokenized_docs:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1
        
        # Calculate IDF for each term
        for token, freq in self.doc_freqs.items():
            # IDF = log((N - df + 0.5) / (df + 0.5))
            self.idf[token] = math.log(
                (self.total_docs - freq + 0.5) / (freq + 0.5)
            )
    
    def score(self, query: str, doc_idx: int) -> float:
        """
        Calculate BM25 score for a document.
        
        Args:
            query: Search query
            doc_idx: Document index
        
        Returns:
            BM25 score
        """
        query_tokens = self.tokenize(query)
        doc_tokens = self.tokenize(self.documents[doc_idx])
        doc_length = self.doc_lengths[doc_idx]
        
        # Count term frequencies in document
        doc_term_freqs = Counter(doc_tokens)
        
        score = 0.0
        for token in query_tokens:
            if token not in self.idf:
                continue
            
            tf = doc_term_freqs.get(token, 0)
            idf = self.idf[token]
            
            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * (doc_length / self.avg_doc_length)
            )
            
            score += idf * (numerator / denominator)
        
        return score
    
    def search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Search documents using BM25.
        
        Args:
            query: Search query
            top_k: Number of top results
        
        Returns:
            List of (doc_id, score) tuples
        """
        scores = []
        for i in range(len(self.documents)):
            score = self.score(query, i)
            if score > 0:
                scores.append((self.doc_ids[i], score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]

# ============================================
# Search Result Models
# ============================================

@dataclass
class SearchResult:
    """Single search result with metadata."""
    id: str
    content: str
    score: float
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    citation: Optional[str] = None
    
    def __lt__(self, other):
        return self.score > other.score  # Higher score is better

@dataclass
class HybridSearchResult:
    """Combined search result from multiple methods."""
    result: SearchResult
    semantic_score: float = 0.0
    bm25_score: float = 0.0
    rerank_score: float = 0.0
    final_score: float = 0.0

# ============================================
# Cross-Encoder Re-ranker
# ============================================

class CrossEncoderReranker:
    """
    Cross-encoder based re-ranking for improved relevance.
    """
    
    def __init__(self, model: str = "BAAI/bge-reranker-v2-m3"):
        self.model = model
    
    async def rerank(
        self,
        query: str,
        candidates: List[SearchResult],
        top_k: int = 20
    ) -> List[Tuple[SearchResult, float]]:
        """
        Re-rank candidates using cross-encoder.
        
        Args:
            query: Search query
            candidates: Candidate results
            top_k: Number of results to return
        
        Returns:
            Re-ranked results with scores
        """
        if not candidates:
            return []
        
        # Prepare pairs for cross-encoder
        pairs = [
            f"Query: {query}\nDocument: {candidate.content[:500]}"
            for candidate in candidates
        ]
        
        # Get relevance scores from model
        # In production, this would call the actual reranker model
        # For now, simulate with a simple scoring
        scores = []
        for i, pair in enumerate(pairs):
            # Simulate relevance scoring
            query_terms = set(query.lower().split())
            doc_terms = set(candidates[i].content.lower().split())
            overlap = len(query_terms & doc_terms)
            score = overlap / max(len(query_terms), 1)
            scores.append(score)
        
        # Combine with results
        reranked = list(zip(candidates, scores))
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        return reranked[:top_k]

# ============================================
# Hybrid Search Engine
# ============================================

class HybridSearchEngine:
    """
    Main hybrid search engine combining multiple retrieval methods.
    """
    
    def __init__(
        self,
        config: Optional[HybridSearchConfig] = None,
        embedder: Optional[DualTierEmbedder] = None
    ):
        self.config = config or HybridSearchConfig()
        self.embedder = embedder or DualTierEmbedder()
        self.bm25_index = BM25Index(
            k1=self.config.bm25_k1,
            b=self.config.bm25_b
        )
        self.reranker = CrossEncoderReranker(self.config.reranker_model)
        
        # Storage
        self.documents = {}
        self.embeddings = {}
    
    def index_documents(
        self,
        documents: List[Dict[str, Any]]
    ):
        """
        Index documents for hybrid search.
        
        Args:
            documents: List of documents with id, content, and metadata
        """
        doc_ids = []
        doc_contents = []
        
        for doc in documents:
            doc_id = doc["id"]
            content = doc["content"]
            
            self.documents[doc_id] = doc
            doc_ids.append(doc_id)
            doc_contents.append(content)
        
        # Index for BM25
        self.bm25_index.index_documents(doc_contents, doc_ids)
    
    async def index_with_embeddings(
        self,
        documents: List[Dict[str, Any]]
    ):
        """
        Index documents with embeddings.
        
        Args:
            documents: List of documents
        """
        # Regular indexing
        self.index_documents(documents)
        
        # Generate embeddings
        contents = [doc["content"] for doc in documents]
        metadata = [doc.get("metadata", {}) for doc in documents]
        
        embeddings = await self.embedder.embed_batch(contents, metadata)
        
        for doc, (embedding, tier) in zip(documents, embeddings):
            self.embeddings[doc["id"]] = embedding
    
    def semantic_search(
        self,
        query_embedding: List[float],
        top_k: int = 50
    ) -> List[Tuple[str, float]]:
        """
        Perform semantic search using embeddings.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results
        
        Returns:
            List of (doc_id, score) tuples
        """
        scores = []
        
        for doc_id, doc_embedding in self.embeddings.items():
            similarity = cosine_similarity(query_embedding, doc_embedding)
            scores.append((doc_id, similarity))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        use_semantic: bool = True,
        use_bm25: bool = True,
        use_reranker: Optional[bool] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[HybridSearchResult]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query
            top_k: Number of results (default from config)
            use_semantic: Use semantic search
            use_bm25: Use BM25 search
            use_reranker: Use re-ranker (default from config)
            metadata_filter: Filter results by metadata
        
        Returns:
            List of hybrid search results
        """
        top_k = top_k or self.config.max_results
        use_reranker = use_reranker if use_reranker is not None else self.config.use_reranker
        
        # Collect candidates
        candidates = {}
        
        # Semantic search
        semantic_scores = {}
        if use_semantic and self.embeddings:
            query_embedding, _ = await self.embedder.embed_single(query)
            semantic_results = self.semantic_search(query_embedding, top_k * 2)
            
            for doc_id, score in semantic_results:
                semantic_scores[doc_id] = score
                if doc_id not in candidates:
                    candidates[doc_id] = self.documents[doc_id]
        
        # BM25 search
        bm25_scores = {}
        if use_bm25:
            bm25_results = self.bm25_index.search(query, top_k * 2)
            
            for doc_id, score in bm25_results:
                # Normalize BM25 scores to [0, 1]
                normalized_score = 1 / (1 + math.exp(-score))
                bm25_scores[doc_id] = normalized_score
                if doc_id not in candidates:
                    candidates[doc_id] = self.documents[doc_id]
        
        # Apply metadata filter
        if metadata_filter:
            filtered_candidates = {}
            for doc_id, doc in candidates.items():
                doc_meta = doc.get("metadata", {})
                match = all(
                    doc_meta.get(k) == v
                    for k, v in metadata_filter.items()
                )
                if match:
                    filtered_candidates[doc_id] = doc
            candidates = filtered_candidates
        
        # Create search results
        search_results = []
        for doc_id, doc in candidates.items():
            result = SearchResult(
                id=doc_id,
                content=doc["content"],
                score=0.0,
                source=doc.get("source", ""),
                metadata=doc.get("metadata", {})
            )
            
            # Add citation if enabled
            if self.config.include_citations:
                meta = doc.get("metadata", {})
                if "path" in meta:
                    citation = self.config.citation_format.format(
                        path=meta["path"],
                        start_line=meta.get("start_line", 1),
                        end_line=meta.get("end_line", 1)
                    )
                    result.citation = citation
            
            search_results.append(result)
        
        # Re-rank if enabled
        rerank_scores = {}
        if use_reranker and search_results:
            reranked = await self.reranker.rerank(
                query,
                search_results,
                self.config.reranker_top_k
            )
            for result, score in reranked:
                rerank_scores[result.id] = score
        
        # Combine scores
        hybrid_results = []
        for result in search_results:
            doc_id = result.id
            
            # Get individual scores
            sem_score = semantic_scores.get(doc_id, 0.0)
            bm25_score = bm25_scores.get(doc_id, 0.0)
            rerank_score = rerank_scores.get(doc_id, 0.0)
            
            # Calculate final score
            if use_reranker and doc_id in rerank_scores:
                # If re-ranked, use re-rank score primarily
                final_score = rerank_score
            else:
                # Weighted combination
                final_score = (
                    self.config.semantic_weight * sem_score +
                    self.config.bm25_weight * bm25_score
                )
            
            # Filter by minimum score
            if final_score < self.config.min_score:
                continue
            
            hybrid_result = HybridSearchResult(
                result=result,
                semantic_score=sem_score,
                bm25_score=bm25_score,
                rerank_score=rerank_score,
                final_score=final_score
            )
            hybrid_result.result.score = final_score
            hybrid_results.append(hybrid_result)
        
        # Sort by final score
        hybrid_results.sort(key=lambda x: x.final_score, reverse=True)
        
        return hybrid_results[:top_k]
    
    def format_results_for_context(
        self,
        results: List[HybridSearchResult],
        max_tokens: int = 4000
    ) -> str:
        """
        Format search results for LLM context.
        
        Args:
            results: Search results
            max_tokens: Maximum context tokens
        
        Returns:
            Formatted context string
        """
        context_parts = []
        current_tokens = 0
        
        for i, result in enumerate(results):
            # Format result
            if result.result.citation:
                header = f"[{i+1}] {result.result.citation} (score: {result.final_score:.3f})"
            else:
                header = f"[{i+1}] {result.result.source} (score: {result.final_score:.3f})"
            
            content = result.result.content[:500]  # Truncate long content
            
            part = f"{header}\n{content}\n"
            part_tokens = len(part.split())  # Simple token estimate
            
            if current_tokens + part_tokens > max_tokens:
                break
            
            context_parts.append(part)
            current_tokens += part_tokens
        
        return "\n".join(context_parts)

# ============================================
# Search Utilities
# ============================================

def merge_search_results(
    results_lists: List[List[SearchResult]],
    weights: Optional[List[float]] = None
) -> List[SearchResult]:
    """
    Merge multiple search result lists.
    
    Args:
        results_lists: Multiple lists of search results
        weights: Optional weights for each list
    
    Returns:
        Merged and re-scored results
    """
    if not results_lists:
        return []
    
    if weights is None:
        weights = [1.0 / len(results_lists)] * len(results_lists)
    
    # Collect all results
    merged = {}
    for results, weight in zip(results_lists, weights):
        for result in results:
            if result.id not in merged:
                merged[result.id] = result
                result.score *= weight
            else:
                merged[result.id].score += result.score * weight
    
    # Sort by combined score
    final_results = list(merged.values())
    final_results.sort(key=lambda x: x.score, reverse=True)
    
    return final_results

# ============================================
# CLI Interface
# ============================================

async def main():
    """CLI for testing hybrid search."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hybrid search system")
    parser.add_argument("--index", help="Index test documents")
    parser.add_argument("--search", help="Search query")
    parser.add_argument("--semantic-only", action="store_true")
    parser.add_argument("--bm25-only", action="store_true")
    parser.add_argument("--no-rerank", action="store_true")
    
    args = parser.parse_args()
    
    engine = HybridSearchEngine()
    
    if args.index:
        # Create test documents
        test_docs = [
            {
                "id": "doc1",
                "content": "Python is a high-level programming language with dynamic semantics.",
                "metadata": {"language": "python", "type": "definition"}
            },
            {
                "id": "doc2",
                "content": "JavaScript is the programming language of the web, enabling interactive websites.",
                "metadata": {"language": "javascript", "type": "definition"}
            },
            {
                "id": "doc3",
                "content": "Machine learning models can be trained using Python libraries like TensorFlow.",
                "metadata": {"language": "python", "type": "tutorial"}
            }
        ]
        
        await engine.index_with_embeddings(test_docs)
        print(f"✅ Indexed {len(test_docs)} documents")
    
    elif args.search:
        use_semantic = not args.bm25_only
        use_bm25 = not args.semantic_only
        use_reranker = not args.no_rerank
        
        results = await engine.search(
            args.search,
            use_semantic=use_semantic,
            use_bm25=use_bm25,
            use_reranker=use_reranker
        )
        
        print(f"\n🔍 Search results for: '{args.search}'")
        print(f"   Method: {'Hybrid' if use_semantic and use_bm25 else 'Semantic' if use_semantic else 'BM25'}")
        print(f"   Re-ranking: {'Enabled' if use_reranker else 'Disabled'}\n")
        
        for i, result in enumerate(results[:5]):
            print(f"[{i+1}] Score: {result.final_score:.3f}")
            print(f"    Semantic: {result.semantic_score:.3f}, BM25: {result.bm25_score:.3f}, Rerank: {result.rerank_score:.3f}")
            print(f"    Content: {result.result.content[:100]}...")
            if result.result.citation:
                print(f"    Citation: {result.result.citation}")
            print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())