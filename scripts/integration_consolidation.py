#!/usr/bin/env python3
"""
Integration Consolidation for Sophia-Intel-AI
Eliminates duplicate integrations and creates clean architecture
"""
import os
import json
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime

@dataclass
class IntegrationAudit:
    name: str
    file_path: str
    size_bytes: int
    last_modified: str
    status: str  # 'keep', 'consolidate', 'deprecate'
    reason: str
    dependencies: List[str]

@dataclass
class ConsolidationPlan:
    total_files: int
    files_to_keep: int
    files_to_consolidate: int
    files_to_deprecate: int
    estimated_reduction: float

class IntegrationConsolidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.audits: List[IntegrationAudit] = []
        self.consolidation_plan: Optional[ConsolidationPlan] = None

    def audit_integration_files(self) -> List[IntegrationAudit]:
        """Audit all integration files and categorize them"""
        print("🔍 Auditing integration files...")

        # Find all integration-related files
        integration_patterns = [
            "**/integration*.py",
            "**/integration*.js",
            "**/integration*.ts",
            "**/integration*.tsx",
            "**/*_integration.py",
            "**/*Integration*.py"
        ]

        all_files = []
        for pattern in integration_patterns:
            files = list(self.project_root.glob(pattern))
            # Filter out node_modules, __pycache__, etc.
            files = [f for f in files if self._is_valid_integration_file(f)]
            all_files.extend(files)

        # Remove duplicates
        all_files = list(set(all_files))

        print(f"  Found {len(all_files)} integration files")

        # Categorize each file
        for file_path in all_files:
            audit = self._audit_single_file(file_path)
            self.audits.append(audit)

        # Sort by status for easier review
        self.audits.sort(key=lambda x: (x.status, x.name))

        return self.audits

    def _is_valid_integration_file(self, file_path: Path) -> bool:
        """Check if file is a valid integration file to audit"""
        exclude_patterns = [
            'node_modules',
            '__pycache__',
            '.git',
            'backups',
            '.venv',
            'dist',
            'build'
        ]

        path_str = str(file_path)
        return not any(pattern in path_str for pattern in exclude_patterns)

    def _audit_single_file(self, file_path: Path) -> IntegrationAudit:
        """Audit a single integration file"""
        relative_path = file_path.relative_to(self.project_root)
        file_stats = file_path.stat()

        # Determine status based on file analysis
        status, reason = self._categorize_file(file_path)

        # Find dependencies (simplified)
        dependencies = self._find_dependencies(file_path)

        return IntegrationAudit(
            name=file_path.name,
            file_path=str(relative_path),
            size_bytes=file_stats.st_size,
            last_modified=datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            status=status,
            reason=reason,
            dependencies=dependencies
        )

    def _categorize_file(self, file_path: Path) -> tuple[str, str]:
        """Categorize file as keep, consolidate, or deprecate"""
        content = ""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return 'deprecate', 'Unable to read file'

        path_str = str(file_path).lower()
        content_lower = content.lower()

        # Business integrations to keep
        business_integrations = [
            'asana', 'linear', 'slack', 'gong', 'business_metrics',
            'enhanced_integration_connectors', 'slack_business_intelligence'
        ]

        if any(integration in path_str for integration in business_integrations):
            if 'class' in content_lower and ('async' in content_lower or 'def' in content_lower):
                return 'keep', 'Core business integration with implementation'
            else:
                return 'consolidate', 'Business integration needing updates'

        # Test files
        if 'test' in path_str:
            if any(integration in path_str for integration in business_integrations):
                return 'keep', 'Test for core business integration'
            else:
                return 'deprecate', 'Test for deprecated integration'

        # Demo/example files
        if any(keyword in path_str for keyword in ['demo', 'example', 'sample', 'temp']):
            return 'deprecate', 'Demo/example file'

        # Infrastructure integrations
        infrastructure_keywords = ['mcp', 'portkey', 'openrouter', 'embedding']
        if any(keyword in path_str for keyword in infrastructure_keywords):
            return 'keep', 'Infrastructure integration'

        # API routers
        if 'api/routers' in path_str or 'api/routes' in path_str:
            return 'keep', 'API router - required for endpoints'

        # Small or empty files
        if file_path.stat().st_size < 100:
            return 'deprecate', 'File too small or empty'

        # Default to consolidate for review
        return 'consolidate', 'Requires manual review'

    def _find_dependencies(self, file_path: Path) -> List[str]:
        """Find dependencies in the file (simplified analysis)"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return []

        dependencies = []

        # Python imports
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('from ') and 'import' in line:
                dep = line.split('from ')[1].split(' import')[0].strip()
                if not dep.startswith('.'):  # Ignore relative imports
                    dependencies.append(dep)
            elif line.startswith('import '):
                dep = line.replace('import ', '').split(' as ')[0].split(',')[0].strip()
                dependencies.append(dep)

        return dependencies[:5]  # Limit to first 5 dependencies

    def create_consolidation_plan(self) -> ConsolidationPlan:
        """Create consolidation plan based on audits"""
        total_files = len(self.audits)
        files_to_keep = len([a for a in self.audits if a.status == 'keep'])
        files_to_consolidate = len([a for a in self.audits if a.status == 'consolidate'])
        files_to_deprecate = len([a for a in self.audits if a.status == 'deprecate'])

        estimated_reduction = ((files_to_deprecate + (files_to_consolidate * 0.5)) / total_files) * 100

        self.consolidation_plan = ConsolidationPlan(
            total_files=total_files,
            files_to_keep=files_to_keep,
            files_to_consolidate=files_to_consolidate,
            files_to_deprecate=files_to_deprecate,
            estimated_reduction=estimated_reduction
        )

        return self.consolidation_plan

    def generate_consolidation_report(self) -> str:
        """Generate detailed consolidation report"""
        if not self.consolidation_plan:
            self.create_consolidation_plan()

        report = [
            "# Integration Consolidation Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Executive Summary",
            f"- **Total integration files found**: {self.consolidation_plan.total_files}",
            f"- **Files to keep**: {self.consolidation_plan.files_to_keep}",
            f"- **Files to consolidate**: {self.consolidation_plan.files_to_consolidate}",
            f"- **Files to deprecate**: {self.consolidation_plan.files_to_deprecate}",
            f"- **Estimated reduction**: {self.consolidation_plan.estimated_reduction:.1f}%",
            "",
            "## Detailed Analysis",
            ""
        ]

        # Group by status
        for status in ['keep', 'consolidate', 'deprecate']:
            status_files = [a for a in self.audits if a.status == status]
            if not status_files:
                continue

            report.extend([
                f"### Files to {status.upper()} ({len(status_files)})",
                ""
            ])

            for audit in status_files:
                size_kb = audit.size_bytes / 1024
                report.extend([
                    f"**{audit.name}**",
                    f"- Path: `{audit.file_path}`",
                    f"- Size: {size_kb:.1f} KB",
                    f"- Reason: {audit.reason}",
                    f"- Dependencies: {', '.join(audit.dependencies[:3]) if audit.dependencies else 'None'}",
                    ""
                ])

        # Add recommendations
        report.extend([
            "## Recommendations",
            "",
            "### Core Business Integrations to Keep",
            "- Enhanced Integration Connectors (Asana, Linear, Slack)",
            "- Business Metrics Service",
            "- Gong Pipeline Integration",
            "- Slack Business Intelligence",
            "",
            "### Consolidation Strategy",
            "1. **Create integration registry** - Single source of truth",
            "2. **Standardize interfaces** - Consistent API patterns",
            "3. **Remove duplicates** - Eliminate redundant implementations",
            "4. **Update tests** - Ensure comprehensive coverage",
            "",
            "### Files to Remove",
            "- Demo and example integrations",
            "- Unused test integrations",
            "- Duplicate implementations",
            "- Legacy integration attempts",
            "",
            "## Implementation Plan",
            "",
            "```bash",
            "# 1. Backup current state",
            "cp -r app/integrations app/integrations_backup_$(date +%Y%m%d)",
            "",
            "# 2. Create new structure",
            "mkdir -p app/integrations/{business,infrastructure,monitoring}",
            "",
            "# 3. Move core business integrations",
            "# (See detailed migration commands in report)",
            "",
            "# 4. Create integration registry",
            "# (Automated by consolidation script)",
            "",
            "# 5. Update imports and tests",
            "# (Semi-automated with validation)",
            "```"
        ])

        return '\n'.join(report)

    def execute_consolidation(self, dry_run: bool = True) -> Dict[str, Any]:
        """Execute the consolidation plan"""
        print(f"🔄 {'DRY RUN: ' if dry_run else ''}Executing consolidation plan...")

        actions_taken = []
        errors = []

        # Create new directory structure
        new_structure = [
            'app/integrations/business',
            'app/integrations/infrastructure',
            'app/integrations/monitoring',
            'app/integrations/deprecated'
        ]

        for directory in new_structure:
            dir_path = self.project_root / directory
            if not dry_run:
                dir_path.mkdir(parents=True, exist_ok=True)
            actions_taken.append(f"Created directory: {directory}")

        # Process files based on status
        for audit in self.audits:
            source_path = self.project_root / audit.file_path

            if audit.status == 'keep':
                # Determine target directory
                if any(keyword in audit.file_path.lower() for keyword in ['business', 'asana', 'linear', 'slack', 'gong']):
                    target_dir = 'app/integrations/business'
                else:
                    target_dir = 'app/integrations/infrastructure'

                target_path = self.project_root / target_dir / audit.name

                if not dry_run and source_path != target_path:
                    try:
                        shutil.move(str(source_path), str(target_path))
                        actions_taken.append(f"Moved to {target_dir}: {audit.name}")
                    except Exception as e:
                        errors.append(f"Failed to move {audit.name}: {e}")
                else:
                    actions_taken.append(f"Would move to {target_dir}: {audit.name}")

            elif audit.status == 'deprecate':
                if not dry_run:
                    deprecated_path = self.project_root / 'app/integrations/deprecated' / audit.name
                    try:
                        shutil.move(str(source_path), str(deprecated_path))
                        actions_taken.append(f"Deprecated: {audit.name}")
                    except Exception as e:
                        errors.append(f"Failed to deprecate {audit.name}: {e}")
                else:
                    actions_taken.append(f"Would deprecate: {audit.name}")

        # Create integration registry
        if not dry_run:
            self._create_integration_registry()
            actions_taken.append("Created integration registry")
        else:
            actions_taken.append("Would create integration registry")

        return {
            'dry_run': dry_run,
            'actions_taken': actions_taken,
            'errors': errors,
            'files_processed': len(self.audits)
        }

    def _create_integration_registry(self):
        """Create the integration registry file"""
        registry_content = '''"""
Integration Registry - Single Source of Truth
Manages all business integrations for sophia-intel-ai
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List

class IntegrationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"

class IntegrationType(Enum):
    BUSINESS = "business"
    INFRASTRUCTURE = "infrastructure"
    MONITORING = "monitoring"

@dataclass
class IntegrationConfig:
    name: str
    type: IntegrationType
    status: IntegrationStatus
    endpoint: str
    health_check: str
    description: str
    version: str
    dependencies: List[str]

# Business Integrations Registry
BUSINESS_INTEGRATIONS: Dict[str, IntegrationConfig] = {
    "asana": IntegrationConfig(
        name="Asana Enhanced Connector",
        type=IntegrationType.BUSINESS,
        status=IntegrationStatus.ACTIVE,
        endpoint="/api/integrations/asana",
        health_check="/api/integrations/asana/health",
        description="Project management and stuck account detection",
        version="2.0.0",
        dependencies=["enhanced_integration_connectors"]
    ),
    "linear": IntegrationConfig(
        name="Linear Enhanced Connector",
        type=IntegrationType.BUSINESS,
        status=IntegrationStatus.ACTIVE,
        endpoint="/api/integrations/linear",
        health_check="/api/integrations/linear/health",
        description="Development velocity and issue tracking",
        version="2.0.0",
        dependencies=["enhanced_integration_connectors"]
    ),
    "slack": IntegrationConfig(
        name="Slack Business Intelligence",
        type=IntegrationType.BUSINESS,
        status=IntegrationStatus.ACTIVE,
        endpoint="/api/integrations/slack",
        health_check="/api/integrations/slack/health",
        description="Communication analysis and team health",
        version="2.1.0",
        dependencies=["slack_integration", "business_metrics"]
    ),
    "gong": IntegrationConfig(
        name="Gong Pipeline Integration",
        type=IntegrationType.BUSINESS,
        status=IntegrationStatus.ACTIVE,
        endpoint="/api/integrations/gong",
        health_check="/api/integrations/gong/health",
        description="Sales pipeline and email processing",
        version="1.5.0",
        dependencies=["gong_pipeline", "email_integration"]
    )
}

def get_active_integrations() -> Dict[str, IntegrationConfig]:
    """Get all active business integrations"""
    return {k: v for k, v in BUSINESS_INTEGRATIONS.items()
            if v.status == IntegrationStatus.ACTIVE}

def get_integrations_by_type(integration_type: IntegrationType) -> Dict[str, IntegrationConfig]:
    """Get integrations by type"""
    return {k: v for k, v in BUSINESS_INTEGRATIONS.items()
            if v.type == integration_type}

def validate_integration_health() -> Dict[str, bool]:
    """Validate health of all active integrations"""
    # TODO: Implement actual health checks
    return {name: True for name in get_active_integrations().keys()}
'''

        registry_path = self.project_root / 'app/integrations/registry.py'
        registry_path.write_text(registry_content)

def main():
    """Main execution function"""
    project_root = Path(__file__).parent.parent
    consolidator = IntegrationConsolidator(project_root)

    print("🔍 Integration Consolidation Analysis")
    print("=" * 50)

    # Step 1: Audit files
    audits = consolidator.audit_integration_files()

    # Step 2: Create plan
    plan = consolidator.create_consolidation_plan()

    # Step 3: Generate report
    report = consolidator.generate_consolidation_report()

    # Save report
    report_path = project_root / 'INTEGRATION_CONSOLIDATION_REPORT.md'
    report_path.write_text(report)
    print(f"📄 Report saved: {report_path}")

    # Step 4: Show summary
    print("\n📊 Consolidation Summary:")
    print(f"  Total files: {plan.total_files}")
    print(f"  Keep: {plan.files_to_keep}")
    print(f"  Consolidate: {plan.files_to_consolidate}")
    print(f"  Deprecate: {plan.files_to_deprecate}")
    print(f"  Estimated reduction: {plan.estimated_reduction:.1f}%")

    # Step 5: Execute dry run
    print("\n🧪 Executing dry run...")
    results = consolidator.execute_consolidation(dry_run=True)

    print(f"  Actions planned: {len(results['actions_taken'])}")
    if results['errors']:
        print(f"  Potential errors: {len(results['errors'])}")

    print("\n✅ Analysis complete!")
    print("📋 Next steps:")
    print("  1. Review INTEGRATION_CONSOLIDATION_REPORT.md")
    print("  2. Run with --execute to perform actual consolidation")
    print("  3. Update imports and tests after consolidation")

if __name__ == "__main__":
    main()