#!/usr/bin/env python3
import os
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def remove_artifacts():
    patterns = ["*.tmp", "*.log"]
    names = {"test_push.txt", "LAST_UPDATE.txt"}
    for path in ROOT.rglob("*"):
        try:
            if path.is_file():
                if path.name in names:
                    path.unlink(missing_ok=True)
                    continue
                for pat in patterns:
                    if path.match(pat):
                        path.unlink(missing_ok=True)
                        break
        except Exception:
            continue


def remove_caches():
    for d in [d for d in ROOT.rglob("__pycache__") if d.is_dir()] + [d for d in ROOT.rglob(".pytest_cache") if d.is_dir()]:
        try:
            shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass


def fix_bare_except_py():
    for py in ROOT.rglob("*.py"):
        try:
            text = py.read_text()
            new = re.sub(r"except\s*:\s*", "except Exception:", text)
            if new != text:
                py.write_text(new)
        except Exception:
            continue


def clean_ts_console_and_any():
    ui_src = ROOT / "agent-ui" / "src"
    if not ui_src.exists():
        return
    for tsfile in ui_src.rglob("*.ts*"):
        try:
            text = tsfile.read_text()
            # Remove console.log lines (simple heuristic)
            lines = text.splitlines()
            lines = [ln for ln in lines if "console.log(" not in ln]
            cleaned = "\n".join(lines)
            # Replace ': any' with ': unknown' (safe-ish minimal change)
            cleaned2 = re.sub(r":\s*any(\b)", r": unknown\1", cleaned)
            if cleaned2 != text:
                tsfile.write_text(cleaned2)
        except Exception:
            continue


if __name__ == "__main__":
    remove_artifacts()
    remove_caches()
    fix_bare_except_py()
    clean_ts_console_and_any()
    print("✅ Final cleanup complete")

