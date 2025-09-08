"""
Basic tool implementations for agent system.
These are simplified tools that work with the current agno version.
"""

import os
import subprocess
from typing import Any


def search_code(query: str, path: str = ".") -> dict[str, Any]:
    """Search for code patterns."""
    try:
        result = subprocess.run(
            ["grep", "-r", "--include=*.py", query, path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {
            "query": query,
            "matches": result.stdout.split("\n")[:10],  # First 10 matches
            "count": len(result.stdout.split("\n")) if result.stdout else 0,
        }
    except Exception as e:
        return {"query": query, "error": str(e), "matches": [], "count": 0}


def read_file(file_path: str) -> dict[str, Any]:
    """Read a file safely."""
    try:
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        return {
            "file_path": file_path,
            "content": content[:2000],  # Limit content size
            "size": len(content),
            "lines": len(content.split("\n")),
        }
    except Exception as e:
        return {"file_path": file_path, "error": str(e)}


def write_file(file_path: str, content: str) -> dict[str, Any]:
    """Write to a file safely."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "file_path": file_path,
            "success": True,
            "bytes_written": len(content.encode("utf-8")),
        }
    except Exception as e:
        return {"file_path": file_path, "error": str(e), "success": False}


def list_directory(dir_path: str = ".") -> dict[str, Any]:
    """List directory contents."""
    try:
        if not os.path.exists(dir_path):
            return {"error": f"Directory not found: {dir_path}"}

        items = []
        for item in os.listdir(dir_path):
            full_path = os.path.join(dir_path, item)
            items.append(
                {
                    "name": item,
                    "type": "directory" if os.path.isdir(full_path) else "file",
                    "size": (
                        os.path.getsize(full_path) if os.path.isfile(full_path) else 0
                    ),
                }
            )

        return {
            "directory": dir_path,
            "items": items[:20],  # Limit to 20 items
            "total": len(items),
        }
    except Exception as e:
        return {"directory": dir_path, "error": str(e)}


def git_status() -> dict[str, Any]:
    """Get git status."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10
        )

        files = []
        for line in result.stdout.split("\n"):
            if line.strip():
                status = line[:2]
                filename = line[3:]
                files.append({"status": status, "file": filename})

        return {"files": files, "clean": len(files) == 0}
    except Exception as e:
        return {"error": str(e), "files": [], "clean": False}


def run_tests(test_path: str = "tests/") -> dict[str, Any]:
    """Run tests safely."""
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", test_path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        return {
            "exit_code": result.returncode,
            "output": result.stdout[-1000:],  # Last 1000 chars
            "errors": result.stderr[-1000:] if result.stderr else "",
            "passed": result.returncode == 0,
        }
    except Exception as e:
        return {"error": str(e), "passed": False}


# Create simple tool classes for compatibility
class CodeSearch:
    """Code search tool."""

    def __call__(self, query: str, path: str = "."):
        return search_code(query, path)


class ReadFile:
    """File reading tool."""

    def __call__(self, file_path: str):
        return read_file(file_path)


class WriteFile:
    """File writing tool."""

    def __call__(self, file_path: str, content: str):
        return write_file(file_path, content)


class ListDirectory:
    """Directory listing tool."""

    def __call__(self, dir_path: str = "."):
        return list_directory(dir_path)


class GitStatus:
    """Git status tool."""

    def __call__(self):
        return git_status()


class GitDiff:
    """Git diff tool."""

    def __call__(self, file_path: str = None):
        try:
            cmd = ["git", "diff"]
            if file_path:
                cmd.append(file_path)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return {"diff": result.stdout, "file": file_path or "all"}
        except Exception as e:
            return {"error": str(e)}


class GitCommit:
    """Git commit tool."""

    def __call__(self, message: str):
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }
        except Exception as e:
            return {"error": str(e), "success": False}


class GitAdd:
    """Git add tool."""

    def __call__(self, file_path: str):
        try:
            result = subprocess.run(
                ["git", "add", file_path], capture_output=True, text=True, timeout=10
            )
            return {"success": result.returncode == 0, "file": file_path}
        except Exception as e:
            return {"error": str(e), "success": False}


class RunTests:
    """Test runner tool."""

    def __call__(self, test_path: str = "tests/"):
        return run_tests(test_path)


class RunTypeCheck:
    """Type checker tool."""

    def __call__(self, file_path: str = "."):
        try:
            result = subprocess.run(
                ["python3", "-m", "mypy", file_path],
                capture_output=True,
                text=True,
                timeout=20,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
            }
        except Exception as e:
            return {"error": str(e), "success": False}


class RunLint:
    """Linting tool."""

    def __call__(self, file_path: str = "."):
        try:
            result = subprocess.run(
                ["python3", "-m", "flake8", file_path],
                capture_output=True,
                text=True,
                timeout=20,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "issues": result.stdout.split("\n") if result.stdout else [],
            }
        except Exception as e:
            return {"error": str(e), "success": False}


class FormatCode:
    """Code formatter tool."""

    def __call__(self, file_path: str):
        try:
            result = subprocess.run(
                ["python3", "-m", "black", file_path],
                capture_output=True,
                text=True,
                timeout=20,
            )
            return {
                "success": result.returncode == 0,
                "formatted": result.returncode == 0,
                "output": result.stdout,
            }
        except Exception as e:
            return {"error": str(e), "success": False}
