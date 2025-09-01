"""
Streamlit Chat UI for Natural Language Interface
Simple chat interface for testing NL commands and workflows
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List


# Page configuration
st.set_page_config(
    page_title="Sophia Intel AI - NL Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = "http://localhost:8003"


# ============================================
# Helper Functions
# ============================================

def process_nl_command(text: str, session_id: str = None) -> Dict[str, Any]:
    """Process natural language command via API"""
    try:
        response = requests.post(
            f"{st.session_state.api_base_url}/api/nl/process",
            json={
                "text": text,
                "context": {},
                "session_id": session_id
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"API Error: {response.status_code}",
                "response_text": f"Failed to process command: {response.text}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_text": f"Error connecting to API: {str(e)}"
        }


def get_system_status() -> Dict[str, Any]:
    """Get system status"""
    try:
        response = requests.get(
            f"{st.session_state.api_base_url}/api/nl/system/status",
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to get status"}
    except Exception as e:
        return {"error": str(e)}


def get_available_intents() -> List[Dict[str, Any]]:
    """Get available intents from API"""
    try:
        response = requests.get(
            f"{st.session_state.api_base_url}/api/nl/intents",
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        st.error(f"Failed to load intents: {e}")
        return []


def get_agent_status(session_id: str) -> Dict[str, Any]:
    """Get agent execution status"""
    try:
        response = requests.get(
            f"{st.session_state.api_base_url}/api/nl/agents/status/{session_id}",
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "No status available"}
    except Exception as e:
        return {"error": str(e)}


# ============================================
# Sidebar
# ============================================

with st.sidebar:
    st.title("🤖 Sophia Intel AI")
    st.subheader("Natural Language Interface")
    
    # API Configuration
    st.divider()
    st.markdown("### API Configuration")
    api_url = st.text_input(
        "API Base URL",
        value=st.session_state.api_base_url,
        help="Base URL for the API server"
    )
    if api_url != st.session_state.api_base_url:
        st.session_state.api_base_url = api_url
    
    # System Status
    st.divider()
    st.markdown("### System Status")
    
    if st.button("🔄 Refresh Status"):
        status = get_system_status()
        st.session_state.system_status = status
    
    if "system_status" in st.session_state:
        status = st.session_state.system_status
        
        if "services" in status:
            for service, state in status["services"].items():
                if state == "running":
                    st.success(f"✅ {service}: {state}")
                elif state == "offline":
                    st.error(f"❌ {service}: {state}")
                else:
                    st.warning(f"⚠️ {service}: {state}")
        
        if "health" in status:
            health_color = "green" if status["health"] == "healthy" else "orange"
            st.markdown(f"**Overall Health:** :{health_color}[{status['health']}]")
    
    # Available Commands
    st.divider()
    st.markdown("### Available Commands")
    
    if st.button("📚 Load Commands"):
        intents = get_available_intents()
        st.session_state.intents = intents
    
    if "intents" in st.session_state:
        with st.expander("View Commands", expanded=False):
            for intent in st.session_state.intents:
                st.markdown(f"**{intent['name']}**")
                st.markdown(f"*{intent['description']}*")
                st.markdown("Examples:")
                for example in intent.get('examples', [])[:2]:
                    st.code(example, language=None)
                st.divider()
    
    # Session Info
    st.divider()
    st.markdown("### Session Info")
    if st.session_state.session_id:
        st.info(f"Session: {st.session_state.session_id[:8]}...")
        
        if st.button("📊 Get Agent Status"):
            agent_status = get_agent_status(st.session_state.session_id)
            st.json(agent_status)
    else:
        st.warning("No active session")
    
    # Clear Chat
    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()


# ============================================
# Main Chat Interface
# ============================================

st.title("💬 Natural Language Interface Chat")
st.markdown("Enter natural language commands to interact with the system")

# Quick Commands
st.markdown("### Quick Commands")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 System Status"):
        st.session_state.quick_command = "show system status"

with col2:
    if st.button("🤖 List Agents"):
        st.session_state.quick_command = "list all agents"

with col3:
    if st.button("📈 Get Metrics"):
        st.session_state.quick_command = "show metrics"

with col4:
    if st.button("❓ Help"):
        st.session_state.quick_command = "help"

# Process quick command if selected
if "quick_command" in st.session_state and st.session_state.quick_command:
    command = st.session_state.quick_command
    st.session_state.quick_command = None
    
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": command,
        "timestamp": datetime.now().isoformat()
    })
    
    # Process command
    result = process_nl_command(command, st.session_state.session_id)
    
    # Update session ID
    if result.get("session_id"):
        st.session_state.session_id = result["session_id"]
    
    # Add assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": result.get("response_text", "Command processed"),
        "intent": result.get("intent", "unknown"),
        "confidence": result.get("confidence", 0),
        "timestamp": datetime.now().isoformat()
    })
    
    st.rerun()

st.divider()

# Chat Messages Container
chat_container = st.container()

with chat_container:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Show additional info for assistant messages
            if message["role"] == "assistant":
                col1, col2, col3 = st.columns(3)
                with col1:
                    if "intent" in message:
                        st.caption(f"Intent: {message['intent']}")
                with col2:
                    if "confidence" in message:
                        st.caption(f"Confidence: {message['confidence']:.2f}")
                with col3:
                    if "timestamp" in message:
                        st.caption(f"Time: {message['timestamp'].split('T')[1].split('.')[0]}")

# Chat Input
if prompt := st.chat_input("Enter a command (e.g., 'show system status', 'run agent researcher')"):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now().isoformat()
    })
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Process the command
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            result = process_nl_command(prompt, st.session_state.session_id)
        
        # Update session ID
        if result.get("session_id"):
            st.session_state.session_id = result["session_id"]
        
        # Display response
        response_text = result.get("response_text", "Command processed")
        st.write(response_text)
        
        # Show additional info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"Intent: {result.get('intent', 'unknown')}")
        with col2:
            st.caption(f"Confidence: {result.get('confidence', 0):.2f}")
        with col3:
            st.caption(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        
        # Add to messages
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "intent": result.get("intent", "unknown"),
            "confidence": result.get("confidence", 0),
            "timestamp": datetime.now().isoformat()
        })

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <small>
            Sophia Intel AI - Natural Language Interface v1.0<br>
            Phase 2 Week 3-4 Implementation
        </small>
    </div>
    """,
    unsafe_allow_html=True
)

# Debug Info (collapsible)
with st.expander("🔍 Debug Info", expanded=False):
    st.markdown("### Current Session State")
    st.json({
        "session_id": st.session_state.session_id,
        "api_base_url": st.session_state.api_base_url,
        "message_count": len(st.session_state.messages),
        "last_message": st.session_state.messages[-1] if st.session_state.messages else None
    })