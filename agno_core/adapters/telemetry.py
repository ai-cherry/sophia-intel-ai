from __future__ import annotations

import json
import threading
from collections import deque
from typing import Any, Deque, Dict


class Telemetry:
    """Simple in-process telemetry bus with ring buffer and stdout logging."""

    def __init__(self, capacity: int = 1000, echo_stdout: bool = True):
        self._buf: Deque[Dict[str, Any]] = deque(maxlen=capacity)
        self._lock = threading.Lock()
        self.echo = echo_stdout

    def emit(self, event: Dict[str, Any]) -> None:
        with self._lock:
            self._buf.append(event)
        if self.echo:
            print("[telemetry]", json.dumps(event, separators=(",", ":")))

    def snapshot(self) -> Any:
        with self._lock:
            return list(self._buf)

