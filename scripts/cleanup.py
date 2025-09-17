#!/usr/bin/env python3
"""
Repository cleanup script - Archives duplicates and legacy code
Runs during setup to clean repository structure
"""
import logging
import shutil
from datetime import datetime
from pathlib import Path
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def cleanup_repository():
    """Archive duplicate files and clean repository structure"""
    logger.info("🧹 Starting repository cleanup...")
    # Create archive directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = Path(f"archive/{timestamp}")
    archive_dir.mkdir(parents=True, exist_ok=True)
    # Files and patterns to remove (tech debt)
    cleanup_targets = [
        # Vercel artifacts
        "vercel.json",
        "api/vercel_gateway.py",
        "api/proxy.js",
        ".vercelignore",
        "deploy_vercel.sh",
        # Duplicate main files
        "backend/main_old.py",
        "backend/main_backup.py",
        "backend/main_simple.py",
        "backend/main_with_chat.py",
        "backend/minimal_main.py",
        # Duplicate services
        "services/duplicate_*",
        # Old test files
        "tests/old_*",
        "backend/tests/*",
        # Environment backups
        ".env.backup",
        ".env.old",
        ".env.template",
        # Cache and build artifacts
        "**/__pycache__",
        "**/*.pyc",
        "**/.pytest_cache",
        "**/node_modules",
        # Duplicate requirements
        "requirements-*.txt",
        "backend/requirements.txt",
        # Legacy Docker files
        "Dockerfile.old",
        "docker-compose.old.yml",
        "docker-compose.dev.yml",
        # Duplicate configs
        "backend/pyproject.toml",
        "backend/uv.lock",
        # DevContainer duplicates
        ".devcontainer/devcontainer-fixed.json",
        ".devcontainer/codespaces-setup.sh",
        # Migration artifacts
        "archive/migration_reports/*",
        "MIGRATION_*.md",
        "PRAGMATIC_*.md",
        "COMPREHENSIVE_*.md",
        "DEPLOYMENT_*.md",
        "SECURITY_*.md",
        "POST_MIGRATION_*.md",
        "DETAILED_*.md",
        "UPDATED_*.md",
        # Monitoring configs (not needed for basic setup)
        "monitoring/*",
        "k8s/*",
        # Security scripts (consolidated)
        "scripts/security/*",
        "security_quick_fix.sh",
        "scripts/migrate_secrets_to_pulumi.sh",
        "scripts/load_secrets.sh",
        # Codespaces artifacts
        "requirements-codespaces.txt",
        "codespaces_preflight_check.sh",
        "scripts/migration-validation.sh",
        # Infrastructure duplicates
        "infrastructure/pulumi/index-kubernetes.ts",
        # Frontend artifacts (not needed for backend-focused setup)
        "frontend/nginx.conf",
        "frontend/Dockerfile",
    ]
    removed_count = 0
    # Process each cleanup target
    for pattern in cleanup_targets:
        for path in Path(".").glob(pattern):
            if path.exists() and not str(path).startswith("archive"):
                try:
                    dest = archive_dir / path.relative_to(".")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if path.is_dir():
                        shutil.move(str(path), str(dest))
                    else:
                        shutil.move(str(path), str(dest))
                    logger.info(f"  ✓ Archived: {path}")
                    removed_count += 1
                except Exception as e:
                    logger.error(f"  ✗ Failed to archive {path}: {e}")
    # Create required directories if missing
    required_dirs = [
        "backend/core",
        "backend/routers",
        "backend/models",
        "scripts",
        "tests",
        "docs",
    ]
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        init_file = Path(dir_path) / "__init__.py"
        if (
            not init_file.exists()
            and "scripts" not in dir_path
            and "docs" not in dir_path
        ):
            init_file.write_text(f'"""Module: {dir_path}"""')
    # Create .env if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://sophia:localdev@localhost:5432/sophia
REDIS_URL=${REDIS_URL}
JWT_SECRET_KEY=dev-secret-change-in-production
DEBUG=true
SENTRY_DSN=
"""
        env_file.write_text(env_content)
        logger.info("Created .env file")
    logger.info(f"✅ Cleanup complete! Archived {removed_count} items")
    logger.info(f"Archive location: {archive_dir}")
if __name__ == "__main__":
    cleanup_repository()
