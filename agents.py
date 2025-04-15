"""
Agent definitions and management module for the AI Brain orchestration system.
Contains 20 specialized agents each with their own model and expertise.
"""
import logging
from typing import Dict, List, Optional, Any

from config import AGENT_PROFILES

# Create a custom logger for agent activities
logger = logging.getLogger("brain_agents")
logger.setLevel(logging.INFO)

# Convert config-based agent profiles to the agent format used in the app
AGENT_DESCRIPTIONS = {}
for key, profile in AGENT_PROFILES.items():
    name_key = key
    # Convert snake_case to display name
    display_name = " ".join(word.capitalize() for word in key.split('_'))
    
    # Handle the model values safely
    model_value = profile.get("model", "")
    if model_value:
        try:
            model_short = model_value.split('/')[-1].split(':')[0]
        except (AttributeError, IndexError):
            model_short = str(model_value)
    else:
        model_short = "Unknown"
    
    AGENT_DESCRIPTIONS[name_key] = {
        "model": model_value,
        "model_short": model_short,
        "description": profile.get("description", ""),
        "supports_vision": "image" in profile.get("input_types", []),
        "capabilities": profile.get("capabilities", [])
    }

# Create prompt templates and system prompts from agent configuration
AGENT_PROMPTS = {}
SYSTEM_PROMPTS = {}

# Populate prompt templates dynamically based on the agent profiles
for key, profile in AGENT_PROFILES.items():
    # Create the prompt template based on agent capabilities
    capabilities = profile.get("capabilities", [])
    if "image_analysis" in capabilities:
        AGENT_PROMPTS[key] = f"Analyze the following image in detail and respond to this request: {{text}}"
    elif "code_generation" in capabilities:
        AGENT_PROMPTS[key] = f"Provide code and technical guidance for the following task: {{text}}"
    elif "research_methodology" in capabilities:
        AGENT_PROMPTS[key] = f"Research and provide detailed information about: {{text}}"
    elif "strategic_planning" in capabilities:
        AGENT_PROMPTS[key] = f"Develop a strategic analysis and plan for: {{text}}"
    elif "creative_ideation" in capabilities:
        AGENT_PROMPTS[key] = f"Generate creative ideas and concepts for: {{text}}"
    else:
        AGENT_PROMPTS[key] = f"Please analyze the following and provide insights: {{text}}"
    
    # Use the system prompt from the profile
    SYSTEM_PROMPTS[key] = profile.get("system_prompt", "You are an AI assistant.")

def get_agent_details(agent_name):
    """
    Get details for a specific agent.
    
    Args:
        agent_name (str): The name of the agent
        
    Returns:
        dict: Agent details including model, description, and prompt templates
    """
    if agent_name not in AGENT_DESCRIPTIONS:
        raise ValueError(f"Agent {agent_name} not found in available agents")
    
    return {
        **AGENT_DESCRIPTIONS[agent_name],
        "prompt_template": AGENT_PROMPTS.get(agent_name, "Please analyze the following: {text}"),
        "system_prompt": SYSTEM_PROMPTS.get(agent_name, "You are an AI assistant.")
    }

def get_available_agents():
    """
    Get a list of all available agents.
    
    Returns:
        list: Names of all available agents
    """
    return list(AGENT_DESCRIPTIONS.keys())

def get_vision_compatible_agents():
    """
    Get a list of agents that support image analysis.
    
    Returns:
        list: Names of agents that support vision capabilities
    """
    return [name for name, details in AGENT_DESCRIPTIONS.items() 
            if details.get("supports_vision", False)]
