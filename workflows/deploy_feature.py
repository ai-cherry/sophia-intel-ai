import asyncio
from temporalio import activity, workflow
from temporalio.client import Client
from datetime import timedelta

from services.config_loader import load_config
from connectors.github_conn import GitHubConnector
from services.sandbox import Sandbox
from services.approvals_github import GitHubApprovalService
from connectors.pulumi_conn import PulumiConnector

# It's better to define activities for each step to leverage Temporal's features.

@activity.defn
async def fetch_pr_details(owner: str, repo: str, pr_number: int) -> dict:
    config = load_config()
    connector = GitHubConnector(config)
    try:
        return await connector.get_pr_details(owner, repo, pr_number)
    finally:
        await connector.close()

@activity.defn
async def run_tests_in_sandbox() -> str:
    sandbox = Sandbox()
    # In a real scenario, you might need to checkout the specific PR branch
    # into a temporary directory and mount that into the sandbox.
    return sandbox.run_pytests()

@activity.defn
async def pulumi_preview(stack_name: str, project_name: str, work_dir: str) -> str:
    config = load_config()
    connector = PulumiConnector(config, project_name, work_dir)
    return await connector.preview(stack_name)

@activity.defn
async def require_approval(owner: str, repo: str, pr_number: int, action: str) -> bool:
    config = load_config()
    approval_service = GitHubApprovalService(config)
    return await approval_service.require_approval(owner, repo, pr_number, action)

@activity.defn
async def merge_pr(owner: str, repo: str, pr_number: int):
    # This would be implemented in the GitHubConnector
    # For now, it's a placeholder.
    print(f"Merging PR #{pr_number} in {owner}/{repo}")
    return True

@activity.defn
async def pulumi_up(stack_name: str, project_name: str, work_dir: str) -> str:
    config = load_config()
    connector = PulumiConnector(config, project_name, work_dir)
    return await connector.up(stack_name)

@activity.defn
async def post_pr_comment(owner: str, repo: str, pr_number: int, comment: str):
    # This would be implemented in the GitHubConnector
    print(f"Posting comment to PR #{pr_number} in {owner}/{repo}:\n{comment}")
    return True


@workflow.defn
class DeployFeatureWorkflow:
    @workflow.run
    async def run(self, owner: str, repo: str, pr_number: int, stack_name: str, project_name: str, work_dir: str) -> str:
        
        pr_details = await workflow.execute_activity(
            fetch_pr_details, args=[owner, repo, pr_number], start_to_close_timeout=timedelta(seconds=60)
        )
        
        test_results = await workflow.execute_activity(
            run_tests_in_sandbox, start_to_close_timeout=timedelta(minutes=5)
        )
        
        preview_output = await workflow.execute_activity(
            pulumi_preview, args=[stack_name, project_name, work_dir], start_to_close_timeout=timedelta(minutes=5)
        )
        
        await workflow.execute_activity(
            post_pr_comment, args=[owner, repo, pr_number, f"Pulumi Preview:\n```\n{preview_output}\n```"], start_to_close_timeout=timedelta(seconds=60)
        )

        approved = await workflow.execute_activity(
            require_approval, args=[owner, repo, pr_number, "pulumi-up"], start_to_close_timeout=timedelta(minutes=30)
        )

        if not approved:
            return "Deployment not approved."

        await workflow.execute_activity(
            merge_pr, args=[owner, repo, pr_number], start_to_close_timeout=timedelta(seconds=60)
        )

        up_output = await workflow.execute_activity(
            pulumi_up, args=[stack_name, project_name, work_dir], start_to_close_timeout=timedelta(minutes=15)
        )

        summary_comment = f"Deployment successful!\n\n**Pulumi Output:**\n```\n{up_output}\n```"
        await workflow.execute_activity(
            post_pr_comment, args=[owner, repo, pr_number, summary_comment], start_to_close_timeout=timedelta(seconds=60)
        )

        return "Deployment workflow completed successfully."

async def main():
    client = await Client.connect("localhost:7233")
    pr_number = 1 # Mock PR number
    result = await client.execute_workflow(
        DeployFeatureWorkflow.run,
        "ai-cherry", "sophia-intel", pr_number, "dev", "my-project", "./pulumi_project",
        id="deploy-feature-workflow",
        task_queue="my-task-queue",
    )
    print(f"Workflow result: {result}")

if __name__ == "__main__":
    if os.getenv("PULUMI_ACCESS_TOKEN") and os.getenv("GH_FINE_GRAINED_TOKEN"):
        asyncio.run(main())
    else:
        print("Required environment variables not set. Skipping example.")