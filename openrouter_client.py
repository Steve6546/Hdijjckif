"""
OpenRouter Client for accessing various AI models through a unified API.
This module provides a client for interacting with OpenRouter API using the OpenAI SDK.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenRouterClient:
    """
    Client for interacting with OpenRouter API using the OpenAI SDK.
    Provides access to various AI models through a unified interface.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key (str, optional): OpenRouter API key. If None, will try to get from environment.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("No OpenRouter API key provided. Set OPENROUTER_API_KEY environment variable.")
        
        self.site_url = os.getenv("SITE_URL", "https://brainos.ai")
        self.site_name = os.getenv("SITE_NAME", "BrainOS AI System")
        
        # Initialize OpenAI client with OpenRouter base URL
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        # Default headers to send with requests
        self.default_headers = {
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name
        }
        
        # List of free models available on OpenRouter
        self.free_models = [
            "google/gemini-2.5-pro-exp-03-25:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "meta-llama/llama-4-maverick:free",
            "qwen/qwen2.5-vl-72b-instruct:free",
            "deepseek/deepseek-v3-base:free",
            "deepseek/deepseek-r1:free",
            "nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
            "deepseek/deepseek-chat-v3-0324:free",
            "open-r1/olympiccoder-32b:free",
            "qwen/qwq-32b:free",
            "google/gemini-2.0-flash-exp:free"
        ]
    
    def generate_text(self, 
                     prompt: str, 
                     model: str = "google/gemini-2.5-pro-exp-03-25:free",
                     max_tokens: int = 1000,
                     temperature: float = 0.7,
                     top_p: float = 0.9) -> str:
        """
        Generate text using the specified model.
        
        Args:
            prompt (str): The text prompt to generate from
            model (str): The model to use for generation
            max_tokens (int): Maximum tokens to generate
            temperature (float): Controls randomness
            top_p (float): Controls diversity via nucleus sampling
            
        Returns:
            str: The generated text
        """
        if not self.api_key:
            return "خطأ: مفتاح OpenRouter API غير متوفر"
        
        # Ensure we're using a free model if not specified
        if model not in self.free_models:
            logger.warning(f"Model {model} not in free models list. Using default free model.")
            model = "google/gemini-2.5-pro-exp-03-25:free"
        
        logger.info(f"Generating text with model: {model}")
        
        try:
            # Create completion
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                extra_headers=self.default_headers
            )
            
            # Extract and return the generated text
            generated_text = completion.choices[0].message.content
            logger.info(f"Successfully generated text of length {len(generated_text)}")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return f"خطأ أثناء توليد النص: {str(e)}"
    
    def analyze_image(self, 
                     prompt: str,
                     image_url: str,
                     model: str = "google/gemini-2.5-pro-exp-03-25:free",
                     max_tokens: int = 1000,
                     temperature: float = 0.7) -> str:
        """
        Analyze an image using a vision model.
        
        Args:
            prompt (str): Text prompt describing what to analyze about the image
            image_url (str): URL of the image to analyze
            model (str): The model to use for analysis
            max_tokens (int): Maximum tokens to generate
            temperature (float): Controls randomness
            
        Returns:
            str: The analysis text
        """
        if not self.api_key:
            return "خطأ: مفتاح OpenRouter API غير متوفر"
        
        # Only certain models support vision
        vision_models = [
            "google/gemini-2.5-pro-exp-03-25:free",
            "qwen/qwen2.5-vl-72b-instruct:free"
        ]
        
        if model not in vision_models:
            logger.warning(f"Model {model} does not support vision. Using default vision model.")
            model = "google/gemini-2.5-pro-exp-03-25:free"
        
        logger.info(f"Analyzing image with model: {model}")
        
        try:
            # Create completion with image
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                extra_headers=self.default_headers
            )
            
            # Extract and return the analysis text
            analysis_text = completion.choices[0].message.content
            logger.info(f"Successfully analyzed image, response length: {len(analysis_text)}")
            return analysis_text
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return f"خطأ أثناء تحليل الصورة: {str(e)}"
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available models from OpenRouter.
        
        Returns:
            List[Dict[str, Any]]: Available models and their details
        """
        if not self.api_key:
            return []
        
        try:
            # Get models from OpenRouter API
            response = self.client.models.list()
            
            # Filter for free models if needed
            free_models = [model for model in response.data if model.id.endswith(":free")]
            
            return free_models
            
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []

# Example usage
if __name__ == "__main__":
    client = OpenRouterClient()
    
    # Test text generation
    result = client.generate_text("اكتب قصة قصيرة عن القمر")
    print(f"Generated text: {result}")
    
    # Test image analysis
    image_result = client.analyze_image(
        "اشرح ما تراه في هذه الصورة",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
    )
    print(f"Image analysis: {image_result}")