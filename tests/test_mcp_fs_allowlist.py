import pytest
from fastapi import HTTPException
from pathlib import Path

from mcp.filesystem import MCPFilesystemServer


def test_mcp_fs_allowlist_validation(tmp_path: Path):
    allowed = [tmp_path]
    server = MCPFilesystemServer(allowlist=allowed, read_only=True)
    # File inside allowlist should validate
    inside = tmp_path / "foo.txt"
    inside.parent.mkdir(parents=True, exist_ok=True)
    inside.write_text("ok")
    assert server.validate_path(str(inside)).exists()
    # File outside should raise
    with pytest.raises(HTTPException):
        server.validate_path("/etc/hosts")

