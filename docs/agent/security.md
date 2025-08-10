# Agent Security

This document outlines the security model for the autonomous agent.

## Secret Management

All secrets are managed through GitHub organization secrets and loaded into the environment at runtime. The agent can also be configured to use Pulumi ESC for more advanced secret management.

For more details, see the [Security Policies](../config/security-policies.md).

## Human-in-the-Loop (HITL)

All destructive operations (e.g., merging a pull request, running `pulumi up`) require manual approval from a human operator. This is enforced through a combination of:

-   **GitHub Pull Request Reviews:** Protected branches require at least one approved review from a designated maintainer.
-   **GitHub Checks:** The agent will post a "Guarded Action" check to the pull request, which will remain pending until approval is granted.

This ensures that no unintended changes are made to the codebase or infrastructure.