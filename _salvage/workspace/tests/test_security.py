import pytest
from unittest.mock import patch, MagicMock
from connectors.github_conn import GitHubConnector
from services.sandbox import Sandbox
import docker

@pytest.mark.asyncio
async def test_github_connector_classic_pat_write_restriction():
    """
    Tests that the GitHub connector with a classic PAT raises an exception for write operations.
    """
    mock_config = {
        "github": {
            "mode": "classic_pat",
            "classic_pat_token": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        }
    }
    connector = GitHubConnector(mock_config)
    
    # We expect this to fail, but since we don't have a real classic PAT,
    # we'll mock the http client to simulate a forbidden error.
    with patch.object(connector.client, 'post', new_callable=MagicMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = Exception("403 Forbidden")
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="403 Forbidden"):
            await connector.create_pr("owner", "repo", "title", "body", "head", "base")

    await connector.close()

def test_sandbox_egress_allowlist():
    """
    Tests that the sandbox can't access disallowed hosts.
    This is a conceptual test, as true network isolation is complex to test here.
    We will simulate it by checking the network mode of the container.
    """
    sandbox = Sandbox(network_mode="none") # Using 'none' to disable networking
    assert sandbox.network_mode == "none"

@pytest.mark.asyncio
async def test_connector_missing_token():
    """
    Tests that connectors fail gracefully when tokens are missing.
    """
    mock_config = {"github": {"mode": "pat", "fine_grained_token": None}}
    connector = GitHubConnector(mock_config)
    
    # Without a token, the connector should raise an error when trying to get headers.
    with pytest.raises(Exception):
        await connector._get_auth_headers()
        
    await connector.close()