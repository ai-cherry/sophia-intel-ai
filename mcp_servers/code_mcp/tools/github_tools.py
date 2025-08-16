"""
Enhanced GitHub Tools for MCP Code Server
Real GitHub API integration with comprehensive repository operations
"""

import asyncio
import base64
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from loguru import logger

from ..config import code_mcp_settings, get_github_headers, validate_repository_access


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors"""

    def __init__(self, status_code: int, message: str, response_data: Optional[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.response_data = response_data
        super().__init__(f"GitHub API Error {status_code}: {message}")


class GitHubTools:
    """Enhanced GitHub integration tools with real API operations"""

    def __init__(self):
        self.base_url = code_mcp_settings.github_api_base
        self.headers = get_github_headers()

        if not code_mcp_settings.github_pat:
            raise ValueError("GitHub PAT token required")

    async def _make_request(
        self, method: str, url: str, data: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> Dict:
        """Make authenticated GitHub API request with error handling"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, headers=self.headers, json=data, params=params, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_data = await response.json() if response.content_type == "application/json" else {}

                    if response.status >= 400:
                        error_message = response_data.get("message", f"HTTP {response.status}")
                        logger.error(f"GitHub API error {response.status}: {error_message}")
                        raise GitHubAPIError(response.status, error_message, response_data)

                    return response_data

        except aiohttp.ClientError as e:
            logger.error(f"GitHub API client error: {e}")
            raise GitHubAPIError(500, f"Client error: {e}")
        except asyncio.TimeoutError:
            logger.error("GitHub API request timeout")
            raise GitHubAPIError(408, "Request timeout")

    async def validate_access(self, repository: str) -> bool:
        """Validate access to repository"""
        if not validate_repository_access(repository):
            logger.warning(f"Repository {repository} not in allowed list")
            return False

        try:
            repo_url = f"{self.base_url}/repos/{repository}"
            await self._make_request("GET", repo_url)
            return True
        except GitHubAPIError:
            return False

    async def get_repository_info(self, repository: str) -> Dict:
        """Get comprehensive repository information"""
        if not await self.validate_access(repository):
            raise GitHubAPIError(403, f"Access denied to repository {repository}")

        try:
            repo_url = f"{self.base_url}/repos/{repository}"
            repo_data = await self._make_request("GET", repo_url)

            # Get additional repository statistics
            stats_url = f"{self.base_url}/repos/{repository}/stats/contributors"
            try:
                contributors = await self._make_request("GET", stats_url)
            except GitHubAPIError:
                contributors = []

            # Get languages
            languages_url = f"{self.base_url}/repos/{repository}/languages"
            try:
                languages = await self._make_request("GET", languages_url)
            except GitHubAPIError:
                languages = {}

            return {
                "basic_info": {
                    "name": repo_data.get("name"),
                    "full_name": repo_data.get("full_name"),
                    "description": repo_data.get("description"),
                    "private": repo_data.get("private"),
                    "default_branch": repo_data.get("default_branch"),
                    "created_at": repo_data.get("created_at"),
                    "updated_at": repo_data.get("updated_at"),
                    "size": repo_data.get("size"),
                    "stargazers_count": repo_data.get("stargazers_count"),
                    "forks_count": repo_data.get("forks_count"),
                    "open_issues_count": repo_data.get("open_issues_count"),
                },
                "languages": languages,
                "contributors_count": len(contributors) if contributors else 0,
                "clone_url": repo_data.get("clone_url"),
                "ssh_url": repo_data.get("ssh_url"),
            }

        except Exception as e:
            logger.error(f"Error getting repository info for {repository}: {e}")
            raise

    async def get_repository_structure(self, repository: str, branch: str = None) -> Dict:
        """Get repository file structure"""
        if not await self.validate_access(repository):
            raise GitHubAPIError(403, f"Access denied to repository {repository}")

        if not branch:
            repo_info = await self.get_repository_info(repository)
            branch = repo_info["basic_info"]["default_branch"]

        try:
            tree_url = f"{self.base_url}/repos/{repository}/git/trees/{branch}?recursive=1"
            tree_data = await self._make_request("GET", tree_url)

            files = []
            directories = []

            for item in tree_data.get("tree", []):
                if item["type"] == "blob":
                    files.append({"path": item["path"], "size": item.get("size", 0), "sha": item["sha"]})
                elif item["type"] == "tree":
                    directories.append({"path": item["path"], "sha": item["sha"]})

            return {
                "branch": branch,
                "total_files": len(files),
                "total_directories": len(directories),
                "files": files,
                "directories": directories,
                "tree_sha": tree_data.get("sha"),
            }

        except Exception as e:
            logger.error(f"Error getting repository structure for {repository}: {e}")
            raise

    async def read_file_content(self, repository: str, file_path: str, branch: str = None) -> Dict:
        """Read file content from repository"""
        if not await self.validate_access(repository):
            raise GitHubAPIError(403, f"Access denied to repository {repository}")

        try:
            params = {"ref": branch} if branch else {}
            content_url = f"{self.base_url}/repos/{repository}/contents/{file_path}"
            content_data = await self._make_request("GET", content_url, params=params)

            if content_data.get("content"):
                # Decode base64 content
                content = base64.b64decode(content_data["content"]).decode("utf-8")

                return {
                    "file_path": file_path,
                    "content": content,
                    "size": content_data.get("size", 0),
                    "sha": content_data.get("sha"),
                    "encoding": content_data.get("encoding"),
                    "branch": branch or "default",
                }
            else:
                raise GitHubAPIError(404, f"No content found for {file_path}")

        except Exception as e:
            logger.error(f"Error reading file {file_path} from {repository}: {e}")
            raise

    async def read_multiple_files(self, repository: str, file_paths: List[str], branch: str = None) -> Dict[str, Dict]:
        """Read multiple files efficiently"""
        if not await self.validate_access(repository):
            raise GitHubAPIError(403, f"Access denied to repository {repository}")

        if len(file_paths) > code_mcp_settings.max_files_per_operation:
            raise ValueError(f"Too many files requested. Max: {code_mcp_settings.max_files_per_operation}")

        results = {}
        errors = {}

        # Use asyncio.gather for concurrent requests
        async def read_single_file(file_path: str):
            try:
                return file_path, await self.read_file_content(repository, file_path, branch)
            except Exception as e:
                return file_path, {"error": str(e)}

        tasks = [read_single_file(fp) for fp in file_paths]
        file_results = await asyncio.gather(*tasks, return_exceptions=True)

        for file_path, result in file_results:
            if isinstance(result, Exception):
                errors[file_path] = str(result)
            elif "error" in result:
                errors[file_path] = result["error"]
            else:
                results[file_path] = result

        return {
            "successful_reads": results,
            "errors": errors,
            "total_requested": len(file_paths),
            "successful_count": len(results),
            "error_count": len(errors),
        }

    async def create_branch(self, repository: str, new_branch: str, source_branch: str = None) -> Dict:
        """Create a new branch from source branch"""
        if not await self.validate_access(repository):
            raise GitHubAPIError(403, f"Access denied to repository {repository}")

        try:
            # Get default branch if source not specified
            if not source_branch:
                repo_info = await self.get_repository_info(repository)
                source_branch = repo_info["basic_info"]["default_branch"]

            # Get source branch SHA
            ref_url = f"{self.base_url}/repos/{repository}/git/ref/heads/{source_branch}"
            ref_data = await self._make_request("GET", ref_url)
            source_sha = ref_data["object"]["sha"]

            # Create new branch
            create_url = f"{self.base_url}/repos/{repository}/git/refs"
            create_data = {"ref": f"refs/heads/{new_branch}", "sha": source_sha}

            result = await self._make_request("POST", create_url, create_data)

            return {
                "branch": new_branch,
                "sha": result["object"]["sha"],
                "source_branch": source_branch,
                "source_sha": source_sha,
                "ref": result["ref"],
                "created_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error creating branch {new_branch} in {repository}: {e}")
            raise

    async def commit_file_change(
        self,
        repository: str,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str,
        author_name: str = None,
        author_email: str = None,
    ) -> Dict:
        """Commit a file change to repository"""
        if not await self.validate_access(repository):
            raise GitHubAPIError(403, f"Access denied to repository {repository}")

        if len(content.encode("utf-8")) > code_mcp_settings.max_file_size:
            raise ValueError(f"File too large. Max size: {code_mcp_settings.max_file_size} bytes")

        try:
            # Get current file SHA if it exists
            file_sha = None
            try:
                content_url = f"{self.base_url}/repos/{repository}/contents/{file_path}"
                existing_file = await self._make_request("GET", content_url, params={"ref": branch})
                file_sha = existing_file.get("sha")
            except GitHubAPIError as e:
                if e.status_code != 404:
                    raise
                # File doesn't exist, that's OK for new files

            # Prepare commit data
            commit_url = f"{self.base_url}/repos/{repository}/contents/{file_path}"
            commit_data = {
                "message": commit_message,
                "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
                "branch": branch,
            }

            if file_sha:
                commit_data["sha"] = file_sha

            if author_name and author_email:
                commit_data["author"] = {"name": author_name, "email": author_email}

            result = await self._make_request("PUT", commit_url, commit_data)

            return {
                "file_path": file_path,
                "commit_sha": result["commit"]["sha"],
                "branch": branch,
                "message": commit_message,
                "content_sha": result["content"]["sha"],
                "size": result["content"]["size"],
                "operation": "updated" if file_sha else "created",
            }

        except Exception as e:
            logger.error(f"Error committing file {file_path} to {repository}: {e}")
            raise

    async def create_pull_request(
        self, repository: str, title: str, description: str, head_branch: str, base_branch: str = None
    ) -> Dict:
        """Create a pull request"""
        if not await self.validate_access(repository):
            raise GitHubAPIError(403, f"Access denied to repository {repository}")

        try:
            # Get default branch if base not specified
            if not base_branch:
                repo_info = await self.get_repository_info(repository)
                base_branch = repo_info["basic_info"]["default_branch"]

            pr_url = f"{self.base_url}/repos/{repository}/pulls"
            pr_data = {"title": title, "body": description, "head": head_branch, "base": base_branch}

            result = await self._make_request("POST", pr_url, pr_data)

            return {
                "pr_number": result["number"],
                "pr_url": result["html_url"],
                "api_url": result["url"],
                "title": result["title"],
                "body": result["body"],
                "head_branch": head_branch,
                "base_branch": base_branch,
                "state": result["state"],
                "created_at": result["created_at"],
                "user": result["user"]["login"],
            }

        except Exception as e:
            logger.error(f"Error creating PR in {repository}: {e}")
            raise

    async def get_pull_requests(self, repository: str, state: str = "open") -> List[Dict]:
        """Get pull requests for repository"""
        if not await self.validate_access(repository):
            raise GitHubAPIError(403, f"Access denied to repository {repository}")

        try:
            pr_url = f"{self.base_url}/repos/{repository}/pulls"
            params = {"state": state, "per_page": 100}

            prs = await self._make_request("GET", pr_url, params=params)

            return [
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "state": pr["state"],
                    "head_branch": pr["head"]["ref"],
                    "base_branch": pr["base"]["ref"],
                    "created_at": pr["created_at"],
                    "updated_at": pr["updated_at"],
                    "user": pr["user"]["login"],
                    "html_url": pr["html_url"],
                }
                for pr in prs
            ]

        except Exception as e:
            logger.error(f"Error getting PRs for {repository}: {e}")
            raise
