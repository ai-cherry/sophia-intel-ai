import asyncio
from temporalio import activity, workflow
from temporalio.client import Client
from datetime import timedelta
import hashlib

from services.config_loader import load_config
from connectors.github_conn import GitHubConnector


@activity.defn
async def read_github_file(owner: str, repo: str, path: str, ref: str = None) -> dict:
    """Activity to read a file from GitHub and return its content and hash."""
    config = load_config()
    connector = GitHubConnector(config)
    try:
        content = await connector.read_file(owner, repo, path, ref)
        sha256_hash = hashlib.sha256(content).hexdigest()
        return {"content": content.decode("utf-8"), "sha256": sha256_hash}
    finally:
        await connector.close()


@workflow.defn
class ReadFileWorkflow:
    @workflow.run
    async def run(self, owner: str, repo: str, path: str, ref: str = None) -> dict:
        """Workflow to read a file from GitHub."""
        return await workflow.execute_activity(
            read_github_file,
            args=[owner, repo, path, ref],
            start_to_close_timeout=timedelta(seconds=30),
        )


async def main():
    """Entry point to run the workflow."""
    client = await Client.connect("localhost:7233")
    result = await client.execute_workflow(
        ReadFileWorkflow.run,
        "ai-cherry",
        "sophia-intel",
        "README.md",
        id="read-file-workflow",
        task_queue="my-task-queue",
    )
    print(f"Workflow result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
