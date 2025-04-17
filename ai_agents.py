# ai_agents.py
import os
import subprocess
import time
import logging
import io
import json
import zipfile
from typing import Dict, Any, List, Optional, Union
from PIL import Image, ImageOps

# Import the specialized agents
from advanced_ai_agent import AdvancedAI
from project_agent import ProjectAgent
from agents.image_agent import ImageAgent
# Import the logger
from logging_system import Logger as ActivityLogger
from ai_dev_studio.engine import AIEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/ai_agents.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ai_agents")

# --- Utility Functions ---
def zip_files(file_list: list, archive_name: str) -> str:
    """
    Creates a zip archive containing the specified files.
    
    Args:
        file_list (list): List of file paths to include in the archive
        archive_name (str): Name of the output zip file
        
    Returns:
        str: Success or error message
    """
    logger.info(f"Zipping {len(file_list)} files into {archive_name}")
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
        # Initialize Logger
        self.logger = ActivityLogger("logs/activity.db")
        logger.info("ActivityLogger initialized.")

        # Initialize specialized agents with shared configuration
        # Get OpenRouter API key from environment
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        default_model = os.getenv("ADVANCED_AI_MODEL", "google/gemini-2.5-pro-exp-03-25:free")
        
        # Initialize AI agent first
        ai_agent = AdvancedAI(model_name=default_model)
        
        # Initialize agents with shared configuration
        self.agents = {
            "ai": ai_agent,  # Text generation agent
            "project": ProjectAgent("data/projects.db"),  # Project management with persistent storage
            "image": ImageAgent(ai_agent=ai_agent)  # Image processing agent with AI capabilities
        }
        logger.info(f"Initialized agents: {list(self.agents.keys())}")

        # Initialize AIEngine for code generation with the same AI model
        self.ai_engine = AIEngine(ai_model=self.agents["ai"])
        logger.info("AIEngine initialized.")
        
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("uploads", exist_ok=True)
        logger.info("Ensured required directories exist.")

    def validate_query(self, query: str) -> Optional[str]:
        """
        Validates the user query.
        
        Args:
            query (str): The query to validate
            
        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        if not query or not query.strip():
            logger.warning("Validation failed: Empty query received.")
            return "الرجاء كتابة سؤال صحيح." # "Please write a valid question."
        
        # Add more validation rules if needed
        return None

    async def process_query(self, query: str, user_id: str, model: str = None, temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Processes a user query, routes to the appropriate agent, and logs the activity.

        Args:
            query (str): The user's query.
            user_id (str): The ID of the user making the query (from auth).
            model (str, optional): The model to use for generation.
            temperature (float, optional): The temperature parameter for generation.
            top_p (float, optional): The top_p parameter for generation.

        Returns:
            str: The response from the agent or a default message.
        """
        logger.info(f"Processing query for user '{user_id}': '{query}'")
        
        # Validate query
        validation_error = self.validate_query(query)
        if validation_error:
            return validation_error
            
        response = f"طلب غير معروف أو غير مدعوم: '{query}'" # Default response: "Unknown or unsupported request"

        # --- Routing Logic ---
        try:
            query_lower = query.lower() # Use lowercase for matching

            # --- Text Generation (AdvancedAI) ---
            if query.startswith("أنشئ نصًا:") or query_lower.startswith("generate text:"):
                prompt = query.split(":", 1)[-1].strip()
                if prompt and "ai" in self.agents:
                    logger.debug(f"Routing to AdvancedAI agent with prompt: '{prompt}'")
                    # Pass model and parameters if provided
                    if model:
                        # Temporarily switch model if specified
                        original_model = self.agents["ai"].model_name
                        self.agents["ai"].model_name = model
                        response = self.agents["ai"].generate(prompt, temperature=temperature, top_p=top_p)
                        # Restore original model
                        self.agents["ai"].model_name = original_model
                    else:
                        response = self.agents["ai"].generate(prompt, temperature=temperature, top_p=top_p)
                else:
                    response = "خطأ: لم يتم توفير موجه نص أو وكيل الذكاء الاصطناعي غير متاح." # "Error: No text prompt provided or AI agent unavailable."
            
            # --- Advanced AI Model Management ---
            elif "تغيير نموذج" in query or "switch model" in query_lower:
                # Extract model name - simple approach
                model_parts = query.split("إلى" if "إلى" in query else "to")
                if len(model_parts) > 1:
                    model_name = model_parts[1].strip()
                    if "ai" in self.agents:
                        logger.debug(f"Switching AI model to: '{model_name}'")
                        response = self.agents["ai"].switch_model(model_name)
                    else:
                        response = "خطأ: وكيل الذكاء الاصطناعي غير متاح." # "Error: AI agent unavailable."
                else:
                    response = "خطأ: يرجى تحديد اسم النموذج. مثال: 'تغيير نموذج إلى gpt2-medium'" # "Error: Please specify model name. Example: 'switch model to gpt2-medium'"
            
            elif "عرض النماذج المتاحة" in query or "list available models" in query_lower:
                if "ai" in self.agents:
                    models = self.agents["ai"].get_available_models()
                    model_info = "\n".join([f"- {name}: {info['description']} ({info['language']})" for name, info in models.items()])
                    response = f"النماذج المتاحة:\n{model_info}" # "Available models:\n{model_info}"
                else:
                    response = "خطأ: وكيل الذكاء الاصطناعي غير متاح." # "Error: AI agent unavailable."

            # --- Project Management ---
            elif "إنشاء مشروع" in query or "create project" in query_lower:
                # Extract project name
                parts = query.split()
                project_name = parts[-1] if len(parts) > 1 else "مشروع_جديد" # "new_project"
                if "project" in self.agents:
                    logger.debug(f"Routing to ProjectAgent to create project '{project_name}'")
                    response = self.agents["project"].create_project(project_name, user_id)
                else:
                    response = "خطأ: وكيل إدارة المشاريع غير متاح." # "Error: Project management agent unavailable."

            elif "إضافة مهمة لمشروع" in query or "add task to project" in query_lower:
                # Extract project name and task
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
            
            elif "عرض المشاريع" in query or "list projects" in query_lower:
                if "project" in self.agents:
                    # Check if filtering by user
                    if "الخاصة بي" in query or "my" in query_lower:
                        projects = self.agents["project"].list_projects(user_id)
                    else:
                        projects = self.agents["project"].list_projects()
                    
                    if projects:
                        project_list = "\n".join([f"- {p['name']} ({p['status']}) - {p['task_count']} مهام" for p in projects])
                        response = f"المشاريع:\n{project_list}" # "Projects:\n{project_list}"
                    else:
                        response = "لا توجد مشاريع متاحة." # "No projects available."
                else:
                    response = "خطأ: وكيل إدارة المشاريع غير متاح." # "Error: Project management agent unavailable."
            
            elif "تفاصيل مشروع" in query or "project details" in query_lower:
                # Extract project name
                parts = query.split()
                project_name = parts[-1] if len(parts) > 1 else ""
                if project_name and "project" in self.agents:
                    details = self.agents["project"].get_project_details(project_name)
                    if isinstance(details, dict):
                        # Format project details
                        tasks_info = "\n".join([f"- {t.get('description', 'مهمة')} ({t.get('status', 'قيد الانتظار')})" for t in details.get("tasks", [])])
                        response = f"مشروع: {details.get('name', project_name)}\n" \
                                  f"المالك: {details.get('owner', 'غير معروف')}\n" \
                                  f"الحالة: {details.get('status', 'غير معروف')}\n" \
                                  f"تاريخ الإنشاء: {details.get('created_at', 'غير معروف')}\n" \
                                  f"المهام:\n{tasks_info if tasks_info else 'لا توجد مهام'}"
                    else:
                        response = str(details) # Error message
                else:
                    response = "خطأ: يرجى تحديد اسم المشروع أو وكيل إدارة المشاريع غير متاح." # "Error: Please specify project name or project agent unavailable."
            
            elif "حذف مشروع" in query or "delete project" in query_lower:
                # Extract project name
                parts = query.split()
                project_name = parts[-1] if len(parts) > 1 else ""
                if project_name and "project" in self.agents:
                    response = self.agents["project"].delete_project(project_name, user_id)
                else:
                    response = "خطأ: يرجى تحديد اسم المشروع أو وكيل إدارة المشاريع غير متاح." # "Error: Please specify project name or project agent unavailable."

            # --- Image Processing ---
            elif any(term in query_lower or term in query for term in ["معالجة صورة", "process image", "edit image", "تعديل صورة"]):
                response = "يرجى استخدام نقطة نهاية /api/edit_image لتحميل وتعديل الصورة. قم بتحديد الصورة ونوع المعالجة المطلوبة." 
                # "Please use the /api/edit_image endpoint to upload and edit an image. Specify the image and the type of processing required."
            
            # --- AI Dev Studio ---
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

            # --- Help Command ---
            elif "مساعدة" in query or "help" in query_lower:
                response = self._generate_help_text()

            # --- Greetings and Simple Queries ---
            elif any(greeting in query_lower or greeting in query for greeting in ["hello", "hi", "hey", "مرحبا", "هلا", "السلام عليكم"]):
                # Handle greetings
                is_arabic = any(ar_char in query for ar_char in "مرحباهلاأهلاالسلام")
                if is_arabic:
                    response = f"مرحباً {user_id}! كيف يمكنني مساعدتك اليوم؟ يمكنك كتابة 'مساعدة' للحصول على قائمة بالأوامر المدعومة."
                else:
                    response = f"Hello {user_id}! How can I help you today? You can type 'help' to see a list of supported commands."
            
            # --- Use AI for general queries ---
            elif len(query.split()) <= 20:  # For short queries, use AI directly
                logger.info(f"Using AI agent for general query: '{query}'")
                if "ai" in self.agents:
                    # Pass model and parameters if provided
                    if model:
                        # Temporarily switch model if specified
                        original_model = self.agents["ai"].model_name
                        self.agents["ai"].model_name = model
                        response = self.agents["ai"].generate(query, temperature=temperature, top_p=top_p)
                        # Restore original model
                        self.agents["ai"].model_name = original_model
                    else:
                        response = self.agents["ai"].generate(query, temperature=temperature, top_p=top_p)
                else:
                    # If no specific route matches, use a generic response
                    logger.info(f"No specific route matched for query: '{query}'. Providing generic response.")
                    response = f"تم استلام طلبك '{query}' بواسطة {user_id}. لا يوجد إجراء محدد تم تكوينه لهذا الطلب. اكتب 'مساعدة' للحصول على قائمة بالأوامر المدعومة."
            
            else:
                # If no specific route matches, use a generic response
                logger.info(f"No specific route matched for query: '{query}'. Providing generic response.")
                response = f"تم استلام طلبك '{query}' بواسطة {user_id}. لا يوجد إجراء محدد تم تكوينه لهذا الطلب. اكتب 'مساعدة' للحصول على قائمة بالأوامر المدعومة."
                         # "Your request '{query}' by {user_id} was received. No specific action configured for this request. Type 'help' for a list of supported commands."

        except Exception as e:
            logger.error(f"Error processing query '{query}' for user '{user_id}': {e}", exc_info=True)
            response = f"حدث خطأ داخلي أثناء معالجة طلبك: {str(e)}" # "An internal error occurred while processing your request: {str(e)}"

        # Log the final activity
        try:
            # Ensure response is a string for logging
            log_result = str(response) if response is not None else "None"
            self.logger.log_activity(action=f"Query by {user_id}: {query}", result=log_result)
        except Exception as log_e:
            # Log errors during logging itself, but don't crash the main process
            logger.error(f"Failed to log activity for query '{query}': {log_e}", exc_info=True)

        return response
    
    def _generate_help_text(self) -> str:
        """
        Generates help text with available commands.
        
        Returns:
            str: Formatted help text
        """
        help_text = """# الأوامر المدعومة

## توليد النص
- `أنشئ نصًا: [النص المطلوب]` - توليد نص باستخدام نموذج الذكاء الاصطناعي
- `تغيير نموذج إلى [اسم النموذج]` - تغيير نموذج الذكاء الاصطناعي المستخدم
- `عرض النماذج المتاحة` - عرض قائمة بنماذج الذكاء الاصطناعي المتاحة

## إدارة المشاريع
- `إنشاء مشروع [اسم المشروع]` - إنشاء مشروع جديد
- `إضافة مهمة لمشروع [اسم المشروع]: [وصف المهمة]` - إضافة مهمة جديدة إلى مشروع
- `عرض المشاريع` - عرض قائمة بجميع المشاريع
- `عرض المشاريع الخاصة بي` - عرض قائمة بالمشاريع الخاصة بك
- `تفاصيل مشروع [اسم المشروع]` - عرض تفاصيل مشروع محدد
- `حذف مشروع [اسم المشروع]` - حذف مشروع محدد

## معالجة الصور
- `معالجة صورة` - الحصول على معلومات حول كيفية معالجة الصور

## استوديو الذكاء الاصطناعي
- `AI Studio: Generate HTML for [وصف]` - توليد كود HTML
- `AI Studio: Generate CSS for [وصف]` - توليد كود CSS
- `AI Studio: Generate JavaScript for [وصف]` - توليد كود JavaScript
- `AI Studio: Generate Backend for [وصف]` - توليد كود الواجهة الخلفية
- `AI Studio: Create Project [اسم المشروع]` - إنشاء مشروع جديد في استوديو الذكاء الاصطناعي
- `AI Studio: Get Project Files [اسم المشروع]` - عرض ملفات مشروع في استوديو الذكاء الاصطناعي

## عام
- `مساعدة` - عرض هذه القائمة من الأوامر
"""
        return help_text
    
    async def process_image(self, query: str, image_bytes: bytes, user_id: str) -> Dict[str, Any]:
        """
        Processes an image with the specified query.
        
        Args:
            query (str): The query describing the image processing
            image_bytes (bytes): The raw image data
            user_id (str): The ID of the user making the request
            
        Returns:
            Dict[str, Any]: Result containing either a message or image path
        """
        logger.info(f"Processing image request from user '{user_id}': '{query}'")
        
        try:
            if "image" not in self.agents:
                logger.error("Image agent not available")
                return {"message": "خطأ: وكيل معالجة الصور غير متاح."} # "Error: Image processing agent unavailable."
            
            # Process the image using the image agent
            result = self.agents["image"].process(query, image_bytes)
            
            # Log the activity
            self.logger.log_activity(
                action=f"Image processing by {user_id}: {query}", 
                result=str(result.get("message", "Success"))
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            return {"message": f"حدث خطأ أثناء معالجة الصورة: {str(e)}"}
    
    def close(self):
        """Closes connections and performs cleanup."""
        # Close the activity logger
        if hasattr(self.logger, 'close'):
            self.logger.close()
            logger.info("Activity logger closed.")
        
        # Close the project agent's database connection
        if "project" in self.agents and hasattr(self.agents["project"], 'close'):
            self.agents["project"].close()
            logger.info("Project agent database connection closed.")

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