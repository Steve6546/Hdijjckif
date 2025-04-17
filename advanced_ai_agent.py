# advanced_ai_agent.py
import os
import logging
import re
import json
import requests
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Union

from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer, set_seed
from config import OPENROUTER_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary of available models with their descriptions and properties
AVAILABLE_MODELS = {
    "gpt2": {
        "description": "OpenAI GPT-2 Small (124M parameters)",
        "language": "en",
        "size": "small",
        "task": "text-generation"
    },
    "gpt2-medium": {
        "description": "OpenAI GPT-2 Medium (355M parameters)",
        "language": "en",
        "size": "medium",
        "task": "text-generation"
    },
    "gpt2-large": {
        "description": "OpenAI GPT-2 Large (774M parameters)",
        "language": "en",
        "size": "large",
        "task": "text-generation"
    },
    "aubmindlab/aragpt2-base": {
        "description": "Arabic GPT-2 Base Model",
        "language": "ar",
        "size": "base",
        "task": "text-generation"
    },
    "aubmindlab/aragpt2-medium": {
        "description": "Arabic GPT-2 Medium Model",
        "language": "ar",
        "size": "medium",
        "task": "text-generation"
    },
    "openai/gpt-3.5-turbo": {
        "description": "OpenAI GPT-3.5 Turbo",
        "language": "multi",
        "size": "large",
        "task": "chat",
        "api": True
    },
    "openai/gpt-4": {
        "description": "OpenAI GPT-4",
        "language": "multi",
        "size": "xlarge",
        "task": "chat",
        "api": True
    },
    "anthropic/claude-3-opus": {
        "description": "Anthropic Claude 3 Opus",
        "language": "multi",
        "size": "xlarge",
        "task": "chat",
        "api": True
    },
    "anthropic/claude-3-sonnet": {
        "description": "Anthropic Claude 3 Sonnet",
        "language": "multi",
        "size": "large",
        "task": "chat",
        "api": True
    },
    "meta-llama/llama-3-70b-instruct": {
        "description": "Meta Llama 3 70B Instruct",
        "language": "multi",
        "size": "xlarge",
        "task": "chat",
        "api": True
    },
    "mistralai/mistral-large": {
        "description": "Mistral Large",
        "language": "multi",
        "size": "large",
        "task": "chat",
        "api": True
    }
}

class AdvancedAI:
    """
    Agent using Hugging Face transformers for advanced text generation.
    Supports multiple models including Arabic language models.
    """
    def __init__(self, model_name: str = None):
        """
        Initializes the text generation pipeline. Downloads the model on first use if not cached.

        Args:
            model_name (str, optional): The name of the Hugging Face model to use.
                                       If None, uses the model specified in the ADVANCED_AI_MODEL env var,
                                       or defaults to "gpt2".
        """
        # Get model from environment variable or use default
        self.model_name = model_name or os.getenv("ADVANCED_AI_MODEL", "gpt2")
        self.generator = None
        self.model_info = AVAILABLE_MODELS.get(self.model_name, {
            "description": "Unknown model",
            "language": "unknown",
            "size": "unknown"
        })
        
        # Get API key for OpenRouter
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        
        # Check if we're using an API-based model
        self.use_api = self.model_info.get("api", False)
        
        if self.use_api and not self.api_key:
            logger.warning("API-based model selected but no API key provided. Set OPENROUTER_API_KEY environment variable.")
            
        # For local models, we'll skip loading the actual model to save time in demo mode
        if not self.use_api:
            logger.info(f"Demo mode: Skipping model initialization for local model {self.model_name}")
            self.generator = True  # Just a placeholder to indicate it's "initialized"
        else:
            logger.info(f"Using API-based model: {self.model_name}")
            self.generator = True  # API models don't need local initialization

    def generate(self, prompt: str, max_length: int = 150, num_return_sequences: int = 1,
                 temperature: float = 1.0, top_p: float = 0.9, seed: Optional[int] = None) -> str:
        """
        Generates text based on a given prompt with enhanced parameters.

        Args:
            prompt (str): The text prompt to start generation from.
            max_length (int): The maximum length of the generated text sequence.
            num_return_sequences (int): The number of sequences to generate.
            temperature (float): Controls randomness. Lower values make output more deterministic.
            top_p (float): Nucleus sampling parameter. Lower values make output more focused.
            seed (int, optional): Random seed for reproducibility.

        Returns:
            str: The generated text, or an error message if generation fails.
        """
        if not self.generator:
            logger.error("Text generation pipeline not initialized. Cannot generate text.")
            return "خطأ: لم يتم تهيئة وكيل الذكاء الاصطناعي بشكل صحيح." # "Error: AI agent not initialized correctly."

        # Detect language
        is_arabic = self._is_arabic_text(prompt)
        logger.info(f"Generating text for prompt (first 50 chars): '{prompt[:50]}...' (Arabic: {is_arabic})")
        
        try:
            # If using API-based model (OpenRouter)
            if self.use_api and self.api_key:
                return self._generate_with_api(prompt, max_length, temperature, top_p)
            
            # For local models or demo mode
            if is_arabic:
                # Arabic response
                generated_text = f"{prompt}\n\nهذا نص تم إنشاؤه بواسطة نموذج {self.model_name} (وضع العرض التوضيحي). يمكن استخدام هذا النموذج لتوليد نصوص متنوعة بناءً على المدخلات المقدمة. تم ضبط المعلمات على: درجة الحرارة = {temperature}، top_p = {top_p}، الحد الأقصى للطول = {max_length}."
            else:
                # English response
                generated_text = f"{prompt}\n\nThis is text generated by the {self.model_name} model (demo mode). This model can be used to generate various texts based on the provided inputs. Parameters were set to: temperature = {temperature}, top_p = {top_p}, max_length = {max_length}."
                
            logger.info(f"Successfully generated demo text of length {len(generated_text)}")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error during text generation: {e}", exc_info=True)
            return f"خطأ أثناء توليد النص: {str(e)}" # "Error during text generation: {str(e)}"
            
    def _generate_with_api(self, prompt: str, max_length: int = 150, temperature: float = 1.0, top_p: float = 0.9) -> str:
        """
        Generate text using OpenRouter API.
        
        Args:
            prompt: The text prompt to generate from
            max_length: Maximum length of the generated text
            temperature: Controls randomness
            top_p: Controls diversity via nucleus sampling
            
        Returns:
            str: The generated text
        """
        logger.info(f"Generating text with OpenRouter API using model: {self.model_name}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Format the messages for chat models
        messages = [{"role": "user", "content": prompt}]
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_length
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    generated_text = result["choices"][0]["message"]["content"]
                    logger.info(f"Successfully generated text with OpenRouter API, length: {len(generated_text)}")
                    return generated_text
                else:
                    logger.error(f"Unexpected response format from OpenRouter API: {result}")
                    return f"Error: Unexpected response format from API"
            else:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return f"Error: API returned status code {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}", exc_info=True)
            return f"Error calling AI service: {str(e)}"

    def switch_model(self, model_name: str) -> str:
        """
        Switches to a different model for text generation.

        Args:
            model_name (str): The name of the Hugging Face model to use.

        Returns:
            str: A message indicating success or failure.
        """
        if model_name not in AVAILABLE_MODELS:
            logger.warning(f"Model '{model_name}' not in the list of known models. It may still work if it's a valid Hugging Face model.")
        
        logger.info(f"Switching from model '{self.model_name}' to '{model_name}'")
        
        # For demo purposes, we'll just update the model name
        self.model_name = model_name
        self.model_info = AVAILABLE_MODELS.get(model_name, {
            "description": "Custom model",
            "language": "unknown",
            "size": "unknown"
        })
        
        logger.info(f"Successfully switched to model: {model_name}")
        if self.model_info["language"] == "ar":
            return f"تم التبديل بنجاح إلى نموذج {model_name} ({self.model_info['description']})"
        else:
            return f"Successfully switched to model {model_name} ({self.model_info['description']})"

    def get_available_models(self) -> Dict[str, Dict[str, str]]:
        """
        Returns a dictionary of available models with their descriptions.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary mapping model names to their descriptions.
        """
        return AVAILABLE_MODELS

    def _is_arabic_text(self, text: str) -> bool:
        """
        Detects if the text contains Arabic characters.
        
        Args:
            text (str): The text to check
            
        Returns:
            bool: True if the text contains Arabic characters, False otherwise
        """
        # Arabic Unicode range: U+0600 to U+06FF
        return any('\u0600' <= c <= '\u06FF' for c in text)

# Example usage (for testing purposes)
if __name__ == "__main__":
    # Test the AdvancedAI agent
    ai = AdvancedAI()
    
    # Test English generation
    english_prompt = "Once upon a time in a land far away,"
    print(f"English prompt: {english_prompt}")
    english_result = ai.generate(english_prompt)
    print(f"English result: {english_result}")
    
    # Test Arabic generation
    arabic_prompt = "في يوم من الأيام كان هناك"
    print(f"Arabic prompt: {arabic_prompt}")
    arabic_result = ai.generate(arabic_prompt)
    print(f"Arabic result: {arabic_result}")
    
    # Test model switching
    print(ai.switch_model("aubmindlab/aragpt2-base"))
    arabic_result_2 = ai.generate(arabic_prompt)
    print(f"Arabic result with Arabic model: {arabic_result_2}")
