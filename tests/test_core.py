"""Core System Tests for Sophia AI V2.0"""
from pathlib import Path
import pytest
import yaml
def test_single_config():
    """Ensure only one config file exists"""
    config_files = list(Path("config").glob("*"))
    # Should only have sophia.yaml and maybe README.md
    yaml_files = [f for f in config_files if f.suffix in [".yaml", ".yml", ".json"]]
    assert len(yaml_files) == 1, f"Expected 1 config file, found {len(yaml_files)}"
    assert yaml_files[0].name == "sophia.yaml"
def test_config_structure():
    """Test config file has correct structure"""
    with open("config/sophia.yaml") as f:
        config = yaml.safe_load(f)
    assert "app" in config
    assert config["app"]["name"] == "sophia-ai"
    assert config["app"]["version"] == "2.0.0"
    assert "asip" in config
    assert config["asip"]["enabled"] == True
    assert "services" in config
    assert "ai" in config
def test_minimal_mcp_servers():
    """Ensure MCP servers are minimal"""
    mcp_dirs = [d for d in Path("mcp_servers").iterdir() if d.is_dir()]
    assert len(mcp_dirs) <= 5, f"Too many MCP servers: {len(mcp_dirs)}"
    # Check for essential servers only
    essential = ["", "base", "business_intelligence", "security"]
    for server in essential:
        assert Path(
            f"mcp_servers/{server}"
        ).exists(), f"Missing essential server: {server}"
def test_minimal_agents():
    """Ensure agent systems are minimal"""
    agent_dirs = [d for d in Path("agents").iterdir() if d.is_dir()]
    assert len(agent_dirs) <= 2, f"Too many agent systems: {len(agent_dirs)}"
def test_backend_main_exists():
    """Ensure minimal backend exists"""
    assert Path("backend/main.py").exists()
    with open("backend/main.py") as f:
        content = f.read()
        assert "FastAPI" in content
        assert "Sophia AI V2.0" in content
        assert len(content.splitlines()) < 50  # Should be minimal
def test_no_docs_directory():
    """Ensure docs directory was deleted"""
    assert not Path("docs").exists(), "Docs directory should be deleted"
@pytest.mark.asyncio
async def test_api_imports():
    """Test that minimal API can be imported"""
    try:
        from backend.main import app
        assert app is not None
    except ImportError as e:
        pytest.skip(f"Dependencies not installed: {e}")
