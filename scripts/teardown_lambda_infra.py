#!/usr/bin/env python3
"""
Tear down all Lambda Cloud infrastructure (instances and SSH keys).
- Dry-run by default: prints terminate/delete plan.
- Requires --confirm-burn-it-down to execute.
- After completion, re-lists to confirm zero instances/keys.
- Prints a green 'CLEAN SLATE' line if successful.
- Prints a red summary table of failures if any API errors occur.
"""
import os
import sys
import asyncio
import httpx
from typing import Any

API_KEY = os.environ.get("LAMBDA_CLOUD_API_KEY")
API_URL = "https://cloud.lambda.ai/api/v1"

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


def print_success(msg: str):
    if console:
        console.print(f"[bold green]{msg}[/bold green]")
    else:
        print(f"SUCCESS: {msg}")


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


async def delete(client, endpoint):
    url = f"{API_URL}{endpoint}"
    resp = await client.delete(url, headers={"Authorization": f"Bearer {API_KEY}"})
    resp.raise_for_status()
    return resp.json()


async def main():
    if not API_KEY or len(API_KEY.strip()) == 0:
        print_error(
            "LAMBDA_CLOUD_API_KEY is missing. Add it to .env.sophia or Codespaces secrets.")
        sys.exit(1)
    confirm = "--confirm-burn-it-down" in sys.argv
    async with httpx.AsyncClient(timeout=30) as client:
        # List instances and keys
        try:
            instances = (await fetch(client, "/instances"))["data"]
            keys = (await fetch(client, "/ssh-keys"))["data"]
        except Exception as e:
            print_error(f"Failed to fetch resources: {e}")
            sys.exit(2)
        # Plan
        inst_rows = [[i.get("id"), i.get("name"), i.get(
            "type"), i.get("status")] for i in instances]
        key_rows = [[k.get("id"), k.get("name"), k.get("fingerprint")]
                    for k in keys]
        print_table("Instances to Terminate", [
                    "ID", "Name", "Type", "Status"], inst_rows)
        print_table("SSH Keys to Delete", [
                    "ID", "Name", "Fingerprint"], key_rows)
        if not confirm:
            print("\nDry-run only. To execute, run with --confirm-burn-it-down\n")
            sys.exit(0)
        # Terminate instances
        fail = []

        async def terminate(inst):
            try:
                await delete(client, f"/instances/{inst['id']}")
                return None
            except Exception as e:
                return (inst['id'], str(e))

        async def delkey(key):
            try:
                await delete(client, f"/ssh-keys/{key['id']}")
                return None
            except Exception as e:
                return (key['id'], str(e))
        # Parallelize
        inst_fails = await asyncio.gather(*[terminate(i) for i in instances])
        key_fails = await asyncio.gather(*[delkey(k) for k in keys])
        fail += [f for f in inst_fails if f]
        fail += [f for f in key_fails if f]
        # Re-list
        try:
            instances2 = (await fetch(client, "/instances"))["data"]
            keys2 = (await fetch(client, "/ssh-keys"))["data"]
        except Exception as e:
            print_error(f"Failed to re-list resources: {e}")
            sys.exit(3)
        if not instances2 and not keys2 and not fail:
            print_success(
                "CLEAN SLATE: All Lambda Cloud instances and SSH keys deleted.")
            sys.exit(0)
        if fail:
            print_error("Some resources failed to delete:")
            print_table("Failures", ["ID", "Error"], fail)
        if instances2:
            print_error("Instances remaining:")
            print_table("Instances", ["ID", "Name", "Type", "Status"], [
                        [i.get("id"), i.get("name"), i.get("type"), i.get("status")] for i in instances2])
        if keys2:
            print_error("SSH Keys remaining:")
            print_table("SSH Keys", ["ID", "Name", "Fingerprint"], [
                        [k.get("id"), k.get("name"), k.get("fingerprint")] for k in keys2])
        sys.exit(4)

if __name__ == "__main__":
    asyncio.run(main())
