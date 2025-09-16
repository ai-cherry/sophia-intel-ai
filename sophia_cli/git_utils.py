from __future__ import annotations
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


def run(cmd: List[str], cwd: Path | None = None, check: bool = True) -> Tuple[int, str, str]:
    p = subprocess.Popen(cmd, cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{err}")
    return p.returncode, out, err


def ensure_repo() -> None:
    run(["git", "rev-parse", "--is-inside-work-tree"])  # raises if not a git repo


def create_branch(name: str) -> None:
    run(["git", "checkout", "-b", name])


def short_id(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-")
    return s[:8] if s else "change"


def changed_paths_from_patch(patch_path: Path) -> List[Path]:
    files: list[Path] = []
    for line in patch_path.read_text(errors="ignore").splitlines():
        if line.startswith("+++ b/"):
            files.append(Path(line[6:]))
    return files


def git_apply_and_commit(patch_path: Path, message: str) -> None:
    run(["git", "apply", "--index", "--whitespace=nowarn", str(patch_path)])
    run(["git", "commit", "-m", message])

