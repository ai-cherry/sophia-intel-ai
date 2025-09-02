import pytest
from app.observability.prometheus_metrics import get_cost_summary

def test_get_cost_summary():
    summary = get_cost_summary(days=30)
    assert summary is not None
    assert 'total_cost' in summary
    assert 'daily_breakdown' in summary
    assert len(summary['daily_breakdown']) == 30