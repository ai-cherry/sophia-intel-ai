"""Business metric loading and indexing for the Pay Ready dashboard."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import yaml

from app.embeddings.business_embeddings import business_embedding_pipeline
from app.indexing.meta_tagging import meta_tagger
from app.models.bi_dashboard import BusinessMetric

logger = logging.getLogger(__name__)


class BusinessMetricStore:
    """Manages metric definitions and refreshes embeddings."""

    def __init__(self, schema_path: Path | None = None) -> None:
        self.schema_path = schema_path or Path("schemas/business_metrics/pay_ready_metrics.yaml")
        self._cache: list[BusinessMetric] | None = None
        self._indexed = False

    def list_metrics(self) -> list[BusinessMetric]:
        if self._cache is None:
            self._cache = self._load()
        return list(self._cache)

    async def refresh_embeddings(self, metrics: Iterable[BusinessMetric] | None = None) -> None:
        data = list(metrics) if metrics is not None else self.list_metrics()
        if not data:
            return
        if metrics is None and self._indexed:
            return
        await business_embedding_pipeline.index_metrics(data)
        if metrics is None:
            self._indexed = True

    def _load(self) -> list[BusinessMetric]:
        try:
            payload = yaml.safe_load(self.schema_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            logger.error("Metric schema missing: %s", exc)
            return []

        metrics: list[BusinessMetric] = []
        for item in payload.get("metrics", []):
            tags = item.get("tags", {})
            try:
                meta_tagger.schema.validate(tags)
            except Exception as exc:
                logger.error("Invalid tags for metric %s: %s", item.get("id"), exc)
                continue
            metrics.append(
                BusinessMetric(
                    id=item["id"],
                    label=item["label"],
                    value=float(item["value"]),
                    unit=item.get("unit"),
                    trend=item.get("trend"),
                    target=item.get("target"),
                    tags=tags,
                )
            )
        return metrics


business_metric_store = BusinessMetricStore()
