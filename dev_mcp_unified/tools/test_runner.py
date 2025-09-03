from __future__ import annotations
import subprocess
from typing import List


def run_tests(path: str = ".") -> List[str]:
    try:
        out = subprocess.run(["pytest", "-q", path], capture_output=True, text=True, timeout=120)
        return out.stdout.splitlines()[-50:]
    except Exception as e:
        return [f"test runner error: {e}"]

