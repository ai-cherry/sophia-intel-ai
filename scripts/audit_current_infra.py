#!/usr/bin/env python3
"""
Audit current Lambda Cloud infrastructure: lists GPU instances and SSH keys.
Requires LAMBDA_CLOUD_API_KEY in environment or .env.sophia.
"""
import os
import sys
import asyncio
import httpx
from typing import Any

API_KEY = os.environ.get("LAMBDA_CLOUD_API_KEY")
API_URL = "https://cloud.lambda.ai/api/v1"

# Pretty table output
try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
except ImportError:
    console = None


def print_error(msg: str):
    if console:
        console.print(f"[bold red]{msg}[/bold red]")
    else:
        print(f"ERROR: {msg}")


def print_table(title: str, columns: list[str], rows: list[list[Any]]):
    if console:
        table = Table(title=title)
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*[str(x) for x in row])
        console.print(table)
    else:
        print(title)
        print(" | ".join(columns))
        for row in rows:
            print(" | ".join(str(x) for x in row))


async def fetch(client, endpoint):
    url = f"{API_URL}{endpoint}"
    resp = await client.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    resp.raise_for_status()
    return resp.json()


async def main():
    if not API_KEY or len(API_KEY.strip()) == 0:
        print_error(
            "LAMBDA_CLOUD_API_KEY is missing. Add it to .env.sophia or Codespaces secrets.")
        sys.exit(1)
    async with httpx.AsyncClient(timeout=30) as client:
        # List GPU instances
        try:
            instances = (await fetch(client, "/instances"))["data"]
        except Exception as e:
            print_error(f"Failed to fetch instances: {e}")
            sys.exit(2)
        rows = []
        for inst in instances:
            rows.append([
                inst.get("id"), inst.get("name"), inst.get(
                    "type"), inst.get("ip"),
                inst.get("region"), inst.get("status"),
                ",".join(inst.get("labels", [])), ",".join(
                    inst.get("ssh_key_names", []))
            ])
        print_table("Lambda Cloud GPU Instances", [
                    "ID", "Name", "Type", "IP", "Region", "Status", "Labels", "SSH Keys"], rows)
        # List SSH keys
        try:
            keys = (await fetch(client, "/ssh-keys"))["data"]
        except Exception as e:
            print_error(f"Failed to fetch SSH keys: {e}")
            sys.exit(3)
        keyrows = []
        for k in keys:
            keyrows.append([k.get("id"), k.get("name"), k.get("fingerprint")])
        print_table("Lambda Cloud SSH Keys", [
                    "ID", "Name", "Fingerprint"], keyrows)

if __name__ == "__main__":
    asyncio.run(main())
