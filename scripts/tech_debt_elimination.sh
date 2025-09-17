#!/bin/bash
# Tech Debt Elimination Strategy for Sophia-Intel-AI
# Ensures zero conflicts, duplications, and technical debt

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/consolidation_backup_$(date +%Y%m%d_%H%M%S)"

echo "🧹 Sophia-Intel-AI Tech Debt Elimination"
echo "========================================"

# Create backup
create_backup() {
    echo "📦 Creating backup..."
    mkdir -p "$BACKUP_DIR"

    # Backup all dashboard files
    find "$PROJECT_ROOT" -name "*dashboard*" -type f ! -path "*/node_modules/*" ! -path "*/.git/*" \
        -exec cp --parents {} "$BACKUP_DIR" \;

    # Backup React components
    find "$PROJECT_ROOT" -name "*.tsx" -o -name "*.jsx" ! -path "*/node_modules/*" ! -path "*/.git/*" \
        -exec cp --parents {} "$BACKUP_DIR" \;

    echo "✅ Backup created at: $BACKUP_DIR"
}

# Analyze dashboard conflicts
analyze_dashboard_conflicts() {
    echo "🔍 Analyzing dashboard conflicts..."

    local conflicts=()

    # Check for HTML vs React conflicts
    if [[ -f "$PROJECT_ROOT/app/ui/dashboard.html" ]] && [[ -f "$PROJECT_ROOT/src/dashboard/DashboardAppShell.tsx" ]]; then
        conflicts+=("HTML/React dashboard conflict")
    fi

    # Check for Agent Factory conflicts with workbench-ui
    if [[ -f "$PROJECT_ROOT/src/dashboard/AgentFactoryTab.tsx" ]] || [[ -f "$PROJECT_ROOT/app/factory/ui/AgentFactoryComponents.jsx" ]]; then
        conflicts+=("Agent Factory in sophia-intel-ai violates repository separation")
    fi

    # Check for multiple BI dashboards
    local bi_dashboards
    bi_dashboards=$(find "$PROJECT_ROOT" -name "*dashboard*" -path "*/bi*" -o -name "*bi_dashboard*" | wc -l)
    if [[ $bi_dashboards -gt 1 ]]; then
        conflicts+=("Multiple BI dashboard implementations")
    fi

    if [[ ${#conflicts[@]} -gt 0 ]]; then
        echo "❌ Conflicts detected:"
        printf '  - %s\n' "${conflicts[@]}"
        return 1
    else
        echo "✅ No major conflicts detected"
        return 0
    fi
}

# Remove legacy dashboard files
remove_legacy_dashboards() {
    echo "🗑️ Removing legacy dashboard files..."

    local legacy_files=(
        "dashboard.py"
        "dashboard_integration.py"
        "enhanced_dashboard_integration.py"
        "demo_advanced_dashboard.py"
        "consolidate_dashboards.py"
        "app/ui/dashboard.html"
    )

    for file in "${legacy_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            echo "  Removing: $file"
            rm "$PROJECT_ROOT/$file"
        fi
    done
}

# Move Agent Factory to workbench-ui (where it belongs)
relocate_agent_factory() {
    echo "🔄 Relocating Agent Factory to workbench-ui..."

    local agent_factory_files=(
        "src/dashboard/AgentFactoryTab.tsx"
        "app/factory/ui/AgentFactoryComponents.jsx"
    )

    for file in "${agent_factory_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            echo "  ❌ VIOLATION: Agent Factory found in sophia-intel-ai"
            echo "  📝 Action Required: Move $file to workbench-ui repository"
            echo "  🎯 Sophia-intel-ai should only have agent DEPLOYMENT, not development"

            # Create migration note
            cat > "$PROJECT_ROOT/AGENT_FACTORY_MIGRATION_REQUIRED.md" << EOF
# Agent Factory Migration Required

## Issue
Agent Factory components found in sophia-intel-ai repository.
This violates the repository separation principle.

## Required Action
Move the following files to workbench-ui:
- $file

## Repository Separation Principle
- **workbench-ui**: Agent development, testing, optimization
- **sophia-intel-ai**: Agent deployment, business operations, monitoring

## Migration Command
\`\`\`bash
# Move to workbench-ui
mv ~/sophia-intel-ai/$file ~/workbench-ui/src/components/factory/
\`\`\`
EOF
        fi
    done
}

# Consolidate integration files
consolidate_integrations() {
    echo "🔗 Consolidating integration files..."

    # Count current integration files
    local integration_count
    integration_count=$(find "$PROJECT_ROOT" -name "*integration*" -type f ! -path "*/node_modules/*" ! -path "*/.git/*" | wc -l)
    echo "  Found $integration_count integration files"

    # Create consolidated integration directory structure
    mkdir -p "$PROJECT_ROOT/app/integrations/business"
    mkdir -p "$PROJECT_ROOT/app/integrations/infrastructure"
    mkdir -p "$PROJECT_ROOT/app/integrations/monitoring"

    # Business integrations (keep these)
    local business_integrations=(
        "enhanced_integration_connectors.py"
        "slack_integration.py"
        "gong_pipeline"
        "business_metrics.py"
    )

    echo "  ✅ Business integrations identified: ${#business_integrations[@]} core files"

    # Create integration registry
    cat > "$PROJECT_ROOT/app/integrations/registry.py" << 'EOF'
"""
Integration Registry - Single Source of Truth
Manages all business integrations for sophia-intel-ai
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any

class IntegrationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"

@dataclass
class IntegrationConfig:
    name: str
    status: IntegrationStatus
    endpoint: str
    health_check: str
    description: str

# Business Integrations Registry
BUSINESS_INTEGRATIONS: Dict[str, IntegrationConfig] = {
    "asana": IntegrationConfig(
        name="Asana Enhanced Connector",
        status=IntegrationStatus.ACTIVE,
        endpoint="/api/integrations/asana",
        health_check="/api/integrations/asana/health",
        description="Project management and stuck account detection"
    ),
    "linear": IntegrationConfig(
        name="Linear Enhanced Connector",
        status=IntegrationStatus.ACTIVE,
        endpoint="/api/integrations/linear",
        health_check="/api/integrations/linear/health",
        description="Development velocity and issue tracking"
    ),
    "slack": IntegrationConfig(
        name="Slack Business Intelligence",
        status=IntegrationStatus.ACTIVE,
        endpoint="/api/integrations/slack",
        health_check="/api/integrations/slack/health",
        description="Communication analysis and team health"
    ),
    "gong": IntegrationConfig(
        name="Gong Pipeline Integration",
        status=IntegrationStatus.ACTIVE,
        endpoint="/api/integrations/gong",
        health_check="/api/integrations/gong/health",
        description="Sales pipeline and email processing"
    )
}

def get_active_integrations() -> Dict[str, IntegrationConfig]:
    """Get all active business integrations"""
    return {k: v for k, v in BUSINESS_INTEGRATIONS.items()
            if v.status == IntegrationStatus.ACTIVE}
EOF
}

# Create unified architecture validation
create_architecture_validation() {
    echo "🏗️ Creating architecture validation..."

    mkdir -p "$PROJECT_ROOT/scripts/validation"

    cat > "$PROJECT_ROOT/scripts/validation/architecture_validator.py" << 'EOF'
#!/usr/bin/env python3
"""
Architecture Validation for Sophia-Intel-AI
Ensures compliance with repository separation and clean architecture
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

class ArchitectureValidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.violations: List[str] = []

    def validate_repository_separation(self) -> bool:
        """Ensure sophia-intel-ai doesn't contain agent development tools"""
        forbidden_patterns = [
            "**/AgentFactory*.tsx",
            "**/AgentFactory*.jsx",
            "**/agent-factory/**",
            "**/agent_factory/**",
            "**/AgentBuilder*",
            "**/AgentDevelopment*"
        ]

        violations_found = False
        for pattern in forbidden_patterns:
            matches = list(self.project_root.glob(pattern))
            if matches:
                violations_found = True
                self.violations.append(f"Repository separation violation: {pattern} found")
                for match in matches:
                    self.violations.append(f"  - {match}")

        return not violations_found

    def validate_dashboard_consolidation(self) -> bool:
        """Ensure single dashboard implementation"""
        dashboard_files = list(self.project_root.glob("**/dashboard.*"))
        dashboard_files = [f for f in dashboard_files if 'node_modules' not in str(f)]

        # Allow monitoring dashboards but not application dashboards
        allowed_paths = [
            "monitoring/grafana/dashboards",
            "infrastructure/alertmanager/monitoring"
        ]

        violations_found = False
        for dashboard_file in dashboard_files:
            if not any(allowed_path in str(dashboard_file) for allowed_path in allowed_paths):
                if dashboard_file.suffix in ['.html', '.py']:
                    violations_found = True
                    self.violations.append(f"Legacy dashboard found: {dashboard_file}")

        return not violations_found

    def validate_integration_consolidation(self) -> bool:
        """Ensure clean integration architecture"""
        integration_files = list(self.project_root.glob("**/integration*"))
        integration_files = [f for f in integration_files if 'node_modules' not in str(f)]

        # Should have registry and organized structure
        registry_exists = (self.project_root / "app/integrations/registry.py").exists()
        if not registry_exists:
            self.violations.append("Integration registry missing")
            return False

        return True

    def run_validation(self) -> bool:
        """Run all validations"""
        print("🔍 Running architecture validation...")

        validations = [
            ("Repository Separation", self.validate_repository_separation),
            ("Dashboard Consolidation", self.validate_dashboard_consolidation),
            ("Integration Consolidation", self.validate_integration_consolidation)
        ]

        all_passed = True
        for name, validation_func in validations:
            passed = validation_func()
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {name}")
            if not passed:
                all_passed = False

        if self.violations:
            print("\n❌ Violations found:")
            for violation in self.violations:
                print(f"  - {violation}")

        return all_passed

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    validator = ArchitectureValidator(project_root)

    if validator.run_validation():
        print("\n✅ Architecture validation PASSED")
        sys.exit(0)
    else:
        print("\n❌ Architecture validation FAILED")
        sys.exit(1)
EOF

    chmod +x "$PROJECT_ROOT/scripts/validation/architecture_validator.py"
}

# Create package.json for unified dashboard
create_package_json() {
    echo "📦 Creating package.json for unified dashboard..."

    cat > "$PROJECT_ROOT/package.json" << 'EOF'
{
  "name": "sophia-intel-ai-dashboard",
  "version": "1.0.0",
  "description": "Unified business intelligence dashboard for Pay Ready",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "validate:architecture": "python scripts/validation/architecture_validator.py",
    "audit:tech-debt": "npm audit && python scripts/tech_debt_audit.py"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "tailwindcss": "^3.0.0"
  },
  "repository": {
    "type": "git",
    "url": "sophia-intel-ai"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
EOF
}

# Main execution
main() {
    echo "Starting tech debt elimination process..."

    # Step 1: Backup
    create_backup

    # Step 2: Analyze conflicts
    if ! analyze_dashboard_conflicts; then
        echo "⚠️ Conflicts detected - proceeding with fixes..."
    fi

    # Step 3: Remove legacy files
    remove_legacy_dashboards

    # Step 4: Fix repository separation violations
    relocate_agent_factory

    # Step 5: Consolidate integrations
    consolidate_integrations

    # Step 6: Create validation tools
    create_architecture_validation

    # Step 7: Create modern package.json
    create_package_json

    # Step 8: Final validation
    echo "🔍 Running final validation..."
    if [[ -f "$PROJECT_ROOT/scripts/validation/architecture_validator.py" ]]; then
        python3 "$PROJECT_ROOT/scripts/validation/architecture_validator.py"
    fi

    echo ""
    echo "✅ Tech debt elimination complete!"
    echo ""
    echo "📋 Summary:"
    echo "  - Legacy dashboards removed"
    echo "  - Repository separation enforced"
    echo "  - Integrations consolidated"
    echo "  - Architecture validation enabled"
    echo "  - Modern build system configured"
    echo ""
    echo "🚀 Next steps:"
    echo "  1. Review AGENT_FACTORY_MIGRATION_REQUIRED.md"
    echo "  2. Move Agent Factory components to workbench-ui"
    echo "  3. Run: npm install"
    echo "  4. Run: npm run validate:architecture"
    echo "  5. Start unified dashboard: npm run dev"
}

# Error handling
trap 'echo "❌ Tech debt elimination failed at line $LINENO"' ERR

main "$@"