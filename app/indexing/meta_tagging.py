"""Meta-tagging utilities for Pay Ready business intelligence documents."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.models.bi_dashboard import BusinessMetric
from app.models.metadata import MemoryMetadata


@dataclass(frozen=True)
class MetaDimension:
    """Definition for a single metadata dimension."""

    name: str
    description: str
    allowed: set[str]


class MetaTaggingSchema:
    """Loads and validates canonical meta-tagging rules."""

    def __init__(self, schema_path: Path | None = None) -> None:
        self.schema_path = schema_path or Path("schemas/business_metrics/meta_tags.yaml")
        self.dimensions = self._load()

    def _load(self) -> dict[str, MetaDimension]:
        raw = yaml.safe_load(self.schema_path.read_text(encoding="utf-8"))
        dimensions: dict[str, MetaDimension] = {}
        for name, payload in raw.get("dimensions", {}).items():
            dimensions[name] = MetaDimension(
                name=name,
                description=payload.get("description", ""),
                allowed=set(payload.get("allowed", [])),
            )
        return dimensions

    def validate(self, tags: dict[str, str]) -> dict[str, str]:
        output: dict[str, str] = {}
        for key, value in tags.items():
            dimension = self.dimensions.get(key)
            if not dimension:
                raise ValueError(f"Unknown meta-tag dimension: {key}")
            if value not in dimension.allowed:
                raise ValueError(f"Value '{value}' not allowed for dimension '{key}'")
            output[key] = value
        return output


class BusinessMetaTagger:
    """Builds MemoryMetadata entries for BI content using canonical tags."""

    def __init__(self, schema: MetaTaggingSchema | None = None) -> None:
        self.schema = schema or MetaTaggingSchema()

    def metric_metadata(self, metric: BusinessMetric) -> MemoryMetadata:
        tags = metric.dict().get("tags", {})  # type: ignore[arg-type]
        validated = self.schema.validate(tags)
        flattened_tags = [f"{key}:{value}" for key, value in validated.items()]
        return MemoryMetadata(
            type="doc",
            topic="pay_ready_metrics",
            source="schemas/business_metrics/pay_ready_metrics.yaml",
            tags=flattened_tags,
            project="pay_ready_bi",
            extra={"raw_tags": validated},
        )

    def encode(self, payload: Any, *, source: str, topic: str) -> MemoryMetadata:
        """General helper for arbitrary payload tagging."""

        tags = payload.get("tags", {}) if isinstance(payload, dict) else {}
        validated = self.schema.validate(tags) if tags else {}
        return MemoryMetadata(
            type="doc",
            topic=topic,
            source=source,
            tags=[f"{key}:{value}" for key, value in validated.items()],
            project="pay_ready_bi",
            extra={"raw": payload},
        )


meta_tagger = BusinessMetaTagger()
