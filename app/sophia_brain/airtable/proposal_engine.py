from __future__ import annotations

from typing import Any, Dict, List


class FieldProposal(dict):
    pass


class SchemaProposal(dict):
    def __init__(self) -> None:
        super().__init__(fields=[], questions=[])

    def add_field(self, field: Dict[str, Any], evidence: List[str] | None = None) -> None:
        f = dict(field)
        if evidence:
            f["evidence"] = evidence
        self["fields"].append(f)

    def add_question(self, q: str) -> None:
        self["questions"].append(q)


class ProposalEngine:
    """Evidence-based schema proposals from extracted entities.

    This is a simplified stub that only proposes fields when confidence is high.
    """

    def propose_from_entities(self, entities: List[Dict[str, Any]]) -> SchemaProposal:
        proposal = SchemaProposal()
        for e in entities:
            name = e.get("name")
            suggested_type = e.get("type")
            confidence = float(e.get("confidence", 0))
            evidence = e.get("evidence", [])
            if not name or not suggested_type:
                continue
            if confidence >= 0.8:
                proposal.add_field({"name": name, "type": suggested_type}, evidence=evidence)
            else:
                proposal.add_question(f"Is '{name}' a {suggested_type}?")
        return proposal

