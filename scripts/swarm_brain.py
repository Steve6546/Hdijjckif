"""
Swarm Brain for BrainOS.
Implements a collective intelligence system where agents collaborate like a neural network.
"""

import os
import sys
import json
import time
import asyncio
import logging
import random
import networkx as nx
from typing import Dict, List, Any, Optional, Set, Tuple
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
logger = logging.getLogger("swarm_brain")

class SwarmBrain:
    """
    Swarm Brain system that coordinates multiple AI agents in a network structure.
    Agents communicate and self-organize to solve complex problems.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the swarm brain.
        
        Args:
            api_key: Optional OpenRouter API key. If None, uses config.
        """
        if IMPORTS_AVAILABLE:
            self.api_key = api_key or OPENROUTER_API_KEY
            self.client = OpenRouterClient(self.api_key)
            self.available_agents = get_available_agents()
        else:
            self.api_key = api_key
            self.client = None
            self.available_agents = []
            logger.warning("Running in standalone mode without BrainOS imports")
        
        # Initialize the agent network
        self.agent_network = nx.DiGraph()
        self.agent_states = {}
        self.message_history = []
        self.activation_threshold = 0.5
        self.knowledge_base = {}
        
    def initialize_network(self, num_agents: Optional[int] = None):
        """
        Initialize the agent network with connections.
        
        Args:
            num_agents: Number of agents to include. If None, uses all available.
        """
        # Clear existing network
        self.agent_network.clear()
        self.agent_states = {}
        
        # Get agents to include
        if not self.available_agents:
            # Create sample agents for standalone mode
            sample_agents = [
                "reasoning_agent", "creative_agent", "analytical_agent",
                "memory_agent", "planning_agent", "critic_agent",
                "research_agent", "integration_agent", "execution_agent"
            ]
            agents_to_use = sample_agents[:num_agents] if num_agents else sample_agents
        else:
            agents_to_use = self.available_agents
            if num_agents:
                agents_to_use = random.sample(agents_to_use, min(num_agents, len(agents_to_use)))
        
        # Add nodes to the network
        for agent in agents_to_use:
            self.agent_network.add_node(agent)
            
            # Initialize agent state
            self.agent_states[agent] = {
                "activation": 0.0,  # Level of activation (0.0 to 1.0)
                "memory": [],      # Short-term memory for this agent
                "expertise": self._get_agent_capabilities(agent),
                "last_output": "",
                "connections": []
            }
        
        # Create connections between agents (not fully connected)
        # Each agent connects to approximately 1/3 of other agents
        for agent in agents_to_use:
            num_connections = max(1, len(agents_to_use) // 3)
            potential_connections = [a for a in agents_to_use if a != agent]
            connections = random.sample(
                potential_connections, 
                min(num_connections, len(potential_connections))
            )
            
            for target in connections:
                # Add weighted edge
                weight = random.uniform(0.3, 0.9)
                self.agent_network.add_edge(agent, target, weight=weight)
                self.agent_states[agent]["connections"].append(target)
        
        logger.info(f"Initialized swarm brain with {len(agents_to_use)} agents and "
                   f"{self.agent_network.number_of_edges()} connections")
    
    async def process_query(self, query: str, max_steps: int = 5) -> Dict[str, Any]:
        """
        Process a query through the swarm brain.
        
        Args:
            query: The query or problem to process
            max_steps: Maximum number of thinking steps
            
        Returns:
            Dict containing results and processing details
        """
        if not self.agent_network or not self.agent_states:
            self.initialize_network()
            
        logger.info(f"Processing query with swarm brain: {query}")
        
        # Reset activation levels and message history
        for agent in self.agent_states:
            self.agent_states[agent]["activation"] = 0.0
        self.message_history = []
        
        # Initial query analysis to determine which agents to activate
        initial_agents = await self._select_initial_agents(query)
        
        # Activate initial agents
        for agent in initial_agents:
            self.agent_states[agent]["activation"] = 1.0
            logger.info(f"Initially activated agent: {agent}")
        
        # Main processing loop
        all_responses = {}
        active_agents = set(initial_agents)
        
        for step in range(max_steps):
            logger.info(f"Processing step {step+1}/{max_steps}")
            
            # Process all currently active agents
            step_responses = {}
            new_active_agents = set()
            
            for agent in active_agents:
                # Process with this agent
                response = await self._process_with_agent(agent, query, step)
                step_responses[agent] = response
                all_responses[agent] = response
                
                # Update agent state
                self.agent_states[agent]["last_output"] = response
                
                # Propagate activation to connected agents
                await self._propagate_activation(agent, query, response)
                
                # Collect newly activated agents
                for connected_agent, state in self.agent_states.items():
                    if (connected_agent not in active_agents and 
                        state["activation"] >= self.activation_threshold):
                        new_active_agents.add(connected_agent)
            
            # Update currently active agents
            active_agents = new_active_agents
            
            # If no more agents are active, break the loop
            if not active_agents:
                logger.info(f"No more active agents after step {step+1}, ending process")
                break
                
            # Record this step
            self.message_history.append({
                "step": step,
                "active_agents": list(active_agents),
                "responses": step_responses
            })
        
        # Final integration of results
        final_response = await self._integrate_results(query, all_responses)
        
        # Prepare result
        result = {
            "query": query,
            "final_response": final_response,
            "contributing_agents": list(all_responses.keys()),
            "steps_taken": len(self.message_history) + 1,
            "message_history": self.message_history,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save result
        self._save_result(query, result)
        
        return result
    
    async def _select_initial_agents(self, query: str) -> List[str]:
        """Select the initial set of agents to activate for a query."""
        if not self.client:
            # In standalone mode, randomly select 2-3 initial agents
            return random.sample(list(self.agent_states.keys()), 
                                min(3, len(self.agent_states)))
        
        # Use a meta-agent to select initial agents
        try:
            # Select a meta-agent model
            model = "anthropic/claude-3-opus"
            
            prompt = f"""
            Analyze this query and determine which types of AI agents would be best suited 
            to begin working on it.
            
            QUERY: {query}
            
            AVAILABLE AGENT TYPES:
            {self._format_available_agents()}
            
            Select 2-3 agents that would be most appropriate to start working on this query.
            Return only the agent names as a comma-separated list.
            """
            
            response = await self.client.process_with_agent(
                agent_model=model,
                text=prompt,
                system_prompt="You are an expert system that can identify which AI agent types would be most suited for different queries."
            )
            
            # Parse the response to extract agent names
            agents = [name.strip() for name in response.split(",")]
            
            # Filter to ensure only valid agents are returned
            valid_agents = [a for a in agents if a in self.agent_states]
            
            # Ensure we have at least one agent
            if not valid_agents and self.agent_states:
                valid_agents = [random.choice(list(self.agent_states.keys()))]
                
            return valid_agents
            
        except Exception as e:
            logger.error(f"Error selecting initial agents: {str(e)}")
            # Fallback to random selection
            return random.sample(list(self.agent_states.keys()), 
                                min(2, len(self.agent_states)))
    
    async def _process_with_agent(self, agent_name: str, original_query: str, step: int) -> str:
        """Process the query with a specific agent."""
        if not self.client:
            # In standalone mode, return a mock response
            return f"Analysis from {agent_name} at step {step}: The query '{original_query}' requires further investigation."
        
        try:
            # Get agent details if available
            if IMPORTS_AVAILABLE:
                agent_details = get_agent_details(agent_name)
                model = agent_details.get("model", "anthropic/claude-3-opus")
                description = agent_details.get("description", f"You are a {agent_name}")
            else:
                model = "anthropic/claude-3-opus"
                description = f"You are a {agent_name.replace('_', ' ')}"
            
            # Create context from other agents' outputs
            context = self._get_context_for_agent(agent_name)
            
            # Create a prompt for this agent
            prompt = f"""
            QUERY: {original_query}
            
            PROCESSING STEP: {step+1}
            
            YOUR ROLE: {agent_name}
            
            CONTEXT FROM OTHER AGENTS:
            {context}
            
            INSTRUCTIONS:
            1. Analyze the query based on your specific expertise and role
            2. Consider the context provided by other agents
            3. Provide your unique perspective and insights
            4. Be concise but thorough in your analysis
            5. Focus on adding new information or perspectives
            
            Your response:
            """
            
            # Process with the agent
            response = await self.client.process_with_agent(
                agent_model=model,
                text=prompt,
                system_prompt=description
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing with agent {agent_name}: {str(e)}")
            return f"Error processing with {agent_name}: {str(e)}"
    
    async def _propagate_activation(self, source_agent: str, query: str, response: str) -> None:
        """
        Propagate activation from a source agent to connected agents.
        
        Args:
            source_agent: The agent sending activation
            query: The original query
            response: The agent's response
        """
        # Get outgoing connections from the source agent
        if source_agent not in self.agent_network:
            return
            
        for target_agent in self.agent_network.successors(source_agent):
            # Get the connection weight
            weight = self.agent_network[source_agent][target_agent].get("weight", 0.5)
            
            # Calculate relevance of the source agent's response to the target agent
            relevance = await self._calculate_relevance(
                source_agent, target_agent, query, response
            )
            
            # Calculate activation to propagate (weight * relevance)
            activation_delta = weight * relevance
            
            # Update target agent's activation
            current_activation = self.agent_states[target_agent]["activation"]
            new_activation = min(1.0, current_activation + activation_delta)
            self.agent_states[target_agent]["activation"] = new_activation
            
            logger.debug(f"Propagated activation from {source_agent} to {target_agent}: "
                        f"{current_activation:.2f} -> {new_activation:.2f}")
            
            # Store the message in target agent's memory
            if new_activation > current_activation:
                memory_entry = {
                    "from": source_agent,
                    "content": self._summarize_text(response, 100),
                    "time": time.time()
                }
                self.agent_states[target_agent]["memory"].append(memory_entry)
                
                # Limit memory size
                if len(self.agent_states[target_agent]["memory"]) > 5:
                    self.agent_states[target_agent]["memory"].pop(0)
    
    async def _calculate_relevance(
        self, source_agent: str, target_agent: str, query: str, response: str
    ) -> float:
        """
        Calculate the relevance of a source agent's response to a target agent.
        
        In a full implementation, this would use a model to calculate relevance.
        Here we use a simplified approach.
        """
        # If we don't have the client, use random relevance
        if not self.client:
            return random.uniform(0.3, 0.9)
            
        # Simple relevance calculation based on expertise overlap
        source_expertise = self.agent_states[source_agent]["expertise"]
        target_expertise = self.agent_states[target_agent]["expertise"]
        
        # Check for keyword overlap in response and target expertise
        relevance = 0.3  # Base relevance
        
        for keyword in target_expertise:
            if keyword.lower() in response.lower():
                relevance += 0.1
                
        # Check expertise overlap
        common_expertise = set(source_expertise).intersection(set(target_expertise))
        relevance += len(common_expertise) * 0.1
        
        # Cap at 0.9 maximum relevance
        return min(0.9, relevance)
    
    async def _integrate_results(self, query: str, all_responses: Dict[str, str]) -> str:
        """
        Integrate all agent responses into a final coherent response.
        
        Args:
            query: The original query
            all_responses: Dictionary of agent responses
            
        Returns:
            Integrated response
        """
        if not self.client or not all_responses:
            # In standalone mode or no responses, return a summary
            return f"Integrated analysis of {len(all_responses)} agents on the query: {query}"
            
        try:
            # Use an integration model
            model = "anthropic/claude-3-opus"
            
            # Format all agent responses
            all_insights = "\n\n".join([
                f"[{agent}]: {response}" 
                for agent, response in all_responses.items()
            ])
            
            # Create integration prompt
            prompt = f"""
            QUERY: {query}
            
            INSIGHTS FROM VARIOUS AGENTS:
            {all_insights}
            
            TASK:
            Synthesize these various insights into a comprehensive, coherent response.
            Integrate the perspectives while resolving any contradictions.
            Provide a clear, well-structured answer to the original query.
            """
            
            # Process with integration agent
            integrated_response = await self.client.process_with_agent(
                agent_model=model,
                text=prompt,
                system_prompt="You are an expert integrator that synthesizes insights from multiple AI agents into coherent, comprehensive responses."
            )
            
            return integrated_response
            
        except Exception as e:
            logger.error(f"Error integrating results: {str(e)}")
            
            # Fallback integration method - concatenate with headers
            integrated = f"Integrated response to: {query}\n\n"
            for agent, response in all_responses.items():
                integrated += f"=== {agent} ===\n{self._summarize_text(response, 200)}\n\n"
            
            return integrated
    
    def visualize_network(self, output_file: str = "agent_network.png") -> None:
        """
        Visualize the agent network and save to a file.
        
        Args:
            output_file: Path to save the visualization
        """
        try:
            import matplotlib.pyplot as plt
            
            # Create the plot
            plt.figure(figsize=(12, 10))
            
            # Get position layout
            pos = nx.spring_layout(self.agent_network)
            
            # Get node colors based on activation
            node_colors = [
                self.agent_states.get(node, {}).get("activation", 0.0)
                for node in self.agent_network.nodes()
            ]
            
            # Get edge weights
            edge_weights = [
                self.agent_network[u][v].get("weight", 0.5) * 5
                for u, v in self.agent_network.edges()
            ]
            
            # Draw the network
            nx.draw_networkx_nodes(
                self.agent_network, pos, 
                node_color=node_colors, 
                cmap=plt.cm.Reds,
                node_size=800,
                alpha=0.8
            )
            
            nx.draw_networkx_edges(
                self.agent_network, pos,
                width=edge_weights,
                alpha=0.5,
                edge_color="gray",
                arrows=True,
                arrowsize=15
            )
            
            nx.draw_networkx_labels(
                self.agent_network, pos,
                font_size=10,
                font_family="sans-serif"
            )
            
            plt.title("Agent Swarm Network")
            plt.axis("off")
            
            # Save the visualization
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()
            
            logger.info(f"Network visualization saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error visualizing network: {str(e)}")
    
    def _get_agent_capabilities(self, agent_name: str) -> List[str]:
        """Get capabilities of an agent."""
        if IMPORTS_AVAILABLE:
            try:
                agent_details = get_agent_details(agent_name)
                return agent_details.get("capabilities", [])
            except:
                pass
                
        # Fallback to generated capabilities based on agent name
        capabilities = []
        name_parts = agent_name.replace("_", " ").split()
        
        common_capabilities = {
            "reasoning": ["logic", "inference", "deduction"],
            "creative": ["ideation", "imagination", "originality"],
            "analytical": ["analysis", "evaluation", "assessment"],
            "research": ["investigation", "fact-checking", "data collection"],
            "memory": ["recall", "storage", "retention"],
            "planning": ["organization", "strategizing", "sequencing"],
            "execution": ["implementation", "action", "operation"],
            "integration": ["synthesis", "combination", "aggregation"]
        }
        
        for part in name_parts:
            if part.lower() in common_capabilities:
                capabilities.extend(common_capabilities[part.lower()])
        
        # Add some generic capabilities if we found none
        if not capabilities:
            capabilities = ["processing", "evaluation", "response generation"]
            
        return capabilities
    
    def _get_context_for_agent(self, agent_name: str) -> str:
        """Get relevant context from other agents for this agent."""
        context = ""
        
        # Compile relevant messages from other agents
        incoming_agents = list(self.agent_network.predecessors(agent_name)) \
            if agent_name in self.agent_network else []
            
        for source_agent in incoming_agents:
            last_output = self.agent_states[source_agent].get("last_output", "")
            if last_output:
                context += f"FROM {source_agent}:\n{self._summarize_text(last_output, 150)}\n\n"
        
        if not context:
            context = "No context available from other agents yet."
            
        return context
    
    def _summarize_text(self, text: str, max_length: int = 100) -> str:
        """Summarize text to a maximum length."""
        if len(text) <= max_length:
            return text
            
        # Simple truncation with ellipsis
        return text[:max_length-3] + "..."
    
    def _format_available_agents(self) -> str:
        """Format the available agents for prompts."""
        formatted = ""
        for agent in self.agent_states:
            expertise = ", ".join(self.agent_states[agent]["expertise"][:5])
            formatted += f"- {agent}: {expertise}\n"
        return formatted
    
    def _save_result(self, query: str, result: Dict[str, Any]) -> None:
        """Save the result to a file."""
        try:
            # Create a filename based on the query
            query_hash = hash(query) % 10000
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cache/swarm_{query_hash}_{timestamp}.json"
            
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w') as f:
                # Create a simplified version for storage
                storage_result = {
                    "query": query,
                    "final_response": result["final_response"],
                    "contributing_agents": result["contributing_agents"],
                    "steps_taken": result["steps_taken"],
                    "timestamp": result["timestamp"]
                }
                json.dump(storage_result, f, indent=2)
                
            logger.info(f"Saved swarm brain result to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save result: {str(e)}")

# Test function
async def test_swarm_brain():
    """Test the swarm brain with a sample query."""
    try:
        # Try to import networkx
        import networkx as nx
    except ImportError:
        print("NetworkX is required for SwarmBrain. Install with 'pip install networkx'")
        return
        
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Note: Matplotlib is not installed. Network visualization will be disabled.")
    
    brain = SwarmBrain()
    brain.initialize_network(num_agents=7)
    
    test_query = "What are the most promising renewable energy technologies for urban environments?"
    
    print(f"Processing query with swarm brain: {test_query}")
    result = await brain.process_query(test_query, max_steps=3)
    
    print("\n====== FINAL RESPONSE ======")
    print(result["final_response"])
    
    print("\n====== CONTRIBUTING AGENTS ======")
    for agent in result["contributing_agents"]:
        print(f"- {agent}")
        
    print(f"\nProcessed in {result['steps_taken']} steps")
    
    # Try to visualize the network
    try:
        brain.visualize_network()
        print("Network visualization saved to agent_network.png")
    except Exception as e:
        print(f"Could not visualize network: {e}")

if __name__ == "__main__":
    asyncio.run(test_swarm_brain())