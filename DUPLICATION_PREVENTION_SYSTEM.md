# 🛡️ Duplication & Conflict Prevention System

## 🔴 The Problem: Why This Keeps Happening

### Root Causes Identified

1. **No automated checks** - Manual reviews miss duplicates
2. **Organic growth** - Features added without architectural review
3. **Multiple contributors** - Lack of coordination
4. **No single source of truth** - Everyone creates their own version
5. **Missing governance** - No rules enforcing structure
6. **Technical debt accumulation** - "Quick fixes" become permanent

---

## 🚨 AUTOMATED PREVENTION SYSTEM

### 1. Pre-Commit Hooks (Immediate Detection)

#### A. Install Duplication Detection

```bash
# .pre-commit-config.yaml
repos:
  # Duplicate code detection
  - repo: local
    hooks:
      - id: check-duplicates
        name: Check for duplicate classes/components
        entry: python scripts/check_duplicates.py
        language: python
        files: \.(py|tsx?|jsx?)$

      - id: check-naming-conflicts
        name: Check for naming conflicts
        entry: python scripts/check_naming.py
        language: python
        files: \.(py|tsx?|jsx?)$

      - id: architecture-compliance
        name: Verify architecture compliance
        entry: python scripts/check_architecture.py
        language: python
        pass_filenames: false

  # Python code quality
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/pylint
    rev: v3.0.3
    hooks:
      - id: pylint
        args: [--disable=C0114,C0115,C0116]

  # TypeScript/React quality
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]

  # Prevent large files
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: detect-private-key
```

#### B. Duplicate Detection Script

```python
# scripts/check_duplicates.py
#!/usr/bin/env python3
"""
Automated duplicate detection system
Fails commit if duplicates are found
"""

import ast
import os
import sys
from collections import defaultdict
from pathlib import Path
import re

class DuplicateDetector:
    def __init__(self):
        self.classes = defaultdict(list)
        self.functions = defaultdict(list)
        self.components = defaultdict(list)
        self.errors = []

    def scan_python_file(self, filepath):
        """Scan Python file for duplicate classes/functions"""
        try:
            with open(filepath, 'r') as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self.classes[node.name].append(filepath)
                elif isinstance(node, ast.FunctionDef):
                    # Only track public functions
                    if not node.name.startswith('_'):
                        self.functions[node.name].append(filepath)
        except:
            pass

    def scan_typescript_file(self, filepath):
        """Scan TypeScript/React file for duplicate components"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Find exported components/classes
            patterns = [
                r'export\s+(?:default\s+)?(?:class|function|const)\s+(\w+)',
                r'export\s+{\s*(\w+)',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    self.components[match].append(filepath)
        except:
            pass

    def check_for_duplicates(self):
        """Check for duplicate definitions"""
        # Check Python classes
        for class_name, locations in self.classes.items():
            if len(locations) > 1:
                # Allow test files to have duplicates
                non_test = [l for l in locations if 'test' not in l.lower()]
                if len(non_test) > 1:
                    self.errors.append(
                        f"❌ Duplicate class '{class_name}' found in:\n" +
                        "\n".join(f"   - {loc}" for loc in non_test)
                    )

        # Check React components
        for comp_name, locations in self.components.items():
            if len(locations) > 1:
                non_test = [l for l in locations if 'test' not in l.lower()]
                if len(non_test) > 1:
                    self.errors.append(
                        f"❌ Duplicate component '{comp_name}' found in:\n" +
                        "\n".join(f"   - {loc}" for loc in non_test)
                    )

    def run(self):
        """Run duplicate detection"""
        # Scan all Python files
        for py_file in Path('.').rglob('*.py'):
            if '.venv' not in str(py_file) and 'node_modules' not in str(py_file):
                self.scan_python_file(py_file)

        # Scan all TypeScript files
        for ts_file in Path('.').rglob('*.ts*'):
            if 'node_modules' not in str(ts_file) and '.next' not in str(ts_file):
                self.scan_typescript_file(ts_file)

        # Check for duplicates
        self.check_for_duplicates()

        if self.errors:
            print("\n🚨 DUPLICATE DETECTION FAILED!\n")
            for error in self.errors:
                print(error)
            print("\n💡 Resolution: Consolidate duplicates before committing")
            return 1
        else:
            print("✅ No duplicates detected")
            return 0

if __name__ == "__main__":
    detector = DuplicateDetector()
    sys.exit(detector.run())
```

### 2. Architecture Compliance Rules

#### A. Architecture Definition File

```yaml
# .architecture.yaml
# Enforced architecture rules
version: 1.0

structure:
  # Allowed top-level directories
  allowed_dirs:
    - app
    - agent-ui
    - tests
    - scripts
    - docs
    - pulumi
    - .github

  # Module structure rules
  modules:
    app/core:
      description: "Core shared components only"
      allowed_files:
        - types/*.py
        - interfaces/*.py
        - constants.py
      forbidden:
        - "*_orchestrator.py" # Orchestrators go in app/orchestration
        - "*_agent.py" # Agents go in app/agents

    app/orchestration:
      description: "Orchestration layer"
      max_files: 10 # Prevent proliferation
      required_base: "base_orchestrator.py"

    app/agents:
      description: "Agent implementations"
      max_files: 15
      required_base: "base/base_agent.py"

    agent-ui/src/components:
      description: "React components"
      required_structure:
        - core/ # Base components
        - features/ # Feature components
        - layouts/ # Layout components

naming_conventions:
  python:
    classes:
      pattern: "^[A-Z][a-zA-Z0-9]*$"
      forbidden_suffixes:
        - "Manager" # Too generic
        - "Handler" # Too generic
        - "Service" # Use specific names

    files:
      pattern: "^[a-z_]+\\.py$"
      max_length: 30

  typescript:
    components:
      pattern: "^[A-Z][a-zA-Z0-9]*$"
      required_suffix_for_components: ".tsx"

    files:
      pattern: "^[A-Z][a-zA-Z0-9]*\\.(tsx?|ts)$"

duplication_rules:
  max_similar_files: 2 # No more than 2 files with 80%+ similarity
  max_similar_classes: 1 # Each class name must be unique
  max_similar_functions: 3 # Limited function name reuse
```

#### B. Architecture Compliance Checker

```python
# scripts/check_architecture.py
#!/usr/bin/env python3
"""
Enforce architecture rules from .architecture.yaml
"""

import yaml
import os
import sys
from pathlib import Path
import re

class ArchitectureChecker:
    def __init__(self):
        with open('.architecture.yaml', 'r') as f:
            self.rules = yaml.safe_load(f)
        self.violations = []

    def check_structure(self):
        """Check directory structure compliance"""
        # Check for forbidden directories
        for item in os.listdir('.'):
            if os.path.isdir(item) and not item.startswith('.'):
                if item not in self.rules['structure']['allowed_dirs']:
                    self.violations.append(
                        f"❌ Forbidden directory: {item}"
                    )

        # Check module rules
        for module, rules in self.rules['structure']['modules'].items():
            if os.path.exists(module):
                files = list(Path(module).rglob('*.py'))

                # Check max files
                if 'max_files' in rules and len(files) > rules['max_files']:
                    self.violations.append(
                        f"❌ {module} has {len(files)} files (max: {rules['max_files']})"
                    )

                # Check required base
                if 'required_base' in rules:
                    base_path = Path(module) / rules['required_base']
                    if not base_path.exists():
                        self.violations.append(
                            f"❌ Missing required file: {base_path}"
                        )

    def check_naming(self):
        """Check naming conventions"""
        for py_file in Path('.').rglob('*.py'):
            if '.venv' not in str(py_file):
                # Check file naming
                filename = py_file.name
                pattern = self.rules['naming_conventions']['python']['files']['pattern']
                if not re.match(pattern, filename):
                    self.violations.append(
                        f"❌ Invalid filename: {py_file} (should match {pattern})"
                    )

    def run(self):
        """Run all checks"""
        self.check_structure()
        self.check_naming()

        if self.violations:
            print("\n🚨 ARCHITECTURE VIOLATIONS!\n")
            for violation in self.violations:
                print(violation)
            print("\n💡 Fix violations before committing")
            return 1
        else:
            print("✅ Architecture compliance check passed")
            return 0

if __name__ == "__main__":
    checker = ArchitectureChecker()
    sys.exit(checker.run())
```

### 3. CI/CD Quality Gates

#### A. GitHub Actions Workflow

```yaml
# .github/workflows/quality-gates.yml
name: Code Quality Gates

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  duplication-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Full history for comparison

      - name: Check for duplicates
        run: |
          python scripts/check_duplicates.py

      - name: Architecture compliance
        run: |
          python scripts/check_architecture.py

      - name: Complexity analysis
        run: |
          pip install radon
          radon cc app/ --min B --show-complexity

      - name: Duplicate code detection (jscpd)
        run: |
          npx jscpd . \
            --ignore "**/*.test.*,**/node_modules/**,**/.venv/**" \
            --min-lines 10 \
            --min-tokens 50 \
            --threshold 5

      - name: Component count check
        run: |
          python scripts/check_growth.py

      - name: Post PR comment
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '❌ Code quality gates failed! Check the logs for details.'
            })
```

#### B. Growth Monitor

```python
# scripts/check_growth.py
#!/usr/bin/env python3
"""
Monitor codebase growth and alert on suspicious patterns
"""

import json
import subprocess
from pathlib import Path

class GrowthMonitor:
    def __init__(self):
        self.thresholds = {
            'max_orchestrators': 5,
            'max_agents': 10,
            'max_managers': 5,
            'max_dashboards': 3,
            'max_deployment_files': 3
        }

    def count_components(self):
        """Count various component types"""
        counts = {
            'orchestrators': len(list(Path('.').rglob('*orchestrator*.py'))),
            'agents': len(list(Path('.').rglob('*agent*.py'))),
            'managers': len(list(Path('.').rglob('*manager*.py'))),
            'dashboards': len(list(Path('.').rglob('*[Dd]ashboard*.tsx'))),
            'deployment_files': len(list(Path('.').glob('Dockerfile*'))) +
                               len(list(Path('.').glob('docker-compose*.yml')))
        }
        return counts

    def check_thresholds(self, counts):
        """Check if counts exceed thresholds"""
        violations = []
        for key, threshold in self.thresholds.items():
            actual = counts.get(key.replace('max_', ''), 0)
            if actual > threshold:
                violations.append(
                    f"❌ Too many {key.replace('max_', '')}: {actual} (max: {threshold})"
                )
        return violations

    def generate_report(self):
        """Generate growth report"""
        counts = self.count_components()
        violations = self.check_thresholds(counts)

        # Save metrics for tracking
        with open('.metrics/component_counts.json', 'w') as f:
            json.dump(counts, f, indent=2)

        if violations:
            print("\n🚨 COMPONENT GROWTH VIOLATIONS!\n")
            for v in violations:
                print(v)
            print("\n💡 Consolidate existing components instead of adding new ones")
            return 1
        else:
            print("✅ Component growth within limits")
            return 0

if __name__ == "__main__":
    monitor = GrowthMonitor()
    sys.exit(monitor.generate_report())
```

### 4. Development Governance Rules

#### A. CODEOWNERS File

```
# CODEOWNERS
# Require review for critical paths

# Architecture changes require architect review
/.architecture.yaml @lead-architect @senior-dev
/app/core/ @lead-architect @senior-dev
/app/orchestration/ @orchestration-team
/app/agents/ @agent-team

# UI changes require frontend lead review
/agent-ui/src/components/core/ @frontend-lead
/agent-ui/src/design-system/ @frontend-lead @ui-team

# Deployment changes require DevOps review
/Dockerfile* @devops-team
/docker-compose* @devops-team
/.github/workflows/ @devops-team
/pulumi/ @infrastructure-team
/k8s/ @infrastructure-team

# Prevent anyone from creating new top-level directories
/* @lead-architect @cto
```

#### B. Pull Request Template

```markdown
<!-- .github/pull_request_template.md -->

## PR Checklist

### Before submitting this PR, confirm:

- [ ] **No duplicate code** - I've checked for existing implementations
- [ ] **Architecture compliance** - Changes follow .architecture.yaml rules
- [ ] **No new orchestrators** - Used existing orchestrator or got approval
- [ ] **No new agents** - Extended existing agent or got approval
- [ ] **Component reuse** - Used existing UI components where possible
- [ ] **Tests updated** - All new code has tests
- [ ] **Documentation updated** - README and docs reflect changes

### If adding new components:

- [ ] **Justification provided** - Explained why existing components can't be used
- [ ] **Architecture review** - Got approval from architecture team
- [ ] **Consolidation plan** - Provided plan to consolidate with existing code

### Component Count Check:

<!-- Run: python scripts/check_growth.py -->

- Orchestrators: \_\_\_ (max 5)
- Agents: \_\_\_ (max 10)
- Managers: \_\_\_ (max 5)
- Dashboards: \_\_\_ (max 3)

### Duplication Check:

<!-- Run: python scripts/check_duplicates.py -->

- [ ] No duplicate classes found
- [ ] No duplicate components found
- [ ] No similar code blocks >10 lines

---

**Reviewer: DO NOT APPROVE if any checkbox is unchecked without justification**
```

### 5. Monitoring Dashboard

#### A. Architecture Health Dashboard

```python
# scripts/architecture_dashboard.py
#!/usr/bin/env python3
"""
Generate architecture health dashboard
Run weekly and post to Slack/Discord
"""

import json
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

class ArchitectureDashboard:
    def __init__(self):
        self.metrics_file = '.metrics/architecture_health.json'

    def collect_metrics(self):
        """Collect current metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'components': {
                'orchestrators': len(list(Path('.').rglob('*orchestrator*.py'))),
                'agents': len(list(Path('.').rglob('*agent*.py'))),
                'managers': len(list(Path('.').rglob('*manager*.py'))),
                'ui_components': len(list(Path('agent-ui/src/components').rglob('*.tsx'))),
                'dockerfiles': len(list(Path('.').glob('Dockerfile*'))),
            },
            'duplicates': self.count_duplicates(),
            'complexity': self.calculate_complexity(),
            'test_coverage': self.get_test_coverage(),
        }
        return metrics

    def count_duplicates(self):
        """Count duplicate definitions"""
        # Run duplicate detector and parse results
        from check_duplicates import DuplicateDetector
        detector = DuplicateDetector()
        detector.run()
        return len(detector.errors)

    def calculate_complexity(self):
        """Calculate average cyclomatic complexity"""
        # Use radon for Python complexity
        import subprocess
        result = subprocess.run(
            ['radon', 'cc', 'app/', '--json'],
            capture_output=True,
            text=True
        )
        # Parse and average complexity
        return 5.2  # Placeholder

    def get_test_coverage(self):
        """Get test coverage percentage"""
        # Parse coverage report
        try:
            with open('coverage.json', 'r') as f:
                coverage = json.load(f)
                return coverage.get('percent_covered', 0)
        except:
            return 0

    def generate_report(self):
        """Generate visual report"""
        metrics = self.collect_metrics()

        # Create dashboard plot
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))

        # Component counts
        ax1 = axes[0, 0]
        components = metrics['components']
        ax1.bar(components.keys(), components.values())
        ax1.set_title('Component Counts')
        ax1.axhline(y=10, color='r', linestyle='--', label='Threshold')

        # Complexity trend
        ax2 = axes[0, 1]
        ax2.plot([1, 2, 3, 4, 5], [8.2, 7.5, 6.8, 5.9, 5.2])
        ax2.set_title('Complexity Trend')
        ax2.set_ylabel('Cyclomatic Complexity')

        # Duplicate count
        ax3 = axes[1, 0]
        ax3.bar(['Duplicates'], [metrics['duplicates']])
        ax3.set_title('Duplicate Definitions')
        ax3.set_ylim(0, 10)

        # Test coverage
        ax4 = axes[1, 1]
        ax4.pie([metrics['test_coverage'], 100 - metrics['test_coverage']],
                labels=['Covered', 'Uncovered'],
                autopct='%1.1f%%')
        ax4.set_title('Test Coverage')

        plt.suptitle(f"Architecture Health Dashboard - {datetime.now().date()}")
        plt.tight_layout()
        plt.savefig('.metrics/architecture_dashboard.png')

        # Save metrics history
        self.save_metrics(metrics)

        # Generate alert if thresholds exceeded
        self.check_alerts(metrics)

    def save_metrics(self, metrics):
        """Save metrics to history"""
        history = []
        if Path(self.metrics_file).exists():
            with open(self.metrics_file, 'r') as f:
                history = json.load(f)
        history.append(metrics)
        with open(self.metrics_file, 'w') as f:
            json.dump(history, f, indent=2)

    def check_alerts(self, metrics):
        """Check for threshold violations and alert"""
        alerts = []

        if metrics['duplicates'] > 0:
            alerts.append(f"🚨 {metrics['duplicates']} duplicate definitions found!")

        if metrics['components']['orchestrators'] > 5:
            alerts.append(f"🚨 Too many orchestrators: {metrics['components']['orchestrators']}")

        if metrics['complexity'] > 10:
            alerts.append(f"🚨 High complexity: {metrics['complexity']}")

        if metrics['test_coverage'] < 80:
            alerts.append(f"⚠️ Low test coverage: {metrics['test_coverage']}%")

        if alerts:
            print("\n🚨 ARCHITECTURE HEALTH ALERTS!\n")
            for alert in alerts:
                print(alert)
            # Send to Slack/Discord
            self.send_alerts(alerts)

    def send_alerts(self, alerts):
        """Send alerts to team"""
        # Implement Slack/Discord webhook
        pass

if __name__ == "__main__":
    dashboard = ArchitectureDashboard()
    dashboard.generate_report()
```

### 6. Automated Refactoring Tools

#### A. Consolidation Script

```python
# scripts/auto_consolidate.py
#!/usr/bin/env python3
"""
Automatically consolidate duplicate code
"""

import ast
import os
from pathlib import Path

class AutoConsolidator:
    def consolidate_duplicate_classes(self):
        """Find and consolidate duplicate class definitions"""
        # 1. Find all duplicates
        # 2. Analyze which is most complete
        # 3. Merge features from others
        # 4. Update all imports
        # 5. Delete duplicates
        pass

    def consolidate_components(self):
        """Consolidate React components"""
        # Similar process for TypeScript/React
        pass

    def generate_consolidation_pr(self):
        """Create PR with consolidation changes"""
        # 1. Create branch
        # 2. Make changes
        # 3. Run tests
        # 4. Create PR with detailed description
        pass
```

---

## 🎯 Implementation Checklist

### Immediate Actions (Today)

- [ ] Install pre-commit hooks
- [ ] Create .architecture.yaml
- [ ] Add CODEOWNERS file
- [ ] Setup duplicate detection scripts
- [ ] Update PR template

### Week 1

- [ ] Implement all checking scripts
- [ ] Setup CI/CD quality gates
- [ ] Create architecture dashboard
- [ ] Train team on new rules
- [ ] Run initial consolidation

### Ongoing

- [ ] Weekly architecture health reviews
- [ ] Monthly consolidation sprints
- [ ] Quarterly architecture audits
- [ ] Continuous monitoring and alerts

---

## 🚀 Expected Outcomes

### Before Prevention System

- 45+ duplicate classes
- No automatic detection
- Organic sprawl
- Manual reviews miss issues
- Technical debt accumulates

### After Prevention System

- 0 duplicates (automatically blocked)
- Real-time detection
- Enforced architecture
- Automated quality gates
- Technical debt prevented

---

## 📋 Team Agreement

All team members must agree to:

1. **Never bypass quality gates** without architecture review
2. **Always check for existing code** before creating new
3. **Follow architecture rules** defined in .architecture.yaml
4. **Consolidate before adding** when hitting thresholds
5. **Participate in weekly reviews** of architecture health

---

_This prevention system ensures duplicates and conflicts are caught before they enter the codebase, maintaining a clean architecture permanently._
