"""Enhanced tools with error handling, safety checks, and validation."""
import asyncio
import hashlib
import json
import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.ai_logger import logger


# Base Tool class
class Tool:
    """Base tool class."""
    def __init__(self, name="", description="", inputs=None, output=None):
        self.name = name
        self.description = description
        self.inputs = inputs or {}
        self.output = output

logger = logging.getLogger(__name__)

@dataclass
class ToolValidation:
    """Validation rules for tool inputs."""
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list[str] = None
    forbidden_paths: list[str] = None
    require_confirmation: bool = False

class SafetyChecker:
    """Safety validation for tool operations."""

    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',
        r'sudo\s+rm',
        r'format\s+c:',
        r'del\s+/s\s+/q',
        r'DROP\s+DATABASE',
        r'DELETE\s+FROM.*WHERE\s+1=1'
    ]

    SENSITIVE_FILES = [
        '.env',
        '.aws',
        '.ssh',
        'credentials',
        'secrets',
        'private_key'
    ]

    @staticmethod
    def is_safe_path(path: Path) -> bool:
        """Check if path is safe to access."""
        try:
            # Resolve to absolute path
            abs_path = path.resolve()

            # Check for sensitive files
            for sensitive in SafetyChecker.SENSITIVE_FILES:
                if sensitive in str(abs_path).lower():
                    logger.warning(f"Blocked access to sensitive path: {abs_path}")
                    return False

            # Ensure within workspace
            workspace = Path.cwd()
            if not str(abs_path).startswith(str(workspace)):
                logger.warning(f"Path outside workspace: {abs_path}")
                return False

            return True

        except Exception as e:
            logger.error(f"Path safety check failed: {e}")
            return False

    @staticmethod
    def is_safe_command(command: str) -> bool:
        """Check if command is safe to execute."""
        import re

        for pattern in SafetyChecker.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                logger.warning(f"Blocked dangerous command: {command}")
                return False

        return True

class EnhancedReadFile(Tool):
    """Enhanced file reading with validation and caching."""

    def __init__(self):
        super().__init__(
            name="enhanced_read_file",
            description="Read file with validation and caching",
            inputs={"filepath": str, "encoding": str},
            output=str
        )
        self._cache = {}
        self._validation = ToolValidation()

    async def run(self, filepath: str, encoding: str = "utf-8") -> str:
        """Read file with enhanced safety and caching."""
        path = Path(filepath)

        # Safety check
        if not SafetyChecker.is_safe_path(path):
            raise ValueError(f"Unsafe path: {filepath}")

        # Check file exists
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Check file size
        file_size = path.stat().st_size
        if file_size > self._validation.max_file_size:
            raise ValueError(f"File too large: {file_size} bytes (max: {self._validation.max_file_size})")

        # Check cache
        cache_key = f"{filepath}:{path.stat().st_mtime}"
        if cache_key in self._cache:
            logger.info(f"Cache hit for {filepath}")
            return self._cache[cache_key]

        try:
            # Read file
            content = path.read_text(encoding=encoding)

            # Update cache
            self._cache[cache_key] = content

            # Limit cache size
            if len(self._cache) > 100:
                # Remove oldest entries
                oldest = sorted(self._cache.keys())[:50]
                for key in oldest:
                    del self._cache[key]

            return content

        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            raise

class EnhancedWriteFile(Tool):
    """Enhanced file writing with backup and validation."""

    def __init__(self):
        super().__init__(
            name="enhanced_write_file",
            description="Write file with backup and validation",
            inputs={"filepath": str, "content": str, "encoding": str, "backup": bool},
            output=dict[str, Any]
        )
        self._validation = ToolValidation()

    async def run(
        self,
        filepath: str,
        content: str,
        encoding: str = "utf-8",
        backup: bool = True
    ) -> dict[str, Any]:
        """Write file with enhanced safety and backup."""
        path = Path(filepath)

        # Safety check
        if not SafetyChecker.is_safe_path(path):
            raise ValueError(f"Unsafe path: {filepath}")

        # Create backup if file exists
        backup_path = None
        if backup and path.exists():
            backup_path = path.with_suffix(f"{path.suffix}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            try:
                backup_path.write_text(path.read_text(encoding=encoding), encoding=encoding)
                logger.info(f"Created backup: {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")

        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            path.write_text(content, encoding=encoding)

            return {
                "success": True,
                "filepath": str(path),
                "size": len(content),
                "backup": str(backup_path) if backup_path else None,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to write {filepath}: {e}")

            # Attempt to restore backup
            if backup_path and backup_path.exists():
                try:
                    path.write_text(backup_path.read_text(encoding=encoding), encoding=encoding)
                    logger.info(f"Restored from backup: {backup_path}")
                except Exception as restore_error:
                    logger.error(f"Failed to restore backup: {restore_error}")

            raise

class EnhancedCodeSearch(Tool):
    """Enhanced code search with intelligent ranking."""

    def __init__(self):
        super().__init__(
            name="enhanced_code_search",
            description="Search code with advanced patterns and ranking",
            inputs={"query": str, "path": str, "file_type": str, "context_lines": int},
            output=list[dict[str, Any]]
        )
        self._result_cache = {}

    async def run(
        self,
        query: str,
        path: str = ".",
        file_type: str | None = None,
        context_lines: int = 2
    ) -> list[dict[str, Any]]:
        """Search code with enhanced features."""
        search_path = Path(path)

        # Safety check
        if not SafetyChecker.is_safe_path(search_path):
            raise ValueError(f"Unsafe path: {path}")

        # Check cache
        cache_key = hashlib.md5(f"{query}:{path}:{file_type}".encode()).hexdigest()
        if cache_key in self._result_cache:
            cache_entry = self._result_cache[cache_key]
            if (datetime.now() - cache_entry["timestamp"]).seconds < 300:  # 5 min cache
                logger.info(f"Cache hit for search: {query}")
                return cache_entry["results"]

        try:
            # Build ripgrep command
            cmd = ["rg", "--json", "-C", str(context_lines), query, str(search_path)]

            if file_type:
                cmd.extend(["-t", file_type])

            # Execute search
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            # Parse results
            matches = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("type") == "match":
                            match_info = {
                                "file": data["data"]["path"]["text"],
                                "line": data["data"]["line_number"],
                                "text": data["data"]["lines"]["text"],
                                "score": self._calculate_relevance(query, data)
                            }
                            matches.append(match_info)
                    except json.JSONDecodeError:
                        continue

            # Sort by relevance
            matches.sort(key=lambda x: x["score"], reverse=True)

            # Cache results
            self._result_cache[cache_key] = {
                "results": matches[:50],  # Limit to top 50
                "timestamp": datetime.now()
            }

            # Clean old cache entries
            if len(self._result_cache) > 100:
                oldest = sorted(
                    self._result_cache.items(),
                    key=lambda x: x[1]["timestamp"]
                )[:50]
                for key, _ in oldest:
                    del self._result_cache[key]

            return matches[:50]

        except subprocess.TimeoutExpired:
            logger.error(f"Search timeout for query: {query}")
            raise TimeoutError("Search operation timed out")
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def _calculate_relevance(self, query: str, match_data: dict) -> float:
        """Calculate relevance score for search result."""
        score = 1.0

        # Exact match bonus
        if query.lower() in match_data["data"]["lines"]["text"].lower():
            score += 2.0

        # File path relevance
        filepath = match_data["data"]["path"]["text"]
        if "test" in filepath.lower():
            score *= 0.8  # Deprioritize test files
        if "vendor" in filepath.lower() or "node_modules" in filepath.lower():
            score *= 0.5  # Deprioritize dependencies

        # Recent file bonus (if we had git info)
        # This would check git log for recent modifications

        return score

class EnhancedGitOps(Tool):
    """Enhanced Git operations with safety and validation."""

    def __init__(self):
        super().__init__(
            name="enhanced_git_ops",
            description="Safe Git operations with validation",
            inputs={"operation": str, "args": dict[str, Any]},
            output=dict[str, Any]
        )

    async def run(self, operation: str, args: dict[str, Any] = None) -> dict[str, Any]:
        """Execute Git operation with safety checks."""
        args = args or {}

        # Validate operation
        allowed_ops = ["status", "diff", "add", "commit", "log", "branch", "checkout"]
        if operation not in allowed_ops:
            raise ValueError(f"Operation not allowed: {operation}")

        try:
            if operation == "status":
                return await self._git_status()
            elif operation == "diff":
                return await self._git_diff(args.get("cached", False))
            elif operation == "add":
                return await self._git_add(args.get("files", []))
            elif operation == "commit":
                return await self._git_commit(args.get("message", ""))
            elif operation == "log":
                return await self._git_log(args.get("limit", 10))
            elif operation == "branch":
                return await self._git_branch()
            elif operation == "checkout":
                return await self._git_checkout(args.get("branch", ""))
            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            logger.error(f"Git operation failed: {operation} - {e}")
            raise

    async def _git_status(self) -> dict[str, Any]:
        """Get git status."""
        result = subprocess.run(
            ["git", "status", "--porcelain", "-b"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Parse status
        lines = result.stdout.strip().split('\n')
        branch = lines[0].replace("## ", "") if lines else "unknown"

        files = {
            "modified": [],
            "added": [],
            "deleted": [],
            "untracked": []
        }

        for line in lines[1:]:
            if line.startswith(" M"):
                files["modified"].append(line[3:])
            elif line.startswith("A "):
                files["added"].append(line[3:])
            elif line.startswith(" D"):
                files["deleted"].append(line[3:])
            elif line.startswith("??"):
                files["untracked"].append(line[3:])

        return {
            "branch": branch,
            "files": files,
            "clean": not any(files.values())
        }

    async def _git_diff(self, cached: bool = False) -> dict[str, Any]:
        """Get git diff."""
        cmd = ["git", "diff", "--stat"]
        if cached:
            cmd.append("--cached")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        return {
            "stats": result.stdout,
            "cached": cached
        }

    async def _git_add(self, files: list[str]) -> dict[str, Any]:
        """Add files to git."""
        if not files:
            raise ValueError("No files specified")

        # Validate file paths
        for filepath in files:
            path = Path(filepath)
            if not SafetyChecker.is_safe_path(path):
                raise ValueError(f"Unsafe path: {filepath}")

        result = subprocess.run(
            ["git", "add"] + files,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise RuntimeError(f"Git add failed: {result.stderr}")

        return {
            "added": files,
            "success": True
        }

    async def _git_commit(self, message: str) -> dict[str, Any]:
        """Create git commit."""
        if not message:
            raise ValueError("Commit message required")

        # Validate message
        if len(message) < 3:
            raise ValueError("Commit message too short")
        if len(message) > 500:
            raise ValueError("Commit message too long")

        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise RuntimeError(f"Git commit failed: {result.stderr}")

        # Extract commit hash
        import re
        match = re.search(r'\[[\w\s]+\s+([\w]+)\]', result.stdout)
        commit_hash = match.group(1) if match else "unknown"

        return {
            "commit": commit_hash,
            "message": message,
            "output": result.stdout
        }

    async def _git_log(self, limit: int = 10) -> dict[str, Any]:
        """Get git log."""
        result = subprocess.run(
            ["git", "log", f"--max-count={limit}", "--oneline"],
            capture_output=True,
            text=True,
            timeout=10
        )

        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(' ', 1)
                commits.append({
                    "hash": parts[0],
                    "message": parts[1] if len(parts) > 1 else ""
                })

        return {"commits": commits, "count": len(commits)}

    async def _git_branch(self) -> dict[str, Any]:
        """List git branches."""
        result = subprocess.run(
            ["git", "branch", "-a"],
            capture_output=True,
            text=True,
            timeout=10
        )

        branches = {"local": [], "remote": [], "current": None}

        for line in result.stdout.strip().split('\n'):
            if line.startswith("* "):
                branches["current"] = line[2:].strip()
                branches["local"].append(line[2:].strip())
            elif line.startswith("  remotes/"):
                branches["remote"].append(line.replace("  remotes/", "").strip())
            elif line.strip():
                branches["local"].append(line.strip())

        return branches

    async def _git_checkout(self, branch: str) -> dict[str, Any]:
        """Checkout git branch."""
        if not branch:
            raise ValueError("Branch name required")

        # Validate branch name
        if not re.match(r'^[\w\-\./_]+$', branch):
            raise ValueError(f"Invalid branch name: {branch}")

        result = subprocess.run(
            ["git", "checkout", branch],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise RuntimeError(f"Git checkout failed: {result.stderr}")

        return {
            "branch": branch,
            "output": result.stdout
        }

class EnhancedTestRunner(Tool):
    """Enhanced test runner with detailed reporting."""

    def __init__(self):
        super().__init__(
            name="enhanced_test_runner",
            description="Run tests with detailed reporting",
            inputs={"path": str, "pattern": str, "verbose": bool},
            output=dict[str, Any]
        )

    async def run(
        self,
        path: str = ".",
        pattern: str = None,
        verbose: bool = False
    ) -> dict[str, Any]:
        """Run tests with enhanced reporting."""
        test_path = Path(path)

        # Safety check
        if not SafetyChecker.is_safe_path(test_path):
            raise ValueError(f"Unsafe path: {path}")

        # Detect test framework
        framework = self._detect_framework(test_path)

        if framework == "pytest":
            return await self._run_pytest(test_path, pattern, verbose)
        elif framework == "unittest":
            return await self._run_unittest(test_path, pattern, verbose)
        else:
            raise ValueError(f"No test framework detected in {path}")

    def _detect_framework(self, path: Path) -> str | None:
        """Detect test framework."""
        # Check for pytest
        if (path / "pytest.ini").exists() or (path / "pyproject.toml").exists():
            return "pytest"

        # Check for unittest
        test_files = list(path.glob("**/test_*.py")) + list(path.glob("**/*_test.py"))
        if test_files:
            return "unittest"

        return None

    async def _run_pytest(
        self,
        path: Path,
        pattern: str | None,
        verbose: bool
    ) -> dict[str, Any]:
        """Run pytest tests."""
        cmd = ["python", "-m", "pytest", str(path), "--json-report", "--json-report-file=/tmp/pytest_report.json"]

        if pattern:
            cmd.extend(["-k", pattern])

        if verbose:
            cmd.append("-v")

        start_time = datetime.now()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        duration = (datetime.now() - start_time).total_seconds()

        # Parse JSON report if available
        report_path = Path("/tmp/pytest_report.json")
        if report_path.exists():
            with open(report_path) as f:
                report = json.load(f)

            return {
                "framework": "pytest",
                "passed": report["summary"]["passed"],
                "failed": report["summary"]["failed"],
                "skipped": report["summary"].get("skipped", 0),
                "duration": duration,
                "output": result.stdout,
                "success": result.returncode == 0
            }
        else:
            # Fallback to parsing output
            return {
                "framework": "pytest",
                "output": result.stdout,
                "errors": result.stderr,
                "duration": duration,
                "success": result.returncode == 0
            }

    async def _run_unittest(
        self,
        path: Path,
        pattern: str | None,
        verbose: bool
    ) -> dict[str, Any]:
        """Run unittest tests."""
        cmd = ["python", "-m", "unittest", "discover", "-s", str(path)]

        if pattern:
            cmd.extend(["-p", f"*{pattern}*.py"])

        if verbose:
            cmd.append("-v")

        start_time = datetime.now()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        duration = (datetime.now() - start_time).total_seconds()

        # Parse output for results
        import re
        match = re.search(r'Ran (\d+) tests? in ([\d.]+)s', result.stderr)
        if match:
            test_count = int(match.group(1))
        else:
            test_count = 0

        return {
            "framework": "unittest",
            "tests_run": test_count,
            "output": result.stdout,
            "errors": result.stderr,
            "duration": duration,
            "success": result.returncode == 0
        }

# Tool registry
ENHANCED_TOOLS = {
    "read_file": EnhancedReadFile(),
    "write_file": EnhancedWriteFile(),
    "code_search": EnhancedCodeSearch(),
    "git_ops": EnhancedGitOps(),
    "test_runner": EnhancedTestRunner()
}

async def main():
    """Test enhanced tools."""
    # Test read file
    reader = EnhancedReadFile()
    content = await reader.run("README.md")
    logger.info(f"Read {len(content)} characters")

    # Test code search
    searcher = EnhancedCodeSearch()
    results = await searcher.run("async def", file_type="py")
    logger.info(f"Found {len(results)} matches")

    # Test git status
    git = EnhancedGitOps()
    status = await git.run("status")
    logger.info(f"Git status: {status}")

if __name__ == "__main__":
    asyncio.run(main())
