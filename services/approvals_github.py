import asyncio
import logging
from typing import Dict, Any, Optional

from connectors.github_conn import GitHubConnector
from services.config_loader import load_config

class GitHubApprovalService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.github_connector = GitHubConnector(config)

    async def require_approval(
        self, owner: str, repo: str, pr_number: int, action: str, plan_artifact: Optional[str] = None
    ) -> bool:
        """
        Requires approval for a given action on a pull request.
        This is a simplified implementation. A real implementation would involve:
        1. Creating a GitHub Check Run.
        2. Posting a comment to the PR with the plan.
        3. Waiting for an "Approved" review or a specific comment.
        4. Updating the Check Run with the result.
        """
        logging.info(f"Requiring approval for action '{action}' on PR {pr_number}")

        # For now, we'll simulate the approval process by checking for an "APPROVED" review.
        # In a real-world scenario, this would be a more robust check,
        # possibly involving a loop with a timeout.

        try:
            pr_details = await self.github_connector.get_pr_details(owner, repo, pr_number)
            reviews = await self._get_pr_reviews(owner, repo, pr_number)

            allowed_users = self.config.get("approvals", {}).get("allowed_users", [])

            for review in reviews:
                if (
                    review["state"] == "APPROVED" and
                    review["user"]["login"] in allowed_users
                ):
                    logging.info(f"Approval received from {review['user']['login']}")
                    return True
            
            logging.warning("No approval found.")
            return False

        finally:
            await self.github_connector.close()

    async def _get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list:
        headers = await self.github_connector._get_auth_headers()
        response = await self.github_connector.client.get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews", headers=headers
        )
        response.raise_for_status()
        return response.json()

async def main():
    """Example usage of the approval service."""
    logging.basicConfig(level=logging.INFO)
    
    # This is a mock PR number. In a real workflow, this would be dynamic.
    pr_number = 1 
    
    config = load_config()
    approval_service = GitHubApprovalService(config)
    
    approved = await approval_service.require_approval(
        "ai-cherry", "sophia-intel", pr_number, "pulumi-up"
    )
    
    if approved:
        print("Action approved!")
    else:
        print("Action not approved.")

if __name__ == "__main__":
    # This example requires a GitHub token and a valid PR number.
    if os.getenv("GH_FINE_GRAINED_TOKEN"):
        asyncio.run(main())
    else:
        print("GH_FINE_GRAINED_TOKEN environment variable not set. Skipping example.")