import asyncio
from types import SimpleNamespace
from unittest.mock import patch


async def test_fs_read_augmentation():
    # Lazy import to avoid heavy top-level deps in this environment
    from app.swarms.core.micro_swarm_base import (
        AgentProfile,
        AgentRole,
        MicroSwarmAgent,
    )

    # Build a minimal agent
    profile = AgentProfile(
        role=AgentRole.ANALYST,
        name="TestAgent",
        description="",
        model_preferences=[""],
        specializations=[""],
        reasoning_style="",
    )
    agent = MicroSwarmAgent(profile, swarm_id="test")

    # Fake MCP client
    fake_client = SimpleNamespace(
        fs_read=lambda path, max_bytes=1000: {"content": "hello world"}
    )

    async def run():
        # Patch detect_stdio_mcp to return fake client
        with patch(
            "app.swarms.core.micro_swarm_base.detect_stdio_mcp",
            return_value=fake_client,
        ):
            text = "Analysis complete.\nREQUEST_FS_READ:README.md:1000"
            out = await agent._maybe_handle_fs_read(text)
            assert out is not None
            assert "FILE_SNIPPET(README.md)" in out
            assert len(out) > len(text)

    asyncio.get_event_loop().run_until_complete(run())
