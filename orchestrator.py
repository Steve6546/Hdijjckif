"""
Core orchestration module for the AI Brain system.
"""

import asyncio
from typing import Dict, List, Optional, Any
import random
from agents import get_agent_details, get_vision_compatible_agents
from api_client import OpenRouterClient

class BrainOrchestrator:
    """Orchestrates the multi-agent AI system."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the brain orchestrator.
        
        Args:
            api_key (str, optional): OpenRouter API key. If None, will try to get from environment.
        """
        self.client = OpenRouterClient(api_key)
        
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
        # If agents not specified, use a default set
        if not agents or len(agents) == 0:
            # If image is provided, prioritize vision-capable agents
            if image_url:
                agents = get_vision_compatible_agents()[:3]  # Get top 3 vision agents
            else:
                # Use a mix of agents for text-only processing
                agents = ["المستقبل العام", "المفكر العميق", "منسق التفكير الداخلي"]
        
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
        # Choose an integration agent - either the coordinator or the general one
        integration_agent = "منسق التفكير الداخلي"
        if integration_agent not in agent_responses:
            integration_agent = "الحارس الأعلى"
            if integration_agent not in agent_responses:
                # If neither is available, use the first agent that responded
                integration_agent = list(agent_responses.keys())[0]
        
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
