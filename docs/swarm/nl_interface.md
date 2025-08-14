# Natural Language Interface for Sophia Swarm

This document describes how to use the natural language interface to interact with the Sophia Swarm system.

## Overview

The natural language interface provides a user-friendly way to interact with the Sophia Swarm system. It allows you to submit plain English instructions and have the Swarm process them through its multi-agent workflow (architect, builder, tester, operator).

## Usage

### Python API

```python
from swarm.nl_interface import process_natural_language

# Submit a natural language query
results = process_natural_language(
    "Create a new API endpoint for user authentication"
)

# Access the individual agent outputs
architect_output = results.get("architect", "")
builder_output = results.get("builder", "")
tester_output = results.get("tester", "")
operator_output = results.get("operator", "")

# Print the results
print(f"Architect: {architect_output}")
print(f"Builder: {builder_output}")
print(f"Tester: {tester_output}")
print(f"Operator: {operator_output}")
```

### Command Line Interface

The `swarm_cli.py` tool provides a command-line interface for interacting with the Swarm system:

```bash
# Basic usage
python -m cli.swarm_cli "Create a new API endpoint for user authentication"

# Read query from a file
python -m cli.swarm_cli -f query.txt

# Output results as JSON
python -m cli.swarm_cli "Create a new API endpoint" --json

# Save results to a file
python -m cli.swarm_cli "Create a new API endpoint" -o results.txt

# Override the default model for all agents
python -m cli.swarm_cli "Create a new API endpoint" --model gpt-4-turbo
```

## Environment Variables

The natural language interface respects the following environment variables:

- `SWARM_DEFAULT_MODEL`: Sets the default model for all agents
- `SWARM_ARCHITECT_MODEL`: Sets the model for the architect agent
- `SWARM_BUILDER_MODEL`: Sets the model for the builder agent
- `SWARM_TESTER_MODEL`: Sets the model for the tester agent
- `SWARM_OPERATOR_MODEL`: Sets the model for the operator agent

Example:

```bash
# Set environment variables
export SWARM_DEFAULT_MODEL="gpt-4"
export SWARM_ARCHITECT_MODEL="claude-3-opus-20240229"

# Run the CLI
python -m cli.swarm_cli "Create a new API endpoint"
```

## Advanced Configuration

For more advanced configuration options, refer to the [Swarm Configuration Guide](../docs/swarm/configuration.md).

## Examples

Here are some example queries you can try:

1. "Create a new REST API endpoint for user registration"
2. "Implement a database migration for the user table"
3. "Add authentication middleware to the web application"
4. "Design a caching layer for the product catalog"
5. "Optimize the performance of the search functionality"

## Troubleshooting

If you encounter issues with the natural language interface, try the following:

1. Check that you have proper authentication for the LLM services
2. Ensure your query is clear and specific
3. Check the logs for any error messages
4. Try using a more advanced model by setting the `SWARM_DEFAULT_MODEL` environment variable

## Limitations

The natural language interface is subject to the following limitations:

1. It depends on the quality of the underlying language models
2. Very complex requests may not be processed accurately
3. Domain-specific knowledge may be limited
4. Processing time increases with request complexity
