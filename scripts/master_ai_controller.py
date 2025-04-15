"""
Master AI Controller for the BrainOS system.
Provides automated management of the multi-agent environment with self-improvement capabilities.
"""

import os
import sys
import time
import json
import logging
import asyncio
import threading
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add root directory to path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import OpenRouterClient
from agents import get_agent_details, get_available_agents
from orchestrator import BrainOrchestrator
from utils import generate_session_id, save_interaction_log
from config import OPENROUTER_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/master_controller.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("master_controller")

class MasterController:
    """
    Master controller that manages the AI brain orchestration system.
    Can operate autonomously to perform various tasks including self-improvement.
    """
    
    def __init__(self):
        """Initialize the master controller."""
        self.orchestrator = BrainOrchestrator(api_key=OPENROUTER_API_KEY)
        self.api_client = OpenRouterClient(api_key=OPENROUTER_API_KEY)
        self.session_id = generate_session_id()
        self.agent_cache = {}
        self.running = False
        self.last_activity = datetime.now()
        
    async def initialize(self):
        """Initialize the controller and verify connectivity."""
        logger.info("Initializing master controller...")
        
        try:
            # Test connection to OpenRouter.ai
            models = await self.orchestrator.get_available_models()
            logger.info(f"Connected to OpenRouter.ai - {len(models)} models available")
            
            # Initialize agent cache with metadata
            available_agents = get_available_agents()
            for agent_name in available_agents:
                agent_details = get_agent_details(agent_name)
                self.agent_cache[agent_name] = {
                    "name": agent_name,
                    "model": agent_details["model"],
                    "capabilities": agent_details.get("capabilities", []),
                    "last_used": None,
                    "success_rate": 1.0
                }
            
            logger.info(f"Initialized {len(self.agent_cache)} agents")
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            return False
    
    async def run_autonomous_cycle(self):
        """Run a complete autonomous processing cycle."""
        if not self.running:
            return
            
        try:
            # 1. Self-assessment: Check agent performance and system health
            logger.info("Running autonomous cycle - self-assessment")
            health_check = await self._perform_health_check()
            
            # 2. Improvement: Update agent prompts if needed
            if random.random() < 0.2:  # 20% chance to perform improvement
                logger.info("Running autonomous cycle - self-improvement")
                await self._perform_self_improvement()
            
            # 3. Simulation: Run test scenarios to evaluate system performance
            logger.info("Running autonomous cycle - simulation")
            await self._run_test_scenarios()
            
            # 4. Update state
            self.last_activity = datetime.now()
            logger.info(f"Autonomous cycle completed successfully")
            
        except Exception as e:
            logger.error(f"Error in autonomous cycle: {str(e)}")
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """Check the health of the system components."""
        health_status = {
            "status": "operational",
            "components": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check API connectivity
        try:
            models = await self.orchestrator.get_available_models()
            health_status["components"]["api_connectivity"] = {
                "status": "operational",
                "models_available": len(models)
            }
        except Exception as e:
            health_status["components"]["api_connectivity"] = {
                "status": "degraded",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check agent availability
        try:
            available_agents = get_available_agents()
            health_status["components"]["agents"] = {
                "status": "operational",
                "count": len(available_agents)
            }
        except Exception as e:
            health_status["components"]["agents"] = {
                "status": "degraded",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Save health status to a file
        health_file = "logs/health_status.json"
        try:
            with open(health_file, "w") as f:
                json.dump(health_status, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save health status: {str(e)}")
        
        return health_status
    
    async def _perform_self_improvement(self):
        """
        Perform self-improvement by analyzing past interactions and updating agent prompts.
        This is a theoretical implementation and would need customization for real-world use.
        """
        # Select a random agent to improve
        available_agents = get_available_agents()
        if not available_agents:
            logger.warning("No agents available for self-improvement")
            return
            
        agent_to_improve = random.choice(available_agents)
        logger.info(f"Attempting to improve agent: {agent_to_improve}")
        
        # Get current agent details
        agent_details = get_agent_details(agent_to_improve)
        current_prompt = agent_details.get("system_prompt", "")
        
        # Analyze the prompt using a meta-agent
        meta_agent_name = random.choice(available_agents)
        meta_agent_details = get_agent_details(meta_agent_name)
        
        improvement_prompt = f"""
        You are a meta-cognitive AI that improves AI system prompts.
        
        Analyze this system prompt for an AI agent named "{agent_to_improve}":
        
        CURRENT PROMPT:
        "{current_prompt}"
        
        CAPABILITIES:
        {agent_details.get('capabilities', [])}
        
        DESCRIPTION:
        {agent_details.get('description', 'No description available')}
        
        Suggest improvements to make this prompt more effective, clear, and aligned with the agent's purpose.
        Keep your response focused only on specific improvements to the prompt.
        """
        
        try:
            improved_prompt = await self.api_client.process_with_agent(
                agent_model=meta_agent_details["model"],
                text=improvement_prompt,
                system_prompt="You are an expert at creating effective AI system prompts."
            )
            
            logger.info(f"Generated potential improvement for {agent_to_improve}")
            
            # In a real implementation, you might:
            # 1. Save this to a suggestions file
            # 2. Have a human review the changes
            # 3. Implement an automated A/B testing system
            
            # For now, we'll just log the suggestion
            improvement_file = f"logs/agents/{agent_to_improve}_improvement.txt"
            os.makedirs(os.path.dirname(improvement_file), exist_ok=True)
            
            with open(improvement_file, "w") as f:
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Current prompt: {current_prompt}\n\n")
                f.write(f"Suggested improvement:\n{improved_prompt}\n")
            
            logger.info(f"Saved improvement suggestion to {improvement_file}")
            
        except Exception as e:
            logger.error(f"Error in self-improvement for {agent_to_improve}: {str(e)}")
    
    async def _run_test_scenarios(self):
        """Run test scenarios to evaluate system performance."""
        # Simple test scenarios
        test_scenarios = [
            "What are the major capital cities in Europe?",
            "Explain how photosynthesis works.",
            "What are three strategies for improving productivity?"
        ]
        
        # Select a random scenario
        test_input = random.choice(test_scenarios)
        logger.info(f"Running test scenario: {test_input}")
        
        try:
            # Run with a subset of agents
            available_agents = get_available_agents()
            test_agents = random.sample(
                available_agents,
                min(3, len(available_agents))
            )
            
            # Process the test request
            test_result = await self.orchestrator.process_request(
                text=test_input,
                agents=test_agents
            )
            
            # Log the test results
            test_session_id = f"test_{int(time.time())}"
            save_interaction_log(
                session_id=test_session_id,
                input_text=test_input,
                agent_responses=test_result['agent_responses'],
                integrated_response=test_result['integrated_response'],
                processing_time=0.0
            )
            
            logger.info(f"Test scenario completed successfully")
            
        except Exception as e:
            logger.error(f"Error running test scenario: {str(e)}")
    
    def start(self):
        """Start the autonomous controller."""
        self.running = True
        logger.info("Master controller started")
        
        # Start the main loop in a separate thread
        self.control_thread = threading.Thread(target=self._control_loop)
        self.control_thread.daemon = True
        self.control_thread.start()
    
    def stop(self):
        """Stop the autonomous controller."""
        self.running = False
        logger.info("Master controller stopped")
    
    def _control_loop(self):
        """Main control loop that runs autonomously."""
        # Initialize the loop
        asyncio.run(self.initialize())
        
        # Main loop
        while self.running:
            try:
                # Run an autonomous cycle
                asyncio.run(self.run_autonomous_cycle())
                
                # Sleep between cycles
                time.sleep(3600)  # 1 hour between cycles
                
            except Exception as e:
                logger.error(f"Error in control loop: {str(e)}")
                time.sleep(300)  # 5 minutes cooldown after error

# Direct execution
if __name__ == "__main__":
    controller = MasterController()
    
    try:
        controller.start()
        # Keep the main thread alive
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        controller.stop()
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        controller.stop()