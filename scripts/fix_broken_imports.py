#!/usr/bin/env python3
"""
Fix all broken imports from deleted orchestrators
Redirect them to SuperOrchestrator or appropriate alternatives
"""

import re
from pathlib import Path

# Mapping of old imports to new ones
IMPORT_FIXES = {
    # SimpleAgentOrchestrator -> SuperOrchestrator
    r"from app\.agents\.simple_orchestrator import .*SimpleAgentOrchestrator.*": "from app.core.super_orchestrator import get_orchestrator as get_super_orchestrator",
    # AgentRole and other classes from simple_orchestrator
    r"from app\.agents\.simple_orchestrator import AgentRole.*": "from enum import Enum\n# Define AgentRole locally or use SuperOrchestrator",
    # Orchestra Manager
    r"from app\.agents\.orchestra_manager import.*": "from app.core.super_orchestrator import get_orchestrator",
    # Unified Enhanced Orchestrator
    r"from app\.swarms\.unified_enhanced_orchestrator import.*": "from app.core.super_orchestrator import get_orchestrator",
    # Swarm Orchestrator
    r"from app\.swarms\.coding\.swarm_orchestrator import.*": "from app.core.super_orchestrator import get_orchestrator",
    # Generic swarm imports
    r"from \.coding\.swarm_orchestrator import SwarmOrchestrator": "# SwarmOrchestrator removed - use SuperOrchestrator",
    r"from \.unified_enhanced_orchestrator import UnifiedSwarmOrchestrator": "# UnifiedSwarmOrchestrator removed - use SuperOrchestrator",
}

# Files to check
FILES_WITH_BROKEN_IMPORTS = [
    "app/analysis/engine.py",
    "app/nl_interface/command_dispatcher.py",
    "app/nl_interface/test_nl.py",
    "app/agno_bridge.py",
    "app/orchestration/unified_facade.py",
    "app/api/nl_endpoints.py",
    "app/swarms/__init__.py",
    "app/swarms/mcp/swarm_mcp_bridge.py",
    "app/infrastructure/dependency_injection.py",
]


def fix_file(filepath):
    """Fix imports in a single file"""
    if not Path(filepath).exists():
        print(f"⚠️  File not found: {filepath}")
        return False

    with open(filepath) as f:
        content = f.read()

    original = content
    changes = []

    # Apply each fix
    for pattern, replacement in IMPORT_FIXES.items():
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes.append(f"  - Fixed: {pattern[:50]}...")

    # Special case: comment out entire import lines that can't be fixed
    broken_patterns = [
        r"^from app\.swarms\.coding\.swarm_orchestrator import.*$",
        r"^from app\.swarms\.unified_enhanced_orchestrator import.*$",
        r"^from app\.agents\.orchestra_manager import.*$",
    ]

    for pattern in broken_patterns:
        content = re.sub(pattern, lambda m: f"# REMOVED: {m.group(0)}", content, flags=re.MULTILINE)

    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        print(f"✅ Fixed {filepath}")
        for change in changes:
            print(change)
        return True
    else:
        print(f"⏭️  No changes needed: {filepath}")
        return False


def add_super_orchestrator_adapter(filepath):
    """Add adapter code to use SuperOrchestrator in place of old orchestrators"""
    adapter_code = '''
# Adapter for SuperOrchestrator to replace old orchestrators
class OrchestratorAdapter:
    """Adapter to use SuperOrchestrator in place of old orchestrators"""

    def __init__(self):
        from app.core.super_orchestrator import get_orchestrator
        self.orchestrator = get_orchestrator()

    async def run_swarm(self, swarm_name: str, **kwargs):
        """Run a swarm through SuperOrchestrator"""
        return await self.orchestrator.process_request({
            "type": "agent",
            "action": "create",
            "config": {"name": swarm_name, **kwargs}
        })

    async def execute_task(self, task: str, **kwargs):
        """Execute a task through SuperOrchestrator"""
        return await self.orchestrator.process_request({
            "type": "command",
            "command": "execute",
            "params": {"task": task, **kwargs}
        })

# Create global adapter instance
orchestrator_adapter = OrchestratorAdapter()
'''
    return adapter_code


def main():
    print("🔧 Fixing broken imports from deleted orchestrators...")
    print("=" * 50)

    fixed_count = 0

    for filepath in FILES_WITH_BROKEN_IMPORTS:
        if fix_file(filepath):
            fixed_count += 1

    # Also check swarms/__init__.py specifically
    init_file = "app/swarms/__init__.py"
    if Path(init_file).exists():
        with open(init_file) as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            if (
                "swarm_orchestrator" in line.lower()
                or "unified_enhanced_orchestrator" in line.lower()
            ):
                new_lines.append(f"# REMOVED: {line}")
            else:
                new_lines.append(line)

        with open(init_file, "w") as f:
            f.writelines(new_lines)
        print(f"✅ Cleaned {init_file}")

    print(f"\n📊 Summary: Fixed {fixed_count} files")
    print("\n⚠️  Note: Some files may need manual adjustment to use SuperOrchestrator properly")
    print("Consider adding the OrchestratorAdapter class where needed.")


if __name__ == "__main__":
    main()
