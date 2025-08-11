from temporalio import activity, workflow
from datetime import timedelta

@activity.defn
async def say_hello(name: str) -> str:
    """A simple activity that returns a greeting."""
    return f"Hello, {name}!"

@workflow.defn
class HelloWorld:
    @workflow.run
    async def run(self, name: str) -> str:
        """A simple workflow that calls an activity."""
        return await workflow.execute_activity(
            say_hello, name, start_to_close_timeout=timedelta(seconds=10)
        )