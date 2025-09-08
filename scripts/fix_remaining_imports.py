#!/usr/bin/env python3
"""
Fix remaining import issues after cleanup
"""

import re
from pathlib import Path


def fix_imports(file_path: Path) -> bool:
    """Fix imports in a file"""
    with open(file_path) as f:
        content = f.read()

    original = content

    # Fix patterns
    replacements = [
        # Unified orchestrator imports
        (
            r"from app\.swarms\.unified_enhanced_orchestrator import UnifiedSwarmOrchestrator",
            "from app.swarms import UnifiedSwarmOrchestrator",
        ),
        # Coding swarm orchestrator
        (
            r"from app\.swarms\.coding\.swarm_orchestrator import SwarmOrchestrator",
            "from app.swarms import SwarmOrchestrator",
        ),
        # Generic swarm import that should use new pattern
        (
            r"from \.unified_enhanced_orchestrator import UnifiedSwarmOrchestrator",
            "from app.swarms import UnifiedSwarmOrchestrator",
        ),
        # Import that refers to old SwarmOrchestrator in coding module
        (
            r"from \.coding\.swarm_orchestrator import SwarmOrchestrator",
            "from app.swarms import SwarmOrchestrator",
        ),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    if content != original:
        with open(file_path, "w") as f:
            f.write(content)
        return True
    return False


def main():
    """Main function"""
    root = Path(__file__).parent.parent

    # Files to fix
    files_to_fix = [
        "tests/test_all_swarms.py",
        "tests/integration/test_memory_swarm_integration.py",
        "scripts/dev/debug_consciousness_tests.py",
        "tests/integration/test_consciousness_tracking_integration.py",
    ]

    fixed_count = 0
    for file_path in files_to_fix:
        full_path = root / file_path
        if full_path.exists():
            if fix_imports(full_path):
                print(f"✅ Fixed imports in {file_path}")
                fixed_count += 1
            else:
                print(f"⏭️  No changes needed in {file_path}")
        else:
            print(f"❌ File not found: {file_path}")

    print(f"\n✨ Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
