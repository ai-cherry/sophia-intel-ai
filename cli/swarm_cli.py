#!/usr/bin/env python
"""
CLI tool for interacting with the Sophia Swarm system using natural language.
"""

import argparse
import json
import os
from typing import Optional

from swarm.nl_interface import process_natural_language


def main():
    parser = argparse.ArgumentParser(description="Interact with Sophia Swarm using natural language")
    parser.add_argument("query", nargs="*", help="Natural language query to process")
    parser.add_argument("-f", "--file", help="File path containing the natural language query")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("-o", "--output", help="File to save the output results")
    parser.add_argument("--model", help="Override the default model for all agents")

    args = parser.parse_args()

    # Get the query from command line or file
    if args.file:
        with open(args.file, "r") as f:
            query = f.read().strip()
    elif args.query:
        query = " ".join(args.query)
    else:
        parser.print_help()
        return

    # Set model override if specified
    if args.model:
        os.environ["SWARM_DEFAULT_MODEL"] = args.model
        print(f"Using model override: {args.model}")

    # Process the query
    results = process_natural_language(query)

    # Handle output
    if args.json:
        output = json.dumps(results, indent=2)
        print(output)

    if args.output:
        output_format = "json" if args.json else "txt"
        with open(args.output, "w") as f:
            if output_format == "json":
                json.dump(results, f, indent=2)
            else:
                for agent, result in results.items():
                    f.write(f"=== {agent.upper()} ===\n\n")
                    f.write(f"{result}\n\n")
        print(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
