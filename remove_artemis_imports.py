#!/usr/bin/env python3
"""Script to remove Artemis imports from Python files."""

import re
from pathlib import Path

files_to_update = [
    "./app/integrations/gong_sophia_bridge.py",
    "./app/orchestration/factory_aware_orchestrator.py",
    "./app/api/routers/research_swarm.py",
    "./app/api/mcp/status.py",
    "./app/swarms/core/swarm_integration.py",
    "./app/swarms/core/scheduler.py",
    "./app/swarms/templates/swarm_generator.py",
    "./app/swarms/orchestrator_research_swarm.py",
    "./app/factory/comprehensive_swarm_factory.py",
    "./tests/test_orchestrators.py",
]

def remove_artemis_imports(filepath):
    """Remove Artemis imports and references from a Python file."""
    try:
        path = Path(filepath)
        if not path.exists():
            print(f"Skipping {filepath} - file not found")
            return
            
        content = path.read_text()
        original = content
        
        # Remove import lines containing artemis
        content = re.sub(r'^from .*artemis.*import.*$', '# Artemis import removed', content, flags=re.MULTILINE)
        content = re.sub(r'^import .*artemis.*$', '# Artemis import removed', content, flags=re.MULTILINE)
        
        # Remove ArtemisOrchestrator, ArtemisAgentFactory, etc. from code
        content = re.sub(r'ArtemisOrchestrator\([^)]*\)', 'None  # ArtemisOrchestrator removed', content)
        content = re.sub(r'ArtemisAgentFactory\([^)]*\)', 'None  # ArtemisAgentFactory removed', content)
        content = re.sub(r'artemis_factory\([^)]*\)', 'None  # artemis_factory removed', content)
        content = re.sub(r'artemis_unified_factory\([^)]*\)', 'None  # artemis_unified_factory removed', content)
        content = re.sub(r'get_artemis_orchestrator\([^)]*\)', 'None  # get_artemis_orchestrator removed', content)
        content = re.sub(r'ArtemisSwarmFactory\([^)]*\)', 'None  # ArtemisSwarmFactory removed', content)
        content = re.sub(r'ArtemisMillitaryOrchestrator\([^)]*\)', 'None  # ArtemisMillitaryOrchestrator removed', content)
        
        if content != original:
            path.write_text(content)
            print(f"Updated {filepath}")
        else:
            print(f"No changes needed in {filepath}")
            
    except Exception as e:
        print(f"Error updating {filepath}: {e}")

if __name__ == "__main__":
    print("Removing Artemis imports from Python files...")
    for filepath in files_to_update:
        remove_artemis_imports(filepath)
    print("Done!")