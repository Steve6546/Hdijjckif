# ai_dev_studio/engine.py
import logging
import os
from advanced_ai_agent import AdvancedAI

logger = logging.getLogger(__name__)

class AIEngine:
    """
    AI engine for generating and managing web development project code.
    This version includes a basic in-memory project structure.
    """
    def __init__(self):
        """Initializes the AIEngine with the AdvancedAI agent and a basic project structure."""
        try:
            self.ai_agent = AdvancedAI()
            logger.info("AIEngine initialized with AdvancedAI agent.")
        except Exception as e:
            logger.error(f"Error initializing AIEngine: {e}", exc_info=True)
            self.ai_agent = None

        # Basic in-memory project structure (non-persistent)
        self.project_files = {} # Dict to store file content, key=filepath, value=content

    def create_project(self, project_name: str) -> str:
        """Creates a new, empty project structure in memory."""
        if project_name in self.project_files:
            return f"Error: Project '{project_name}' already exists."

        # Basic project structure (can be expanded)
        self.project_files[f"{project_name}/index.html"] = ""
        self.project_files[f"{project_name}/style.css"] = ""
        self.project_files[f"{project_name}/script.js"] = ""
        logger.info(f"Created new project structure in memory: {project_name}")
        return f"Project '{project_name}' created successfully."

    def generate_code(self, prompt: str, file_type: str = "html", project_name: str = None) -> str:
        """
        Generates a code snippet based on the given prompt and file type.

        Args:
            prompt: A text prompt describing the desired code.
            file_type: The type of code to generate (e.g., "html", "css", "javascript", "backend").
            project_name: The name of the project to add the code to. If None, generates standalone code.

        Returns:
            A string containing the generated code snippet, or an error message.
        """
        if not self.ai_agent:
            logger.error("Cannot generate code: AdvancedAI agent not initialized.")
            return "Error: AI code generation is currently unavailable."

        try:
            # Add some context or instructions suitable for code generation
            code_prompt = f"Generate only {file_type} code for the following request: {prompt}"
            logger.info(f"Generating {file_type} code with prompt (truncated): '{code_prompt[:100]}...'")
            generated_code = self.ai_agent.generate(code_prompt)
            logger.info("Code generation successful.")

            if project_name:
                # Add to project if project_name is given
                filepath = f"{project_name}/"
                if file_type == "html":
                    filepath += "index.html"
                elif file_type == "css":
                    filepath += "style.css"
                elif file_type == "javascript":
                    filepath += "script.js"
                else:
                    filepath = None # Invalid file type

                if filepath:
                    if filepath in self.project_files:
                        self.project_files[filepath] += generated_code # Append to existing file
                        logger.info(f"Appended generated {file_type} code to {filepath}")
                    else:
                        logger.warning(f"File {filepath} not found in project. Code not added.")
                        return f"Error: File {filepath} not found in project. Code not added."
                else:
                    return "Error: Invalid file type specified."
            return generated_code

        except Exception as e:
            logger.error(f"Error during code generation: {e}", exc_info=True)
            return f"Error: Code generation failed. Details: {e}"

    def get_project_files(self, project_name: str) -> dict | str:
        """Returns the files and content for a given project."""
        project_files = {}
        for filepath, content in self.project_files.items():
            if filepath.startswith(f"{project_name}/"):
                project_files[filepath] = content
        if project_files:
            return project_files
        else:
            return f"Error: Project '{project_name}' not found."

# Example usage (for testing)
if __name__ == "__main__":
    ai_engine = AIEngine()
    if ai_engine.ai_agent:
        ai_engine.create_project("MyWebApp")
        test_prompt = "Create a simple HTML form with fields for name and email"
        generated_html = ai_engine.generate_code(test_prompt, file_type="html", project_name="MyWebApp")
        print(f"Generated HTML:\n{generated_html}")

        test_prompt_css = "Add a dark theme with a blue accent color"
        generated_css = ai_engine.generate_code(test_prompt_css, file_type="css", project_name="MyWebApp")
        print(f"Generated CSS:\n{generated_css}")

        project_files = ai_engine.get_project_files("MyWebApp")
        print("\nProject Files:")
        for filepath, content in project_files.items():
            print(f"\n--- {filepath} ---\n{content}")

    else:
        print("AIEngine could not be initialized.")