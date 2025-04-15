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
    
    AGENT_DESCRIPTIONS[name_key] = {
        "model": profile.get("model"),
        "model_short": profile.get("model").split('/')[-1].split(':')[0],
        "description": profile.get("description"),
        "supports_vision": "image" in profile.get("input_types", []),
        "capabilities": profile.get("capabilities", [])
    }

# Agent prompt templates based on their roles
AGENT_PROMPTS = {
    "المستقبل العام": "As a general AI assistant, please provide a comprehensive and insightful response to the following: {text}",
    "قارئ الصور": "Analyze the following image in detail and respond to this request: {text}",
    "الفيلسوف الداخلي": "As a philosophical thinker, provide deep insights on this topic: {text}",
    "المفكر العميق": "Analyze this topic deeply and provide structured reasoning: {text}",
    "مراقب الأمان": "Review the following for security concerns and safety issues: {text}",
    "قارئ بيانات المستخدم": "Analyze the following user data or request for patterns and insights: {text}",
    "منسق التفكير الداخلي": "Coordinate different perspectives and create a balanced view on: {text}",
    "منشئ الواجهة الأمامية": "Design a frontend interface concept for: {text}",
    "مصمم الستايل": "Provide style and design recommendations for: {text}",
    "منشئ الاختبارات": "Create test cases and validation approaches for: {text}",
    "فلاش التحليل السريع": "Provide a quick, concise analysis of: {text}",
    "كاتب تقارير": "Write a detailed report on the following topic: {text}",
    "المهندس الأول": "Provide software engineering insights and architecture recommendations for: {text}",
    "الحارس الأعلى": "Give final oversight and high-level recommendations on: {text}",
    "محلل المتطلبات": "Analyze these requirements and convert them to actionable specifications: {text}",
    "منشئ الواجهة الخلفية": "Design backend architecture and APIs for: {text}",
    "مصحح الأكواد": "Review the following code or concept for issues and suggest improvements: {text}",
    "رقيب الخصوصية": "Evaluate this from a privacy and data protection perspective: {text}",
    "مهندس البنية": "Design system architecture and infrastructure for: {text}"
}

# System prompts for setting agent context
SYSTEM_PROMPTS = {
    "المستقبل العام": "You are a general AI assistant that can handle a wide range of tasks. Provide comprehensive and helpful responses.",
    "قارئ الصور": "You are a visual analysis specialist. Analyze images in detail and provide insights based on visual content.",
    "الفيلسوف الداخلي": "You are a philosophical thinker who provides deep insights on complex topics.",
    "المفكر العميق": "You are a deep reasoning specialist who analyzes topics thoroughly and provides structured insights.",
    "مراقب الأمان": "You are a security specialist who identifies potential risks and safety concerns.",
    "قارئ بيانات المستخدم": "You are a data analyst who identifies patterns and insights from user data and requests.",
    "منسق التفكير الداخلي": "You are a coordination specialist who balances different perspectives to create integrated views.",
    "منشئ الواجهة الأمامية": "You are a frontend design specialist who creates user interface concepts.",
    "مصمم الستايل": "You are a style and design specialist who provides aesthetic recommendations.",
    "منشئ الاختبارات": "You are a testing specialist who develops validation approaches and test cases.",
    "فلاش التحليل السريع": "You are a rapid analysis specialist who provides quick, concise insights.",
    "كاتب تقارير": "You are a report writing specialist who creates detailed documentation.",
    "المهندس الأول": "You are a software engineering specialist who provides architectural insights.",
    "الحارس الأعلى": "You are the final oversight specialist who provides high-level guidance and decisions.",
    "محلل المتطلبات": "You are a requirements analysis specialist who converts needs into specifications.",
    "منشئ الواجهة الخلفية": "You are a backend architecture specialist who designs system APIs and services.",
    "مصحح الأكواد": "You are a code review specialist who identifies issues and suggests improvements.",
    "رقيب الخصوصية": "You are a privacy specialist who ensures data protection and confidentiality.",
    "مهندس البنية": "You are a system architecture specialist who designs technical infrastructure."
}

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
