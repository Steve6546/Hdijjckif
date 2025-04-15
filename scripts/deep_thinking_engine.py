"""
Deep Thinking Engine for BrainOS.
Provides advanced reasoning and deep analysis capabilities for complex problems.
"""

import os
import sys
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Add root directory to path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import OpenRouterClient
from orchestrator import BrainOrchestrator
from config import OPENROUTER_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("deep_thinking")

class DeepThinkingEngine:
    """
    Engine for deep, multi-step thinking and problem solving.
    Uses chain-of-thought reasoning across multiple AI models.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the deep thinking engine.
        
        Args:
            api_key: Optional OpenRouter API key. If None, uses config.
        """
        self.client = OpenRouterClient(api_key or OPENROUTER_API_KEY)
        self.orchestrator = BrainOrchestrator(api_key or OPENROUTER_API_KEY)
        self.reasoning_steps = []
        self.thinking_depth = 3  # Default depth of thinking
        
        # Model selection for different reasoning types
        self.models = {
            "creative": "anthropic/claude-3-opus",
            "analytical": "google/gemini-1.5-pro",
            "logical": "meta-llama/llama-3-70b-instruct",
            "integrative": "anthropic/claude-3-opus"
        }
    
    async def think_deeply(self, problem: str, depth: int = 3) -> Dict[str, Any]:
        """
        Perform deep thinking on a problem through multiple steps.
        
        Args:
            problem: The problem or question to analyze
            depth: Number of thinking steps to perform
            
        Returns:
            Dict containing the thinking process and final conclusion
        """
        self.thinking_depth = max(2, min(5, depth))  # Constrain between 2-5 steps
        self.reasoning_steps = []
        
        logger.info(f"Starting deep thinking process with depth {self.thinking_depth}")
        
        # Step 1: Initial problem formulation
        initial_analysis = await self._perform_step(
            "problem_formulation",
            f"""
            Analyze the following problem carefully:
            
            PROBLEM: {problem}
            
            Your task is to:
            1. Identify key components of this problem
            2. Clarify any ambiguities or assumptions
            3. Reformulate the problem in precise terms
            4. Identify what information is needed to solve it
            """
        )
        
        # Step 2: Multi-perspective analysis
        perspectives = await self._perform_step(
            "perspective_analysis", 
            f"""
            Consider the following problem from multiple perspectives:
            
            PROBLEM: {problem}
            
            INITIAL ANALYSIS: {initial_analysis}
            
            Your task is to:
            1. Analyze this problem from at least 3 different perspectives
            2. Consider contrasting viewpoints and approaches
            3. Identify the strengths and weaknesses of each perspective
            4. Note any contradictions or tensions between perspectives
            """
        )
        
        # Intermediate steps based on depth
        for i in range(self.thinking_depth - 2):
            step_name = f"deep_analysis_{i+1}"
            
            if i == 0:
                # First extra step: Explore solutions
                await self._perform_step(
                    step_name,
                    f"""
                    Based on our analysis so far, explore possible solutions:
                    
                    PROBLEM: {problem}
                    
                    INITIAL ANALYSIS: {initial_analysis}
                    
                    PERSPECTIVES: {perspectives}
                    
                    Your task is to:
                    1. Generate 3-5 potential approaches to solve this problem
                    2. For each approach, outline the key steps required
                    3. Analyze the feasibility and potential challenges of each approach
                    4. Identify any resources or prerequisites needed
                    """
                )
            elif i == 1:
                # Second extra step: Critical evaluation
                await self._perform_step(
                    step_name,
                    f"""
                    Critically evaluate the solutions proposed so far:
                    
                    PROBLEM: {problem}
                    
                    PROPOSED SOLUTIONS: {self.reasoning_steps[-1]['content']}
                    
                    Your task is to:
                    1. Rigorously test each proposed solution against the problem requirements
                    2. Identify potential unintended consequences or edge cases
                    3. Apply relevant theoretical frameworks or principles to evaluate each solution
                    4. Suggest refinements or combinations that might improve the solutions
                    """
                )
            else:
                # Additional steps: Deepen analysis
                await self._perform_step(
                    step_name,
                    f"""
                    Let's deepen our analysis further:
                    
                    PROBLEM: {problem}
                    
                    PREVIOUS ANALYSIS: {self.reasoning_steps[-1]['content']}
                    
                    Your task is to:
                    1. Identify any assumptions we've been making
                    2. Consider alternative frameworks or paradigms
                    3. Look for meta-patterns across our analysis
                    4. Suggest how we might reframe our understanding of the problem
                    """
                )
        
        # Final step: Synthesis and conclusion
        conclusion = await self._perform_step(
            "synthesis",
            f"""
            Synthesize all our thinking to provide a comprehensive conclusion:
            
            ORIGINAL PROBLEM: {problem}
            
            THINKING PROCESS:
            {self._format_reasoning_steps()}
            
            Your task is to:
            1. Synthesize the key insights from our deep thinking process
            2. Present a clear, well-reasoned conclusion or answer to the original problem
            3. Acknowledge limitations and uncertainties in our conclusion
            4. Suggest next steps or further questions that could deepen understanding
            5. Provide a concise executive summary at the end
            """
        )
        
        # Prepare the final result
        result = {
            "problem": problem,
            "conclusion": conclusion,
            "thinking_process": self.reasoning_steps,
            "depth": self.thinking_depth,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save the thinking process to a file for reference
        self._save_thinking_process(problem, result)
        
        return result
    
    async def _perform_step(self, step_name: str, prompt: str) -> str:
        """
        Perform a single step in the thinking process.
        
        Args:
            step_name: Name of the thinking step
            prompt: Detailed prompt for this step
            
        Returns:
            The response for this step
        """
        logger.info(f"Performing thinking step: {step_name}")
        
        # Select appropriate model for this step
        model = self._select_model_for_step(step_name)
        
        # System prompt for deep thinking
        system_prompt = """You are an expert analytical and critical thinking system capable of deep, 
        nuanced analysis. Your task is to think through complex problems step-by-step, 
        considering multiple perspectives and approaches. Be thorough, precise, and intellectually rigorous. 
        Avoid superficial analysis, and push beyond obvious solutions. 
        Structure your responses clearly with logical sections and clear reasoning."""
        
        try:
            # Process with the selected model
            start_time = time.time()
            response = await self.client.process_with_agent(
                agent_model=model,
                text=prompt,
                system_prompt=system_prompt,
                temperature=0.7,  # Slightly creative but still focused
                max_tokens=2000  # Allow for detailed responses
            )
            processing_time = time.time() - start_time
            
            # Record this step
            self.reasoning_steps.append({
                "step": step_name,
                "model": model,
                "prompt": prompt,
                "content": response,
                "processing_time": processing_time
            })
            
            logger.info(f"Completed thinking step: {step_name} in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error in thinking step {step_name}: {str(e)}")
            # Return error message and continue process
            error_message = f"Error in analysis: {str(e)}"
            self.reasoning_steps.append({
                "step": step_name,
                "model": model,
                "prompt": prompt,
                "content": error_message,
                "error": True
            })
            return error_message
    
    def _select_model_for_step(self, step_name: str) -> str:
        """Select the most appropriate model for a given thinking step."""
        if "problem_formulation" in step_name:
            return self.models["analytical"]
        elif "perspective" in step_name:
            return self.models["creative"]
        elif "critical" in step_name or "evaluation" in step_name:
            return self.models["logical"]
        elif "synthesis" in step_name:
            return self.models["integrative"]
        else:
            # For other steps, rotate between models
            index = len(self.reasoning_steps) % len(self.models)
            return list(self.models.values())[index]
    
    def _format_reasoning_steps(self) -> str:
        """Format the reasoning steps for inclusion in prompts."""
        formatted = ""
        for step in self.reasoning_steps:
            formatted += f"STEP: {step['step']}\n"
            formatted += f"ANALYSIS:\n{step['content']}\n\n"
        return formatted
    
    def _save_thinking_process(self, problem: str, result: Dict[str, Any]) -> None:
        """Save the thinking process to a file."""
        try:
            # Create a filename based on the problem
            problem_hash = hash(problem) % 10000
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cache/thinking_{problem_hash}_{timestamp}.json"
            
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
                
            logger.info(f"Saved thinking process to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save thinking process: {str(e)}")

# Test function
async def test_deep_thinking():
    """Test the deep thinking engine with a sample problem."""
    engine = DeepThinkingEngine()
    
    test_problem = "What are the most effective strategies for addressing climate change while balancing economic growth?"
    
    print(f"Thinking deeply about: {test_problem}")
    result = await engine.think_deeply(test_problem, depth=3)
    
    print("\n====== CONCLUSION ======")
    print(result["conclusion"])
    print("\n====== THINKING PROCESS SUMMARY ======")
    for i, step in enumerate(result["thinking_process"]):
        print(f"Step {i+1}: {step['step']} (model: {step['model']})")
    
    print(f"\nFull thinking process saved to cache directory.")

if __name__ == "__main__":
    asyncio.run(test_deep_thinking())