import httpx
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class GitHubApproval:
    check_run_id: int
    status: str = "pending"

class GitHubApprovalService:
    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the GitHub approval service.
        """
        github_config = config.get("github", {})
        self.token = github_config.get("token")
        self.repo = os.getenv("GITHUB_REPOSITORY") # e.g., "my-org/my-repo"
        self.client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )

    async def create_guarded_action_check(self, sha: str, action_id: str) -> Optional[GitHubApproval]:
        """
        Creates a pending GitHub Check for a guarded action.
        """
        if not self.token or not self.repo:
            print("GitHub token or repository not configured. Skipping check creation.")
            return None

        print(f"Creating 'Guarded Action' check for SHA {sha} and action {action_id}...")
        response = await self.client.post(
            f"/repos/{self.repo}/check-runs",
            json={
                "name": f"Guarded Action: {action_id}",
                "head_sha": sha,
                "status": "in_progress",
                "output": {
                    "title": "Approval Required",
                    "summary": f"This action requires manual approval. To approve, comment `/approve action={action_id}` on the pull request.",
                },
            },
        )
        if response.status_code == 201:
            check_run = response.json()
            print(f"Created check run with ID: {check_run['id']}")
            return GitHubApproval(check_run_id=check_run['id'])
        else:
            print(f"Failed to create check run: {response.text}")
            return None

    async def update_check_status(self, check_run_id: int, approved: bool):
        """
        Updates the status of the GitHub Check based on approval.
        """
        conclusion = "success" if approved else "failure"
        summary = "Action approved and executed." if approved else "Action rejected."

        print(f"Updating check run {check_run_id} to {conclusion}...")
        await self.client.patch(
            f"/repos/{self.repo}/check-runs/{check_run_id}",
            json={
                "status": "completed",
                "conclusion": conclusion,
                "output": {
                    "title": f"Action {conclusion.capitalize()}",
                    "summary": summary,
                },
            },
        )
        print("Check run updated.")

if __name__ == "__main__":
    import os
    import asyncio

    # Example usage (requires GitHub credentials and a real SHA)
    mock_config = {
        "github": {
            "token": os.getenv("GH_FINE_GRAINED_TOKEN")
        }
    }
    # Make sure to set GITHUB_REPOSITORY, e.g., "your-org/your-repo"
    # and a valid SHA for GITHUB_SHA
    os.environ["GITHUB_REPOSITORY"] = os.getenv("GITHUB_REPOSITORY", "ai-cherry/sophia-intel")
    GITHUB_SHA = os.getenv("GITHUB_SHA", "a6df717") # Use a recent commit for testing

    approval_service = GitHubApprovalService(mock_config)

    async def main():
        if not GITHUB_SHA:
            print("GITHUB_SHA environment variable not set. Skipping example.")
            return

        approval = await approval_service.create_guarded_action_check(GITHUB_SHA, "pulumi-up")
        if approval:
            print(f"Created approval gate: {approval}")
            # Simulate waiting for approval
            await asyncio.sleep(5)
            # Simulate approval
            await approval_service.update_check_status(approval.check_run_id, approved=True)

    if approval_service.token:
        asyncio.run(main())
    else:
        print("GH_FINE_GRAINED_TOKEN not set, skipping example.")