# Agent Architecture

This document provides a high-level overview of the autonomous agent's architecture. For a more detailed breakdown, please refer to the [Final Architecture planning document](../../planning/final_architecture.md).

The agent is built on a microservices-based architecture, orchestrated by [Temporal](https://temporal.io/). The key components are:

- **Workflows:** Long-running, durable functions that define the overall logic of a task (e.g., deploying a feature).
- **Activities:** Short-lived, stateless functions that perform a single, well-defined action (e.g., reading a file from GitHub, running a test).
- **Connectors:** Clients for interacting with external services (e.g., GitHub, Pulumi, Qdrant).
- **Services:** Internal services that provide core functionality (e.g., configuration loading, sandboxing, approvals).