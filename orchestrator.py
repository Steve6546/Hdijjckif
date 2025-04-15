"""
Core orchestration module for the AI Brain system.
Coordinates communication and processing between 20 specialized AI agents.
"""

import asyncio
import logging
import time
import random
import concurrent.futures
from typing import Dict, List, Optional, Any, Tuple, Set

from agents import get_agent_details, get_available_agents, get_vision_compatible_agents
from api_client import OpenRouterClient
from config import OPENROUTER_API_KEY, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, MAX_CONCURRENT_AGENTS

# Set up logging for the orchestrator
logger = logging.getLogger("brain_orchestrator")
logger.setLevel(logging.INFO)

class BrainOrchestrator:
    """Orchestrates the multi-agent AI system and manages communication between agents."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the brain orchestrator.
        
        Args:
            api_key (str, optional): OpenRouter API key. If None, will try to get from environment.
        """
        self.client = OpenRouterClient(api_key)
        self.agent_registry = {}  # Store agent instances for reuse
        self.session_history = {}  # Track session-specific interaction history
        
    async def get_available_models(self) -> List[Dict]:
        """
        Get a list of available AI models from OpenRouter.
        
        Returns:
            List[Dict]: Information about available models
        """
        try:
            return await self.client.get_model_list()
        except Exception as e:
            logger.error(f"Error fetching model list: {str(e)}")
            return []
    
    async def agent_select_task(self, task_description: str) -> List[str]:
        """
        Automatically select the most appropriate agents for a given task.
        Uses a meta-agent to analyze the task and choose specialists.
        
        Args:
            task_description (str): Description of the task to be performed
            
        Returns:
            List[str]: List of recommended agent names for the task
        """
        # Use an internal agent to analyze the task
        system_prompt = (
            "You are a task analysis specialist. Your job is to analyze a task description "
            "and identify which specialized AI agents would be best suited to handle it."
        )
        
        agent_details = get_agent_details(random.choice(get_available_agents()))
        
        # List all available agents with their capabilities
        available_agents = get_available_agents()
        agent_capabilities = "\n".join([
            f"- {agent}: {get_agent_details(agent)['description']}" 
            for agent in available_agents
        ])
        
        prompt = f"""
        Analyze this task and recommend which specialized agents should handle it:
        
        TASK: {task_description}
        
        AVAILABLE AGENTS:
        {agent_capabilities}
        
        Select 3-5 agents best suited for this task. Return ONLY a comma-separated list of agent names.
        """
        
        try:
            result = await self.client.process_with_agent(
                agent_model=agent_details["model"],
                text=prompt,
                system_prompt=system_prompt
            )
            
            # Parse the result to extract agent names
            # This assumes the model returns a simple comma-separated list
            selected_agents = [
                name.strip() for name in result.split(",")
                if name.strip() in available_agents
            ]
            
            # Ensure we have at least one valid agent
            if not selected_agents and available_agents:
                selected_agents = [available_agents[0]]
                
            return selected_agents
            
        except Exception as e:
            logger.error(f"Error in agent selection: {str(e)}")
            # Fallback to random selection of 3 agents
            return random.sample(
                get_available_agents(), 
                min(3, len(get_available_agents()))
            )
        
    async def process_with_single_agent(
        self, 
        agent_name: str, 
        text: str, 
        image_url: Optional[str] = None
    ) -> str:
        """
        Process a request with a single agent.
        
        Args:
            agent_name (str): Name of the agent to use
            text (str): Text input to process
            image_url (str, optional): URL to an image for vision-capable agents
            
        Returns:
            str: The agent's response
        """
        agent_details = get_agent_details(agent_name)
        
        # Check if this agent supports vision if an image is provided
        if image_url and not agent_details.get("supports_vision", False):
            return f"Note: {agent_name} does not support image analysis. Processing text only.\n\n" + \
                   await self.client.process_with_agent(
                       agent_model=agent_details["model"],
                       text=text,
                       system_prompt=agent_details["system_prompt"]
                   )
        
        # Process with or without image
        return await self.client.process_with_agent(
            agent_model=agent_details["model"],
            text=text,
            system_prompt=agent_details["system_prompt"],
            image_url=image_url if agent_details.get("supports_vision", False) else None
        )
    
    async def process_request(
        self, 
        text: str, 
        image_url: Optional[str] = None,
        agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a request with multiple agents and integrate their responses.
        
        Args:
            text (str): Text input to process
            image_url (str, optional): URL to an image for vision models
            agents (List[str], optional): List of specific agents to use. If None, uses a default set.
            
        Returns:
            Dict: Results including individual agent responses and an integrated response
        """
        # If agents not specified, select an appropriate set of agents
        if not agents or len(agents) == 0:
            all_available_agents = get_available_agents()
            # If no agents were specified, use a suitable subset
            if image_url:
                # If an image is provided, prioritize vision-capable agents
                vision_agents = get_vision_compatible_agents()
                # Mix vision agents with general purpose agents
                agents = vision_agents[:3]  # Top 3 vision agents
                
                # Add some non-vision agents for additional perspectives
                non_vision_agents = [a for a in all_available_agents if a not in vision_agents]
                agents.extend(random.sample(non_vision_agents, min(2, len(non_vision_agents))))
            else:
                # For text-only, select a balanced mix of agent types
                agent_count = min(5, len(all_available_agents))  # Use up to 5 agents
                agents = random.sample(all_available_agents, agent_count)
            
            # Ensure we don't exceed the max concurrent agents limit
            agents = agents[:MAX_CONCURRENT_AGENTS]
            
            # Log the selected agents
            logger.info(f"Auto-selected agents: {agents}")
        
        # Process in parallel with all specified agents
        tasks = [
            self.process_with_single_agent(agent, text, image_url)
            for agent in agents
        ]
        
        agent_responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any failed responses
        agent_results = {}
        for i, response in enumerate(agent_responses):
            agent_name = agents[i]
            if isinstance(response, Exception):
                agent_results[agent_name] = f"Error: {str(response)}"
            else:
                agent_results[agent_name] = response
        
        # Integrate the responses
        integrated_response = await self._integrate_responses(
            agent_results, 
            text, 
            image_url
        )
        
        return {
            "agent_responses": agent_results,
            "integrated_response": integrated_response,
            "input_text": text,
            "image_provided": image_url is not None
        }
    
    async def _integrate_responses(
        self, 
        agent_responses: Dict[str, str], 
        original_text: str,
        image_url: Optional[str] = None
    ) -> str:
        """
        Integrate multiple agent responses into a coherent output.
        
        Uses a coordinator agent to synthesize the outputs.
        
        Args:
            agent_responses (Dict[str, str]): Responses from each agent
            original_text (str): The original input text
            image_url (str, optional): URL to the original image
            
        Returns:
            str: Integrated response
        """
        # Choose an integration agent specializing in coordination or synthesis
        # Look for agents with coordination capabilities first
        integration_agent = None
        available_agents = list(agent_responses.keys())
        
        # First, try to find agents with coordination capabilities
        for agent_name in available_agents:
            agent_details = get_agent_details(agent_name)
            capabilities = agent_details.get("capabilities", [])
            
            # Look for agents with coordination, synthesis, or integration capabilities
            if any(cap in capabilities for cap in ["agent_coordination", "response_integration", 
                                                "information_synthesis", "multi-source_integration"]):
                integration_agent = agent_name
                logger.info(f"Using dedicated coordinator agent: {integration_agent}")
                break
        
        # If no coordinator found, use a generalist agent or the first available
        if not integration_agent:
            # Find a general purpose agent
            for agent_name in available_agents:
                if "general" in agent_name or "orchestrator" in agent_name:
                    integration_agent = agent_name
                    logger.info(f"Using general purpose agent: {integration_agent}")
                    break
            
            # If still no agent found, use the first available
            if not integration_agent and available_agents:
                integration_agent = available_agents[0]
                logger.info(f"Using first available agent: {integration_agent}")
        
        # Fallback if somehow we still have no integration agent
        if not integration_agent:
            # This should never happen if agent_responses has at least one entry
            logger.warning("No integration agent available, generating generic response")
            return "No agent was able to process your request. Please try again."
        
        # Prepare the integration prompt
        responses_text = "\n\n".join([
            f"【{agent}】: {response}" 
            for agent, response in agent_responses.items()
        ])
        
        integration_prompt = f"""
        Your task is to synthesize multiple AI responses into a coherent, comprehensive answer.

        Original request: {original_text}

        AI responses:
        {responses_text}

        Please integrate these perspectives into a unified, well-structured response that:
        1. Captures the core insights from all responses
        2. Resolves any contradictions or disagreements
        3. Organizes information logically and coherently
        4. Provides a comprehensive answer to the original request
        """
        
        # Get the details of the integration agent
        agent_details = get_agent_details(integration_agent)
        
        # Process with the integration agent
        integrated_result = await self.client.process_with_agent(
            agent_model=agent_details["model"],
            text=integration_prompt,
            system_prompt="You are an expert at synthesizing multiple perspectives into coherent responses.",
            image_url=image_url if agent_details.get("supports_vision", False) else None
        )
        
        return integrated_result
