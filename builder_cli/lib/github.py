"""
GitHub integration for CLI agents with push capabilities.
Provides safe, controlled Git operations for automated agents.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class GitHubAgent:
    """GitHub operations for CLI agents with safety controls."""
    
    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path.cwd()
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.safe_mode = os.getenv("GIT_SAFE_MODE", "true").lower() == "true"
        self.allow_push = os.getenv("GIT_ALLOW_PUSH", "false").lower() == "true"
        
    def _run_git(self, *args, check=True) -> Tuple[int, str, str]:
        """Run a git command safely."""
        cmd = ["git"] + list(args)
        logger.debug(f"Running git command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if check and result.returncode != 0:
                logger.error(f"Git command failed: {result.stderr}")
                
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timed out: {' '.join(cmd)}")
            return 1, "", "Command timed out"
        except Exception as e:
            logger.error(f"Git command error: {e}")
            return 1, "", str(e)
    
    def status(self) -> Dict[str, Any]:
        """Get repository status."""
        code, stdout, _ = self._run_git("status", "--porcelain")
        
        if code != 0:
            return {"error": "Failed to get status"}
        
        files = {
            "modified": [],
            "added": [],
            "deleted": [],
            "untracked": []
        }
        
        for line in stdout.strip().split("\n"):
            if not line:
                continue
                
            status = line[:2]
            filepath = line[3:]
            
            if status == "??":
                files["untracked"].append(filepath)
            elif "M" in status:
                files["modified"].append(filepath)
            elif "A" in status:
                files["added"].append(filepath)
            elif "D" in status:
                files["deleted"].append(filepath)
        
        # Get branch info
        _, branch_out, _ = self._run_git("branch", "--show-current")
        current_branch = branch_out.strip()
        
        # Get remote info
        _, remote_out, _ = self._run_git("remote", "-v")
        remotes = {}
        for line in remote_out.strip().split("\n"):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    remotes[parts[0]] = parts[1]
        
        return {
            "branch": current_branch,
            "files": files,
            "remotes": remotes,
            "clean": all(len(v) == 0 for v in files.values())
        }
    
    def create_branch(self, branch_name: str, from_branch: str = "main") -> bool:
        """Create a new branch."""
        if self.safe_mode:
            logger.info(f"Would create branch: {branch_name} from {from_branch}")
            return True
        
        # Checkout base branch
        code, _, _ = self._run_git("checkout", from_branch)
        if code != 0:
            return False
        
        # Pull latest
        code, _, _ = self._run_git("pull", "origin", from_branch, check=False)
        
        # Create and checkout new branch
        code, _, _ = self._run_git("checkout", "-b", branch_name)
        return code == 0
    
    def add_files(self, files: List[str] = None) -> bool:
        """Stage files for commit."""
        if files is None:
            files = ["."]
        
        for file in files:
            code, _, _ = self._run_git("add", file)
            if code != 0:
                return False
        
        return True
    
    def commit(self, message: str, co_author: bool = True) -> bool:
        """Create a commit with optional co-author."""
        if not message:
            logger.error("Empty commit message")
            return False
        
        # Add co-author footer if requested
        if co_author:
            message += "\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        
        if self.safe_mode:
            logger.info(f"Would commit with message:\n{message}")
            return True
        
        code, _, _ = self._run_git("commit", "-m", message)
        return code == 0
    
    def push(self, branch: str = None, force: bool = False) -> bool:
        """Push to remote repository."""
        if not self.allow_push:
            logger.warning("Push disabled (set GIT_ALLOW_PUSH=true to enable)")
            return False
        
        if self.safe_mode:
            logger.info(f"Would push branch: {branch or 'current'}")
            return True
        
        args = ["push", "origin"]
        if branch:
            args.append(branch)
        if force:
            args.append("--force-with-lease")
        
        code, _, _ = self._run_git(*args)
        return code == 0
    
    def create_pr(self, title: str, body: str, base: str = "main") -> Optional[str]:
        """Create a pull request using GitHub CLI."""
        if self.safe_mode:
            logger.info(f"Would create PR: {title}")
            return "mock-pr-url"
        
        # Check if gh CLI is available
        try:
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
        except:
            logger.error("GitHub CLI (gh) not available")
            return None
        
        # Create PR
        cmd = [
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--base", base
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Extract PR URL from output
                for line in result.stdout.split("\n"):
                    if "github.com" in line:
                        return line.strip()
            
            logger.error(f"Failed to create PR: {result.stderr}")
            return None
            
        except Exception as e:
            logger.error(f"PR creation error: {e}")
            return None
    
    def safe_commit_and_push(self, 
                            message: str,
                            files: List[str] = None,
                            branch: str = None,
                            create_pr: bool = False) -> Dict[str, Any]:
        """Safe workflow for committing and pushing changes."""
        result = {
            "success": False,
            "branch": branch,
            "committed": False,
            "pushed": False,
            "pr_url": None
        }
        
        try:
            # Get current status
            status = self.status()
            if status.get("clean"):
                logger.info("No changes to commit")
                result["success"] = True
                return result
            
            # Create branch if specified
            if branch and branch != status.get("branch"):
                if not self.create_branch(branch):
                    logger.error(f"Failed to create branch: {branch}")
                    return result
                result["branch"] = branch
            
            # Stage files
            if not self.add_files(files):
                logger.error("Failed to stage files")
                return result
            
            # Commit
            if not self.commit(message):
                logger.error("Failed to commit")
                return result
            result["committed"] = True
            
            # Push if allowed
            if self.allow_push:
                if not self.push(branch):
                    logger.error("Failed to push")
                    return result
                result["pushed"] = True
                
                # Create PR if requested
                if create_pr and branch and branch != "main":
                    pr_url = self.create_pr(
                        title=message.split("\n")[0],
                        body=message,
                        base="main"
                    )
                    if pr_url:
                        result["pr_url"] = pr_url
            
            result["success"] = True
            return result
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            result["error"] = str(e)
            return result


class GitHubIntegration:
    """High-level GitHub integration for agents."""
    
    def __init__(self):
        self.agent = GitHubAgent()
        
    def ensure_clean_state(self) -> bool:
        """Ensure repository is in a clean state."""
        status = self.agent.status()
        
        if status.get("clean"):
            return True
        
        # Optionally stash changes
        if os.getenv("GIT_AUTO_STASH", "false").lower() == "true":
            logger.info("Stashing uncommitted changes")
            code, _, _ = self.agent._run_git("stash", "push", "-m", f"Auto-stash {datetime.now()}")
            return code == 0
        
        logger.warning("Repository has uncommitted changes")
        return False
    
    def commit_agent_work(self, 
                         task_type: str,
                         changes_summary: str,
                         detailed_changes: List[str] = None) -> Dict[str, Any]:
        """Commit work done by an agent."""
        
        # Generate commit message
        message = f"feat({task_type}): {changes_summary}\n\n"
        
        if detailed_changes:
            message += "Changes:\n"
            for change in detailed_changes:
                message += f"- {change}\n"
        
        # Use feature branch for non-trivial changes
        branch = None
        if task_type != "fix" and not self.agent.safe_mode:
            branch = f"agent/{task_type}/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        return self.agent.safe_commit_and_push(
            message=message,
            branch=branch,
            create_pr=bool(branch)
        )
    
    def get_recent_commits(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent commit history."""
        code, stdout, _ = self.agent._run_git(
            "log", 
            f"-{limit}", 
            "--pretty=format:%H|%an|%ae|%at|%s"
        )
        
        if code != 0:
            return []
        
        commits = []
        for line in stdout.strip().split("\n"):
            if line:
                parts = line.split("|")
                if len(parts) >= 5:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "timestamp": parts[3],
                        "message": parts[4]
                    })
        
        return commits


# Agent helper functions
def setup_git_for_agents():
    """Setup Git configuration for agents."""
    config = {
        "user.name": os.getenv("GIT_USER_NAME", "Sophia Agent"),
        "user.email": os.getenv("GIT_USER_EMAIL", "agent@sophia-intel.ai"),
        "pull.rebase": "false",
        "push.autoSetupRemote": "true"
    }
    
    agent = GitHubAgent()
    for key, value in config.items():
        agent._run_git("config", key, value)
    
    logger.info("Git configured for agents")
    return True


def can_agent_push() -> bool:
    """Check if agent has push permissions."""
    return (
        os.getenv("GIT_ALLOW_PUSH", "false").lower() == "true" and
        (os.getenv("GITHUB_TOKEN") or os.path.exists(os.path.expanduser("~/.ssh/id_rsa")))
    )