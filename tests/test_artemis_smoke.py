"""Artemis smoke tests - fast, essential tests for collaboration proposals"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.smoke
def test_artemis_import():
    """Test that Artemis demo module can be imported"""
    from app.artemis_demo import artemis_status

    assert artemis_status is not None


@pytest.mark.smoke
def test_artemis_status():
    """Test Artemis status returns expected structure"""
    from app.artemis_demo import artemis_status

    status = artemis_status()
    assert status["status"] == "active"
    assert status["version"] == "2.0"
    assert status["collaboration"] is True


@pytest.mark.smoke
def test_proposal_processing():
    """Test proposal processing function"""
    from app.artemis_demo import process_proposal

    result = process_proposal("test-123")
    assert result["proposal_id"] == "test-123"
    assert result["status"] == "processed"


@pytest.mark.smoke
def test_collaboration_ready():
    """Verify collaboration system is ready"""
    from app.artemis_demo import artemis_status

    status = artemis_status()
    assert "Artemis collaboration system operational" in status["message"]


if __name__ == "__main__":
    # Run smoke tests only
    pytest.main([__file__, "-v", "-m", "smoke"])
