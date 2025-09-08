"""
Sophia AI Chat Dashboard - Streamlit Interface
Natural language chat interface with ASIP integration
"""

import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Sophia AI Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .stChat {
        height: 600px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .gpu-status {
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .gpu-online {
        background-color: #d4edda;
        color: #155724;
    }
    .gpu-offline {
        background-color: #f8d7da;
        color: #721c24;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().timestamp()}"
if "metrics" not in st.session_state:
    st.session_state.metrics = {
        "total_messages": 0,
        "avg_response_time": 0,
        "cache_hits": 0,
        "gpu_usage": {},
    }

# API Configuration
ASIP_BRIDGE_URL = os.getenv("ASIP_BRIDGE_URL", "http://localhost:8100")


def call_asip_chat(message: str, context: dict = None) -> dict:
    """Call ASIP Chat Bridge API"""
    try:
        response = requests.post(
            f"{ASIP_BRIDGE_URL}/chat",
            json={
                "message": message,
                "context": context or {},
                "session_id": st.session_state.session_id,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "response": f"Error connecting to ASIP Bridge: {e!s}",
            "metadata": {"error": True},
        }


def get_metrics() -> dict:
    """Get metrics from ASIP Bridge"""
    try:
        response = requests.get(f"{ASIP_BRIDGE_URL}/metrics", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:return {"cache_size": 0, "gpu_loads": {}, "active_sessions": 0}


# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # Execution Mode Selection
    execution_mode = st.selectbox(
        "Execution Mode",
        ["Auto", "Reactive", "Deliberative", "Symbiotic"],
        help="Select the ASIP execution mode",
    )

    # GPU Instance Selection
    gpu_instance = st.selectbox(
        "GPU Instance",
        [
            "Auto",
            "GH200 (141GB)",
            "A100 (80GB)",
            "RTX6000 (24GB)",
            "A6000 (48GB)",
            "A10 (24GB)",
        ],
        help="Select the Lambda Labs GPU instance",
    )

    # Priority Level
    priority = st.select_slider(
        "Priority",
        options=["low", "normal", "high", "critical"],
        value="normal",
        help="Set the request priority",
    )

    st.divider()

    # System Metrics
    st.header("📊 System Metrics")

    metrics = get_metrics()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Cache Size", metrics.get("cache_size", 0))
    with col2:
        st.metric("Active Sessions", metrics.get("active_sessions", 0))

    # GPU Status
    st.subheader("GPU Status")
    gpu_loads = metrics.get("gpu_loads", {})

    for gpu_name, load in gpu_loads.items():
        status_class = "gpu-online" if load < 80 else "gpu-offline"
        st.markdown(
            f"""
            <div class="gpu-status {status_class}">
                <strong>{gpu_name.upper()}</strong>: {load}% load
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.divider()

    # Session Info
    st.header("📝 Session Info")
    st.code(st.session_state.session_id[:20] + "...", language="text")
    st.metric("Messages", len(st.session_state.messages))

    # Clear Chat Button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = f"session_{datetime.now().timestamp()}"
        st.rerun()

# Main Chat Interface
st.title("🤖 Sophia AI Natural Chat")
st.caption("Powered by ASIP Orchestrator and Lambda Labs GPUs")

# Create tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📈 Analytics", "🔍 Debug"])

with tab1:
    # Display chat messages
    chat_container = st.container(height=500)

    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(
                message["role"], avatar="🧑" if message["role"] == "user" else "🤖"
            ):
                st.markdown(message["content"])

                # Show metadata for assistant messages
                if message["role"] == "assistant" and "metadata" in message:
                    metadata = message["metadata"]
                    with st.expander("Details", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Execution Mode", metadata.get("execution_mode", "N/A")
                            )
                        with col2:
                            st.metric("GPU", metadata.get("gpu_instance", "N/A"))
                        with col3:
                            st.metric(
                                "Response Time",
                                f"{metadata.get('processing_time', 0):.2f}s",
                            )

                        st.json(metadata)

    # Chat input
    if prompt := st.chat_input("Ask me anything...", key="chat_input"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get context
        context = {
            "execution_mode": (
                execution_mode.lower() if execution_mode != "Auto" else None
            ),
            "gpu_instance": (
                gpu_instance.split()[0].lower() if gpu_instance != "Auto" else None
            ),
            "priority": priority,
        }

        # Get AI response
        with st.spinner("Thinking..."):
            response_data = call_asip_chat(prompt, context)

        # Add assistant message
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response_data.get("response", "No response"),
                "metadata": response_data.get("metadata", {}),
            }
        )

        # Update metrics
        st.session_state.metrics["total_messages"] += 1
        if response_data.get("metadata", {}).get("processing_time"):
            current_avg = st.session_state.metrics["avg_response_time"]
            new_time = response_data["metadata"]["processing_time"]
            total = st.session_state.metrics["total_messages"]
            st.session_state.metrics["avg_response_time"] = (
                current_avg * (total - 1) + new_time
            ) / total

        st.rerun()

with tab2:
    st.header("📈 Performance Analytics")

    # Create metrics cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Messages", st.session_state.metrics["total_messages"], delta=None
        )

    with col2:
        st.metric(
            "Avg Response Time",
            f"{st.session_state.metrics['avg_response_time']:.2f}s",
            delta=None,
        )

    with col3:
        cache_hit_rate = 0
        if st.session_state.metrics["total_messages"] > 0:
            cache_hit_rate = (
                st.session_state.metrics["cache_hits"]
                / st.session_state.metrics["total_messages"]
            ) * 100
        st.metric("Cache Hit Rate", f"{cache_hit_rate:.1f}%", delta=None)

    with col4:
        st.metric("Active GPUs", len(metrics.get("gpu_loads", {})), delta=None)

    # Response Time Chart
    if len(st.session_state.messages) > 0:
        response_times = []
        message_indices = []

        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "assistant" and "metadata" in msg:
                if "processing_time" in msg["metadata"]:
                    response_times.append(msg["metadata"]["processing_time"])
                    message_indices.append(i)

        if response_times:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=message_indices,
                    y=response_times,
                    mode="lines+markers",
                    name="Response Time",
                    line=dict(color="#1f77b4", width=2),
                    marker=dict(size=8),
                )
            )

            fig.update_layout(
                title="Response Time Trend",
                xaxis_title="Message Index",
                yaxis_title="Response Time (seconds)",
                height=400,
                showlegend=False,
            )

            st.plotly_chart(fig, use_container_width=True)

    # GPU Usage Distribution
    if gpu_loads:
        gpu_df = pd.DataFrame(list(gpu_loads.items()), columns=["GPU", "Load %"])

        fig = px.bar(
            gpu_df,
            x="GPU",
            y="Load %",
            title="GPU Load Distribution",
            color="Load %",
            color_continuous_scale="RdYlGn_r",
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("🔍 Debug Information")

    # Session State Debug
    with st.expander("Session State", expanded=False):
        st.json(
            {
                "session_id": st.session_state.session_id,
                "message_count": len(st.session_state.messages),
                "metrics": st.session_state.metrics,
            }
        )

    # Last Response Debug
    if st.session_state.messages:
        last_assistant_msg = None
        for msg in reversed(st.session_state.messages):
            if msg["role"] == "assistant":
                last_assistant_msg = msg
                break

        if last_assistant_msg and "metadata" in last_assistant_msg:
            with st.expander("Last Response Metadata", expanded=True):
                st.json(last_assistant_msg["metadata"])

    # API Health Check
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Check ASIP Bridge Health"):
            try:
                response = requests.get(f"{ASIP_BRIDGE_URL}/", timeout=5)
                st.success("✅ ASIP Bridge is healthy")
                st.json(response.json())
            except Exception:st.error("❌ ASIP Bridge is not responding")

    with col2:
        if st.button("Refresh Metrics"):
            metrics = get_metrics()
            st.success("✅ Metrics refreshed")
            st.json(metrics)

    # Configuration Display
    with st.expander("Current Configuration", expanded=False):
        st.json(
            {
                "execution_mode": execution_mode,
                "gpu_instance": gpu_instance,
                "priority": priority,
                "asip_bridge_url": ASIP_BRIDGE_URL,
            }
        )

# Footer
st.divider()
st.caption(
    "Sophia AI Chat Interface - Powered by ASIP Architecture and Lambda Labs Infrastructure"
)
