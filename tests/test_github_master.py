"""
Tests for SOPHIAGitHubMaster
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import requests
from sophia.core.github_master import SOPHIAGitHubMaster, GitHubRepoInfo, GitHubCommitInfo, GitHubPRInfo

class TestSOPHIAGitHubMaster:
    """Test cases for SOPHIAGitHubMaster."""

    def test_github_master_initialization(self):
        """Test that GitHub master initializes correctly with valid token."""
        repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            master = SOPHIAGitHubMaster(repo_info)
            assert master.repo_info == repo_info
            assert master.token == "test_token"
            assert "Authorization" in master.headers
            assert master.headers["Authorization"] == "token test_token"

    def test_github_master_initialization_no_token(self):
        """Test that GitHub master raises error when no token is provided."""
        repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError, match="GITHUB_TOKEN or GITHUB_PAT is not set"):
                SOPHIAGitHubMaster(repo_info)

    def test_github_master_uses_github_pat(self):
        """Test that GitHub master can use GITHUB_PAT as fallback."""
        repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
        
        with patch.dict(os.environ, {"GITHUB_PAT": "pat_token"}, clear=True):
            master = SOPHIAGitHubMaster(repo_info)
            assert master.token == "pat_token"

    def test_github_repo_info_dataclass(self):
        """Test GitHubRepoInfo dataclass functionality."""
        repo_info = GitHubRepoInfo(owner="test-owner", repo="test-repo")
        assert repo_info.owner == "test-owner"
        assert repo_info.repo == "test-repo"
        assert repo_info.default_branch == "main"  # default value
        
        repo_info_custom = GitHubRepoInfo(owner="test", repo="test", default_branch="develop")
        assert repo_info_custom.default_branch == "develop"

    @patch('requests.get')
    def test_get_repository_info_success(self, mock_get):
        """Test successful repository info retrieval."""
        repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "name": "sophia-intel",
            "full_name": "ai-cherry/sophia-intel",
            "default_branch": "main",
            "private": False,
            "description": "Test repo",
            "language": "Python",
            "stargazers_count": 10,
            "forks_count": 5,
            "updated_at": "2024-01-01T00:00:00Z"
        }
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            master = SOPHIAGitHubMaster(repo_info)
            info = master.get_repository_info()
            
            assert info["name"] == "sophia-intel"
            assert info["full_name"] == "ai-cherry/sophia-intel"
            assert info["default_branch"] == "main"
            assert info["private"] is False
            assert info["stars"] == 10

    @patch('requests.get')
    @patch('requests.post')
    def test_create_branch_success(self, mock_post, mock_get):
        """Test successful branch creation."""
        repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
        
        # Mock getting base branch SHA
        mock_get_response = MagicMock()
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = {"object": {"sha": "base_sha_123"}}
        mock_get.return_value = mock_get_response
        
        # Mock creating new branch
        mock_post_response = MagicMock()
        mock_post_response.raise_for_status.return_value = None
        mock_post_response.json.return_value = {"object": {"sha": "new_sha_456"}}
        mock_post.return_value = mock_post_response
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            master = SOPHIAGitHubMaster(repo_info)
            sha = master.create_branch("test-branch")
            
            assert sha == "new_sha_456"
            mock_get.assert_called_once()
            mock_post.assert_called_once()

    @patch('requests.get')
    @patch('requests.post')
    @patch('requests.patch')
    def test_commit_and_push_success(self, mock_patch, mock_post, mock_get):
        """Test successful commit and push operation."""
        repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
        
        # Mock getting branch reference
        mock_get.side_effect = [
            # First call: get branch ref
            MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value={"object": {"sha": "commit_sha_123"}})
            ),
            # Second call: get commit details
            MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value={"tree": {"sha": "tree_sha_456"}})
            )
        ]
        
        # Mock blob creation, tree creation, commit creation
        mock_post.side_effect = [
            # Blob creation
            MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value={"sha": "blob_sha_789"})
            ),
            # Tree creation
            MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value={"sha": "new_tree_sha_abc"})
            ),
            # Commit creation
            MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value={"sha": "new_commit_sha_def"})
            )
        ]
        
        # Mock branch update
        mock_patch.return_value = MagicMock(raise_for_status=MagicMock())
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            master = SOPHIAGitHubMaster(repo_info)
            files = {"test.py": "print('hello world')"}
            commit_sha = master.commit_and_push("test-branch", files, "Test commit")
            
            assert commit_sha == "new_commit_sha_def"
            assert mock_get.call_count == 2
            assert mock_post.call_count == 3
            mock_patch.assert_called_once()

    @patch('requests.post')
    def test_create_pull_request_success(self, mock_post):
        """Test successful pull request creation."""
        repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "number": 123,
            "title": "Test PR",
            "state": "open",
            "html_url": "https://github.com/ai-cherry/sophia-intel/pull/123",
            "head": {"ref": "test-branch"},
            "base": {"ref": "main"}
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            master = SOPHIAGitHubMaster(repo_info)
            pr_info = master.create_pull_request("test-branch", "Test PR", "Test description")
            
            assert isinstance(pr_info, GitHubPRInfo)
            assert pr_info.number == 123
            assert pr_info.title == "Test PR"
            assert pr_info.html_url == "https://github.com/ai-cherry/sophia-intel/pull/123"

    @patch('requests.get')
    def test_get_branches_success(self, mock_get):
        """Test successful branch listing."""
        repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"name": "main"},
            {"name": "develop"},
            {"name": "feature/test"}
        ]
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            master = SOPHIAGitHubMaster(repo_info)
            branches = master.get_branches()
            
            assert branches == ["main", "develop", "feature/test"]

    @patch('requests.get')
    def test_get_recent_commits_success(self, mock_get):
        """Test successful recent commits retrieval."""
        repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {
                "sha": "commit1",
                "commit": {
                    "message": "First commit",
                    "author": {"name": "Test Author", "date": "2024-01-01T00:00:00Z"}
                },
                "html_url": "https://github.com/ai-cherry/sophia-intel/commit/commit1"
            },
            {
                "sha": "commit2",
                "commit": {
                    "message": "Second commit",
                    "author": {"name": "Test Author", "date": "2024-01-02T00:00:00Z"}
                },
                "html_url": "https://github.com/ai-cherry/sophia-intel/commit/commit2"
            }
        ]
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            master = SOPHIAGitHubMaster(repo_info)
            commits = master.get_recent_commits()
            
            assert len(commits) == 2
            assert all(isinstance(commit, GitHubCommitInfo) for commit in commits)
            assert commits[0].sha == "commit1"
            assert commits[0].message == "First commit"

    @patch('requests.delete')
    def test_delete_branch_success(self, mock_delete):
        """Test successful branch deletion."""
        repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            master = SOPHIAGitHubMaster(repo_info)
            result = master.delete_branch("test-branch")
            
            assert result is True
            mock_delete.assert_called_once()

    @patch('requests.get')
    def test_check_rate_limit_success(self, mock_get):
        """Test successful rate limit check."""
        repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "rate": {
                "limit": 5000,
                "remaining": 4999,
                "reset": 1640995200,
                "used": 1
            }
        }
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            master = SOPHIAGitHubMaster(repo_info)
            rate_limit = master.check_rate_limit()
            
            assert rate_limit["limit"] == 5000
            assert rate_limit["remaining"] == 4999
            assert rate_limit["used"] == 1

    def test_github_commit_info_dataclass(self):
        """Test GitHubCommitInfo dataclass functionality."""
        commit_info = GitHubCommitInfo(
            sha="abc123",
            message="Test commit",
            author="Test Author",
            date="2024-01-01T00:00:00Z",
            url="https://github.com/test/test/commit/abc123"
        )
        
        assert commit_info.sha == "abc123"
        assert commit_info.message == "Test commit"
        assert commit_info.author == "Test Author"

    def test_github_pr_info_dataclass(self):
        """Test GitHubPRInfo dataclass functionality."""
        pr_info = GitHubPRInfo(
            number=123,
            title="Test PR",
            state="open",
            html_url="https://github.com/test/test/pull/123",
            head_branch="feature",
            base_branch="main"
        )
        
        assert pr_info.number == 123
        assert pr_info.title == "Test PR"
        assert pr_info.state == "open"
        assert pr_info.head_branch == "feature"
        assert pr_info.base_branch == "main"

