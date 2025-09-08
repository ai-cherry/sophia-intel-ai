#!/usr/bin/env python3
"""
Unified AI Agent CLI
Provides standardized access to Grok, Claude Coder, and Codex agents
Implements all Codex suggestions for unified environment and routing
"""

import os
import sys
import json
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv('.env.mcp')
    load_dotenv('.env.sophia')
except ImportError:
    pass

class UnifiedAgentCLI:
    """Unified CLI for all AI agents with consistent routing"""
    
    def __init__(self):
        self.agents = {
            "grok": {
                "model": "x-ai/grok-code-fast-1",
                "provider": "openrouter",
                "key_env": "GROK_API_KEY",
                "specialties": ["code_generation", "debugging", "review"]
            },
            "claude": {
                "model": "anthropic/claude-3.5-sonnet-20241022",
                "provider": "anthropic", 
                "key_env": "ANTHROPIC_API_KEY",
                "specialties": ["refactoring", "architecture", "complex_logic"]
            },
            "codex": {
                "model": "openai/gpt-4-turbo-preview",
                "provider": "openai",
                "key_env": "OPENAI_API_KEY",
                "specialties": ["testing", "documentation", "completion"]
            }
        }
        
        # Load model configuration if available
        self._load_model_config()
        
        # MCP configuration
        self.mcp_port = int(os.getenv("MCP_MEMORY_PORT", "8765"))
        self.mcp_host = os.getenv("MCP_MEMORY_HOST", "localhost")
        
    def _load_model_config(self):
        """Load model configuration from app/config/models_config.json if available"""
        config_path = Path(__file__).parent.parent / "app" / "config" / "models_config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    # Update agent models from config if present
                    if "agents" in config:
                        for agent_name, agent_config in config["agents"].items():
                            if agent_name in self.agents:
                                self.agents[agent_name].update(agent_config)
            except Exception as e:
                print(f"Warning: Could not load model config: {e}")
    
    def whoami(self, args):
        """Print environment and configuration details"""
        print("\n" + "="*60)
        print("🤖 UNIFIED AI AGENT CLI - ENVIRONMENT REPORT")
        print("="*60)
        
        # Selected agent
        if args.agent:
            agent = self.agents.get(args.agent)
            if agent:
                print(f"\n📍 Selected Agent: {args.agent.upper()}")
                print(f"   Model: {agent['model']}")
                print(f"   Provider: {agent['provider']}")
                
                # Check API key
                key_env = agent['key_env']
                if os.getenv(key_env):
                    print(f"   API Key: {key_env} = ***{os.getenv(key_env)[-4:]}")
                else:
                    print(f"   API Key: {key_env} = NOT SET ❌")
                
                print(f"   Specialties: {', '.join(agent['specialties'])}")
        
        # Environment
        print(f"\n🌍 Environment:")
        print(f"   Python: {sys.version.split()[0]}")
        print(f"   Working Dir: {os.getcwd()}")
        print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
        
        # MCP Configuration
        print(f"\n🔌 MCP Configuration:")
        print(f"   Memory Server: {self.mcp_host}:{self.mcp_port}")
        
        # Check MCP health
        try:
            import httpx
            response = httpx.get(f"http://{self.mcp_host}:{self.mcp_port}/health", timeout=2)
            if response.status_code == 200:
                print(f"   Status: ✅ Connected")
            else:
                print(f"   Status: ⚠️  Unhealthy ({response.status_code})")
        except:
            print(f"   Status: ❌ Not reachable")
        
        # Available providers
        print(f"\n🔑 API Keys Status:")
        for name, agent in self.agents.items():
            key_env = agent['key_env']
            status = "✅" if os.getenv(key_env) else "❌"
            print(f"   {name}: {status} {key_env}")
        
        # Additional keys
        extra_keys = ["OPENROUTER_API_KEY", "PORTKEY_API_KEY"]
        for key in extra_keys:
            if os.getenv(key):
                print(f"   Router: ✅ {key}")
        
        print("\n" + "="*60)
    
    async def execute_task(self, args):
        """Execute a task with the selected agent"""
        agent_name = args.agent
        if agent_name not in self.agents:
            print(f"❌ Unknown agent: {agent_name}")
            print(f"Available agents: {', '.join(self.agents.keys())}")
            return 1
        
        agent = self.agents[agent_name]
        
        # Check API key
        if not os.getenv(agent['key_env']):
            print(f"❌ API key not set: {agent['key_env']}")
            return 1
        
        # Build task
        task = {
            "agent": agent_name,
            "model": agent['model'],
            "mode": args.mode,
            "task": args.task,
            "timestamp": datetime.now().isoformat()
        }
        
        if args.file:
            if Path(args.file).exists():
                task["file"] = args.file
                task["file_content"] = Path(args.file).read_text()
            else:
                print(f"❌ File not found: {args.file}")
                return 1
        
        if args.dry_run:
            print("\n🔸 DRY RUN - Would execute:")
            print(json.dumps(task, indent=2))
            return 0
        
        # Execute task (simplified for now)
        print(f"\n🚀 Executing with {agent_name.upper()}...")
        print(f"   Model: {agent['model']}")
        print(f"   Mode: {args.mode}")
        print(f"   Task: {args.task}")
        
        # Try to use existing MultiTransportLLM if available
        try:
            from app.llm.multi_transport import MultiTransportLLM
            
            llm = MultiTransportLLM(
                provider=agent['provider'],
                model=agent['model']
            )
            
            # Build prompt based on mode
            if args.mode == "code":
                prompt = f"Generate code for: {args.task}"
            else:
                prompt = args.task
            
            response = await llm.generate(prompt)
            print(f"\n📝 Response:")
            print(response)
            
        except ImportError:
            # Fallback to simple output
            print(f"\n📝 Response (Mock):")
            print(f"Would call {agent['provider']} API with model {agent['model']}")
            print(f"Task: {args.task}")
            
            if args.mode == "code":
                print("\n```python")
                print(f"# Generated by {agent_name}")
                print(f"# Task: {args.task}")
                print("# Implementation would go here")
                print("```")
        
        return 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified AI Agent CLI for Grok, Claude, and Codex",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --agent grok --mode code --task "sum 1..10"
  %(prog)s --agent claude --mode chat --task "explain recursion"
  %(prog)s --agent codex --mode code --file main.py --task "add tests"
  %(prog)s --whoami
  %(prog)s --agent grok --dry-run --task "create REST API"
        """
    )
    
    parser.add_argument(
        "--agent",
        choices=["grok", "claude", "codex"],
        help="AI agent to use"
    )
    
    parser.add_argument(
        "--mode",
        choices=["chat", "code"],
        default="chat",
        help="Interaction mode (default: chat)"
    )
    
    parser.add_argument(
        "--task",
        help="Task description or prompt"
    )
    
    parser.add_argument(
        "--file",
        help="Optional file path for context"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    
    parser.add_argument(
        "--whoami",
        action="store_true",
        help="Print environment and configuration details"
    )
    
    args = parser.parse_args()
    
    cli = UnifiedAgentCLI()
    
    # Handle whoami
    if args.whoami:
        cli.whoami(args)
        return 0
    
    # Require agent and task for execution
    if not args.agent:
        parser.print_help()
        return 1
    
    if not args.task and not args.whoami:
        print("❌ --task is required when using --agent")
        return 1
    
    # Execute task
    return asyncio.run(cli.execute_task(args))

if __name__ == "__main__":
    sys.exit(main())