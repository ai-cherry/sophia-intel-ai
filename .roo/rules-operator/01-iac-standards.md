# Infrastructure as Code Standards

## Core Principles

1. **Plan First**: Always run previews before applying changes
2. **Small Changes**: Break infrastructure changes into minimal, reviewable units
3. **Rollback Ready**: Every change must have a clear rollback procedure
4. **No Direct Changes**: All infrastructure changes must go through IaC

## Pulumi Best Practices

### Project Structure

```
infra/
  __main__.py       # Main deployment entry point
  dns_tls.py        # DNS and TLS configuration
  k3s.py            # Kubernetes resources
  lambda_dynamic.py # Serverless resources
  Pulumi.yaml       # Project configuration
  Pulumi.dev.yaml   # Dev stack configuration
  Pulumi.prod.yaml  # Production stack configuration
```

### Configuration Management

Use stack configuration files for environment-specific settings:

```yaml
# Pulumi.dev.yaml
config:
  aws:region: us-west-2
  sophia:instanceSize: small
  sophia:replicas: 1
```

### Resource Naming

Use consistent naming patterns:

```python
from pulumi import export, ResourceOptions

# Naming pattern: {project}-{environment}-{resource-type}-{purpose}
instance_name = f"sophia-{stack}-vm-agent"

vm = compute.Instance(
    instance_name,
    # other properties
    opts=ResourceOptions(
        protect=stack == "prod"  # Protect production resources
    )
)

export("vm_ip", vm.public_ip)
```

### Change Workflow

1. **Plan**: Always preview changes first
   ```bash
   pulumi preview
   ```

2. **Apply**: Apply changes with confirmation
   ```bash
   pulumi up
   ```

3. **Document**: Update runbooks and documentation

4. **Test**: Verify resources are working as expected

### CI Integration

Example GitHub Action workflow:

```yaml
name: Pulumi
on:
  pull_request:
    paths:
      - 'infra/**'

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r infra/requirements.txt
      - uses: pulumi/actions@v3
        with:
          command: preview
          stack-name: dev
          comment-on-pr: true
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
```

## Rollback Procedures

### Documentation

Every infrastructure change should include:

1. What was changed (resources, configurations)
2. How to verify success (endpoint checks, logs)
3. How to roll back (specific commands)

### Rollback Template

```markdown
# Rollback Procedure for [Change Name]

## Overview
Brief description of what was changed

## Rollback Steps
1. Run `pulumi stack select dev`
2. Run `pulumi destroy -t "urn:pulumi:dev::sophia::aws:s3/bucket:Bucket::new-feature-bucket"`
3. Verify removal by checking [verification steps]

## Verification
How to verify the rollback was successful

## Additional Notes
Any special considerations or dependencies
```

## Security Practices

1. **Least Privilege**: Use minimal IAM permissions
2. **Secrets Management**: Use Pulumi or cloud-native secrets management
3. **Network Security**: Default-deny with specific allows
4. **Encryption**: Encrypt data at rest and in transit

## Monitoring and Observability

1. **Infrastructure Metrics**: CPU, memory, disk usage
2. **Application Metrics**: Request rates, latencies, error rates
3. **Logs**: Centralized logging with retention policies
4. **Alerts**: Critical thresholds with clear playbooks
