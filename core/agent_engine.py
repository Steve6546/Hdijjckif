"""
Agent Engine for the All-Agents-App
This module coordinates the execution of agents and manages their interactions.
"""

import os
import logging
import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentEngine:
    """
    Coordinates the execution of agents and manages their interactions.
    Acts as the central brain for agent orchestration.
    """
    
    def __init__(self, agents: Dict[str, Any] = None):
        """
        Initialize the agent engine.
        
        Args:
            agents: Dictionary of agent instances keyed by agent name
        """
        self.agents = agents or {}
        logger.info(f"AgentEngine initialized with {len(self.agents)} agents: {list(self.agents.keys())}")
        
        # Dictionary to store agent states
        self.agent_states = {}
        
        # Dictionary to store conversation history
        self.conversation_history = {}
    
    def register_agent(self, name: str, agent: Any) -> None:
        """
        Register an agent with the engine.
        
        Args:
            name: Name of the agent
            agent: Agent instance
        """
        self.agents[name] = agent
        self.agent_states[name] = {"status": "idle"}
        logger.info(f"Registered agent: {name}")
    
    def get_agent(self, name: str) -> Optional[Any]:
        """
        Get an agent by name.
        
        Args:
            name: Name of the agent
            
        Returns:
            Agent instance, or None if not found
        """
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """
        List all registered agents.
        
        Returns:
            List of agent names
        """
        return list(self.agents.keys())
    
    def get_agent_state(self, name: str) -> Dict[str, Any]:
        """
        Get the state of an agent.
        
        Args:
            name: Name of the agent
            
        Returns:
            Agent state dictionary
        """
        return self.agent_states.get(name, {"status": "unknown"})
    
    def set_agent_state(self, name: str, state: Dict[str, Any]) -> None:
        """
        Set the state of an agent.
        
        Args:
            name: Name of the agent
            state: Agent state dictionary
        """
        self.agent_states[name] = state
    
    def execute_agent(self, name: str, input_data: Any) -> Dict[str, Any]:
        """
        Execute an agent with the given input.
        
        Args:
            name: Name of the agent
            input_data: Input data for the agent
            
        Returns:
            Dict containing the result of the operation
        """
        if name not in self.agents:
            logger.error(f"Agent '{name}' not found")
            return {
                "status": "error",
                "message": f"Agent '{name}' not found"
            }
        
        agent = self.agents[name]
        
        try:
            # Update agent state
            self.agent_states[name] = {"status": "running"}
            
            # Execute the agent
            if hasattr(agent, 'execute') and callable(agent.execute):
                result = agent.execute(input_data)
            elif hasattr(agent, 'process') and callable(agent.process):
                result = agent.process(input_data)
            elif hasattr(agent, 'generate') and callable(agent.generate):
                result = agent.generate(input_data)
            elif hasattr(agent, 'handle') and callable(agent.handle):
                result = agent.handle(input_data)
            else:
                logger.error(f"Agent '{name}' does not have a valid interface method")
                self.agent_states[name] = {"status": "error", "message": "No valid interface method"}
                return {
                    "status": "error",
                    "message": f"Agent '{name}' does not have a valid interface method"
                }
            
            # Update agent state
            self.agent_states[name] = {"status": "idle"}
            
            # Standardize the result format
            if isinstance(result, dict):
                if "agent" not in result:
                    result["agent"] = name
                if "status" not in result:
                    result["status"] = "success"
                return result
            else:
                return {
                    "status": "success",
                    "message": str(result) if result is not None else "",
                    "agent": name
                }
            
        except Exception as e:
            logger.error(f"Error executing agent '{name}': {e}", exc_info=True)
            self.agent_states[name] = {"status": "error", "message": str(e)}
            return {
                "status": "error",
                "message": f"Error executing agent '{name}': {str(e)}",
                "agent": name
            }
    
    async def execute_agent_async(self, name: str, input_data: Any) -> Dict[str, Any]:
        """
        Execute an agent asynchronously with the given input.
        
        Args:
            name: Name of the agent
            input_data: Input data for the agent
            
        Returns:
            Dict containing the result of the operation
        """
        if name not in self.agents:
            logger.error(f"Agent '{name}' not found")
            return {
                "status": "error",
                "message": f"Agent '{name}' not found"
            }
        
        agent = self.agents[name]
        
        try:
            # Update agent state
            self.agent_states[name] = {"status": "running"}
            
            # Execute the agent
            if hasattr(agent, 'execute_async') and callable(agent.execute_async):
                result = await agent.execute_async(input_data)
            elif hasattr(agent, 'process_async') and callable(agent.process_async):
                result = await agent.process_async(input_data)
            elif hasattr(agent, 'generate_async') and callable(agent.generate_async):
                result = await agent.generate_async(input_data)
            elif hasattr(agent, 'handle_async') and callable(agent.handle_async):
                result = await agent.handle_async(input_data)
            else:
                # Fall back to synchronous execution
                return self.execute_agent(name, input_data)
            
            # Update agent state
            self.agent_states[name] = {"status": "idle"}
            
            # Standardize the result format
            if isinstance(result, dict):
                if "agent" not in result:
                    result["agent"] = name
                if "status" not in result:
                    result["status"] = "success"
                return result
            else:
                return {
                    "status": "success",
                    "message": str(result) if result is not None else "",
                    "agent": name
                }
            
        except Exception as e:
            logger.error(f"Error executing agent '{name}' asynchronously: {e}", exc_info=True)
            self.agent_states[name] = {"status": "error", "message": str(e)}
            return {
                "status": "error",
                "message": f"Error executing agent '{name}' asynchronously: {str(e)}",
                "agent": name
            }
    
    def execute_workflow(self, workflow: List[Dict[str, Any]], initial_input: Any = None) -> List[Dict[str, Any]]:
        """
        Execute a workflow of agent operations.
        
        Args:
            workflow: List of workflow steps, each containing agent name and input
            initial_input: Initial input for the workflow
            
        Returns:
            List of results from each workflow step
        """
        results = []
        current_input = initial_input
        
        for step in workflow:
            agent_name = step.get("agent")
            if not agent_name:
                logger.error("Workflow step missing agent name")
                results.append({
                    "status": "error",
                    "message": "Workflow step missing agent name"
                })
                continue
            
            # Get input for this step
            step_input = step.get("input", current_input)
            
            # Execute the agent
            result = self.execute_agent(agent_name, step_input)
            results.append(result)
            
            # Update current input for the next step if needed
            if step.get("pass_result", True):
                current_input = result
            
            # Check if we should continue based on the result
            if step.get("continue_on_error", True) is False and result.get("status") == "error":
                logger.warning(f"Workflow stopped due to error in step with agent '{agent_name}'")
                break
        
        return results
    
    async def execute_workflow_async(self, workflow: List[Dict[str, Any]], initial_input: Any = None) -> List[Dict[str, Any]]:
        """
        Execute a workflow of agent operations asynchronously.
        
        Args:
            workflow: List of workflow steps, each containing agent name and input
            initial_input: Initial input for the workflow
            
        Returns:
            List of results from each workflow step
        """
        results = []
        current_input = initial_input
        
        for step in workflow:
            agent_name = step.get("agent")
            if not agent_name:
                logger.error("Workflow step missing agent name")
                results.append({
                    "status": "error",
                    "message": "Workflow step missing agent name"
                })
                continue
            
            # Get input for this step
            step_input = step.get("input", current_input)
            
            # Execute the agent
            result = await self.execute_agent_async(agent_name, step_input)
            results.append(result)
            
            # Update current input for the next step if needed
            if step.get("pass_result", True):
                current_input = result
            
            # Check if we should continue based on the result
            if step.get("continue_on_error", True) is False and result.get("status") == "error":
                logger.warning(f"Workflow stopped due to error in step with agent '{agent_name}'")
                break
        
        return results
    
    def add_to_conversation(self, conversation_id: str, message: Dict[str, Any]) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            conversation_id: ID of the conversation
            message: Message to add
        """
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = time.time()
        
        self.conversation_history[conversation_id].append(message)
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get the conversation history.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of messages in the conversation
        """
        return self.conversation_history.get(conversation_id, [])