# advanced_ai_agent.py
import logging
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

class AdvancedAI:
    """
    Agent using Hugging Face transformers for advanced text generation.
    """
    def __init__(self, model_name="gpt2"): # Default to gpt2, can be changed
        """
        Initializes the text generation pipeline. Downloads the model on first use if not cached.

        Args:
            model_name (str): The name of the Hugging Face model to use (e.g., "gpt2", "gpt2-medium", an Arabic model).
        """
        self.model_name = model_name
        self.generator = None
        try:
            # Initialize pipeline - this might take time on first run to download model
            logger.info(f"Initializing text generation pipeline with model: {self.model_name}")
            # Check if model exists locally first? (More advanced setup)
            # For simplicity, directly initialize pipeline
            self.generator = pipeline("text-generation", model=self.model_name)
            logger.info(f"Pipeline for model {repr(self.model_name)} initialized successfully.")
        except OSError as e:
             logger.error(f"Could not find or load model {repr(self.model_name)}. "
                          f"Ensure it's a valid Hugging Face model name and you have internet access. Error: {e}")
             # You might want to fall back to a simpler mechanism or raise the error
             # For now, the agent will fail gracefully in generate() if self.generator is None.
        except Exception as e:
            logger.error(f"An unexpected error occurred during pipeline initialization: {e}", exc_info=True)
            # Handle other potential errors (e.g., missing dependencies like torch/tensorflow)

    def generate(self, prompt: str, max_length=150, num_return_sequences=1) -> str:
        """
        Generates text based on a given prompt.

        Args:
            prompt (str): The text prompt to start generation from.
            max_length (int): The maximum length of the generated text sequence.
            num_return_sequences (int): The number of sequences to generate.

        Returns:
            str: The generated text, or an error message if generation fails.
        """
        if not self.generator:
            logger.error("Text generation pipeline not initialized. Cannot generate text.")
            return "خطأ: لم يتم تهيئة وكيل الذكاء الاصطناعي بشكل صحيح." # "Error: AI agent not initialized correctly."

        logger.info(f"Generating text for prompt (first 50 chars): '{prompt[:50]}...'")
        try:
            # Generate text
            results = self.generator(
                prompt,
                max_length=max_length,
                num_return_sequences=num_return_sequences,
                pad_token_id=self.generator.tokenizer.eos_token_id # Suppress warning for models like gpt2
            )
            # Extract the generated text from the first result
            generated_text = results[0]['generated_text']
            logger.info(f"Text generation successful.")
            logger.debug(f"Generated text: {generated_text}")
            return generated_text
        except Exception as e:
            logger.error(f"Error during text generation: {e}", exc_info=True)
            return f"خطأ أثناء توليد النص: {e}" # "Error during text generation: {e}"

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