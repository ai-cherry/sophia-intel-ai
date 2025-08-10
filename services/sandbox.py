import docker
import os
from typing import List

class Sandbox:
    def __init__(self, image: str = "python:3.11-slim", network_mode: str = "host"):
        self.client = docker.from_env()
        self.image = image
        self.network_mode = network_mode

    def run_command(self, command: List[str], working_dir: str = "/app", volumes: dict = None) -> str:
        """
        Runs a command in a sandboxed Docker container.
        """
        if volumes is None:
            # By default, mount the current working directory into the container
            volumes = {os.getcwd(): {"bind": "/app", "mode": "rw"}}

        try:
            container = self.client.containers.run(
                self.image,
                command,
                working_dir=working_dir,
                volumes=volumes,
                network_mode=self.network_mode,
                detach=True,
            )
            result = container.wait()
            logs = container.logs().decode("utf-8")
            container.remove()
            
            if result["StatusCode"] != 0:
                raise Exception(f"Command failed with exit code {result['StatusCode']}:\n{logs}")
                
            return logs
        except docker.errors.ImageNotFound:
            print(f"Pulling image {self.image}...")
            self.client.images.pull(self.image)
            return self.run_command(command, working_dir, volumes)

    def run_pytests(self, path: str = ".") -> str:
        """Runs pytest in the sandbox."""
        return self.run_command(["pytest", path])

    def run_ruff(self, path: str = ".") -> str:
        """Runs ruff in the sandbox."""
        return self.run_command(["ruff", "check", path])

    def run_black_check(self, path: str = ".") -> str:
        """Runs black in check mode in the sandbox."""
        return self.run_command(["black", "--check", path])

# Example usage
if __name__ == "__main__":
    sandbox = Sandbox()
    
    print("--- Running a simple command ---")
    output = sandbox.run_command(["echo", "hello from the sandbox"])
    print(output)

    # To run the following examples, you would need to have the respective
    # tools (pytest, ruff, black) installed in the Docker image or provide
    # a custom Dockerfile. For now, these are commented out.

    # print("\n--- Running pytest ---")
    # try:
    #     pytest_output = sandbox.run_pytests()
    #     print(pytest_output)
    # except Exception as e:
    #     print(f"Could not run pytest: {e}")
