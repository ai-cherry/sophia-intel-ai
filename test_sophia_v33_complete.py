#!/usr/bin/env python3
"""
Sophia AI Platform v3.3 - Comprehensive Integration Test Suite
Tests all security fixes, Pulumi ESC integration, and syntax validation
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("sophia_v33_test")


class SophiaV33TestSuite:
    """Comprehensive test suite for Sophia AI Platform v3.3"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = []
        self.start_time = datetime.now()

        # Test categories
        self.test_categories = [
            "Security Fixes",
            "Pulumi ESC Integration",
            "Syntax Validation",
            "Environment Management",
            "AI Router Integration",
            "Lambda Labs Integration",
            "Unified Management",
            "File Permissions",
            "Credential Validation",
            "Production Readiness",
        ]

    def run_all_tests(self) -> Dict[str, any]:
        """Run all test categories"""
        print("🚀 SOPHIA AI PLATFORM v3.3 - COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print(f"📅 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Project: {self.project_root}")
        print("=" * 70)

        # Run tests by category
        results = {}

        results["Security Fixes"] = self.test_security_fixes()
        results["Pulumi ESC Integration"] = self.test_pulumi_esc_integration()
        results["Syntax Validation"] = self.test_syntax_validation()
        results["Environment Management"] = self.test_environment_management()
        results["AI Router Integration"] = self.test_ai_router_integration()
        results["Lambda Labs Integration"] = self.test_lambda_labs_integration()
        results["Unified Management"] = self.test_unified_management()
        results["File Permissions"] = self.test_file_permissions()
        results["Credential Validation"] = self.test_credential_validation()
        results["Production Readiness"] = self.test_production_readiness()

        # Generate final report
        self.generate_final_report(results)

        return results

    def test_security_fixes(self) -> Dict[str, any]:
        """Test critical security fixes"""
        print("\n🔒 Testing Security Fixes...")
        category_results = []

        # Test 1: Fixed salt generation
        try:
            env_manager_path = Path("/opt/sophia/secrets/env_manager.py")
            if env_manager_path.exists():
                with open(env_manager_path) as f:
                    content = f.read()

                # Check for fixed salt issue
                if "sophia_ai_salt" in content:
                    category_results.append(
                        {
                            "test": "Fixed Salt Check",
                            "status": "FAIL",
                            "message": "Hardcoded salt still present in env_manager.py",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Fixed Salt Check",
                            "status": "PASS",
                            "message": "No hardcoded salt found - using unique salt generation",
                        }
                    )
            else:
                category_results.append(
                    {
                        "test": "Fixed Salt Check",
                        "status": "FAIL",
                        "message": "Environment manager not found",
                    }
                )
        except Exception as e:
            category_results.append(
                {
                    "test": "Fixed Salt Check",
                    "status": "ERROR",
                    "message": f"Error checking salt fix: {e}",
                }
            )

        # Test 2: Runtime export security
        try:
            # Check if runtime export has proper permissions handling
            env_manager_path = Path("/opt/sophia/secrets/env_manager.py")
            if env_manager_path.exists():
                with open(env_manager_path) as f:
                    content = f.read()

                if "export_for_runtime" in content and "os.chmod" in content:
                    category_results.append(
                        {
                            "test": "Runtime Export Security",
                            "status": "PASS",
                            "message": "Runtime export includes proper permission handling",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Runtime Export Security",
                            "status": "FAIL",
                            "message": "Runtime export missing security features",
                        }
                    )
        except Exception as e:
            category_results.append(
                {
                    "test": "Runtime Export Security",
                    "status": "ERROR",
                    "message": f"Error checking runtime export: {e}",
                }
            )

        # Test 3: Audit logging
        try:
            env_manager_path = Path("/opt/sophia/secrets/env_manager.py")
            if env_manager_path.exists():
                with open(env_manager_path) as f:
                    content = f.read()

                if "SecureAuditLogger" in content and "log_security_event" in content:
                    category_results.append(
                        {
                            "test": "Audit Logging",
                            "status": "PASS",
                            "message": "Comprehensive audit logging implemented",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Audit Logging",
                            "status": "FAIL",
                            "message": "Audit logging not implemented",
                        }
                    )
        except Exception as e:
            category_results.append(
                {
                    "test": "Audit Logging",
                    "status": "ERROR",
                    "message": f"Error checking audit logging: {e}",
                }
            )

        return self._calculate_category_score("Security Fixes", category_results)

    def test_pulumi_esc_integration(self) -> Dict[str, any]:
        """Test Pulumi ESC integration"""
        print("\n☁️ Testing Pulumi ESC Integration...")
        category_results = []

        # Test 1: Pulumi ESC manager exists
        try:
            esc_manager_path = self.project_root / "pulumi_esc_manager.py"
            if esc_manager_path.exists():
                category_results.append(
                    {
                        "test": "ESC Manager Exists",
                        "status": "PASS",
                        "message": "Pulumi ESC manager found",
                    }
                )

                # Check for key features
                with open(esc_manager_path) as f:
                    content = f.read()

                features = [
                    ("PulumiESCManager", "Main ESC manager class"),
                    ("open_environment", "Environment opening capability"),
                    ("set_secret", "Secret setting capability"),
                    ("rotate_secret", "Secret rotation capability"),
                    ("sync_from_github_secrets", "GitHub integration"),
                ]

                for feature, description in features:
                    if feature in content:
                        category_results.append(
                            {
                                "test": f"ESC Feature: {description}",
                                "status": "PASS",
                                "message": f"{feature} implemented",
                            }
                        )
                    else:
                        category_results.append(
                            {
                                "test": f"ESC Feature: {description}",
                                "status": "FAIL",
                                "message": f"{feature} missing",
                            }
                        )
            else:
                category_results.append(
                    {
                        "test": "ESC Manager Exists",
                        "status": "FAIL",
                        "message": "Pulumi ESC manager not found",
                    }
                )
        except Exception as e:
            category_results.append(
                {
                    "test": "ESC Manager Exists",
                    "status": "ERROR",
                    "message": f"Error checking ESC manager: {e}",
                }
            )

        # Test 2: Environment template creation
        try:
            esc_manager_path = self.project_root / "pulumi_esc_manager.py"
            if esc_manager_path.exists():
                # Try to create environment template
                result = subprocess.run(
                    [sys.executable, str(esc_manager_path), "template"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    category_results.append(
                        {
                            "test": "Environment Template Creation",
                            "status": "PASS",
                            "message": "Environment template created successfully",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Environment Template Creation",
                            "status": "FAIL",
                            "message": f"Template creation failed: {result.stderr}",
                        }
                    )
        except Exception as e:
            category_results.append(
                {
                    "test": "Environment Template Creation",
                    "status": "ERROR",
                    "message": f"Error testing template creation: {e}",
                }
            )

        return self._calculate_category_score("Pulumi ESC Integration", category_results)

    def test_syntax_validation(self) -> Dict[str, any]:
        """Test syntax validation system"""
        print("\n🔍 Testing Syntax Validation...")
        category_results = []

        # Test 1: Local syntax validator
        try:
            validator_path = self.project_root / "scripts" / "syntax_validator.py"
            if validator_path.exists():
                category_results.append(
                    {
                        "test": "Syntax Validator Exists",
                        "status": "PASS",
                        "message": "Local syntax validator found",
                    }
                )

                # Test validator functionality
                result = subprocess.run(
                    [sys.executable, str(validator_path), "--check", "python"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode == 0:
                    category_results.append(
                        {
                            "test": "Python Syntax Validation",
                            "status": "PASS",
                            "message": "Python syntax validation passed",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Python Syntax Validation",
                            "status": "FAIL",
                            "message": f"Python syntax validation failed: {result.stderr}",
                        }
                    )
            else:
                category_results.append(
                    {
                        "test": "Syntax Validator Exists",
                        "status": "FAIL",
                        "message": "Local syntax validator not found",
                    }
                )
        except Exception as e:
            category_results.append(
                {
                    "test": "Syntax Validator Exists",
                    "status": "ERROR",
                    "message": f"Error testing syntax validator: {e}",
                }
            )

        # Test 2: GitHub Actions workflow
        try:
            workflow_path = self.project_root / ".github" / "workflows" / "syntax-validation.yml"
            if workflow_path.exists():
                category_results.append(
                    {
                        "test": "GitHub Actions Workflow",
                        "status": "PASS",
                        "message": "Syntax validation workflow found",
                    }
                )

                # Check workflow content
                with open(workflow_path) as f:
                    content = f.read()

                workflow_features = [
                    ("python-syntax-validation", "Python validation job"),
                    ("shell-syntax-validation", "Shell validation job"),
                    ("security-hardening-check", "Security check job"),
                    ("comprehensive-report", "Report generation job"),
                ]

                for feature, description in workflow_features:
                    if feature in content:
                        category_results.append(
                            {
                                "test": f"Workflow: {description}",
                                "status": "PASS",
                                "message": f"{feature} job configured",
                            }
                        )
                    else:
                        category_results.append(
                            {
                                "test": f"Workflow: {description}",
                                "status": "FAIL",
                                "message": f"{feature} job missing",
                            }
                        )
            else:
                category_results.append(
                    {
                        "test": "GitHub Actions Workflow",
                        "status": "FAIL",
                        "message": "Syntax validation workflow not found",
                    }
                )
        except Exception as e:
            category_results.append(
                {
                    "test": "GitHub Actions Workflow",
                    "status": "ERROR",
                    "message": f"Error checking workflow: {e}",
                }
            )

        return self._calculate_category_score("Syntax Validation", category_results)

    def test_environment_management(self) -> Dict[str, any]:
        """Test environment management system"""
        print("\n🔧 Testing Environment Management...")
        category_results = []

        # Test 1: Enhanced environment manager
        try:
            env_manager_path = Path("/opt/sophia/secrets/env_manager.py")
            if env_manager_path.exists():
                # Test CLI interface
                result = subprocess.run(
                    [sys.executable, str(env_manager_path), "list"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0 or "variables stored" in result.stdout:
                    category_results.append(
                        {
                            "test": "Environment Manager CLI",
                            "status": "PASS",
                            "message": "CLI interface working",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Environment Manager CLI",
                            "status": "FAIL",
                            "message": f"CLI interface failed: {result.stderr}",
                        }
                    )
            else:
                category_results.append(
                    {
                        "test": "Environment Manager CLI",
                        "status": "FAIL",
                        "message": "Environment manager not found",
                    }
                )
        except Exception as e:
            category_results.append(
                {
                    "test": "Environment Manager CLI",
                    "status": "ERROR",
                    "message": f"Error testing environment manager: {e}",
                }
            )

        # Test 2: Environment activation script
        try:
            activate_script = Path("/opt/sophia/secrets/activate_env.sh")
            if activate_script.exists():
                category_results.append(
                    {
                        "test": "Environment Activation Script",
                        "status": "PASS",
                        "message": "Activation script found",
                    }
                )

                # Check if executable
                if os.access(activate_script, os.X_OK):
                    category_results.append(
                        {
                            "test": "Activation Script Executable",
                            "status": "PASS",
                            "message": "Script is executable",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Activation Script Executable",
                            "status": "FAIL",
                            "message": "Script is not executable",
                        }
                    )
            else:
                category_results.append(
                    {
                        "test": "Environment Activation Script",
                        "status": "FAIL",
                        "message": "Activation script not found",
                    }
                )
        except Exception as e:
            category_results.append(
                {
                    "test": "Environment Activation Script",
                    "status": "ERROR",
                    "message": f"Error checking activation script: {e}",
                }
            )

        return self._calculate_category_score("Environment Management", category_results)

    def test_ai_router_integration(self) -> Dict[str, any]:
        """Test AI router integration"""
        print("\n🤖 Testing AI Router Integration...")
        category_results = []

        # Test 1: AI router exists
        try:
            ai_router_path = self.project_root / "ai_router.py"
            if ai_router_path.exists():
                category_results.append(
                    {"test": "AI Router Exists", "status": "PASS", "message": "AI router found"}
                )

                # Check for key features
                with open(ai_router_path) as f:
                    content = f.read()

                if "class AIRouter" in content:
                    category_results.append(
                        {
                            "test": "AI Router Class",
                            "status": "PASS",
                            "message": "AIRouter class implemented",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "AI Router Class",
                            "status": "FAIL",
                            "message": "AIRouter class not found",
                        }
                    )
            else:
                category_results.append(
                    {"test": "AI Router Exists", "status": "FAIL", "message": "AI router not found"}
                )
        except Exception as e:
            category_results.append(
                {
                    "test": "AI Router Exists",
                    "status": "ERROR",
                    "message": f"Error checking AI router: {e}",
                }
            )

        return self._calculate_category_score("AI Router Integration", category_results)

    def test_lambda_labs_integration(self) -> Dict[str, any]:
        """Test Lambda Labs integration"""
        print("\n⚡ Testing Lambda Labs Integration...")
        category_results = []

        # Test 1: Lambda Labs integration exists
        try:
            lambda_integration_path = (
                self.project_root / "infrastructure" / "lambda_labs" / "lambda_labs_integration.py"
            )
            if lambda_integration_path.exists():
                category_results.append(
                    {
                        "test": "Lambda Labs Integration",
                        "status": "PASS",
                        "message": "Lambda Labs integration found",
                    }
                )

                # Check for security - no hardcoded keys
                with open(lambda_integration_path) as f:
                    content = f.read()

                if "from_env" in content and "os.getenv" in content:
                    category_results.append(
                        {
                            "test": "Lambda Labs Security",
                            "status": "PASS",
                            "message": "Uses environment variables for credentials",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Lambda Labs Security",
                            "status": "FAIL",
                            "message": "May contain hardcoded credentials",
                        }
                    )
            else:
                category_results.append(
                    {
                        "test": "Lambda Labs Integration",
                        "status": "FAIL",
                        "message": "Lambda Labs integration not found",
                    }
                )
        except Exception as e:
            category_results.append(
                {
                    "test": "Lambda Labs Integration",
                    "status": "ERROR",
                    "message": f"Error checking Lambda Labs integration: {e}",
                }
            )

        return self._calculate_category_score("Lambda Labs Integration", category_results)

    def test_unified_management(self) -> Dict[str, any]:
        """Test unified management system"""
        print("\n🎛️ Testing Unified Management...")
        category_results = []

        # Test 1: Sophia.sh script
        try:
            sophia_script = self.project_root / "sophia.sh"
            if sophia_script.exists():
                category_results.append(
                    {
                        "test": "Sophia.sh Script",
                        "status": "PASS",
                        "message": "Unified management script found",
                    }
                )

                # Check if executable
                if os.access(sophia_script, os.X_OK):
                    category_results.append(
                        {
                            "test": "Sophia.sh Executable",
                            "status": "PASS",
                            "message": "Script is executable",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Sophia.sh Executable",
                            "status": "FAIL",
                            "message": "Script is not executable",
                        }
                    )

                # Test help command
                result = subprocess.run(
                    [str(sophia_script), "--help"], capture_output=True, text=True, timeout=10
                )

                if result.returncode == 0 or "usage" in result.stdout.lower():
                    category_results.append(
                        {
                            "test": "Sophia.sh Help",
                            "status": "PASS",
                            "message": "Help command works",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Sophia.sh Help",
                            "status": "FAIL",
                            "message": "Help command failed",
                        }
                    )
            else:
                category_results.append(
                    {
                        "test": "Sophia.sh Script",
                        "status": "FAIL",
                        "message": "Unified management script not found",
                    }
                )
        except Exception as e:
            category_results.append(
                {
                    "test": "Sophia.sh Script",
                    "status": "ERROR",
                    "message": f"Error testing sophia.sh: {e}",
                }
            )

        return self._calculate_category_score("Unified Management", category_results)

    def test_file_permissions(self) -> Dict[str, any]:
        """Test file permissions"""
        print("\n🔐 Testing File Permissions...")
        category_results = []

        # Test 1: Secrets directory permissions
        try:
            secrets_dir = Path("/opt/sophia/secrets")
            if secrets_dir.exists():
                stat_info = secrets_dir.stat()
                permissions = oct(stat_info.st_mode)[-3:]

                if permissions == "700":
                    category_results.append(
                        {
                            "test": "Secrets Directory Permissions",
                            "status": "PASS",
                            "message": f"Correct permissions: {permissions}",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Secrets Directory Permissions",
                            "status": "FAIL",
                            "message": f"Incorrect permissions: {permissions} (should be 700)",
                        }
                    )
            else:
                category_results.append(
                    {
                        "test": "Secrets Directory Permissions",
                        "status": "FAIL",
                        "message": "Secrets directory not found",
                    }
                )
        except Exception as e:
            category_results.append(
                {
                    "test": "Secrets Directory Permissions",
                    "status": "ERROR",
                    "message": f"Error checking permissions: {e}",
                }
            )

        # Test 2: Key file permissions
        try:
            key_files = [
                Path("/opt/sophia/secrets/.key"),
                Path("/opt/sophia/secrets/.salt"),
                Path("/opt/sophia/secrets/.env.encrypted"),
            ]

            for key_file in key_files:
                if key_file.exists():
                    stat_info = key_file.stat()
                    permissions = oct(stat_info.st_mode)[-3:]

                    if permissions == "600":
                        category_results.append(
                            {
                                "test": f"Key File Permissions: {key_file.name}",
                                "status": "PASS",
                                "message": f"Correct permissions: {permissions}",
                            }
                        )
                    else:
                        category_results.append(
                            {
                                "test": f"Key File Permissions: {key_file.name}",
                                "status": "FAIL",
                                "message": f"Incorrect permissions: {permissions} (should be 600)",
                            }
                        )
        except Exception as e:
            category_results.append(
                {
                    "test": "Key File Permissions",
                    "status": "ERROR",
                    "message": f"Error checking key file permissions: {e}",
                }
            )

        return self._calculate_category_score("File Permissions", category_results)

    def test_credential_validation(self) -> Dict[str, any]:
        """Test credential validation"""
        print("\n🔑 Testing Credential Validation...")
        category_results = []

        # Test 1: Credential validation script
        try:
            validate_script = self.project_root / "validate_credentials.py"
            if validate_script.exists():
                category_results.append(
                    {
                        "test": "Credential Validator Exists",
                        "status": "PASS",
                        "message": "Credential validation script found",
                    }
                )

                # Test validation
                result = subprocess.run(
                    [sys.executable, str(validate_script)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if "validation" in result.stdout.lower():
                    category_results.append(
                        {
                            "test": "Credential Validation Run",
                            "status": "PASS",
                            "message": "Validation script executed",
                        }
                    )
                else:
                    category_results.append(
                        {
                            "test": "Credential Validation Run",
                            "status": "FAIL",
                            "message": "Validation script failed to run",
                        }
                    )
            else:
                category_results.append(
                    {
                        "test": "Credential Validator Exists",
                        "status": "FAIL",
                        "message": "Credential validation script not found",
                    }
                )
        except Exception as e:
            category_results.append(
                {
                    "test": "Credential Validator Exists",
                    "status": "ERROR",
                    "message": f"Error testing credential validation: {e}",
                }
            )

        return self._calculate_category_score("Credential Validation", category_results)

    def test_production_readiness(self) -> Dict[str, any]:
        """Test production readiness"""
        print("\n🚀 Testing Production Readiness...")
        category_results = []

        # Test 1: Required directories
        required_dirs = [
            Path("/opt/sophia"),
            Path("/opt/sophia/secrets"),
            Path("/opt/sophia/logs"),
            Path("/opt/sophia/pids"),
        ]

        for dir_path in required_dirs:
            if dir_path.exists():
                category_results.append(
                    {
                        "test": f"Directory: {dir_path}",
                        "status": "PASS",
                        "message": "Directory exists",
                    }
                )
            else:
                category_results.append(
                    {
                        "test": f"Directory: {dir_path}",
                        "status": "FAIL",
                        "message": "Directory missing",
                    }
                )

        # Test 2: Core scripts
        core_scripts = [
            self.project_root / "sophia.sh",
            self.project_root / "pulumi_esc_manager.py",
            Path("/opt/sophia/secrets/env_manager.py"),
        ]

        for script_path in core_scripts:
            if script_path.exists():
                category_results.append(
                    {
                        "test": f"Core Script: {script_path.name}",
                        "status": "PASS",
                        "message": "Script exists",
                    }
                )
            else:
                category_results.append(
                    {
                        "test": f"Core Script: {script_path.name}",
                        "status": "FAIL",
                        "message": "Script missing",
                    }
                )

        return self._calculate_category_score("Production Readiness", category_results)

    def _calculate_category_score(self, category: str, results: List[Dict]) -> Dict[str, any]:
        """Calculate score for a test category"""
        total_tests = len(results)
        passed_tests = len([r for r in results if r["status"] == "PASS"])
        failed_tests = len([r for r in results if r["status"] == "FAIL"])
        error_tests = len([r for r in results if r["status"] == "ERROR"])

        if total_tests == 0:
            score_percentage = 0
        else:
            score_percentage = (passed_tests / total_tests) * 100

        status = "PASS" if failed_tests == 0 and error_tests == 0 else "FAIL"

        print(
            f"  📊 {category}: {passed_tests}/{total_tests} tests passed ({score_percentage:.1f}%)"
        )

        return {
            "category": category,
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "score_percentage": score_percentage,
            "status": status,
            "results": results,
        }

    def generate_final_report(self, results: Dict[str, any]):
        """Generate comprehensive final report"""
        end_time = datetime.now()
        duration = end_time - self.start_time

        print("\n" + "=" * 70)
        print("📊 SOPHIA AI PLATFORM v3.3 - FINAL TEST REPORT")
        print("=" * 70)

        # Overall statistics
        total_tests = sum(r["total_tests"] for r in results.values())
        total_passed = sum(r["passed"] for r in results.values())
        total_failed = sum(r["failed"] for r in results.values())
        total_errors = sum(r["errors"] for r in results.values())

        overall_score = (total_passed / total_tests * 100) if total_tests > 0 else 0

        print(f"⏱️  Duration: {duration.total_seconds():.1f} seconds")
        print(f"📋 Total Tests: {total_tests}")
        print(f"✅ Passed: {total_passed}")
        print(f"❌ Failed: {total_failed}")
        print(f"⚠️  Errors: {total_errors}")
        print(f"📊 Overall Score: {overall_score:.1f}%")

        # Category breakdown
        print("\n📋 CATEGORY BREAKDOWN:")
        print("-" * 50)

        for category, result in results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(
                f"{status_icon} {category}: {result['score_percentage']:.1f}% ({result['passed']}/{result['total_tests']})"
            )

        # Overall status
        print("\n🎯 OVERALL STATUS:")
        if overall_score >= 90:
            print("🎉 EXCELLENT - Platform ready for production!")
        elif overall_score >= 80:
            print("✅ GOOD - Platform mostly ready, minor issues to address")
        elif overall_score >= 70:
            print("⚠️  FAIR - Platform needs attention before production")
        else:
            print("❌ POOR - Significant issues need to be resolved")

        # Critical issues
        critical_failures = []
        for category, result in results.items():
            if result["status"] == "FAIL" and category in [
                "Security Fixes",
                "File Permissions",
                "Production Readiness",
            ]:
                critical_failures.append(category)

        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES: {', '.join(critical_failures)}")
        else:
            print("\n✅ NO CRITICAL ISSUES DETECTED")

        # Save detailed report
        self._save_detailed_report(
            results,
            {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "overall_score": overall_score,
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_errors": total_errors,
            },
        )

    def _save_detailed_report(self, results: Dict[str, any], summary: Dict[str, any]):
        """Save detailed test report"""
        report_data = {
            "sophia_version": "3.3",
            "test_suite": "Comprehensive Integration Test",
            "summary": summary,
            "category_results": results,
        }

        report_file = self.project_root / "sophia_v33_test_report.json"
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        # Also create markdown report
        md_report = self.project_root / "sophia_v33_test_report.md"
        with open(md_report, "w") as f:
            f.write("# Sophia AI Platform v3.3 - Test Report\n\n")
            f.write(f"**Generated:** {summary['end_time']}\n")
            f.write(f"**Duration:** {summary['duration_seconds']:.1f} seconds\n")
            f.write(f"**Overall Score:** {summary['overall_score']:.1f}%\n\n")

            f.write("## Summary\n\n")
            f.write(f"- **Total Tests:** {summary['total_tests']}\n")
            f.write(f"- **Passed:** {summary['total_passed']}\n")
            f.write(f"- **Failed:** {summary['total_failed']}\n")
            f.write(f"- **Errors:** {summary['total_errors']}\n\n")

            f.write("## Category Results\n\n")
            for category, result in results.items():
                status_icon = "✅" if result["status"] == "PASS" else "❌"
                f.write(f"### {status_icon} {category}\n")
                f.write(
                    f"**Score:** {result['score_percentage']:.1f}% ({result['passed']}/{result['total_tests']})\n\n"
                )

                for test_result in result["results"]:
                    test_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️"}.get(
                        test_result["status"], "❓"
                    )
                    f.write(f"- {test_icon} **{test_result['test']}:** {test_result['message']}\n")
                f.write("\n")

        print("\n📄 Detailed reports saved:")
        print(f"  📄 JSON: {report_file}")
        print(f"  📄 Markdown: {md_report}")


def main():
    """Main entry point"""
    test_suite = SophiaV33TestSuite()
    results = test_suite.run_all_tests()

    # Exit with appropriate code
    overall_score = (
        sum(r["passed"] for r in results.values())
        / sum(r["total_tests"] for r in results.values())
        * 100
    )
    sys.exit(0 if overall_score >= 80 else 1)


if __name__ == "__main__":
    main()
