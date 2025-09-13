#!/usr/bin/env python3
"""
Validate common Sophia Intel AI ports are free or report conflicts.
This is a lightweight preflight helper for local dev and CI.
"""
from __future__ import annotations

import os
import socket
from dataclasses import dataclass


@dataclass
class PortStatus:
    name: str
    port: int
    free: bool
    host: str = "localhost"


def is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.25)
    try:
        return s.connect_ex((host, int(port))) != 0
    finally:
        try:
            s.close()
        except Exception:
            pass


def getenv_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def main() -> int:
    ports = [
        ("UI", getenv_int("SOPHIA_UI_PORT", 3000)),
        ("API", getenv_int("SOPHIA_API_PORT", 8000)),
        ("Proxy", getenv_int("SOPHIA_PROXY_PORT", 8080)),
        ("MCP Memory", getenv_int("MCP_MEMORY_PORT", 8081)),
        ("MCP FS", getenv_int("MCP_FS_PORT", 8082)),
        ("MCP Git", getenv_int("MCP_GIT_PORT", 8084)),
    ]
    statuses: list[PortStatus] = []
    conflicts = 0
    for name, port in ports:
        free = is_port_free(port)
        statuses.append(PortStatus(name=name, port=port, free=free))
        if not free:
            conflicts += 1

    print("Sophia Port Validation:")
    for st in statuses:
        badge = "OK" if st.free else "IN USE"
        print(f"  {st.name:11s} {st.port:5d}  {badge}")

    if conflicts:
        print(f"\nConflicts detected: {conflicts}. Set env vars to override or free ports.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

