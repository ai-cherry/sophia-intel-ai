import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

# Import your workflows and activities here
# from workflows.hello_world import HelloWorld

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Create a client to connect to Temporal
    client = await Client.connect("localhost:7233")

    # Create a worker
    # The worker listens to a task queue and executes workflows and activities.
    worker = Worker(
        client,
        task_queue="my-task-queue",
        # workflows=[HelloWorld],
        # activities=[...],
    )

    # Start the worker
    logging.info("Starting worker...")
    await worker.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Worker shut down.")