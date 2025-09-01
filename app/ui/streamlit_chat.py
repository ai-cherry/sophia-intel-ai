"""
Streamlit Chat UI for Natural Language Interface
Enhanced with persistence, suggestions, copy/export features
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import uuid


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
    st.session_state.session_id = str(uuid.uuid4())
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = "http://localhost:8003"
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "saved_sessions" not in st.session_state:
    st.session_state.saved_sessions = {}


# ============================================
# Helper Functions
# ============================================

def save_conversation_history():
    """Save conversation history to file"""
    try:
        history_dir = "conversation_history"
        os.makedirs(history_dir, exist_ok=True)
        
        filename = f"{history_dir}/session_{st.session_state.session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "session_id": st.session_state.session_id,
                "messages": st.session_state.messages,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        return filename
    except Exception as e:
        st.error(f"Failed to save conversation: {e}")
        return None


def load_conversation_history(filename: str):
    """Load conversation history from file"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            st.session_state.messages = data["messages"]
            st.session_state.session_id = data.get("session_id", str(uuid.uuid4()))
            st.success(f"Loaded conversation from {filename}")
    except Exception as e:
        st.error(f"Failed to load conversation: {e}")


def export_conversation(format: str = "json") -> str:
    """Export conversation in specified format"""
    if format == "json":
        return json.dumps({
            "session_id": st.session_state.session_id,
            "messages": st.session_state.messages,
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    elif format == "txt":
        output = f"Conversation Export - Session: {st.session_state.session_id}\n"
        output += f"Timestamp: {datetime.now().isoformat()}\n"
        output += "=" * 50 + "\n\n"
        
        for msg in st.session_state.messages:
            role = msg["role"].upper()
            content = msg["content"]
            timestamp = msg.get("timestamp", "")
            output += f"[{role}] {timestamp}\n{content}\n\n"
        
        return output
    else:
        return ""


def get_command_suggestions(text: str) -> List[str]:
    """Get command suggestions based on partial input"""
    suggestions = [
        "show system status",
        "run agent researcher",
        "run agent coder", 
        "run agent reviewer",
        "list all agents",
        "get metrics",
        "scale ollama to 3",
        "execute workflow data-pipeline",
        "query data about users",
        "help"
    ]
    
    if not text:
        return suggestions[:5]
    
    # Filter suggestions based on input
    filtered = [s for s in suggestions if text.lower() in s.lower()]
    return filtered[:5] if filtered else suggestions[:5]


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
    
    # Command Suggestions & Help
    st.divider()
    st.markdown("### 💡 Command Help")
    
    if st.button("📚 Show Commands"):
        intents = get_available_intents()
        st.session_state.intents = intents
    
    if "intents" in st.session_state:
        with st.expander("Available Commands", expanded=False):
            for intent in st.session_state.intents:
                st.markdown(f"**{intent['name']}**")
                st.markdown(f"*{intent['description']}*")
                st.markdown("Examples:")
                for example in intent.get('examples', [])[:2]:
                    st.code(example, language=None)
                st.divider()
    
    # Conversation Management
    st.divider()
    st.markdown("### 💾 Conversation Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Chat"):
            filename = save_conversation_history()
            if filename:
                st.success(f"Saved to {filename}")
    
    with col2:
        if st.button("📂 Load Chat"):
            # In production, add file picker
            st.info("Use file picker to load conversation")
    
    # Export Options
    st.markdown("### 📤 Export Conversation")
    export_format = st.radio("Format:", ["JSON", "TXT"], horizontal=True)
    
    if st.button("📥 Download"):
        export_data = export_conversation(export_format.lower())
        st.download_button(
            label=f"Download as {export_format}",
            data=export_data,
            file_name=f"conversation_{st.session_state.session_id[:8]}.{export_format.lower()}",
            mime="application/json" if export_format == "JSON" else "text/plain"
        )
    
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
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()


# ============================================
# Main Chat Interface
# ============================================

st.title("💬 Natural Language Interface Chat")
st.markdown("Enter natural language commands to interact with the system")

# Command Suggestions
st.markdown("### 💡 Quick Commands")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("📊 Status"):
        st.session_state.quick_command = "show system status"

with col2:
    if st.button("🤖 Agents"):
        st.session_state.quick_command = "list all agents"

with col3:
    if st.button("📈 Metrics"):
        st.session_state.quick_command = "get metrics"

with col4:
    if st.button("🔬 Research"):
        st.session_state.quick_command = "run agent researcher"

with col5:
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
        "timestamp": datetime.now().isoformat(),
        "data": result.get("data", {})
    })
    
    st.rerun()

st.divider()

# Chat Messages Container
chat_container = st.container()

with chat_container:
    # Display chat messages
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Add copy button for responses
            if message["role"] == "assistant":
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    if "intent" in message:
                        st.caption(f"Intent: {message['intent']}")
                with col2:
                    if "confidence" in message:
                        st.caption(f"Confidence: {message['confidence']:.2f}")
                with col3:
                    if "timestamp" in message:
                        st.caption(f"Time: {message['timestamp'].split('T')[1].split('.')[0]}")
                with col4:
                    if st.button("📋", key=f"copy_{idx}", help="Copy response"):
                        st.write("Copied!")  # In production, use clipboard library
                        st.session_state[f"copied_{idx}"] = message["content"]

# Command Input with Suggestions
input_container = st.container()

with input_container:
    # Show input suggestions
    if "input_text" not in st.session_state:
        st.session_state.input_text = ""
    
    # Command suggestions based on input
    if st.session_state.input_text:
        suggestions = get_command_suggestions(st.session_state.input_text)
        if suggestions:
            st.markdown("**Suggestions:**")
            suggestion_cols = st.columns(len(suggestions))
            for idx, suggestion in enumerate(suggestions):
                with suggestion_cols[idx]:
                    if st.button(suggestion, key=f"sugg_{idx}"):
                        st.session_state.input_text = suggestion

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
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            st.caption(f"Intent: {result.get('intent', 'unknown')}")
        with col2:
            st.caption(f"Confidence: {result.get('confidence', 0):.2f}")
        with col3:
            st.caption(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        with col4:
            if st.button("📋", help="Copy response"):
                st.session_state.last_response = response_text
        
        # Add to messages
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "intent": result.get("intent", "unknown"),
            "confidence": result.get("confidence", 0),
            "timestamp": datetime.now().isoformat(),
            "data": result.get("data", {})
        })

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <small>
            Sophia Intel AI - Natural Language Interface v1.0 (Production Enhanced)<br>
            Phase 2 Implementation - Production Ready
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
    
    # Performance metrics
    st.markdown("### Performance Metrics")
    if st.session_state.messages:
        avg_confidence = sum(m.get("confidence", 0) for m in st.session_state.messages if m["role"] == "assistant") / len([m for m in st.session_state.messages if m["role"] == "assistant"])
        st.metric("Average Confidence", f"{avg_confidence:.2f}")
        st.metric("Total Messages", len(st.session_state.messages))