import os
import pytest

pytestmark = pytest.mark.integration


def test_delegated_placeholder():
    # Placeholder: run only if a delegated access token is provided
    token = os.getenv("MS_DELEGATED_TOKEN")
    if not token:
        pytest.skip("MS_DELEGATED_TOKEN not set; delegated-flow tests skipped")
    # Future: hit Graph /me with provided bearer token
    assert token.startswith("ey") or len(token) > 20

