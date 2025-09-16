#!/usr/bin/env python3
"""
System Validation Script for Sophia Intel AI
Tests all components without requiring Portkey to work
"""
import json
import subprocess
import requests
import time
from pathlib import Path

def test_mcp_servers():
    """Test all MCP servers are running"""
    servers = {
        "Memory Server": "http://localhost:8081/health",
        "Filesystem Server": "http://localhost:8082/health", 
        "Git Server": "http://localhost:8084/health",
        "Vector Server": "http://localhost:8085/health"
    }
    
    print("🔍 Testing MCP Servers...")
    all_ok = True
    for name, url in servers.items():
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print(f"  ✅ {name}: Running")
            else:
                print(f"  ❌ {name}: Not healthy (status {r.status_code})")
                all_ok = False
        except:
            print(f"  ❌ {name}: Not reachable")
            all_ok = False
    return all_ok

def test_workbench_ui():
    """Test Workbench UI is running"""
    print("\n🔍 Testing Workbench UI...")
    try:
        r = requests.get("http://localhost:3200", timeout=2)
        if r.status_code in [200, 302]:
            print(f"  ✅ Workbench UI: Running on port 3200")
            return True
        else:
            print(f"  ❌ Workbench UI: Unexpected status {r.status_code}")
            return False
    except:
        print(f"  ❌ Workbench UI: Not reachable")
        return False

def test_cli_structure():
    """Test CLI is properly installed"""
    print("\n🔍 Testing CLI Structure...")
    cli_path = Path("./bin/sophia")
    if cli_path.exists() and cli_path.is_file():
        print(f"  ✅ CLI Binary: Found at {cli_path}")
        # Test it can be executed
        try:
            result = subprocess.run(
                ["./bin/sophia", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"  ✅ CLI Execution: Working")
                return True
            else:
                print(f"  ❌ CLI Execution: Failed")
                return False
        except:
            print(f"  ❌ CLI Execution: Error")
            return False
    else:
        print(f"  ❌ CLI Binary: Not found")
        return False

def test_virtual_keys():
    """Check virtual keys are configured"""
    print("\n🔍 Checking Virtual Keys Configuration...")
    vk_file = Path("config/portkey_virtual_keys.json")
    if vk_file.exists():
        data = json.loads(vk_file.read_text())
        vks = data.get("virtual_keys", {})
        print(f"  📋 Found {len(vks)} virtual keys configured:")
        for provider, key in vks.items():
            if key and key != "":
                print(f"    ✅ {provider}: {key[:20]}...")
            else:
                print(f"    ❌ {provider}: Not configured")
        return True
    else:
        print(f"  ❌ Virtual keys config not found")
        return False

def test_git_status():
    """Check git repository status"""
    print("\n🔍 Checking Git Status...")
    try:
        # Check current branch
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True
        ).stdout.strip()
        print(f"  📌 Current branch: {branch}")
        
        # Check for uncommitted changes
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True
        ).stdout
        if status:
            print(f"  ⚠️  Uncommitted changes detected")
        else:
            print(f"  ✅ Working directory clean")
        return True
    except:
        print(f"  ❌ Git check failed")
        return False

def main():
    print("=" * 60)
    print("SOPHIA INTEL AI - SYSTEM VALIDATION")
    print("=" * 60)
    
    results = {
        "MCP Servers": test_mcp_servers(),
        "Workbench UI": test_workbench_ui(),
        "CLI Structure": test_cli_structure(),
        "Virtual Keys": test_virtual_keys(),
        "Git Status": test_git_status()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_pass = True
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {component}: {'PASS' if status else 'FAIL'}")
        if not status:
            all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass:
        print("✅ SYSTEM FULLY OPERATIONAL (except Portkey API keys)")
        print("\nTo complete setup:")
        print("1. Verify your OpenAI API key in Portkey dashboard")
        print("2. Wait 1-2 minutes for changes to propagate")
        print("3. Test with: source setup_portkey_env.sh && ./bin/sophia chat --model openai/gpt-4o-mini --input 'test'")
    else:
        print("❌ SOME COMPONENTS NEED ATTENTION")
        print("\nPlease fix the failed components above.")
    print("=" * 60)

if __name__ == "__main__":
    main()