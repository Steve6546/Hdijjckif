"""
Master AI Controller for BrainOS.
Central coordinating system that manages all agent interactions and provides a unified interface.
"""

import os
import sys
import json
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Add parent directory to path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
try:
    from api_client import OpenRouterClient
    from config import OPENROUTER_API_KEY
    from orchestrator import BrainOrchestrator
    from agents import get_agent_details, get_available_agents
    from utils import generate_session_id

    # Import specialized components
    from scripts.brainos_core import BrainOSCore
    from scripts.neural_bridge import NeuralBridge
    from scripts.agent_task_scheduler import AgentTaskScheduler
    from scripts.deep_thinking_engine import DeepThinkingEngine
    from scripts.swarm_brain import SwarmBrain
    from scripts.quantum_vision_analyzer import QuantumVisionAnalyzer

    FULL_IMPORTS_AVAILABLE = True
except ImportError as e:
    FULL_IMPORTS_AVAILABLE = False
    print(f"Warning: Not all imports available: {e}")

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

class MasterAIController:
    """
    Master AI Controller that provides a unified interface to the entire BrainOS.
    Acts as the single point of contact for all user interactions.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Master AI Controller.

        Args:
            api_key: Optional OpenRouter API key. If None, uses config.
        """
        self.api_key = api_key or OPENROUTER_API_KEY
        self.session_id = generate_session_id()
        logger.info(f"Initializing Master AI Controller (Session: {self.session_id})")

        # Initialize BrainOS Core
        try:
            self.brain_core = BrainOSCore(api_key=self.api_key)
            self.core_available = True
            logger.info("BrainOS Core initialized successfully")
        except Exception as e:
            self.brain_core = None
            self.core_available = False
            logger.error(f"Failed to initialize BrainOS Core: {str(e)}")

        # Initialize basic orchestrator as fallback
        try:
            self.orchestrator = BrainOrchestrator(api_key=self.api_key)
            logger.info("Basic orchestrator initialized as fallback")
        except Exception as e:
            self.orchestrator = None
            logger.error(f"Failed to initialize basic orchestrator: {str(e)}")

        # Track system state
        self.system_state = "initializing"
        self.last_activity = datetime.now()
        self.system_state = "running"

        # Start the system
        #if self.core_available:
        #    self.brain_core.start()
        #    self.system_state = "running"
        #    logger.info("System started successfully")
        #else:
        #    self.system_state = "degraded"
        #    logger.warning("System running in degraded mode")

    async def process_user_request(self, 
                                 text: Optional[str] = None, 
                                 image_data: Optional[str] = None,
                                 mode: str = "auto") -> Dict[str, Any]:
        """
        Process a user request through the system.

        Args:
            text: Optional text input from the user
            image_data: Optional base64 encoded image data
            mode: Processing mode (auto, deep, swarm, etc.)

        Returns:
            Processing results
        """
        start_time = time.time()
        logger.info(f"Processing user request in {mode} mode")
        self.last_activity = datetime.now()

        try:
            # Prepare the request data
            request = {
                "text": text or "",
                "image_url": image_data,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }

            # Determine the optimal processing mode if set to auto
            if mode == "auto":
                mode = self._determine_processing_mode(text, image_data)

            # Process with Brain Core if available
            if self.core_available:
                logger.info(f"Using BrainOS Core with {mode} mode")
                result = await self.brain_core.process_request(
                    request=request,
                    processing_mode=mode
                )
            # Fallback to basic orchestrator
            elif self.orchestrator:
                logger.info("Falling back to basic orchestrator")
                result = await self.orchestrator.process_request(
                    text=text,
                    image_url=image_data
                )
            else:
                raise ValueError("No processing system available")

            # Add processing metadata
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            result["mode"] = mode

            logger.info(f"Request processed in {processing_time:.2f}s using {mode} mode")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing request: {str(e)}")

            return {
                "error": str(e),
                "status": "failed",
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }

    async def analyze_image(self, image_data: str) -> Dict[str, Any]:
        """
        Analyze an image using the quantum vision system.

        Args:
            image_data: Base64 encoded image data

        Returns:
            Analysis results
        """
        if not self.core_available:
            raise ValueError("BrainOS Core not available")

        try:
            logger.info("Analyzing image with quantum vision analyzer")
            result = await self.brain_core.analyze_image(image_data)
            return result

        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {"error": str(e)}

    def get_system_status(self) -> Dict[str, Any]:
        """Get the current status of the entire system."""
        status = {
            "session_id": self.session_id,
            "system_state": self.system_state,
            "last_activity": self.last_activity.isoformat(),
            "timestamp": datetime.now().isoformat()
        }

        # Add Brain Core status if available
        if self.core_available:
            core_status = self.brain_core.get_system_status()
            status["brain_core"] = core_status

        return status

    def _determine_processing_mode(self, text: Optional[str], image_data: Optional[str]) -> str:
        """
        Determine the optimal processing mode based on input.

        Args:
            text: Optional text input
            image_data: Optional image data

        Returns:
            Processing mode to use
        """
        # Default to standard processing
        mode = "standard"

        if not text and image_data:
            # Image-only requests use quantum vision (via standard)
            return "standard"

        if not text or len(text) < 50:
            # Short queries use standard processing
            return "standard"

        # Check for complexity indicators in the text
        complex_indicators = [
            "explain", "analyze", "compare", "discuss", "evaluate",
            "pros and cons", "advantages", "disadvantages", "detailed",
            "comprehensive", "thorough", "in-depth", "complex", "difficult"
        ]

        creative_indicators = [
            "creative", "imagine", "design", "generate", "innovate",
            "story", "poem", "art", "novel", "unique", "original"
        ]

        collaborative_indicators = [
            "collaborate", "team", "together", "multiple perspectives",
            "diverse", "various", "different viewpoints", "opinions",
            "consensus", "aggregate", "combine"
        ]

        text_lower = text.lower()

        # Count indicators
        complex_count = sum(1 for ind in complex_indicators if ind in text_lower)
        creative_count = sum(1 for ind in creative_indicators if ind in text_lower)
        collab_count = sum(1 for ind in collaborative_indicators if ind in text_lower)

        # Determine mode based on indicators
        if collab_count > 1 or "swarm" in text_lower:
            mode = "swarm"
        elif complex_count > 2 or "deep" in text_lower:
            mode = "deep"
        elif creative_count > 2 and collab_count > 0:
            mode = "neuralsym"

        logger.info(f"Determined processing mode: {mode} for request")
        return mode

# Helper function to create a controller instance
def get_master_controller(api_key: Optional[str] = None) -> MasterAIController:
    """Get or create a master controller instance."""
    return MasterAIController(api_key=api_key)

# Test function if run directly
async def test_master_controller():
    """Test the master controller with a sample request."""
    controller = get_master_controller()

    # Test status
    status = controller.get_system_status()
    print(f"System Status: {status['system_state']}")

    # Test processing a simple request
    result = await controller.process_user_request(
        text="What are the best practices for sustainable architecture?",
        mode="auto"
    )

    print(f"\nProcessed request in {result.get('processing_time', 0):.2f}s")
    print(f"Using mode: {result.get('mode', 'unknown')}")

    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        if "integrated_response" in result:
            print(f"\nResponse: {result['integrated_response'][:300]}...")
        elif "final_output" in result:
            print(f"\nResponse: {result['final_output'][:300]}...")
        elif "conclusion" in result:
            print(f"\nResponse: {result['conclusion'][:300]}...")

if __name__ == "__main__":
    asyncio.run(test_master_controller())