# advanced_ai_agent.py
import logging
import os
from typing import Dict, Any, List, Optional, Union
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer, set_seed

logger = logging.getLogger(__name__)

# Define available models with their properties
AVAILABLE_MODELS = {
    "gpt2": {
        "description": "English GPT-2 base model",
        "language": "en",
        "size": "small"
    },
    "gpt2-medium": {
        "description": "English GPT-2 medium model",
        "language": "en",
        "size": "medium"
    },
    "aubmindlab/aragpt2-base": {
        "description": "Arabic GPT-2 base model",
        "language": "ar",
        "size": "medium"
    },
    "aubmindlab/aragpt2-medium": {
        "description": "Arabic GPT-2 medium model",
        "language": "ar",
        "size": "large"
    },
    "asafaya/bert-base-arabic": {
        "description": "Arabic BERT base model",
        "language": "ar",
        "size": "medium",
        "task": "fill-mask"  # Different task than text generation
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
        
        try:
            # Initialize pipeline - this might take time on first run to download model
            logger.info(f"Initializing text generation pipeline with model: {self.model_name}")
            
            # Set task based on model info or default to text-generation
            task = self.model_info.get("task", "text-generation")
            
            # Initialize the pipeline with appropriate task
            self.generator = pipeline(task, model=self.model_name)
            logger.info(f"Pipeline for model {repr(self.model_name)} ({self.model_info['description']}) initialized successfully.")
        except OSError as e:
            logger.error(f"Could not find or load model {repr(self.model_name)}. "
                         f"Ensure it's a valid Hugging Face model name and you have internet access. Error: {e}")
            # Try to fall back to default model if the requested one fails
            if self.model_name != "gpt2":
                logger.info(f"Attempting to fall back to default 'gpt2' model...")
                try:
                    self.model_name = "gpt2"
                    self.model_info = AVAILABLE_MODELS.get(self.model_name)
                    self.generator = pipeline("text-generation", model=self.model_name)
                    logger.info(f"Successfully fell back to default 'gpt2' model.")
                except Exception as fallback_error:
                    logger.error(f"Failed to initialize fallback model: {fallback_error}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during pipeline initialization: {e}", exc_info=True)
            # Handle other potential errors (e.g., missing dependencies like torch/tensorflow)

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

        # Set seed for reproducibility if provided
        if seed is not None:
            set_seed(seed)
            
        # Detect language and use appropriate model if needed
        is_arabic = any('\u0600' <= c <= '\u06FF' for c in prompt)
        if is_arabic and self.model_info.get("language") != "ar":
            logger.info(f"Arabic text detected but using non-Arabic model. Consider using an Arabic model for better results.")

        logger.info(f"Generating text for prompt (first 50 chars): '{prompt[:50]}...'")
        try:
            # Handle different task types
            task = self.model_info.get("task", "text-generation")
            
            if task == "text-generation":
                # Generate text
                results = self.generator(
                    prompt,
                    max_length=max_length,
                    num_return_sequences=num_return_sequences,
                    temperature=temperature,
                    top_p=top_p,
                    pad_token_id=self.generator.tokenizer.eos_token_id # Suppress warning for models like gpt2
                )
                # Extract the generated text from the first result
                generated_text = results[0]['generated_text']
            elif task == "fill-mask":
                # For masked language models
                # Replace [MASK] with appropriate token for the model
                mask_token = self.generator.tokenizer.mask_token
                if mask_token not in prompt:
                    prompt = f"{prompt} {mask_token}"
                results = self.generator(prompt, top_k=num_return_sequences)
                # Format results for masked language models
                generated_text = prompt
                for i, result in enumerate(results[:num_return_sequences]):
                    generated_text += f"\nOption {i+1}: {result['sequence']}"
            else:
                return f"خطأ: نوع المهمة '{task}' غير مدعوم حاليًا."
                
            logger.info(f"Text generation successful.")
            logger.debug(f"Generated text: {generated_text}")
            return generated_text
        except Exception as e:
            logger.error(f"Error during text generation: {e}", exc_info=True)
            return f"خطأ أثناء توليد النص: {e}" # "Error during text generation: {e}"
    
    def get_available_models(self) -> Dict[str, Dict[str, str]]:
        """
        Returns information about available models.
        
        Returns:
            Dict[str, Dict[str, str]]: Dictionary of model information
        """
        return AVAILABLE_MODELS
        
    def switch_model(self, model_name: str) -> str:
        """
        Switches to a different model.
        
        Args:
            model_name (str): The name of the model to switch to.
            
        Returns:
            str: Success or error message.
        """
        if model_name == self.model_name:
            return f"النموذج '{model_name}' قيد الاستخدام بالفعل."
            
        try:
            # Check if model exists in our predefined list
            if model_name not in AVAILABLE_MODELS:
                logger.warning(f"Model '{model_name}' not in predefined list. Attempting to load anyway.")
            
            # Initialize new pipeline
            logger.info(f"Switching to model: {model_name}")
            
            # Determine task based on model info or default to text-generation
            task = AVAILABLE_MODELS.get(model_name, {}).get("task", "text-generation")
            
            # Initialize the pipeline with appropriate task
            new_generator = pipeline(task, model=model_name)
            
            # If successful, update instance variables
            self.generator = new_generator
            self.model_name = model_name
            self.model_info = AVAILABLE_MODELS.get(model_name, {
                "description": "Custom model",
                "language": "unknown",
                "size": "unknown",
                "task": task
            })
            
            logger.info(f"Successfully switched to model: {model_name}")
            return f"تم التبديل بنجاح إلى النموذج '{model_name}'."
        except Exception as e:
            logger.error(f"Error switching to model '{model_name}': {e}", exc_info=True)
            return f"خطأ أثناء التبديل إلى النموذج '{model_name}': {e}"

# Example usage (optional, for testing)
if __name__ == "__main__":
    try:
        # Test with default gpt2
        ai_agent = AdvancedAI()
        if ai_agent.generator: # Only test if initialized
            prompt1 = "The future of artificial intelligence in education is"
            print(f"\nTesting with prompt: '{prompt1}'")
            response1 = ai_agent.generate(prompt1)
            print("Response 1:\n", response1)

            prompt2 = "اكتب قصة قصيرة عن رائد فضاء يكتشف كوكبًا جديدًا:" # "Write a short story about an astronaut discovering a new planet:"
            print(f"\nTesting with prompt: '{prompt2}'")
            response2 = ai_agent.generate(prompt2, max_length=200)
            print("Response 2:\n", response2)
        else:
            print("\nAI Agent could not be initialized, skipping generation tests.")

        # Example with a potentially non-existent model (will log error during init)
        # print("\nTesting with non-existent model:")
        # non_existent_agent = AdvancedAI(model_name="non-existent-model-123")
        # non_existent_agent.generate("Test")

    except Exception as e:
        print(f"\nAn error occurred during AdvancedAI test: {e}")