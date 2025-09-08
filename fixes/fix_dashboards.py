#!/usr/bin/env python3
import re
from pathlib import Path

"""
Applies simple regex-based fixes to common TSX syntax issues found in dashboards.
This is a non-destructive pass that only runs if files exist.
"""

dashboards = [
    'agent-ui/src/components/sophia/PayReadyDashboard.tsx',
    'agent-ui/src/components/sophia/MCPBusinessIntelligence.tsx',
    'agent-ui/src/components/dashboards/TeamPerformanceOptimizer.tsx',
    'agent-ui/src/components/dashboards/SalesPerformanceDashboard.tsx'
]

for dash_path in dashboards:
    p = Path(dash_path)
    if not p.exists():
        continue

    content = p.read_text()
    original = content

    # Fix unescaped < in JSX text
    content = re.sub(r'>(\s*)<(\s*\d)', r'>\1&lt;\2', content)

    # Fix missing semicolons before const/return across lines
    content = re.sub(r'(\w)\n(\s*(?:const|return))', r'\1;\n\2', content)

    if content != original:
        p.write_text(content)
        print(f"✅ Fixed {dash_path}")
    else:
        print(f"ℹ️ No changes needed: {dash_path}")

