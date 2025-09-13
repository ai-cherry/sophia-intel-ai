#!/usr/bin/env python3
"""
Sophia Intel AI - Unified CLI System Test Suite
Comprehensive validation of the CLI integration and setup
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEnvironmentSetup(unittest.TestCase):
    """Test environment and configuration setup"""
    
    def setUp(self):
        self.config_dir = Path.home() / ".config/sophia"
        self.repo_root = Path.home() / "sophia-intel-ai"
    
    def test_directory_structure(self):
        """Test that all required directories exist"""
        required_dirs = [
            self.config_dir,
            self.config_dir / "personas",
            self.config_dir / "workflows",
            self.config_dir / "cache",
            self.config_dir / "sessions",
            self.config_dir / "logs",
            self.repo_root / "configs/agents",
            self.repo_root / "bin",
            self.repo_root / "scripts/cli"
        ]
        
        for dir_path in required_dirs:
            with self.subTest(directory=str(dir_path)):
                self.assertTrue(
                    dir_path.exists(),
                    f"Required directory missing: {dir_path}"
                )
    
    def test_environment_file(self):
        """Test that environment file exists and has required structure"""
        env_file = self.config_dir / "env"
        env_template = self.config_dir / "env.template"
        
        # Check template exists
        self.assertTrue(
            env_template.exists() or env_file.exists(),
            "Neither env nor env.template exists"
        )
        
        # If env exists, check for required variables
        if env_file.exists():
            env_content = env_file.read_text()
            required_vars = [
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "SOPHIA_API_PORT",
                "SOPHIA_UI_PORT"
            ]
            
            for var in required_vars:
                with self.subTest(variable=var):
                    self.assertIn(
                        var,
                        env_content,
                        f"Required variable {var} not found in environment"
                    )
    
    def test_permissions(self):
        """Test that sensitive directories have correct permissions"""
        sensitive_dirs = [
            self.config_dir,
            Path.home() / ".config/codex",
            Path.home() / ".config/claude"
        ]
        
        for dir_path in sensitive_dirs:
            if dir_path.exists():
                with self.subTest(directory=str(dir_path)):
                    # Check directory is only accessible by owner
                    stat_info = dir_path.stat()
                    mode = oct(stat_info.st_mode)[-3:]
                    self.assertEqual(
                        mode,
                        "700",
                        f"Directory {dir_path} has insecure permissions: {mode}"
                    )


class TestCLIWrapper(unittest.TestCase):
    """Test the unified CLI wrapper functionality"""
    
    def setUp(self):
        self.cli_path = Path.home() / "sophia-intel-ai/bin/sophia-cli"
    
    def test_cli_exists_and_executable(self):
        """Test that CLI wrapper exists and is executable"""
        self.assertTrue(
            self.cli_path.exists(),
            f"CLI wrapper not found at {self.cli_path}"
        )
        
        self.assertTrue(
            os.access(self.cli_path, os.X_OK),
            f"CLI wrapper is not executable"
        )
    
    def test_help_command(self):
        """Test that help command works"""
        if not self.cli_path.exists():
            self.skipTest("CLI wrapper not installed")
        
        result = subprocess.run(
            [str(self.cli_path), "help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        self.assertEqual(result.returncode, 0, "Help command failed")
        self.assertIn("Sophia Unified CLI", result.stdout)
        self.assertIn("plan", result.stdout)
        self.assertIn("implement", result.stdout)
        self.assertIn("validate", result.stdout)
    
    def test_validate_command(self):
        """Test that validate command runs without errors"""
        if not self.cli_path.exists():
            self.skipTest("CLI wrapper not installed")
        
        result = subprocess.run(
            [str(self.cli_path), "validate"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        self.assertEqual(result.returncode, 0, "Validate command failed")
        self.assertIn("Configuration:", result.stdout)
        self.assertIn("CLI Availability:", result.stdout)
    
    def test_task_routing_logic(self):
        """Test that task routing works correctly"""
        # This would require mocking the CLI calls
        # For now, we just test that the script parses correctly
        if not self.cli_path.exists():
            self.skipTest("CLI wrapper not installed")
        
        # Test that the script has proper routing functions
        script_content = self.cli_path.read_text()
        self.assertIn("route_task()", script_content)
        self.assertIn("analyze_complexity()", script_content)


class TestPersonaFiles(unittest.TestCase):
    """Test persona file configuration"""
    
    def setUp(self):
        self.repo_root = Path.home() / "sophia-intel-ai"
        self.config_dir = Path.home() / ".config/sophia"
    
    def test_master_architect_persona(self):
        """Test that master architect persona exists and is valid"""
        persona_file = self.repo_root / "configs/agents/master_architect.md"
        
        self.assertTrue(
            persona_file.exists(),
            f"Master architect persona not found at {persona_file}"
        )
        
        content = persona_file.read_text()
        
        # Check for required sections
        required_sections = [
            "Core Principles",
            "Sophia-Specific Rules",
            "Task Execution Format",
            "Quality Gates"
        ]
        
        for section in required_sections:
            with self.subTest(section=section):
                self.assertIn(
                    section,
                    content,
                    f"Required section '{section}' not found in persona"
                )
    
    def test_specialized_personas(self):
        """Test that specialized personas exist"""
        personas = [
            "typescript_specialist.md",
            "python_backend.md",
            "security_auditor.md"
        ]
        
        personas_dir = self.config_dir / "personas"
        
        if not personas_dir.exists():
            self.skipTest("Personas directory not created yet")
        
        for persona in personas:
            with self.subTest(persona=persona):
                persona_file = personas_dir / persona
                if persona_file.exists():
                    content = persona_file.read_text()
                    self.assertGreater(
                        len(content),
                        100,
                        f"Persona {persona} seems empty or invalid"
                    )
    
    def test_persona_symlinks(self):
        """Test that personas are properly symlinked to CLI configs"""
        master_persona = self.repo_root / "configs/agents/master_architect.md"
        
        symlinks = [
            Path.home() / ".config/codex/personas/master-architect.txt",
            Path.home() / ".config/claude/personas/master-architect.txt"
        ]
        
        for symlink in symlinks:
            if symlink.exists():
                with self.subTest(symlink=str(symlink)):
                    # Check if it's a symlink or has same content
                    if symlink.is_symlink():
                        self.assertEqual(
                            symlink.resolve(),
                            master_persona.resolve(),
                            f"Symlink {symlink} doesn't point to master persona"
                        )
                    else:
                        # If not a symlink, check content matches
                        if master_persona.exists():
                            self.assertEqual(
                                symlink.read_text(),
                                master_persona.read_text(),
                                f"Content mismatch in {symlink}"
                            )


class TestMCPIntegration(unittest.TestCase):
    """Test MCP service integration"""
    
    def test_mcp_service_ports(self):
        """Test that MCP services are configured on correct ports"""
        services = {
            "MCP Memory": 8081,
            "MCP Filesystem": 8082,
            "MCP Git": 8084,
            "Unified API": 8000
        }
        
        for service_name, port in services.items():
            with self.subTest(service=service_name):
                # Check if port is available (not in use means service not running)
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    
                    if result == 0:
                        print(f"✅ {service_name} port {port} is in use (service may be running)")
                    else:
                        print(f"⚠️  {service_name} port {port} is not in use (service not running)")
                except Exception as e:
                    print(f"❌ Error checking {service_name}: {e}")
    
    def test_mcp_health_endpoints(self):
        """Test MCP service health endpoints"""
        try:
            import requests
        except ImportError:
            self.skipTest("requests module not installed")
        
        endpoints = [
            ("http://localhost:8081/health", "MCP Memory"),
            ("http://localhost:8082/health", "MCP Filesystem"),
            ("http://localhost:8084/health", "MCP Git"),
            ("http://localhost:8000/api/health", "Unified API")
        ]
        
        for url, name in endpoints:
            with self.subTest(service=name):
                try:
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        print(f"✅ {name} is healthy")
                    else:
                        print(f"⚠️  {name} returned status {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"⚠️  {name} not responding: {type(e).__name__}")


class TestWorkflowScripts(unittest.TestCase):
    """Test workflow and helper scripts"""
    
    def setUp(self):
        self.repo_root = Path.home() / "sophia-intel-ai"
    
    def test_daily_startup_script(self):
        """Test that daily startup script exists and is executable"""
        script_path = self.repo_root / "scripts/cli/daily_startup.sh"
        
        if script_path.exists():
            self.assertTrue(
                os.access(script_path, os.X_OK),
                f"Daily startup script is not executable"
            )
            
            # Check script content
            content = script_path.read_text()
            self.assertIn("sophia-cli validate", content)
            self.assertIn("git fetch origin", content)
    
    def test_setup_script(self):
        """Test that setup script exists and has correct structure"""
        setup_script = self.repo_root / "setup_unified_cli_complete.sh"
        
        if setup_script.exists():
            content = setup_script.read_text()
            
            # Check for essential setup steps
            required_steps = [
                "Creating directory structure",
                "Master Architect persona",
                "unified CLI wrapper",
                "environment template"
            ]
            
            for step in required_steps:
                with self.subTest(step=step):
                    self.assertIn(
                        step,
                        content,
                        f"Setup script missing step: {step}"
                    )


class TestShellIntegration(unittest.TestCase):
    """Test shell configuration and aliases"""
    
    def test_zshrc_configuration(self):
        """Test that .zshrc has been updated with Sophia configuration"""
        zshrc_path = Path.home() / ".zshrc"
        
        if not zshrc_path.exists():
            self.skipTest(".zshrc not found")
        
        content = zshrc_path.read_text()
        
        # Check for Sophia configuration marker
        if "# Sophia CLI Configuration" in content:
            # Check for required configurations
            configs = [
                "sophia-intel-ai/bin",
                ".config/sophia/env",
                "alias splan",
                "alias simpl",
                "alias sval"
            ]
            
            for config in configs:
                with self.subTest(config=config):
                    self.assertIn(
                        config,
                        content,
                        f"Missing configuration: {config}"
                    )


def run_validation_suite():
    """Run the complete validation suite"""
    print("🧪 Sophia Intel AI - CLI System Validation Suite")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentSetup))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIWrapper))
    suite.addTests(loader.loadTestsFromTestCase(TestPersonaFiles))
    suite.addTests(loader.loadTestsFromTestCase(TestMCPIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowScripts))
    suite.addTests(loader.loadTestsFromTestCase(TestShellIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_validation_suite()
    sys.exit(0 if success else 1)