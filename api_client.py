"""
Client for interacting with the OpenRouter.ai API.
"""

import os
import base64
import aiohttp
import asyncio
from typing import Dict, List, Optional, Union, Any

class OpenRouterClient:
    """Client for making API calls to OpenRouter.ai."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key (str, optional): OpenRouter API key. If None, will try to get from environment.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"
        self.site_info = {
            "HTTP-Referer": os.getenv("SITE_URL", "https://brain-orchestrator.streamlit.app"),
            "X-Title": os.getenv("SITE_NAME", "AI Brain Orchestration")
        }
    
    async def generate_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict:
        """
        Generate a completion using the specified model.
        
        Args:
            model (str): The model to use for generation
            messages (List[Dict]): Messages for the conversation
            temperature (float): Sampling temperature
            max_tokens (int): Maximum tokens to generate
            
        Returns:
            Dict: The completion response
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.site_info
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error: {response.status} - {error_text}")
                    
                    return await response.json()
            except aiohttp.ClientError as e:
                raise Exception(f"Network error when contacting OpenRouter: {str(e)}")
            except Exception as e:
                raise Exception(f"Error generating completion: {str(e)}")
    
    async def process_with_agent(
        self,
        agent_model: str,
        text: str,
        system_prompt: str = "You are a helpful assistant.",
        image_url: Optional[str] = None
    ) -> str:
        """
        Process input with a specific agent model.
        
        Args:
            agent_model (str): The model to use
            text (str): Text input to process
            system_prompt (str): System message to set the context
            image_url (str, optional): URL to an image for vision models
            
        Returns:
            str: The generated response
        """
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add user message based on whether we have an image
        if image_url:
            # Multi-modal content with image
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            })
        else:
            # Text-only content
            messages.append({
                "role": "user",
                "content": text
            })
        
        try:
            response = await self.generate_completion(
                model=agent_model,
                messages=messages
            )
            
            if (
                response 
                and "choices" in response 
                and len(response["choices"]) > 0 
                and "message" in response["choices"][0]
                and "content" in response["choices"][0]["message"]
            ):
                return response["choices"][0]["message"]["content"]
            else:
                raise Exception("Invalid response format from OpenRouter")
                
        except Exception as e:
            raise Exception(f"Error processing with agent {agent_model}: {str(e)}")
