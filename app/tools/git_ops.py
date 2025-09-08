import subprocess

from agno import Tool


class GitStatus(Tool):
    """Tool for checking git status."""

    name = "git_status"
    description = "Check the current git status of the repository"
    parameters = {"type": "object", "properties": {}, "required": []}

    async def run(self) -> str:
        """Get git status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )

            if not result.stdout:
                return "Working directory is clean"

            return f"Git status:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            return f"Git error: {e.stderr}"
        except Exception as e:
            return f"Error checking git status: {str(e)}"


class GitDiff(Tool):
    """Tool for showing git differences."""

    name = "git_diff"
    description = "Show git differences for staged or unstaged changes"
    parameters = {
        "type": "object",
        "properties": {
            "staged": {
                "type": "boolean",
                "description": "Show staged changes instead of unstaged",
                "default": False,
            }
        },
        "required": [],
    }

    async def run(self, staged: bool = False) -> str:
        """Get git diff."""
        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--cached")

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if not result.stdout:
                return f"No {'staged' if staged else 'unstaged'} changes"

            return f"Git diff ({'staged' if staged else 'unstaged'}):\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            return f"Git error: {e.stderr}"
        except Exception as e:
            return f"Error getting git diff: {str(e)}"


class GitCommit(Tool):
    """Tool for creating git commits."""

    name = "git_commit"
    description = "Create a git commit with the staged changes"
    parameters = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "The commit message"}
        },
        "required": ["message"],
    }

    async def run(self, message: str) -> str:
        """Create a git commit."""
        try:
            # First check if there are staged changes
            status = subprocess.run(
                ["git", "diff", "--cached", "--stat"], capture_output=True, text=True
            )

            if not status.stdout:
                return "No staged changes to commit. Use 'git add' first."

            # Create the commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                check=True,
            )

            return f"Commit created successfully:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            return f"Git error: {e.stderr}"
        except Exception as e:
            return f"Error creating commit: {str(e)}"


class GitAdd(Tool):
    """Tool for staging files for commit."""

    name = "git_add"
    description = "Stage files for commit"
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "Path to file or directory to stage (use '.' for all)",
                "default": ".",
            }
        },
        "required": [],
    }

    async def run(self, filepath: str = ".") -> str:
        """Stage files for commit."""
        try:
            subprocess.run(
                ["git", "add", filepath], capture_output=True, text=True, check=True
            )

            return f"Successfully staged: {filepath}"
        except subprocess.CalledProcessError as e:
            return f"Git error: {e.stderr}"
        except Exception as e:
            return f"Error staging files: {str(e)}"
