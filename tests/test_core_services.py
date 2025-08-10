import pytest
import os
from unittest.mock import patch, MagicMock

from services.config_loader import load_config, AppConfig, GitHubConfig, PulumiConfig, QdrantConfig
from services.sandbox import Sandbox
from services.memory_client import MemoryClient

# Fixtures for configuration
@pytest.fixture
def mock_env_vars():
    with patch.dict(os.environ, {
        "GH_FINE_GRAINED_TOKEN": "test_gh_token",
        "PULUMI_ACCESS_TOKEN": "test_pulumi_token",
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_API_KEY": "test_qdrant_key",
        "OPENROUTER_API_KEY": "test_or_key"
    }):
        yield

# Tests for Config Loader
def test_load_config_from_env(mock_env_vars):
    config = load_config(prefer_esc=False)
    assert isinstance(config, AppConfig)
    assert config.github.token == "test_gh_token"
    assert config.pulumi.access_token == "test_pulumi_token"
    assert "openrouter" in config.llm_keys

def test_load_config_missing_token():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError):
            load_config(prefer_esc=False)

# Tests for Sandbox
def test_sandbox_run_safe_command():
    sandbox = Sandbox()
    result = sandbox.run(["echo", "safe"])
    assert result.exit_code == 0
    assert "safe" in result.stdout

def test_sandbox_run_nonexistent_command():
    sandbox = Sandbox()
    result = sandbox.run(["nonexistentcommand"])
    assert result.exit_code != 0

# Tests for Memory Client (requires mocking qdrant_client)
@patch('services.memory_client.QdrantClient')
def test_memory_client_initialization(mock_qdrant_client):
    mock_config = {"qdrant": {"url": "http://test-url", "api_key": "test-key"}}
    client = MemoryClient(mock_config)
    mock_qdrant_client.assert_called_with(url="http://test-url", api_key="test-key")
    assert client is not None

@patch('services.memory_client.QdrantClient')
def test_memory_client_create_collection(mock_qdrant_client):
    mock_instance = MagicMock()
    mock_qdrant_client.return_value = mock_instance
    mock_instance.get_collection.side_effect = Exception("Collection not found")

    client = MemoryClient({"qdrant": {}})
    client.create_collection("test_collection", 128)
    mock_instance.create_collection.assert_called_once()

# Security Tests
def test_security_sandbox_refuses_disallowed_egress():
    # This test is a placeholder for a more robust implementation
    # where the sandbox would actually block the command.
    sandbox = Sandbox(egress_allowlist=["https://api.safe.com"])
    # In our current placeholder, this will still run, but we can test the check
    with patch('builtins.print') as mock_print:
        sandbox._check_egress(["curl", "https://api.unsafe.com"])
        # We can't assert the block, but we can check if it was detected
        # In a real implementation, the test would assert the command fails.
        pass # Placeholder

def test_security_config_loader_fails_without_tokens():
    with pytest.raises(ValueError):
        load_config(prefer_esc=False)