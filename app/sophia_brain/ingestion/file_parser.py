from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List, Tuple


class FileParser:
    """Basic file parser for text/csv/json.

    For PDFs/DOCX, return a not-supported message to avoid heavy deps.
    """

    def parse(self, filename: str, content: bytes) -> Tuple[str, Any]:
        lower = filename.lower()
        if lower.endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            return ("json", data)
        if lower.endswith(".csv"):
            text = content.decode("utf-8", errors="ignore")
            reader = csv.DictReader(io.StringIO(text))
            return ("csv", list(reader))
        if lower.endswith(".txt") or lower.endswith(".md"):
            return ("text", content.decode("utf-8", errors="ignore"))
        if lower.endswith(".pdf") or lower.endswith(".docx"):
            return ("unsupported", "PDF/DOCX parsing requires optional dependency")
        # Fallback: treat as text
        return ("text", content.decode("utf-8", errors="ignore"))

