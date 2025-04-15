"""
Neural Bridge for BrainOS.
Provides an inter-agent communication architecture for seamless communication between 20 specialized AI agents.
"""

import os
import sys
import json
import asyncio
import time
import random
import logging
import hashlib
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime

# Add root directory to path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from agents import get_agent_details, get_available_agents
    from api_client import OpenRouterClient
    from config import OPENROUTER_API_KEY
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("Warning: BrainOS imports not available. Running in standalone mode.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neural_bridge")

class NeuralBridge:
    """
    Neural Bridge system that facilitates communication between AI agents.
    Acts as a central communication hub for the "brain" of specialized agents.
    """
    
    _agents = {}  # Static registry of agents
    _connections = {}  # Static registry of agent connections
    _message_queue = []  # Static message queue
    _message_history = {}  # Static message history by conversation ID
    _processing_functions = {}  # Static registry of processing functions
    
    @classmethod
    def register_agent(cls, agent_name: str, agent_function: Callable, metadata: Optional[Dict] = None):
        """
        Register an agent with the neural bridge.
        
        Args:
            agent_name: Name of the agent
            agent_function: Function to call when processing with this agent
            metadata: Optional metadata about the agent
        """
        agent_id = cls._generate_agent_id(agent_name)
        
        cls._agents[agent_id] = {
            "name": agent_name,
            "function": agent_function,
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat()
        }
        
        # Initialize connections list for this agent
        if agent_id not in cls._connections:
            cls._connections[agent_id] = []
            
        logger.info(f"Registered agent: {agent_name} (ID: {agent_id})")
        return agent_id
    
    @classmethod
    def connect_agents(cls, source_agent: str, target_agent: str, connection_strength: float = 1.0):
        """
        Create a connection between two agents.
        
        Args:
            source_agent: Name or ID of the source agent
            target_agent: Name or ID of the target agent
            connection_strength: Strength of the connection (0.0 to 1.0)
        """
        source_id = cls._get_agent_id(source_agent)
        target_id = cls._get_agent_id(target_agent)
        
        if not source_id or not target_id:
            raise ValueError(f"Invalid agent(s): {source_agent} -> {target_agent}")
            
        # Add connection
        cls._connections[source_id].append({
            "target": target_id,
            "strength": max(0.0, min(1.0, connection_strength))
        })
        
        logger.info(f"Created connection: {cls._agents[source_id]['name']} -> {cls._agents[target_id]['name']} (strength: {connection_strength:.2f})")
    
    @classmethod
    async def send_message(cls, 
                          source_agent: str,
                          target_agent: str, 
                          message: Dict[str, Any],
                          conversation_id: Optional[str] = None) -> str:
        """
        Send a message from one agent to another.
        
        Args:
            source_agent: Name or ID of the sending agent
            target_agent: Name or ID of the receiving agent
            message: Message content
            conversation_id: Optional conversation ID to group related messages
            
        Returns:
            Message ID
        """
        source_id = cls._get_agent_id(source_agent)
        target_id = cls._get_agent_id(target_agent)
        
        if not source_id or not target_id:
            raise ValueError(f"Invalid agent(s): {source_agent} -> {target_agent}")
            
        # Generate message ID and conversation ID
        message_id = cls._generate_message_id()
        if not conversation_id:
            conversation_id = cls._generate_conversation_id()
            
        # Create message object
        message_obj = {
            "id": message_id,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "source": source_id,
            "target": target_id,
            "content": message,
            "status": "pending"
        }
        
        # Add to queue
        cls._message_queue.append(message_obj)
        
        # Add to history
        if conversation_id not in cls._message_history:
            cls._message_history[conversation_id] = []
        cls._message_history[conversation_id].append(message_obj)
        
        # Process message asynchronously
        asyncio.create_task(cls._process_message(message_obj))
        
        return message_id
    
    @classmethod
    async def broadcast_message(cls,
                              source_agent: str,
                              message: Dict[str, Any],
                              target_filter: Optional[Callable] = None,
                              conversation_id: Optional[str] = None) -> List[str]:
        """
        Broadcast a message from one agent to multiple agents.
        
        Args:
            source_agent: Name or ID of the sending agent
            message: Message content
            target_filter: Optional function to filter target agents
            conversation_id: Optional conversation ID to group related messages
            
        Returns:
            List of message IDs
        """
        source_id = cls._get_agent_id(source_agent)
        if not source_id:
            raise ValueError(f"Invalid source agent: {source_agent}")
            
        # Find connected agents
        connected_agents = []
        for agent_id in cls._agents:
            if agent_id == source_id:
                continue
                
            # Check if there's a connection
            for conn in cls._connections.get(source_id, []):
                if conn["target"] == agent_id:
                    connected_agents.append(agent_id)
                    break
        
        # Apply filter if provided
        if target_filter and callable(target_filter):
            filtered_agents = []
            for agent_id in connected_agents:
                agent_data = cls._agents[agent_id]
                if target_filter(agent_data):
                    filtered_agents.append(agent_id)
            connected_agents = filtered_agents
        
        # Send message to each target
        message_ids = []
        send_tasks = []
        
        for target_id in connected_agents:
            send_task = cls.send_message(
                source_agent=source_id,
                target_agent=target_id,
                message=message,
                conversation_id=conversation_id
            )
            send_tasks.append(send_task)
        
        # Wait for all messages to be sent
        if send_tasks:
            message_ids = await asyncio.gather(*send_tasks)
        
        return message_ids
    
    @classmethod
    async def process_task(cls, 
                          task: Dict[str, Any],
                          agents: Optional[List[str]] = None,
                          conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a task through multiple agents in sequence.
        
        Args:
            task: Task description and content
            agents: Optional list of agents to use. If None, selects automatically.
            conversation_id: Optional conversation ID
            
        Returns:
            Processing results and conversation history
        """
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = cls._generate_conversation_id()
            
        # Select agents if not specified
        if not agents:
            agents = await cls._select_agents_for_task(task)
            
        if not agents:
            raise ValueError("No agents available to process task")
            
        # Initialize results
        results = {
            "conversation_id": conversation_id,
            "task": task,
            "agents_used": agents,
            "agent_outputs": {},
            "final_output": None,
            "processing_time": 0
        }
        
        start_time = time.time()
        
        # Process through agents in sequence
        current_state = task.copy()  # Start with original task
        
        for i, agent_name in enumerate(agents):
            agent_id = cls._get_agent_id(agent_name)
            if not agent_id:
                logger.warning(f"Invalid agent: {agent_name}, skipping")
                continue
                
            try:
                # Get the agent's processing function
                agent_info = cls._agents[agent_id]
                process_func = agent_info["function"]
                
                # Add context from previous agents
                if i > 0:
                    current_state["previous_outputs"] = {
                        agents[j]: results["agent_outputs"][agents[j]]
                        for j in range(i)
                        if agents[j] in results["agent_outputs"]
                    }
                
                # Process with this agent
                logger.info(f"Processing with agent: {agent_name}")
                agent_output = await process_func(current_state)
                
                # Store result
                results["agent_outputs"][agent_name] = agent_output
                
                # Update current state for next agent
                current_state["current_state"] = agent_output
                
            except Exception as e:
                logger.error(f"Error processing with agent {agent_name}: {str(e)}")
                results["agent_outputs"][agent_name] = {"error": str(e)}
        
        # Calculate processing time
        results["processing_time"] = time.time() - start_time
        
        # Set final output to the last agent's output
        if agents and agents[-1] in results["agent_outputs"]:
            results["final_output"] = results["agent_outputs"][agents[-1]]
        
        return results
    
    @classmethod
    async def get_conversation_history(cls, conversation_id: str) -> List[Dict[str, Any]]:
        """Get the history of messages for a conversation."""
        return cls._message_history.get(conversation_id, [])
    
    @classmethod
    def get_agent_info(cls, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered agent."""
        agent_id = cls._get_agent_id(agent_name)
        if not agent_id:
            return None
        return cls._agents.get(agent_id)
    
    @classmethod
    def get_registered_agents(cls) -> List[Dict[str, Any]]:
        """Get a list of all registered agents."""
        return [
            {
                "id": agent_id,
                "name": info["name"],
                "metadata": info["metadata"],
                "connections": len(cls._connections.get(agent_id, []))
            }
            for agent_id, info in cls._agents.items()
        ]
    
    @classmethod
    def register_processing_function(cls, function_name: str, function_impl: Callable):
        """Register a global processing function that can be used by agents."""
        cls._processing_functions[function_name] = function_impl
        logger.info(f"Registered processing function: {function_name}")
    
    @classmethod
    def get_processing_function(cls, function_name: str) -> Optional[Callable]:
        """Get a registered processing function by name."""
        return cls._processing_functions.get(function_name)
    
    @classmethod
    async def _process_message(cls, message: Dict[str, Any]) -> None:
        """Process a message by calling the target agent's function."""
        try:
            target_id = message["target"]
            if target_id not in cls._agents:
                logger.warning(f"Target agent not found: {target_id}")
                message["status"] = "failed"
                message["error"] = "Target agent not found"
                return
                
            # Get the agent's processing function
            target_agent = cls._agents[target_id]
            process_func = target_agent["function"]
            
            # Call the processing function
            result = await process_func(message["content"])
            
            # Update message with result
            message["status"] = "processed"
            message["response"] = result
            message["processed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error processing message {message['id']}: {str(e)}")
            message["status"] = "failed"
            message["error"] = str(e)
    
    @classmethod
    async def _select_agents_for_task(cls, task: Dict[str, Any]) -> List[str]:
        """
        Select appropriate agents for a task.
        
        In a full implementation, this would use machine learning or 
        a meta-agent to select appropriate agents.
        """
        if not cls._agents:
            return []
            
        # Simple implementation: select up to 3 random agents
        agent_names = [info["name"] for info in cls._agents.values()]
        selected = random.sample(agent_names, min(3, len(agent_names)))
        
        return selected
    
    @classmethod
    def _generate_agent_id(cls, agent_name: str) -> str:
        """Generate a unique ID for an agent."""
        return hashlib.sha256(agent_name.encode('utf-8')).hexdigest()[:12]
    
    @classmethod
    def _generate_message_id(cls) -> str:
        """Generate a unique message ID."""
        return f"msg_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    
    @classmethod
    def _generate_conversation_id(cls) -> str:
        """Generate a unique conversation ID."""
        return f"conv_{int(time.time())}_{random.randint(1000, 9999)}"
    
    @classmethod
    def _get_agent_id(cls, agent_identifier: str) -> Optional[str]:
        """
        Get an agent's ID from either name or ID.
        
        Args:
            agent_identifier: Either agent name or agent ID
            
        Returns:
            Agent ID if found, None otherwise
        """
        # Check if it's already an ID
        if agent_identifier in cls._agents:
            return agent_identifier
            
        # Look up by name
        for agent_id, info in cls._agents.items():
            if info["name"] == agent_identifier:
                return agent_id
                
        return None

# Sample agent processing functions for testing
async def reasoning_agent_process(message: Dict[str, Any]) -> Dict[str, Any]:
    """Sample reasoning agent processing function."""
    return {
        "analysis": f"Reasoning analysis of: {message.get('content', 'No content')}",
        "processed_at": datetime.now().isoformat()
    }

async def creative_agent_process(message: Dict[str, Any]) -> Dict[str, Any]:
    """Sample creative agent processing function."""
    return {
        "ideas": [
            f"Idea 1 related to {message.get('topic', 'unknown topic')}",
            f"Idea 2 with a creative twist",
            f"Idea 3 thinking outside the box"
        ],
        "processed_at": datetime.now().isoformat()
    }

# Test function
async def test_neural_bridge():
    """Test the neural bridge with sample agents."""
    # Register test agents
    NeuralBridge.register_agent("reasoning_agent", reasoning_agent_process, {
        "capabilities": ["logical analysis", "problem solving", "deduction"],
        "model": "gpt-4"
    })
    
    NeuralBridge.register_agent("creative_agent", creative_agent_process, {
        "capabilities": ["idea generation", "creative thinking", "innovation"],
        "model": "claude-3"
    })
    
    # Connect agents
    NeuralBridge.connect_agents("reasoning_agent", "creative_agent", 0.8)
    
    # Send a test message
    message_id = await NeuralBridge.send_message(
        source_agent="reasoning_agent",
        target_agent="creative_agent",
        message={
            "topic": "renewable energy solutions",
            "context": "Urban environments with limited space"
        }
    )
    
    # Wait for processing
    await asyncio.sleep(1)
    
    # Get all registered agents
    agents = NeuralBridge.get_registered_agents()
    print("Registered agents:")
    for agent in agents:
        print(f"- {agent['name']} (ID: {agent['id']})")
        
    # Process a task through multiple agents
    task_result = await NeuralBridge.process_task({
        "description": "Analyze renewable energy options for urban environments",
        "requirements": ["efficiency", "cost-effectiveness", "space utilization"],
        "constraints": ["limited roof space", "noise regulations", "budget constraints"]
    })
    
    print("\nTask processing results:")
    print(f"Agents used: {task_result['agents_used']}")
    print(f"Processing time: {task_result['processing_time']:.2f}s")
    print(f"Final output: {task_result.get('final_output')}")

if __name__ == "__main__":
    asyncio.run(test_neural_bridge())