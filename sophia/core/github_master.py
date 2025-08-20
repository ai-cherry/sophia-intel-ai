"""
SOPHIA V4 GitHub Master
Manages GitHub operations: branch creation, commits, pushes, PRs.
Uses personal access token stored in the environment (GITHUB_TOKEN).
"""

import os
import logging
import base64
from dataclasses import dataclass
from typing import Optional, Dict, List, Any

import requests

logger = logging.getLogger(__name__)

@dataclass
class GitHubRepoInfo:
    """Information about a GitHub repository."""
    owner: str
    repo: str
    default_branch: str = "main"

@dataclass
class GitHubCommitInfo:
    """Information about a GitHub commit."""
    sha: str
    message: str
    author: str
    date: str
    url: str

@dataclass
class GitHubPRInfo:
    """Information about a GitHub pull request."""
    number: int
    title: str
    state: str
    html_url: str
    head_branch: str
    base_branch: str

class SOPHIAGitHubMaster:
    """
    Manages GitHub operations: branch creation, commits, pushes, PRs.
    Uses personal access token stored in the environment (GITHUB_TOKEN).
    
    This class provides autonomous GitHub operations for Sophia, allowing her to:
    - Create and manage branches
    - Commit and push changes
    - Open and manage pull requests
    - Monitor repository status
    """

    def __init__(self, repo_info: GitHubRepoInfo):
        """
        Initialize GitHub master with repository information.
        
        Args:
            repo_info: Repository information including owner and repo name
            
        Raises:
            EnvironmentError: If GITHUB_TOKEN is not set
        """
        self.repo_info = repo_info
        self.api_base = "https://api.github.com"
        self.token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
        
        if not self.token:
            raise EnvironmentError("GITHUB_TOKEN or GITHUB_PAT is not set in environment")
        
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        logger.info(f"Initialized GitHub master for {repo_info.owner}/{repo_info.repo}")

    def get_repository_info(self) -> Dict[str, Any]:
        """
        Get basic repository information.
        
        Returns:
            Dictionary with repository details
            
        Raises:
            requests.HTTPError: If API call fails
        """
        url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            repo_data = response.json()
            return {
                "name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "default_branch": repo_data["default_branch"],
                "private": repo_data["private"],
                "description": repo_data.get("description", ""),
                "language": repo_data.get("language", ""),
                "stars": repo_data["stargazers_count"],
                "forks": repo_data["forks_count"],
                "updated_at": repo_data["updated_at"]
            }
        except requests.RequestException as e:
            logger.error(f"Failed to get repository info: {e}")
            raise

    def create_branch(self, branch_name: str, base_sha: Optional[str] = None) -> str:
        """
        Create a new branch on GitHub.
        
        Args:
            branch_name: Name of the new branch
            base_sha: SHA of the commit to branch from. If None, uses default branch's latest commit
            
        Returns:
            The new branch's SHA
            
        Raises:
            requests.HTTPError: If API call fails
        """
        try:
            # Step 1: Get reference of the base branch if base_sha not provided
            if base_sha is None:
                ref_url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/git/ref/heads/{self.repo_info.default_branch}"
                ref_resp = requests.get(ref_url, headers=self.headers)
                ref_resp.raise_for_status()
                base_sha = ref_resp.json()["object"]["sha"]
                logger.info(f"Using base SHA {base_sha} from {self.repo_info.default_branch}")
            
            # Step 2: Create the new branch
            create_ref_url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/git/refs"
            data = {
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            }
            
            resp = requests.post(create_ref_url, json=data, headers=self.headers)
            resp.raise_for_status()
            
            new_sha = resp.json()["object"]["sha"]
            logger.info(f"Created branch {branch_name} with SHA {new_sha}")
            return new_sha
            
        except requests.RequestException as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            raise

    def commit_and_push(self, branch_name: str, files: Dict[str, str], commit_message: str, author_name: str = "SOPHIA AI", author_email: str = "sophia@ai-cherry.com") -> str:
        """
        Commit changes to given files and push to GitHub.
        
        Args:
            branch_name: Name of the branch to commit to
            files: Mapping of file paths to their new content (string)
            commit_message: Commit message
            author_name: Name of the commit author
            author_email: Email of the commit author
            
        Returns:
            SHA of the new commit
            
        Raises:
            requests.HTTPError: If API call fails
        """
        try:
            # Step 1: Get latest commit SHA and tree SHA for branch
            ref_url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/git/ref/heads/{branch_name}"
            ref_resp = requests.get(ref_url, headers=self.headers)
            ref_resp.raise_for_status()
            
            commit_sha = ref_resp.json()["object"]["sha"]
            
            # Get commit details
            commit_url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/git/commits/{commit_sha}"
            commit_resp = requests.get(commit_url, headers=self.headers)
            commit_resp.raise_for_status()
            
            base_tree_sha = commit_resp.json()["tree"]["sha"]
            logger.info(f"Base commit SHA: {commit_sha}, tree SHA: {base_tree_sha}")

            # Step 2: Create blobs for each file
            blob_shas = {}
            for path, content in files.items():
                blob_data = {
                    "content": content,
                    "encoding": "utf-8"
                }
                
                blob_url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/git/blobs"
                blob_resp = requests.post(blob_url, headers=self.headers, json=blob_data)
                blob_resp.raise_for_status()
                
                blob_shas[path] = blob_resp.json()["sha"]
                logger.info(f"Created blob for {path}: {blob_shas[path]}")

            # Step 3: Create a new tree with updated files
            tree_items = [
                {
                    "path": path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": sha
                }
                for path, sha in blob_shas.items()
            ]
            
            tree_data = {
                "base_tree": base_tree_sha,
                "tree": tree_items
            }
            
            tree_url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/git/trees"
            tree_resp = requests.post(tree_url, headers=self.headers, json=tree_data)
            tree_resp.raise_for_status()
            
            new_tree_sha = tree_resp.json()["sha"]
            logger.info(f"Created new tree: {new_tree_sha}")

            # Step 4: Create a new commit
            commit_data = {
                "message": commit_message,
                "tree": new_tree_sha,
                "parents": [commit_sha],
                "author": {
                    "name": author_name,
                    "email": author_email
                },
                "committer": {
                    "name": author_name,
                    "email": author_email
                }
            }
            
            commit_url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/git/commits"
            commit_resp = requests.post(commit_url, headers=self.headers, json=commit_data)
            commit_resp.raise_for_status()
            
            new_commit_sha = commit_resp.json()["sha"]
            logger.info(f"Created new commit: {new_commit_sha}")

            # Step 5: Update the branch reference
            update_data = {
                "sha": new_commit_sha,
                "force": False
            }
            
            update_url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/git/refs/heads/{branch_name}"
            update_resp = requests.patch(update_url, headers=self.headers, json=update_data)
            update_resp.raise_for_status()
            
            logger.info(f"Successfully pushed commit {new_commit_sha} to branch {branch_name}")
            return new_commit_sha
            
        except requests.RequestException as e:
            logger.error(f"Failed to commit and push to {branch_name}: {e}")
            raise

    def create_pull_request(self, branch_name: str, title: str, body: str, base_branch: Optional[str] = None) -> GitHubPRInfo:
        """
        Create a pull request from branch_name to the base branch.
        
        Args:
            branch_name: Source branch name
            title: PR title
            body: PR description
            base_branch: Target branch (defaults to repository's default branch)
            
        Returns:
            GitHubPRInfo with PR details
            
        Raises:
            requests.HTTPError: If API call fails
        """
        if base_branch is None:
            base_branch = self.repo_info.default_branch
        
        try:
            pr_url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/pulls"
            payload = {
                "title": title,
                "head": branch_name,
                "base": base_branch,
                "body": body
            }
            
            resp = requests.post(pr_url, headers=self.headers, json=payload)
            resp.raise_for_status()
            
            pr_data = resp.json()
            pr_info = GitHubPRInfo(
                number=pr_data["number"],
                title=pr_data["title"],
                state=pr_data["state"],
                html_url=pr_data["html_url"],
                head_branch=pr_data["head"]["ref"],
                base_branch=pr_data["base"]["ref"]
            )
            
            logger.info(f"Created PR #{pr_info.number}: {pr_info.html_url}")
            return pr_info
            
        except requests.RequestException as e:
            logger.error(f"Failed to create pull request: {e}")
            raise

    def get_pull_requests(self, state: str = "open") -> List[GitHubPRInfo]:
        """
        Get list of pull requests.
        
        Args:
            state: PR state ('open', 'closed', 'all')
            
        Returns:
            List of GitHubPRInfo objects
            
        Raises:
            requests.HTTPError: If API call fails
        """
        try:
            url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/pulls"
            params = {"state": state}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            prs = []
            for pr_data in response.json():
                pr_info = GitHubPRInfo(
                    number=pr_data["number"],
                    title=pr_data["title"],
                    state=pr_data["state"],
                    html_url=pr_data["html_url"],
                    head_branch=pr_data["head"]["ref"],
                    base_branch=pr_data["base"]["ref"]
                )
                prs.append(pr_info)
            
            logger.info(f"Retrieved {len(prs)} {state} pull requests")
            return prs
            
        except requests.RequestException as e:
            logger.error(f"Failed to get pull requests: {e}")
            raise

    def get_branches(self) -> List[str]:
        """
        Get list of all branches in the repository.
        
        Returns:
            List of branch names
            
        Raises:
            requests.HTTPError: If API call fails
        """
        try:
            url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/branches"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            branches = [branch["name"] for branch in response.json()]
            logger.info(f"Retrieved {len(branches)} branches")
            return branches
            
        except requests.RequestException as e:
            logger.error(f"Failed to get branches: {e}")
            raise

    def get_recent_commits(self, branch: Optional[str] = None, limit: int = 10) -> List[GitHubCommitInfo]:
        """
        Get recent commits from a branch.
        
        Args:
            branch: Branch name (defaults to default branch)
            limit: Maximum number of commits to retrieve
            
        Returns:
            List of GitHubCommitInfo objects
            
        Raises:
            requests.HTTPError: If API call fails
        """
        if branch is None:
            branch = self.repo_info.default_branch
        
        try:
            url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/commits"
            params = {"sha": branch, "per_page": limit}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            commits = []
            for commit_data in response.json():
                commit_info = GitHubCommitInfo(
                    sha=commit_data["sha"],
                    message=commit_data["commit"]["message"],
                    author=commit_data["commit"]["author"]["name"],
                    date=commit_data["commit"]["author"]["date"],
                    url=commit_data["html_url"]
                )
                commits.append(commit_info)
            
            logger.info(f"Retrieved {len(commits)} recent commits from {branch}")
            return commits
            
        except requests.RequestException as e:
            logger.error(f"Failed to get recent commits: {e}")
            raise

    def delete_branch(self, branch_name: str) -> bool:
        """
        Delete a branch from the repository.
        
        Args:
            branch_name: Name of the branch to delete
            
        Returns:
            True if successful
            
        Raises:
            requests.HTTPError: If API call fails
        """
        try:
            url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/git/refs/heads/{branch_name}"
            
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            
            logger.info(f"Deleted branch {branch_name}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to delete branch {branch_name}: {e}")
            raise

    def get_file_content(self, file_path: str, branch: Optional[str] = None) -> str:
        """
        Get the content of a file from the repository.
        
        Args:
            file_path: Path to the file
            branch: Branch name (defaults to default branch)
            
        Returns:
            File content as string
            
        Raises:
            requests.HTTPError: If API call fails
        """
        if branch is None:
            branch = self.repo_info.default_branch
        
        try:
            url = f"{self.api_base}/repos/{self.repo_info.owner}/{self.repo_info.repo}/contents/{file_path}"
            params = {"ref": branch}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            file_data = response.json()
            if file_data["encoding"] == "base64":
                content = base64.b64decode(file_data["content"]).decode("utf-8")
            else:
                content = file_data["content"]
            
            logger.info(f"Retrieved content for {file_path} from {branch}")
            return content
            
        except requests.RequestException as e:
            logger.error(f"Failed to get file content for {file_path}: {e}")
            raise

    def check_rate_limit(self) -> Dict[str, Any]:
        """
        Check GitHub API rate limit status.
        
        Returns:
            Dictionary with rate limit information
            
        Raises:
            requests.HTTPError: If API call fails
        """
        try:
            url = f"{self.api_base}/rate_limit"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            rate_limit_data = response.json()
            return {
                "limit": rate_limit_data["rate"]["limit"],
                "remaining": rate_limit_data["rate"]["remaining"],
                "reset": rate_limit_data["rate"]["reset"],
                "used": rate_limit_data["rate"]["used"]
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to check rate limit: {e}")
            raise

