# Agent Runbook

This document provides instructions for operating and troubleshooting the autonomous agent.

## Running the Agent

1.  **Set up the environment:** Ensure all required environment variables are set. You can use the `tools/smoke_env_check.py` script to verify your setup.
2.  **Start the Temporal worker:**
    ```bash
    python orchestrator/app.py
    ```
3.  **Execute a workflow:** You can trigger a workflow using the Temporal CLI or by running the example scripts in the `workflows` directory (e.g., `python workflows/read_file.py`).

## Troubleshooting

-   **"Temporal server not available":** Make sure the Temporal server is running and accessible at `localhost:7233`.
-   **"Missing environment variables":** Run `python tools/smoke_env_check.py` to identify which variables are missing.
-   **"GitHub API errors":** Check that your `GH_FINE_GRAINED_TOKEN` is valid and has the required permissions.