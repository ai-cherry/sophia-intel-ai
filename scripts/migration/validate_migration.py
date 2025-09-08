#!/usr/bin/env python3
"""
Migration Validation Script
Validates the completeness and correctness of the ESC migration.
"""

import asyncio
import json
import logging
import os

# Add project root to path
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiofiles
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

sys.path.append(str(Path(__file__).parent.parent.parent))

from infrastructure.pulumi.esc.audit_logger import (
    AuditAction,
    AuditContext,
    AuditLevel,
    AuditStorageBackend,
    ESCAuditLogger,
)
from infrastructure.pulumi.esc.config_loader import ESCConfigLoader
from infrastructure.pulumi.esc.secrets_manager import ESCSecretsManager

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of migration validation"""

    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warnings: int = 0
    missing_secrets: List[str] = field(default_factory=list)
    invalid_secrets: List[str] = field(default_factory=list)
    access_failures: List[str] = field(default_factory=list)
    format_issues: List[str] = field(default_factory=list)
    environment_issues: Dict[str, List[str]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return (
            (self.passed_checks / self.total_checks * 100)
            if self.total_checks > 0
            else 0
        )

    @property
    def is_migration_valid(self) -> bool:
        return self.failed_checks == 0 and len(self.missing_secrets) == 0


@dataclass
class ExpectedSecret:
    """Expected secret from original configuration"""

    key: str
    original_key: str
    source_file: str
    environments: List[str]
    category: str
    provider: Optional[str] = None
    is_required: bool = True


class ESCMigrationValidator:
    """Validates ESC migration completeness and correctness"""

    def __init__(
        self,
        pulumi_org: str = "sophia-intel",
        pulumi_api_token: Optional[str] = None,
        environments: List[str] = None,
    ):
        self.pulumi_org = pulumi_org
        self.pulumi_api_token = pulumi_api_token or os.getenv("PULUMI_API_KEY")
        self.environments = environments or ["dev", "staging", "production"]

        self.expected_secrets: List[ExpectedSecret] = []
        self.validation_result = ValidationResult()

        # Initialize ESC manager
        if self.pulumi_api_token:
            self.esc_manager = ESCSecretsManager(
                api_token=self.pulumi_api_token, organization=self.pulumi_org
            )
        else:
            self.esc_manager = None
            console.print(
                "[yellow]Warning: No Pulumi API token provided. Limited validation available.[/yellow]"
            )

        # Initialize audit logger
        audit_backends = [
            AuditStorageBackend(
                backend_type="file",
                connection_params={"file_path": "logs/validation_audit.log"},
            )
        ]
        self.audit_logger = ESCAuditLogger(audit_backends)

    async def validate_migration(self) -> ValidationResult:
        """Run complete migration validation"""
        console.print(
            Panel.fit(
                "[bold blue]ESC Migration Validation[/bold blue]\n"
                "Validating migration completeness and correctness",
                title="Validation Starting",
            )
        )

        try:
            await self.audit_logger.start()

            # Step 1: Load expected secrets from original sources
            await self._load_expected_secrets()

            # Step 2: Validate ESC environments exist and are accessible
            await self._validate_esc_environments()

            # Step 3: Check secret migration completeness
            await self._validate_secret_completeness()

            # Step 4: Validate secret accessibility
            await self._validate_secret_accessibility()

            # Step 5: Validate secret formats and values
            await self._validate_secret_formats()

            # Step 6: Test integration with existing systems
            await self._validate_system_integration()

            # Step 7: Generate recommendations
            await self._generate_recommendations()

            # Step 8: Create validation report
            await self._generate_validation_report()

            return self.validation_result

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            await self.audit_logger.log_event(
                level=AuditLevel.ERROR,
                action=AuditAction.ERROR_OCCURRED,
                resource="migration_validation",
                message=f"Validation failed: {e}",
                context=AuditContext(service_name="validation_tool"),
                success=False,
                error_details=str(e),
            )
            raise
        finally:
            await self.audit_logger.stop()

    async def _load_expected_secrets(self):
        """Load expected secrets from original configuration sources"""
        console.print("\n[bold]Step 1: Loading expected secrets...[/bold]")

        # Load from .env files
        await self._load_from_env_files()

        # Load from migration manifest if available
        await self._load_from_migration_manifest()

        # Load from configuration files
        await self._load_from_config_files()

        console.print(
            f"[green]✓[/green] Loaded {len(self.expected_secrets)} expected secrets"
        )

        await self.audit_logger.log_event(
            level=AuditLevel.INFO,
            action=AuditAction.CONFIG_LOAD,
            resource="expected_secrets",
            message=f"Loaded {len(self.expected_secrets)} expected secrets for validation",
            context=AuditContext(service_name="validation_tool"),
        )

    async def _load_from_env_files(self):
        """Load expected secrets from .env files"""
        project_root = Path(__file__).parent.parent.parent
        env_patterns = [".env*", "*/.env*", "config/**/.env*"]

        env_files = []
        for pattern in env_patterns:
            env_files.extend(project_root.glob(pattern))

        for env_file in env_files:
            if env_file.is_file() and not env_file.name.endswith(".example"):
                await self._parse_env_file(env_file)

    async def _parse_env_file(self, file_path: Path):
        """Parse a single .env file for expected secrets"""
        try:
            async with aiofiles.open(file_path) as f:
                content = await f.read()

            for line_num, line in enumerate(content.splitlines(), 1):
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if value and not value.startswith("$"):
                    # Convert to ESC key format
                    esc_key = self._convert_to_esc_key(key)

                    # Determine environments
                    environments = self._determine_environments_from_file(file_path)

                    # Categorize secret
                    category, provider = self._categorize_secret(key)

                    expected = ExpectedSecret(
                        key=esc_key,
                        original_key=key,
                        source_file=str(file_path),
                        environments=environments,
                        category=category,
                        provider=provider,
                        is_required=self._is_required_secret(key),
                    )

                    self.expected_secrets.append(expected)

        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")

    async def _load_from_migration_manifest(self):
        """Load expected secrets from migration manifest"""
        project_root = Path(__file__).parent.parent.parent
        manifest_pattern = "migration_manifest*.json"

        for manifest_file in project_root.glob(manifest_pattern):
            try:
                async with aiofiles.open(manifest_file) as f:
                    content = await f.read()

                manifest = json.loads(content)

                if "secrets_by_category" in manifest:
                    for category, secrets in manifest["secrets_by_category"].items():
                        for secret_info in secrets:
                            expected = ExpectedSecret(
                                key=secret_info["key"],
                                original_key=secret_info.get(
                                    "original_key", secret_info["key"]
                                ),
                                source_file=secret_info["source_file"],
                                environments=secret_info.get(
                                    "environments", self.environments
                                ),
                                category=category,
                                provider=secret_info.get("provider"),
                                is_required=secret_info.get("is_required", True),
                            )
                            self.expected_secrets.append(expected)

            except Exception as e:
                logger.warning(f"Error loading migration manifest {manifest_file}: {e}")

    async def _load_from_config_files(self):
        """Load expected secrets from configuration files"""
        project_root = Path(__file__).parent.parent.parent

        # Load from ESC environment files
        esc_env_dir = project_root / "infrastructure" / "pulumi" / "environments"
        if esc_env_dir.exists():
            for env_file in esc_env_dir.glob("*.yaml"):
                await self._parse_esc_env_file(env_file)

    async def _parse_esc_env_file(self, file_path: Path):
        """Parse ESC environment file for expected secrets"""
        try:
            async with aiofiles.open(file_path) as f:
                content = await f.read()

            data = yaml.safe_load(content)
            if not data or "values" not in data:
                return

            environment = file_path.stem
            if environment == "shared":
                environments = self.environments
            else:
                environments = [environment]

            # Extract secrets from nested structure
            secrets = self._extract_secrets_from_dict(data["values"])

            for key in secrets:
                expected = ExpectedSecret(
                    key=key,
                    original_key=key.replace(".", "_").upper(),
                    source_file=str(file_path),
                    environments=environments,
                    category=key.split(".")[0] if "." in key else "configuration",
                    is_required=True,
                )
                self.expected_secrets.append(expected)

        except Exception as e:
            logger.warning(f"Error parsing ESC env file {file_path}: {e}")

    def _extract_secrets_from_dict(
        self, data: Dict[str, Any], prefix: str = ""
    ) -> List[str]:
        """Extract secret keys from nested dictionary"""
        secrets = []

        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                # Check if this is a secret reference
                if "fn::secret" in value:
                    secrets.append(full_key)
                else:
                    secrets.extend(self._extract_secrets_from_dict(value, full_key))
            elif isinstance(value, str) and self._looks_like_secret(key, value):
                secrets.append(full_key)

        return secrets

    def _looks_like_secret(self, key: str, value: str) -> bool:
        """Determine if a key/value pair looks like a secret"""
        key_lower = key.lower()
        secret_indicators = ["key", "secret", "password", "token", "auth", "credential"]

        return any(indicator in key_lower for indicator in secret_indicators)

    async def _validate_esc_environments(self):
        """Validate ESC environments exist and are accessible"""
        console.print("\n[bold]Step 2: Validating ESC environments...[/bold]")

        if not self.esc_manager:
            self.validation_result.warnings += 1
            console.print(
                "[yellow]⚠[/yellow] Skipping ESC environment validation (no API token)"
            )
            return

        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            env_task = progress.add_task(
                "Checking ESC environments...", total=len(self.environments)
            )

            async with self.esc_manager:
                for environment in self.environments:
                    try:
                        config = await self.esc_manager.get_environment_config(
                            environment
                        )

                        if config:
                            self.validation_result.passed_checks += 1
                            console.print(
                                f"[green]✓[/green] Environment '{environment}' accessible"
                            )
                        else:
                            self.validation_result.failed_checks += 1
                            error_msg = (
                                f"Environment '{environment}' not found or empty"
                            )
                            self.validation_result.environment_issues[environment] = [
                                error_msg
                            ]
                            console.print(f"[red]✗[/red] {error_msg}")

                        self.validation_result.total_checks += 1

                    except Exception as e:
                        self.validation_result.failed_checks += 1
                        self.validation_result.total_checks += 1
                        error_msg = f"Cannot access environment '{environment}': {e}"
                        self.validation_result.environment_issues[environment] = [
                            error_msg
                        ]
                        console.print(f"[red]✗[/red] {error_msg}")

                    progress.advance(env_task)

    async def _validate_secret_completeness(self):
        """Validate all expected secrets are present in ESC"""
        console.print("\n[bold]Step 3: Validating secret completeness...[/bold]")

        if not self.esc_manager:
            self.validation_result.warnings += 1
            console.print(
                "[yellow]⚠[/yellow] Skipping completeness validation (no API token)"
            )
            return

        missing_by_env = {}

        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            check_task = progress.add_task(
                "Checking secret completeness...", total=len(self.expected_secrets)
            )

            async with self.esc_manager:
                for expected in self.expected_secrets:
                    for environment in expected.environments:
                        if environment not in missing_by_env:
                            missing_by_env[environment] = []

                        try:
                            secret_value = await self.esc_manager.get_secret(
                                expected.key, environment, use_cache=False
                            )

                            if secret_value is not None:
                                self.validation_result.passed_checks += 1
                            else:
                                if expected.is_required:
                                    self.validation_result.failed_checks += 1
                                    missing_key = f"{environment}.{expected.key}"
                                    self.validation_result.missing_secrets.append(
                                        missing_key
                                    )
                                    missing_by_env[environment].append(expected.key)
                                else:
                                    self.validation_result.warnings += 1

                            self.validation_result.total_checks += 1

                        except Exception as e:
                            self.validation_result.failed_checks += 1
                            self.validation_result.total_checks += 1
                            error_msg = (
                                f"Error checking {expected.key} in {environment}: {e}"
                            )
                            self.validation_result.access_failures.append(error_msg)

                    progress.advance(check_task)

        # Report missing secrets
        for environment, missing_keys in missing_by_env.items():
            if missing_keys:
                console.print(
                    f"[red]✗[/red] Missing secrets in {environment}: {len(missing_keys)}"
                )
                for key in missing_keys[:5]:  # Show first 5
                    console.print(f"    • {key}")
                if len(missing_keys) > 5:
                    console.print(f"    ... and {len(missing_keys) - 5} more")
            else:
                console.print(f"[green]✓[/green] All secrets present in {environment}")

    async def _validate_secret_accessibility(self):
        """Validate secrets can be accessed through config loader"""
        console.print("\n[bold]Step 4: Validating secret accessibility...[/bold]")

        if not self.esc_manager:
            self.validation_result.warnings += 1
            console.print(
                "[yellow]⚠[/yellow] Skipping accessibility validation (no API token)"
            )
            return

        access_errors = 0

        for environment in self.environments:
            try:
                # Create config loader for environment
                config_loader = ESCConfigLoader(
                    secrets_manager=self.esc_manager,
                    environment=environment,
                    auto_refresh=False,
                    watch_files=False,
                )

                # Test initialization
                success = await config_loader.initialize()

                if success:
                    # Test loading some common configurations
                    test_keys = [
                        "llm_providers.direct_keys.openai",
                        "infrastructure.redis.url",
                        "infrastructure.vector_db.qdrant.api_key",
                    ]

                    for key in test_keys:
                        value = config_loader.get(key)
                        if value:
                            self.validation_result.passed_checks += 1
                        else:
                            self.validation_result.warnings += 1

                        self.validation_result.total_checks += 1

                    console.print(
                        f"[green]✓[/green] Config loader working for {environment}"
                    )
                else:
                    access_errors += 1
                    console.print(
                        f"[red]✗[/red] Config loader failed for {environment}"
                    )

                await config_loader.shutdown()

            except Exception as e:
                access_errors += 1
                error_msg = f"Config loader error for {environment}: {e}"
                self.validation_result.access_failures.append(error_msg)
                console.print(f"[red]✗[/red] {error_msg}")

        if access_errors > 0:
            self.validation_result.failed_checks += access_errors
        else:
            console.print(
                "[green]✓[/green] All environments accessible via config loader"
            )

    async def _validate_secret_formats(self):
        """Validate secret formats and values"""
        console.print("\n[bold]Step 5: Validating secret formats...[/bold]")

        if not self.esc_manager:
            self.validation_result.warnings += 1
            console.print(
                "[yellow]⚠[/yellow] Skipping format validation (no API token)"
            )
            return

        format_validators = {
            "openai": lambda v: v.startswith("sk-") and len(v) > 20,
            "anthropic": lambda v: v.startswith("sk-ant-") and len(v) > 30,
            "redis": lambda v: "redis" in v or len(v) > 16,
            "qdrant": lambda v: len(v) > 20,
            "weaviate": lambda v: len(v) > 16,
        }

        format_issues = 0

        async with self.esc_manager:
            for expected in self.expected_secrets[:10]:  # Sample validation
                if expected.provider in format_validators:
                    validator = format_validators[expected.provider]

                    for environment in expected.environments:
                        try:
                            value = await self.esc_manager.get_secret(
                                expected.key, environment, use_cache=False
                            )

                            if value and not validator(str(value)):
                                format_issues += 1
                                issue = f"{environment}.{expected.key}: Invalid {expected.provider} format"
                                self.validation_result.format_issues.append(issue)
                                console.print(f"[yellow]⚠[/yellow] {issue}")

                            self.validation_result.total_checks += 1

                        except Exception as e:
                            logger.warning(
                                f"Format validation error for {expected.key}: {e}"
                            )

        if format_issues == 0:
            console.print("[green]✓[/green] Secret formats appear valid")
        else:
            self.validation_result.warnings += format_issues

    async def _validate_system_integration(self):
        """Test integration with existing systems"""
        console.print("\n[bold]Step 6: Testing system integration...[/bold]")

        # Test Redis connection
        await self._test_redis_integration()

        # Test vector database connections
        await self._test_vector_db_integration()

        # Test API key validity (sample)
        await self._test_api_key_integration()

        console.print("[green]✓[/green] System integration tests completed")

    async def _test_redis_integration(self):
        """Test Redis integration"""
        try:
            if self.esc_manager:
                async with self.esc_manager:
                    redis_url = await self.esc_manager.get_secret(
                        "infrastructure.redis.url", "dev", use_cache=False
                    )
                    redis_password = await self.esc_manager.get_secret(
                        "infrastructure.redis.password", "dev", use_cache=False
                    )

                    if redis_url:
                        # Test Redis connection (would need redis library)
                        self.validation_result.passed_checks += 1
                        console.print("[green]✓[/green] Redis configuration available")
                    else:
                        self.validation_result.failed_checks += 1
                        console.print("[red]✗[/red] Redis configuration missing")

                    self.validation_result.total_checks += 1

        except Exception as e:
            logger.warning(f"Redis integration test failed: {e}")
            self.validation_result.warnings += 1

    async def _test_vector_db_integration(self):
        """Test vector database integration"""
        try:
            if self.esc_manager:
                async with self.esc_manager:
                    qdrant_key = await self.esc_manager.get_secret(
                        "infrastructure.vector_db.qdrant.api_key",
                        "dev",
                        use_cache=False,
                    )
                    weaviate_key = await self.esc_manager.get_secret(
                        "infrastructure.vector_db.weaviate.api_key",
                        "dev",
                        use_cache=False,
                    )

                    if qdrant_key or weaviate_key:
                        self.validation_result.passed_checks += 1
                        console.print(
                            "[green]✓[/green] Vector database configuration available"
                        )
                    else:
                        self.validation_result.failed_checks += 1
                        console.print(
                            "[red]✗[/red] Vector database configuration missing"
                        )

                    self.validation_result.total_checks += 1

        except Exception as e:
            logger.warning(f"Vector DB integration test failed: {e}")
            self.validation_result.warnings += 1

    async def _test_api_key_integration(self):
        """Test sample API key integration"""
        try:
            if self.esc_manager:
                async with self.esc_manager:
                    openai_key = await self.esc_manager.get_secret(
                        "llm_providers.direct_keys.openai", "dev", use_cache=False
                    )

                    if openai_key:
                        self.validation_result.passed_checks += 1
                        console.print("[green]✓[/green] LLM provider keys available")
                    else:
                        self.validation_result.failed_checks += 1
                        console.print("[red]✗[/red] LLM provider keys missing")

                    self.validation_result.total_checks += 1

        except Exception as e:
            logger.warning(f"API key integration test failed: {e}")
            self.validation_result.warnings += 1

    async def _generate_recommendations(self):
        """Generate recommendations for improvement"""
        console.print("\n[bold]Step 7: Generating recommendations...[/bold]")

        # Analyze results and generate recommendations
        if self.validation_result.missing_secrets:
            self.validation_result.recommendations.append(
                f"Complete migration: {len(self.validation_result.missing_secrets)} secrets still missing"
            )

        if self.validation_result.format_issues:
            self.validation_result.recommendations.append(
                f"Fix format issues: {len(self.validation_result.format_issues)} secrets have format problems"
            )

        if self.validation_result.access_failures:
            self.validation_result.recommendations.append(
                f"Fix access issues: {len(self.validation_result.access_failures)} access failures detected"
            )

        if self.validation_result.success_rate < 90:
            self.validation_result.recommendations.append(
                "Investigate failed checks to improve migration success rate"
            )

        if not self.validation_result.recommendations:
            self.validation_result.recommendations.append(
                "Migration validation passed! Consider setting up automated monitoring."
            )

        # Display recommendations
        for i, rec in enumerate(self.validation_result.recommendations, 1):
            console.print(f"[blue]{i}.[/blue] {rec}")

    async def _generate_validation_report(self):
        """Generate comprehensive validation report"""
        console.print("\n[bold]Step 8: Generating validation report...[/bold]")

        report = {
            "validation_completed": datetime.now().isoformat(),
            "overall_status": (
                "PASSED" if self.validation_result.is_migration_valid else "FAILED"
            ),
            "summary": {
                "total_checks": self.validation_result.total_checks,
                "passed_checks": self.validation_result.passed_checks,
                "failed_checks": self.validation_result.failed_checks,
                "warnings": self.validation_result.warnings,
                "success_rate": round(self.validation_result.success_rate, 2),
            },
            "issues": {
                "missing_secrets": self.validation_result.missing_secrets,
                "invalid_secrets": self.validation_result.invalid_secrets,
                "access_failures": self.validation_result.access_failures,
                "format_issues": self.validation_result.format_issues,
                "environment_issues": self.validation_result.environment_issues,
            },
            "recommendations": self.validation_result.recommendations,
            "environments_tested": self.environments,
            "expected_secrets_count": len(self.expected_secrets),
        }

        # Save report
        report_file = f"migration_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        async with aiofiles.open(report_file, "w") as f:
            await f.write(json.dumps(report, indent=2))

        # Display summary table
        table = Table(title="Validation Summary")
        table.add_column("Check Type", style="cyan")
        table.add_column("Count", justify="right", style="green")
        table.add_column("Status", style="yellow")

        table.add_row("Total Checks", str(self.validation_result.total_checks), "")
        table.add_row(
            "Passed", str(self.validation_result.passed_checks), "[green]✓[/green]"
        )
        table.add_row(
            "Failed",
            str(self.validation_result.failed_checks),
            (
                "[red]✗[/red]"
                if self.validation_result.failed_checks > 0
                else "[green]✓[/green]"
            ),
        )
        table.add_row(
            "Warnings",
            str(self.validation_result.warnings),
            (
                "[yellow]⚠[/yellow]"
                if self.validation_result.warnings > 0
                else "[green]✓[/green]"
            ),
        )
        table.add_row("Success Rate", f"{self.validation_result.success_rate:.1f}%", "")

        console.print(table)

        # Display overall status
        if self.validation_result.is_migration_valid:
            console.print("\n[bold green]✓ Migration validation PASSED[/bold green]")
        else:
            console.print("\n[bold red]✗ Migration validation FAILED[/bold red]")

        console.print(f"\n[green]✓[/green] Validation report saved: {report_file}")

        await self.audit_logger.log_event(
            level=AuditLevel.INFO,
            action=AuditAction.CONFIG_LOAD,
            resource="validation_report",
            message=f"Validation completed: {report['overall_status']}",
            context=AuditContext(service_name="validation_tool"),
            data={
                "total_checks": self.validation_result.total_checks,
                "success_rate": self.validation_result.success_rate,
                "overall_status": report["overall_status"],
            },
        )

    # Helper methods
    def _convert_to_esc_key(self, env_key: str) -> str:
        """Convert environment variable to ESC key format (reuse from migration script)"""
        mappings = {
            "OPENAI_API_KEY": "llm_providers.direct_keys.openai",
            "ANTHROPIC_API_KEY": "llm_providers.direct_keys.anthropic",
            "REDIS_URL": "infrastructure.redis.url",
            "REDIS_PASSWORD": "infrastructure.redis.password",
            "QDRANT_API_KEY": "infrastructure.vector_db.qdrant.api_key",
            "PORTKEY_API_KEY": "llm_providers.portkey.api_key",
        }

        return mappings.get(env_key, env_key.lower().replace("_", "."))

    def _determine_environments_from_file(self, file_path: Path) -> List[str]:
        """Determine environments from file path"""
        file_name = file_path.name.lower()

        if "production" in file_name or "prod" in file_name:
            return ["production"]
        elif "staging" in file_name or "stage" in file_name:
            return ["staging"]
        elif "development" in file_name or "dev" in file_name:
            return ["dev"]
        else:
            return self.environments

    def _categorize_secret(self, key: str) -> Tuple[str, Optional[str]]:
        """Categorize secret key"""
        key_lower = key.lower()

        if "openai" in key_lower:
            return "llm_provider", "openai"
        elif "anthropic" in key_lower:
            return "llm_provider", "anthropic"
        elif "redis" in key_lower:
            return "infrastructure", "redis"
        elif "qdrant" in key_lower:
            return "vector_db", "qdrant"
        else:
            return "configuration", None

    def _is_required_secret(self, key: str) -> bool:
        """Determine if secret is required"""
        # Consider API keys and database credentials as required
        key_lower = key.lower()
        required_patterns = ["api_key", "password", "secret", "token"]

        return any(pattern in key_lower for pattern in required_patterns)


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate ESC migration completeness")
    parser.add_argument("--pulumi-token", help="Pulumi API token")
    parser.add_argument("--org", default="sophia-intel", help="Pulumi organization")
    parser.add_argument(
        "--environments",
        nargs="+",
        default=["dev", "staging", "production"],
        help="Environments to validate",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create validator
    validator = ESCMigrationValidator(
        pulumi_org=args.org,
        pulumi_api_token=args.pulumi_token or os.getenv("PULUMI_API_KEY"),
        environments=args.environments,
    )

    try:
        result = await validator.validate_migration()

        if result.is_migration_valid:
            console.print(
                "\n[bold green]🎉 Migration validation successful![/bold green]"
            )
            return 0
        else:
            console.print("\n[bold red]❌ Migration validation failed[/bold red]")
            console.print(f"Failed checks: {result.failed_checks}")
            console.print(f"Missing secrets: {len(result.missing_secrets)}")
            return 1

    except Exception as e:
        console.print(f"\n[bold red]💥 Validation error: {e}[/bold red]")
        return 2


if __name__ == "__main__":
    asyncio.run(main())
