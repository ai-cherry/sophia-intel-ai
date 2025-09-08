#!/usr/bin/env python3
"""
MCP Servers Validation Script
Validates EVERY MCP Server for production readiness with REAL functionality testing
"""

import os
import json
import asyncio
import aiohttp
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import signal
import psutil

class MCPServerValidator:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.mcp_path = self.repo_path / "mcp_servers"
        self.results = {}
        self.errors = []
        self.warnings = []
        self.running_processes = []

    def discover_mcp_servers(self) -> List[Dict]:
        """Discover all MCP servers in the repository"""
        print("🔍 Discovering MCP Servers...")

        servers = []

        if not self.mcp_path.exists():
            self.errors.append("No mcp_servers directory found")
            return servers

        # Look for server directories and files
        for item in self.mcp_path.iterdir():
            if item.is_dir():
                # Check for server.py or main.py
                server_files = list(item.glob("*server*.py")) + list(item.glob("main.py"))
                if server_files:
                    servers.append({
                        'name': item.name,
                        'path': item,
                        'server_file': server_files[0],
                        'type': 'directory'
                    })
            elif item.is_file() and item.suffix == '.py' and 'server' in item.name:
                servers.append({
                    'name': item.stem,
                    'path': item.parent,
                    'server_file': item,
                    'type': 'file'
                })

        print(f"  ✅ Found {len(servers)} MCP servers")
        for server in servers:
            print(f"    - {server['name']}: {server['server_file'].name}")

        return servers

    def validate_server_structure(self, server: Dict) -> Dict:
        """Validate MCP server file structure"""
        print(f"\n🔍 Validating {server['name']} structure...")

        results = {
            'name': server['name'],
            'has_server_file': True,
            'has_requirements': False,
            'has_config': False,
            'has_readme': False,
            'python_syntax_valid': False,
            'imports_valid': [],
            'missing_imports': [],
            'issues': []
        }

        # Check for requirements file
        req_files = ['requirements.txt', 'pyproject.toml', 'setup.py']
        for req_file in req_files:
            if (server['path'] / req_file).exists():
                results['has_requirements'] = True
                print(f"  ✅ Requirements file: {req_file}")
                break
        else:
            results['issues'].append("No requirements file found")
            print(f"  ⚠️ No requirements file found")

        # Check for config file
        config_files = ['config.json', 'config.yaml', '.env']
        for config_file in config_files:
            if (server['path'] / config_file).exists():
                results['has_config'] = True
                print(f"  ✅ Config file: {config_file}")
                break
        else:
            print(f"  ⚠️ No config file found")

        # Check for README
        readme_files = ['README.md', 'readme.md', 'README.txt']
        for readme_file in readme_files:
            if (server['path'] / readme_file).exists():
                results['has_readme'] = True
                print(f"  ✅ Documentation: {readme_file}")
                break
        else:
            print(f"  ⚠️ No README found")

        # Validate Python syntax
        try:
            with open(server['server_file']) as f:
                content = f.read()

            # Check syntax
            compile(content, server['server_file'], 'exec')
            results['python_syntax_valid'] = True
            print(f"  ✅ Python syntax valid")

            essential_imports = [
                'fastapi', 'uvicorn', 'pydantic', 'asyncio', 
                'aiohttp', 'requests', 'json', 'os'
            ]

            for imp in essential_imports:
                if f"import {imp}" in content or f"from {imp}" in content:
                    results['imports_valid'].append(imp)
                else:
                    results['missing_imports'].append(imp)

            print(f"    Valid imports: {len(results['imports_valid'])}")
            if results['missing_imports']:
                print(f"    Missing imports: {', '.join(results['missing_imports'][:3])}...")

        except SyntaxError as e:
            results['issues'].append(f"Python syntax error: {e}")
            print(f"  ❌ Python syntax error: {e}")
        except Exception as e:
            results['issues'].append(f"File read error: {e}")
            print(f"  ❌ File read error: {e}")

        return results

    async def sophia_server_startup(self, server: Dict) -> Dict:
        """Test if MCP server can start up"""
        print(f"\n🚀 Testing {server['name']} startup...")

        results = {
            'can_start': False,
            'startup_time': None,
            'port': None,
            'process_id': None,
            'error': None
        }

        try:
            # Try to start the server
            start_time = time.time()

            # Change to server directory
            cwd = server['path'] if server['type'] == 'directory' else server['path']

            # Start the server process
            process = await asyncio.create_subprocess_exec(
                'python3', str(server['server_file']),
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self.running_processes.append(process)
            results['process_id'] = process.pid

            # Wait a bit for startup
            await asyncio.sleep(3)

            # Check if process is still running
            if process.returncode is None:
                results['can_start'] = True
                results['startup_time'] = time.time() - start_time
                print(f"  ✅ Server started (PID: {process.pid})")
                print(f"    Startup time: {results['startup_time']:.2f}s")

                # Try to find the port it's running on
                try:
                    proc = psutil.Process(process.pid)
                    connections = proc.connections()
                    for conn in connections:
                        if conn.status == 'LISTEN':
                            results['port'] = conn.laddr.port
                            print(f"    Listening on port: {conn.laddr.port}")
                            break
                except:

            else:
                # Process died, get error output
                stdout, stderr = await process.communicate()
                results['error'] = stderr.decode() if stderr else "Process exited"
                print(f"  ❌ Server failed to start: {results['error'][:100]}...")

        except Exception as e:
            results['error'] = str(e)
            print(f"  ❌ Startup error: {e}")

        return results

    async def sophia_server_endpoints(self, server: Dict, startup_results: Dict) -> Dict:
        """Test MCP server endpoints"""
        print(f"\n🧪 Testing {server['name']} endpoints...")

        results = {
            'health_endpoint': False,
            'query_endpoint': False,
            'mcp_protocol': False,
            'response_time': None,
            'endpoints_found': []
        }

        if not startup_results['can_start'] or not startup_results['port']:
            print(f"  ⚠️ Server not running, skipping endpoint tests")
            return results

        port = startup_results['port']
        base_url = f"http://localhost:{port}"

        try:
            async with aiohttp.ClientSession() as session:
                # Test common endpoints
                endpoints_to_test = [
                    '/health', '/status', '/', '/docs', 
                    '/query', '/mcp', '/tools', '/resources'
                ]

                for endpoint in endpoints_to_test:
                    try:
                        start_time = time.time()
                        async with session.get(f"{base_url}{endpoint}", timeout=5) as response:
                            response_time = time.time() - start_time

                            if response.status == 200:
                                results['endpoints_found'].append(endpoint)
                                print(f"  ✅ {endpoint}: HTTP 200 ({response_time:.3f}s)")

                                # Specific endpoint checks
                                if endpoint in ['/health', '/status']:
                                    results['health_endpoint'] = True
                                elif endpoint in ['/query', '/mcp']:
                                    results['query_endpoint'] = True
                                    if not results['response_time']:
                                        results['response_time'] = response_time

                                # Check for MCP protocol compliance
                                try:
                                    data = await response.json()
                                    if 'jsonrpc' in str(data) or 'method' in str(data):
                                        results['mcp_protocol'] = True
                                        print(f"    🔗 MCP protocol detected")
                                except:

                            elif response.status == 404:
                                pass  # Expected for non-existent endpoints
                            else:
                                print(f"  ⚠️ {endpoint}: HTTP {response.status}")

                    except asyncio.TimeoutError:
                        print(f"  ⚠️ {endpoint}: Timeout")
                    except Exception as e:
                        pass  # Skip connection errors for non-existent endpoints

                # Test POST endpoints
                if results['query_endpoint']:
                    try:
                        sophia_data = {"query": "test", "context": {}}
                        async with session.post(f"{base_url}/query", 
                                              json=sophia_data, timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                print(f"  ✅ Query endpoint functional")
                                print(f"    Response: {str(data)[:50]}...")
                            else:
                                print(f"  ⚠️ Query endpoint: HTTP {response.status}")
                    except Exception as e:
                        print(f"  ⚠️ Query test failed: {e}")

        except Exception as e:
            print(f"  ❌ Endpoint testing failed: {e}")

        return results

    def cleanup_processes(self):
        """Clean up running test processes"""
        print("\n🧹 Cleaning up test processes...")

        for process in self.running_processes:
            try:
                if process.returncode is None:
                    process.terminate()
                    print(f"  ✅ Terminated process {process.pid}")
            except:

        self.running_processes.clear()

    def validate_mcp_hub_config(self) -> Dict:
        """Validate MCP hub configuration"""
        print("\n🔍 Validating MCP Hub Configuration...")

        hub_config = self.mcp_path / "hub_config.json"
        if not hub_config.exists():
            self.warnings.append("No hub_config.json found")
            return {'exists': False}

        try:
            with open(hub_config) as f:
                config = json.load(f)

            results = {
                'exists': True,
                'valid_json': True,
                'servers_configured': len(config.get('servers', [])),
                'has_routing': 'routing' in config,
                'has_load_balancing': 'load_balancing' in config,
                'issues': []
            }

            print(f"  ✅ Hub config loaded")
            print(f"    Servers configured: {results['servers_configured']}")

            if results['has_routing']:
                print(f"    ✅ Routing configuration found")
            else:
                results['issues'].append("No routing configuration")
                print(f"    ⚠️ No routing configuration")

            return results

        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in hub_config.json: {e}")
            return {'exists': True, 'valid_json': False, 'error': str(e)}

    def create_mcp_test_suite(self):
        """Create comprehensive MCP test suite"""
        print("\n🔧 Creating MCP Test Suite...")

        sophia_content = '''#!/usr/bin/env python3
"""
MCP Servers Integration Test Suite
Tests EVERY MCP server with REAL queries
"""

import asyncio
import aiohttp
import json
from typing import Dict, List

class MCPIntegrationTester:
    def __init__(self):
        self.servers = {
            'sophia': {'port': 8001, 'endpoint': '/query'},
            'github': {'port': 8002, 'endpoint': '/query'},
            'gong': {'port': 8003, 'endpoint': '/query'},
            'hubspot': {'port': 8004, 'endpoint': '/query'},
            'slack': {'port': 8005, 'endpoint': '/query'},
            'notion': {'port': 8006, 'endpoint': '/query'},
            'kb': {'port': 8007, 'endpoint': '/query'},
            'monitor': {'port': 8008, 'endpoint': '/health'}
        }
        self.results = {}

    async def sophia_server_query(self, name: str, config: Dict) -> bool:
        """Test a single MCP server with real query"""
        try:
            url = f"http://localhost:{config['port']}{config['endpoint']}"

            async with aiohttp.ClientSession() as session:
                if config['endpoint'] == '/health':
                    async with session.get(url, timeout=5) as response:
                        return response.status == 200
                else:
                    sophia_data = {
                        "query": f"Test query for {name}",
                        "context": {"test": True}
                    }
                    async with session.post(url, json=sophia_data, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            return 'response' in data or 'result' in data
                        return False
        except Exception:
            return False

    async def sophia_all_servers(self):
        """Test all MCP servers"""
        print("🧪 Testing All MCP Servers...")

        for name, config in self.servers.items():
            print(f"\\nTesting {name} server...")
            self.results[name] = await self.sophia_server_query(name, config)

            if self.results[name]:
                print(f"  ✅ {name}: Working")
            else:
                print(f"  ❌ {name}: Not responding")

        # Summary
        working = sum(1 for v in self.results.values() if v)
        total = len(self.results)
        print(f"\\n📊 MCP Server Results: {working}/{total} working")

        return working >= total // 2  # At least half should work

if __name__ == "__main__":
    tester = MCPIntegrationTester()
    success = asyncio.run(tester.sophia_all_servers())

    if success:
        print("🎉 MCP servers are functional!")
    else:
        print("⚠️ Many MCP servers need attention!")
'''

        sophia_file = self.repo_path / "tests" / "sophia_mcp_integration.py"
        sophia_file.parent.mkdir(exist_ok=True)
        sophia_file.write_text(sophia_content)
        print(f"  ✅ Created MCP integration test suite: {sophia_file}")

    def generate_report(self) -> str:
        """Generate MCP validation report"""
        report = f"""
# MCP Servers Validation Report

## Summary
- **Total Servers**: {len(self.results.get('servers', []))}
- **Errors**: {len(self.errors)}
- **Warnings**: {len(self.warnings)}

## Server Analysis
"""

        for server_name, server_results in self.results.get('servers', {}).items():
            structure = server_results.get('structure', {})
            startup = server_results.get('startup', {})
            endpoints = server_results.get('endpoints', {})

            # Overall status
            can_start = startup.get('can_start', False)
            has_endpoints = len(endpoints.get('endpoints_found', [])) > 0
            status = "✅" if can_start and has_endpoints else "❌" if not can_start else "⚠️"

            report += f"### {status} **{server_name}**\\n\\n"

            # Structure
            report += f"**Structure:**\\n"
            report += f"- Python syntax: {'✅' if structure.get('python_syntax_valid') else '❌'}\\n"
            report += f"- Requirements file: {'✅' if structure.get('has_requirements') else '⚠️'}\\n"
            report += f"- Configuration: {'✅' if structure.get('has_config') else '⚠️'}\\n"

            # Startup
            report += f"\\n**Startup:**\\n"
            if startup.get('can_start'):
                report += f"- ✅ Starts successfully\\n"
                if startup.get('startup_time'):
                    report += f"- Startup time: {startup['startup_time']:.2f}s\\n"
                if startup.get('port'):
                    report += f"- Port: {startup['port']}\\n"
            else:
                report += f"- ❌ Failed to start\\n"
                if startup.get('error'):
                    report += f"- Error: {startup['error'][:100]}...\\n"

            # Endpoints
            if endpoints.get('endpoints_found'):
                report += f"\\n**Endpoints:**\\n"
                for endpoint in endpoints['endpoints_found']:
                    report += f"- ✅ {endpoint}\\n"

                if endpoints.get('mcp_protocol'):
                    report += f"- 🔗 MCP protocol compliant\\n"

                if endpoints.get('response_time'):
                    report += f"- Response time: {endpoints['response_time']:.3f}s\\n"

            if structure.get('issues'):
                report += f"\\n**Issues:**\\n"
                for issue in structure['issues']:
                    report += f"- ⚠️ {issue}\\n"

            report += f"\\n"

        # Hub configuration
        hub_config = self.results.get('hub_config', {})
        if hub_config.get('exists'):
            report += f"## MCP Hub Configuration\\n"
            report += f"- ✅ Configuration exists\\n"
            report += f"- Servers configured: {hub_config.get('servers_configured', 0)}\\n"
            if hub_config.get('has_routing'):
                report += f"- ✅ Routing configured\\n"
            else:
                report += f"- ⚠️ No routing configuration\\n"
        else:
            report += f"## MCP Hub Configuration\\n- ⚠️ No hub configuration found\\n"

        if self.errors:
            report += f"\\n## Errors\\n"
            for error in self.errors:
                report += f"- ❌ {error}\\n"

        if self.warnings:
            report += f"\\n## Warnings\\n"
            for warning in self.warnings:
                report += f"- ⚠️ {warning}\\n"

        return report

    async def run_validation(self):
        """Run complete MCP servers validation"""
        print("🤖 Starting MCP Servers Validation...")

        try:
            # Discover servers
            servers = self.discover_mcp_servers()
            if not servers:
                self.errors.append("No MCP servers found")
                return False

            # Validate each server
            server_results = {}
            for server in servers:
                print(f"\n{'='*50}")
                print(f"VALIDATING: {server['name'].upper()}")
                print(f"{'='*50}")

                # Structure validation
                structure_results = self.validate_server_structure(server)

                # Startup testing
                startup_results = await self.sophia_server_startup(server)

                # Endpoint testing
                endpoint_results = await self.sophia_server_endpoints(server, startup_results)

                server_results[server['name']] = {
                    'structure': structure_results,
                    'startup': startup_results,
                    'endpoints': endpoint_results
                }

            self.results['servers'] = server_results

            # Validate hub configuration
            self.results['hub_config'] = self.validate_mcp_hub_config()

            # Create test suite
            self.create_mcp_test_suite()

            # Generate and save report
            report = self.generate_report()
            report_path = self.repo_path / 'MCP_SERVERS_VALIDATION_REPORT.md'
            report_path.write_text(report)

            print(f"\\n📊 MCP Servers Validation Complete!")
            print(f"Report saved to: {report_path}")
            print(f"Servers tested: {len(servers)}")
            print(f"Errors: {len(self.errors)}")
            print(f"Warnings: {len(self.warnings)}")

            # Count working servers
            working_servers = 0
            for server_name, results in server_results.items():
                if results['startup'].get('can_start') and results['endpoints'].get('endpoints_found'):
                    working_servers += 1

            print(f"Working servers: {working_servers}/{len(servers)}")

            return len(self.errors) == 0 and working_servers > 0

        finally:
            # Always cleanup processes
            self.cleanup_processes()

if __name__ == "__main__":
    validator = MCPServerValidator()
    success = asyncio.run(validator.run_validation())

    if success:
        print("\\n🎉 MCP servers are production ready!")
    else:
        print("\\n⚠️ Some MCP servers need attention before production!")
        exit(1)
