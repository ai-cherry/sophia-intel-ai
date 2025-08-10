import asyncio
from temporalio import activity, workflow
from temporalio.client import Client
from datetime import timedelta

from services.config_loader import load_config
from connectors.pulumi_conn import PulumiConnector
from services.approvals_github import GitHubApprovalService

@activity.defn
async def pulumi_preview(stack_name: str, project_name: str, work_dir: str) -> str:
    """Activity to run pulumi preview."""
    config = load_config()
    connector = PulumiConnector(config, project_name, work_dir)
    return await connector.preview(stack_name)

@activity.defn
async def pulumi_up(stack_name: str, project_name: str, work_dir: str) -> str:
    """Activity to run pulumi up."""
    config = load_config()
    connector = PulumiConnector(config, project_name, work_dir)
    return await connector.up(stack_name)

@activity.defn
async def require_approval(owner: str, repo: str, pr_number: int, action: str) -> bool:
    """Activity to require approval on a PR."""
    config = load_config()
    approval_service = GitHubApprovalService(config)
    return await approval_service.require_approval(owner, repo, pr_number, action)

@workflow.defn
class PulumiPreviewAndUpWorkflow:
    @workflow.run
    async def run(self, owner: str, repo: str, pr_number: int, stack_name: str, project_name: str, work_dir: str) -> str:
        """Workflow to run pulumi preview and then up after approval."""
        
        preview_output = await workflow.execute_activity(
            pulumi_preview,
            args=[stack_name, project_name, work_dir],
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        approved = await workflow.execute_activity(
            require_approval,
            args=[owner, repo, pr_number, "pulumi-up"],
            start_to_close_timeout=timedelta(minutes=30),
        )
        
        if approved:
            up_output = await workflow.execute_activity(
                pulumi_up,
                args=[stack_name, project_name, work_dir],
                start_to_close_timeout=timedelta(minutes=15),
            )
            return f"Pulumi up completed successfully:\n{up_output}"
        else:
            return "Pulumi up was not approved."

async def main():
    """Entry point to run the workflow."""
    client = await Client.connect("localhost:7233")
    
    # This is a mock PR number. In a real workflow, this would be dynamic.
    pr_number = 1
    
    result = await client.execute_workflow(
        PulumiPreviewAndUpWorkflow.run,
        "ai-cherry", "sophia-intel", pr_number, "dev", "my-project", "./pulumi_project",
        id="pulumi-preview-and-up-workflow",
        task_queue="my-task-queue",
    )
    print(f"Workflow result: {result}")

if __name__ == "__main__":
    # This example requires a Pulumi and GitHub access token to be set.
    if os.getenv("PULUMI_ACCESS_TOKEN") and os.getenv("GH_FINE_GRAINED_TOKEN"):
        asyncio.run(main())
    else:
        print("PULUMI_ACCESS_TOKEN or GH_FINE_GRAINED_TOKEN not set. Skipping example.")