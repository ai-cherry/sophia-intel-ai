import os
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.microsoft]


def _has_ms_env() -> bool:
    """Check if Microsoft Graph credentials are available."""
    return bool(
        (os.getenv("MS_TENANT_ID") or os.getenv("MICROSOFT_TENANT_ID"))
        and (os.getenv("MS_CLIENT_ID") or os.getenv("MICROSOFT_CLIENT_ID"))
        and (
            (os.getenv("MS_CLIENT_SECRET") or os.getenv("MICROSOFT_SECRET_KEY"))
            or (os.getenv("MICROSOFT_CERTIFICATE_ID") and (
                os.getenv("MICROSOFT_SIGNING_CERTIFICATE") or 
                os.getenv("MICROSOFT_SIGNING_CERTIFICATE_BASE64")
            ))
        )
    )


@pytest.mark.asyncio
async def test_microsoft_graph_authentication():
    """Test Microsoft Graph client authentication (cert or secret)."""
    if not _has_ms_env():
        pytest.skip("Microsoft Graph credentials not configured")

    from app.integrations.microsoft_graph_client import MicrosoftGraphClient

    # Test that we can create client and authenticate
    client = MicrosoftGraphClient()
    assert client.tenant_id is not None
    assert client.client_id is not None
    assert client._auth_method in ["certificate", "client_secret"]
    
    # Test token acquisition
    token = client._ensure_token()
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_microsoft_graph_users():
    """Test Microsoft Graph users endpoint."""
    if not _has_ms_env():
        pytest.skip("Microsoft Graph credentials not configured")

    from app.integrations.microsoft_graph_client import MicrosoftGraphClient

    client = MicrosoftGraphClient()
    users = await client.list_users(top=1)
    
    assert isinstance(users, dict)
    assert "value" in users
    assert isinstance(users["value"], list)
    
    # If users exist, check structure
    if users["value"]:
        user = users["value"][0]
        assert "id" in user
        assert "displayName" in user or "userPrincipalName" in user


@pytest.mark.asyncio 
async def test_microsoft_graph_teams():
    """Test Microsoft Graph teams/groups endpoint."""
    if not _has_ms_env():
        pytest.skip("Microsoft Graph credentials not configured")

    from app.integrations.microsoft_graph_client import MicrosoftGraphClient

    client = MicrosoftGraphClient()
    teams = await client.list_teams(top=1)
    
    assert isinstance(teams, dict)
    assert "value" in teams
    assert isinstance(teams["value"], list)
    
    # If teams exist, check structure  
    if teams["value"]:
        team = teams["value"][0]
        assert "id" in team
        assert "displayName" in team


@pytest.mark.asyncio
async def test_microsoft_graph_drive():
    """Test Microsoft Graph drive root endpoint.""" 
    if not _has_ms_env():
        pytest.skip("Microsoft Graph credentials not configured")

    from app.integrations.microsoft_graph_client import MicrosoftGraphClient

    client = MicrosoftGraphClient()
    drive = await client.drive_root()
    
    assert isinstance(drive, dict)
    assert "id" in drive
    assert "driveType" in drive or "name" in drive
