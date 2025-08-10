import asyncio
import os
from typing import Dict, Any
from pulumi import automation as auto

class PulumiConnector:
    def __init__(self, config: Dict[str, Any], project_name: str, work_dir: str):
        self.config = config
        self.project_name = project_name
        self.work_dir = work_dir
        # Ensure PULUMI_ACCESS_TOKEN is set in the environment for the Automation API
        if "access_token" in self.config.get("pulumi", {}):
            os.environ["PULUMI_ACCESS_TOKEN"] = self.config["pulumi"]["access_token"]

    async def _create_stack(self, stack_name: str):
        return await asyncio.to_thread(
            auto.create_or_select_stack,
            stack_name=stack_name,
            project_name=self.project_name,
            work_dir=self.work_dir,
        )

    async def preview(self, stack_name: str) -> str:
        stack = await self._create_stack(stack_name)
        preview_result = await asyncio.to_thread(stack.preview)
        return preview_result.stdout

    async def up(self, stack_name: str) -> str:
        stack = await self._create_stack(stack_name)
        up_result = await asyncio.to_thread(stack.up, on_output=print)
        return up_result.stdout

# Example usage (for testing)
async def main():
    # This is a mock configuration for demonstration purposes.
    # In a real scenario, this would be loaded by the config_loader.
    mock_config = {
        "pulumi": {
            "access_token": os.getenv("PULUMI_ACCESS_TOKEN")
        }
    }
    
    # You would need a sample Pulumi project in './pulumi_project' for this to work.
    # For now, this part is for demonstration of the class structure.
    if not os.path.exists("./pulumi_project"):
        os.makedirs("./pulumi_project")
        with open("./pulumi_project/Pulumi.yaml", "w") as f:
            f.write("name: my-project\nruntime: python\n")
        with open("./pulumi_project/__main__.py", "w") as f:
            f.write("import pulumi\n\npulumi.export('output_value', 'hello world')\n")


    connector = PulumiConnector(
        config=mock_config,
        project_name="my-project",
        work_dir="./pulumi_project"
    )
    
    stack_name = "dev"
    
    print("--- Running Pulumi Preview ---")
    preview_output = await connector.preview(stack_name)
    print(preview_output)
    
    # print("\n--- Running Pulumi Up ---")
    # up_output = await connector.up(stack_name)
    # print(up_output)

if __name__ == "__main__":
    # This example requires a Pulumi access token to be set in the environment.
    if os.getenv("PULUMI_ACCESS_TOKEN"):
        asyncio.run(main())
    else:
        print("PULUMI_ACCESS_TOKEN environment variable not set. Skipping example.")