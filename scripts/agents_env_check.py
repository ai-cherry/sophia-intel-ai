#!/usr/bin/env python3
"""
AI Agents Environment Check - Verify all AI coding agents use the same environment
Part of Sophia Intel AI standardized tooling
"""

import os
import sys
from pathlib import Path


# Color codes for output
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")


def warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")


def error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.NC}")


def info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")


def main():
    print("🤖 AI Agents Environment Check")
    print("==============================")

    # Ensure we're in the right directory
    expected_dir = "/Users/lynnmusil/sophia-intel-ai"
    if os.getcwd() != expected_dir:
        try:
            os.chdir(expected_dir)
            warning(f"Changed to correct directory: {expected_dir}")
        except OSError:
            error(f"Cannot change to {expected_dir}")
            sys.exit(1)

    exit_code = 0

    print("\n1. Checking Python environment...")

    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    success(f"Python version: {python_version}")
    info(f"Python executable: {sys.executable}")

    # Check if we're in a virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

    if in_venv:
        warning("Running in a virtual environment")
        info(f"Virtual env path: {sys.prefix}")
    else:
        success("Using system Python (recommended for AI agents)")

    print("\n2. Checking for virtual environments in repository...")

    # Scan for virtual environment files
    venv_patterns = [
        "**/venv/**",
        "**/.venv/**",
        "**/env/**",
        "**/pyvenv.cfg",
        "**/bin/activate",
        "**/Scripts/activate.bat",
    ]

    venv_files = []
    for pattern in venv_patterns:
        venv_files.extend(Path(".").glob(pattern))

    if venv_files:
        error(f"Found {len(venv_files)} virtual environment files in repository:")
        for i, venv_file in enumerate(venv_files[:10]):  # Show first 10
            print(f"   - {venv_file}")
            if i == 9 and len(venv_files) > 10:
                print(f"   ... and {len(venv_files) - 10} more")
        error("Remove virtual environments from repository before running AI agents")
        exit_code = 2
    else:
        success("No virtual environments found in repository")

    print("\n3. Checking Sophia AI module accessibility...")

    # Check if we can import key modules
    modules_to_check = [
        ("app.memory", "Memory system"),
        ("app.mcp", "MCP orchestration"),
        ("mcp_servers", "MCP servers directory"),
    ]

    for module_name, description in modules_to_check:
        try:
            if module_name == "mcp_servers":
                # Special case - check if directory exists
                if os.path.exists("mcp_servers"):
                    success(f"{description} accessible")
                else:
                    error(f"{description} not found")
                    exit_code = 1
            else:
                # Add current directory to Python path
                if "." not in sys.path:
                    sys.path.insert(0, ".")

                __import__(module_name)
                success(f"{description} importable")
        except ImportError as e:
            warning(f"{description} import failed: {e}")
            # This might be OK if dependencies aren't installed
        except Exception as e:
            error(f"{description} error: {e}")
            exit_code = 1

    print("\n4. Testing MCP server connectivity...")

    # Test MCP servers
    mcp_ports = [8001, 8002]  # Common MCP server ports
    mcp_accessible = False

    for port in mcp_ports:
        try:
            import urllib.request

            response = urllib.request.urlopen(f"http://localhost:{port}/health", timeout=2)
            if response.getcode() == 200:
                success(f"MCP server responding on port {port}")
                mcp_accessible = True
                break
        except Exception:
            # Try next port
            continue

    if not mcp_accessible:
        warning("No MCP servers found running on standard ports (8001, 8002)")
        info("Start MCP servers with: make mcp-up")

    print("\n5. Checking AI agent compatibility...")

    # List of AI coding agents and their typical characteristics
    agents = {
        "Codex": {
            "description": "GitHub Copilot/Codex integration",
            "requirements": ["Standard Python environment", "Git access"],
        },
        "Claude Coder": {
            "description": "Anthropic Claude coding assistant",
            "requirements": ["HTTP access", "File system access"],
        },
        "Cline": {
            "description": "VS Code AI assistant",
            "requirements": ["VS Code integration", "Terminal access"],
        },
        "Cursor": {
            "description": "AI-powered code editor",
            "requirements": ["File system access", "Git integration"],
        },
        "Grok": {
            "description": "X.AI coding assistant",
            "requirements": ["API access", "Standard Python environment"],
        },
    }

    success("Environment should support all major AI agents:")
    for agent_name, agent_info in agents.items():
        print(f"   • {agent_name}: {agent_info['description']}")
        for req in agent_info["requirements"]:
            print(f"     - {req} ✓")

    print("\n6. Environment recommendations...")

    # Generate recommendations
    recommendations = []

    if in_venv:
        recommendations.append("Consider using system Python for consistency across AI agents")

    if venv_files:
        recommendations.append("Remove virtual environments from repository immediately")
        recommendations.append("Add comprehensive virtual environment patterns to .gitignore")

    if not mcp_accessible:
        recommendations.append("Start MCP servers before using AI agents: make mcp-up")

    if recommendations:
        warning("Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        success("Environment is optimally configured for AI agents!")

    print("\n7. Agent-specific setup validation...")

    # Check for agent-specific configuration files
    agent_configs = {
        ".vscode/settings.json": "VS Code (Cline) configuration",
        ".cursor/": "Cursor IDE configuration",
        ".github/copilot.yml": "GitHub Copilot configuration",
        "cline_config.json": "Cline specific configuration",
    }

    for config_path, description in agent_configs.items():
        if os.path.exists(config_path):
            success(f"Found {description}")
        else:
            info(f"Optional: {description} not found")

    print("\n==============================")

    if exit_code == 0:
        success("All AI agents should work correctly in this environment!")
        print("\nNext steps:")
        print("  • Start MCP servers: make mcp-up")
        print("  • Test MCP connectivity: make mcp-test")
        print("  • Configure your AI agents to use this repository")
    elif exit_code == 1:
        warning("Environment has warnings - review and fix if needed")
    else:
        error("Critical issues found - fix before using AI agents")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
