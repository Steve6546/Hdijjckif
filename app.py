import streamlit as st
import os
import asyncio
from PIL import Image
import io
import base64
from orchestrator import BrainOrchestrator
from agents import AGENT_DESCRIPTIONS
import utils

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

# Group agents by category
agent_categories = {
    "Perception": ["قارئ الصور", "قارئ النية", "المستقبل العام", "قارئ بيانات المستخدم"],
    "Analysis": ["الفيلسوف الداخلي", "المفكر العميق", "فلاش التحليل السريع", "محلل المتطلبات"],
    "Creation": ["منشئ الواجهة الأمامية", "مصمم الستايل", "كاتب تقارير", "منشئ الواجهة الخلفية"],
    "Validation": ["مراقب الأمان", "المهندس الأول", "منشئ الاختبارات", "مصحح الأكواد"],
    "Coordination": ["منسق التفكير الداخلي", "الحارس الأعلى", "رقيب الخصوصية", "مهندس البنية"]
}

# Allow users to select which agents to include
for category, agents in agent_categories.items():
    st.sidebar.markdown(f"**{category}**")
    for agent in agents:
        if agent in AGENT_DESCRIPTIONS:
            selected_agents[agent] = st.sidebar.checkbox(
                f"{agent} ({AGENT_DESCRIPTIONS[agent]['model_short']})", 
                value=agent in ["المستقبل العام", "منسق التفكير الداخلي"]
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
                
                # Process with the orchestrator
                try:
                    results = asyncio.run(orchestrator.process_request(
                        text=user_input,
                        image_url=image_data,
                        agents=active_agents
                    ))
                    
                    # Display results
                    st.success("Processing complete!")
                    
                    # Show individual agent responses in expandable sections
                    st.subheader("Agent Responses")
                    
                    for agent, response in results['agent_responses'].items():
                        with st.expander(f"{agent} ({AGENT_DESCRIPTIONS[agent]['model_short']})", expanded=False):
                            st.markdown(response)
                    
                    # Show summarized response
                    st.subheader("Integrated Response")
                    st.markdown(results['integrated_response'])
                    
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")
                    st.info("Please check your OpenRouter API key or try again later.")

# Footer
st.markdown("---")
st.caption("AI Brain Orchestration System - Powered by OpenRouter.ai")
