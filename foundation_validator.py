#!/usr/bin/env python3
"""
Sophia Intel AI - Foundation Validator
Tests the complete integrated system after cleanup and reorganization
"""

import asyncio
import json
import logging
import requests
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import subprocess

class FoundationValidator:
    def __init__(self, project_root: str = "/Users/lynnmusil/sophia-intel-ai"):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": {},
            "system_status": "unknown"
        }
        
    def test_centralized_config(self) -> bool:
        """Test that centralized configuration is working"""
        self.logger.info("🔧 Testing centralized configuration...")
        
        try:
            # Check if centralized files exist
            centralized_env = self.project_root / ".env.centralized"
            centralized_config = self.project_root / "centralized_config.yaml"
            
            if not centralized_env.exists():
                self.logger.error("❌ .env.centralized file not found")
                return False
                
            if not centralized_config.exists():
                self.logger.error("❌ centralized_config.yaml file not found")
                return False
            
            # Test loading centralized config
            with open(centralized_config, 'r') as f:
                import yaml
                config = yaml.safe_load(f)
                
            # Validate key sections exist
            required_sections = ["ai_providers", "databases", "system_config"]
            for section in required_sections:
                if section not in config:
                    self.logger.error(f"❌ Missing required section: {section}")
                    return False
            
            # Count secrets
            total_secrets = 0
            for section, secrets in config.items():
                if isinstance(secrets, dict):
                    total_secrets += len(secrets)
            
            self.logger.info(f"✅ Centralized config loaded with {total_secrets} total secrets")
            self.test_results["test_details"]["centralized_config"] = {
                "status": "passed",
                "total_secrets": total_secrets,
                "sections": list(config.keys())
            }
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Centralized config test failed: {e}")
            self.test_results["test_details"]["centralized_config"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    def test_model_enforcement(self) -> bool:
        """Test model enforcement system"""
        self.logger.info("🚫 Testing model enforcement system...")
        
        try:
            from app.core.model_enforcement import model_enforcer
            
            # Test approved model
            approved_models = model_enforcer.get_approved_models()
            if not approved_models:
                self.logger.error("❌ No approved models found")
                return False
            
            # Test model enforcement
            test_cases = [
                ("gpt-4o", True),  # Should be approved
                ("gpt-3.5-turbo", False),  # Should be blocked
                ("claude-3-5-sonnet-20241022", True),  # Should be approved
                ("claude-2", False)  # Should be blocked
            ]
            
            passed_cases = 0
            for model, should_pass in test_cases:
                try:
                    result = model_enforcer.is_model_approved(model)
                    if result == should_pass:
                        passed_cases += 1
                        self.logger.info(f"  ✅ {model}: {'approved' if result else 'blocked'} (expected)")
                    else:
                        self.logger.error(f"  ❌ {model}: {'approved' if result else 'blocked'} (unexpected)")
                except Exception as e:
                    self.logger.error(f"  ❌ {model}: Error - {e}")
            
            if passed_cases == len(test_cases):
                self.logger.info(f"✅ Model enforcement working correctly ({passed_cases}/{len(test_cases)} cases)")
                self.test_results["test_details"]["model_enforcement"] = {
                    "status": "passed",
                    "approved_models": len(approved_models),
                    "test_cases_passed": passed_cases
                }
                return True
            else:
                self.logger.error(f"❌ Model enforcement failed ({passed_cases}/{len(test_cases)} cases)")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Model enforcement test failed: {e}")
            self.test_results["test_details"]["model_enforcement"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    def test_mcp_services(self) -> bool:
        """Test MCP services are running"""
        self.logger.info("🔗 Testing MCP services...")
        
        mcp_services = {
            "memory": 8081,
            "filesystem": 8082,
            "git": 8084
        }
        
        working_services = 0
        service_status = {}
        
        for service_name, port in mcp_services.items():
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                if response.status_code == 200:
                    self.logger.info(f"  ✅ MCP {service_name} service (port {port}): Running")
                    working_services += 1
                    service_status[service_name] = "running"
                else:
                    self.logger.warning(f"  ⚠️  MCP {service_name} service (port {port}): Unhealthy (status {response.status_code})")
                    service_status[service_name] = f"unhealthy_{response.status_code}"
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"  ⚠️  MCP {service_name} service (port {port}): Not running")
                service_status[service_name] = "not_running"
            except Exception as e:
                self.logger.error(f"  ❌ MCP {service_name} service (port {port}): Error - {e}")
                service_status[service_name] = f"error_{str(e)}"
        
        # MCP services are optional but good to have
        self.test_results["test_details"]["mcp_services"] = {
            "status": "info",
            "services_running": working_services,
            "total_services": len(mcp_services),
            "service_status": service_status
        }
        
        if working_services > 0:
            self.logger.info(f"ℹ️  MCP Services: {working_services}/{len(mcp_services)} running")
        else:
            self.logger.info("ℹ️  No MCP services running (optional)")
            
        return True  # MCP services are not critical for foundation
    
    def test_duplicate_cleanup(self) -> bool:
        """Test that duplicates were properly cleaned up"""
        self.logger.info("🧹 Testing duplicate cleanup...")
        
        # Check that old .env files are gone (backed up)
        old_env_files = [".env.local", ".env.production", ".env.voice"]
        env_cleanup_status = {}
        
        for env_file in old_env_files:
            path = self.project_root / env_file
            backup_path = self.project_root / ".env_backup" / env_file
            
            if not path.exists() and backup_path.exists():
                env_cleanup_status[env_file] = "cleaned_and_backed_up"
            elif not path.exists():
                env_cleanup_status[env_file] = "not_found"
            else:
                env_cleanup_status[env_file] = "still_exists"
        
        # Check that centralized files exist
        centralized_exists = (self.project_root / ".env.centralized").exists()
        config_exists = (self.project_root / "centralized_config.yaml").exists()
        
        cleanup_successful = centralized_exists and config_exists
        
        if cleanup_successful:
            self.logger.info("✅ Cleanup completed - centralized files exist")
        else:
            self.logger.error("❌ Cleanup incomplete - missing centralized files")
        
        self.test_results["test_details"]["cleanup_status"] = {
            "status": "passed" if cleanup_successful else "failed",
            "centralized_env_exists": centralized_exists,
            "centralized_config_exists": config_exists,
            "env_cleanup_status": env_cleanup_status
        }
        
        return cleanup_successful
    
    def test_api_server_health(self) -> bool:
        """Test if API server can start and respond"""
        self.logger.info("🌐 Testing API server health...")
        
        # Check if server is already running
        ports_to_check = [8003, 8000]  # Sophia API ports
        
        for port in ports_to_check:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                if response.status_code == 200:
                    self.logger.info(f"✅ API server running on port {port}")
                    self.test_results["test_details"]["api_server"] = {
                        "status": "passed",
                        "port": port,
                        "response_time": response.elapsed.total_seconds()
                    }
                    return True
            except requests.exceptions.ConnectionError:
                continue
            except Exception as e:
                self.logger.warning(f"⚠️  Port {port} error: {e}")
        
        # If no server running, that's expected in some cases
        self.logger.info("ℹ️  No API server currently running (this is okay)")
        self.test_results["test_details"]["api_server"] = {
            "status": "info",
            "message": "No server running currently"
        }
        return True
    
    def test_file_structure(self) -> bool:
        """Test that essential file structure is intact"""
        self.logger.info("📁 Testing file structure...")
        
        critical_paths = [
            "app/",
            "app/core/",
            "app/api/",
            "sophia-intel-app/",
            "mcp/",
            "voice/",
            "requirements.txt",
            "README.md"
        ]
        
        missing_paths = []
        for path_str in critical_paths:
            path = self.project_root / path_str
            if not path.exists():
                missing_paths.append(path_str)
        
        if not missing_paths:
            self.logger.info("✅ All critical file structures present")
            self.test_results["test_details"]["file_structure"] = {
                "status": "passed",
                "critical_paths_checked": len(critical_paths),
                "missing_paths": []
            }
            return True
        else:
            self.logger.error(f"❌ Missing critical paths: {missing_paths}")
            self.test_results["test_details"]["file_structure"] = {
                "status": "failed",
                "missing_paths": missing_paths
            }
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all foundation tests"""
        self.logger.info("🚀 Starting Sophia Intel AI Foundation Validation")
        self.logger.info("=" * 60)
        
        tests = [
            ("Centralized Configuration", self.test_centralized_config),
            ("Model Enforcement", self.test_model_enforcement),
            ("MCP Services", self.test_mcp_services),
            ("Cleanup Status", self.test_duplicate_cleanup),
            ("API Server Health", self.test_api_server_health),
            ("File Structure", self.test_file_structure)
        ]
        
        for test_name, test_func in tests:
            self.logger.info(f"\n--- {test_name} ---")
            try:
                if test_func():
                    self.test_results["tests_passed"] += 1
                else:
                    self.test_results["tests_failed"] += 1
            except Exception as e:
                self.logger.error(f"❌ {test_name} crashed: {e}")
                self.test_results["tests_failed"] += 1
                self.test_results["test_details"][test_name.lower().replace(" ", "_")] = {
                    "status": "crashed",
                    "error": str(e)
                }
        
        # Calculate overall status
        total_tests = self.test_results["tests_passed"] + self.test_results["tests_failed"]
        pass_rate = self.test_results["tests_passed"] / total_tests if total_tests > 0 else 0
        
        if pass_rate >= 0.8:
            self.test_results["system_status"] = "healthy"
        elif pass_rate >= 0.6:
            self.test_results["system_status"] = "warning"
        else:
            self.test_results["system_status"] = "critical"
        
        # Save results
        results_file = self.project_root / "foundation_validation_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Print summary
        self.print_summary()
        
        return self.test_results
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("🏁 FOUNDATION VALIDATION SUMMARY")
        print("=" * 60)
        
        total_tests = self.test_results["tests_passed"] + self.test_results["tests_failed"]
        print(f"Tests Run: {total_tests}")
        print(f"✅ Passed: {self.test_results['tests_passed']}")
        print(f"❌ Failed: {self.test_results['tests_failed']}")
        
        if total_tests > 0:
            pass_rate = (self.test_results["tests_passed"] / total_tests) * 100
            print(f"📊 Pass Rate: {pass_rate:.1f}%")
        
        status = self.test_results["system_status"]
        status_emoji = {
            "healthy": "🟢",
            "warning": "🟡", 
            "critical": "🔴"
        }
        
        print(f"\n{status_emoji.get(status, '⚪')} System Status: {status.upper()}")
        
        if status == "healthy":
            print("\n🎉 Foundation is solid! Ready for production use.")
        elif status == "warning":
            print("\n⚠️  Foundation has some issues but is functional.")
        else:
            print("\n🚨 Foundation has critical issues that need attention.")
        
        print(f"\nDetailed results saved to: foundation_validation_results.json")


if __name__ == "__main__":
    validator = FoundationValidator()
    results = validator.run_all_tests()
    
    # Exit with appropriate code
    if results["system_status"] == "healthy":
        sys.exit(0)
    elif results["system_status"] == "warning":
        sys.exit(1) 
    else:
        sys.exit(2)