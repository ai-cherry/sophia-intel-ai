import streamlit as st
import json
import asyncio
from typing import Dict, Any
from app.api.unified_gateway import router as api_router
from fastapi.testclient import TestClient
from app.swarms.config.model_assignments import SWARM_MODEL_ASSIGNMENTS
from app.swarms.core.model_selector import IntelligentModelSelector
from app.config.env_loader import get_env_config

st.set_page_config(page_title="Sophia Intel AI Chat", layout="wide")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'model' not in st.session_state:
    st.session_state.model = "google/gemini-2.5-pro"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def render_model_costs():
    """Render model cost analysis panel."""
    st.subheader("💰 Model Cost Analysis")
    
    # Get model configuration
    config = get_env_config()
    max_daily_cost = config.daily_budget_usd
    
    # Mock cost data (would be replaced with actual metrics)
    model_costs = {
        "openai/gpt-5": {"used": 8.50, "limit": max_daily_cost, "tokens": 150000},
        "x-ai/grok-4": {"used": 2.30, "limit": max_daily_cost, "tokens": 75000},
        "anthropic/claude-sonnet-4": {"used": 1.75, "limit": max_daily_cost, "tokens": 60000},
        "google/gemini-2.5-flash": {"used": 0.45, "limit": max_daily_cost, "tokens": 20000},
        "z-ai/glm-4.5-air": {"used": 0.10, "limit": max_daily_cost, "tokens": 15000},
    }
    
    # Sort models by 'used' cost for prioritization
    sorted_models = sorted(model_costs.items(), key=lambda x: x[1]['used'], reverse=True)
    
    # Display in columns
    for model, data in sorted_models[:3]:  # Show top 3 models
        with st.expander(f"{model.replace('openai/gpt-5', 'GPT-5')}"):
            # Cost progress
            progress = min(data['used'] / data['limit'], 1.0)
            st.progress(progress, text=f"${data['used']:.2f} / ${data['limit']:.2f}")
            
            # Token usage
            st.metric("Tokens", f"{data['tokens']:,}")
            
            # Premium labeling
            if "gpt-5" in model:
                st.warning("Premium Model")
            elif data['used'] < max_daily_cost * 0.2:
                st.success("Economy")
            else:
                st.info("Standard")
    
    # Daily budget indicator
    total_used = sum(data['used'] for data in model_costs.values())
    st.info(f"Total daily cost: ${total_used:.2f} of ${max_daily_cost:.2f}")

def render_model_picker():
    """Render model selection dropdown for the UI."""
    st.sidebar.subheader("Model Selection")
    
    # Get available models based on environment
    models = list(SWARM_MODEL_ASSIGNMENTS["coding_swarm"].values())
    
    # Add fallback default to the list
    models.append("google/gemini-2.5-pro")
    models = sorted(set(models))
    
    # Model selection dropdown
    st.session_state.model = st.selectbox(
        "Select Model",
        options=models,
        index=models.index(st.session_state.model) if st.session_state.model in models else 0
    )
    
    # Premium model visibility
    if "gpt-5" in st.session_state.model:
        st.warning("⚠️ GPT-5 is a premium model with higher costs. Use sparingly for critical tasks.")
    
    # Budget guidance
    if st.session_state.model == "openai/gpt-5" and get_env_config().daily_budget_usd > 50:
        st.info("💡 GPT-5 has higher associated costs. Consider daily budget: ${:.2f}".format(get_env_config().daily_budget_usd))

async def send_message():
    """Send message to the API and get response."""
    if st.session_state.user_input:
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user",
            "content": st.session_state.user_input
        })
        st.session_state.chat_history.append(("user", st.session_state.user_input))
        
        # Clear input
        st.session_state.user_input = ""
        
        # Send to API
        with st.spinner("Thinking..."):
            # Prepare messages for API
            payload = {
                "model": st.session_state.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."}
                ] + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
            }
            
            # Mock API call (in real implementation, call API)
            async with TestClient(api_router) as client:
                response = await client.post("/chat", json=payload)
                
                if response.status_code == 200:
                    response_data = response.json()
                    response_text = response_data["choices"][0]["message"]["content"]
                    
                    # Add AI response to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text
                    })
                    st.session_state.chat_history.append(("assistant", response_text))
                else:
                    st.error(f"API error: {response.status_code}")

# Main UI
st.title("Sophia Intel AI Chat")

# Render model picker in sidebar
render_model_picker()

# Cost monitor panel
render_model_costs()

# Chat interface
for role, content in st.session_state.chat_history:
    if role == "user":
        st.chat_message("user").markdown(content)
    else:
        st.chat_message("assistant").markdown(content)

# User input
st.text_input(
    "Type your message here...",
    key="user_input",
    on_change=send_message
)

# Additional debug info (hidden)
if st.sidebar.checkbox("Show debug info"):
    st.sidebar.json({
        "Selected model": st.session_state.model,
        "Config": get_env_config(),
        "Surge": "Distributed AI infrastructure"
    })

# Model selection info
st.sidebar.markdown("---")
st.sidebar.subheader("Model Availability")
st.sidebar.write("Models active in this environment:")
available_models = [
    m for m in SWARM_MODEL_ASSIGNMENTS["coding_swarm"].values() 
    if not m.startswith("z-")  # Show premium models first
] + ["google/gemini-2.5-flash"]
st.sidebar.code(", ".join(available_models))
if "openai/gpt-5" in available_models:
    st.sidebar.warning("GPT-5 enabled - premium model available")
