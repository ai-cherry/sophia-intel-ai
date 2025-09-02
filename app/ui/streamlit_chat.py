import streamlit as st
import requests
import json

st.set_page_config(
    page_title="AI Code Review System",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI-Powered Code Review System")
st.markdown("Enter your code below for an intelligent review with suggestions and improvements.")

# Code input area
code_input = st.text_area(
    "Code to Review",
    height=None,
    placeholder="Paste your Python, JavaScript, or other code here...",
    help="Supported languages: Python, JavaScript, TypeScript, Java, C++"
)

# Review button
if st.button("🔍 Review Code", type="primary", use_container_width=True):
    if not code_input.strip():
        st.warning("Please enter some code to review.")
    else:
        with st.spinner("Analyzing code..."):
            try:
                # Call the MCP server's code review endpoint
                response = requests.post(
                    "http://localhost:8000/mcp/code-review",
                    json={"code": code_input},
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                # Display results
                st.success("Review completed successfully!")
                st.subheader("Review Results")
                
                # Display suggestions
                if "suggestions" in result and result["suggestions"]:
                    st.markdown("### 🔍 Suggestions")
                    for i, suggestion in enumerate(result["suggestions"], 1):
                        st.markdown(f"**{i}. {suggestion['type']}**")
                        st.markdown(f"**Location:** {suggestion['location']}")
                        st.markdown(f"**Description:** {suggestion['description']}")
                        st.markdown(f"**Fix:** {suggestion['fix']}")
                        st.divider()
                
                # Display metrics
                if "metrics" in result:
                    st.markdown("### 📊 Code Quality Metrics")
                    metrics = result["metrics"]
                    st.metric("Complexity", metrics.get("complexity", "N/A"))
                    st.metric("Readability", f"{metrics.get('readability', 'N/A')}%")
                    st.metric("Potential Bugs", metrics.get("bug_risk", "N/A"))
                    
            except requests.exceptions.RequestException as e:
                st.error(f"API Error: {str(e)}")
                st.info("Check if the MCP server is running: `curl http://localhost:8000/health`")
            except json.JSONDecodeError:
                st.error("Invalid response from server. Please try again.")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "This AI code review system uses **Sophia MCP** to coordinate with backend services. "
    "Powered by enterprise-grade observability and security features."
)