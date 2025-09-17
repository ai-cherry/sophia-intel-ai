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
