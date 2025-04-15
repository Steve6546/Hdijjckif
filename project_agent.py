# project_agent.py
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ProjectAgent:
    """
    Agent responsible for basic project management tasks.
    Uses in-memory dictionary for storage (non-persistent).
    """
    def __init__(self):
        """Initializes the project agent with an empty project dictionary."""
        # In-memory storage. Replace with a database (e.g., SQLite, JSON file)
        # for persistence across application restarts.
        self.projects: Dict[str, Dict[str, Any]] = {}
        logger.info("ProjectAgent initialized with in-memory storage.")

    def create_project(self, name: str, owner_id: str) -> str:
        """
        Creates a new project if it doesn't exist.

        Args:
            name: The name of the project.
            owner_id: The identifier of the user creating the project.

        Returns:
            A status message indicating success or failure.
        """
        logger.info(f"Attempting to create project '{name}' for user '{owner_id}'.")
        if not name or not name.strip():
             logger.warning("Project creation failed: Project name cannot be empty.")
             return "خطأ: اسم المشروع لا يمكن أن يكون فارغًا." # "Error: Project name cannot be empty."
        if name in self.projects:
            logger.warning(f"Project creation failed: Project '{name}' already exists.")
            return f"خطأ: المشروع '{name}' موجود بالفعل." # "Error: Project '{name}' already exists."

        self.projects[name] = {"owner": owner_id, "status": "جديد", "tasks": []} # "new"
        logger.info(f"Project '{name}' created successfully for user '{owner_id}'.")
        return f"تم إنشاء المشروع '{name}' بواسطة {owner_id}." # "Project '{name}' created by {owner_id}."

    def add_task(self, project_name: str, task: str) -> str:
        """
        Adds a task to an existing project.

        Args:
            project_name: The name of the project to add the task to.
            task: The description of the task.

        Returns:
            A status message indicating success or failure.
        """
        logger.info(f"Attempting to add task '{task}' to project '{project_name}'.")
        if not project_name or not project_name.strip() or not task or not task.strip():
             logger.warning("Add task failed: Project name and task cannot be empty.")
             return "خطأ: اسم المشروع والمهمة لا يمكن أن يكونا فارغين." # "Error: Project name and task cannot be empty."
        if project_name not in self.projects:
            logger.warning(f"Add task failed: Project '{project_name}' not found.")
            return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."

        self.projects[project_name]["tasks"].append(task)
        logger.info(f"Task '{task}' added successfully to project '{project_name}'.")
        return f"تمت إضافة المهمة '{task}' للمشروع '{project_name}'." # "Task '{task}' added to project '{project_name}'."

    def get_project_details(self, project_name: str) -> Dict[str, Any] | str:
        """
        Retrieves details for a specific project.

        Args:
            project_name: The name of the project.

        Returns:
            A dictionary with project details or an error message string.
        """
        logger.info(f"Retrieving details for project '{project_name}'.")
        if project_name in self.projects:
            return self.projects[project_name]
        else:
            logger.warning(f"Get details failed: Project '{project_name}' not found.")
            return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."

    def list_projects(self) -> List[str]:
         """Lists the names of all current projects."""
         logger.info("Listing all projects.")
         return list(self.projects.keys())

    # --- Potential future methods ---
    # def delete_project(self, project_name: str, user_id: str) -> str:
    #     """Deletes a project if the user is the owner."""
    #     # Add ownership check
    #     pass
    #
    # def update_status(self, project_name: str, status: str) -> str:
    #     """Updates the status of a project."""
    #     pass

# Example usage (optional, for testing)
if __name__ == "__main__":
    project_agent = ProjectAgent()

    print(project_agent.create_project("WebApp Redesign", "user123"))
    print(project_agent.create_project("WebApp Redesign", "user456")) # Error: exists
    print(project_agent.create_project("API Development", "user123"))

    print(project_agent.add_task("WebApp Redesign", "Design mockups"))
    print(project_agent.add_task("WebApp Redesign", "Develop frontend"))
    print(project_agent.add_task("API Development", "Define endpoints"))
    print(project_agent.add_task("NonExistent Project", "Do something")) # Error: not found

    print("\nProject List:", project_agent.list_projects())
    print("\nWebApp Redesign Details:", project_agent.get_project_details("WebApp Redesign"))
    print("\nNonExistent Project Details:", project_agent.get_project_details("NonExistent Project"))