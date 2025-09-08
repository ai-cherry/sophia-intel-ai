import os
import re
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/repo", tags=["repository"])

# Security constants
ROOT_DIR = Path(os.getenv("PROJECT_ROOT", os.getcwd()))
EXCLUDED_PATHS = [".git", ".env", "*.key", "*.pem", "__pycache__"]
MAX_FILE_SIZE = 1024 * 1024  # 1MB
MAX_TREE_DEPTH = 5
MAX_SEARCH_RESULTS = 100


def validate_path(path: str) -> str:
    """Validate and sanitize path to prevent directory traversal"""
    path = os.path.normpath(path)
    if not path.startswith(str(ROOT_DIR)):
        raise HTTPException(status_code=403, detail="Path outside project root")
    for pattern in EXCLUDED_PATHS:
        if re.search(pattern, path):
            raise HTTPException(status_code=403, detail="Access to excluded path")
    return path


@router.get("/tree")
async def get_tree(
    path: str = ".",
    depth: int = 3,
    include_hidden: bool = False,
    include_git_status: bool = True,
):
    path = validate_path(path)
    results = []
    for root, dirs, files in os.walk(path, topdown=True):
        if depth > 0 and len(root[len(str(ROOT_DIR)) :] // os.sep) > depth:
            break
        if not include_hidden:
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            files = [f for f in files if not f.startswith(".")]
        dir_info = {
            "path": str(Path(root).relative_to(ROOT_DIR)),
            "type": "directory",
            "children": [],
        }
        for f in files:
            file_path = Path(root) / f
            if file_path.stat().st_size > MAX_FILE_SIZE:
                continue
            file_info = {
                "name": f,
                "type": "file",
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime,
                "git_status": "clean",
            }
            if include_git_status:
                try:
                    status = (
                        subprocess.check_output(
                            ["git", "status", "--porcelain", str(file_path)],
                            cwd=ROOT_DIR,
                        )
                        .decode()
                        .strip()
                    )
                    file_info["git_status"] = status.split()[0] if status else "clean"
                except Exception:file_info["git_status"] = "unknown"
            dir_info["children"].append(file_info)
        results.append(dir_info)
    return results


# Additional endpoints as per ROO PROMPT (file, search, analyze, git status, diff)
