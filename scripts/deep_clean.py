#!/usr/bin/env python3
"""
DEEP CLEAN - Final sweep to remove ALL duplicates and conflicts
This is the nuclear option - removes everything that could cause confusion
"""

import json
import shutil
from datetime import datetime
from pathlib import Path


# Use print for this script to avoid dependencies
class Logger:
    def info(self, msg):
        print(msg)


logger = Logger()


class DeepCleaner:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.root = Path(".")
        self.deleted_items = []
        self.findings = []

    def execute(self):
        """Execute deep cleaning"""

        logger.info("🔥 DEEP CLEAN - FINAL SWEEP")
        logger.info("=" * 50)

        if self.dry_run:
            logger.info("⚠️  DRY RUN MODE - No actual deletions")

        # Step 1: Remove backup directories
        self.remove_backup_directories()

        # Step 2: Remove duplicate orchestrators
        self.remove_duplicate_orchestrators()

        # Step 3: Clean up archive files
        self.clean_archive_files()

        # Step 4: Remove conflicting managers
        self.remove_conflicting_managers()

        # Step 5: Clean documentation
        self.clean_documentation()

        # Step 6: Generate report
        self.generate_report()

    def remove_backup_directories(self):
        """Remove all backup and archive directories"""

        logger.info("\n🗑️  Removing backup directories...")

        backup_dirs = ["backup_before_clean_slate", "docs/archive"]

        for dir_path in backup_dirs:
            path = Path(dir_path)
            if path.exists():
                if not self.dry_run:
                    shutil.rmtree(path)
                self.deleted_items.append(str(path))
                logger.info(f"   ❌ Deleted: {path}")

    def remove_duplicate_orchestrators(self):
        """Remove any orchestrators that aren't SuperOrchestrator"""

        logger.info("\n🗑️  Removing duplicate orchestrators...")

        # Files to check for orchestrator classes
        files_to_check = [
            "app/swarms/agno_teams.py",  # Contains AgnoOrchestrator
            "app/orchestration/unified_facade.py",  # Contains UnifiedOrchestratorFacade
        ]

        for file_path in files_to_check:
            path = Path(file_path)
            if path.exists():
                # Check if file contains orchestrator classes
                with open(path) as f:
                    content = f.read()

                if "Orchestrator" in content and "SuperOrchestrator" not in content:
                    self.findings.append(
                        {
                            "file": str(path),
                            "issue": "Contains orchestrator class (not SuperOrchestrator)",
                            "recommendation": "Consider removing or refactoring to use SuperOrchestrator",
                        }
                    )

                    # For aggressive cleaning, we could delete these
                    # if not self.dry_run:
                    #     path.unlink()
                    # self.deleted_items.append(str(path))
                    # logger.info(f"   ❌ Deleted: {path}")

    def clean_archive_files(self):
        """Remove all backup, temp, and archive files"""

        logger.info("\n🗑️  Cleaning archive files...")

        patterns = [
            "*.backup",
            "*.bak",
            "*.old",
            "*.orig",
            "*~",
            "*.tmp",
            "*.archive",
            "*.copy",
        ]

        for pattern in patterns:
            for file_path in self.root.rglob(pattern):
                if ".venv" not in str(file_path) and "node_modules" not in str(
                    file_path
                ):
                    if not self.dry_run:
                        file_path.unlink()
                    self.deleted_items.append(str(file_path))
                    logger.info(f"   ❌ Deleted: {file_path}")

    def remove_conflicting_managers(self):
        """Identify managers that might conflict with SuperOrchestrator"""

        logger.info("\n🔍 Analyzing manager classes...")

        # Managers that are OK (specialized purposes)
        allowed_managers = [
            "EmbeddedMemoryManager",  # Part of SuperOrchestrator
            "EmbeddedStateManager",  # Part of SuperOrchestrator
            "EmbeddedTaskManager",  # Part of SuperOrchestrator
            "AISystemMonitor",  # Part of SuperOrchestrator
            "CircuitBreakerManager",  # Infrastructure
            "WebSocketManager",  # Infrastructure
            "MCPWebSocketManager",  # MCP specific
            "FeatureFlagManager",  # Feature flags
            "PortkeyVirtualKeyManager",  # Portkey integration
            "EvaluationGateManager",  # Evaluation system
            "GracefulDegradationManager",  # Resilience
            "MCPSecurityManager",  # Security
            "KnowledgeGraphManager",  # Knowledge graph
            "IndexingManager",  # Indexing
            "EnhancedSwarmManager",  # Swarm management
        ]

        # Find potentially conflicting managers
        for py_file in self.root.glob("app/**/*.py"):
            if "__pycache__" not in str(py_file):
                try:
                    with open(py_file) as f:
                        content = f.read()

                    import re

                    manager_classes = re.findall(
                        r"^class\s+(\w*Manager)", content, re.MULTILINE
                    )

                    for manager_class in manager_classes:
                        if manager_class not in allowed_managers:
                            self.findings.append(
                                {
                                    "file": str(py_file),
                                    "class": manager_class,
                                    "issue": "Manager class not in allowed list",
                                    "recommendation": f"Consider if {manager_class} should be embedded in SuperOrchestrator",
                                }
                            )

                except Exception:
                    pass

    def clean_documentation(self):
        """Update documentation to reflect new architecture"""

        logger.info("\n📝 Checking documentation...")

        docs_to_update = []

        # Check all markdown files for references to old components
        for md_file in self.root.rglob("*.md"):
            if ".venv" not in str(md_file) and "node_modules" not in str(md_file):
                try:
                    with open(md_file) as f:
                        content = f.read()

                    # Check for references to deleted components
                    old_refs = [
                        "simple_orchestrator",
                        "orchestra_manager",
                        "swarm_orchestrator",
                        "unified_enhanced_orchestrator",
                        "integrated_manager",
                        "hybrid_vector_manager",
                    ]

                    for ref in old_refs:
                        if ref in content.lower():
                            docs_to_update.append(
                                {
                                    "file": str(md_file),
                                    "reference": ref,
                                    "recommendation": "Update to reference SuperOrchestrator",
                                }
                            )

                except Exception:
                    pass

        if docs_to_update:
            self.findings.append(
                {"category": "Documentation", "files_needing_update": docs_to_update}
            )

    def generate_report(self):
        """Generate deep clean report"""

        logger.info("\n📊 DEEP CLEAN REPORT")
        logger.info("=" * 50)

        report = {
            "timestamp": datetime.now().isoformat(),
            "mode": "DRY_RUN" if self.dry_run else "EXECUTED",
            "deleted_items": self.deleted_items,
            "findings": self.findings,
            "statistics": {
                "items_deleted": len(self.deleted_items),
                "issues_found": len(self.findings),
            },
        }

        # Save report
        report_path = "deep_clean_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        logger.info("\n📈 Summary:")
        logger.info(f"   Items deleted: {report['statistics']['items_deleted']}")
        logger.info(f"   Issues found: {report['statistics']['issues_found']}")

        if self.findings:
            logger.info("\n⚠️  Findings requiring attention:")
            for finding in self.findings[:5]:  # Show first 5
                logger.info(f"   - {finding}")

        logger.info(f"\n   Full report saved to: {report_path}")

        return report


class DocumentationUpdater:
    """Update all documentation to reflect new architecture"""

    def __init__(self):
        self.root = Path(".")
        self.updates_made = []

    def update_all_docs(self):
        """Update all documentation"""

        logger.info("\n📚 Updating documentation...")

        # Create main system documentation
        self.create_system_overview()

        # Update README if needed
        self.update_readme()

        # Create API documentation
        self.create_api_docs()

        logger.info(f"\n✅ Documentation updated: {len(self.updates_made)} files")

    def create_system_overview(self):
        """Create comprehensive system overview"""

        content = """# System Architecture Overview

## Core Components

### 1. SuperOrchestrator (`app/core/super_orchestrator.py`)
The central control system for all orchestration needs.

**Features:**
- Embedded memory, state, and task managers
- AI-powered monitoring and optimization
- WebSocket support for real-time UI
- Self-healing capabilities

**Usage:**
```python
from app.core.super_orchestrator import get_orchestrator

orchestrator = get_orchestrator()
await orchestrator.initialize()

response = await orchestrator.process_request({
    "type": "chat",
    "message": "Hello!"
})
```

### 2. AI Logger (`app/core/ai_logger.py`)
Intelligent logging system replacing all print statements.

**Features:**
- Pattern analysis and anomaly detection
- Root cause analysis
- Structured logging with trace IDs
- Real-time alerting

**Usage:**
```python
from app.core.ai_logger import logger

logger.info("Task completed", {"task_id": "123"})
logger.error("Connection failed", exc_info=True)
```

### 3. Agno Embedding Service (`app/embeddings/agno_embedding_service.py`)
Unified embedding service with Portkey integration.

**Features:**
- 6 embedding models via Together AI
- Intelligent model selection
- In-memory caching
- Cost optimization

**Usage:**
```python
from app.embeddings.agno_embedding_service import AgnoEmbeddingService

service = AgnoEmbeddingService()
embeddings = await service.embed(["text to embed"])
```

## Removed Components

The following have been consolidated into SuperOrchestrator:
- ❌ simple_orchestrator.py
- ❌ orchestra_manager.py
- ❌ unified_enhanced_orchestrator.py
- ❌ All standalone manager files
- ❌ 14 Docker files (now 1 unified Dockerfile)

## Architecture Principles

1. **Single Responsibility:** One component for each major function
2. **Embedded Management:** Managers are embedded, not separate
3. **AI Enhancement:** AI monitoring and optimization throughout
4. **Clean Hierarchy:** Clear, simple component relationships
"""

        doc_path = self.root / "SYSTEM_ARCHITECTURE.md"
        with open(doc_path, "w") as f:
            f.write(content)

        self.updates_made.append(str(doc_path))
        logger.info(f"   Created: {doc_path}")

    def update_readme(self):
        """Update README to reflect new architecture"""

        readme_path = self.root / "README.md"
        if readme_path.exists():
            # Would update README here
            # For now, just log that it needs updating
            logger.info("   README.md exists - may need updates")

    def create_api_docs(self):
        """Create API documentation for SuperOrchestrator"""

        content = """# SuperOrchestrator API Documentation

## Endpoints

### Process Request
**POST** `/orchestrator/process`

Process any type of orchestration request.

**Request Body:**
```json
{
  "type": "chat|command|query|agent",
  "message": "string (for chat)",
  "command": "string (for command)",
  "params": {}
}
```

**Response:**
```json
{
  "type": "response_type",
  "result": {},
  "timestamp": "ISO 8601"
}
```

### WebSocket Connection
**WS** `/orchestrator/ws`

Real-time connection for monitoring and updates.

## Request Types

### Chat
```json
{
  "type": "chat",
  "message": "Your message here"
}
```

### Command
```json
{
  "type": "command",
  "command": "deploy|scale|optimize|analyze|heal",
  "params": {}
}
```

### Query
```json
{
  "type": "query",
  "query_type": "metrics|state|tasks|insights"
}
```

### Agent
```json
{
  "type": "agent",
  "action": "create|destroy|status",
  "config": {}
}
```
"""

        api_doc_path = self.root / "docs" / "API_REFERENCE.md"
        api_doc_path.parent.mkdir(exist_ok=True)

        with open(api_doc_path, "w") as f:
            f.write(content)

        self.updates_made.append(str(api_doc_path))
        logger.info(f"   Created: {api_doc_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Deep clean the codebase")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run")
    parser.add_argument(
        "--update-docs", action="store_true", help="Update documentation"
    )
    parser.add_argument(
        "--aggressive", action="store_true", help="Aggressive cleaning (delete more)"
    )

    args = parser.parse_args()

    # Run deep clean
    cleaner = DeepCleaner(dry_run=args.dry_run)
    report = cleaner.execute()

    # Update documentation if requested
    if args.update_docs:
        updater = DocumentationUpdater()
        updater.update_all_docs()

    # Show final status
    if report["statistics"]["issues_found"] > 0:
        logger.info("\n⚠️  Issues found - review deep_clean_report.json")
    else:
        logger.info("\n✅ System is clean!")


if __name__ == "__main__":
    main()
