# Human-in-the-Loop (HITL) and Observability

This document details the design of the mandatory approval gate for critical operations and the observability stack for monitoring the agent and its managed services.

## 1. Human-in-the-Loop (HITL) Approval Gateway

A mandatory approval gate is required for all critical, destructive, or production-impacting actions.

### 1.1. Approval Workflow
1.  The Central Orchestrator identifies a high-risk action (e.g., `pulumi destroy`, merging to `main`).
2.  The orchestrator pauses the workflow and enters the `AwaitingApproval` state.
3.  The orchestrator sends an approval request to the HITL Gateway.
4.  The HITL Gateway forwards this request to the human operator via the configured communication channel.
5.  The operator reviews the request and submits an `Approve` or `Deny` response.
6.  The HITL Gateway validates the response and sends it back to the orchestrator.
7.  The orchestrator resumes the workflow. If approved, it proceeds with the action. If denied, it terminates the workflow or executes a fallback plan.

### 1.2. Communication Channel
We recommend using a chat-based platform like **Slack** or **Microsoft Teams** for HITL communication.
- **Why Chat?**
  - **Real-time:** Provides immediate notifications to operators.
  - **Interactive:** Supports interactive buttons and forms for easy `Approve`/`Deny` responses.
  - **Integration:** Easily integrated with the orchestration engine via webhooks.

### 1.3. Approval Request Format
Each approval request will contain the following information:
- **Action:** The command to be executed (e.g., `pulumi destroy`).
- **Target:** The resource the action will affect (e.g., the `production` stack).
- **Requester:** The ID of the workflow requesting the action.
- **Plan Details:** For infrastructure changes, the output of the `pulumi preview`.
- **Timeout:** The time the operator has to respond before the request expires.

### 1.4. Audit Trail
Every HITL request and response will be logged to a dedicated, immutable audit log. This log will capture:
- The full content of the approval request.
- The identity of the operator who responded.
- The timestamp of the response.
- The final decision (`Approved` or `Denied`).

## 2. Observability Stack

A comprehensive observability stack is required to monitor the health and performance of the agent and the services it manages. We recommend a stack based on the "three pillars of observability": logs, metrics, and traces.

### 2.1. Recommended Tooling
- **Metrics:** **Prometheus** for collecting and storing time-series data.
- **Logs:** **Loki** for collecting and aggregating logs from all components.
- **Traces:** **Tempo** for distributed tracing to understand the flow of requests across services.
- **Visualization:** **Grafana** to create dashboards for logs, metrics, and traces.

### 2.2. What to Monitor
- **Agent Metrics:**
  - Workflow execution status (success, failure, duration).
  - Task execution status.
  - Resource utilization of the sandbox environment.
- **Service Metrics:**
  - Health and latency of each external service (GitHub, Pulumi, etc.).
  - Resource utilization of managed services (Qdrant, Redis, etc.).
- **Logs:**
  - Structured logs (in JSON format) from all agent components.
  - Logs from the managed services.
- **Traces:**
  - Traces for each workflow, showing the full lifecycle of the operation.

## 3. Logging and Alerting Strategy

A proactive logging and alerting strategy is essential for maintaining system health and responding to incidents.

### 3.1. Structured Logging
All agent components **must** produce structured logs in **JSON format**. Each log entry should include:
- `timestamp`: The time of the event.
- `level`: The log level (`INFO`, `WARN`, `ERROR`).
- `message`: The log message.
- `workflow_id`: The ID of the workflow the log belongs to.
- `task_id`: The ID of the task the log belongs to.

### 3.2. Alerting Rules
Alerts will be configured in Prometheus's **Alertmanager**. Key alerting rules will include:
- **High Workflow Failure Rate:** An alert will be fired if the percentage of failed workflows exceeds a defined threshold.
- **Task Stuck in `Running` State:** An alert will be fired if a task remains in the `Running` state for longer than its expected timeout.
- **Service Unhealthy:** An alert will be fired if any of the external services (GitHub, Pulumi, etc.) become unhealthy.
- **Credential Vault Unreachable:** A high-priority alert will be fired if the agent cannot communicate with HashiCorp Vault.

### 3.3. Alerting Channels
- **High Priority Alerts (e.g., Vault unreachable, high workflow failure rate):** PagerDuty and Slack.
- **Low Priority Alerts (e.g., task stuck):** Slack only.