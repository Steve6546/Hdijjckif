# ai_agents.py
import os
import subprocess
import time
import logging
# Removed Github and OpenRouter imports as they are no longer used by MasterAgent
# from github import Github
# from openrouter import OpenRouterClient
from abc import ABC, abstractmethod
import io
import json
import zipfile # Keep for zip placeholder if needed elsewhere, or remove if only used in MasterAgent
import os # Keep for path operations if needed
from PIL import Image, ImageOps # Keep for ImageFilterAgent if it remains
# Import the new agents specified in v3.0 spec
from advanced_ai_agent import AdvancedAI
from project_agent import ProjectAgent
# Import the logger
from logging_system import Logger as ActivityLogger # Use alias from app.py
from ai_dev_studio.engine import AIEngine # Import the AIEngine

# Configure logging (keeping existing setup)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/ai_agents.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ai_agents")

# Removed AgentBase, NLPAgent, ImageFilterAgent, DesignAgent, NewCodeAgent, NewImageAgent
# as they are replaced by the new structure or not used in v3.0 MasterAgent.
# Keeping the logger config at the top.

# --- Placeholder Function (Keep if needed, or remove if logic moves elsewhere) ---
def zip_files(file_list: list, archive_name: str):
    """Placeholder function to zip files."""
    logger.info(f"Placeholder: Zipping {file_list} into {archive_name}")
    # Example basic implementation (replace with robust logic if needed)
    try:
        with zipfile.ZipFile(archive_name, 'w') as zipf:
            for file in file_list:
                if os.path.exists(file):
                    zipf.write(file, os.path.basename(file))
                else:
                    logger.warning(f"File not found for zipping: {file}")
        logger.info(f"Successfully created zip archive: {archive_name}")
        return f"تم ضغط الملفات بنجاح في {archive_name}" # Files zipped successfully into {archive_name}
    except Exception as e:
        logger.error(f"Error creating zip file {archive_name}: {e}")
        return f"حدث خطأ أثناء ضغط الملفات: {e}" # Error occurred during zipping


# --- Master Agent v3.0 ---
class MasterAgent:
    """
    Central coordinator for the AI Agent System v3.0.
    Manages specialized agents and logs activities.
    """
    def __init__(self):
        """Initializes the MasterAgent, logger, and specialized agents."""
        # Initialize Logger (using the alias)
        # Consider making the db path configurable
        self.logger = ActivityLogger("logs/activity.db")
        logger.info("ActivityLogger initialized.")

        # Initialize specialized agents
        self.agents = {
            "ai": AdvancedAI(), # Using default model "gpt2" for now
            "project": ProjectAgent()
            # Add other agents here as needed (e.g., image, file processing)
        }
        logger.info(f"Initialized agents: {list(self.agents.keys())}")

        # Initialize AIEngine
        self.ai_engine = AIEngine()
        logger.info("AIEngine initialized.")

        # Removed GitHub/OpenRouter/Update/Security agent initializations from previous versions

    def validate_query(self, query: str) -> str | None:
        """Validates the user query."""
        if not query or not query.strip():
            logger.warning("Validation failed: Empty query received.")
            return "الرجاء كتابة سؤال صحيح." # "Please write a valid question."
        # Add more validation rules if needed
        return None

    async def process_query(self, query: str, user_id: str) -> str:
        """
        Processes a user query, routes to the appropriate agent, and logs the activity.

        Args:
            query (str): The user's query.
            user_id (str): The ID of the user making the query (from auth).

        Returns:
            str: The response from the agent or a default message.
        """
        logger.info(f"Processing query for user '{user_id}': '{query}'")
        response = f"طلب غير معروف أو غير مدعوم: '{query}'" # Default response: "Unknown or unsupported request"

        # --- Routing Logic based on v3.0 spec ---
        try:
            query_lower = query.lower() # Use lowercase for matching

            # Route to AdvancedAI Agent (General Text Generation - kept for compatibility)
            if query.startswith("أنشئ نصًا:") or query_lower.startswith("generate text:"):
                prompt = query.split(":", 1)[-1].strip()
                if prompt and "ai" in self.agents:
                    logger.debug(f"Routing to AdvancedAI agent with prompt: '{prompt}'")
                    response = self.agents["ai"].generate(prompt)
                else:
                    response = "خطأ: لم يتم توفير موجه نص أو وكيل الذكاء الاصطناعي غير متاح." # "Error: No text prompt provided or AI agent unavailable."

            # Route to Project Agent
            elif "إنشاء مشروع" in query or "create project" in query_lower:
                # Attempt to extract project name (simple example)
                parts = query.split()
                project_name = parts[-1] if len(parts) > 1 else "مشروع_جديد" # "new_project"
                if "project" in self.agents:
                    logger.debug(f"Routing to ProjectAgent to create project '{project_name}'")
                    response = self.agents["project"].create_project(project_name, user_id)
                else:
                    response = "خطأ: وكيل إدارة المشاريع غير متاح." # "Error: Project management agent unavailable."

            elif "إضافة مهمة لمشروع" in query or "add task to project" in query_lower:
                # Attempt to extract project name and task (simple example)
                # Assumes format like "إضافة مهمة لمشروع ProjectName: Task Description"
                try:
                    parts = query.split(":", 1)
                    task_description = parts[1].strip()
                    project_part = parts[0]
                    project_name = project_part.split()[-1] # Get last word before ':'
                    if "project" in self.agents:
                        logger.debug(f"Routing to ProjectAgent to add task '{task_description}' to project '{project_name}'")
                        response = self.agents["project"].add_task(project_name, task_description)
                    else:
                        response = "خطأ: وكيل إدارة المشاريع غير متاح." # "Error: Project management agent unavailable."
                except IndexError:
                    response = "خطأ: تنسيق أمر إضافة المهمة غير صحيح. استخدم 'إضافة مهمة لمشروع [اسم المشروع]: [وصف المهمة]'"
                    # "Error: Incorrect format for add task command. Use 'add task to project [Project Name]: [Task Description]'"
                    logger.warning(f"Incorrect format for add task command: {query}")

            # --- AI Dev Studio Routing ---
            elif query_lower.startswith("ai studio: generate"):
                # Example: "AI Studio: Generate HTML for a login form"
                try:
                    parts = query.split(":", 1)
                    generation_prompt = parts[1].strip()
                    # Default to HTML if not specified
                    file_type = "html"
                    if "css" in query_lower:
                        file_type = "css"
                    elif "javascript" in query_lower or "js" in query_lower:
                        file_type = "javascript"
                    elif "backend" in query_lower:
                        file_type = "backend" # Example for backend code
                    logger.info(f"AI Studio: Generating {file_type} code for prompt: '{generation_prompt[:50]}...'")
                    response = self.ai_engine.generate_code(generation_prompt, file_type=file_type)
                except IndexError as e:
                    response = "Error: Invalid AI Studio generate command format. Use 'AI Studio: Generate [HTML/CSS/JavaScript/Backend] for ...'"
                    logger.warning(f"Invalid AI Studio generate command format: {query}")

            elif query_lower.startswith("ai studio: create project"):
                try:
                    parts = query.split(":", 1)
                    project_name = parts[1].strip()
                    logger.info(f"AI Studio: Creating project: '{project_name}'")
                    response = self.ai_engine.create_project(project_name)
                except IndexError as e:
                    response = "Error: Invalid AI Studio create project command. Use 'AI Studio: Create Project [Project Name]'"
                    logger.warning(f"Invalid AI Studio create project command: {query}")

            elif query_lower.startswith("ai studio: get project files"):
                try:
                    parts = query.split(":", 1)
                    project_name = parts[1].strip()
                    logger.info(f"AI Studio: Getting project files for: '{project_name}'")
                    project_files = self.ai_engine.get_project_files(project_name)
                    response = str(project_files) # Convert dict to string for now
                except IndexError as e:
                    response = "Error: Invalid AI Studio get project files command. Use 'AI Studio: Get Project Files [Project Name]'"
                    logger.warning(f"Invalid AI Studio get project files command: {query}")

            else:
                # If no specific route matches, use a generic response
                logger.info(f"No specific route matched for query: '{query}'. Providing generic response.")
                # You could potentially call the NLP agent here as a fallback if needed
                response = f"تم استلام طلبك '{query}' بواسطة {user_id}. لا يوجد إجراء محدد تم تكوينه لهذا الطلب."
                         # "Your request '{query}' by {user_id} was received. No specific action configured for this request."

        except Exception as e:
            logger.error(f"Error processing query '{query}' for user '{user_id}': {e}", exc_info=True)
            response = f"حدث خطأ داخلي أثناء معالجة طلبك." # "An internal error occurred while processing your request."

        # Log the final activity
        try:
            # Ensure response is a string for logging
            log_result = str(response) if response is not None else "None"
            self.logger.log_activity(action=f"Query by {user_id}: {query}", result=log_result)
        except Exception as log_e:
            # Log errors during logging itself, but don't crash the main process
            logger.error(f"Failed to log activity for query '{query}': {log_e}", exc_info=True)

        return response

    # --- Keep existing methods for updates and security ---
    def check_for_updates(self):
        try:
            latest_commit = self.repo.get_commits()[0].sha
            # Ensure git command runs in the correct directory if needed
            current_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
            if latest_commit != current_commit:
                logger.info("New commit found. Updating project...")
                self.update_project()
            else:
                logger.info("No new commits found.")
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")

    def update_project(self):
        try:
            logger.info("Checking for actual updates before pulling...")
            # Ensure git command runs in the correct directory if needed
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
            # Check remote status as well
            subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True, text=True)
            status_ahead = subprocess.run(["git", "rev-list", "HEAD...origin/main", "--count"], capture_output=True, text=True, check=True)
            status_behind = subprocess.run(["git", "rev-list", "origin/main...HEAD", "--count"], capture_output=True, text=True, check=True)

            if int(status_behind.stdout.strip()) > 0: # Check if local is behind remote
                 logger.info("Pulling latest changes from GitHub...")
                 subprocess.run(["git", "pull", "origin", "main"], check=True, capture_output=True, text=True)
                 logger.info("Restarting the application...")
                 # Use environment variable or config for restart command if not always 'replit'
                 restart_cmd = os.getenv("RESTART_COMMAND", "replit restart").split()
                 subprocess.run(restart_cmd, check=True, capture_output=True, text=True)
                 logger.info("Project updated and restarted successfully.")
            else:
                 logger.info("Local repository is up-to-date or ahead. No pull needed.")

        except subprocess.CalledProcessError as e:
            logger.error(f"Error updating project via git: {e.stderr}")
        except Exception as e:
            logger.error(f"Error updating project: {e}")

    def run_security_checks(self):
        # Placeholder for security checks
        logger.info("Running security checks...")
        # Implement security checks here
        logger.info("Security checks completed.")

# --- Existing agents (keep as is or integrate if needed) ---

class UpdateAgent:
    def __init__(self, master_agent):
        self.master_agent = master_agent

    def run_hourly_updates(self):
        while True:
            logger.info("UpdateAgent checking for updates...")
            self.master_agent.check_for_updates()
            time.sleep(3600)  # Check every hour

class SecurityAgent:
    def __init__(self, master_agent):
        self.master_agent = master_agent

    def start_monitoring(self):
        while True:
            logger.info("SecurityAgent running checks...")
            self.master_agent.run_security_checks()
            time.sleep(600)  # Check every 10 minutes

# --- Main block (updated for testing v3.0 MasterAgent) ---

if __name__ == "__main__":
    import asyncio

    async def run_tests():
        # Example usage for testing the new structure
        try:
            # Load environment variables if needed (e.g., using python-dotenv)
            # from dotenv import load_dotenv
            # load_dotenv()

            logger.info("Starting MasterAgent v3.0 tests...")
            master = MasterAgent()

            # Test AI Generation
            test_query_ai = "أنشئ نصًا: عن أهمية الطاقة المتجددة"
            print(f"\nTesting Query: '{test_query_ai}'")
            result_ai = await master.process_query(test_query_ai, user_id="test_user_01")
            print(f"Result: {result_ai}")

            # Test Project Creation
            test_query_proj_create = "إنشاء مشروع موقع التجارة الإلكترونية"
            print(f"\nTesting Query: '{test_query_proj_create}'")
            result_proj_create = await master.process_query(test_query_proj_create, user_id="test_user_02")
            print(f"Result: {result_proj_create}")

            # Test Add Task
            test_query_proj_task = "إضافة مهمة لمشروع موقع التجارة الإلكترونية: إعداد بوابة الدفع"
            print(f"\nTesting Query: '{test_query_proj_task}'")
            result_proj_task = await master.process_query(test_query_proj_task, user_id="test_user_02")
            print(f"Result: {result_proj_task}")

            # Test Add Task (Incorrect Format)
            test_query_proj_task_bad = "إضافة مهمة لمشروع موقع التجارة الإلكترونية"
            print(f"\nTesting Query (Bad Format): '{test_query_proj_task_bad}'")
            result_proj_task_bad = await master.process_query(test_query_proj_task_bad, user_id="test_user_02")
            print(f"Result: {result_proj_task_bad}")

            # Test Unknown Query
            test_query_unknown = "ما هي حالة الطقس اليوم؟"
            print(f"\nTesting Query: '{test_query_unknown}'")
            result_unknown = await master.process_query(test_query_unknown, user_id="test_user_03")
            print(f"Result: {result_unknown}")

            # --- Test AI Dev Studio Commands ---
            test_query_studio_generate = "AI Studio: Generate HTML for a login form"
            print(f"\nTesting AI Studio Generate: '{test_query_studio_generate}'")
            result_studio_generate = await master.process_query(test_query_studio_generate, user_id="test_user_04")
            print(f"Result: {result_studio_generate}")

            test_query_studio_create = "AI Studio: Create Project MyNewWebsite"
            print(f"\nTesting AI Studio Create Project: '{test_query_studio_create}'")
            result_studio_create = await master.process_query(test_query_studio_create, user_id="test_user_04")
            print(f"Result: {result_studio_create}")

            test_query_studio_getfiles = "AI Studio: Get Project Files MyNewWebsite"
            print(f"\nTesting AI Studio Get Project Files: '{test_query_studio_getfiles}'")
            result_studio_getfiles = await master.process_query(test_query_studio_getfiles, user_id="test_user_04")
            print(f"Result: {result_studio_getfiles}")

            test_query_studio_generate_css = "AI Studio: Generate CSS for a dark theme"
            print(f"\nTesting AI Studio Generate CSS: '{test_query_studio_generate_css}'")
            result_studio_generate_css = await master.process_query(test_query_studio_generate_css, user_id="test_user_04")
            print(f"Result: {result_studio_generate_css}")

            test_query_studio_generate_backend = "AI Studio: Generate Backend code for user authentication"
            print(f"\nTesting AI Studio Generate Backend: '{test_query_studio_generate_backend}'")
            result_studio_generate_backend = await master.process_query(test_query_studio_generate_backend, user_id="test_user_04")
            print(f"Result: {result_studio_generate_backend}")

        except ValueError as e:
            print(f"Configuration error during test: {e}")
        except Exception as e:
            print(f"An error occurred during test: {e}")
        finally:
            # Close logger connection if necessary (depends on logger implementation)
            if hasattr(master.logger, 'close'):
                 master.logger.close()

    # Run the async test function
    asyncio.run(run_tests())