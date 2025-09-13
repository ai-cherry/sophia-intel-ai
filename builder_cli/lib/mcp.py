#!/usr/bin/env python3
"""
MCPManager: Start/stop/status helper for MCP servers (memory, filesystem, git).
Used by builder-cli/forge.py to orchestrate local MCP lifecycle.
"""
from __future__ import annotations
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.request import urlopen


@dataclass
class MCPServerConfig:
    name: str
    module: str
    port: int


class MCPManager:
    def __init__(self):
        self._cfgs: Dict[str, MCPServerConfig] = {
            "memory": MCPServerConfig("memory", "mcp.memory_server:app", int(os.getenv("MCP_MEMORY_PORT", "8081"))),
            "filesystem": MCPServerConfig("filesystem", "mcp.filesystem.server:app", int(os.getenv("MCP_FILESYSTEM_PORT", "8082"))),
            "git": MCPServerConfig("git", "mcp.git.server:app", int(os.getenv("MCP_GIT_PORT", "8084"))),
        }

    def _health_url(self, cfg: MCPServerConfig) -> str:
        return f"http://127.0.0.1:{cfg.port}/health"

    def _check_health(self, cfg: MCPServerConfig, timeout: float = 0.75) -> bool:
        try:
            with urlopen(self._health_url(cfg), timeout=timeout) as r:
                return r.status == 200
        except Exception:
            return False

    async def get_status(self) -> Dict[str, Dict]:
        # Simple sync check; forge CLI awaits this but it’s fast
        out: Dict[str, Dict] = {}
        for key, cfg in self._cfgs.items():
            out[key] = {"running": self._check_health(cfg), "port": cfg.port}
        return out

    async def start_server(self, server: str) -> int:
        server = server.lower()
        if server not in self._cfgs:
            raise ValueError(f"Unknown MCP server: {server}")
        cfg = self._cfgs[server]
        if self._check_health(cfg):
            return cfg.port
        # Launch via uvicorn in a detached subprocess
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            cfg.module,
            "--host",
            "0.0.0.0",
            "--port",
            str(cfg.port),
        ]
        env = os.environ.copy()
        subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Wait briefly for health
        for _ in range(20):
            if self._check_health(cfg, timeout=0.2):
                return cfg.port
            time.sleep(0.2)
        raise RuntimeError(f"Failed to start {server} on port {cfg.port}")

