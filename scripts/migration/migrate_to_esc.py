#!/usr/bin/env python3
"""
Migration Script: Environment Files to Pulumi ESC
Migrates existing .env files and scattered API keys to centralized Pulumi ESC management.
"""

import asyncio
import json
import logging
import os
import re

# Add the project root to path for imports
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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
from infrastructure.pulumi.esc.secrets_manager import ESCSecretsManager

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class MigrationConfig:
    """Configuration for the migration process"""

    source_env_files: List[str] = field(default_factory=list)
    target_environments: List[str] = field(default_factory=lambda: ["dev", "staging", "production"])
    backup_directory: str = "backup_configs/migration"
    dry_run: bool = False
    validate_keys: bool = True
    create_backups: bool = True
    pulumi_org: str = "sophia-intel"
    pulumi_api_token: Optional[str] = None


@dataclass
class DiscoveredSecret:
    """A secret discovered during migration"""

    key: str
    value: str
    source_file: str
    category: str  # "llm_provider", "infrastructure", "database", etc.
    provider: Optional[str] = None  # "openai", "redis", etc.
    is_sensitive: bool = True
    environments: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class MigrationResult:
    """Result of migration operation"""

    total_secrets: int = 0
    successful_migrations: int = 0
    failed_migrations: int = 0
    skipped_secrets: int = 0
    validation_errors: int = 0
    backup_created: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    migrated_secrets: List[str] = field(default_factory=list)


class SecretCategorizer:
    """Categorizes secrets based on key patterns"""

    CATEGORY_PATTERNS = {
        "llm_provider": {
            "openai": [r"openai.*api.*key", r"openai.*vk"],
            "anthropic": [r"anthropic.*api.*key", r"anthropic.*vk"],
            "deepseek": [r"deepseek.*api.*key", r"deepseek.*vk"],
            "openrouter": [r"openrouter.*api.*key", r"openrouter.*vk"],
            "perplexity": [r"perplexity.*api.*key", r"perplexity.*vk"],
            "groq": [r"groq.*api.*key", r"groq.*vk"],
            "mistral": [r"mistral.*api.*key", r"mistral.*vk"],
            "xai": [r"xai.*api.*key", r"xai.*vk"],
            "together": [r"together.*api.*key", r"together.*vk"],
            "cohere": [r"cohere.*api.*key", r"cohere.*vk"],
            "gemini": [r"gemini.*api.*key", r"gemini.*vk"],
            "huggingface": [r"huggingface.*api.*key", r"huggingface.*vk", r"hf_.*"],
            "llama": [r"llama.*api.*key"],
            "aimlapi": [r"aimlapi.*api.*key"],
        },
        "vector_db": {
            "qdrant": [r"qdrant.*api.*key", r"qdrant.*url", r"qdrant.*vk"],
            "weaviate": [r"weaviate.*api.*key", r"weaviate.*url"],
            "milvus": [r"milvus.*api.*key", r"milvus.*url", r"milvus.*vk"],
        },
        "infrastructure": {
            "redis": [r"redis.*url", r"redis.*password", r"redis.*api.*key"],
            "mem0": [r"mem0.*api.*key", r"mem0.*url"],
            "neon": [r"neon.*api.*key"],
            "neo4j": [r"neo4j.*api.*key"],
            "n8n": [r"n8n.*api.*key"],
            "portkey": [r"portkey.*api.*key", r"portkey.*base.*url"],
            "pulumi": [r"pulumi.*api.*key"],
            "agno": [r"agno.*api.*key"],
            "continue": [r"continue.*api.*key"],
        },
        "business": {"netsuite": [r"netsuite.*", r"ns_.*"], "gong": [r"gong.*"]},
    }

    @classmethod
    def categorize_secret(cls, key: str) -> Tuple[str, Optional[str]]:
        """Categorize a secret key and return (category, provider)"""
        key_lower = key.lower()

        for category, providers in cls.CATEGORY_PATTERNS.items():
            for provider, patterns in providers.items():
                for pattern in patterns:
                    if re.search(pattern, key_lower):
                        return category, provider

        # Default categorization
        if "api" in key_lower and "key" in key_lower:
            return "api_keys", None
        elif "password" in key_lower or "secret" in key_lower:
            return "credentials", None
        elif "url" in key_lower or "endpoint" in key_lower:
            return "endpoints", None
        else:
            return "configuration", None


class ESCMigrationTool:
    """Main migration tool for moving secrets to Pulumi ESC"""

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.discovered_secrets: List[DiscoveredSecret] = []
        self.categorizer = SecretCategorizer()
        self.migration_result = MigrationResult()

        # Initialize ESC manager if we have API token
        self.esc_manager: Optional[ESCSecretsManager] = None
        if config.pulumi_api_token:
            self.esc_manager = ESCSecretsManager(
                api_token=config.pulumi_api_token, organization=config.pulumi_org
            )

        # Initialize audit logger
        audit_backends = [
            AuditStorageBackend(
                backend_type="file",
                connection_params={"file_path": "logs/migration_audit.log"},
                encryption_enabled=True,
                compression_enabled=True,
            )
        ]
        self.audit_logger = ESCAuditLogger(audit_backends)

    async def run_migration(self) -> MigrationResult:
        """Run the complete migration process"""
        console.print(
            Panel.fit(
                "[bold blue]Sophia Intel AI - ESC Migration Tool[/bold blue]\n"
                "Migrating environment files to Pulumi ESC",
                title="Migration Starting",
            )
        )

        try:
            await self.audit_logger.start()

            # Step 1: Discovery
            await self._discover_secrets()

            # Step 2: Analysis and categorization
            await self._analyze_secrets()

            # Step 3: Create backups
            if self.config.create_backups:
                await self._create_backups()

            # Step 4: Validation (if enabled)
            if self.config.validate_keys:
                await self._validate_secrets()

            # Step 5: Migration
            if not self.config.dry_run:
                await self._migrate_secrets()
            else:
                console.print("[yellow]DRY RUN MODE - No actual migration performed[/yellow]")
                self._simulate_migration()

            # Step 6: Generate report
            await self._generate_migration_report()

            return self.migration_result

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.migration_result.errors.append(f"Migration failed: {e}")
            raise
        finally:
            await self.audit_logger.stop()

    async def _discover_secrets(self):
        """Discover secrets from various sources"""
        console.print("\n[bold]Step 1: Discovering secrets...[/bold]")

        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            discovery_task = progress.add_task("Scanning environment files...", total=None)

            # Auto-discover .env files if not specified
            if not self.config.source_env_files:
                self.config.source_env_files = self._auto_discover_env_files()

            # Process each env file
            for env_file in self.config.source_env_files:
                progress.update(discovery_task, description=f"Processing {env_file}...")
                await self._scan_env_file(env_file)

            # Scan for additional secrets in config files
            await self._scan_config_directories()

            progress.update(
                discovery_task, description=f"Found {len(self.discovered_secrets)} secrets"
            )

        await self.audit_logger.log_event(
            level=AuditLevel.INFO,
            action=AuditAction.CONFIG_LOAD,
            resource="migration_discovery",
            message=f"Discovered {len(self.discovered_secrets)} secrets from {len(self.config.source_env_files)} files",
            context=AuditContext(service_name="migration_tool"),
        )

    def _auto_discover_env_files(self) -> List[str]:
        """Auto-discover .env files in the project"""
        project_root = Path(__file__).parent.parent.parent
        env_files = []

        # Common .env file patterns
        patterns = [".env*", "*.env", "config/**/.env*", "environments/**/*.env*"]

        for pattern in patterns:
            for file_path in project_root.glob(pattern):
                if file_path.is_file() and not file_path.name.endswith(".example"):
                    env_files.append(str(file_path))

        return sorted(set(env_files))

    async def _scan_env_file(self, file_path: str):
        """Scan a single .env file for secrets"""
        try:
            if not Path(file_path).exists():
                self.migration_result.warnings.append(f"File not found: {file_path}")
                return

            async with aiofiles.open(file_path) as f:
                content = await f.read()

            # Parse environment variables
            for line_num, line in enumerate(content.splitlines(), 1):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Parse KEY=VALUE format
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    if value and not value.startswith("$"):  # Skip variable references
                        category, provider = self.categorizer.categorize_secret(key)

                        secret = DiscoveredSecret(
                            key=key,
                            value=value,
                            source_file=file_path,
                            category=category,
                            provider=provider,
                            is_sensitive=self._is_sensitive_key(key),
                        )

                        # Determine target environments
                        secret.environments = self._determine_target_environments(file_path, key)

                        self.discovered_secrets.append(secret)

        except Exception as e:
            error_msg = f"Error scanning {file_path}: {e}"
            logger.error(error_msg)
            self.migration_result.errors.append(error_msg)

    async def _scan_config_directories(self):
        """Scan configuration directories for additional secrets"""
        project_root = Path(__file__).parent.parent.parent
        config_dirs = ["config", "configs", "secrets"]

        for config_dir in config_dirs:
            config_path = project_root / config_dir
            if config_path.exists():
                for config_file in config_path.rglob("*.json"):
                    await self._scan_json_config(config_file)
                for config_file in config_path.rglob("*.yaml"):
                    await self._scan_yaml_config(config_file)

    async def _scan_json_config(self, file_path: Path):
        """Scan JSON configuration file for secrets"""
        try:
            async with aiofiles.open(file_path) as f:
                content = await f.read()

            data = json.loads(content)
            await self._extract_secrets_from_dict(data, str(file_path))

        except Exception as e:
            logger.warning(f"Error scanning JSON config {file_path}: {e}")

    async def _scan_yaml_config(self, file_path: Path):
        """Scan YAML configuration file for secrets"""
        try:
            async with aiofiles.open(file_path) as f:
                content = await f.read()

            data = yaml.safe_load(content)
            if data:
                await self._extract_secrets_from_dict(data, str(file_path))

        except Exception as e:
            logger.warning(f"Error scanning YAML config {file_path}: {e}")

    async def _extract_secrets_from_dict(
        self, data: Dict[str, Any], source_file: str, prefix: str = ""
    ):
        """Extract secrets from nested dictionary"""
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                await self._extract_secrets_from_dict(value, source_file, full_key)
            elif isinstance(value, str) and self._is_sensitive_key(full_key):
                category, provider = self.categorizer.categorize_secret(full_key)

                secret = DiscoveredSecret(
                    key=full_key,
                    value=value,
                    source_file=source_file,
                    category=category,
                    provider=provider,
                    is_sensitive=True,
                )

                self.discovered_secrets.append(secret)

    def _is_sensitive_key(self, key: str) -> bool:
        """Determine if a key contains sensitive information"""
        sensitive_patterns = [
            r".*key.*",
            r".*secret.*",
            r".*password.*",
            r".*token.*",
            r".*auth.*",
            r".*credential.*",
            r".*private.*",
        ]

        key_lower = key.lower()
        return any(re.search(pattern, key_lower) for pattern in sensitive_patterns)

    def _determine_target_environments(self, file_path: str, key: str) -> List[str]:
        """Determine which environments a secret should be migrated to"""
        file_name = Path(file_path).name.lower()

        # Environment-specific files
        if "production" in file_name or "prod" in file_name:
            return ["production"]
        elif "staging" in file_name or "stage" in file_name:
            return ["staging"]
        elif "development" in file_name or "dev" in file_name:
            return ["dev"]
        elif "test" in file_name:
            return ["dev"]  # Test keys go to dev environment
        else:
            # Default to all environments for generic files
            return self.config.target_environments.copy()

    async def _analyze_secrets(self):
        """Analyze discovered secrets and provide insights"""
        console.print("\n[bold]Step 2: Analyzing secrets...[/bold]")

        # Create analysis table
        table = Table(title="Secret Discovery Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right", style="green")
        table.add_column("Providers", style="yellow")

        # Group by category
        category_stats = {}
        for secret in self.discovered_secrets:
            if secret.category not in category_stats:
                category_stats[secret.category] = {"count": 0, "providers": set()}

            category_stats[secret.category]["count"] += 1
            if secret.provider:
                category_stats[secret.category]["providers"].add(secret.provider)

        # Populate table
        for category, stats in sorted(category_stats.items()):
            providers = ", ".join(sorted(stats["providers"])) if stats["providers"] else "N/A"
            table.add_row(category, str(stats["count"]), providers)

        console.print(table)

        # Analysis insights
        total_secrets = len(self.discovered_secrets)
        sensitive_secrets = len([s for s in self.discovered_secrets if s.is_sensitive])

        console.print("\n[bold]Analysis Results:[/bold]")
        console.print(f"• Total secrets found: {total_secrets}")
        console.print(f"• Sensitive secrets: {sensitive_secrets}")
        console.print(f"• Categories: {len(category_stats)}")
        console.print(f"• Source files: {len(set(s.source_file for s in self.discovered_secrets))}")

        self.migration_result.total_secrets = total_secrets

    async def _create_backups(self):
        """Create backups of current configuration"""
        console.print("\n[bold]Step 3: Creating backups...[/bold]")

        backup_dir = Path(self.config.backup_directory)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"migration_backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        try:
            # Backup source files
            for env_file in self.config.source_env_files:
                if Path(env_file).exists():
                    source_path = Path(env_file)
                    backup_file = backup_path / source_path.name

                    async with aiofiles.open(source_path) as src:
                        content = await src.read()

                    async with aiofiles.open(backup_file, "w") as dst:
                        await dst.write(content)

            # Create migration manifest
            manifest = {
                "backup_created": datetime.now().isoformat(),
                "source_files": self.config.source_env_files,
                "discovered_secrets": len(self.discovered_secrets),
                "target_environments": self.config.target_environments,
                "secrets_by_category": {},
            }

            # Group secrets for manifest
            for secret in self.discovered_secrets:
                if secret.category not in manifest["secrets_by_category"]:
                    manifest["secrets_by_category"][secret.category] = []

                manifest["secrets_by_category"][secret.category].append(
                    {
                        "key": secret.key,
                        "source_file": secret.source_file,
                        "provider": secret.provider,
                        "environments": secret.environments,
                        "is_sensitive": secret.is_sensitive,
                    }
                )

            manifest_file = backup_path / "migration_manifest.json"
            async with aiofiles.open(manifest_file, "w") as f:
                await f.write(json.dumps(manifest, indent=2))

            self.migration_result.backup_created = True
            console.print(f"[green]✓[/green] Backup created: {backup_path}")

            await self.audit_logger.log_event(
                level=AuditLevel.INFO,
                action=AuditAction.BACKUP_CREATE,
                resource="migration_backup",
                message=f"Created migration backup at {backup_path}",
                context=AuditContext(service_name="migration_tool"),
                data={
                    "backup_path": str(backup_path),
                    "files_backed_up": len(self.config.source_env_files),
                },
            )

        except Exception as e:
            error_msg = f"Failed to create backup: {e}"
            self.migration_result.errors.append(error_msg)
            console.print(f"[red]✗[/red] {error_msg}")

    async def _validate_secrets(self):
        """Validate discovered secrets"""
        console.print("\n[bold]Step 4: Validating secrets...[/bold]")

        validation_errors = 0

        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            validation_task = progress.add_task(
                "Validating secrets...", total=len(self.discovered_secrets)
            )

            for secret in self.discovered_secrets:
                # Basic validation
                if not secret.value:
                    secret.notes.append("Empty value")
                    validation_errors += 1

                if len(secret.value) < 8 and secret.is_sensitive:
                    secret.notes.append("Suspiciously short for a secret")
                    validation_errors += 1

                # Provider-specific validation
                if secret.provider == "openai" and not secret.value.startswith("sk-"):
                    secret.notes.append("OpenAI key format invalid")
                    validation_errors += 1

                if secret.provider == "anthropic" and not secret.value.startswith("sk-ant-"):
                    secret.notes.append("Anthropic key format invalid")
                    validation_errors += 1

                progress.advance(validation_task)

        self.migration_result.validation_errors = validation_errors

        if validation_errors > 0:
            console.print(f"[yellow]⚠[/yellow] Found {validation_errors} validation issues")
        else:
            console.print("[green]✓[/green] All secrets passed validation")

    def _simulate_migration(self):
        """Simulate migration for dry run mode"""
        console.print("\n[bold]Step 5: Simulating migration (DRY RUN)...[/bold]")

        for environment in self.config.target_environments:
            console.print(f"\n[blue]Environment: {environment}[/blue]")

            env_secrets = [s for s in self.discovered_secrets if environment in s.environments]

            table = Table(title=f"Secrets for {environment}")
            table.add_column("Key", style="cyan")
            table.add_column("Category", style="green")
            table.add_column("Provider", style="yellow")
            table.add_column("Source", style="dim")

            for secret in env_secrets:
                table.add_row(
                    secret.key,
                    secret.category,
                    secret.provider or "N/A",
                    Path(secret.source_file).name,
                )

            console.print(table)

        self.migration_result.successful_migrations = len(self.discovered_secrets)

    async def _migrate_secrets(self):
        """Perform actual migration to Pulumi ESC"""
        if not self.esc_manager:
            raise ValueError("ESC manager not initialized - missing Pulumi API token")

        console.print("\n[bold]Step 5: Migrating secrets to Pulumi ESC...[/bold]")

        async with self.esc_manager:
            for environment in self.config.target_environments:
                console.print(f"\n[blue]Migrating to environment: {environment}[/blue]")

                env_secrets = [s for s in self.discovered_secrets if environment in s.environments]

                with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
                    migration_task = progress.add_task(
                        f"Migrating to {environment}...", total=len(env_secrets)
                    )

                    for secret in env_secrets:
                        try:
                            # Convert key to nested format for ESC
                            esc_key = self._convert_to_esc_key(secret)

                            # Migrate secret
                            success = await self.esc_manager.set_secret(
                                esc_key, secret.value, environment
                            )

                            if success:
                                self.migration_result.successful_migrations += 1
                                self.migration_result.migrated_secrets.append(
                                    f"{environment}.{esc_key}"
                                )

                                await self.audit_logger.log_event(
                                    level=AuditLevel.SECURITY,
                                    action=AuditAction.SECRET_CREATE,
                                    resource=f"{environment}.{esc_key}",
                                    message=f"Migrated secret from {secret.source_file}",
                                    context=AuditContext(service_name="migration_tool"),
                                    success=True,
                                )
                            else:
                                self.migration_result.failed_migrations += 1
                                error_msg = f"Failed to migrate {secret.key} to {environment}"
                                self.migration_result.errors.append(error_msg)

                                await self.audit_logger.log_event(
                                    level=AuditLevel.ERROR,
                                    action=AuditAction.SECRET_CREATE,
                                    resource=f"{environment}.{esc_key}",
                                    message=f"Failed to migrate secret from {secret.source_file}",
                                    context=AuditContext(service_name="migration_tool"),
                                    success=False,
                                    error_details=error_msg,
                                )

                        except Exception as e:
                            self.migration_result.failed_migrations += 1
                            error_msg = f"Error migrating {secret.key}: {e}"
                            self.migration_result.errors.append(error_msg)
                            logger.error(error_msg)

                        progress.advance(migration_task)

    def _convert_to_esc_key(self, secret: DiscoveredSecret) -> str:
        """Convert environment variable key to ESC nested key format"""

        # Define mapping patterns
        mappings = {
            # LLM Provider keys
            "OPENAI_API_KEY": "llm_providers.direct_keys.openai",
            "ANTHROPIC_API_KEY": "llm_providers.direct_keys.anthropic",
            "DEEPSEEK_API_KEY": "llm_providers.direct_keys.deepseek",
            "OPENROUTER_API_KEY": "llm_providers.direct_keys.openrouter",
            "PERPLEXITY_API_KEY": "llm_providers.direct_keys.perplexity",
            "GROQ_API_KEY": "llm_providers.direct_keys.groq",
            "MISTRAL_API_KEY": "llm_providers.direct_keys.mistral",
            "XAI_API_KEY": "llm_providers.direct_keys.xai",
            "TOGETHER_AI_API_KEY": "llm_providers.direct_keys.together_ai",
            "HUGGINGFACE_API_KEY": "llm_providers.direct_keys.huggingface",
            "GEMINI_API_KEY": "llm_providers.direct_keys.gemini",
            "LLAMA_API_KEY": "llm_providers.direct_keys.llama",
            "AIMLAPI_API_KEY": "llm_providers.direct_keys.aimlapi",
            # Portkey virtual keys
            "OPENAI_VK": "llm_providers.portkey.virtual_keys.openai",
            "ANTHROPIC_VK": "llm_providers.portkey.virtual_keys.anthropic",
            "DEEPSEEK_VK": "llm_providers.portkey.virtual_keys.deepseek",
            "PORTKEY_API_KEY": "llm_providers.portkey.api_key",
            # Infrastructure
            "REDIS_URL": "infrastructure.redis.url",
            "REDIS_PASSWORD": "infrastructure.redis.password",
            "QDRANT_API_KEY": "infrastructure.vector_db.qdrant.api_key",
            "QDRANT_URL": "infrastructure.vector_db.qdrant.url",
            "WEAVIATE_API_KEY": "infrastructure.vector_db.weaviate.api_key",
            "WEAVIATE_URL": "infrastructure.vector_db.weaviate.url",
            # Infrastructure providers
            "MEM0_API_KEY": "infrastructure_providers.mem0.api_key",
            "NEON_API_KEY": "infrastructure_providers.neon.api_key",
            "NEO4J_API_KEY": "infrastructure_providers.neo4j.api_key",
            "N8N_API_KEY": "infrastructure_providers.n8n.api_key",
            "PULUMI_API_KEY": "pulumi.api_key",
            "AGNO_API_KEY": "infrastructure_providers.agno.api_key",
            "CONTINUE_API_KEY": "infrastructure_providers.continue.api_key",
        }

        # Check for direct mapping
        if secret.key in mappings:
            return mappings[secret.key]

        # Generic conversion based on category and provider
        if secret.category and secret.provider:
            return f"{secret.category}.{secret.provider}.{secret.key.lower().replace('_', '.')}"
        elif secret.category:
            return f"{secret.category}.{secret.key.lower().replace('_', '.')}"
        else:
            # Fallback: convert underscore to dots and lowercase
            return secret.key.lower().replace("_", ".")

    async def _generate_migration_report(self):
        """Generate comprehensive migration report"""
        console.print("\n[bold]Step 6: Generating migration report...[/bold]")

        report = {
            "migration_completed": datetime.now().isoformat(),
            "configuration": {
                "dry_run": self.config.dry_run,
                "source_files": self.config.source_env_files,
                "target_environments": self.config.target_environments,
                "validation_enabled": self.config.validate_keys,
                "backup_created": self.migration_result.backup_created,
            },
            "results": {
                "total_secrets": self.migration_result.total_secrets,
                "successful_migrations": self.migration_result.successful_migrations,
                "failed_migrations": self.migration_result.failed_migrations,
                "validation_errors": self.migration_result.validation_errors,
                "success_rate": (
                    self.migration_result.successful_migrations
                    / self.migration_result.total_secrets
                    * 100
                    if self.migration_result.total_secrets > 0
                    else 0
                ),
            },
            "migrated_secrets": self.migration_result.migrated_secrets,
            "errors": self.migration_result.errors,
            "warnings": self.migration_result.warnings,
        }

        # Save report
        report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        async with aiofiles.open(report_file, "w") as f:
            await f.write(json.dumps(report, indent=2))

        # Display summary
        table = Table(title="Migration Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")

        table.add_row("Total Secrets", str(self.migration_result.total_secrets))
        table.add_row("Successful", str(self.migration_result.successful_migrations))
        table.add_row("Failed", str(self.migration_result.failed_migrations))
        table.add_row("Validation Errors", str(self.migration_result.validation_errors))
        table.add_row("Success Rate", f"{report['results']['success_rate']:.1f}%")

        console.print(table)
        console.print(f"\n[green]✓[/green] Migration report saved: {report_file}")

        if self.migration_result.errors:
            console.print(f"\n[red]Errors encountered ({len(self.migration_result.errors)}):[/red]")
            for error in self.migration_result.errors[:5]:  # Show first 5 errors
                console.print(f"  • {error}")
            if len(self.migration_result.errors) > 5:
                console.print(f"  ... and {len(self.migration_result.errors) - 5} more")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate environment files to Pulumi ESC")
    parser.add_argument(
        "--dry-run", action="store_true", help="Perform dry run without actual migration"
    )
    parser.add_argument("--no-validation", action="store_true", help="Skip secret validation")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--pulumi-token", help="Pulumi API token")
    parser.add_argument("--org", default="sophia-intel", help="Pulumi organization")
    parser.add_argument("--env-files", nargs="+", help="Specific .env files to migrate")
    parser.add_argument(
        "--environments",
        nargs="+",
        default=["dev", "staging", "production"],
        help="Target ESC environments",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create migration configuration
    config = MigrationConfig(
        source_env_files=args.env_files or [],
        target_environments=args.environments,
        dry_run=args.dry_run,
        validate_keys=not args.no_validation,
        create_backups=not args.no_backup,
        pulumi_org=args.org,
        pulumi_api_token=args.pulumi_token or os.getenv("PULUMI_API_KEY"),
    )

    # Run migration
    migration_tool = ESCMigrationTool(config)

    try:
        result = await migration_tool.run_migration()

        if result.successful_migrations > 0:
            console.print("\n[bold green]✓ Migration completed successfully![/bold green]")
            console.print(f"Migrated {result.successful_migrations} secrets to Pulumi ESC")
        else:
            console.print("\n[bold red]✗ Migration completed with issues[/bold red]")

        return 0 if result.failed_migrations == 0 else 1

    except Exception as e:
        console.print(f"\n[bold red]✗ Migration failed: {e}[/bold red]")
        return 1


if __name__ == "__main__":
    asyncio.run(main())
