import streamlit as st
import os
import asyncio
import time
import json
import logging
from datetime import datetime
from PIL import Image
import io
import base64
import concurrent.futures
import uuid

from orchestrator import BrainOrchestrator
from agents import AGENT_DESCRIPTIONS, get_agent_details, get_available_agents, get_vision_compatible_agents
from utils import (
    encode_image_to_base64, truncate_text, generate_session_id, 
    format_agent_response, get_error_message, save_interaction_log, 
    analyze_agent_performance
)
from config import OPENROUTER_API_KEY, SITE_NAME, MAX_CONCURRENT_AGENTS, ALLOWED_EXTENSIONS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log")
    ]
)
logger = logging.getLogger("brain_app")

# Page configuration
st.set_page_config(
    page_title="AI Brain - Multi-Agent Orchestration",
    page_icon="🧠",
    layout="wide"
)

# Initialize orchestrator
@st.cache_resource
def get_orchestrator():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        st.warning("⚠️ OpenRouter API key not found in environment variables. Some functionality may be limited.")
    
    return BrainOrchestrator(api_key=api_key)

# Initialize the orchestrator
orchestrator = get_orchestrator()

# Sidebar for agent selection and configuration
st.sidebar.title("🧠 AI Brain Control")

# Display information about each agent
st.sidebar.subheader("Available Agents")
selected_agents = {}

# Show available agent list from config
available_agents = get_available_agents()

# Create agent categories based on capabilities
agent_categories = {}

# Create categories dynamically from agent capabilities
for agent_name in available_agents:
    agent_details = get_agent_details(agent_name)
    capabilities = agent_details.get("capabilities", [])
    
    # Determine the category based on main capabilities
    if "image_analysis" in capabilities or "visual" in agent_details.get("description", "").lower():
        category = "Perception"
    elif "reasoning" in capabilities or "analysis" in capabilities:
        category = "Analysis"
    elif "generation" in capabilities or "creation" in capabilities or "design" in capabilities:
        category = "Creation"
    elif "security" in capabilities or "testing" in capabilities or "review" in capabilities:
        category = "Validation"
    elif "coordination" in capabilities or "integration" in capabilities or "orchestration" in capabilities:
        category = "Coordination"
    else:
        category = "General"
    
    # Add the agent to the appropriate category
    if category not in agent_categories:
        agent_categories[category] = []
    agent_categories[category].append(agent_name)

# Additional filters
st.sidebar.subheader("Filter Options")
auto_select = st.sidebar.checkbox("Auto-select appropriate agents", value=True)
show_vision_only = st.sidebar.checkbox("Show vision-capable agents only", value=False)

# Allow users to select which agents to include
for category, agents in agent_categories.items():
    st.sidebar.markdown(f"**{category}**")
    
    # Filter by vision capability if requested
    display_agents = agents
    if show_vision_only:
        vision_agents = get_vision_compatible_agents()
        display_agents = [a for a in agents if a in vision_agents]
    
    for agent in display_agents:
        agent_details = get_agent_details(agent)
        selected_agents[agent] = st.sidebar.checkbox(
            f"{agent} - {agent_details.get('description', '')}",
            value=False  # We'll handle auto-selection in processing
        )

# Main content area
st.title("🧠 Multi-Agent AI Orchestration System")
st.markdown("""
This system coordinates 20 specialized AI agents through OpenRouter.ai to process 
and analyze different types of inputs. Each agent has specific capabilities 
and roles in the cognitive process.
""")

# Input options
input_type = st.radio("Select input type:", ["Text", "Image + Text"], horizontal=True)

if input_type == "Text":
    user_input = st.text_area("Enter your text:", height=150)
    uploaded_image = None
else:  # Image + Text
    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_image = st.file_uploader("Upload an image:", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="Uploaded Image", use_column_width=True)
    with col2:
        user_input = st.text_area("Enter your text:", height=150)

# Process button
if st.button("Process with AI Brain"):
    if not user_input and not uploaded_image:
        st.error("Please provide either text input or an image to process.")
    else:
        # Prepare active agents list
        active_agents = [agent for agent, is_selected in selected_agents.items() if is_selected]
        
        # Auto-select agents if enabled and none were manually selected
        if auto_select and not active_agents:
            # If we have an image, use image-capable agents
            if uploaded_image:
                vision_agents = get_vision_compatible_agents()
                # Get a mix of vision and non-vision agents
                active_agents = vision_agents[:3]  # Top 3 vision agents
                
                # Add some general agents
                general_agents = [a for a in available_agents 
                                 if "general" in get_agent_details(a).get("capabilities", [])]
                if general_agents:
                    active_agents.extend(general_agents[:2])
            else:
                # For text, analyze the content to select appropriate agents
                if user_input:
                    # Get specialized agents based on input
                    selected_task_agents = asyncio.run(
                        orchestrator.agent_select_task(user_input)
                    )
                    active_agents = selected_task_agents
                else:
                    # Select some default agents if no input provided
                    active_agents = [a for a in available_agents 
                                    if any(cap in get_agent_details(a).get("capabilities", [])
                                          for cap in ["general", "analysis", "integration"])][:3]
            
            # Ensure we don't exceed limits
            active_agents = active_agents[:MAX_CONCURRENT_AGENTS]
            st.info(f"Auto-selected agents: {', '.join(active_agents)}")
        
        if not active_agents:
            st.warning("Please select at least one agent to process your input.")
        else:
            with st.spinner("The AI Brain is processing your input..."):
                # Convert image to base64 if provided
                image_data = None
                if uploaded_image:
                    image_bytes = uploaded_image.getvalue()
                    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                    image_data = f"data:image/{uploaded_image.type.split('/')[-1]};base64,{image_b64}"
                
                # Generate a session ID for this interaction
                session_id = generate_session_id()
                
                # Record the start time for performance tracking
                start_time = time.time()
                
                # Process with the orchestrator
                try:
                    # Create a progress bar to show processing steps
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Phase 1: Agent selection
                    status_text.text("Selecting and initializing agents...")
                    progress_bar.progress(10)
                    
                    # Phase 2: Processing input
                    status_text.text(f"Processing input with {len(active_agents)} agents...")
                    
                    # Run the main orchestration process
                    results = asyncio.run(orchestrator.process_request(
                        text=user_input,
                        image_url=image_data,
                        agents=active_agents
                    ))
                    
                    # Phase 3: Integrating responses
                    progress_bar.progress(75)
                    status_text.text("Integrating agent responses...")
                    
                    # Calculate processing time
                    processing_time = time.time() - start_time
                    
                    # Log the interaction details
                    save_interaction_log(
                        session_id=session_id,
                        input_text=user_input,
                        agent_responses=results['agent_responses'],
                        integrated_response=results['integrated_response'],
                        image_provided=image_data is not None,
                        processing_time=processing_time
                    )
                    progress_bar.progress(100)
                    status_text.text(f"Processing complete! Time: {processing_time:.2f}s")
                    
                    # Display results
                    st.success(f"Processing complete in {processing_time:.2f} seconds")
                    
                    # Information about the session
                    st.info(f"Session ID: {session_id} | Agents: {len(active_agents)} | Time: {processing_time:.2f}s")
                    
                    # Show individual agent responses in expandable sections
                    st.subheader("Agent Responses")
                    
                    for agent, response in results['agent_responses'].items():
                        agent_details = get_agent_details(agent)
                        with st.expander(f"{agent} ({agent_details.get('model_short', 'Unknown')})", expanded=False):
                            st.markdown(response)
                            
                            # Show performance analysis for the agent
                            performance = analyze_agent_performance(agent, response)
                            st.caption(f"Response length: {performance['response_length']} chars | Paragraphs: {performance['response_paragraphs']}")
                    
                    # Show summarized response
                    st.subheader("Integrated Response")
                    st.markdown(results['integrated_response'])
                    
                except Exception as e:
                    logger.error(f"Error in request processing: {str(e)}")
                    error_message = get_error_message(e)
                    st.error(f"Error: {error_message}")
                    
                    # Check if it's an OpenRouter API key issue
                    if "API key" in str(e):
                        st.warning("Please make sure your OpenRouter API key is set in the environment variables (.env file).")
                    
                    # Show more detailed error information in an expander
                    with st.expander("Technical Details", expanded=False):
                        st.code(str(e), language="python")

# Footer
st.markdown("---")
st.caption("AI Brain Orchestration System - Powered by OpenRouter.ai")
