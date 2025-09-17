"""Business intelligence embedding pipeline for Pay Ready metrics."""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from app.memory.unified.vector_store import (
    EmbeddingModel,
    VectorMetadata,
    VectorStore,
)
from app.models.bi_dashboard import BusinessMetric

logger = logging.getLogger(__name__)


class BusinessEmbeddingPipeline:
    """Indexes Pay Ready BI metrics and contextual docs into the vector store."""

    def __init__(self, vector_store: VectorStore | None = None) -> None:
        self.vector_store = vector_store or VectorStore()
        self.domain = "pay_ready_business_intelligence"

    async def index_metrics(self, metrics: Iterable[BusinessMetric]) -> None:
        """Index metric briefs to enable contextual search."""

        if not metrics:
            return

        tasks = [self._index_metric(metric) for metric in metrics]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _index_metric(self, metric: BusinessMetric) -> None:
        content = self._build_metric_summary(metric)
        metadata = VectorMetadata(
            content_type="text",
            embedding_model=EmbeddingModel.SENTENCE_TRANSFORMERS,
            dimensions=384,
            preprocessing_steps=["metric_summary"],
            parent_document_id=metric.id,
            quality_score=0.95,
        )

        try:
            await self.vector_store.store_embedding(
                content=content,
                embedding=None,
                metadata=metadata,
                memory_id=f"metric::{metric.id}",
                domain=self.domain,
            )
        except Exception as exc:  # pragma: no cover - dependent on vector backends
            logger.warning("Failed to index metric %s: %s", metric.id, exc)

    def _build_metric_summary(self, metric: BusinessMetric) -> str:
        unit = metric.unit or ""
        trend = metric.trend or "flat"
        target = metric.target if metric.target is not None else "unassigned"
        tag_summary = ', '.join(f"{key}:{value}" for key, value in metric.tags.items()) if metric.tags else 'no tags'
        return (
            f"Metric {metric.label} ({metric.id}) currently reports {metric.value}{unit}. "
            f"Trend is {trend} with target {target}. Tags: {tag_summary}."
        )


business_embedding_pipeline = BusinessEmbeddingPipeline()
