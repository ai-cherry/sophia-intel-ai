from app.swarms.cli.artemis_runner import format_scout_json


class DummyResult:
    def __init__(
        self,
        final_output: str,
        success: bool = True,
        confidence: float = 0.85,
        execution_time_ms: float = 1234.0,
        metadata: dict | None = None,
    ):
        self.final_output = final_output
        self.success = success
        self.confidence = confidence
        self.execution_time_ms = execution_time_ms
        self.metadata = metadata or {}


def test_format_scout_json_parses_sections_minimal():
    output = (
        "FINDINGS:\n"
        "- Found important integration points\n"
        "- Hotspots in auth flow\n"
        "INTEGRATIONS:\n"
        "- Redis\n"
        "- Weaviate\n"
        "RISKS:\n"
        "- Token leakage in logs\n"
        "RECOMMENDATIONS:\n"
        "- Rotate API keys regularly\n"
    )
    res = DummyResult(output, metadata={"tool_usage_total": 3})
    out = format_scout_json("test task", res)

    assert out["task"] == "test task"
    assert any("integration points" in it for it in out["findings"])  # section captured
    assert "- Redis" in out["integrations"]
    assert out["risks"] and out["risks"][0]["text"].startswith("-")
    assert out["recommendations"][0].startswith("-")
    assert out["metrics"]["confidence"] == res.confidence
    assert out["metrics"]["execution_time"] == res.execution_time_ms
    assert out["metrics"]["tool_usage_total"] == 3
    assert out["success"] is True


def test_format_scout_json_handles_missing_sections():
    # Only RISKS present; others should default to empty lists
    output = "RISKS:\n" "- Missing input validation\n"
    res = DummyResult(output, success=False, confidence=0.0, execution_time_ms=0.0)
    out = format_scout_json("task b", res)

    assert out["findings"] == []
    assert out["integrations"] == []
    assert out["recommendations"] == []
    assert out["risks"] and out["risks"][0]["text"].startswith("-")
    assert out["success"] is False
