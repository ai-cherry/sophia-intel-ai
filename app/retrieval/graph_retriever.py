from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.embeddings.together_embeddings import (
    EmbeddingModel,
    TogetherEmbeddingService,
    get_embedding_service,
)
from app.weaviate.weaviate_client import WeaviateClient

logger = logging.getLogger(__name__)


@dataclass
class GraphSearchRequest:
    query: str
    top_k: int = 10
    hops: int = 0  # placeholder for future multi-hop support
    filters: dict[str, Any] = field(default_factory=dict)
    start_nodes: list[str] = field(default_factory=list)
    model: str | None = None  # EmbeddingModel value


@dataclass
class GraphSearchHit:
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    # For future multi-hop graph paths
    path: list[str] = field(default_factory=list)


@dataclass
class GraphSearchResult:
    hits: list[GraphSearchHit]
    query: str
    top_k: int
    hops: int
    used_model: str
    notes: str | None = None


class GraphRetriever:
    """
    Initial Graph-RAG retriever. Current implementation:
      - Embeds the query
      - Performs vector search in Weaviate with optional repo_path filter
      - Returns top ranked chunks
    Future:
      - If hops > 0, perform multi-hop traversal via GraphQL with cross-ref expansion
      - Merge vector results with graph traversals (union + rerank)
    """

    def __init__(
        self,
        weaviate_client: WeaviateClient | None = None,
        embedding_service: TogetherEmbeddingService | None = None,
    ):
        self.weaviate = weaviate_client or WeaviateClient()
        self.embedder = embedding_service or get_embedding_service()

    async def search(self, req: GraphSearchRequest) -> GraphSearchResult:
        # Choose embedding model
        model = EmbeddingModel.M2_BERT_8K
        if req.model:
            try:
                model = EmbeddingModel(req.model)
            except Exception:
                logger.warning("Unknown embedding model '%s'. Falling back to %s", req.model, model.value)

        # Embed query
        embed_res = await self.embedder.embed_async([req.query], model=model)
        query_vec = embed_res.embeddings[0]

        # Basic metadata filter support (repo_path first)
        repo_path = None
        if "repo_path" in req.filters:
            repo_path = str(req.filters["repo_path"])

        # Vector search
        vec_hits = await self.weaviate.search_embeddings(
            query_embedding=query_vec,
            top_k=req.top_k,
            repo_path=repo_path,
        )

        hits: list[GraphSearchHit] = []
        for h in vec_hits:
            hits.append(
                GraphSearchHit(
                    id=h.get("id", ""),
                    text=h.get("text", ""),
                    score=float(h.get("score", 0.0)),
                    metadata=h.get("metadata") or {},
                    path=[],
                )
            )

        notes = None
        if req.hops and req.hops > 0:
            # Placeholder for graph traversal expansion
            notes = "Multi-hop traversal not yet implemented; returned vector results only."

        return GraphSearchResult(
            hits=hits,
            query=req.query,
            top_k=req.top_k,
            hops=req.hops,
            used_model=embed_res.model,
            notes=notes,
        )
