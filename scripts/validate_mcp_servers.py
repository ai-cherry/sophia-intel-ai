#!/usr/bin/env python3
"""
MCP Server Validation Script
Tests all MCP servers and their endpoints to ensure they are operational.
"""

import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import requests
import argparse
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import box

console = Console()

# MCP Server Configuration
MCP_SERVERS = {
    "Memory": {
        "port": 8081,
        "health": "/health",
        "endpoints": [
            {
                "name": "Store Memory",
                "method": "POST",
                "path": "/sessions/test-validation/memory",
                "data": {"content": "Validation test entry", "role": "user"},
                "description": "Store memory in session"
            },
            {
                "name": "Retrieve Memory",
                "method": "GET",
                "path": "/sessions/test-validation/memory",
                "description": "Retrieve session memory"
            },
            {
                "name": "Search Memory",
                "method": "POST",
                "path": "/search",
                "data": {"query": "test"},
                "description": "Search across memories"
            },
            {
                "name": "List Sessions",
                "method": "GET",
                "path": "/sessions",
                "description": "List all active sessions"
            },
            {
                "name": "Clear Session",
                "method": "DELETE",
                "path": "/sessions/test-validation/memory",
                "description": "Clear test session"
            }
        ]
    },
    "Filesystem": {
        "port": 8082,
        "health": "/health",
        "endpoints": [
            {
                "name": "List Files",
                "method": "POST",
                "path": "/fs/list",
                "data": {"path": "."},
                "description": "List workspace files"
            },
            {
                "name": "Read File",
                "method": "POST",
                "path": "/fs/read",
                "data": {"path": "README.md"},
                "description": "Read a file"
            },
            {
                "name": "Repo List",
                "method": "POST",
                "path": "/repo/list",
                "data": {"root": ".", "limit": 10},
                "description": "List repository files"
            },
            {
                "name": "Repo Search",
                "method": "POST",
                "path": "/repo/search",
                "data": {"query": "def", "limit": 5},
                "description": "Search in repository"
            },
            {
                "name": "Symbol Index",
                "method": "POST",
                "path": "/symbols/index",
                "data": {"languages": ["python"]},
                "description": "Index code symbols"
            }
        ]
    },
    "Git": {
        "port": 8084,
        "health": "/health",
        "endpoints": [
            {
                "name": "Git Status",
                "method": "GET",
                "path": "/status",
                "description": "Get repository status"
            },
            {
                "name": "Git Log",
                "method": "GET",
                "path": "/log?limit=5",
                "description": "Get recent commits"
            },
            {
                "name": "Git Branches",
                "method": "GET",
                "path": "/branches",
                "description": "List branches"
            }
        ]
    }
}

class MCPValidator:
    """Validates MCP server health and functionality."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: Dict[str, Dict] = {}
        self.session = requests.Session()
        # Set default headers for MCP authentication
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": "Bearer dev-token"  # Dev bypass token
        })
    
    def test_health(self, server_name: str, port: int, health_path: str) -> Tuple[bool, str]:
        """Test server health endpoint."""
        try:
            url = f"http://localhost:{port}{health_path}"
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                
                if status in ["healthy", "ok"]:
                    return True, f"✅ Healthy - {json.dumps(data)[:100]}"
                else:
                    return False, f"⚠️ Unhealthy - {status}"
            else:
                return False, f"❌ HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "❌ Connection refused - server not running"
        except requests.exceptions.Timeout:
            return False, "❌ Timeout - server not responding"
        except Exception as e:
            return False, f"❌ Error: {str(e)[:50]}"
    
    def test_endpoint(self, server_name: str, port: int, endpoint: Dict) -> Tuple[bool, str]:
        """Test a specific endpoint."""
        try:
            url = f"http://localhost:{port}{endpoint['path']}"
            method = endpoint.get("method", "GET")
            data = endpoint.get("data")
            
            if method == "GET":
                response = self.session.get(url, timeout=5)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=5)
            elif method == "DELETE":
                response = self.session.delete(url, timeout=5)
            else:
                return False, f"❌ Unsupported method: {method}"
            
            if response.status_code in [200, 201, 204]:
                if response.content:
                    try:
                        result = response.json()
                        preview = json.dumps(result)[:100]
                        return True, f"✅ Success - {preview}"
                    except:
                        return True, f"✅ Success - {response.status_code}"
                else:
                    return True, f"✅ Success - {response.status_code}"
            elif response.status_code == 404:
                return False, "⚠️ Endpoint not found (404)"
            elif response.status_code == 401:
                return False, "⚠️ Authentication required (401)"
            else:
                return False, f"❌ HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "❌ Connection refused"
        except requests.exceptions.Timeout:
            return False, "❌ Timeout"
        except Exception as e:
            return False, f"❌ Error: {str(e)[:50]}"
    
    def validate_server(self, server_name: str, config: Dict) -> Dict:
        """Validate a single MCP server."""
        results = {
            "server": server_name,
            "port": config["port"],
            "health": None,
            "endpoints": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
        
        # Test health
        console.print(f"\n[cyan]Testing {server_name} Server (port {config['port']})...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task(f"Checking health...", total=None)
            
            health_ok, health_msg = self.test_health(
                server_name, 
                config["port"], 
                config["health"]
            )
            results["health"] = {
                "ok": health_ok,
                "message": health_msg
            }
            
            progress.update(task, description=health_msg)
        
        # Test endpoints if health check passed
        if health_ok:
            for endpoint in config.get("endpoints", []):
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True
                ) as progress:
                    task = progress.add_task(
                        f"Testing {endpoint['name']}...", 
                        total=None
                    )
                    
                    ep_ok, ep_msg = self.test_endpoint(
                        server_name,
                        config["port"],
                        endpoint
                    )
                    
                    results["endpoints"].append({
                        "name": endpoint["name"],
                        "path": endpoint["path"],
                        "method": endpoint.get("method", "GET"),
                        "ok": ep_ok,
                        "message": ep_msg,
                        "description": endpoint.get("description", "")
                    })
                    
                    results["summary"]["total"] += 1
                    if ep_ok:
                        results["summary"]["passed"] += 1
                    else:
                        results["summary"]["failed"] += 1
                    
                    progress.update(task, description=ep_msg)
                    
                    if self.verbose:
                        console.print(f"  {endpoint['name']}: {ep_msg}")
        else:
            console.print(f"[red]⚠️ Skipping endpoint tests - health check failed[/red]")
        
        return results
    
    def run_validation(self) -> bool:
        """Run validation for all MCP servers."""
        console.print(Panel.fit(
            "[bold cyan]MCP Server Validation[/bold cyan]\n"
            f"Timestamp: {datetime.now().isoformat()}",
            box=box.DOUBLE
        ))
        
        all_passed = True
        
        for server_name, config in MCP_SERVERS.items():
            results = self.validate_server(server_name, config)
            self.results[server_name] = results
            
            if not results["health"]["ok"]:
                all_passed = False
            elif results["summary"]["failed"] > 0:
                all_passed = False
        
        return all_passed
    
    def print_summary(self):
        """Print validation summary."""
        console.print("\n" + "="*60)
        console.print("[bold cyan]VALIDATION SUMMARY[/bold cyan]")
        console.print("="*60)
        
        # Create summary table
        table = Table(box=box.ROUNDED)
        table.add_column("Server", style="cyan")
        table.add_column("Port", style="yellow")
        table.add_column("Health", style="green")
        table.add_column("Endpoints", style="blue")
        table.add_column("Status", style="magenta")
        
        for server_name, results in self.results.items():
            health_status = "✅ OK" if results["health"]["ok"] else "❌ Failed"
            
            if results["summary"]["total"] > 0:
                endpoint_summary = f"{results['summary']['passed']}/{results['summary']['total']} passed"
                if results['summary']['failed'] > 0:
                    endpoint_status = "⚠️ Partial"
                else:
                    endpoint_status = "✅ All Pass"
            else:
                endpoint_summary = "N/A"
                endpoint_status = "⏭️ Skipped"
            
            if not results["health"]["ok"]:
                overall_status = "❌ Down"
            elif results["summary"]["failed"] > 0:
                overall_status = "⚠️ Degraded"
            else:
                overall_status = "✅ Operational"
            
            table.add_row(
                server_name,
                str(results["port"]),
                health_status,
                endpoint_summary,
                overall_status
            )
        
        console.print(table)
        
        # Print detailed failures if any
        has_failures = False
        for server_name, results in self.results.items():
            failures = [ep for ep in results["endpoints"] if not ep["ok"]]
            if failures or not results["health"]["ok"]:
                has_failures = True
                
                if not has_failures:
                    console.print("\n[bold red]FAILURES:[/bold red]")
                
                console.print(f"\n[yellow]{server_name} Server:[/yellow]")
                
                if not results["health"]["ok"]:
                    console.print(f"  Health Check: {results['health']['message']}")
                
                for failure in failures:
                    console.print(f"  {failure['name']}: {failure['message']}")
        
        # Print recommendations
        if has_failures:
            console.print("\n[bold yellow]RECOMMENDATIONS:[/bold yellow]")
            console.print("1. Check if all MCP servers are running: ./startup.sh")
            console.print("2. Verify Redis is running: redis-cli ping")
            console.print("3. Check server logs for errors: tail -f logs/mcp_*.log")
            console.print("4. Ensure proper environment variables are set")
    
    def save_report(self, filename: str = "mcp_validation_report.json"):
        """Save validation report to file."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "summary": {
                "total_servers": len(self.results),
                "healthy_servers": sum(1 for r in self.results.values() if r["health"]["ok"]),
                "total_endpoints": sum(r["summary"]["total"] for r in self.results.values()),
                "passed_endpoints": sum(r["summary"]["passed"] for r in self.results.values()),
                "failed_endpoints": sum(r["summary"]["failed"] for r in self.results.values())
            }
        }
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        console.print(f"\n[green]Report saved to: {filename}[/green]")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate MCP Servers")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-o", "--output", help="Output report filename")
    parser.add_argument("--quick", action="store_true", help="Quick health check only")
    args = parser.parse_args()
    
    validator = MCPValidator(verbose=args.verbose)
    
    try:
        if args.quick:
            # Quick health check only
            console.print("[cyan]Running quick health check...[/cyan]")
            all_healthy = True
            for server_name, config in MCP_SERVERS.items():
                health_ok, health_msg = validator.test_health(
                    server_name,
                    config["port"],
                    config["health"]
                )
                console.print(f"{server_name}: {health_msg}")
                if not health_ok:
                    all_healthy = False
            
            sys.exit(0 if all_healthy else 1)
        
        # Full validation
        all_passed = validator.run_validation()
        validator.print_summary()
        
        if args.output:
            validator.save_report(args.output)
        
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Validation interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()