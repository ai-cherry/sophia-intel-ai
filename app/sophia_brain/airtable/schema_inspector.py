from __future__ import annotations

from typing import Any, Dict, List


class SchemaInspector:
    """Analyze Airtable table structures (field names/types) from metadata.

    This is a placeholder that expects Airtable metadata payloads.
    """

    def infer_structure(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        fields = []
        for f in metadata.get("fields", []):
            fields.append({
                "name": f.get("name"),
                "type": f.get("type"),
                "options": f.get("options", {}),
            })
        return {"fields": fields}

