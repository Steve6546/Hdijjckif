"""
Configuration module for the BrainOS system.
Contains all settings and agent definitions.
"""
import os
from typing import Dict, List, Any

# API Settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SITE_URL = "https://brainos.ai"
SITE_NAME = "BrainOS v5.0"

# System Settings
ALLOWED_EXTENSIONS = ['.jpg', '.png', '.pdf', '.txt', '.zip']
MAX_UPLOAD_SIZE = 200  # MB
MAX_CONCURRENT_AGENTS = 20
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2000

# Agent Configuration
AGENT_PROFILES = {
    # Vision and Image Processing
    "visual_analyzer": {
        "model": "google/gemini-2.5-pro-exp-03-25:free",
        "description": "Detailed analysis of images and visual content",
        "system_prompt": "You are a highly advanced visual analysis AI that can interpret and explain complex visual content.",
        "input_types": ["text", "image"],
        "capabilities": ["image_analysis", "object_detection", "scene_interpretation"]
    },
    "perception_specialist": {
        "model": "meta-llama/llama-4-maverick:free",
        "description": "Specialized in pattern recognition and context understanding from visual data",
        "system_prompt": "You specialize in identifying patterns, contexts, and hidden details in images.",
        "input_types": ["text", "image"],
        "capabilities": ["pattern_recognition", "contextual_understanding"]
    },
    
    # Language Processing
    "linguistic_expert": {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "description": "Expert in language understanding, translation, and complex text analysis",
        "system_prompt": "You are a linguistic expert specialized in deep language understanding and analysis.",
        "input_types": ["text"],
        "capabilities": ["language_analysis", "translation", "sentiment_analysis"]
    },
    "semantic_processor": {
        "model": "deepseek/deepseek-v3-base:free",
        "description": "Deep semantic understanding and context analysis",
        "system_prompt": "You specialize in understanding semantic meaning and extracting contextual information from text.",
        "input_types": ["text"],
        "capabilities": ["semantic_analysis", "context_extraction"]
    },
    
    # Reasoning and Problem Solving
    "logical_reasoner": {
        "model": "deepseek/deepseek-r1:free",
        "description": "Expert in logical reasoning and problem-solving",
        "system_prompt": "You are a logical reasoning expert that can solve complex problems through structured analysis.",
        "input_types": ["text"],
        "capabilities": ["logical_reasoning", "problem_solving", "decision_making"]
    },
    "creative_thinker": {
        "model": "qwen/qwen2.5-vl-72b-instruct:free",
        "description": "Generates creative ideas and alternative perspectives",
        "system_prompt": "You are a creative thinking specialist that generates innovative ideas and unique perspectives.",
        "input_types": ["text", "image"],
        "capabilities": ["creative_ideation", "brainstorming", "alternative_perspectives"]
    },
    
    # Knowledge and Research
    "knowledge_navigator": {
        "model": "nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
        "description": "Vast knowledge repository with information retrieval capabilities",
        "system_prompt": "You possess vast knowledge and can retrieve accurate information on a wide range of topics.",
        "input_types": ["text"],
        "capabilities": ["information_retrieval", "fact_checking", "knowledge_synthesis"]
    },
    "research_assistant": {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "description": "Specialized in research methodology and thorough investigations",
        "system_prompt": "You are a research specialist that can find, analyze, and synthesize information systematically.",
        "input_types": ["text"],
        "capabilities": ["research_methodology", "data_analysis", "source_evaluation"]
    },
    
    # Coding and Technical
    "code_architect": {
        "model": "open-r1/olympiccoder-32b:free",
        "description": "Software architecture and code generation expert",
        "system_prompt": "You are an expert programmer that can design architectures and generate efficient, high-quality code.",
        "input_types": ["text"],
        "capabilities": ["code_generation", "architecture_design", "debugging"]
    },
    "technical_analyst": {
        "model": "qwen/qwq-32b:free",
        "description": "Technical system analysis and optimization",
        "system_prompt": "You specialize in analyzing technical systems and providing optimization recommendations.",
        "input_types": ["text"],
        "capabilities": ["system_analysis", "performance_optimization", "technical_documentation"]
    },
    
    # Strategic Thinking
    "strategic_advisor": {
        "model": "google/gemini-2.0-flash-exp:free",
        "description": "Long-term planning and strategic thinking",
        "system_prompt": "You are a strategic thinking specialist that can develop long-term plans and identify opportunities.",
        "input_types": ["text"],
        "capabilities": ["strategic_planning", "opportunity_identification", "risk_assessment"]
    },
    "futurist": {
        "model": "meta-llama/llama-4-maverick:free",
        "description": "Future trend prediction and scenario planning",
        "system_prompt": "You specialize in predicting future trends and analyzing potential future scenarios.",
        "input_types": ["text"],
        "capabilities": ["trend_prediction", "scenario_planning", "forecasting"]
    },
    
    # Domain Specialists
    "scientific_expert": {
        "model": "deepseek/deepseek-v3-base:free",
        "description": "Expertise in scientific domains including physics, chemistry, and biology",
        "system_prompt": "You are a scientific expert with deep knowledge across physics, chemistry, biology, and other scientific domains.",
        "input_types": ["text"],
        "capabilities": ["scientific_analysis", "hypothesis_generation", "experimental_design"]
    },
    "financial_analyst": {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "description": "Financial analysis and economic insights",
        "system_prompt": "You are a financial analysis expert with deep understanding of economics and market dynamics.",
        "input_types": ["text"],
        "capabilities": ["financial_analysis", "economic_forecasting", "investment_strategy"]
    },
    "medical_consultant": {
        "model": "google/gemini-2.5-pro-exp-03-25:free",
        "description": "Medical knowledge and health-related insights",
        "system_prompt": "You have extensive medical knowledge and can provide health-related insights (with appropriate disclaimers).",
        "input_types": ["text", "image"],
        "capabilities": ["medical_knowledge", "symptom_analysis", "health_education"]
    },
    
    # Specialized Communication
    "empathetic_communicator": {
        "model": "meta-llama/llama-4-maverick:free",
        "description": "Empathetic communication and emotional intelligence",
        "system_prompt": "You specialize in empathetic communication with high emotional intelligence.",
        "input_types": ["text"],
        "capabilities": ["emotional_intelligence", "empathetic_response", "supportive_communication"]
    },
    "storytelling_expert": {
        "model": "qwen/qwen2.5-vl-72b-instruct:free",
        "description": "Narrative creation and storytelling",
        "system_prompt": "You are an expert storyteller with the ability to craft engaging narratives across different genres.",
        "input_types": ["text", "image"],
        "capabilities": ["narrative_creation", "character_development", "plot_structuring"]
    },
    
    # Integration and Coordination
    "synthesis_specialist": {
        "model": "nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
        "description": "Integrates and synthesizes information from multiple sources",
        "system_prompt": "You excel at integrating and synthesizing information from diverse sources into coherent insights.",
        "input_types": ["text"],
        "capabilities": ["information_synthesis", "multi-source_integration", "insight_generation"]
    },
    "orchestrator": {
        "model": "google/gemini-2.0-flash-exp:free",
        "description": "Coordinates between different agents and integrates their responses",
        "system_prompt": "You are the central coordinator that organizes input from various specialist agents and synthesizes their insights.",
        "input_types": ["text"],
        "capabilities": ["response_integration", "agent_coordination", "decision_synthesis"]
    }
}

# Paths for file organization
PATHS = {
    "cache": "./cache",
    "uploads": "./uploads",
    "logs": "./logs"
}

# Create necessary directories if they don't exist
for path in PATHS.values():
    os.makedirs(path, exist_ok=True)

# Ensure database directories exist
os.makedirs("cache/responses", exist_ok=True)
os.makedirs("logs/agents", exist_ok=True)
os.makedirs("uploads", exist_ok=True)