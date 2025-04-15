"""
BrainOS Core Module.
The central nervous system of the BrainOS platform, connecting all components into a unified AI brain.
"""

import os
import sys
import json
import asyncio
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set

# Add root directory to path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import core components
try:
    from orchestrator import BrainOrchestrator
    from agents import get_agent_details, get_available_agents
    from config import OPENROUTER_API_KEY
    from api_client import OpenRouterClient
    from utils import generate_session_id, save_interaction_log
    # Import script modules
    from scripts.neural_bridge import NeuralBridge
    from scripts.agent_task_scheduler import AgentTaskScheduler
    from scripts.deep_thinking_engine import DeepThinkingEngine
    from scripts.swarm_brain import SwarmBrain
    from scripts.quantum_vision_analyzer import QuantumVisionAnalyzer
    # Check if all components loaded
    FULL_SYSTEM_AVAILABLE = True
except ImportError as e:
    FULL_SYSTEM_AVAILABLE = False
    print(f"Warning: Not all BrainOS components are available: {e}")
    print("Running in partial mode with limited functionality.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/brainos_core.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("brainos_core")

class BrainOSCore:
    """
    Core system for BrainOS that integrates all components.
    Acts as the central hub for the entire brain architecture.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the BrainOS Core.
        
        Args:
            api_key: Optional OpenRouter API key. If None, uses environment.
        """
        self.api_key = api_key or OPENROUTER_API_KEY
        self.session_id = generate_session_id()
        logger.info(f"Initializing BrainOS Core (Session: {self.session_id})")
        
        # Initialize core components
        self.components = {}
        self.component_status = {}
        self.running = False
        self.system_state = "initializing"
        self.last_activity = datetime.now()
        self.autonomous_mode = True
        
        # Performance metrics
        self.metrics = {
            "requests_processed": 0,
            "avg_processing_time": 0.0,
            "component_usage": {},
            "error_count": 0
        }
        
        # Try to initialize all components
        try:
            self._initialize_components()
            self.system_state = "ready"
            logger.info("BrainOS Core initialized successfully")
        except Exception as e:
            self.system_state = "degraded"
            logger.error(f"Error initializing BrainOS Core: {str(e)}")
    
    def _initialize_components(self):
        """Initialize all BrainOS components."""
        if not FULL_SYSTEM_AVAILABLE:
            logger.warning("Full system not available. Some components will be missing.")
        
        # Initialize primary orchestrator
        try:
            self.components["orchestrator"] = BrainOrchestrator(api_key=self.api_key)
            self.component_status["orchestrator"] = "ready"
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {str(e)}")
            self.component_status["orchestrator"] = "failed"
        
        # Initialize Neural Bridge
        try:
            self.components["neural_bridge"] = NeuralBridge
            self.component_status["neural_bridge"] = "ready"
            
            # Register base agents
            available_agents = get_available_agents()
            for agent_name in available_agents:
                agent_details = get_agent_details(agent_name)
                NeuralBridge.register_agent(
                    agent_name=agent_name,
                    agent_function=self._create_agent_function(agent_name),
                    metadata=agent_details
                )
        except Exception as e:
            logger.error(f"Failed to initialize neural bridge: {str(e)}")
            self.component_status["neural_bridge"] = "failed"
        
        # Initialize Task Scheduler
        try:
            self.components["task_scheduler"] = AgentTaskScheduler()
            self.component_status["task_scheduler"] = "ready"
            
            # Register agents with the scheduler
            available_agents = get_available_agents()
            for agent_name in available_agents:
                agent_details = get_agent_details(agent_name)
                capabilities = agent_details.get("capabilities", [])
                self.components["task_scheduler"].register_agent(
                    agent_name=agent_name,
                    capabilities=capabilities
                )
        except Exception as e:
            logger.error(f"Failed to initialize task scheduler: {str(e)}")
            self.component_status["task_scheduler"] = "failed"
        
        # Initialize Deep Thinking Engine
        try:
            self.components["deep_thinking"] = DeepThinkingEngine(api_key=self.api_key)
            self.component_status["deep_thinking"] = "ready"
        except Exception as e:
            logger.error(f"Failed to initialize deep thinking engine: {str(e)}")
            self.component_status["deep_thinking"] = "failed"
        
        # Initialize Swarm Brain
        try:
            self.components["swarm_brain"] = SwarmBrain(api_key=self.api_key)
            self.component_status["swarm_brain"] = "ready"
            self.components["swarm_brain"].initialize_network()
        except Exception as e:
            logger.error(f"Failed to initialize swarm brain: {str(e)}")
            self.component_status["swarm_brain"] = "failed"
        
        # Initialize Quantum Vision Analyzer
        try:
            self.components["quantum_vision"] = QuantumVisionAnalyzer()
            self.component_status["quantum_vision"] = "ready"
        except Exception as e:
            logger.error(f"Failed to initialize quantum vision analyzer: {str(e)}")
            self.component_status["quantum_vision"] = "failed"
    
    def start(self):
        """Start the BrainOS Core and all its components."""
        if self.running:
            logger.warning("BrainOS Core is already running")
            return
            
        self.running = True
        self.system_state = "running"
        logger.info("Starting BrainOS Core")
        
        # Start autonomous operation thread
        if self.autonomous_mode:
            self.autonomous_thread = threading.Thread(target=self._autonomous_operation)
            self.autonomous_thread.daemon = True
            self.autonomous_thread.start()
            logger.info("Autonomous operation mode activated")
    
    def stop(self):
        """Stop the BrainOS Core and all its components."""
        if not self.running:
            return
            
        self.running = False
        self.system_state = "stopped"
        logger.info("Stopping BrainOS Core")
        
        # Stop task scheduler if running
        if "task_scheduler" in self.components and self.component_status["task_scheduler"] == "ready":
            self.components["task_scheduler"].stop()
    
    async def process_request(self, 
                            request: Dict[str, Any],
                            processing_mode: str = "standard") -> Dict[str, Any]:
        """
        Process a request using the appropriate component based on mode.
        
        Args:
            request: The request data
            processing_mode: Mode to use for processing
                - "standard": Uses basic orchestrator
                - "deep": Uses deep thinking engine
                - "swarm": Uses swarm brain
                - "neuralsym": Uses neural bridge and symbolic reasoning
                
        Returns:
            Processing results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing request in {processing_mode} mode")
            self.last_activity = datetime.now()
            
            # Select the processing component based on mode
            if processing_mode == "deep" and "deep_thinking" in self.components:
                # Process with deep thinking engine
                result = await self._process_with_deep_thinking(request)
                component = "deep_thinking"
                
            elif processing_mode == "swarm" and "swarm_brain" in self.components:
                # Process with swarm brain
                result = await self._process_with_swarm(request)
                component = "swarm_brain"
                
            elif processing_mode == "neuralsym" and "neural_bridge" in self.components:
                # Process with neural bridge
                result = await self._process_with_neural_bridge(request)
                component = "neural_bridge"
                
            elif "orchestrator" in self.components:
                # Default to standard processing with orchestrator
                result = await self._process_with_orchestrator(request)
                component = "orchestrator"
                
            else:
                raise ValueError("No valid processing component available")
            
            # Update metrics
            processing_time = time.time() - start_time
            self._update_metrics(component, processing_time)
            
            # Add processing metadata
            result["processing"] = {
                "mode": processing_mode,
                "component": component,
                "time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Request processed successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing request: {str(e)}")
            
            # Update error metrics
            self.metrics["error_count"] += 1
            
            return {
                "error": str(e),
                "processing": {
                    "mode": processing_mode,
                    "status": "failed",
                    "time": processing_time,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def analyze_image(self, image_data: str) -> Dict[str, Any]:
        """
        Analyze an image using quantum vision analyzer.
        
        Args:
            image_data: Base64 encoded image or image file path
            
        Returns:
            Analysis results
        """
        if "quantum_vision" not in self.components:
            raise ValueError("Quantum Vision Analyzer not available")
            
        try:
            analyzer = self.components["quantum_vision"]
            analysis = analyzer.analyze_image(image_data)
            
            # If possible, create visualization
            visualization = None
            try:
                viz_bytes = analyzer.visualize_analysis(image_data, analysis)
                visualization = f"data:image/png;base64,{viz_bytes.decode('utf-8')}"
            except Exception as e:
                logger.warning(f"Could not create visualization: {str(e)}")
            
            result = {
                "analysis": analysis,
                "visualization": visualization
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {
                "error": str(e)
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get the current status of the BrainOS system."""
        # Get the status of all components
        component_status = {}
        for component, status in self.component_status.items():
            component_status[component] = {
                "status": status,
                "details": self._get_component_details(component)
            }
        
        # Get agent status if available
        agent_status = {}
        if "task_scheduler" in self.components and self.component_status["task_scheduler"] == "ready":
            agent_status = self.components["task_scheduler"].get_agent_status()
            
        status = {
            "system_state": self.system_state,
            "session_id": self.session_id,
            "running": self.running,
            "autonomous_mode": self.autonomous_mode,
            "last_activity": self.last_activity.isoformat(),
            "metrics": self.metrics,
            "components": component_status,
            "agents": agent_status,
            "timestamp": datetime.now().isoformat()
        }
        
        return status
    
    def _get_component_details(self, component_name: str) -> Dict[str, Any]:
        """Get detailed status for a specific component."""
        component = self.components.get(component_name)
        if not component:
            return {"error": "Component not found"}
            
        if component_name == "orchestrator":
            return {"instance": "BrainOrchestrator"}
        elif component_name == "neural_bridge":
            return {
                "registered_agents": len(NeuralBridge.get_registered_agents())
            }
        elif component_name == "task_scheduler":
            return {
                "active_tasks": len(component.active_tasks),
                "completed_tasks": len(component.completed_tasks),
                "queued_tasks": len(component.task_queue)
            }
        elif component_name == "deep_thinking":
            return {"thinking_depth": component.thinking_depth}
        elif component_name == "swarm_brain":
            return {"initialized": True}
        elif component_name == "quantum_vision":
            return {"qiskit_available": getattr(component, "QISKIT_AVAILABLE", False)}
            
        return {}
    
    async def _process_with_orchestrator(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request using the standard orchestrator."""
        # Extract request data
        text = request.get("text", "")
        image_url = request.get("image_url")
        agents = request.get("agents")
        
        # Check if we have input
        if not text and not image_url:
            raise ValueError("No text or image provided in request")
            
        # Process with orchestrator
        results = await self.components["orchestrator"].process_request(
            text=text,
            image_url=image_url,
            agents=agents
        )
        
        return results
    
    async def _process_with_deep_thinking(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request using the deep thinking engine."""
        # Extract request data
        problem = request.get("text", "")
        if not problem:
            raise ValueError("No problem text provided for deep thinking")
            
        # Get thinking depth if specified
        depth = request.get("depth", 3)
        
        # Process with deep thinking engine
        results = await self.components["deep_thinking"].think_deeply(
            problem=problem,
            depth=depth
        )
        
        return results
    
    async def _process_with_swarm(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request using the swarm brain."""
        # Extract request data
        query = request.get("text", "")
        if not query:
            raise ValueError("No query text provided for swarm processing")
            
        # Get max steps if specified
        max_steps = request.get("max_steps", 5)
        
        # Process with swarm brain
        results = await self.components["swarm_brain"].process_query(
            query=query,
            max_steps=max_steps
        )
        
        return results
    
    async def _process_with_neural_bridge(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request using the neural bridge."""
        # Extract request data
        task = request.get("task", {})
        if not task:
            # Convert request to task format
            task = {
                "description": request.get("text", ""),
                "data": request.get("data", {}),
                "requirements": request.get("requirements", [])
            }
            
        # Get specified agents if any
        agents = request.get("agents")
        
        # Process with neural bridge
        results = await NeuralBridge.process_task(
            task=task,
            agents=agents
        )
        
        return results
    
    def _create_agent_function(self, agent_name: str):
        """Create a processing function for an agent to use with neural bridge."""
        agent_details = get_agent_details(agent_name)
        
        async def process_message(message):
            try:
                # Get the agent's model
                model = agent_details.get("model", "anthropic/claude-3-opus")
                system_prompt = agent_details.get("system_prompt", f"You are {agent_name}.")
                
                # Create a client if needed
                client = OpenRouterClient(self.api_key)
                
                # Process the message
                text = message.get("text", "")
                if not text and isinstance(message, dict):
                    # Try to convert message to text
                    text = json.dumps(message)
                
                response = await client.process_with_agent(
                    agent_model=model,
                    text=text,
                    system_prompt=system_prompt
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Error in agent {agent_name} processing: {str(e)}")
                return f"Error: {str(e)}"
        
        return process_message
    
    def _autonomous_operation(self):
        """Run the autonomous operation loop."""
        while self.running and self.autonomous_mode:
            try:
                # Check if any maintenance or optimization is needed
                self._perform_maintenance()
                
                # Sleep for a while
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in autonomous operation: {str(e)}")
                time.sleep(60)  # Shorter wait on error
    
    def _perform_maintenance(self):
        """Perform periodic maintenance operations."""
        current_time = datetime.now()
        
        # Check if system has been idle for a while
        idle_time = (current_time - self.last_activity).total_seconds()
        if idle_time > 3600:  # 1 hour
            logger.info(f"System idle for {idle_time:.2f}s, running maintenance")
            
            # Example tasks that could be performed:
            # - Clean up old logs
            # - Update agent metrics
            # - Optimize system parameters
            
            # For now, just log the activity
            self.last_activity = current_time
    
    def _update_metrics(self, component: str, processing_time: float):
        """Update performance metrics after a request."""
        # Update total requests and average time
        self.metrics["requests_processed"] += 1
        current_total = self.metrics["requests_processed"]
        current_avg = self.metrics["avg_processing_time"]
        
        self.metrics["avg_processing_time"] = (
            (current_avg * (current_total - 1) + processing_time) / current_total
        )
        
        # Update component usage
        if component not in self.metrics["component_usage"]:
            self.metrics["component_usage"][component] = 0
        self.metrics["component_usage"][component] += 1

# Main function to test the system
async def test_brainos_core():
    """Test the BrainOS Core with sample requests."""
    core = BrainOSCore()
    core.start()
    
    print("BrainOS Core Status:")
    status = core.get_system_status()
    print(f"System State: {status['system_state']}")
    print(f"Components:")
    for component, details in status["components"].items():
        print(f"- {component}: {details['status']}")
    
    # Process a standard request
    print("\nTesting standard request processing...")
    result = await core.process_request({
        "text": "What are the most important challenges in renewable energy adoption?",
        "processing_mode": "standard"
    })
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Processed in {result['processing']['time']:.2f}s")
        print(f"Response: {result.get('integrated_response', '')[:100]}...")
    
    # Test deep thinking if available
    if "deep_thinking" in core.components and core.component_status["deep_thinking"] == "ready":
        print("\nTesting deep thinking processing...")
        deep_result = await core.process_request({
            "text": "What strategies could address climate change while balancing economic growth?",
            "processing_mode": "deep"
        })
        
        if "error" in deep_result:
            print(f"Error: {deep_result['error']}")
        else:
            print(f"Deep thinking completed in {deep_result['processing']['time']:.2f}s")
            print(f"Conclusion: {deep_result.get('conclusion', '')[:100]}...")
    
    # Show final metrics
    print("\nFinal Metrics:")
    print(f"Requests Processed: {core.metrics['requests_processed']}")
    print(f"Average Processing Time: {core.metrics['avg_processing_time']:.2f}s")
    
    # Stop the core
    core.stop()

if __name__ == "__main__":
    asyncio.run(test_brainos_core())