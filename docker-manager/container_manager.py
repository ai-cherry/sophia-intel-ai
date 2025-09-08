#!/usr/bin/env python3
"""
Docker Container Manager

A simple utility to manage Docker containers from within a dev container.
This script demonstrates how to interact with the Docker daemon that's available
within the dev container environment.
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, List, Optional


class DockerManager:
    """Manages Docker containers through the CLI."""

    @staticmethod
    def run_command(command: List[str]) -> subprocess.CompletedProcess:
        """Run a Docker command and return the result."""
        try:
            result = subprocess.run(
                command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {' '.join(command)}")
            print(f"Error message: {e.stderr}")
            sys.exit(1)

    def list_containers(self, all_containers: bool = False) -> List[Dict]:
        """List running containers or all containers if specified."""
        cmd = ["docker", "ps", "--format", "{{json .}}"]
        if all_containers:
            cmd.append("-a")

        result = self.run_command(cmd)

        # Parse the JSON output line by line
        containers = []
        for line in result.stdout.strip().split("\n"):
            if line:  # Skip empty lines
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Error parsing container info: {line}")

        return containers

    def container_stats(self, container_id: str) -> Dict:
        """Get real-time statistics for a specific container."""
        cmd = ["docker", "stats", container_id, "--no-stream", "--format", "{{json .}}"]
        result = self.run_command(cmd)

        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            print(f"Error parsing container stats: {result.stdout}")
            return {}

    def start_container(
        self,
        image: str,
        name: Optional[str] = None,
        ports: Optional[List[str]] = None,
        volumes: Optional[List[str]] = None,
        env_vars: Optional[List[str]] = None,
        detach: bool = True,
    ) -> str:
        """Start a new container with the given parameters."""
        cmd = ["docker", "run"]

        if detach:
            cmd.append("-d")

        if name:
            cmd.extend(["--name", name])

        if ports:
            for port in ports:
                cmd.extend(["-p", port])

        if volumes:
            for volume in volumes:
                cmd.extend(["-v", volume])

        if env_vars:
            for env_var in env_vars:
                cmd.extend(["-e", env_var])

        cmd.append(image)

        result = self.run_command(cmd)
        return result.stdout.strip()

    def stop_container(self, container_id: str) -> str:
        """Stop a running container."""
        cmd = ["docker", "stop", container_id]
        result = self.run_command(cmd)
        return result.stdout.strip()

    def remove_container(self, container_id: str, force: bool = False) -> str:
        """Remove a container."""
        cmd = ["docker", "rm", container_id]
        if force:
            cmd.append("-f")
        result = self.run_command(cmd)
        return result.stdout.strip()

    def get_logs(self, container_id: str, tail: Optional[int] = None) -> str:
        """Get logs from a container."""
        cmd = ["docker", "logs", container_id]
        if tail:
            cmd.extend(["--tail", str(tail)])
        result = self.run_command(cmd)
        return result.stdout


def main():
    """Main entry point for the Docker Manager CLI."""
    parser = argparse.ArgumentParser(description="Docker Container Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="List containers")
    list_parser.add_argument(
        "-a", "--all", action="store_true", help="Show all containers (default shows just running)"
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Get container statistics")
    stats_parser.add_argument("container_id", help="Container ID or name")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start a new container")
    start_parser.add_argument("image", help="Docker image to run")
    start_parser.add_argument("-n", "--name", help="Assign a name to the container")
    start_parser.add_argument(
        "-p", "--ports", action="append", help="Port mappings (host:container)"
    )
    start_parser.add_argument(
        "-v", "--volumes", action="append", help="Volume mappings (host:container)"
    )
    start_parser.add_argument(
        "-e", "--env", action="append", help="Environment variables (KEY=VALUE)"
    )

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop a container")
    stop_parser.add_argument("container_id", help="Container ID or name")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a container")
    remove_parser.add_argument("container_id", help="Container ID or name")
    remove_parser.add_argument(
        "-f", "--force", action="store_true", help="Force remove a running container"
    )

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Get container logs")
    logs_parser.add_argument("container_id", help="Container ID or name")
    logs_parser.add_argument("--tail", type=int, help="Number of lines to show from the end")

    args = parser.parse_args()
    manager = DockerManager()

    if args.command == "list":
        containers = manager.list_containers(all_containers=args.all)
        if containers:
            print(json.dumps(containers, indent=2))
        else:
            print("No containers found.")

    elif args.command == "stats":
        stats = manager.container_stats(args.container_id)
        print(json.dumps(stats, indent=2))

    elif args.command == "start":
        container_id = manager.start_container(
            args.image, name=args.name, ports=args.ports, volumes=args.volumes, env_vars=args.env
        )
        print(f"Container started with ID: {container_id}")

    elif args.command == "stop":
        result = manager.stop_container(args.container_id)
        print(f"Container stopped: {result}")

    elif args.command == "remove":
        result = manager.remove_container(args.container_id, force=args.force)
        print(f"Container removed: {result}")

    elif args.command == "logs":
        logs = manager.get_logs(args.container_id, tail=args.tail)
        print(logs)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
