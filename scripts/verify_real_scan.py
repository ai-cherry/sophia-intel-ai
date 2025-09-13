#!/usr/bin/env python3
"""
Verify that agents are doing REAL scans, not simulated bullshit
"""
import glob
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Count actual files in repo
repo_path = "/Users/lynnmusil/sophia-intel-ai"
print("VERIFYING REAL REPOSITORY STRUCTURE:")
print("=" * 50)
# Count files
py_files = glob.glob(f"{repo_path}/**/*.py", recursive=True)
ts_files = glob.glob(f"{repo_path}/**/*.ts", recursive=True)
tsx_files = glob.glob(f"{repo_path}/**/*.tsx", recursive=True)
yaml_files = glob.glob(f"{repo_path}/**/*.yaml", recursive=True)
print(f"Python files: {len(py_files)}")
print(f"TypeScript files: {len(ts_files)}")
print(f"TSX files: {len(tsx_files)}")
print(f"YAML files: {len(yaml_files)}")
print(
    f"TOTAL CODE FILES: {len(py_files) + len(ts_files) + len(tsx_files) + len(yaml_files)}"
)
print("\nKEY DIRECTORIES:")
for dir in ["app", "sophia-intel-app", "scripts", "k8s", "tests"]:
    path = os.path.join(repo_path, dir)
    if os.path.exists(path):
        print(f"✓ /{dir}/ exists")
print("\nCRITICAL FILES TO SCAN:")
critical_files = [
    "app//unified_factory.py",
    "app/sophia/sophia_orchestrator.py",
    "app/core/websocket_manager.py",
    "app/core/portkey_config.py",
    ".env",
]
for file in critical_files:
    path = os.path.join(repo_path, file)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"✓ {file} ({size:,} bytes)")
    else:
        print(f"✗ {file} NOT FOUND")
print("\n" + "=" * 50)
print("AGENTS SHOULD REPORT THESE REAL FILES AND ISSUES")
