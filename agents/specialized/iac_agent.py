#!/usr/bin/env python3
"""
Infrastructure as Code (IaC) Agent - BaseAgent Pattern Implementation
Provides intelligent infrastructure management with Terraform, Kubernetes, and cloud automation
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import yaml

from agents.core.base_agent import AgentCapability, AgentConfig, AgentStatus, BaseAgent

class IaCTool(Enum):
    """Infrastructure as Code tools"""

    TERRAFORM = "terraform"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    ANSIBLE = "ansible"
    CLOUDFORMATION = "cloudformation"
    PULUMI = "pulumi"

class IaCOperation(Enum):
    """IaC operation types"""

    PLAN = "plan"
    APPLY = "apply"
    DESTROY = "destroy"
    VALIDATE = "validate"
    FORMAT = "format"
    INIT = "init"
    DEPLOY = "deploy"
    SCALE = "scale"
    ROLLBACK = "rollback"

class IaCEnvironment(Enum):
    """Infrastructure environments"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"

@dataclass
class IaCResource:
    """Infrastructure resource definition"""

    name: str
    type: str
    provider: str
    configuration: dict[str, Any]
    dependencies: list[str]
    tags: dict[str, str]

@dataclass
class IaCPlan:
    """Infrastructure plan result"""

    tool: IaCTool
    operation: IaCOperation
    environment: IaCEnvironment
    resources_to_create: list[IaCResource]
    resources_to_update: list[IaCResource]
    resources_to_destroy: list[IaCResource]
    estimated_cost: float
    risk_score: float
    validation_errors: list[str]
    warnings: list[str]

@dataclass
class IaCDeployment:
    """Infrastructure deployment result"""

    deployment_id: str
    plan: IaCPlan
    status: str
    start_time: datetime
    end_time: datetime | None
    resources_created: list[str]
    resources_updated: list[str]
    resources_destroyed: list[str]
    errors: list[str]
    logs: list[str]

class IaCAgent(BaseAgent):
    """
    Infrastructure as Code Agent with intelligent automation
    Provides safe, validated infrastructure operations with cost optimization
    """

    def __init__(self):
        """Initialize IaCAgent with BaseAgent pattern"""
        config = AgentConfig(
            agent_id="iac-agent",
            agent_name="Infrastructure as Code Agent",
            agent_type="infrastructure_automation",
            capabilities=[
                AgentCapability.ANALYSIS,
                AgentCapability.GENERATION,
                AgentCapability.VALIDATION,
                AgentCapability.OPTIMIZATION,
            ],
            max_concurrent_tasks=3,
        )
        super().__init__(config)

        # IaC-specific components
        self.terraform_binary = None
        self.kubectl_binary = None
        self.docker_binary = None
        self.working_directory = None
        self.state_backends = {}
        self.cost_calculator = None
        self.security_scanner = None

    async def _initialize_agent_specific(self) -> None:
        """Initialize IaC-specific components"""
        try:
            # Check for required tools
            await self._check_tool_availability()

            # Initialize working directory
            self.working_directory = os.path.join(tempfile.gettempdir(), "iac_agent")
            os.makedirs(self.working_directory, exist_ok=True)

            # Initialize state backends configuration
            self._initialize_state_backends()

            # Initialize cost calculator
            self._initialize_cost_calculator()

            # Initialize security scanner
            self._initialize_security_scanner()

            self.logger.info("IaC Agent initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize IaC Agent: {str(e)}")
            raise

    async def _process_task_impl(
        self, task_id: str, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process IaC operation tasks"""
        operation_type = task_data.get("operation_type")

        if not operation_type:
            raise ValueError("operation_type is required")

        try:
            operation_enum = IaCOperation(operation_type)
        except ValueError:
            raise ValueError(f"Unsupported operation type: {operation_type}")

        # Route to appropriate handler
        if operation_enum == IaCOperation.PLAN:
            return await self._handle_plan_operation(task_data)
        elif operation_enum == IaCOperation.APPLY:
            return await self._handle_apply_operation(task_data)
        elif operation_enum == IaCOperation.DESTROY:
            return await self._handle_destroy_operation(task_data)
        elif operation_enum == IaCOperation.VALIDATE:
            return await self._handle_validate_operation(task_data)
        elif operation_enum == IaCOperation.FORMAT:
            return await self._handle_format_operation(task_data)
        elif operation_enum == IaCOperation.INIT:
            return await self._handle_init_operation(task_data)
        elif operation_enum == IaCOperation.DEPLOY:
            return await self._handle_deploy_operation(task_data)
        elif operation_enum == IaCOperation.SCALE:
            return await self._handle_scale_operation(task_data)
        elif operation_enum == IaCOperation.ROLLBACK:
            return await self._handle_rollback_operation(task_data)
        else:
            raise ValueError(f"Handler not implemented for operation: {operation_type}")

    async def _cleanup_agent_specific(self) -> None:
        """Cleanup IaC-specific resources"""
        try:
            # Cleanup temporary files
            if self.working_directory and os.path.exists(self.working_directory):
                import shutil

                shutil.rmtree(self.working_directory, ignore_errors=True)

            self.logger.info("IaC Agent cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during IaC Agent cleanup: {str(e)}")

    # Public API methods
    async def create_infrastructure_plan(
        self,
        tool: IaCTool,
        environment: IaCEnvironment,
        config_path: str,
        variables: dict[str, Any] | None = None,
    ) -> IaCPlan:
        """Create an infrastructure plan"""
        try:
            self.logger.info(
                f"Creating infrastructure plan with {tool.value} for {environment.value}"
            )

            # Validate configuration
            validation_errors = await self._validate_configuration(tool, config_path)

            # Parse configuration
            resources = await self._parse_configuration(
                tool, config_path, variables or {}
            )

            # Calculate costs
            estimated_cost = await self._calculate_estimated_cost(resources)

            # Assess risk
            risk_score = await self._assess_risk(resources, environment)

            # Generate warnings
            warnings = await self._generate_warnings(resources, environment)

            plan = IaCPlan(
                tool=tool,
                operation=IaCOperation.PLAN,
                environment=environment,
                resources_to_create=resources,
                resources_to_update=[],
                resources_to_destroy=[],
                estimated_cost=estimated_cost,
                risk_score=risk_score,
                validation_errors=validation_errors,
                warnings=warnings,
            )

            self.logger.info(
                f"Infrastructure plan created: {len(resources)} resources, ${estimated_cost:.2f} estimated cost"
            )
            return plan

        except Exception as e:
            self.logger.error(f"Error creating infrastructure plan: {str(e)}")
            raise

    async def apply_infrastructure_plan(self, plan: IaCPlan) -> IaCDeployment:
        """Apply an infrastructure plan"""
        try:
            deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"Applying infrastructure plan: {deployment_id}")

            # Safety checks
            if plan.risk_score > 0.8:
                raise ValueError(f"Plan risk score too high: {plan.risk_score}")

            if plan.validation_errors:
                raise ValueError(
                    f"Plan has validation errors: {plan.validation_errors}"
                )

            # Create deployment record
            deployment = IaCDeployment(
                deployment_id=deployment_id,
                plan=plan,
                status="in_progress",
                start_time=datetime.now(),
                end_time=None,
                resources_created=[],
                resources_updated=[],
                resources_destroyed=[],
                errors=[],
                logs=[],
            )

            # Execute deployment based on tool
            if plan.tool == IaCTool.TERRAFORM:
                await self._apply_terraform_plan(plan, deployment)
            elif plan.tool == IaCTool.KUBERNETES:
                await self._apply_kubernetes_plan(plan, deployment)
            elif plan.tool == IaCTool.DOCKER:
                await self._apply_docker_plan(plan, deployment)
            else:
                raise ValueError(f"Unsupported tool for apply: {plan.tool}")

            deployment.end_time = datetime.now()
            deployment.status = "completed" if not deployment.errors else "failed"

            self.logger.info(
                f"Infrastructure deployment completed: {deployment.status}"
            )
            return deployment

        except Exception as e:
            self.logger.error(f"Error applying infrastructure plan: {str(e)}")
            raise

    async def validate_infrastructure_config(
        self, tool: IaCTool, config_path: str
    ) -> dict[str, Any]:
        """Validate infrastructure configuration"""
        try:
            self.logger.info(f"Validating {tool.value} configuration: {config_path}")

            validation_errors = await self._validate_configuration(tool, config_path)
            security_issues = await self._scan_security_issues(tool, config_path)
            best_practices = await self._check_best_practices(tool, config_path)

            result = {
                "valid": len(validation_errors) == 0,
                "validation_errors": validation_errors,
                "security_issues": security_issues,
                "best_practice_violations": best_practices,
                "recommendations": await self._generate_recommendations(
                    tool, config_path
                ),
            }

            self.logger.info(
                f"Configuration validation completed: {'valid' if result['valid'] else 'invalid'}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error validating configuration: {str(e)}")
            raise

    async def optimize_infrastructure_costs(
        self, resources: list[IaCResource]
    ) -> dict[str, Any]:
        """Optimize infrastructure costs"""
        try:
            self.logger.info("Analyzing infrastructure for cost optimization")

            current_cost = await self._calculate_estimated_cost(resources)
            optimizations = []

            for resource in resources:
                optimization = await self._analyze_resource_optimization(resource)
                if optimization:
                    optimizations.append(optimization)

            optimized_cost = sum(opt.get("new_cost", 0) for opt in optimizations)
            savings = current_cost - optimized_cost

            result = {
                "current_cost": current_cost,
                "optimized_cost": optimized_cost,
                "potential_savings": savings,
                "savings_percentage": (
                    (savings / current_cost * 100) if current_cost > 0 else 0
                ),
                "optimizations": optimizations,
            }

            self.logger.info(
                f"Cost optimization analysis completed: ${savings:.2f} potential savings"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error optimizing infrastructure costs: {str(e)}")
            raise

    # Private helper methods
    async def _handle_plan_operation(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """Handle plan operation task"""
        tool = IaCTool(task_data.get("tool", "terraform"))
        environment = IaCEnvironment(task_data.get("environment", "development"))
        config_path = task_data.get("config_path")
        variables = task_data.get("variables", {})

        if not config_path:
            raise ValueError("config_path is required for plan operation")

        plan = await self.create_infrastructure_plan(
            tool, environment, config_path, variables
        )

        return {
            "operation_type": "plan",
            "tool": plan.tool.value,
            "environment": plan.environment.value,
            "resources_to_create": len(plan.resources_to_create),
            "estimated_cost": plan.estimated_cost,
            "risk_score": plan.risk_score,
            "validation_errors": plan.validation_errors,
            "warnings": plan.warnings,
        }

    async def _handle_apply_operation(
        self, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle apply operation task"""
        # This would require a pre-created plan
        # For now, return a placeholder
        return {
            "operation_type": "apply",
            "success": False,
            "message": "Apply operation requires a pre-created plan",
        }

    async def _handle_destroy_operation(
        self, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle destroy operation task"""
        return {
            "operation_type": "destroy",
            "success": False,
            "message": "Destroy operation not yet implemented",
        }

    async def _handle_validate_operation(
        self, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle validate operation task"""
        tool = IaCTool(task_data.get("tool", "terraform"))
        config_path = task_data.get("config_path")

        if not config_path:
            raise ValueError("config_path is required for validate operation")

        result = await self.validate_infrastructure_config(tool, config_path)

        return {
            "operation_type": "validate",
            "valid": result["valid"],
            "validation_errors": result["validation_errors"],
            "security_issues": result["security_issues"],
            "recommendations": result["recommendations"],
        }

    async def _handle_format_operation(
        self, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle format operation task"""
        return {
            "operation_type": "format",
            "success": False,
            "message": "Format operation not yet implemented",
        }

    async def _handle_init_operation(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """Handle init operation task"""
        return {
            "operation_type": "init",
            "success": False,
            "message": "Init operation not yet implemented",
        }

    async def _handle_deploy_operation(
        self, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle deploy operation task"""
        return {
            "operation_type": "deploy",
            "success": False,
            "message": "Deploy operation not yet implemented",
        }

    async def _handle_scale_operation(
        self, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle scale operation task"""
        return {
            "operation_type": "scale",
            "success": False,
            "message": "Scale operation not yet implemented",
        }

    async def _handle_rollback_operation(
        self, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle rollback operation task"""
        return {
            "operation_type": "rollback",
            "success": False,
            "message": "Rollback operation not yet implemented",
        }

    async def _check_tool_availability(self) -> None:
        """Check availability of IaC tools"""
        tools_to_check = {
            "terraform": "terraform version",
            "kubectl": "kubectl version --client",
            "docker": "docker --version",
        }

        available_tools = {}

        for tool, command in tools_to_check.items():
            try:
                result = await self._run_command(command.split())
                available_tools[tool] = result.returncode == 0
                if available_tools[tool]:
                    self.logger.info(f"{tool} is available")
                else:
                    self.logger.warning(f"{tool} is not available")
            except Exception:
                available_tools[tool] = False
                self.logger.warning(f"{tool} is not available")

        # Set binary paths for available tools
        if available_tools.get("terraform"):
            self.terraform_binary = "terraform"
        if available_tools.get("kubectl"):
            self.kubectl_binary = "kubectl"
        if available_tools.get("docker"):
            self.docker_binary = "docker"

    def _initialize_state_backends(self) -> None:
        """Initialize state backend configurations"""
        self.state_backends = {
            "local": {"type": "local", "path": "./terraform.tfstate"},
            "s3": {
                "type": "s3",
                "bucket": "terraform-state",
                "region": "lambda-labs-us-west",
            },
            "gcs": {"type": "gcs", "bucket": "terraform-state"},
            "azure": {"type": "azurerm", "storage_account_name": "terraformstate"},
        }

    def _initialize_cost_calculator(self) -> None:
        """Initialize cost calculation engine"""
        # Mock cost calculator - in production, this would integrate with cloud pricing APIs
        self.cost_calculator = {
            "aws": {
                "ec2": {"t3.micro": 0.0104, "t3.small": 0.0208, "t3.medium": 0.0416},
                "rds": {"db.t3.micro": 0.017, "db.t3.small": 0.034},
                "s3": {"standard": 0.023},
            },
            "gcp": {
                "compute": {"e2-micro": 0.008, "e2-small": 0.016, "e2-medium": 0.032},
                "storage": {"standard": 0.020},
            },
            "azure": {
                "vm": {"B1s": 0.0104, "B2s": 0.0416},
                "storage": {"standard": 0.024},
            },
        }

    def _initialize_security_scanner(self) -> None:
        """Initialize security scanning rules"""
        self.security_scanner = {
            "terraform": {
                "high_risk_patterns": [
                    r"public_key\s*=\s*['\"][^'\"]+['\"]",
                    r"password\s*=\s*['\"][^'\"]+['\"]",
                    r"secret\s*=\s*['\"][^'\"]+['\"]",
                ],
                "best_practices": [
                    "Use variables for sensitive data",
                    "Enable encryption at rest",
                    "Use least privilege access",
                    "Enable logging and monitoring",
                ],
            }
        }

    async def _validate_configuration(
        self, tool: IaCTool, config_path: str
    ) -> list[str]:
        """Validate infrastructure configuration"""
        errors = []

        # Check if file exists
        if not os.path.exists(config_path):
            errors.append(f"Configuration file not found: {config_path}")
            return errors

        # Tool-specific validation
        if tool == IaCTool.TERRAFORM:
            errors.extend(await self._validate_terraform_config(config_path))
        elif tool == IaCTool.KUBERNETES:
            errors.extend(await self._validate_kubernetes_config(config_path))

        return errors

    async def _validate_terraform_config(self, config_path: str) -> list[str]:
        """Validate Terraform configuration"""
        errors = []

        try:
            # Basic syntax validation
            with open(config_path) as f:
                content = f.read()

            # Check for basic Terraform syntax
            if not any(
                keyword in content
                for keyword in ["resource", "provider", "variable", "output"]
            ):
                errors.append(
                    "No Terraform resources, providers, variables, or outputs found"
                )

            # Check for required providers
            if "provider" not in content:
                errors.append("No provider configuration found")

        except Exception as e:
            errors.append(f"Error reading configuration file: {str(e)}")

        return errors

    async def _validate_kubernetes_config(self, config_path: str) -> list[str]:
        """Validate Kubernetes configuration"""
        errors = []

        try:
            with open(config_path) as f:
                docs = yaml.safe_load_all(f)

                for doc in docs:
                    if not doc:
                        continue

                    # Check for required fields
                    if "apiVersion" not in doc:
                        errors.append("Missing apiVersion in Kubernetes manifest")
                    if "kind" not in doc:
                        errors.append("Missing kind in Kubernetes manifest")
                    if "metadata" not in doc:
                        errors.append("Missing metadata in Kubernetes manifest")

        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML syntax: {str(e)}")
        except Exception as e:
            errors.append(f"Error reading Kubernetes configuration: {str(e)}")

        return errors

    async def _parse_configuration(
        self, tool: IaCTool, config_path: str, variables: dict[str, Any]
    ) -> list[IaCResource]:
        """Parse configuration and extract resources"""
        resources = []

        try:
            if tool == IaCTool.TERRAFORM:
                resources = await self._parse_terraform_config(config_path, variables)
            elif tool == IaCTool.KUBERNETES:
                resources = await self._parse_kubernetes_config(config_path)

        except Exception as e:
            self.logger.error(f"Error parsing configuration: {str(e)}")

        return resources

    async def _parse_terraform_config(
        self, config_path: str, variables: dict[str, Any]
    ) -> list[IaCResource]:
        """Parse Terraform configuration"""

        # Mock parsing - in production, this would use Terraform's JSON output
        actual_resources = [
            IaCResource(
                name="example_instance",
                type="LAMBDA_LABS_CONFIG",
                provider="aws",
                configuration={"instance_type": "t3.micro", "ami": "ami-12345"},
                dependencies=[],
                tags={"Environment": "development"},
            )
        ]

        return actual_resources

    async def _parse_kubernetes_config(self, config_path: str) -> list[IaCResource]:
        """Parse Kubernetes configuration"""
        resources = []

        try:
            with open(config_path) as f:
                docs = yaml.safe_load_all(f)

                for doc in docs:
                    if not doc:
                        continue

                    resource = IaCResource(
                        name=doc.get("metadata", {}).get("name", "unknown"),
                        type=doc.get("kind", "unknown"),
                        provider="kubernetes",
                        configuration=doc.get("spec", {}),
                        dependencies=[],
                        tags=doc.get("metadata", {}).get("labels", {}),
                    )
                    resources.append(resource)

        except Exception as e:
            self.logger.error(f"Error parsing Kubernetes config: {str(e)}")

        return resources

    async def _calculate_estimated_cost(self, resources: list[IaCResource]) -> float:
        """Calculate estimated cost for resources"""
        total_cost = 0.0

        for resource in resources:
            cost = await self._calculate_resource_cost(resource)
            total_cost += cost

        return total_cost

    async def _calculate_resource_cost(self, resource: IaCResource) -> float:
        """Calculate cost for a single resource"""
        # Mock cost calculation
        if resource.provider == "aws":
            if resource.type == "LAMBDA_LABS_CONFIG":
                instance_type = resource.configuration.get("instance_type", "t3.micro")
                return (
                    self.cost_calculator["aws"]["ec2"].get(instance_type, 0.0) * 24 * 30
                )  # Monthly cost

        return 0.0

    async def _assess_risk(
        self, resources: list[IaCResource], environment: IaCEnvironment
    ) -> float:
        """Assess risk score for infrastructure changes"""
        risk_factors = []

        # Environment risk
        env_risk = {
            IaCEnvironment.DEVELOPMENT: 0.1,
            IaCEnvironment.TEST: 0.2,
            IaCEnvironment.STAGING: 0.5,
            IaCEnvironment.PRODUCTION: 0.8,
        }
        risk_factors.append(env_risk.get(environment, 0.5))

        # Resource count risk
        resource_count_risk = min(
            len(resources) / 50, 0.5
        )  # More resources = higher risk
        risk_factors.append(resource_count_risk)

        # Resource type risk
        high_risk_types = [
            "LAMBDA_LABS_CONFIG",
            "LAMBDA_LABS_CONFIG",
            "LAMBDA_LABS_CONFIG3_bucket",
        ]
        high_risk_count = sum(1 for r in resources if r.type in high_risk_types)
        type_risk = min(high_risk_count / 10, 0.3)
        risk_factors.append(type_risk)

        return sum(risk_factors) / len(risk_factors) if risk_factors else 0.0

    async def _generate_warnings(
        self, resources: list[IaCResource], environment: IaCEnvironment
    ) -> list[str]:
        """Generate warnings for infrastructure plan"""
        warnings = []

        # Check for production environment
        if environment == IaCEnvironment.PRODUCTION:
            warnings.append(
                "Deploying to production environment - extra caution required"
            )

        # Check for high-cost resources
        for resource in resources:
            cost = await self._calculate_resource_cost(resource)
            if cost > 100:  # $100/month threshold
                warnings.append(
                    f"High-cost resource detected: {resource.name} (${cost:.2f}/month)"
                )

        return warnings

    async def _scan_security_issues(self, tool: IaCTool, config_path: str) -> list[str]:
        """Scan for security issues in configuration"""
        issues = []

        try:
            with open(config_path) as f:
                content = f.read()

            # Check for hardcoded secrets
            if tool in self.security_scanner:
                patterns = self.security_scanner[tool.value]["high_risk_patterns"]
                for pattern in patterns:
                    import re

                    if re.search(pattern, content, re.IGNORECASE):
                        issues.append(f"Potential hardcoded secret detected: {pattern}")

        except Exception as e:
            issues.append(f"Error scanning for security issues: {str(e)}")

        return issues

    async def _check_best_practices(self, tool: IaCTool, config_path: str) -> list[str]:
        """Check for best practice violations"""
        violations = []

        # Mock best practice checks
        violations.append("Consider using remote state backend")
        violations.append("Add resource tags for better organization")

        return violations

    async def _generate_recommendations(
        self, tool: IaCTool, config_path: str
    ) -> list[str]:
        """Generate recommendations for improvement"""
        recommendations = []

        if tool in self.security_scanner:
            recommendations.extend(self.security_scanner[tool.value]["best_practices"])

        recommendations.extend(
            [
                "Use version constraints for providers",
                "Implement proper backup strategies",
                "Set up monitoring and alerting",
            ]
        )

        return recommendations

    async def _analyze_resource_optimization(
        self, resource: IaCResource
    ) -> dict[str, Any] | None:
        """Analyze optimization opportunities for a resource"""
        # Mock optimization analysis
        if resource.type == "LAMBDA_LABS_CONFIG":
            instance_type = resource.configuration.get("instance_type")
            if instance_type == "t3.medium":
                return {
                    "resource": resource.name,
                    "current_cost": 30.0,
                    "new_cost": 15.0,
                    "optimization": "Downgrade to t3.small",
                    "savings": 15.0,
                }

        return None

    async def _apply_terraform_plan(
        self, plan: IaCPlan, deployment: IaCDeployment
    ) -> IaCDeployment:
        """Apply Terraform plan"""
        # Mock Terraform apply
        deployment.logs.append("Initializing Terraform...")
        deployment.logs.append("Planning infrastructure changes...")
        deployment.logs.append("Applying changes...")

        for resource in plan.resources_to_create:
            deployment.resources_created.append(resource.name)
            deployment.logs.append(f"Created resource: {resource.name}")

        return deployment

    async def _apply_kubernetes_plan(
        self, plan: IaCPlan, deployment: IaCDeployment
    ) -> IaCDeployment:
        """Apply Kubernetes plan"""
        # Mock Kubernetes apply
        deployment.logs.append("Applying Kubernetes manifests...")

        for resource in plan.resources_to_create:
            deployment.resources_created.append(resource.name)
            deployment.logs.append(f"Created Kubernetes resource: {resource.name}")

        return deployment

    async def _apply_docker_plan(
        self, plan: IaCPlan, deployment: IaCDeployment
    ) -> IaCDeployment:
        """Apply Docker plan"""
        # Mock Docker deployment
        deployment.logs.append("Building Docker images...")
        deployment.logs.append("Deploying containers...")

        for resource in plan.resources_to_create:
            deployment.resources_created.append(resource.name)
            deployment.logs.append(f"Deployed container: {resource.name}")

        return deployment

    async def _run_command(self, command: list[str]) -> subprocess.CompletedProcess:
        """Run a command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_directory,
            )

            stdout, stderr = await process.communicate()

            return subprocess.CompletedProcess(
                args=command,
                returncode=process.returncode,
                stdout=stdout.decode("utf-8") if stdout else "",
                stderr=stderr.decode("utf-8") if stderr else "",
            )

        except Exception as e:
            self.logger.error(f"Error running command {command}: {str(e)}")
            raise

# Factory function for easy instantiation
def create_iac_agent() -> IaCAgent:
    """Create and return an IaCAgent instance"""
    return IaCAgent()

# Entry point for immediate execution
async def main():
    """Main execution function for IaC operations"""
    agent = IaCAgent()
    await agent.initialize()

    try:
        # Example: Create infrastructure plan
        result = await agent.process_task(
            "iac-plan",
            {
                "operation_type": "plan",
                "tool": "terraform",
                "environment": "development",
                "config_path": "/tmp/main.tf",
                "variables": {"instance_type": "t3.micro"},
            },
        )

        print("🏗️ Infrastructure Plan Created")
        print(f"📊 Plan Result: {result}")

    finally:
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
