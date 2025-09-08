import pytest

from app.swarms.scout.prompts import (
    ANALYST_OVERLAY,
    SCOUT_OUTPUT_SCHEMA,
    STRATEGIST_OVERLAY,
    VALIDATOR_OVERLAY,
)


@pytest.mark.smoke
def test_scout_overlays_present():
    assert FINDINGS in SCOUT_OUTPUT_SCHEMA
    assert INTEGRATIONS in SCOUT_OUTPUT_SCHEMA
    assert RISKS in SCOUT_OUTPUT_SCHEMA
    assert RECOMMENDATIONS in SCOUT_OUTPUT_SCHEMA
    assert CONFIDENCE in SCOUT_OUTPUT_SCHEMA
    assert hotspots in ANALYST_OVERLAY.lower()
    assert integrations in STRATEGIST_OVERLAY.lower()
    assert feasibility in VALIDATOR_OVERLAY.lower()
