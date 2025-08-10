# Orchestration and Execution

This document details the design of the agent's Central Orchestrator and the task execution workflow.

## 1. Central Orchestrator Design

The Central Orchestrator is the "brain" of the agent. It is responsible for planning and executing the complex, multi-step tasks required to manage the development and operational workflow.

### 1.1. Core Responsibilities
- **Planning & Decomposition:** Receiving a high-level goal (e.g., "deploy the new feature from PR #123") and breaking it down into a directed acyclic graph (DAG) of executable tasks.
- **State Management:** Durably tracking the state of each task (e.g., `pending`, `running`, `completed`, `failed`) and the overall workflow. The state must be resilient to failures and restarts.
- **Tool Selection:** For each task, selecting the appropriate tool from the Tool & Service Abstraction Layer (e.g., the GitHub connector, the Pulumi connector).
- **Execution:** Invoking the selected tool with the correct parameters.
- **Coordination:** Managing the flow of data and control between tasks, including handling dependencies and parallelism.
- **Error Handling & Retries:** Implementing robust error handling and configurable retry policies for transient failures.

### 1.2. Recommended Technology: Temporal
We recommend building the Central Orchestrator using **Temporal**, a durable execution system.
- **Why Temporal?**
  - **Durability:** Temporal workflows are durable, meaning their state is preserved across process restarts and failures. This is critical for long-running operations like infrastructure provisioning.
  - **Reliability:** Temporal guarantees that a workflow will run to completion, even in the face of failures. It has built-in support for retries and error handling.
  - **Stateful Workflows:** Temporal is designed for stateful, long-running applications, which is a perfect fit for our agent's orchestration needs.
  - **Scalability:** Temporal is horizontally scalable to handle a large number of concurrent workflows.

### 1.3. Task Definition
Tasks will be defined as activities within a Temporal workflow. Each activity will correspond to a specific action the agent can perform.
- **Example Task (Activity):** `commit_code`
  - **Input:** `repository`, `branch`, `commit_message`, `files`
  - **Action:** Uses the GitHub connector to commit the specified files to the repository.

## 2. Task Execution Workflow

A workflow is a Directed Acyclic Graph (DAG) of tasks that accomplishes a high-level goal. The orchestrator is responsible for executing this DAG, respecting dependencies and managing state.

### 2.1. Task State Machine
Each task in the workflow will follow this state machine:
- **Pending:** The task is waiting for its dependencies to be met.
- **Running:** The task is currently being executed by an agent worker.
- **AwaitingApproval:** The task is a high-risk operation and is paused, waiting for human approval via the HITL gateway.
- **Succeeded:** The task completed successfully.
- **Failed:** The task failed. The workflow may be paused or terminated based on the failure mode.

### 2.2. Example Workflow: "Deploy New Feature"
**Goal:** Deploy the feature in pull request `#123`.

**Workflow DAG:**
1.  **`fetch_pr_details(pr_number=123)`:** Get the source branch and other details from the GitHub PR.
2.  **`run_unit_tests(branch='feature-branch-xyz')`:** Execute the unit test suite in the sandboxed environment.
3.  **`run_lint_checks(branch='feature-branch-xyz')`:** Run the linter.
4.  **`pulumi_preview()` (depends on 2, 3):** Run `pulumi preview` to see the infrastructure changes.
5.  **`request_deployment_approval(plan_details)` (depends on 4):** Post the Pulumi plan to the HITL gateway and wait for approval.
6.  **`merge_pr(pr_number=123)` (depends on 5):** Merge the PR to the `main` branch.
7.  **`pulumi_up()` (depends on 6):** Apply the infrastructure changes.
8.  **`monitor_deployment()` (depends on 7):** Use the observability stack to monitor the health of the new deployment.
9.  **`notify_on_completion()` (depends on 8):** Notify the human operator that the deployment is complete and successful.

## 3. Sandboxed Execution Environment

The agent requires a secure, isolated environment to execute shell commands, run tests, and manage local files.

### 3.1. Container-Based Sandbox
The execution environment will be a container-based sandbox, built using **Docker** or a similar OCI-compliant container runtime. This approach provides strong isolation and reproducibility.

### 3.2. Ephemeral Filesystem
Each task or workflow that requires a local execution environment will be run in a new container with an ephemeral filesystem.
- **Isolation:** This ensures that tasks cannot interfere with each other's files.
- **Reproducibility:** Each task starts with a clean, consistent environment.
- **Workspace:** A dedicated workspace directory will be mounted into the container, allowing the agent to check out code and manage files for the duration of the task.

### 3.3. Network Policy
A restrictive network policy will be applied to the sandbox container's network namespace.
- **Egress Control:** Only outbound connections to the specific services required by the architecture (Vault, GitHub API, Pulumi, etc.) will be permitted. All other outbound traffic will be blocked.
- **Ingress Control:** No inbound connections to the container will be allowed.

### 3.4. Resource Limits
To prevent resource exhaustion, strict CPU and memory limits will be applied to each sandbox container. These limits will be configurable based on the requirements of the task.