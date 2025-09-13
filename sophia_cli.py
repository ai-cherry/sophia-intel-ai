#!/usr/bin/env python3
"""
Sophia CLI - Canonical entrypoint for Builder Stack

Thin wrapper that delegates to builder_cli.forge:cli
"""

import sys
import asyncio
from builder_cli.forge import cli


if __name__ == "__main__":
    # Mirror builder_cli/forge.py behavior for async commands
    if len(sys.argv) > 1 and sys.argv[1] in ["codegen", "review", "plan"]:
        asyncio.run(cli())
    else:
        cli()
