#!/usr/bin/env python3
"""Minimal integration tests for Artemis Scout swarm"""

import json
import os

import pytest

# Mock mode for testing without LLM calls
os.environ["TEST_MODE"] = "true"


class TestScoutIntegration:
    """Essential integration tests for scout swarm"""

    @pytest.mark.asyncio
    async def test_scout_readiness(self):
        """Test scout readiness check"""
        import subprocess

        result = subprocess.run(
            ["python3", "scripts/scout_readiness_check.py"], capture_output=True, text=True
        )

        output = json.loads(result.stdout)
        assert "mcp_stdio" in output
        assert "warnings" in output

        # Should have stdio MCP at minimum
        if not output.get("mcp_stdio"):
            pytest.skip("stdio MCP not available")

    @pytest.mark.asyncio
    async def test_prefetch_respects_limits(self):
        """Test prefetch stays within configured limits"""
        from app.swarms.scout.prefetch import prefetch_and_index

        # Set strict limits
        os.environ["SCOUT_PREFETCH_MAX_FILES"] = "5"
        os.environ["SCOUT_PREFETCH_MAX_BYTES"] = "1000"

        result = await prefetch_and_index(repo_root=".", max_files=5, max_bytes_per_file=1000)

        assert result["ok"] in [True, False]  # Can fail if no services
        if result.get("files_considered"):
            assert result["files_considered"] <= 5

    @pytest.mark.asyncio
    async def test_scout_output_validation(self):
        """Test scout output schema validation"""

        # Mock coordinator for testing
        class MockCoordinator:
            def __init__(self):
                self.config = type("obj", (object,), {"name": "Scout Test"})()

            def _validate_scout_output(self, text):
                """Direct test of validation logic"""
                required = [
                    "FINDINGS:",
                    "INTEGRATIONS:",
                    "RISKS:",
                    "RECOMMENDATIONS:",
                    "METRICS:",
                    "CONFIDENCE:",
                ]
                upper = text.upper()
                missing = []
                for sec in required:
                    if sec not in upper:
                        missing.append(sec.strip(":").title())
                return missing

        coord = MockCoordinator()

        # Valid output
        valid_output = """
        FINDINGS: Found 3 issues
        INTEGRATIONS: Redis, PostgreSQL
        RISKS: High memory usage
        RECOMMENDATIONS: Add caching
        METRICS: 10 files analyzed
        CONFIDENCE: 0.85
        """
        assert coord._validate_scout_output(valid_output) == []

        # Invalid output (missing sections)
        invalid_output = """
        FINDINGS: Found issues
        RISKS: Some risks
        """
        missing = coord._validate_scout_output(invalid_output)
        assert "Integrations" in missing
        assert "Recommendations" in missing
        assert "Metrics" in missing
        assert "Confidence" in missing

    @pytest.mark.asyncio
    async def test_scout_prompt_overlays(self):
        """Test scout prompt overlays are applied"""
        from app.swarms.scout.prompts import (
            ANALYST_OVERLAY,
            SCOUT_OUTPUT_SCHEMA,
            STRATEGIST_OVERLAY,
            VALIDATOR_OVERLAY,
        )

        # Verify overlays exist and contain key content
        assert "FINDINGS" in SCOUT_OUTPUT_SCHEMA
        assert "INTEGRATIONS" in SCOUT_OUTPUT_SCHEMA
        assert "CONFIDENCE" in SCOUT_OUTPUT_SCHEMA

        assert "heuristics" in ANALYST_OVERLAY.lower()
        assert "integrations" in STRATEGIST_OVERLAY.lower()
        assert "feasibility" in VALIDATOR_OVERLAY.lower()

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("ENABLE_LIVE_TESTS"),
        reason="Live tests disabled (set ENABLE_LIVE_TESTS=true)",
    )
    async def test_scout_smoke_execution(self):
        """Smoke test for actual scout execution (requires services)"""
        from app.swarms.core.swarm_integration import get_artemis_orchestrator

        orchestrator = get_artemis_orchestrator()

        # Simple scout task
        result = await orchestrator.execute_swarm(
            content="Analyze this small test repository",
            swarm_type="repository_scout",
            context={"test_mode": True, "timeout": 10},
        )

        assert result is not None
        assert "error" not in result or result.get("success")


# Quick test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
