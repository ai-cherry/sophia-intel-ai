#!/usr/bin/env python3
"""
Docker Hub Authentication Fix Script
Fixes Docker Hub authentication issues and adds auto-rotation capabilities.
"""

import json
import os
import subprocess
from pathlib import Path


class DockerAuthFixer:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.workflows_dir = self.repo_root / ".github" / "workflows"
        self.docker_compose_file = self.repo_root / "docker-compose.yml"

    def check_docker_hub_auth(self):
        """Check current Docker Hub authentication status"""
        print("🔍 Checking Docker Hub authentication status...")

        try:
            # Try to login with current credentials
            result = subprocess.run(
                [
                    "docker",
                    "login",
                    "--username",
                    os.getenv("DOCKER_USERNAME", ""),
                    "--password-stdin",
                ],
                input=os.getenv("DOCKER_TOKEN", "").encode(),
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Docker Hub authentication is working")
                return True
            else:
                print(f"❌ Docker Hub authentication failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error checking Docker Hub auth: {e}")
            return False

    def update_github_secrets_template(self):
        """Create template for updating GitHub secrets"""
        secrets_template = {
            "DOCKER_USERNAME": "your_docker_hub_username",
            "DOCKER_TOKEN": "your_docker_hub_access_token",
            "DOCKER_REGISTRY": "docker.io",
            "DOCKER_REPOSITORY": "sophia-ai",
        }

        template_file = self.repo_root / ".github" / "secrets-template.json"
        with open(template_file, "w") as f:
            json.dump(secrets_template, f, indent=2)

        print(f"📝 Created secrets template at {template_file}")
        print("🔧 Please update GitHub repository secrets with these values:")
        for key, value in secrets_template.items():
            print(f"   {key}: {value}")

    def fix_workflow_docker_auth(self):
        """Fix Docker authentication in GitHub workflows"""
        print("🔧 Fixing Docker authentication in workflows...")

        for workflow_file in self.workflows_dir.glob("*.yml"):
            if not workflow_file.exists():
                continue

            with open(workflow_file) as f:
                content = f.read()

            # Check if workflow uses Docker
            if "docker" not in content.lower():
                continue

            print(f"📝 Updating {workflow_file.name}...")

            # Add Docker login step template
            docker_login_step = """
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_TOKEN }}
          registry: docker.io
"""

            # Check if Docker login already exists
            if "docker/login-action" not in content:
                # Find a good place to insert the login step
                lines = content.split("\n")
                updated_lines = []

                for i, line in enumerate(lines):
                    updated_lines.append(line)

                    # Insert after checkout step
                    if "uses: actions/checkout@" in line:
                        updated_lines.extend(docker_login_step.split("\n"))

                # Write updated content
                with open(workflow_file, "w") as f:
                    f.write("\n".join(updated_lines))

                print(f"✅ Added Docker login to {workflow_file.name}")
            else:
                print(f"ℹ️ Docker login already exists in {workflow_file.name}")

    def create_docker_health_check(self):
        """Create Pulumi health check for Docker registry"""
        health_check_script = """#!/usr/bin/env python3
\"\"\"
Docker Registry Health Check for Pulumi
Monitors Docker Hub registry health and authentication status.
\"\"\"

import pulumi
import pulumi_aws as aws
import json

def create_docker_registry_health_check():
    \"\"\"Create CloudWatch alarm for Docker registry health\"\"\"

    # Lambda function for health check
    health_check_lambda = aws.lambda_.Function(
        "docker-registry-health-check",
        runtime="python3.12",
        handler="index.handler",
        role=lambda_role.arn,
        code=pulumi.AssetArchive({
            "index.py": pulumi.StringAsset('''
import json
import boto3
import requests
from datetime import datetime

def handler(event, context):
    try:
        # Check Docker Hub API status
        response = requests.get("https://hub.docker.com/v2/repositories/library/hello-world/")

        if response.status_code == 200:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat(),
                    'registry': 'docker.io'
                })
            }
        else:
            raise Exception(f"Docker Hub API returned {response.status_code}")

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
            ''')
        }),
        timeout=30,
        environment={
            "variables": {
                "DOCKER_REGISTRY": "docker.io"
            }
        }
    )

    # CloudWatch alarm
    docker_health_alarm = aws.cloudwatch.MetricAlarm(
        "docker-registry-health-alarm",
        comparison_operator="LessThanThreshold",
        evaluation_periods=2,
        metric_name="Duration",
        namespace="AWS/Lambda",
        period=300,
        statistic="Average",
        threshold=1000,
        alarm_description="Docker registry health check",
        dimensions={
            "FunctionName": health_check_lambda.name
        },
        alarm_actions=[
            # Add SNS topic ARN for notifications
        ]
    )

    return health_check_lambda, docker_health_alarm

# Create IAM role for Lambda
lambda_role = aws.iam.Role(
    "docker-health-check-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            }
        }]
    })
)

# Attach basic execution policy
aws.iam.RolePolicyAttachment(
    "docker-health-check-policy",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
)

# Create the health check
health_check_lambda, health_alarm = create_docker_registry_health_check()

# Export outputs
pulumi.export("docker_health_check_function", health_check_lambda.name)
pulumi.export("docker_health_alarm", health_alarm.name)
"""

        pulumi_dir = self.repo_root / "infrastructure" / "pulumi" / "monitoring"
        pulumi_dir.mkdir(parents=True, exist_ok=True)

        health_check_file = pulumi_dir / "docker_registry_health.py"
        with open(health_check_file, "w") as f:
            f.write(health_check_script)

        print(f"📝 Created Docker registry health check at {health_check_file}")

    def create_auto_rotation_script(self):
        """Create automated Docker token rotation script"""
        rotation_script = """#!/usr/bin/env python3
\"\"\"
Automated Docker Hub Token Rotation Script
Rotates Docker Hub access tokens and updates GitHub secrets.
\"\"\"

import os
import sys
import requests
import json
from datetime import datetime, timedelta
import subprocess

class DockerTokenRotator:
    def __init__(self):
        self.docker_username = os.getenv("DOCKER_USERNAME")
        self.docker_password = os.getenv("DOCKER_PASSWORD")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv("GITHUB_REPOSITORY", "sophia-ai/sophia-main")

    def create_new_docker_token(self):
        \"\"\"Create new Docker Hub access token\"\"\"
        print("🔄 Creating new Docker Hub access token...")

        # Docker Hub API endpoint for token creation
        url = "https://hub.docker.com/v2/app/"

        login_data = {
            "username": self.docker_username,
            "password": self.docker_password
        }

        try:
            # Login to get JWT token
            response = requests.post(url, json=login_data)
            response.raise_for_status()

            jwt_token = response.json().get("token")

            # Create new access token
            token_url = "https://hub.docker.com/v2/access-tokens/"
            headers = {"Authorization": f"JWT {jwt_token}"}

            token_data = {
                "description": f"Sophia AI Auto-Rotation {datetime.now().strftime('%Y-%m-%d')}",
                "scopes": ["repo:write", "repo:read"]
            }

            token_response = requests.post(token_url, json=token_data, headers=headers)
            token_response.raise_for_status()

            new_token = token_response.json().get("token")
            print("✅ New Docker Hub token created successfully")

            return new_token

        except Exception as e:
            print(f"❌ Failed to create Docker Hub token: {e}")
            return None

    def update_github_secret(self, secret_name, secret_value):
        \"\"\"Update GitHub repository secret\"\"\"
        print(f"🔄 Updating GitHub secret: {secret_name}")

        try:
            # Use GitHub CLI to update secret
            cmd = [
                "gh", "secret", "set", secret_name,
                "--body", secret_value,
                "--repo", self.github_repo
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ GitHub secret {secret_name} updated successfully")
                return True
            else:
                print(f"❌ Failed to update GitHub secret: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error updating GitHub secret: {e}")
            return False

    def revoke_old_tokens(self):
        \"\"\"Revoke old Docker Hub tokens\"\"\"
        print("🔄 Revoking old Docker Hub tokens...")

        # This would require additional API calls to list and revoke old tokens
        # Implementation depends on Docker Hub API capabilities
        print("ℹ️ Manual token cleanup recommended via Docker Hub dashboard")

    def rotate_token(self):
        \"\"\"Main token rotation process\"\"\"
        print("🚀 Starting Docker Hub token rotation...")

        # Create new token
        new_token = self.create_new_docker_token()
        if not new_token:
            return False

        # Update GitHub secret
        if not self.update_github_secret("DOCKER_TOKEN", new_token):
            return False

        # Test new token
        if self.sophia_new_token(new_token):
            print("✅ Token rotation completed successfully")

            # Schedule old token revocation (optional)
            # self.revoke_old_tokens()

            return True
        else:
            print("❌ Token rotation failed - new token doesn't work")
            return False

    def sophia_new_token(self, token):
        \"\"\"Test the new Docker token\"\"\"
        print("🧪 Testing new Docker token...")

        try:
            result = subprocess.run(
                ["docker", "login", "--username", self.docker_username, "--password-stdin"],
                input=token.encode(),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("✅ New token works correctly")
                return True
            else:
                print(f"❌ New token test failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error testing new token: {e}")
            return False

if __name__ == "__main__":
    rotator = DockerTokenRotator()

    if rotator.rotate_token():
        sys.exit(0)
    else:
        sys.exit(1)
"""

        scripts_dir = self.repo_root / "scripts" / "security"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        rotation_file = scripts_dir / "rotate_docker_token.py"
        with open(rotation_file, "w") as f:
            f.write(rotation_script)

        # Make script executable
        os.chmod(rotation_file, 0o755)

        print(f"📝 Created auto-rotation script at {rotation_file}")

    def run_fixes(self):
        """Run all Docker authentication fixes"""
        print("🚀 Starting Docker Hub authentication fixes...")

        # Check current status
        auth_working = self.check_docker_hub_auth()

        # Create fixes regardless of current status
        self.update_github_secrets_template()
        self.fix_workflow_docker_auth()
        self.create_docker_health_check()
        self.create_auto_rotation_script()

        print("\n✅ Docker Hub authentication fixes completed!")
        print("\n📋 Next steps:")
        print("1. Update GitHub repository secrets with new Docker Hub credentials")
        print("2. Test workflow deployments")
        print("3. Deploy Pulumi health check monitoring")
        print("4. Schedule automated token rotation")

        if not auth_working:
            print("\n⚠️ Current Docker authentication is not working.")
            print("   Please update DOCKER_USERNAME and DOCKER_TOKEN environment variables")
            print("   or GitHub repository secrets before running deployments.")


def main():
    fixer = DockerAuthFixer()
    fixer.run_fixes()


if __name__ == "__main__":
    main()
