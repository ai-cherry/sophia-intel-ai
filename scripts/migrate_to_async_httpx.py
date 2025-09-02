#!/usr/bin/env python3
"""
Migration Script: Replace all blocking requests with async HTTPX
Part of 2025 Architecture Migration
"""

import os
import re
import asyncio
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Patterns to identify blocking HTTP calls
BLOCKING_PATTERNS = [
    (r'import requests\b', 'import httpx'),
    (r'from requests import', 'from httpx import'),
    (r'requests\.get\(', 'await async_client.get('),
    (r'requests\.post\(', 'await async_client.post('),
    (r'requests\.put\(', 'await async_client.put('),
    (r'requests\.delete\(', 'await async_client.delete('),
    (r'requests\.Session\(\)', 'httpx.AsyncClient()'),
    (r'\.json\(\)', '.json()'),  # httpx has same API
    (r'\.text', '.text'),  # httpx has same API
    (r'\.status_code', '.status_code'),  # httpx has same API
]

# Files to migrate
def find_python_files(root_dir: str) -> List[Path]:
    """Find all Python files that might use requests"""
    files = []
    for path in Path(root_dir).rglob("*.py"):
        # Skip migration scripts and tests
        if "migrate" in str(path) or "test_" in str(path):
            continue
        
        # Check if file contains requests
        try:
            content = path.read_text()
            if "requests" in content or "urllib" in content:
                files.append(path)
        except Exception:
            pass
    
    return files


def analyze_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a file for blocking HTTP calls"""
    content = file_path.read_text()
    lines = content.split('\n')
    
    findings = {
        "file": str(file_path),
        "has_requests": "import requests" in content or "from requests" in content,
        "has_urllib": "urllib" in content,
        "blocking_calls": [],
        "async_ready": "async def" in content
    }
    
    # Find blocking calls
    for i, line in enumerate(lines, 1):
        for pattern, _ in BLOCKING_PATTERNS:
            if re.search(pattern, line):
                findings["blocking_calls"].append({
                    "line": i,
                    "code": line.strip(),
                    "pattern": pattern
                })
    
    return findings


def generate_migration_report(files: List[Path]) -> str:
    """Generate migration report"""
    report = []
    report.append("=" * 60)
    report.append("ASYNC HTTPX MIGRATION REPORT")
    report.append("=" * 60)
    report.append("")
    
    total_blocking_calls = 0
    files_to_migrate = []
    
    for file_path in files:
        analysis = analyze_file(file_path)
        if analysis["blocking_calls"]:
            files_to_migrate.append(analysis)
            total_blocking_calls += len(analysis["blocking_calls"])
    
    report.append(f"Files analyzed: {len(files)}")
    report.append(f"Files with blocking calls: {len(files_to_migrate)}")
    report.append(f"Total blocking calls found: {total_blocking_calls}")
    report.append("")
    
    if files_to_migrate:
        report.append("FILES TO MIGRATE:")
        report.append("-" * 40)
        for analysis in files_to_migrate[:10]:  # Show first 10
            rel_path = os.path.relpath(analysis["file"], "/Users/lynnmusil/sophia-intel-ai")
            report.append(f"\n📁 {rel_path}")
            report.append(f"   Async ready: {'✅' if analysis['async_ready'] else '❌'}")
            report.append(f"   Blocking calls: {len(analysis['blocking_calls'])}")
            
            for call in analysis["blocking_calls"][:3]:  # Show first 3
                report.append(f"   Line {call['line']}: {call['code'][:60]}...")
    
    return "\n".join(report)


def create_async_wrapper(file_path: Path) -> str:
    """Create async wrapper for a file"""
    content = file_path.read_text()
    
    # Add async HTTP client import
    if "import httpx" not in content:
        import_line = "from app.core.async_http_client import AsyncHTTPClient, async_get, async_post\n"
        
        # Find where to insert import
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                continue
            else:
                lines.insert(i, import_line)
                break
        
        content = '\n'.join(lines)
    
    # Replace blocking patterns
    for pattern, replacement in BLOCKING_PATTERNS:
        content = re.sub(pattern, replacement, content)
    
    # Make functions async if they contain await
    if "await " in content and "async def" not in content:
        content = re.sub(r'def (\w+)\(', r'async def \1(', content)
    
    return content


async def test_migration():
    """Test the migration with a sample file"""
    sample_code = '''
import requests
import json

def fetch_data(url):
    response = requests.get(url, timeout=10)
    return response.json()

def post_data(url, data):
    response = requests.post(url, json=data)
    return response.status_code
'''
    
    print("BEFORE MIGRATION:")
    print(sample_code)
    print("\n" + "=" * 40 + "\n")
    
    # Simulate migration
    migrated = sample_code
    for pattern, replacement in BLOCKING_PATTERNS:
        migrated = re.sub(pattern, replacement, migrated)
    
    # Make async
    migrated = re.sub(r'def (\w+)\(', r'async def \1(', migrated)
    
    # Add imports
    migrated = "from app.core.async_http_client import AsyncHTTPClient, async_get, async_post\n" + migrated
    
    print("AFTER MIGRATION:")
    print(migrated)


def main():
    """Run migration analysis"""
    root_dir = "/Users/lynnmusil/sophia-intel-ai"
    
    print("🔍 Scanning for files with blocking HTTP calls...")
    files = find_python_files(root_dir)
    
    print(f"📊 Found {len(files)} files to analyze")
    
    report = generate_migration_report(files)
    print(report)
    
    # Save report
    report_path = Path(root_dir) / "migration_report_httpx.txt"
    report_path.write_text(report)
    print(f"\n📝 Report saved to: {report_path}")
    
    # Optionally run test
    print("\n🧪 Running migration test...")
    asyncio.run(test_migration())


if __name__ == "__main__":
    main()