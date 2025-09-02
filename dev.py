#!/usr/bin/env python3
"""
Sophia Intel AI Development Script
Streamlined development workflow for AI swarm orchestration.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests


# ANSI color codes
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def log(message: str, color: str = Colors.WHITE):
    """Print colored log message."""
    print(f"{color}{message}{Colors.RESET}")

def run_command(cmd: list[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command with optional directory change."""
    try:
        log(f"Running: {' '.join(cmd)}", Colors.CYAN)
        result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {e}", Colors.RED)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        if check:
            raise
        return e

def check_dependencies():
    """Check if required dependencies are installed."""
    log("🔍 Checking dependencies...", Colors.BLUE)

    # Check Python version
    if sys.version_info < (3, 11):
        log(f"❌ Python 3.11+ required, found {sys.version_info.major}.{sys.version_info.minor}", Colors.RED)
        return False

    # Check Node.js
    try:
        result = run_command(['node', '--version'], check=False)
        if result.returncode != 0:
            log("❌ Node.js not found", Colors.RED)
            return False
        log(f"✅ Node.js {result.stdout.strip()}", Colors.GREEN)
    except FileNotFoundError:
        log("❌ Node.js not found", Colors.RED)
        return False

    # Check npm
    try:
        result = run_command(['npm', '--version'], check=False)
        if result.returncode != 0:
            log("❌ npm not found", Colors.RED)
            return False
        log(f"✅ npm {result.stdout.strip()}", Colors.GREEN)
    except FileNotFoundError:
        log("❌ npm not found", Colors.RED)
        return False

    log("✅ Dependencies check passed", Colors.GREEN)
    return True

def setup_environment():
    """Set up development environment."""
    log("🔧 Setting up development environment...", Colors.BLUE)

    # Create .env.local if it doesn't exist
    env_file = Path('.env.local')
    if not env_file.exists():
        log("📝 Creating .env.local file...", Colors.YELLOW)
        env_content = """# Local development environment
ENVIRONMENT=dev
AGENT_API_PORT=8003
FRONTEND_PORT=3000

# API Keys (add your keys here)
OPENROUTER_API_KEY=your_openrouter_key_here
PORTKEY_API_KEY=your_portkey_key_here

# Model Configuration
ORCHESTRATOR_MODEL=openai/gpt-5
AGENT_SWARM_MODELS=x-ai/grok-code-fast-1,google/gemini-2.5-flash,google/gemini-2.5-pro,deepseek/deepseek-chat-v3-0324,deepseek/deepseek-chat-v3.1,qwen/qwen3-30b-a3b,qwen/qwen3-coder,openai/gpt-5,deepseek/deepseek-r1-0528:free,openai/gpt-4o-mini,z-ai/glm-4.5

# Embedding Configuration
EMBEDDING_PRIMARY_MODEL=togethercomputer/m2-bert-80M-8k-retrieval
EMBEDDING_FALLBACK_MODELS=BAAI/bge-large-en-v1.5,BAAI/bge-base-en-v1.5

# Features
EMBEDDINGS_ENABLED=true
MEMORY_ENABLED=true
TRACING_ENABLED=true
COST_TRACKING_ENABLED=true

# Rate Limiting
API_RATE_LIMIT=100
API_RATE_WINDOW=60

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3002,http://localhost:7777,http://localhost:3333
"""
        env_file.write_text(env_content)
        log("✅ Created .env.local with default configuration", Colors.GREEN)
    else:
        log("✅ .env.local already exists", Colors.GREEN)

    # Install Python dependencies
    log("📦 Installing Python dependencies...", Colors.BLUE)
    run_command([sys.executable, '-m', 'pip', 'install', '-e', '.'])

    # Install Node.js dependencies
    log("📦 Installing Node.js dependencies...", Colors.BLUE)
    run_command(['npm', 'install'], cwd='agent-ui')

    # Create data directories
    data_dirs = [
        'data/cost_tracking',
        'data/memory',
        'data/logs',
        'data/sessions'
    ]

    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    log("✅ Environment setup complete", Colors.GREEN)

def check_services():
    """Check if services are running."""
    services = {
        'API Server': ('http://localhost:8003/healthz', 8003),
        'Frontend': ('http://localhost:3000', 3000),
    }

    log("🔍 Checking service health...", Colors.BLUE)

    for name, (url, port) in services.items():
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                log(f"✅ {name} is running on port {port}", Colors.GREEN)
            else:
                log(f"⚠️  {name} responded with status {response.status_code}", Colors.YELLOW)
        except requests.RequestException:
            log(f"❌ {name} is not responding on port {port}", Colors.RED)

def start_services():
    """Start all development services."""
    log("🚀 Starting development services...", Colors.BLUE)

    processes = []

    try:
        # Start API server
        log("Starting API server on port 8003...", Colors.BLUE)
        api_env = os.environ.copy()
        api_env.update({
            'OPENROUTER_API_KEY': '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',
            'PORTKEY_API_KEY': 'nYraiE8dOR9A1gDwaRNpSSXRkXBc',
            'LOCAL_DEV_MODE': 'true',
            'AGENT_API_PORT': '8003'
        })

        api_process = subprocess.Popen([
            sys.executable, '-m', 'app.api.unified_server'
        ], env=api_env)
        processes.append(('API Server', api_process))

        # Wait a bit for API server to start
        time.sleep(3)

        # Start frontend
        log("Starting frontend on port 3000...", Colors.BLUE)
        frontend_env = os.environ.copy()
        frontend_env['NEXT_PUBLIC_API_URL'] = 'http://localhost:8003'

        frontend_process = subprocess.Popen([
            'npm', 'run', 'dev'
        ], cwd='agent-ui', env=frontend_env)
        processes.append(('Frontend', frontend_process))

        # Wait for services to be ready
        log("⏳ Waiting for services to be ready...", Colors.YELLOW)
        time.sleep(5)

        # Check service health
        check_services()

        log("🎉 All services started successfully!", Colors.GREEN)
        log("📱 Frontend: http://localhost:3000", Colors.CYAN)
        log("🔧 API Docs: http://localhost:8003/docs", Colors.CYAN)
        log("💰 Cost Dashboard: Available in frontend", Colors.CYAN)
        log("\nPress Ctrl+C to stop all services", Colors.YELLOW)

        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log("\n🛑 Shutting down services...", Colors.YELLOW)

    finally:
        # Cleanup processes
        for name, process in processes:
            try:
                log(f"Stopping {name}...", Colors.YELLOW)
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                log(f"Force killing {name}...", Colors.RED)
                process.kill()
                process.wait()
            except Exception as e:
                log(f"Error stopping {name}: {e}", Colors.RED)

        log("✅ All services stopped", Colors.GREEN)

def run_tests():
    """Run all tests."""
    log("🧪 Running tests...", Colors.BLUE)

    # Python tests
    log("Running Python tests...", Colors.BLUE)
    try:
        run_command([sys.executable, '-m', 'pytest', 'tests/', '-v'])
        log("✅ Python tests passed", Colors.GREEN)
    except subprocess.CalledProcessError:
        log("❌ Python tests failed", Colors.RED)
        return False

    # Frontend tests (if available)
    frontend_test_path = Path('agent-ui/package.json')
    if frontend_test_path.exists():
        with open(frontend_test_path) as f:
            package_data = json.load(f)
            if 'test' in package_data.get('scripts', {}):
                log("Running frontend tests...", Colors.BLUE)
                try:
                    run_command(['npm', 'test'], cwd='agent-ui')
                    log("✅ Frontend tests passed", Colors.GREEN)
                except subprocess.CalledProcessError:
                    log("❌ Frontend tests failed", Colors.RED)
                    return False

    log("✅ All tests passed", Colors.GREEN)
    return True

def build_project():
    """Build the entire project."""
    log("🏗️  Building project...", Colors.BLUE)

    # Build frontend
    log("Building frontend...", Colors.BLUE)
    run_command(['npm', 'run', 'build'], cwd='agent-ui')

    log("✅ Project built successfully", Colors.GREEN)

def lint_and_format():
    """Lint and format the code."""
    log("🧹 Linting and formatting code...", Colors.BLUE)

    # Python linting and formatting
    try:
        log("Running black formatter...", Colors.BLUE)
        run_command(['black', '.', '--exclude', 'agent-ui/'])

        log("Running ruff linter...", Colors.BLUE)
        run_command(['ruff', 'check', '.', '--exclude', 'agent-ui/'])

        log("✅ Python code formatted and linted", Colors.GREEN)
    except FileNotFoundError:
        log("⚠️  Python linting tools not installed. Install with: pip install black ruff", Colors.YELLOW)
    except subprocess.CalledProcessError:
        log("❌ Python linting failed", Colors.RED)

    # Frontend linting
    try:
        log("Running ESLint...", Colors.BLUE)
        run_command(['npm', 'run', 'lint'], cwd='agent-ui')
        log("✅ Frontend code linted", Colors.GREEN)
    except subprocess.CalledProcessError:
        log("⚠️  Frontend linting completed with warnings", Colors.YELLOW)

def show_logs():
    """Show recent logs."""
    log("📄 Recent logs:", Colors.BLUE)

    log_files = [
        'data/logs/api.log',
        'data/logs/cost_tracking.log',
        'data/logs/embedding.log'
    ]

    for log_file in log_files:
        if Path(log_file).exists():
            log(f"\n--- {log_file} ---", Colors.CYAN)
            try:
                run_command(['tail', '-20', log_file])
            except subprocess.CalledProcessError:
                # Fallback for systems without tail
                with open(log_file) as f:
                    lines = f.readlines()
                    for line in lines[-20:]:
                        print(line.rstrip())
        else:
            log(f"📄 {log_file} - No logs yet", Colors.YELLOW)

def clean():
    """Clean build artifacts and caches."""
    log("🧹 Cleaning build artifacts...", Colors.BLUE)

    # Python cache
    run_command(['find', '.', '-name', '__pycache__', '-exec', 'rm', '-rf', '{}', '+'], check=False)
    run_command(['find', '.', '-name', '*.pyc', '-delete'], check=False)

    # Node.js cache
    run_command(['rm', '-rf', 'agent-ui/node_modules/.cache'], check=False)
    run_command(['rm', '-rf', 'agent-ui/.next'], check=False)

    log("✅ Cleanup complete", Colors.GREEN)

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Sophia Intel AI Development Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s setup          # Set up development environment
  %(prog)s start          # Start all services
  %(prog)s test           # Run all tests
  %(prog)s build          # Build the project
  %(prog)s lint           # Lint and format code
  %(prog)s logs           # Show recent logs
  %(prog)s clean          # Clean build artifacts
  %(prog)s status         # Check service health
        """
    )

    parser.add_argument('command', nargs='?', default='help',
                      choices=['setup', 'start', 'test', 'build', 'lint', 'logs', 'clean', 'status', 'help'],
                      help='Command to run')

    args = parser.parse_args()

    if args.command == 'help':
        parser.print_help()
        return

    # Print banner
    log(f"""
{Colors.CYAN}{Colors.BOLD}🤖 Sophia Intel AI Development Tool{Colors.RESET}
{Colors.BLUE}AI Swarm Orchestration Platform{Colors.RESET}
""")

    # Change to project root
    os.chdir(Path(__file__).parent)

    if args.command == 'setup':
        if not check_dependencies():
            sys.exit(1)
        setup_environment()

    elif args.command == 'start':
        if not check_dependencies():
            sys.exit(1)
        start_services()

    elif args.command == 'test':
        if not run_tests():
            sys.exit(1)

    elif args.command == 'build':
        build_project()

    elif args.command == 'lint':
        lint_and_format()

    elif args.command == 'logs':
        show_logs()

    elif args.command == 'clean':
        clean()

    elif args.command == 'status':
        check_services()

if __name__ == '__main__':
    main()
