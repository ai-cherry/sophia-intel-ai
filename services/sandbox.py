import subprocess
from dataclasses import dataclass
from typing import List


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str


class Sandbox:
    def __init__(
        self,
        image: str = "python:3.11-slim",
        cpu_limit: float = 0.5,
        mem_limit: str = "512m",
        egress_allowlist: List[str] = None,
    ):
        """
        Initializes the sandbox environment.
        In a real implementation, this would configure a container runtime
        like Docker or Podman.
        """
        self.image = image
        self.cpu_limit = cpu_limit
        self.mem_limit = mem_limit
        self.egress_allowlist = egress_allowlist or []
        print(f"Sandbox initialized with image: {self.image}")

    def run(self, command: List[str]) -> SandboxResult:
        """
        Runs a command in the sandbox.
        This is a placeholder implementation that runs the command on the host.
        A real implementation would use a container runtime to isolate the process.
        """
        print(f"Running command in sandbox: {' '.join(command)}")

        # Placeholder for egress filtering. In a real containerized setup,
        # this would be enforced by network policies.
        if not self._check_egress(command):
            return SandboxResult(1, "", "Egress blocked by sandbox policy.")

        try:
            # In a real implementation, this would be `docker run ...` or similar
            process = subprocess.run(
                command, capture_output=True, text=True, timeout=60
            )
            return SandboxResult(
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
            )
        except FileNotFoundError:
            return SandboxResult(1, "", f"Command not found: {command[0]}")
        except subprocess.TimeoutExpired:
            return SandboxResult(1, "", "Command timed out.")
        except Exception as e:
            return SandboxResult(1, "", f"An unexpected error occurred: {e}")

    def _check_egress(self, command: List[str]) -> bool:
        """
        A simple check for disallowed network access in the command.
        This is a placeholder and not a secure way to control egress.
        """
        for arg in command:
            if "curl" in arg or "wget" in arg:
                # A more sophisticated check would parse the URL and check against the allowlist
                print(f"Potential egress detected in command: {arg}")
                # Return False if not in allowlist (simplified for now)
        return True


if __name__ == "__main__":
    # Example usage
    sandbox = Sandbox()

    # Test a safe command
    result = sandbox.run(["echo", "Hello from the sandbox"])
    print(f"Result: {result}")
    assert result.exit_code == 0
    assert "Hello" in result.stdout

    # Test a command that would be blocked in a real sandbox
    result = sandbox.run(["curl", "-I", "https://example.com"])
    print(f"Result: {result}")
    # In this placeholder, it will likely run. In a real sandbox, it would be blocked.

    # Test a non-existent command
    result = sandbox.run(["nonexistentcommand"])
    print(f"Result: {result}")
    assert result.exit_code != 0
