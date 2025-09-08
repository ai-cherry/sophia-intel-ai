#!/usr/bin/env python3
from typing import Dict, Any
import time
import json


class TelemetryWire:
    """Simple in-process telemetry aggregator with optional flush to endpoint."""

    def __init__(self):
        self.events = []
        self.metrics = {}

    def record(self, event_type: str, data: Dict[str, Any]):
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": data,
        }
        self.events.append(event)

        # Update metrics
        category = data.get("category", "unknown")
        if category not in self.metrics:
            self.metrics[category] = {"count": 0, "total_ms": 0}

        self.metrics[category]["count"] += 1
        if "duration_ms" in data:
            self.metrics[category]["total_ms"] += data["duration_ms"]

    def get_p95(self, category: str) -> float:
        events = [e for e in self.events if e["data"].get("category") == category]
        if len(events) < 5:
            return 0

        durations = sorted([e["data"].get("duration_ms", 0) for e in events])
        p95_idx = int(len(durations) * 0.95)
        p95_idx = min(max(p95_idx, 0), len(durations) - 1)
        return durations[p95_idx]

    def flush_to_endpoint(self):
        """Send to telemetry endpoint if available; clear buffer on success."""
        import httpx

        if not self.events:
            return
        try:
            resp = httpx.post("http://localhost:5003/api/telemetry/events", json=self.events, timeout=5.0)
            if resp.status_code < 300:
                self.events = []  # Clear after sending
        except Exception:
            # Silent fail in dev
            pass


telemetry = TelemetryWire()

