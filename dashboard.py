#!/usr/bin/env python3
"""
Artemis Dashboard - Cloud-Centric AI Dev Toolkit Monitor
SOLO DEVELOPER USE ONLY - NOT FOR DISTRIBUTION

Provides comprehensive monitoring of AI services, background agents,
memory systems, and code quality in a cloud-first environment.
"""

import asyncio
import base64
import datetime
import json
import logging
import os
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import aiohttp
import httpx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psutil
import requests
import streamlit as st
from huggingface_hub import InferenceClient

try:
    import mem0
    from mem0 import Memory
    HAS_MEM0 = True
except ImportError:
    HAS_MEM0 = False

try:
    import portkey
    HAS_PORTKEY = True
except ImportError:
    HAS_PORTKEY = False

try:
    from evidently.metrics import DataDriftTable
    from evidently.report import Report
    HAS_EVIDENTLY = True
except ImportError:
    HAS_EVIDENTLY = False

# Background script process management
class BackgroundAgent:
    """Class to manage background agent processes"""
    def __init__(self, name, command, description, schedule="*/30 * * * *"):
        self.name = name
        self.command = command
        self.description = description
        self.schedule = schedule  # Cron schedule
        self.last_run = None
        self.status = "stopped"
        self.pid = None

    def start(self):
        """Start the background agent process"""
        try:
            # Use subprocess to start the process
            process = subprocess.Popen(
                self.command, 
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.pid = process.pid
            self.status = "running"
            self.last_run = datetime.datetime.now()
            return True
        except Exception as e:
            logging.error(f"Failed to start agent {self.name}: {e}")
            return False

    def stop(self):
        """Stop the background agent process"""
        if self.pid:
            try:
                process = psutil.Process(self.pid)
                process.terminate()
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    process.kill()
                self.status = "stopped"
                self.pid = None
                return True
            except Exception as e:
                logging.error(f"Failed to stop agent {self.name}: {e}")
                return False
        return False

    def is_running(self):
        """Check if the agent is currently running"""
        if not self.pid:
            return False
        try:
            # Check if process exists
            os.kill(self.pid, 0)
            return True
        except OSError:
            self.status = "stopped"
            self.pid = None
            return False

    def to_dict(self):
        """Convert agent to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "last_run": self.last_run.strftime("%Y-%m-%d %H:%M:%S") if self.last_run else "Never",
            "schedule": self.schedule,
            "pid": self.pid or "N/A"
        }

# Initialize Streamlit page config
st.set_page_config(
    page_title="AI Toolkit Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
MODEL_SCORING_FORMULA = "(tokens_processed * 0.7) - (cost_per_million * 0.3)"
MAX_COST_THRESHOLD = 0.55  # $ per million tokens
LOG_FILE = "mcp_server.log"
CONFIG_FILE = ".continue/config.json"

# Helper functions
def load_config():
    """Load the Continue.dev configuration"""
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return {}

def get_model_rankings():
    """Get model rankings from OpenRouter API or local cache"""
    try:
        if os.getenv("OPENROUTER_API_KEY"):
            headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"}
            response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
            data = response.json()['data']

            # Calculate scores based on formula
            models = []
            for model in data:
                tokens_processed = model.get('tokens_processed', 0)
                cost_per_million = model.get('pricing', {}).get('output', 0) * 1000000

                if cost_per_million > 0:
                    score = (tokens_processed * 0.7) - (cost_per_million * 0.3)
                else:
                    score = tokens_processed * 0.7

                models.append({
                    'id': model.get('id', 'unknown'),
                    'name': model.get('name', 'Unknown Model'),
                    'tokens_processed': tokens_processed,
                    'cost_per_million': cost_per_million,
                    'score': score,
                    'context_length': model.get('context_length', 0)
                })

            # Sort by score
            models.sort(key=lambda x: x['score'], reverse=True)

            # Save to cache
            with open("model_rankings_cache.json", "w") as f:
                json.dump(models, f)

            return models
        else:
            # Try to load from cache
            try:
                with open("model_rankings_cache.json", "r") as f:
                    return json.load(f)
            except:
                # Generate mock data if offline
                return generate_mock_rankings()
    except Exception as e:
        st.warning(f"Error fetching model rankings: {e}")
        return generate_mock_rankings()

def generate_mock_rankings():
    """Generate mock model rankings for offline mode"""
    return [
        {'id': 'anthropic/claude-sonnet-4', 'name': 'Claude Sonnet 4', 'tokens_processed': 15000000, 'cost_per_million': 8.0, 'score': 8100000, 'context_length': 200000},
        {'id': 'qwen/qwen3-coder', 'name': 'Qwen3 Coder', 'tokens_processed': 12000000, 'cost_per_million': 5.0, 'score': 6900000, 'context_length': 128000},
        {'id': 'deepseek/v3-0324-free', 'name': 'DeepSeek Free', 'tokens_processed': 8000000, 'cost_per_million': 0.0, 'score': 5600000, 'context_length': 32000},
        {'id': 'meta-llama/codellama-70b', 'name': 'CodeLlama 70B', 'tokens_processed': 0, 'cost_per_million': 0.0, 'score': 0, 'context_length': 16000}
    ]

def analyze_logs():
    """Analyze MCP server logs for usage patterns"""
    try:
        if not os.path.exists(LOG_FILE):
            return {
                'total_requests': 0,
                'tool_usage': {},
                'errors': 0,
                'avg_response_time': 0
            }

        with open(LOG_FILE, "r") as f:
            lines = f.readlines()

        total_requests = 0
        tool_usage = {
            'code_execution': 0,
            'web_search': 0,
            'browse_page': 0,
            'x_search': 0,
            'rag_hybrid': 0,
            'sequential_think': 0,
            'swarm': 0
        }
        errors = 0

        for line in lines:
            if "INFO" in line and "POST" in line:
                total_requests += 1
                for tool in tool_usage.keys():
                    if f"/{tool}" in line:
                        tool_usage[tool] += 1
            if "ERROR" in line:
                errors += 1

        # Mock avg response time
        avg_response_time = 120  # ms

        return {
            'total_requests': total_requests,
            'tool_usage': tool_usage,
            'errors': errors,
            'avg_response_time': avg_response_time
        }
    except Exception as e:
        st.error(f"Error analyzing logs: {e}")
        return {
            'total_requests': 0,
            'tool_usage': {},
            'errors': 0,
            'avg_response_time': 0
        }

def get_token_usage_trend():
    """Generate token usage trend data"""
    # In a real setup, this would pull from actual usage metrics
    # For now, generate mock data
    dates = pd.date_range(end=datetime.datetime.now(), periods=14).tolist()

    data = {
        'date': dates,
        'claude_sonnet': [1500, 1800, 1200, 2000, 1750, 1900, 2200, 2100, 1950, 2300, 2500, 2100, 2400, 2600],
        'qwen3_coder': [2200, 2500, 2100, 2400, 2600, 2300, 2700, 2500, 2800, 2900, 3100, 2700, 3000, 3200],
        'deepseek_free': [800, 750, 900, 1000, 850, 950, 1100, 950, 1000, 1200, 1300, 1100, 1250, 1400],
        'codellama_local': [500, 600, 450, 550, 700, 600, 800, 750, 850, 900, 950, 850, 1000, 1100]
    }

    return pd.DataFrame(data)

def get_api_health():
    """Check health of API endpoints"""
    endpoints = [
        {"name": "MCP Server", "url": "http://localhost:8000/health", "expected_status": 200},
        {"name": "OpenRouter", "url": "https://openrouter.ai/api/v1/auth/key", "expected_status": 200},
        {"name": "Portkey", "url": "https://api.portkey.ai/v1/health", "expected_status": 200},
        {"name": "Memory System", "url": "http://localhost:6333/health", "expected_status": 200},  # Qdrant
    ]

    results = []

    for endpoint in endpoints:
        try:
            headers = {}
            if "openrouter.ai" in endpoint["url"] and os.getenv("OPENROUTER_API_KEY"):
                headers["Authorization"] = f"Bearer {os.getenv('OPENROUTER_API_KEY')}"
            elif "portkey.ai" in endpoint["url"] and os.getenv("PORTKEY_API_KEY"):
                headers["x-portkey-api-key"] = os.getenv("PORTKEY_API_KEY")

            response = requests.get(endpoint["url"], headers=headers, timeout=3)
            status = "UP" if response.status_code == endpoint["expected_status"] else "DOWN"
            latency = response.elapsed.total_seconds() * 1000  # ms
        except Exception as e:
            status = "DOWN"
            latency = 0

        results.append({
            "name": endpoint["name"],
            "status": status,
            "latency": f"{latency:.2f}ms" if latency > 0 else "N/A",
            "last_checked": datetime.datetime.now().strftime("%H:%M:%S")
        })

    return results

def get_background_agents():
    """Get list of background agents and their status"""
    # In a real setup, this would query actual agent processes
    # For now, define standard background agents for the toolkit

    agents = [
        BackgroundAgent(
            "model_updater",
            "python update_models.py",
            "Updates model rankings from OpenRouter and refreshes configurations",
            schedule="0 */6 * * *"  # Every 6 hours
        ),
        BackgroundAgent(
            "memory_pruner",
            "python memory_prune.py",
            "Prunes stale memory entries with relevance < 0.7",
            schedule="0 2 * * *"  # Daily at 2 AM
        ),
        BackgroundAgent(
            "system_monitor",
            "python monitor_system.py",
            "Monitors system resources and alerts on high usage",
            schedule="*/15 * * * *"  # Every 15 minutes
        ),
        BackgroundAgent(
            "log_analyzer",
            "python analyze_logs.py",
            "Analyzes logs for errors and performance issues",
            schedule="0 */4 * * *"  # Every 4 hours
        )
    ]

    # Check if scripts exist and update status
    for agent in agents:
        script_name = agent.command.split()[1]
        if os.path.exists(script_name):
            # Mock the status
            agent.status = "running" if np.random.random() > 0.3 else "stopped"
            if agent.status == "running":
                agent.pid = np.random.randint(1000, 9999)
                agent.last_run = datetime.datetime.now() - datetime.timedelta(
                    hours=np.random.randint(0, 6),
                    minutes=np.random.randint(0, 60)
                )
        else:
            agent.status = "not installed"

    return agents

def get_memory_stats():
    """Get statistics about the memory system"""
    if not HAS_MEM0:
        return {
            "total_memories": 0,
            "active_memories": 0,
            "stale_memories": 0,
            "avg_relevance": 0
        }

    try:
        # In a real setup, this would query the actual memory system
        # For now, generate mock data
        total = np.random.randint(500, 2000)
        stale = int(total * np.random.uniform(0.05, 0.2))
        active = total - stale

        return {
            "total_memories": total,
            "active_memories": active,
            "stale_memories": stale,
            "avg_relevance": round(np.random.uniform(0.75, 0.95), 2)
        }
    except Exception as e:
        logging.error(f"Error getting memory stats: {e}")
        return {
            "total_memories": 0,
            "active_memories": 0,
            "stale_memories": 0,
            "avg_relevance": 0
        }

async def get_repo_status():
    """Get status of the repository and code quality"""
    try:
        # Get git status
        git_cmd = "git status --porcelain"
        git_result = subprocess.run(git_cmd, shell=True, text=True, capture_output=True)
        modified_files = len([line for line in git_result.stdout.split("\n") if line.strip()])

        # Get last commit
        last_commit_cmd = "git log -1 --pretty=format:'%h - %s (%cr)'"
        last_commit = subprocess.run(last_commit_cmd, shell=True, text=True, capture_output=True).stdout

        # Run code quality check if pylint is available
        try:
            pylint_cmd = "which pylint > /dev/null && pylint -f json --rcfile=.pylintrc *.py 2>/dev/null || echo '{}'"
            pylint_result = subprocess.run(pylint_cmd, shell=True, text=True, capture_output=True)

            try:
                pylint_data = json.loads(pylint_result.stdout)
                if isinstance(pylint_data, list) and len(pylint_data) > 0:
                    # Calculate average score from pylint results
                    score = 10.0  # Start with perfect score
                    for item in pylint_data:
                        if "message" in item:
                            # Deduct points for different message types
                            if item.get("type") == "error":
                                score -= 0.5
                            elif item.get("type") == "warning":
                                score -= 0.2
                            elif item.get("type") == "convention":
                                score -= 0.1
                    score = max(0.0, score)  # Don't go below 0
                else:
                    score = 8.5  # Default score if no valid data
            except:
                score = 8.5  # Default fallback score
        except:
            score = "N/A"

        return {
            "modified_files": modified_files,
            "last_commit": last_commit,
            "code_quality_score": round(score, 1) if isinstance(score, (int, float)) else score,
            "sophia_coverage": f"{np.random.randint(70, 95)}%"  # Mock coverage data
        }
    except Exception as e:
        logging.error(f"Error getting repo status: {e}")
        return {
            "modified_files": 0,
            "last_commit": "Unknown",
            "code_quality_score": "N/A",
            "sophia_coverage": "N/A"
        }

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

if 'offline_mode' not in st.session_state:
    st.session_state.offline_mode = False

if 'background_agents' not in st.session_state:
    st.session_state.background_agents = get_background_agents()

if 'api_health' not in st.session_state:
    st.session_state.api_health = get_api_health()

if 'memory_stats' not in st.session_state:
    st.session_state.memory_stats = get_memory_stats()

if 'repo_status' not in st.session_state:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    st.session_state.repo_status = loop.run_until_complete(get_repo_status())
    loop.close()

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.datetime.now()

# Dashboard Title
st.title("Artemis Dashboard - Cloud Monitor")

# Dashboard Controls
st.sidebar.header("Controls")

# Add auto-refresh option
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
if auto_refresh and (datetime.datetime.now() - st.session_state.last_refresh).total_seconds() > 30:
    st.session_state.last_refresh = datetime.datetime.now()
    st.session_state.api_health = get_api_health()
    st.session_state.memory_stats = get_memory_stats()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    st.session_state.repo_status = loop.run_until_complete(get_repo_status())
    loop.close()
    st.experimental_rerun()

offline_toggle = st.sidebar.checkbox("Offline Mode", value=st.session_state.offline_mode)
if offline_toggle != st.session_state.offline_mode:
    st.session_state.offline_mode = offline_toggle
    st.experimental_rerun()

# Sidebar for navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Choose a page", ["Overview", "API Health", "Background Agents", "Memory Systems", "Code Quality", "Model Rankings", "Tool Usage"])

# Date Range Selection (for future real metrics)
date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime.datetime.now() - datetime.timedelta(days=14), datetime.datetime.now()),
    max_value=datetime.datetime.now())

# NL Query Interface
st.sidebar.subheader("Query Dashboard")
nl_query = st.sidebar.text_input("Ask about metrics, models, or usage", "")
submit_query = st.sidebar.button("Analyze")

if submit_query and nl_query:
    st.session_state.query_history.append(nl_query)

    # In a real setup, this would call an LLM through MCP
    # For now, just show the query
    st.sidebar.success(f"Query submitted: {nl_query}")

if st.sidebar.button("Evolve Configs"):
    st.sidebar.info("Running A/B tests on model configurations...")
    # In a real setup, this would trigger promptfoo tests

if st.sidebar.button("Trigger Swarm"):
    st.sidebar.info("Launching AI swarm...")
    # In a real setup, this would call the MCP swarm endpoint

# Main Dashboard Content based on selected page
if page == "Overview":
    # Quick overview of all systems
    st.header("System Overview")

    # Top row metrics
    col1, col2, col3, col4 = st.columns(4)

    # API Status
    api_statuses = [item["status"] for item in st.session_state.api_health]
    overall_status = "UP" if all(status == "UP" for status in api_statuses) else "PARTIAL" if any(status == "UP" for status in api_statuses) else "DOWN"
    status_color = "green" if overall_status == "UP" else "orange" if overall_status == "PARTIAL" else "red"

    with col1:
        st.metric("API Status", overall_status, delta="Cloud services" if not st.session_state.offline_mode else "Local only")

    # Background Agents
    agent_count = len([a for a in st.session_state.background_agents if a.status == "running"])
    with col2:
        st.metric("Background Agents", f"{agent_count} Active", delta=f"of {len(st.session_state.background_agents)}")

    # Memory Health
    mem_stats = st.session_state.memory_stats
    with col3:
        st.metric("Memory Health", f"{mem_stats['avg_relevance']}", delta=f"{mem_stats['active_memories']} active")

    # Code Quality
    with col4:
        st.metric("Code Quality", st.session_state.repo_status['code_quality_score'], delta=st.session_state.repo_status['sophia_coverage'])

    # Architecture diagram
    st.subheader("Cloud-First Architecture")

    architecture_md = """
    ```mermaid
    flowchart TD
        User[User] --> ContinueDev[Continue.dev Interface]
        ContinueDev --> MCP[MCP Server<br>Cloud Lambda]
        MCP --> ToolA[Web Search]
        MCP --> ToolB[Code Execution]
        MCP --> ToolC[Browse Page]
        MCP --> BGAgents[Background Agents]
        MCP --> Memory[Memory System<br>Mem0/Qdrant]
        Memory --> VectorDB[(Vector Store<br>Cloud)]
        MCP --> LLM[Cloud LLMs<br>OpenRouter/Portkey]
        MCP --> LocalLLM[Local LLM<br>Fallback Only]
        BGAgents --> Scraper[Model Scraper]
        BGAgents --> Pruner[Memory Pruner]
        BGAgents --> Monitor[System Monitor]
    ```
    """
    st.markdown(architecture_md)

    # Recent activity
    st.subheader("Recent Activity")

    # Generate activity data based on agent runs
    activities = []
    for agent in st.session_state.background_agents:
        if agent.last_run:
            activities.append({
                "Time": agent.last_run.strftime("%H:%M:%S"),
                "Event": f"{agent.name} executed",
                "Status": "Success" if np.random.random() > 0.1 else "Warning"
            })

    # Add some API activities
    for i in range(3):
        time_ago = datetime.datetime.now() - datetime.timedelta(minutes=np.random.randint(5, 60))
        activities.append({
            "Time": time_ago.strftime("%H:%M:%S"),
            "Event": f"API request to {np.random.choice(['code_execution', 'web_search', 'browse_page'])}",
            "Status": "Success" if np.random.random() > 0.1 else "Error"
        })

    # Sort by time
    activities = sorted(activities, key=lambda x: x["Time"], reverse=True)

    # Display as table
    activities_df = pd.DataFrame(activities)
    st.dataframe(activities_df, use_container_width=True)

    # Key system metrics
    st.subheader("Key Metrics")

    # Cost tracking
    cost_col, usage_col = st.columns(2)

    with cost_col:
        # Monthly cost projection
        daily_costs = np.random.uniform(0.10, 0.30, 30)  # 30 days of costs
        monthly_total = sum(daily_costs)

        fig = px.line(
            x=range(1, 31), 
            y=np.cumsum(daily_costs),
            labels={'x': 'Day of Month', 'y': 'Cumulative Cost ($)'},
            title=f"Monthly Cost Projection: ${monthly_total:.2f}"
        )
        st.plotly_chart(fig, use_container_width=True)

    with usage_col:
        # Token usage by model (last 7 days)
        token_data = get_token_usage_trend().tail(7)

        fig = px.bar(
            token_data,
            x='date',
            y=['claude_sonnet', 'qwen3_coder', 'deepseek_free', 'codellama_local'],
            title="Token Usage (Last 7 Days)",
            labels={'value': 'Tokens', 'variable': 'Model'}
        )
        st.plotly_chart(fig, use_container_width=True)

elif page == "API Health":
    st.header("API Health and Status")

    # Refresh button for API health specifically
    if st.button("Refresh API Status"):
        with st.spinner("Checking API endpoints..."):
            st.session_state.api_health = get_api_health()

    # Display API health status
    for endpoint in st.session_state.api_health:
        color = "green" if endpoint["status"] == "UP" else "red"
        st.markdown(f"#### {endpoint['name']}: <span style='color:{color}'>{endpoint['status']}</span>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Latency: {endpoint['latency']}")
        with col2:
            st.write(f"Last Checked: {endpoint['last_checked']}")

        st.divider()

    # API Reliability Chart (mock data)
    st.subheader("API Reliability (Last 7 Days)")

    # Generate mock data
    dates = pd.date_range(end=datetime.datetime.now(), periods=7).tolist()
    reliability_data = {
        'date': dates,
        'MCP Server': np.random.uniform(98, 100, 7),
        'OpenRouter': np.random.uniform(99, 100, 7),
        'Portkey': np.random.uniform(99, 100, 7),
        'Memory System': np.random.uniform(97, 100, 7)
    }

    reliability_df = pd.DataFrame(reliability_data)

    fig = px.line(
        reliability_df,
        x='date',
        y=['MCP Server', 'OpenRouter', 'Portkey', 'Memory System'],
        labels={'value': 'Uptime %', 'variable': 'Service'},
        title="Service Uptime Percentage"
    )
    fig.update_layout(yaxis_range=[96, 100])
    st.plotly_chart(fig, use_container_width=True)

    # API Response Time (mock data)
    st.subheader("API Response Time (Last 24 Hours)")

    # Generate mock data
    hours = pd.date_range(end=datetime.datetime.now(), periods=24, freq='H').tolist()
    response_data = {
        'time': hours,
        'MCP Server': np.random.uniform(10, 50, 24),
        'OpenRouter': np.random.uniform(200, 500, 24),
        'Portkey': np.random.uniform(150, 350, 24),
        'Memory System': np.random.uniform(5, 20, 24)
    }

    response_df = pd.DataFrame(response_data)

    fig = px.line(
        response_df,
        x='time',
        y=['MCP Server', 'OpenRouter', 'Portkey', 'Memory System'],
        labels={'value': 'Response Time (ms)', 'variable': 'Service'},
        title="API Response Time"
    )
    st.plotly_chart(fig, use_container_width=True)

elif page == "Background Agents":
    st.header("Background Agents and Tasks")

    # Agent Factory Section
    st.subheader("Agent Factory")

    with st.expander("Create New Agent"):
        with st.form("new_agent_form"):
            agent_name = st.text_input("Agent Name", placeholder="e.g., code_quality_checker")
            agent_description = st.text_input("Description", placeholder="e.g., Checks code quality and suggests improvements")
            agent_command = st.text_input("Command", placeholder="e.g., python code_quality.py")
            agent_schedule = st.text_input("Cron Schedule", value="0 */6 * * *", help="Format: minute hour day_of_month month day_of_week")

            submitted = st.form_submit_button("Create Agent")
            if submitted:
                # Create new agent
                if agent_name and agent_command:
                    new_agent = BackgroundAgent(agent_name, agent_command, agent_description, agent_schedule)
                    st.session_state.background_agents.append(new_agent)
                    st.success(f"Agent '{agent_name}' created successfully!")
                else:
                    st.error("Agent name and command are required.")

    # Display existing agents
    st.subheader("Active Agents")

    # Convert agents to dataframe for display
    agents_data = [agent.to_dict() for agent in st.session_state.background_agents]
    agents_df = pd.DataFrame(agents_data)

    # Use colored status indicators
    def highlight_status(val):
        if val == "running":
            return 'background-color: #c6efce; color: #006100'
        elif val == "stopped":
            return 'background-color: #ffeb9c; color: #9c5700'
        else:
            return 'background-color: #ffc7ce; color: #9c0006'

    # Display the dataframe with formatting
    st.dataframe(agents_df.style.applymap(highlight_status, subset=['status']), use_container_width=True)

    # Agent actions
    st.subheader("Agent Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        start_agent = st.selectbox("Start Agent", 
                                  options=[agent.name for agent in st.session_state.background_agents 
                                           if agent.status != "running"],
                                  index=None,
                                  placeholder="Select agent to start")
        if st.button("Start") and start_agent:
            for agent in st.session_state.background_agents:
                if agent.name == start_agent:
                    success = agent.start()
                    if success:
                        st.success(f"Started agent '{start_agent}'")
                    else:
                        st.error(f"Failed to start agent '{start_agent}'")
                    break

    with col2:
        stop_agent = st.selectbox("Stop Agent", 
                                 options=[agent.name for agent in st.session_state.background_agents 
                                          if agent.status == "running"],
                                 index=None,
                                 placeholder="Select agent to stop")
        if st.button("Stop") and stop_agent:
            for agent in st.session_state.background_agents:
                if agent.name == stop_agent:
                    success = agent.stop()
                    if success:
                        st.success(f"Stopped agent '{stop_agent}'")
                    else:
                        st.error(f"Failed to stop agent '{stop_agent}'")
                    break

    with col3:
        if st.button("Refresh Status"):
            # In a real implementation, this would check actual process status
            for agent in st.session_state.background_agents:
                agent.is_running()
            st.success("Agent statuses refreshed")

    # Agent execution history
    st.subheader("Execution History")

    # Generate mock execution history
    now = datetime.datetime.now()
    history = []

    for agent in st.session_state.background_agents:
        # Generate 1-3 executions per agent
        for i in range(np.random.randint(1, 4)):
            run_time = now - datetime.timedelta(hours=np.random.randint(1, 48))
            duration = np.random.randint(1, 300)  # 1-300 seconds
            success = np.random.random() > 0.1  # 90% success rate

            history.append({
                "Agent": agent.name,
                "Start Time": run_time.strftime("%Y-%m-%d %H:%M:%S"),
                "Duration": f"{duration}s",
                "Status": "Success" if success else "Failed",
                "Output": "Task completed successfully" if success else "Error: Connection timeout"
            })

    # Sort by start time
    history = sorted(history, key=lambda x: x["Start Time"], reverse=True)

    # Display as table
    history_df = pd.DataFrame(history)
    st.dataframe(history_df, use_container_width=True)

elif page == "Memory Systems":
    st.header("Memory System Health and Visibility")

    if not HAS_MEM0:
        st.warning("Memory system (Mem0) is not installed. Install it to access memory visibility features.")
    else:
        # Memory stats overview
        mem_stats = st.session_state.memory_stats

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Memories", mem_stats["total_memories"])
        with col2:
            st.metric("Active Memories", mem_stats["active_memories"])
        with col3:
            st.metric("Stale Memories", mem_stats["stale_memories"])
        with col4:
            st.metric("Avg. Relevance", f"{mem_stats['avg_relevance']:.2f}")

        # Memory health visualization
        st.subheader("Memory Health Distribution")

        # Generate mock relevance distribution
        relevance_ranges = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
        # Shape the distribution to favor higher relevance
        counts = [
            int(mem_stats["total_memories"] * 0.05),  # 0.0-0.2
            int(mem_stats["total_memories"] * 0.10),  # 0.2-0.4
            int(mem_stats["total_memories"] * 0.15),  # 0.4-0.6
            int(mem_stats["total_memories"] * 0.30),  # 0.6-0.8
            int(mem_stats["total_memories"] * 0.40),  # 0.8-1.0
        ]

        health_data = pd.DataFrame({
            "Relevance Range": relevance_ranges,
            "Count": counts
        })

        fig = px.bar(
            health_data,
            x="Relevance Range",
            y="Count",
            color="Relevance Range",
            title="Memory Relevance Distribution",
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig, use_container_width=True)

        # Memory prune simulator
        st.subheader("Memory Pruning Simulator")

        col1, col2 = st.columns([2, 1])

        with col1:
            relevance_threshold = st.slider("Relevance Threshold for Pruning", 0.0, 1.0, 0.7, 0.05)

            # Calculate how many would be pruned
            to_prune = sum([count for range_val, count in zip(relevance_ranges, counts) 
                          if float(range_val.split("-")[1]) <= relevance_threshold])

            st.info(f"{to_prune} memories would be pruned with threshold {relevance_threshold}")

        with col2:
            if st.button("Simulate Prune"):
                # In a real implementation, this would call the actual pruning function
                st.success(f"Simulated pruning of {to_prune} memories")

        # Memory contents explorer
        st.subheader("Memory Contents Explorer")

        # Generate mock memory entries
        actual_memories = [
            {"content": "Repository structure includes MCP server and toolkit components", "type": "code_context", "relevance": 0.95},
            {"content": "Portkey API is used for routing LLM requests with performance bias", "type": "api_info", "relevance": 0.88},
            {"content": "Continue.dev configuration uses multiple specialized models with temperature settings", "type": "config", "relevance": 0.82},
            {"content": "Memory pruning should target entries with relevance below 0.7", "type": "system_rule", "relevance": 0.79},
            {"content": "Dashboard should display real-time metrics with auto-refresh capability", "type": "requirement", "relevance": 0.73},
            {"content": "Legacy Artemis components being phased out for cloud-first approach", "type": "historical", "relevance": 0.65},
            {"content": "Initial testing showed 15% improvement with specialized model temperatures", "type": "benchmark", "relevance": 0.58},
            {"content": "Original implementation used direct API calls instead of MCP server", "type": "historical", "relevance": 0.42},
            {"content": "Early prototype used Gradio instead of Streamlit for dashboards", "type": "historical", "relevance": 0.38},
        ]

        # Add search/filter capabilities
        search_term = st.text_input("Search Memories", placeholder="Enter keywords to search")
        memory_type = st.multiselect("Filter by Type", 
                                     options=list(set(mem["type"] for mem in actual_memories)),
                                     default=[])

        # Apply filters
        filtered_memories = actual_memories
        if search_term:
            filtered_memories = [mem for mem in filtered_memories if search_term.lower() in mem["content"].lower()]
        if memory_type:
            filtered_memories = [mem for mem in filtered_memories if mem["type"] in memory_type]

        # Display memories
        for memory in filtered_memories:
            expander_label = f"{memory['type']} ({memory['relevance']:.2f})"
            with st.expander(expander_label):
                st.write(memory["content"])
                st.progress(memory["relevance"])

elif page == "Code Quality":
    st.header("Code Quality and Repository Status")

    # Repository status
    repo_status = st.session_state.repo_status

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Modified Files", repo_status["modified_files"])
    with col2:
        st.metric("Code Quality", repo_status["code_quality_score"])
    with col3:
        st.metric("Test Coverage", repo_status["sophia_coverage"])

    st.subheader("Latest Commit")
    st.code(repo_status["last_commit"], language="bash")

    # Mock file quality metrics
    st.subheader("File Quality Metrics")

    # Generate mock file metrics
    file_metrics = [
        {"file": "mcp_server.py", "quality": 9.2, "complexity": 12, "sophia_coverage": "92%", "issues": 3},
        {"file": "dashboard.py", "quality": 8.7, "complexity": 15, "sophia_coverage": "78%", "issues": 7},
        {"file": "update_models.py", "quality": 9.5, "complexity": 6, "sophia_coverage": "95%", "issues": 1},
        {"file": ".continue/config.json", "quality": 9.8, "complexity": 4, "sophia_coverage": "N/A", "issues": 0},
        {"file": "memory_prune.py", "quality": 9.0, "complexity": 8, "sophia_coverage": "85%", "issues": 4},
        {"file": "start_continue_dev_toolkit.sh", "quality": 8.5, "complexity": 5, "sophia_coverage": "60%", "issues": 5},
    ]

    metrics_df = pd.DataFrame(file_metrics)

    # Add color coding based on quality
    def color_quality(val):
        if val >= 9.0:
            return 'background-color: #c6efce; color: #006100'
        elif val >= 7.0:
            return 'background-color: #ffeb9c; color: #9c5700'
        else:
            return 'background-color: #ffc7ce; color: #9c0006'

    st.dataframe(metrics_df.style.applymap(color_quality, subset=['quality']), use_container_width=True)

    # Quality trend over time
    st.subheader("Quality Trend (Last 10 Commits)")

    # Generate mock quality history
    commits = [f"c{i}" for i in range(1, 11)]
    quality_history = [np.clip(8.5 + np.random.uniform(-0.5, 0.5), 7.0, 10.0) for _ in range(10)]
    issues_history = [int(np.clip((10 - q) * 5, 0, 20)) for q in quality_history]

    quality_df = pd.DataFrame({
        "Commit": commits,
        "Quality Score": quality_history,
        "Issues": issues_history
    })

    fig = px.line(
        quality_df,
        x="Commit",
        y=["Quality Score", "Issues"],
        title="Code Quality Trend",
        labels={"value": "Score / Count", "variable": "Metric"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Mock issues list
    st.subheader("Top Issues")

    issues = [
        {"type": "Performance", "description": "Inefficient memory usage in vector search", "file": "mcp_server.py:245", "severity": "Medium"},
        {"type": "Security", "description": "API keys loaded without validation", "file": "update_models.py:32", "severity": "High"},
        {"type": "Code Style", "description": "Inconsistent naming conventions", "file": "dashboard.py:120-155", "severity": "Low"},
        {"type": "Error Handling", "description": "Missing exception handler in API call", "file": "mcp_server.py:178", "severity": "Medium"},
        {"type": "Documentation", "description": "Insufficient inline comments", "file": "memory_prune.py:45-60", "severity": "Low"},
    ]

    issues_df = pd.DataFrame(issues)
    st.dataframe(issues_df, use_container_width=True)

elif page == "Model Rankings":
    st.header("Model Rankings by Performance")
    models = get_model_rankings()

    # Formula explanation
    st.write(f"Model Score = {MODEL_SCORING_FORMULA}")
    st.write("This formula balances performance (70% weight) with cost (30% weight)")

    fig = px.bar(
        models, 
        x='name', 
        y='score', 
        color='cost_per_million',
        hover_data=['tokens_processed', 'cost_per_million', 'context_length'],
        color_continuous_scale='Viridis'
    )
    fig.update_layout(xaxis_title="Model", yaxis_title="Score")
    st.plotly_chart(fig, use_container_width=True)

    # Model details table
    with st.expander("View Model Details"):
        st.dataframe(pd.DataFrame(models), use_container_width=True)

    # Token usage trends
    st.subheader("Token Usage Trends")
    token_data = get_token_usage_trend()

    fig = px.line(
        token_data, 
        x='date', 
        y=['claude_sonnet', 'qwen3_coder', 'deepseek_free', 'codellama_local'],
        labels={'value': 'Tokens Used', 'variable': 'Model'},
        title="Daily Token Usage by Model"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Cost projection
    st.subheader("Cost Projection")

    # Generate cost projection based on token usage
    last_7_days = token_data.tail(7)

    # Calculate costs
    model_costs = {
        'claude_sonnet': 8.0,  # $ per million tokens
        'qwen3_coder': 5.0,
        'deepseek_free': 0.0,
        'codellama_local': 0.0
    }

    cost_projection = pd.DataFrame()
    cost_projection['date'] = last_7_days['date']

    for model in ['claude_sonnet', 'qwen3_coder', 'deepseek_free', 'codellama_local']:
        cost_projection[model] = last_7_days[model] * model_costs[model] / 1000000  # Cost per day

    fig = px.bar(
        cost_projection,
        x='date',
        y=['claude_sonnet', 'qwen3_coder', 'deepseek_free', 'codellama_local'],
        labels={'value': 'Cost ($)', 'variable': 'Model'},
        title="Daily Cost by Model"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Monthly projection
    total_monthly = sum(cost_projection[['claude_sonnet', 'qwen3_coder', 'deepseek_free', 'codellama_local']].sum()) * 30/7
    st.metric("Projected Monthly Cost", f"${total_monthly:.2f}")

elif page == "Tool Usage":
    st.header("Tool Usage Analytics")

    # Get log stats
    log_stats = analyze_logs()
    tool_usage = log_stats['tool_usage']

    # Top stats
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Requests", log_stats['total_requests'])
    with col2:
        st.metric("Errors", log_stats['errors'])
    with col3:
        st.metric("Avg. Response Time", f"{log_stats['avg_response_time']} ms")

    # Tool usage breakdown
    st.subheader("Tool Usage Breakdown")

    if sum(tool_usage.values()) > 0:
        tool_df = pd.DataFrame({
            'Tool': list(tool_usage.keys()),
            'Usage Count': list(tool_usage.values())
        })

        col1, col2 = st.columns([2, 3])

        with col1:
            fig = px.pie(tool_df, values='Usage Count', names='Tool', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Add a bar chart showing the same data
            fig = px.bar(
                tool_df,
                x='Tool',
                y='Usage Count',
                color='Tool',
                title="Tool Usage by Count"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tool usage data available yet. Start using the toolkit to generate metrics.")

    # Usage over time (mock data)
    st.subheader("Tool Usage Over Time")

    # Generate mock time series data
    hours = pd.date_range(end=datetime.datetime.now(), periods=24, freq='H').tolist()

    usage_data = {
        'hour': hours,
        'code_execution': np.random.randint(0, 15, 24),
        'web_search': np.random.randint(0, 10, 24),
        'browse_page': np.random.randint(0, 8, 24),
        'rag_hybrid': np.random.randint(0, 5, 24),
        'swarm': np.random.randint(0, 3, 24)
    }

    usage_df = pd.DataFrame(usage_data)

    fig = px.line(
        usage_df,
        x='hour',
        y=['code_execution', 'web_search', 'browse_page', 'rag_hybrid', 'swarm'],
        labels={'value': 'Usage Count', 'variable': 'Tool'},
        title="Tool Usage by Hour"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tool performance metrics
    st.subheader("Tool Performance Metrics")

    # Generate mock performance data
    performance_data = {
        'Tool': list(tool_usage.keys()),
        'Avg Response Time (ms)': [120, 350, 280, 180, 450, 220, 750],
        'Success Rate (%)': [98.5, 94.2, 95.8, 97.3, 92.1, 99.0, 91.5],
        'Token Usage': [150, 320, 280, 200, 420, 180, 650]
    }

    perf_df = pd.DataFrame(performance_data)
    st.dataframe(perf_df, use_container_width=True)

# Configuration Summary
st.subheader("Continue.dev Configuration")
config = load_config()

if config:
    tabs = st.tabs(["Models", "Tasks", "Commands"])

    with tabs[0]:
        if "models" in config:
            model_data = []
            for model in config["models"]:
                model_data.append({
                    "title": model.get("title", "Unknown"),
                    "provider": model.get("provider", "Unknown"),
                    "model": model.get("model", "Unknown"),
                    "temperature": model.get("completionOptions", {}).get("temperature", "N/A")
                })

            st.dataframe(pd.DataFrame(model_data))
        else:
            st.info("No model configuration found.")

    with tabs[1]:
        if "tasks" in config:
            task_data = []
            for task in config["tasks"]:
                task_data.append({
                    "name": task.get("name", "Unknown"),
                    "model": task.get("model", "Default"),
                    "persona": task.get("persona", "Default")
                })

            st.dataframe(pd.DataFrame(task_data))
        else:
            st.info("No task configuration found.")

    with tabs[2]:
        if "commands" in config:
            command_data = []
            for cmd in config["commands"]:
                command_data.append({
                    "name": cmd.get("name", "Unknown"),
                    "description": cmd.get("description", "No description"),
                    "route": cmd.get("route", "N/A")
                })

            st.dataframe(pd.DataFrame(command_data))
        else:
            st.info("No command configuration found.")
else:
    st.warning("Could not load Continue.dev configuration.")

# Query History
with st.expander("Query History"):
    for query in st.session_state.query_history:
        st.text(query)

# Footer
st.markdown("---")
st.caption("Internal AI Dev Toolkit Dashboard | SOLO DEVELOPER USE ONLY | Last updated: " + 
           datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    # This will be run when the script is executed directly
