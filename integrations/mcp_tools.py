from __future__ import annotations
import os
from pathlib import Path

USE_MCP = os.getenv("USE_MCP", "1") == "1"
SESSION_DIR = Path(os.getenv("MCP_SESSION_DIR", ".sophia_sessions"))
SESSION_DIR.mkdir(parents=True, exist_ok=True)

def _noop(*args, **kwargs): return [] if "search" in kwargs or (args and isinstance(args[0], str)) else {}

# defaults (no-op if MCP not available or disabled)
mcp_semantic_search = lambda query, k=8: []
mcp_file_map = lambda paths=None: {}
mcp_smart_hints = lambda tool_name, context="": {}
def mcp_learn(event: dict) -> None: pass

if USE_MCP:
    try:
        from libs.mcp_client.sophia_client import SophiaClient
        from libs.mcp_client.session_manager import SessionManager
        from libs.mcp_client.repo_intelligence import RepoIntelligence
        from libs.mcp_client.context_tools import ContextTools
        from libs.mcp_client.predictive_assistant import PredictiveAssistant
        from libs.mcp_client.performance_monitor import PerfMonitor

        _mgr = SessionManager(session_dir=str(SESSION_DIR))
        _sess = _mgr.start_or_resume()
        _cli  = SophiaClient(
            code_context_transport=os.getenv("MCP_CODE_CONTEXT", "stdio"),
            http_url=os.getenv("MCP_HTTP_URL", "")
        )
        _repo = RepoIntelligence(client=_cli, session=_sess)
        _ctx  = ContextTools(client=_cli, session=_sess)
        _pred = PredictiveAssistant(client=_cli, session=_sess)
        _perf = PerfMonitor(client=_cli, session=_sess)

        def mcp_semantic_search(query: str, k: int = 8) -> list[dict]:
            return _repo.semantic_search(query=query, k=k) or []

        def mcp_file_map(paths: list[str] | None = None) -> dict:
            return _repo.code_map(paths or [])

        def mcp_smart_hints(tool_name: str, context: str = "") -> dict:
            return _pred.next_actions(tool_name=tool_name, context=context) or {}

        def mcp_learn(event: dict) -> None:
            try:
                _ctx.learn(event); _perf.record(event)
            except Exception:
                pass
    except Exception:
        # fall back silently, keep the stubs above
        pass
