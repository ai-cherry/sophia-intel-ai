#!/usr/bin/env python3
"""
MCP MASTER STARTUP SYSTEM
Ensures ALL MCP servers are running and connected for all AI coding assistants
"""

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv()


class MCPMasterController:
    """Master controller for all MCP servers"""

    def __init__(self):
        self.repo_path = Path(__file__).parent.parent
        self.mcp_configs = self.load_mcp_configs()
        self.server_processes = {}
        self.connection_status = {}
        self.log_file = (
            self.repo_path / "logs" / f"mcp_startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

        # Ensure log directory exists
        self.log_file.parent.mkdir(exist_ok=True)

    def load_mcp_configs(self) -> Dict:
        """Load all MCP server configurations"""
        return {
            "filesystem": {
                "name": "MCP Filesystem Server",
                "port": 8001,
                "command": ["python3", "-m", "mcp.servers.filesystem"],
                "health_endpoint": "/health",
                "required_for": ["unified-agent-cli"],
                "capabilities": ["read_files", "write_files", "list_directory", "file_search"],
            },
            "git": {
                "name": "MCP Git Server",
                "port": 8002,
                "command": ["python3", "-m", "mcp.servers.git"],
                "health_endpoint": "/health",
                "required_for": ["unified-agent-cli"],
                "capabilities": ["git_status", "git_commit", "git_push", "git_diff"],
            },
            "memory": {
                "name": "MCP Supermemory Server",
                "port": 8003,
                "command": ["python3", "-m", "app.memory.supermemory_mcp"],
                "health_endpoint": "/health",
                "required_for": ["sophia", "artemis", "unified-agent-cli"],
                "capabilities": ["store_memory", "retrieve_memory", "semantic_search"],
            },
            "embeddings": {
                "name": "MCP Embeddings Server",
                "port": 8004,
                "command": ["python3", "-m", "app.embeddings.embedding_server"],
                "health_endpoint": "/health",
                "required_for": ["sophia", "artemis"],
                "capabilities": ["generate_embeddings", "vector_search"],
            },
            "unified_api": {
                "name": "Unified API Server",
                "port": 8003,
                "command": ["python3", "app/api/unified_server.py"],
                "health_endpoint": "/healthz",
                "required_for": ["sophia", "artemis", "unified-agent-cli"],
                "capabilities": ["orchestration", "routing", "team_execution"],
            },
            "websocket": {
                "name": "WebSocket Manager",
                "port": 8005,
                "command": ["python3", "-m", "app.core.websocket_manager"],
                "health_endpoint": "/ws/health",
                "required_for": ["sophia-ui", "artemis-ui"],
                "capabilities": ["real_time_updates", "streaming"],
            },
            "redis": {
                "name": "Redis Cache",
                "port": 6379,
                "command": ["redis-server"],
                "health_check": "redis_ping",
                "required_for": ["memory", "cache"],
                "capabilities": ["caching", "pub_sub"],
            },
        }

    def log(self, message: str, level: str = "INFO"):
        """Log messages to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"

        print(log_message)
        with open(self.log_file, "a") as f:
            f.write(log_message + "\n")

    def check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return True
        except:
            return False

    def kill_process_on_port(self, port: int) -> bool:
        """Kill any process using a specific port"""
        try:
            # Find process using the port
            result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)

            if result.stdout:
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = int(parts[1])
                        self.log(f"Killing process {pid} on port {port}", "WARNING")
                        os.kill(pid, 9)
                        time.sleep(1)
                return True
        except Exception as e:
            self.log(f"Error killing process on port {port}: {e}", "ERROR")
        return False

    async def start_server(self, server_id: str, config: Dict) -> bool:
        """Start a single MCP server"""
        try:
            port = config.get("port")

            # Check if already running
            if not self.check_port_available(port):
                self.log(f"{config['name']} may already be running on port {port}")
                # Try to kill existing process
                self.kill_process_on_port(port)
                time.sleep(2)

            # Start the server
            self.log(f"Starting {config['name']} on port {port}...")

            # Build command with proper Python path
            command = config["command"]
            if command[0] == "python3":
                # Use the current Python interpreter
                command[0] = sys.executable

            # Set environment variables
            env = os.environ.copy()
            env["MCP_PORT"] = str(port)
            env["MCP_SERVER_ID"] = server_id

            # Start process
            process = subprocess.Popen(
                command, cwd=self.repo_path, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            self.server_processes[server_id] = process

            # Wait for server to start
            await asyncio.sleep(3)

            # Check if server is running
            if process.poll() is None:
                self.log(f"✅ {config['name']} started (PID: {process.pid})", "SUCCESS")
                return True
            else:
                stderr = process.stderr.read().decode() if process.stderr else ""
                self.log(f"❌ {config['name']} failed to start: {stderr}", "ERROR")
                return False

        except Exception as e:
            self.log(f"Error starting {config['name']}: {e}", "ERROR")
            return False

    async def check_server_health(self, server_id: str, config: Dict) -> bool:
        """Check if a server is healthy"""
        try:
            port = config.get("port")

            # Special handling for Redis
            if server_id == "redis":
                try:
                    import redis

                    r = redis.Redis(host="localhost", port=port, decode_responses=True)
                    r.ping()
                    return True
                except:
                    return False

            # HTTP health check for other servers
            health_endpoint = config.get("health_endpoint", "/health")
            url = f"http://localhost:{port}{health_endpoint}"

            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                return response.status_code == 200

        except Exception as e:
            self.log(f"Health check failed for {config['name']}: {e}", "WARNING")
            return False

    async def start_all_servers(self) -> Dict[str, bool]:
        """Start all MCP servers"""
        self.log("=" * 70)
        self.log("🚀 MCP MASTER STARTUP SEQUENCE INITIATED")
        self.log("=" * 70)

        results = {}

        # Start Redis first if needed
        if "redis" in self.mcp_configs:
            self.log("\n📦 Starting Redis Cache...")
            if not self.check_port_available(6379):
                self.log("Redis already running")
                results["redis"] = True
            else:
                # Start Redis
                subprocess.Popen(
                    ["redis-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                await asyncio.sleep(2)
                results["redis"] = await self.check_server_health(
                    "redis", self.mcp_configs["redis"]
                )

        # Start other servers
        for server_id, config in self.mcp_configs.items():
            if server_id == "redis":
                continue

            self.log(f"\n🔧 Starting {config['name']}...")
            success = await self.start_server(server_id, config)

            if success:
                # Verify health
                healthy = await self.check_server_health(server_id, config)
                results[server_id] = healthy

                if healthy:
                    self.log(f"✅ {config['name']} is healthy", "SUCCESS")
                else:
                    self.log(f"⚠️ {config['name']} started but health check failed", "WARNING")
            else:
                results[server_id] = False

        return results

    def create_claude_config(self):
        """Create Claude Desktop configuration for MCP servers"""
        claude_config = {
            "mcpServers": {
                "filesystem": {
                    "command": "python3",
                    "args": ["-m", "mcp.servers.filesystem", str(self.repo_path)],
                    "env": {},
                },
                "git": {
                    "command": "python3",
                    "args": ["-m", "mcp.servers.git", str(self.repo_path)],
                    "env": {},
                },
                "memory": {
                    "command": "python3",
                    "args": [str(self.repo_path / "app" / "memory" / "supermemory_mcp.py")],
                    "env": {},
                },
            }
        }

        # Save Claude config
        claude_config_path = (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
        claude_config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(claude_config_path, "w") as f:
            json.dump(claude_config, f, indent=2)

        self.log(f"✅ Claude Desktop config created at {claude_config_path}", "SUCCESS")

    def create_cursor_config(self):
        """Create Cursor/Cline configuration"""
        cursor_config = {
            "mcp.servers": [
                {
                    "name": "sophia-filesystem",
                    "url": "http://localhost:8001",
                    "capabilities": ["filesystem"],
                },
                {"name": "sophia-git", "url": "http://localhost:8002", "capabilities": ["git"]},
                {
                    "name": "sophia-memory",
                    "url": "http://localhost:8003",
                    "capabilities": ["memory", "search"],
                },
            ]
        }

        # Save to .vscode/settings.json
        vscode_settings_path = self.repo_path / ".vscode" / "settings.json"
        vscode_settings_path.parent.mkdir(exist_ok=True)

        existing_settings = {}
        if vscode_settings_path.exists():
            with open(vscode_settings_path) as f:
                existing_settings = json.load(f)

        existing_settings.update(cursor_config)

        with open(vscode_settings_path, "w") as f:
            json.dump(existing_settings, f, indent=2)

        self.log(f"✅ Cursor/Cline config updated in {vscode_settings_path}", "SUCCESS")

    def generate_status_report(self, results: Dict[str, bool]):
        """Generate comprehensive status report"""
        self.log("\n" + "=" * 70)
        self.log("📊 MCP SERVER STATUS REPORT")
        self.log("=" * 70)

        # Group by status
        running = []
        failed = []

        for server_id, status in results.items():
            config = self.mcp_configs[server_id]
            if status:
                running.append((server_id, config))
            else:
                failed.append((server_id, config))

        # Report running servers
        if running:
            self.log("\n✅ RUNNING SERVERS:")
            for server_id, config in running:
                self.log(f"  • {config['name']} (port {config.get('port', 'N/A')})")
                self.log(f"    Capabilities: {', '.join(config.get('capabilities', []))}")
                self.log(f"    Required for: {', '.join(config.get('required_for', []))}")

        # Report failed servers
        if failed:
            self.log("\n❌ FAILED SERVERS:")
            for server_id, config in failed:
                self.log(f"  • {config['name']} (port {config.get('port', 'N/A')})")
                self.log("    Check logs for details")

        # Connection instructions
        self.log("\n" + "=" * 70)
        self.log("🔌 CONNECTION INSTRUCTIONS")
        self.log("=" * 70)

        self.log("\n📱 For Claude Desktop:")
        self.log(
            "  Config saved to ~/Library/Application Support/Claude/claude_desktop_config.json"
        )
        self.log("  Restart Claude Desktop to apply")

        self.log("\n💻 For Cursor/Cline:")
        self.log("  Config saved to .vscode/settings.json")
        self.log("  Reload VS Code window to apply")

        self.log("\n🖥️ For Terminal/Codex:")
        self.log(
            "  Export MCP_SERVERS='http://localhost:8001,http://localhost:8002,http://localhost:8003'"
        )

        self.log("\n🌐 For Sophia/Artemis:")
        self.log("  API endpoint: http://localhost:8003")
        self.log("  WebSocket: ws://localhost:8005")

        # Save status to file
        status_file = self.repo_path / "mcp_status.json"
        with open(status_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "servers": results,
                    "log_file": str(self.log_file),
                },
                f,
                indent=2,
            )

        self.log(f"\n💾 Status saved to {status_file}")
        self.log(f"📝 Full logs at {self.log_file}")

    async def run(self):
        """Main execution"""
        try:
            # Start all servers
            results = await self.start_all_servers()

            # Create configurations
            self.create_claude_config()
            self.create_cursor_config()

            # Generate report
            self.generate_status_report(results)

            # Keep servers running
            if any(results.values()):
                self.log("\n" + "=" * 70)
                self.log("✅ MCP SERVERS RUNNING")
                self.log("Press Ctrl+C to stop all servers")
                self.log("=" * 70)

                # Monitor servers
                while True:
                    await asyncio.sleep(30)
                    # Could add health checks here

        except KeyboardInterrupt:
            self.log("\n🛑 Shutting down MCP servers...")
            self.shutdown()

    def shutdown(self):
        """Shutdown all servers"""
        for server_id, process in self.server_processes.items():
            if process and process.poll() is None:
                self.log(f"Stopping {self.mcp_configs[server_id]['name']}...")
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()

        self.log("✅ All servers stopped")


async def main():
    """Main entry point"""
    controller = MCPMasterController()
    await controller.run()


if __name__ == "__main__":
    asyncio.run(main())
