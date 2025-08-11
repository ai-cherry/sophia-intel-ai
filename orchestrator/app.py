import asyncio
import logging
import os
from temporalio.client import Client
from temporalio.worker import Worker

# Import all workflows and activities
from orchestrator.workflows.hello_world import HelloWorld, say_hello
from orchestrator.workflows.read_file import ReadFileWorkflow, read_github_file
from orchestrator.workflows.deploy_feature import DeployFeatureWorkflow, run_deploy
from orchestrator.workflows.pulumi_preview_and_up import (
    PulumiPreviewAndUpWorkflow,
    pulumi_preview,
    pulumi_up
)


async def main():
    logging.basicConfig(level=logging.INFO)

    # Create a client to connect to Temporal
    # Use environment variable if set, otherwise default to localhost
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(temporal_host)

    # Create a worker
    # The worker listens to a task queue and executes workflows and activities.
    worker = Worker(
        client,
        task_queue="agno-task-queue",
        workflows=[
            HelloWorld,
            ReadFileWorkflow,
            DeployFeatureWorkflow,
            PulumiPreviewAndUpWorkflow
        ],
        activities=[
            say_hello,
            read_github_file,
            run_deploy,
            pulumi_preview,
            pulumi_up
        ],
        # Enable Update-with-Start
        build_id="1.0",
        identity="agno-worker-1",
    )

    # Start the worker
    logging.info("Starting worker...")
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Worker shut down.")
