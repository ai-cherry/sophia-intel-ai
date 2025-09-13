"""Top-level MCP servers (HTTP shims) for filesystem, git, and memory.
These servers intentionally live outside the existing app/ tree to avoid
conflicts with prior MCP integrations. Dockerfiles point uvicorn at these
modules directly.
"""
