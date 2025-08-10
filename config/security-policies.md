# Security Policies

## Secret Management

- **No secrets in the repository:** All secrets, API keys, and sensitive configuration must be stored in GitHub organization secrets.
- **Environment loading:** The application will load secrets from environment variables.
- **Pulumi ESC (optional):** If `ESC_TOKEN` and `ESC_ENV` are present, the application will prefer loading secrets from Pulumi ESC.

## Human-in-the-Loop (HITL) and Approvals

- **GitHub-native approvals:** All write actions to protected branches require approval via GitHub pull request reviews and status checks.
- **No Slack integration:** All notifications and approval flows will be handled within GitHub.
- **Approval enforcement:** Write actions are only permitted on protected branches after all required approvals are granted.

## Interim Mode

- **PAT allowed only in Interim Mode:** The use of Personal Access Tokens (`GH_FINE_GRAINED_TOKEN`) is only permitted during the interim phase.
- **Default to GitHub App:** The target state is to use a GitHub App for authentication.