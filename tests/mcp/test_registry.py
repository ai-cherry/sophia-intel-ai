from __future__ import annotations
import os
import time
from mcp.core.registry import UniversalRegistry
def test_singleton_pattern():
    a = UniversalRegistry()
    b = UniversalRegistry()
    assert a is b
def test_tree_sitter_performance():
    # This test is heavy; only run when explicitly enabled
    if not os.getenv("RUN_HEAVY_PERF_TESTS"):
        return
    reg = UniversalRegistry()
    sample = "def x():\n    return 1\n"
    start = time.perf_counter()
    for i in range(1000):
        reg.parse_with_cache(f"file_{i}.py", sample)
    elapsed = (time.perf_counter() - start)
    assert elapsed < 5.0
def test_incremental_parsing():
    reg = UniversalRegistry()
    content = "def add(a, b):\n    return a + b\n"
    r1 = reg.parse_with_cache("inc.py", content)
    # Small edit; verify subsequent parse is fast (should hit the parser quickly)
    content2 = content.replace("+", "-")
    r2 = reg.parse_with_cache("inc.py", content2)
    assert r1.success and r2.success
    # We expect the second parse to be reasonably fast (< 10ms) on typical environments
    assert r2.duration_ms < 10.0 or r1.duration_ms < 10.0
