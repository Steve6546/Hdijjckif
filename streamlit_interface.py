"""
Streamlit Interface for Brain Controller System
Provides a unified interface to interact with the Master AI Controller
"""

import os
import sys
import json
import asyncio
import time
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime

import streamlit as st
from PIL import Image
import numpy as np

# Add the parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import controller
from master_ai_controller import get_master_controller
from api_client import OpenRouterClient
from config import OPENROUTER_API_KEY
from utils import generate_session_id

# Configure page settings
st.set_page_config(
    page_title="AI Brain Controller System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Configure Streamlit to handle server issues
if not os.environ.get("STREAMLIT_SERVER_PORT"):
    os.environ["STREAMLIT_SERVER_PORT"] = "5000"
os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_SERVER_ENABLE_CORS"] = "true"
os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"

# Use custom CSS
st.markdown("""
<style>
    .main-header {
        color: #4CAF50; 
        text-align: center;
    }
    .agent-box {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .active-agent {
        background-color: rgba(76, 175, 80, 0.2);
        border-left: 3px solid #4CAF50;
    }
    .inactive-agent {
        background-color: rgba(200, 200, 200, 0.2);
    }
    .output-container {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 15px;
        background-color: #f5f5f5;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .status-running {
        background-color: #4CAF50;
    }
    .status-error {
        background-color: #F44336;
    }
    .status-waiting {
        background-color: #FFC107;
    }
</style>
""", unsafe_allow_html=True)

# Initialize controller
@st.cache_resource
def initialize_controller():
    """Initialize and return the controller."""
    return get_master_controller(api_key=OPENROUTER_API_KEY)

# Initialize session state
if "controller" not in st.session_state:
    st.session_state.controller = initialize_controller()
    st.session_state.conversation_history = []
    st.session_state.messages = []
    st.session_state.processing_modes = ["auto", "standard", "deep", "swarm", "neuralsym"]
    st.session_state.selected_mode = "auto"
    st.session_state.session_id = generate_session_id()

# Main header
st.markdown("<h1 class='main-header'>🧠 AI Brain Control System</h1>", unsafe_allow_html=True)

# Get system status
system_status = st.session_state.controller.get_system_status()

# Sidebar with system info
with st.sidebar:
    st.header("🧮 System Information")
    
    # Status indicators
    status_color = {
        "running": "status-running",
        "degraded": "status-error",
        "initializing": "status-waiting"
    }
    
    system_state = system_status.get("system_state", "unknown")
    st.markdown(f"<div><span class='status-indicator {status_color.get(system_state, 'status-waiting')}'></span> System State: {system_state.capitalize()}</div>", unsafe_allow_html=True)
    
    st.markdown(f"Session ID: `{st.session_state.session_id}`")
    st.markdown(f"Last Activity: {system_status.get('last_activity', 'N/A')}")
    
    # Advanced Settings
    st.subheader("🛠️ Advanced Settings")
    
    # Processing mode selection
    selected_mode = st.selectbox(
        "Processing Mode:",
        st.session_state.processing_modes,
        index=st.session_state.processing_modes.index(st.session_state.selected_mode)
    )
    if selected_mode != st.session_state.selected_mode:
        st.session_state.selected_mode = selected_mode
    
    # Show debug information checkbox
    st.session_state.show_debug = st.checkbox("Show Debug Information", value=False)
    
    # Reset conversation
    if st.button("Reset Conversation"):
        st.session_state.conversation_history = []
        st.session_state.messages = []
        st.success("Conversation has been reset!")

# Main interface with tabs
main_tab, analytics_tab, debug_tab = st.tabs(["Main Interface", "Analytics", "Debug"])

with main_tab:
    # Two columns for input methods
    text_col, image_col = st.columns([3, 1])
    
    with text_col:
        # Text input area
        user_input = st.text_area("Enter your message:", height=100)
    
    with image_col:
        # Image upload
        uploaded_image = st.file_uploader("Upload an image (optional):", type=["jpg", "jpeg", "png"])
        
        # Show uploaded image
        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="Uploaded Image", use_column_width=True)
    
    # Process button
    if st.button("Process with AI Brain"):
        if not user_input and not uploaded_image:
            st.error("Please provide text input or upload an image.")
        else:
            with st.spinner("Processing with AI Brain..."):
                # Prepare image data if provided
                image_data = None
                if uploaded_image:
                    image_bytes = uploaded_image.getvalue()
                    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                    image_data = f"data:image/{uploaded_image.type.split('/')[-1]};base64,{image_b64}"
                
                # Add user message to history
                user_message = {
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat(),
                    "has_image": uploaded_image is not None
                }
                st.session_state.conversation_history.append(user_message)
                
                # Process request
                try:
                    # Convert async to sync (Streamlit doesn't support async directly)
                    result = asyncio.run(
                        st.session_state.controller.process_user_request(
                            text=user_input,
                            image_data=image_data,
                            mode=st.session_state.selected_mode
                        )
                    )
                    
                    # Extract response based on processing mode
                    response_text = None
                    
                    if "error" in result:
                        response_text = f"Error: {result['error']}"
                    elif "integrated_response" in result:
                        response_text = result["integrated_response"]
                    elif "final_output" in result:
                        if isinstance(result["final_output"], str):
                            response_text = result["final_output"]
                        else:
                            response_text = json.dumps(result["final_output"], indent=2)
                    elif "conclusion" in result:
                        response_text = result["conclusion"]
                    else:
                        response_text = "No response generated."
                    
                    # Add system response to history
                    system_message = {
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": datetime.now().isoformat(),
                        "processing_time": result.get("processing_time", 0),
                        "mode": result.get("mode", "unknown"),
                        "raw_result": result if st.session_state.show_debug else None
                    }
                    st.session_state.conversation_history.append(system_message)
                    
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")
                    # Add error message to history
                    error_message = {
                        "role": "system",
                        "content": f"Error: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                        "is_error": True
                    }
                    st.session_state.conversation_history.append(error_message)
    
    # Display conversation history
    st.subheader("Conversation")
    
    for message in st.session_state.conversation_history:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
            if message.get("has_image", False):
                st.markdown("*(Image attached)*")
        elif message["role"] == "assistant":
            st.markdown(f"**AI Brain:** {message['content']}")
            if "processing_time" in message:
                st.caption(f"Processed in {message['processing_time']:.2f}s using {message['mode']} mode")
        elif message["role"] == "system" and message.get("is_error", False):
            st.error(message["content"])

with analytics_tab:
    st.header("📊 Brain Analytics")
    
    # Add analytics content
    st.markdown("""
    ### System Performance
    Track the performance of the AI Brain components over time.
    """)
    
    # Sample analytics
    if st.session_state.conversation_history:
        # Collect processing times and modes
        processing_times = []
        modes = []
        
        for message in st.session_state.conversation_history:
            if message["role"] == "assistant" and "processing_time" in message:
                processing_times.append(message["processing_time"])
                modes.append(message["mode"])
        
        if processing_times:
            # Display average processing time
            avg_time = sum(processing_times) / len(processing_times)
            st.metric("Average Processing Time", f"{avg_time:.2f}s")
            
            # Display processing time trends
            if len(processing_times) > 1:
                st.line_chart(processing_times)
            
            # Display mode distribution
            mode_counts = {}
            for mode in modes:
                if mode in mode_counts:
                    mode_counts[mode] += 1
                else:
                    mode_counts[mode] = 1
            
            st.bar_chart(mode_counts)
    else:
        st.info("No conversation data available yet.")

with debug_tab:
    st.header("🔍 Debug Information")
    
    if st.session_state.show_debug:
        # Display system status
        st.subheader("System Status")
        st.json(system_status)
        
        # Display raw results from conversations
        st.subheader("Raw Results")
        for message in st.session_state.conversation_history:
            if message["role"] == "assistant" and "raw_result" in message:
                st.markdown(f"**Timestamp:** {message['timestamp']}")
                st.json(message["raw_result"])
                st.markdown("---")
    else:
        st.info("Enable 'Show Debug Information' in the sidebar to view debug data.")

# Footer
st.markdown("---")
st.caption("BrainOS Controller v1.0 | All agents working autonomously")