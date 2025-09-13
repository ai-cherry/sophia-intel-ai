from __future__ import annotations

from typing import Any, Dict, List


class EntityExtractor:
    """Very simple entity extractor stub.

    In reality, would use NLP; here we detect simple key/value patterns in JSON/CSV rows.
    """

    def extract_from_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        entities: List[Dict[str, Any]] = []
        for row in records:
            for k, v in row.items():
                if isinstance(v, (str, int, float)) and k:
                    entities.append({
                        "name": k,
                        "type": self._guess_type(v),
                        "confidence": 0.85,  # simplistic stub
                        "evidence": [f"row:{k}"],
                    })
        return entities

    def _guess_type(self, v: Any) -> str:
        if isinstance(v, bool):
            return "checkbox"
        if isinstance(v, (int, float)):
            return "number"
        return "text"

