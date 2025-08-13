# Pulumi ESC Integration for SOPHIA

This document describes how Environment Secret Control (ESC) is implemented in the SOPHIA project for secure cloud operations.

## What is Pulumi ESC?

Pulumi Environment Secret Control (ESC) is a secure secrets management system that:

1. Stores secrets centrally, encrypted at rest
2. Provides access control for teams
3. Enables secure secrets access without hardcoding
4. Integrates with CI/CD and cloud providers
5. Supports OIDC for zero-trust authentication

## Setup

### 1. Prerequisites

- Pulumi CLI installed
- `.env.sophia` file with `PULUMI_ESC_TOKEN` and `PULUMI_ORG` values

### 2. Bootstrap ESC

Run the setup script:

```bash
bash scripts/esc/pulumi_esc_setup.sh
```

This will:
- Verify Pulumi CLI is installed
- Log in to Pulumi
- Create an ESC context for your organization
- Configure secrets (GitHub token, etc.)
- Set up access policies for your projects

### 3. Using ESC in Pulumi Code

In your Pulumi programs, access secrets securely:

```typescript
// Get a secret from ESC
const githubToken = pulumi.getSecretOutput("github_token");

// Use it securely with providers
const githubProvider = new github.Provider("github", {
    token: githubToken,
});
```

See `pulumi/examples/esc_example.ts` for a complete example.

## OIDC Integration

For GitHub Actions workflows, use OIDC for zero-trust authentication:

```yaml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v2
  with:
    role-to-assume: ${{ vars.AWS_ROLE_ARN }}
    aws-region: ${{ vars.AWS_REGION }}
```

This avoids storing long-lived credentials in GitHub Secrets.

## Security Practices

- Never commit `.env.sophia` with actual secrets
- Use short-lived OIDC tokens for CI/CD
- Store organization-level secrets in ESC
- Prefer environment-specific stack configs over hardcoded values

## Resources

- [Pulumi ESC Documentation](https://www.pulumi.com/docs/esc/)
- [GitHub OIDC Guide](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-cloud-providers)
