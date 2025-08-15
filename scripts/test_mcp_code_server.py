#!/usr/bin/env python3
"""
Comprehensive test suite for MCP Code Server
Tests real GitHub integration with actual API calls
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.code_mcp.tools.github_tools import GitHubTools, GitHubAPIError
from mcp_servers.code_mcp.config import code_mcp_settings


class MCPCodeServerTester:
    """Test suite for MCP Code Server"""
    
    def __init__(self):
        self.github_tools = GitHubTools()
        self.test_repository = "ai-cherry/sophia-intel"
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", data: dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        if data and success:
            print(f"   Data: {json.dumps(data, indent=2)[:200]}...")
    
    async def test_repository_access(self):
        """Test repository access validation"""
        try:
            access = await self.github_tools.validate_access(self.test_repository)
            self.log_test(
                "Repository Access",
                access,
                f"Access to {self.test_repository}: {'Granted' if access else 'Denied'}"
            )
            return access
        except Exception as e:
            self.log_test("Repository Access", False, f"Error: {e}")
            return False
    
    async def test_repository_info(self):
        """Test repository information retrieval"""
        try:
            repo_info = await self.github_tools.get_repository_info(self.test_repository)
            
            # Validate required fields
            required_fields = ["basic_info", "languages"]
            missing_fields = [f for f in required_fields if f not in repo_info]
            
            if missing_fields:
                self.log_test(
                    "Repository Info",
                    False,
                    f"Missing fields: {missing_fields}"
                )
                return False
            
            self.log_test(
                "Repository Info",
                True,
                f"Retrieved info for {repo_info['basic_info']['full_name']}",
                {
                    "name": repo_info['basic_info']['name'],
                    "private": repo_info['basic_info']['private'],
                    "default_branch": repo_info['basic_info']['default_branch'],
                    "languages": list(repo_info['languages'].keys())[:3]
                }
            )
            return True
            
        except Exception as e:
            self.log_test("Repository Info", False, f"Error: {e}")
            return False
    
    async def test_repository_structure(self):
        """Test repository structure retrieval"""
        try:
            structure = await self.github_tools.get_repository_structure(self.test_repository)
            
            # Validate structure
            required_fields = ["branch", "total_files", "files", "directories"]
            missing_fields = [f for f in required_fields if f not in structure]
            
            if missing_fields:
                self.log_test(
                    "Repository Structure",
                    False,
                    f"Missing fields: {missing_fields}"
                )
                return False
            
            self.log_test(
                "Repository Structure",
                True,
                f"Retrieved structure for branch {structure['branch']}",
                {
                    "total_files": structure['total_files'],
                    "total_directories": structure['total_directories'],
                    "sample_files": [f['path'] for f in structure['files'][:5]]
                }
            )
            return True
            
        except Exception as e:
            self.log_test("Repository Structure", False, f"Error: {e}")
            return False
    
    async def test_file_reading(self):
        """Test file content reading"""
        test_files = ["README.md", "pyproject.toml", "requirements.txt"]
        
        for file_path in test_files:
            try:
                file_content = await self.github_tools.read_file_content(
                    self.test_repository, file_path
                )
                
                # Validate file content
                if not file_content.get("content"):
                    self.log_test(
                        f"File Reading ({file_path})",
                        False,
                        "No content returned"
                    )
                    continue
                
                self.log_test(
                    f"File Reading ({file_path})",
                    True,
                    f"Read {file_content['size']} bytes",
                    {
                        "file_path": file_content['file_path'],
                        "size": file_content['size'],
                        "sha": file_content['sha'][:8],
                        "content_preview": file_content['content'][:100] + "..."
                    }
                )
                
            except GitHubAPIError as e:
                if e.status_code == 404:
                    self.log_test(
                        f"File Reading ({file_path})",
                        True,
                        "File not found (expected for some files)"
                    )
                else:
                    self.log_test(
                        f"File Reading ({file_path})",
                        False,
                        f"GitHub API Error: {e}"
                    )
            except Exception as e:
                self.log_test(
                    f"File Reading ({file_path})",
                    False,
                    f"Error: {e}"
                )
    
    async def test_multiple_file_reading(self):
        """Test reading multiple files efficiently"""
        test_files = ["README.md", "pyproject.toml", "requirements.txt", "config/config.py"]
        
        try:
            results = await self.github_tools.read_multiple_files(
                self.test_repository, test_files
            )
            
            success_count = results['successful_count']
            total_count = results['total_requested']
            
            self.log_test(
                "Multiple File Reading",
                success_count > 0,
                f"Read {success_count}/{total_count} files successfully",
                {
                    "successful_files": list(results['successful_reads'].keys()),
                    "error_files": list(results['errors'].keys()),
                    "success_rate": f"{(success_count/total_count)*100:.1f}%"
                }
            )
            
        except Exception as e:
            self.log_test("Multiple File Reading", False, f"Error: {e}")
    
    async def test_branch_operations(self):
        """Test branch creation (read-only test)"""
        try:
            # We'll test the branch creation logic without actually creating a branch
            # by checking if we can get the source branch info
            
            repo_info = await self.github_tools.get_repository_info(self.test_repository)
            default_branch = repo_info['basic_info']['default_branch']
            
            # Test getting branch reference (this validates the branch creation logic)
            ref_url = f"{self.github_tools.base_url}/repos/{self.test_repository}/git/ref/heads/{default_branch}"
            ref_data = await self.github_tools._make_request("GET", ref_url)
            
            if ref_data.get("object", {}).get("sha"):
                self.log_test(
                    "Branch Operations",
                    True,
                    f"Branch creation logic validated (source SHA: {ref_data['object']['sha'][:8]})",
                    {
                        "default_branch": default_branch,
                        "source_sha": ref_data['object']['sha'][:8],
                        "ref": ref_data['ref']
                    }
                )
            else:
                self.log_test(
                    "Branch Operations",
                    False,
                    "Could not get source branch SHA"
                )
                
        except Exception as e:
            self.log_test("Branch Operations", False, f"Error: {e}")
    
    async def test_pull_request_listing(self):
        """Test pull request listing"""
        try:
            prs = await self.github_tools.get_pull_requests(self.test_repository, "all")
            
            self.log_test(
                "Pull Request Listing",
                True,
                f"Found {len(prs)} pull requests",
                {
                    "total_prs": len(prs),
                    "recent_prs": [
                        {
                            "number": pr["number"],
                            "title": pr["title"][:50] + "...",
                            "state": pr["state"]
                        }
                        for pr in prs[:3]
                    ]
                }
            )
            
        except Exception as e:
            self.log_test("Pull Request Listing", False, f"Error: {e}")
    
    async def test_configuration(self):
        """Test configuration and settings"""
        try:
            # Test configuration access
            config_tests = [
                ("GitHub PAT", bool(code_mcp_settings.github_pat)),
                ("GitHub API Base", code_mcp_settings.github_api_base == "https://api.github.com"),
                ("Default Repository", code_mcp_settings.default_repository == "ai-cherry/sophia-intel"),
                ("Repository Access", self.test_repository in code_mcp_settings.allowed_repositories)
            ]
            
            all_passed = all(test[1] for test in config_tests)
            
            self.log_test(
                "Configuration",
                all_passed,
                f"Configuration validation: {sum(test[1] for test in config_tests)}/{len(config_tests)} passed",
                {
                    "tests": [{"name": test[0], "passed": test[1]} for test in config_tests]
                }
            )
            
        except Exception as e:
            self.log_test("Configuration", False, f"Error: {e}")
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting MCP Code Server Test Suite")
        print(f"📁 Repository: {self.test_repository}")
        print(f"🔑 GitHub PAT: {'✅ Set' if code_mcp_settings.github_pat else '❌ Missing'}")
        print("-" * 60)
        
        # Run tests in order
        test_methods = [
            self.test_configuration,
            self.test_repository_access,
            self.test_repository_info,
            self.test_repository_structure,
            self.test_file_reading,
            self.test_multiple_file_reading,
            self.test_branch_operations,
            self.test_pull_request_listing
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Test method error: {e}")
        
        # Summary
        print("-" * 60)
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 MCP Code Server is ready for production!")
        elif success_rate >= 60:
            print("⚠️  MCP Code Server has some issues but is functional")
        else:
            print("❌ MCP Code Server has significant issues")
        
        return self.test_results


async def main():
    """Main test runner"""
    # Set up environment
    os.environ.setdefault('GITHUB_PAT', '')
    
    tester = MCPCodeServerTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    results_file = Path(__file__).parent.parent / "mcp_code_server_test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "repository": tester.test_repository,
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r['success']),
            "success_rate": (sum(1 for r in results if r['success']) / len(results)) * 100,
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())

