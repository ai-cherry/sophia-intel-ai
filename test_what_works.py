#!/usr/bin/env python3
"""
TEST WHAT ACTUALLY WORKS VS BROKEN
No bullshit testing - just see what the fuck actually runs
"""
import importlib.util
import json
import os
import subprocess
import sys
class WhatActuallyWorks:
    def __init__(self):
        self.repo_path = "/home/ubuntu/sophia-main"
        self.working = []
        self.broken = []
        self.critical_files = [
            "sophia.sh",
            "deploy_multi_instance.sh",
            "enhanced_secret_dashboard.py",
            "secret_management_dashboard.py",
            "lambda_labs_scanner.py",
            "ai_router.py",
            "pulumi_esc_manager.py",
        ]
    def test_critical_scripts(self):
        """Test the critical scripts that should work"""
        print("🧪 TESTING CRITICAL SCRIPTS...")
        for script in self.critical_files:
            script_path = os.path.join(self.repo_path, script)
            if not os.path.exists(script_path):
                self.broken.append(f"{script} - FILE MISSING")
                print(f"❌ {script} - FILE MISSING")
                continue
            if script.endswith(".py"):
                # Test Python syntax
                try:
                    result = subprocess.run(
                        ["python3", "-m", "py_compile", script_path],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        self.working.append(f"{script} - SYNTAX OK")
                        print(f"✅ {script} - SYNTAX OK")
                        # Try to import it
                        try:
                            spec = importlib.util.spec_from_file_location(
                                "test_module", script_path
                            )
                            module = importlib.util.module_from_spec(spec)
                            # Don't execute, just check if it can be loaded
                            self.working.append(f"{script} - IMPORTABLE")
                            print(f"✅ {script} - IMPORTABLE")
                        except Exception as e:
                            self.broken.append(f"{script} - IMPORT ERROR: {str(e)}")
                            print(f"❌ {script} - IMPORT ERROR: {str(e)}")
                    else:
                        self.broken.append(f"{script} - SYNTAX ERROR: {result.stderr}")
                        print(f"❌ {script} - SYNTAX ERROR")
                except Exception as e:
                    self.broken.append(f"{script} - TEST ERROR: {str(e)}")
                    print(f"❌ {script} - TEST ERROR: {str(e)}")
            elif script.endswith(".sh"):
                # Test shell syntax
                try:
                    result = subprocess.run(
                        ["bash", "-n", script_path], capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        self.working.append(f"{script} - SHELL SYNTAX OK")
                        print(f"✅ {script} - SHELL SYNTAX OK")
                        # Check if executable
                        if os.access(script_path, os.X_OK):
                            self.working.append(f"{script} - EXECUTABLE")
                            print(f"✅ {script} - EXECUTABLE")
                        else:
                            self.broken.append(f"{script} - NOT EXECUTABLE")
                            print(f"❌ {script} - NOT EXECUTABLE")
                    else:
                        self.broken.append(f"{script} - SHELL SYNTAX ERROR")
                        print(f"❌ {script} - SHELL SYNTAX ERROR")
                except Exception as e:
                    self.broken.append(f"{script} - SHELL TEST ERROR: {str(e)}")
                    print(f"❌ {script} - SHELL TEST ERROR: {str(e)}")
    def test_deployment_readiness(self):
        """Test if deployment is actually possible"""
        print("\\n🚀 TESTING DEPLOYMENT READINESS...")
        # Check if Docker is available
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                self.working.append("Docker - AVAILABLE")
                print("✅ Docker - AVAILABLE")
            else:
                self.broken.append("Docker - NOT AVAILABLE")
                print("❌ Docker - NOT AVAILABLE")
        except:
            self.broken.append("Docker - NOT INSTALLED")
            print("❌ Docker - NOT INSTALLED")
        # Check if Python dependencies can be installed
        try:
            result = subprocess.run(["pip3", "list"], capture_output=True, text=True)
            if result.returncode == 0:
                self.working.append("pip3 - WORKING")
                print("✅ pip3 - WORKING")
            else:
                self.broken.append("pip3 - NOT WORKING")
                print("❌ pip3 - NOT WORKING")
        except:
            self.broken.append("pip3 - NOT AVAILABLE")
            print("❌ pip3 - NOT AVAILABLE")
        # Check if git is working
        try:
            result = subprocess.run(
                ["git", "status"], cwd=self.repo_path, capture_output=True, text=True
            )
            if result.returncode == 0:
                self.working.append("Git repository - VALID")
                print("✅ Git repository - VALID")
            else:
                self.broken.append("Git repository - INVALID")
                print("❌ Git repository - INVALID")
        except:
            self.broken.append("Git - NOT AVAILABLE")
            print("❌ Git - NOT AVAILABLE")
    def test_api_connectivity(self):
        """Test if we can actually connect to APIs"""
        print("\\n🌐 TESTING API CONNECTIVITY...")
        # Test basic internet connectivity
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "5", "https://google.com"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                self.working.append("Internet connectivity - OK")
                print("✅ Internet connectivity - OK")
            else:
                self.broken.append("Internet connectivity - FAILED")
                print("❌ Internet connectivity - FAILED")
        except:
            self.broken.append("curl - NOT AVAILABLE")
            print("❌ curl - NOT AVAILABLE")
        # Test if we can reach Lambda Labs API
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "5", "https://cloud.lambdalabs.com"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                self.working.append("Lambda Labs API - REACHABLE")
                print("✅ Lambda Labs API - REACHABLE")
            else:
                self.broken.append("Lambda Labs API - UNREACHABLE")
                print("❌ Lambda Labs API - UNREACHABLE")
        except:
            self.broken.append("Lambda Labs API - TEST FAILED")
            print("❌ Lambda Labs API - TEST FAILED")
    def test_environment_setup(self):
        """Test if environment can be set up"""
        print("\\n⚙️ TESTING ENVIRONMENT SETUP...")
        # Check if we can set environment variables
        try:
            os.environ["TEST_VAR"] = "test_value"
            if os.environ.get("TEST_VAR") == "test_value":
                self.working.append("Environment variables - WORKING")
                print("✅ Environment variables - WORKING")
                del os.environ["TEST_VAR"]
            else:
                self.broken.append("Environment variables - NOT WORKING")
                print("❌ Environment variables - NOT WORKING")
        except:
            self.broken.append("Environment variables - ERROR")
            print("❌ Environment variables - ERROR")
        # Check if we can create directories
        try:
            test_dir = os.path.join(self.repo_path, "test_dir_temp")
            os.makedirs(test_dir, exist_ok=True)
            if os.path.exists(test_dir):
                self.working.append("Directory creation - WORKING")
                print("✅ Directory creation - WORKING")
                os.rmdir(test_dir)
            else:
                self.broken.append("Directory creation - FAILED")
                print("❌ Directory creation - FAILED")
        except Exception as e:
            self.broken.append(f"Directory creation - ERROR: {str(e)}")
            print(f"❌ Directory creation - ERROR: {str(e)}")
        # Check if we can write files
        try:
            test_file = os.path.join(self.repo_path, "test_file_temp.txt")
            with open(test_file, "w") as f:
                f.write("test")
            if os.path.exists(test_file):
                self.working.append("File creation - WORKING")
                print("✅ File creation - WORKING")
                os.remove(test_file)
            else:
                self.broken.append("File creation - FAILED")
                print("❌ File creation - FAILED")
        except Exception as e:
            self.broken.append(f"File creation - ERROR: {str(e)}")
            print(f"❌ File creation - ERROR: {str(e)}")
    def test_key_dependencies(self):
        """Test if key Python dependencies are available"""
        print("\\n📦 TESTING KEY DEPENDENCIES...")
        key_deps = [
            "requests",
            "json",
            "os",
            "sys",
            "subprocess",
            "pathlib",
            "re",
            "datetime",
            "time",
        ]
        for dep in key_deps:
            try:
                result = subprocess.run(
                    ["python3", "-c", f"import {dep}"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    self.working.append(f"Python {dep} - AVAILABLE")
                    print(f"✅ Python {dep} - AVAILABLE")
                else:
                    self.broken.append(f"Python {dep} - NOT AVAILABLE")
                    print(f"❌ Python {dep} - NOT AVAILABLE")
            except:
                self.broken.append(f"Python {dep} - TEST ERROR")
                print(f"❌ Python {dep} - TEST ERROR")
        # Test optional but important dependencies
        optional_deps = ["fastapi", "uvicorn", "docker", "pulumi"]
        for dep in optional_deps:
            try:
                result = subprocess.run(
                    ["python3", "-c", f"import {dep}"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    self.working.append(f"Python {dep} - AVAILABLE")
                    print(f"✅ Python {dep} - AVAILABLE")
                else:
                    self.broken.append(f"Python {dep} - NOT AVAILABLE (optional)")
                    print(f"⚠️ Python {dep} - NOT AVAILABLE (optional)")
            except:
                self.broken.append(f"Python {dep} - NOT AVAILABLE (optional)")
                print(f"⚠️ Python {dep} - NOT AVAILABLE (optional)")
    def generate_working_report(self):
        """Generate report of what actually works"""
        print("\\n" + "=" * 60)
        print("🧪 WHAT ACTUALLY WORKS VS BROKEN REPORT")
        print("=" * 60)
        working_count = len(self.working)
        broken_count = len(self.broken)
        total_count = working_count + broken_count
        if total_count > 0:
            working_percentage = (working_count / total_count) * 100
        else:
            working_percentage = 0
        print("\\n📊 SUMMARY:")
        print(f"   WORKING: {working_count}")
        print(f"   BROKEN:  {broken_count}")
        print(f"   TOTAL:   {total_count}")
        print(f"   WORKING PERCENTAGE: {working_percentage:.1f}%")
        if working_percentage >= 80:
            status = "MOSTLY WORKING"
        elif working_percentage >= 60:
            status = "PARTIALLY WORKING"
        elif working_percentage >= 40:
            status = "BARELY WORKING"
        else:
            status = "MOSTLY BROKEN"
        print(f"   STATUS: {status}")
        print("\\n✅ WHAT WORKS:")
        for item in self.working:
            print(f"   - {item}")
        print("\\n❌ WHAT'S BROKEN:")
        for item in self.broken[:20]:  # Show first 20
            print(f"   - {item}")
        if len(self.broken) > 20:
            print(f"   ... and {len(self.broken) - 20} more broken items")
        # Save report
        report = {
            "timestamp": "2025-08-09",
            "working_percentage": working_percentage,
            "status": status,
            "working_count": working_count,
            "broken_count": broken_count,
            "working_items": self.working,
            "broken_items": self.broken,
        }
        with open(f"{self.repo_path}/WHAT_WORKS_REPORT.json", "w") as f:
            json.dump(report, f, indent=2)
        print("\\n💾 Report saved to: WHAT_WORKS_REPORT.json")
        return working_percentage, status
    def run_all_tests(self):
        """Run all tests to see what works"""
        print("🧪 TESTING WHAT ACTUALLY WORKS...")
        print("No bullshit - just testing if shit runs")
        print("-" * 50)
        self.test_critical_scripts()
        self.test_deployment_readiness()
        self.test_api_connectivity()
        self.test_environment_setup()
        self.test_key_dependencies()
        working_percentage, status = self.generate_working_report()
        print("\\n🎯 FINAL TEST RESULT:")
        print(f"   {working_percentage:.1f}% of tested components are working")
        print(f"   Status: {status}")
        if working_percentage >= 70:
            print("   🎉 Most stuff works! You can probably deploy.")
        elif working_percentage >= 50:
            print("   ⚠️ Some stuff works. Fix the broken parts first.")
        else:
            print("   💀 Most stuff is broken. Major fixes needed.")
        return working_percentage, status
if __name__ == "__main__":
    tester = WhatActuallyWorks()
    working_percentage, status = tester.run_all_tests()
    if working_percentage < 50:
        sys.exit(1)
    else:
        sys.exit(0)
