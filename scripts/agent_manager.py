#!/usr/bin/env python3
"""
Background Agent Manager
SOLO DEVELOPER USE ONLY - NOT FOR DISTRIBUTION

Manages and schedules background scripts for the AI Development Toolkit.
"""

import os
import sys
import time
import logging
import argparse
import datetime
import subprocess
import signal
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/agent_manager.log',
    filemode='a'
)
logger = logging.getLogger('agent_manager')

# Define background agents
AGENTS = [
    {
        "name": "model_updater",
        "command": "python scripts/update_models.py",
        "description": "Updates model rankings from OpenRouter and refreshes configurations",
        "schedule": "0 */6 * * *",  # Every 6 hours
        "timeout": 300,  # 5 minutes max execution time
        "pid": None,
        "process": None,
        "last_run": None,
        "enabled": True,
        "requires_internet": True
    },
    {
        "name": "memory_pruner",
        "command": "python scripts/memory_prune.py",
        "description": "Prunes stale memory entries with relevance below 0.7",
        "schedule": "0 2 * * *",  # Daily at 2 AM
        "timeout": 600,  # 10 minutes max execution time
        "pid": None,
        "process": None,
        "last_run": None,
        "enabled": True,
        "requires_internet": False
    },
    {
        "name": "system_monitor",
        "command": "python scripts/monitor_system.py",
        "description": "Monitors system resources and API health",
        "schedule": "*/15 * * * *",  # Every 15 minutes
        "timeout": 120,  # 2 minutes max execution time
        "pid": None,
        "process": None,
        "last_run": None,
        "enabled": True,
        "requires_internet": False
    },
    {
        "name": "log_analyzer",
        "command": "python scripts/analyze_logs.py",
        "description": "Analyzes logs for errors and performance issues",
        "schedule": "0 */4 * * *",  # Every 4 hours
        "timeout": 300,  # 5 minutes max execution time
        "pid": None,
        "process": None,
        "last_run": None,
        "enabled": True,
        "requires_internet": False
    },
    {
        "name": "repo_indexer",
        "command": "python scripts/index_repository.py",
        "description": "Updates repository index with latest code changes using configured indexing system",
        "schedule": "0 2 * * *",  # Daily at 2 AM
        "timeout": 1200,  # 20 minutes max execution time (indexing can be resource intensive)
        "pid": None,
        "process": None,
        "last_run": None,
        "enabled": True,
        "requires_internet": False
    }
]

# Helper function to parse cron schedules
def is_due(schedule: str, now: Optional[datetime.datetime] = None) -> bool:
    """
    Check if a cron schedule is due to run
    """
    if now is None:
        now = datetime.datetime.now()

    # Parse cron schedule (minute, hour, day, month, day_of_week)
    parts = schedule.split()
    if len(parts) != 5:
        logger.error(f"Invalid cron schedule: {schedule}")
        return False

    minute, hour, day, month, day_of_week = parts

    # Helper function to check a single cron field
    def matches(field: str, value: int, max_val: int) -> bool:
        if field == "*":
            return True

        for part in field.split(","):
            if "/" in part:  # Handle */n format
                step_parts = part.split("/")
                if len(step_parts) != 2:
                    continue

                if step_parts[0] == "*" and value % int(step_parts[1]) == 0:
                    return True
            elif "-" in part:  # Handle ranges like 1-5
                range_parts = part.split("-")
                if len(range_parts) != 2:
                    continue

                start, end = int(range_parts[0]), int(range_parts[1])
                if start <= value <= end:
                    return True
            elif int(part) == value:  # Handle exact match
                return True

        return False

    # Check each field
    return (matches(minute, now.minute, 59) and
            matches(hour, now.hour, 23) and
            matches(day, now.day, 31) and
            matches(month, now.month, 12) and
            matches(day_of_week, now.weekday(), 6))

def run_agent(agent: Dict[str, Any], offline_mode: bool = False) -> bool:
    """
    Run a background agent
    """
    if not agent["enabled"]:
        logger.info(f"Agent {agent['name']} is disabled")
        return False

    # Skip internet-requiring agents in offline mode
    if offline_mode and agent.get("requires_internet", False):
        logger.info(f"Agent {agent['name']} requires internet but running in offline mode")
        return False

    # Check if agent is already running
    if agent["process"] is not None and agent["process"].poll() is None:
        logger.info(f"Agent {agent['name']} is already running (PID: {agent['pid']})")
        return False

    try:
        logger.info(f"Starting agent: {agent['name']}")

        # Create logs directory for agent if it doesn't exist
        agent_logs_dir = os.path.join("logs", "agents")
        os.makedirs(agent_logs_dir, exist_ok=True)

        # Set up log file
        log_file_path = os.path.join(agent_logs_dir, f"{agent['name']}.log")
        with open(log_file_path, "a") as log_file:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"\n\n--- Agent run started at {timestamp} ---\n")

        # Set environment variables if needed
        env = os.environ.copy()
        if offline_mode:
            env["OFFLINE_MODE"] = "true"

        # Run the process with log redirection
        process = subprocess.Popen(
            agent["command"], 
            shell=True,
            stdout=open(log_file_path, "a"),
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid,  # Create a new process group
            env=env
        )

        agent["process"] = process
        agent["pid"] = process.pid
        agent["last_run"] = datetime.datetime.now()

        # Create status file
        status_dir = os.path.join("status", "agents")
        os.makedirs(status_dir, exist_ok=True)

        with open(os.path.join(status_dir, f"{agent['name']}.json"), "w") as status_file:
            json.dump({
                "name": agent["name"],
                "description": agent["description"],
                "status": "running",
                "pid": agent["pid"],
                "started_at": timestamp,
                "command": agent["command"]
            }, status_file, indent=2)

        logger.info(f"Started agent {agent['name']} with PID {agent['pid']}")
        return True
    except Exception as e:
        logger.error(f"Error starting agent {agent['name']}: {e}")
        return False

def stop_agent(agent: Dict[str, Any]) -> bool:
    """
    Stop a running agent
    """
    if agent["process"] is None or agent["pid"] is None:
        logger.info(f"Agent {agent['name']} is not running")
        return False

    try:
        # Try to terminate gracefully
        os.killpg(os.getpgid(agent["pid"]), signal.SIGTERM)

        # Give it a moment to shut down
        time.sleep(2)

        # Check if it's still running
        if agent["process"].poll() is None:
            # Force kill if still running
            os.killpg(os.getpgid(agent["pid"]), signal.SIGKILL)

        agent["process"] = None
        agent["pid"] = None

        logger.info(f"Stopped agent {agent['name']}")
        return True
    except Exception as e:
        logger.error(f"Error stopping agent {agent['name']}: {e}")
        return False

def check_agent_timeout(agent: Dict[str, Any]) -> bool:
    """
    Check if an agent has exceeded its timeout and kill it if necessary
    """
    if (agent["process"] is not None and 
        agent["last_run"] is not None and 
        agent["process"].poll() is None):

        # Calculate run time
        runtime = (datetime.datetime.now() - agent["last_run"]).total_seconds()

        if runtime > agent["timeout"]:
            logger.warning(f"Agent {agent['name']} exceeded timeout of {agent['timeout']}s (ran for {runtime:.1f}s)")
            return stop_agent(agent)

    return False

def check_agent_output(agent: Dict[str, Any]) -> None:
    """
    Check output from a finished agent
    """
    if (agent["process"] is not None and 
        agent["process"].poll() is not None):  # Process has finished

        returncode = agent["process"].poll()

        # Update status file
        status_dir = os.path.join("status", "agents")
        status_file_path = os.path.join(status_dir, f"{agent['name']}.json")

        try:
            if os.path.exists(status_file_path):
                with open(status_file_path, "r") as status_file:
                    status_data = json.load(status_file)
            else:
                status_data = {
                    "name": agent["name"],
                    "description": agent["description"],
                }

            status_data["status"] = "completed" if returncode == 0 else "failed"
            status_data["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_data["exit_code"] = returncode

            with open(status_file_path, "w") as status_file:
                json.dump(status_data, status_file, indent=2)
        except Exception as e:
            logger.error(f"Error updating status file for agent {agent['name']}: {e}")

        if returncode != 0:
            logger.warning(f"Agent {agent['name']} exited with non-zero status {returncode}")

            # Read the log file for errors
            agent_log_path = os.path.join("logs", "agents", f"{agent['name']}.log")
            if os.path.exists(agent_log_path):
                try:
                    with open(agent_log_path, "r") as log_file:
                        # Get the last few lines
                        lines = log_file.readlines()
                        last_lines = lines[-20:] if len(lines) >= 20 else lines
                        error_output = "".join(last_lines)
                        logger.warning(f"Last output from {agent['name']}:\n{error_output}")
                except Exception as e:
                    logger.error(f"Error reading log file for agent {agent['name']}: {e}")
        else:
            logger.info(f"Agent {agent['name']} completed successfully")

        # Reset process
        agent["process"] = None
        agent["pid"] = None

def save_agent_status() -> None:
    """
    Save agent status for dashboard to read
    """
    status_dir = Path("status")
    status_dir.mkdir(exist_ok=True)

    status = []
    for agent in AGENTS:
        agent_status = {
            "name": agent["name"],
            "description": agent["description"],
            "schedule": agent["schedule"],
            "enabled": agent["enabled"],
            "status": "running" if agent["process"] is not None and agent["process"].poll() is None else "stopped",
            "pid": agent["pid"],
            "last_run": agent["last_run"].isoformat() if agent["last_run"] else None
        }
        status.append(agent_status)

    with open(status_dir / "agent_status.json", "w") as f:
        json.dump({
            "timestamp": datetime.datetime.now().isoformat(),
            "agents": status
        }, f, indent=2)

def run_scheduler(interval: int = 60, offline_mode: bool = False) -> None:
    """
    Run scheduler loop to check and execute agents based on schedule
    """
    logger.info(f"Starting agent scheduler with interval {interval}s")
    logger.info(f"Offline mode: {offline_mode}")

    # Create directories for logs and status
    os.makedirs("logs/agents", exist_ok=True)
    os.makedirs("status/agents", exist_ok=True)

    # Write manager status file
    with open(os.path.join("status", "agents", "manager.json"), "w") as status_file:
        json.dump({
            "pid": os.getpid(),
            "started_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "interval": interval,
            "offline_mode": offline_mode,
            "status": "running",
            "agents_managed": len(AGENTS),
            "version": "2.0" # Aug 2025 version
        }, status_file, indent=2)

    try:
        while True:
            now = datetime.datetime.now()
            logger.debug(f"Scheduler check at {now.isoformat()}")

            for agent in AGENTS:
                # Check if agent has timed out
                check_agent_timeout(agent)

                # Check output from finished agents
                check_agent_output(agent)

                # Check if agent is due to run
                if is_due(agent["schedule"], now):
                    if agent["process"] is None or agent["process"].poll() is not None:
                        run_agent(agent, offline_mode=offline_mode)

            # Save status for dashboard
            save_agent_status()

            # Wait for next check
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted, shutting down agents")
        for agent in AGENTS:
            if agent["process"] is not None and agent["process"].poll() is None:
                stop_agent(agent)

        # Update manager status
        with open(os.path.join("status", "agents", "manager.json"), "w") as status_file:
            json.dump({
                "pid": os.getpid(),
                "started_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "stopped_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "interval": interval,
                "offline_mode": offline_mode,
                "status": "stopped",
                "agents_managed": len(AGENTS),
                "version": "2.0" # Aug 2025 version
            }, status_file, indent=2)

        logger.info("All agents stopped")

def main() -> None:
    """
    Main function
    """
    parser = argparse.ArgumentParser(description="Background Agent Manager for AI Development Toolkit (Aug 2025)")
    parser.add_argument("--interval", type=int, default=60,
                       help="Scheduler check interval in seconds (default: 60)")
    parser.add_argument("--run", type=str,
                       help="Run a specific agent immediately")
    parser.add_argument("--stop", type=str,
                       help="Stop a specific agent")
    parser.add_argument("--status", action="store_true",
                       help="Show status of all agents")
    parser.add_argument("--enable", type=str,
                       help="Enable a specific agent")
    parser.add_argument("--disable", type=str,
                       help="Disable a specific agent")
    parser.add_argument("--offline-mode", action="store_true",
                       help="Run in offline mode, skipping agents that require internet access")
    parser.add_argument("--auto-update", action="store_true",
                       help="Enable auto-updating of agent scripts from repository")
    parser.add_argument("--list-logs", action="store_true",
                       help="List all agent log files")
    args = parser.parse_args()

    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("logs/agents", exist_ok=True)
    os.makedirs("status", exist_ok=True)
    os.makedirs("status/agents", exist_ok=True)

    # Handle command-line actions
    if args.run:
        for agent in AGENTS:
            if agent["name"] == args.run:
                if run_agent(agent, offline_mode=args.offline_mode):
                    print(f"Started agent {agent['name']}")
                else:
                    print(f"Failed to start agent {agent['name']}")
                sys.exit(0)
        print(f"Agent '{args.run}' not found")
        sys.exit(1)

    if args.stop:
        for agent in AGENTS:
            if agent["name"] == args.stop:
                if stop_agent(agent):
                    print(f"Stopped agent {agent['name']}")
                else:
                    print(f"Failed to stop agent {agent['name']}")
                sys.exit(0)
        print(f"Agent '{args.stop}' not found")
        sys.exit(1)

    if args.enable:
        for agent in AGENTS:
            if agent["name"] == args.enable:
                agent["enabled"] = True
                print(f"Enabled agent {agent['name']}")
                sys.exit(0)
        print(f"Agent '{args.enable}' not found")
        sys.exit(1)

    if args.disable:
        for agent in AGENTS:
            if agent["name"] == args.disable:
                agent["enabled"] = False
                print(f"Disabled agent {agent['name']}")
                sys.exit(0)
        print(f"Agent '{args.disable}' not found")
        sys.exit(1)

    if args.list_logs:
        log_dir = os.path.join("logs", "agents")
        if os.path.exists(log_dir):
            logs = os.listdir(log_dir)
            if logs:
                print(f"Agent log files in {log_dir}:")
                for log in logs:
                    log_path = os.path.join(log_dir, log)
                    size = os.path.getsize(log_path)
                    mtime = os.path.getmtime(log_path)
                    mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"  {log:<20} {size/1024:.1f} KB  {mtime_str}")
            else:
                print(f"No log files found in {log_dir}")
        else:
            print(f"Log directory {log_dir} does not exist")
        sys.exit(0)

    if args.status:
        print(f"{'Agent':<15} {'Status':<10} {'PID':<8} {'Last Run':<20} {'Schedule':<15} {'Enabled'} {'Internet'}")
        print("-" * 95)
        for agent in AGENTS:
            status = "running" if agent["process"] is not None and agent["process"].poll() is None else "stopped"
            pid = agent["pid"] if agent["pid"] else "N/A"
            last_run = agent["last_run"].strftime("%Y-%m-%d %H:%M:%S") if agent["last_run"] else "Never"
            requires_net = "Yes" if agent.get("requires_internet", False) else "No"
            print(f"{agent['name']:<15} {status:<10} {pid:<8} {last_run:<20} {agent['schedule']:<15} " + 
                  f"{'Yes' if agent['enabled'] else 'No':<7} {requires_net}")
        sys.exit(0)

    # Check environment variable for offline mode
    env_offline = os.environ.get("OFFLINE_MODE", "").lower() in ("true", "1", "yes")
    offline_mode = args.offline_mode or env_offline

    if offline_mode:
        logger.info("Running in OFFLINE MODE - internet-requiring agents will be skipped")

    # Run scheduler
    run_scheduler(args.interval, offline_mode=offline_mode)

if __name__ == "__main__":
    main()
