"""
Agent Router for the All-Agents-App
This module handles routing messages between the core AI and specialized agents.
"""

import logging
import os
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AgentRouter:
    """
    Routes messages between the core AI and specialized agents.
    Implements a standardized communication protocol.
    """
    
    def __init__(self, agents: Dict[str, Any] = None):
        """
        Initialize the agent router with available agents.
        
        Args:
            agents: Dictionary of agent instances keyed by agent name
        """
        self.agents = agents or {}
        logger.info(f"AgentRouter initialized with {len(self.agents)} agents: {list(self.agents.keys())}")
    
    def register_agent(self, name: str, agent: Any) -> None:
        """
        Register a new agent with the router.
        
        Args:
            name: Name of the agent
            agent: Agent instance
        """
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    def route_message(self, message: str, target_agent: str, **kwargs) -> Dict[str, Any]:
        """
        Route a message to a specific agent.
        
        Args:
            message: The message to route
            target_agent: The name of the target agent
            **kwargs: Additional parameters to pass to the agent
            
        Returns:
            Dict containing the response from the agent
        """
        if target_agent not in self.agents:
            logger.error(f"Agent '{target_agent}' not found. Available agents: {list(self.agents.keys())}")
            return {
                "status": "error",
                "message": f"Agent '{target_agent}' not found",
                "agent": "router"
            }
        
        try:
            logger.info(f"Routing message to agent '{target_agent}'")
            agent = self.agents[target_agent]
            
            # Check if the agent has a process method
            if hasattr(agent, 'process') and callable(agent.process):
                response = agent.process(message, **kwargs)
            # Check if the agent has a generate method
            elif hasattr(agent, 'generate') and callable(agent.generate):
                response = agent.generate(message, **kwargs)
            # Check if the agent has a handle method
            elif hasattr(agent, 'handle') and callable(agent.handle):
                response = agent.handle(message, **kwargs)
            else:
                logger.error(f"Agent '{target_agent}' does not have a valid interface method")
                return {
                    "status": "error",
                    "message": f"Agent '{target_agent}' does not have a valid interface method",
                    "agent": "router"
                }
            
            # Standardize the response format
            if isinstance(response, str):
                return {
                    "status": "success",
                    "message": response,
                    "agent": target_agent
                }
            elif isinstance(response, dict):
                if "agent" not in response:
                    response["agent"] = target_agent
                if "status" not in response:
                    response["status"] = "success"
                return response
            else:
                return {
                    "status": "success",
                    "message": str(response),
                    "agent": target_agent
                }
                
        except Exception as e:
            logger.error(f"Error routing message to agent '{target_agent}': {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error routing message to agent '{target_agent}': {str(e)}",
                "agent": "router"
            }
    
    def determine_agent(self, message: str) -> str:
        """
        Determine which agent should handle a message based on content.
        
        Args:
            message: The message to analyze
            
        Returns:
            Name of the most appropriate agent
        """
        message_lower = message.lower()
        
        # Check for image-related queries
        if any(term in message_lower for term in ["image", "picture", "photo", "صورة", "تصوير"]):
            return "image" if "image" in self.agents else "ai"
            
        # Check for project-related queries
        if any(term in message_lower for term in ["project", "task", "مشروع", "مهمة"]):
            return "project" if "project" in self.agents else "ai"
            
        # Check for code-related queries
        if any(term in message_lower for term in ["code", "programming", "برمجة", "كود"]):
            return "ai_engine" if "ai_engine" in self.agents else "ai"
            
        # Default to the AI agent
        return "ai"
    
    def route_by_content(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Automatically route a message to the appropriate agent based on content.
        
        Args:
            message: The message to route
            **kwargs: Additional parameters to pass to the agent
            
        Returns:
            Dict containing the response from the agent
        """
        target_agent = self.determine_agent(message)
        logger.info(f"Auto-routing message to agent '{target_agent}' based on content analysis")
        return self.route_message(message, target_agent, **kwargs)