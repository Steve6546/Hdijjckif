# project_agent.py
import logging
import sqlite3
import os
import json
import datetime
from typing import Dict, List, Any, Union, Optional

logger = logging.getLogger(__name__)

class ProjectAgent:
    """
    Agent responsible for project management tasks.
    Uses SQLite database for persistent storage.
    """
    def __init__(self, db_path: str = "projects.db"):
        """
        Initializes the project agent with a SQLite database connection.
        
        Args:
            db_path (str): Path to the SQLite database file. Defaults to "projects.db".
        """
        self.db_path = db_path
        self.conn = None
        
        try:
            # Ensure the directory for the db exists if it's not in the root
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logger.info(f"Created directory for database: {db_dir}")
                
            # Connect to the database
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
            # Create tables if they don't exist
            self._create_tables()
            logger.info(f"ProjectAgent initialized with SQLite database at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"SQLite error during initialization: {e}")
            # Fall back to in-memory storage if database connection fails
            self.conn = None
            self.projects = {}
            logger.warning("Falling back to in-memory storage due to database connection failure.")
        except Exception as e:
            logger.error(f"Error during ProjectAgent initialization: {e}", exc_info=True)
            # Fall back to in-memory storage
            self.conn = None
            self.projects = {}
            logger.warning("Falling back to in-memory storage due to initialization error.")

    def _create_tables(self):
        """Creates the necessary tables in the database if they don't exist."""
        try:
            with self.conn:
                # Projects table
                self.conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    owner_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
                
                # Tasks table with foreign key to projects
                self.conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
                )
                """)
                
                logger.info("Database tables created successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error creating database tables: {e}")
            raise

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
        
        # Use database if available, otherwise use in-memory storage
        if self.conn:
            try:
                now = datetime.datetime.now().isoformat()
                with self.conn:
                    self.conn.execute(
                        "INSERT INTO projects (name, owner_id, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                        (name, owner_id, "جديد", now, now)
                    )
                logger.info(f"Project '{name}' created successfully for user '{owner_id}' in database.")
                return f"تم إنشاء المشروع '{name}' بواسطة {owner_id}." # "Project '{name}' created by {owner_id}."
            except sqlite3.IntegrityError:
                logger.warning(f"Project creation failed: Project '{name}' already exists in database.")
                return f"خطأ: المشروع '{name}' موجود بالفعل." # "Error: Project '{name}' already exists."
            except sqlite3.Error as e:
                logger.error(f"SQLite error during project creation: {e}")
                return f"خطأ في قاعدة البيانات: {e}" # "Database error: {e}"
        else:
            # Fallback to in-memory storage
            if name in self.projects:
                logger.warning(f"Project creation failed: Project '{name}' already exists in memory.")
                return f"خطأ: المشروع '{name}' موجود بالفعل." # "Error: Project '{name}' already exists."
            
            now = datetime.datetime.now().isoformat()
            self.projects[name] = {
                "owner": owner_id, 
                "status": "جديد", 
                "tasks": [],
                "created_at": now,
                "updated_at": now
            }
            logger.info(f"Project '{name}' created successfully for user '{owner_id}' in memory.")
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
        
        # Use database if available, otherwise use in-memory storage
        if self.conn:
            try:
                # First check if the project exists
                cursor = self.conn.execute("SELECT id FROM projects WHERE name = ?", (project_name,))
                project = cursor.fetchone()
                
                if not project:
                    logger.warning(f"Add task failed: Project '{project_name}' not found in database.")
                    return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."
                
                project_id = project[0]
                now = datetime.datetime.now().isoformat()
                
                with self.conn:
                    self.conn.execute(
                        "INSERT INTO tasks (project_id, description, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                        (project_id, task, "قيد الانتظار", now, now)
                    )
                    # Update the project's updated_at timestamp
                    self.conn.execute(
                        "UPDATE projects SET updated_at = ? WHERE id = ?",
                        (now, project_id)
                    )
                
                logger.info(f"Task '{task}' added successfully to project '{project_name}' in database.")
                return f"تمت إضافة المهمة '{task}' للمشروع '{project_name}'." # "Task '{task}' added to project '{project_name}'."
            except sqlite3.Error as e:
                logger.error(f"SQLite error during task addition: {e}")
                return f"خطأ في قاعدة البيانات: {e}" # "Database error: {e}"
        else:
            # Fallback to in-memory storage
            if project_name not in self.projects:
                logger.warning(f"Add task failed: Project '{project_name}' not found in memory.")
                return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."
            
            now = datetime.datetime.now().isoformat()
            task_obj = {
                "description": task,
                "status": "قيد الانتظار",
                "created_at": now,
                "updated_at": now
            }
            self.projects[project_name]["tasks"].append(task_obj)
            self.projects[project_name]["updated_at"] = now
            
            logger.info(f"Task '{task}' added successfully to project '{project_name}' in memory.")
            return f"تمت إضافة المهمة '{task}' للمشروع '{project_name}'." # "Task '{task}' added to project '{project_name}'."

    def get_project_details(self, project_name: str) -> Dict[str, Any]:
        """
        Retrieves details for a specific project.

        Args:
            project_name: The name of the project.

        Returns:
            A dictionary with project details or an error message string.
        """
        logger.info(f"Retrieving details for project '{project_name}'.")
        
        # Use database if available, otherwise use in-memory storage
        if self.conn:
            try:
                # Get project details
                cursor = self.conn.execute(
                    "SELECT id, name, owner_id, status, created_at, updated_at FROM projects WHERE name = ?", 
                    (project_name,)
                )
                project = cursor.fetchone()
                
                if not project:
                    logger.warning(f"Get details failed: Project '{project_name}' not found in database.")
                    return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."
                
                project_id, name, owner_id, status, created_at, updated_at = project
                
                # Get tasks for the project
                cursor = self.conn.execute(
                    "SELECT id, description, status, created_at, updated_at FROM tasks WHERE project_id = ? ORDER BY created_at",
                    (project_id,)
                )
                tasks = []
                for task_row in cursor.fetchall():
                    task_id, description, task_status, task_created_at, task_updated_at = task_row
                    tasks.append({
                        "id": task_id,
                        "description": description,
                        "status": task_status,
                        "created_at": task_created_at,
                        "updated_at": task_updated_at
                    })
                
                # Construct project details dictionary
                project_details = {
                    "id": project_id,
                    "name": name,
                    "owner": owner_id,
                    "status": status,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "tasks": tasks
                }
                
                return project_details
            except sqlite3.Error as e:
                logger.error(f"SQLite error retrieving project details: {e}")
                return f"خطأ في قاعدة البيانات: {e}" # "Database error: {e}"
        else:
            # Fallback to in-memory storage
            if project_name in self.projects:
                return self.projects[project_name]
            else:
                logger.warning(f"Get details failed: Project '{project_name}' not found in memory.")
                return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."

    def list_projects(self, owner_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lists all projects, optionally filtered by owner.
        
        Args:
            owner_id (str, optional): If provided, only returns projects owned by this user.
            
        Returns:
            List of project dictionaries with basic information.
        """
        logger.info(f"Listing projects" + (f" for owner '{owner_id}'" if owner_id else ""))
        
        # Use database if available, otherwise use in-memory storage
        if self.conn:
            try:
                if owner_id:
                    cursor = self.conn.execute(
                        "SELECT id, name, status, created_at, updated_at FROM projects WHERE owner_id = ? ORDER BY updated_at DESC",
                        (owner_id,)
                    )
                else:
                    cursor = self.conn.execute(
                        "SELECT id, name, owner_id, status, created_at, updated_at FROM projects ORDER BY updated_at DESC"
                    )
                
                projects = []
                for row in cursor.fetchall():
                    if owner_id:
                        project_id, name, status, created_at, updated_at = row
                        owner = owner_id
                    else:
                        project_id, name, owner, status, created_at, updated_at = row
                    
                    # Count tasks for this project
                    task_cursor = self.conn.execute(
                        "SELECT COUNT(*) FROM tasks WHERE project_id = ?",
                        (project_id,)
                    )
                    task_count = task_cursor.fetchone()[0]
                    
                    projects.append({
                        "id": project_id,
                        "name": name,
                        "owner": owner,
                        "status": status,
                        "task_count": task_count,
                        "created_at": created_at,
                        "updated_at": updated_at
                    })
                
                return projects
            except sqlite3.Error as e:
                logger.error(f"SQLite error listing projects: {e}")
                return []
        else:
            # Fallback to in-memory storage
            projects = []
            for name, details in self.projects.items():
                if owner_id and details["owner"] != owner_id:
                    continue
                
                projects.append({
                    "name": name,
                    "owner": details["owner"],
                    "status": details["status"],
                    "task_count": len(details.get("tasks", [])),
                    "created_at": details.get("created_at", ""),
                    "updated_at": details.get("updated_at", "")
                })
            
            # Sort by updated_at in descending order
            projects.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return projects

    def delete_project(self, project_name: str, user_id: str) -> str:
        """
        Deletes a project if the user is the owner.
        
        Args:
            project_name (str): The name of the project to delete.
            user_id (str): The ID of the user attempting to delete the project.
            
        Returns:
            str: Success or error message.
        """
        logger.info(f"Attempting to delete project '{project_name}' by user '{user_id}'.")
        
        # Use database if available, otherwise use in-memory storage
        if self.conn:
            try:
                # Check if project exists and user is the owner
                cursor = self.conn.execute(
                    "SELECT id, owner_id FROM projects WHERE name = ?",
                    (project_name,)
                )
                project = cursor.fetchone()
                
                if not project:
                    logger.warning(f"Delete project failed: Project '{project_name}' not found.")
                    return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."
                
                project_id, owner_id = project
                
                if owner_id != user_id:
                    logger.warning(f"Delete project failed: User '{user_id}' is not the owner of project '{project_name}'.")
                    return f"خطأ: لا يمكنك حذف هذا المشروع لأنك لست المالك." # "Error: You cannot delete this project as you are not the owner."
                
                # Delete the project (tasks will be deleted automatically due to CASCADE)
                with self.conn:
                    self.conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                
                logger.info(f"Project '{project_name}' deleted successfully by user '{user_id}'.")
                return f"تم حذف المشروع '{project_name}' بنجاح." # "Project '{project_name}' deleted successfully."
            except sqlite3.Error as e:
                logger.error(f"SQLite error during project deletion: {e}")
                return f"خطأ في قاعدة البيانات: {e}" # "Database error: {e}"
        else:
            # Fallback to in-memory storage
            if project_name not in self.projects:
                logger.warning(f"Delete project failed: Project '{project_name}' not found in memory.")
                return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."
            
            if self.projects[project_name]["owner"] != user_id:
                logger.warning(f"Delete project failed: User '{user_id}' is not the owner of project '{project_name}'.")
                return f"خطأ: لا يمكنك حذف هذا المشروع لأنك لست المالك." # "Error: You cannot delete this project as you are not the owner."
            
            del self.projects[project_name]
            logger.info(f"Project '{project_name}' deleted successfully by user '{user_id}' from memory.")
            return f"تم حذف المشروع '{project_name}' بنجاح." # "Project '{project_name}' deleted successfully."

    def update_project_status(self, project_name: str, status: str, user_id: str) -> str:
        """
        Updates the status of a project.
        
        Args:
            project_name (str): The name of the project.
            status (str): The new status for the project.
            user_id (str): The ID of the user attempting to update the project.
            
        Returns:
            str: Success or error message.
        """
        logger.info(f"Attempting to update status of project '{project_name}' to '{status}' by user '{user_id}'.")
        
        if not status or not status.strip():
            logger.warning("Update status failed: Status cannot be empty.")
            return "خطأ: الحالة لا يمكن أن تكون فارغة." # "Error: Status cannot be empty."
        
        # Use database if available, otherwise use in-memory storage
        if self.conn:
            try:
                # Check if project exists and user is the owner
                cursor = self.conn.execute(
                    "SELECT id, owner_id FROM projects WHERE name = ?",
                    (project_name,)
                )
                project = cursor.fetchone()
                
                if not project:
                    logger.warning(f"Update status failed: Project '{project_name}' not found.")
                    return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."
                
                project_id, owner_id = project
                
                if owner_id != user_id:
                    logger.warning(f"Update status failed: User '{user_id}' is not the owner of project '{project_name}'.")
                    return f"خطأ: لا يمكنك تحديث هذا المشروع لأنك لست المالك." # "Error: You cannot update this project as you are not the owner."
                
                # Update the project status
                now = datetime.datetime.now().isoformat()
                with self.conn:
                    self.conn.execute(
                        "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
                        (status, now, project_id)
                    )
                
                logger.info(f"Status of project '{project_name}' updated to '{status}' successfully.")
                return f"تم تحديث حالة المشروع '{project_name}' إلى '{status}' بنجاح." # "Project '{project_name}' status updated to '{status}' successfully."
            except sqlite3.Error as e:
                logger.error(f"SQLite error during status update: {e}")
                return f"خطأ في قاعدة البيانات: {e}" # "Database error: {e}"
        else:
            # Fallback to in-memory storage
            if project_name not in self.projects:
                logger.warning(f"Update status failed: Project '{project_name}' not found in memory.")
                return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."
            
            if self.projects[project_name]["owner"] != user_id:
                logger.warning(f"Update status failed: User '{user_id}' is not the owner of project '{project_name}'.")
                return f"خطأ: لا يمكنك تحديث هذا المشروع لأنك لست المالك." # "Error: You cannot update this project as you are not the owner."
            
            now = datetime.datetime.now().isoformat()
            self.projects[project_name]["status"] = status
            self.projects[project_name]["updated_at"] = now
            
            logger.info(f"Status of project '{project_name}' updated to '{status}' successfully in memory.")
            return f"تم تحديث حالة المشروع '{project_name}' إلى '{status}' بنجاح." # "Project '{project_name}' status updated to '{status}' successfully."

    def update_task_status(self, project_name: str, task_id: Union[int, str], status: str, user_id: str) -> str:
        """
        Updates the status of a task.
        
        Args:
            project_name (str): The name of the project containing the task.
            task_id (int or str): The ID of the task to update.
            status (str): The new status for the task.
            user_id (str): The ID of the user attempting to update the task.
            
        Returns:
            str: Success or error message.
        """
        logger.info(f"Attempting to update status of task '{task_id}' in project '{project_name}' to '{status}' by user '{user_id}'.")
        
        if not status or not status.strip():
            logger.warning("Update task status failed: Status cannot be empty.")
            return "خطأ: الحالة لا يمكن أن تكون فارغة." # "Error: Status cannot be empty."
        
        # Use database if available, otherwise use in-memory storage
        if self.conn:
            try:
                # Check if project exists and user is the owner
                cursor = self.conn.execute(
                    "SELECT id, owner_id FROM projects WHERE name = ?",
                    (project_name,)
                )
                project = cursor.fetchone()
                
                if not project:
                    logger.warning(f"Update task status failed: Project '{project_name}' not found.")
                    return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."
                
                project_id, owner_id = project
                
                if owner_id != user_id:
                    logger.warning(f"Update task status failed: User '{user_id}' is not the owner of project '{project_name}'.")
                    return f"خطأ: لا يمكنك تحديث هذه المهمة لأنك لست مالك المشروع." # "Error: You cannot update this task as you are not the project owner."
                
                # Check if task exists
                cursor = self.conn.execute(
                    "SELECT id FROM tasks WHERE id = ? AND project_id = ?",
                    (task_id, project_id)
                )
                task = cursor.fetchone()
                
                if not task:
                    logger.warning(f"Update task status failed: Task '{task_id}' not found in project '{project_name}'.")
                    return f"خطأ: المهمة '{task_id}' غير موجودة في المشروع '{project_name}'." # "Error: Task '{task_id}' not found in project '{project_name}'."
                
                # Update the task status
                now = datetime.datetime.now().isoformat()
                with self.conn:
                    self.conn.execute(
                        "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                        (status, now, task_id)
                    )
                    # Also update the project's updated_at timestamp
                    self.conn.execute(
                        "UPDATE projects SET updated_at = ? WHERE id = ?",
                        (now, project_id)
                    )
                
                logger.info(f"Status of task '{task_id}' in project '{project_name}' updated to '{status}' successfully.")
                return f"تم تحديث حالة المهمة '{task_id}' في المشروع '{project_name}' إلى '{status}' بنجاح." # "Task '{task_id}' status in project '{project_name}' updated to '{status}' successfully."
            except sqlite3.Error as e:
                logger.error(f"SQLite error during task status update: {e}")
                return f"خطأ في قاعدة البيانات: {e}" # "Database error: {e}"
        else:
            # Fallback to in-memory storage
            if project_name not in self.projects:
                logger.warning(f"Update task status failed: Project '{project_name}' not found in memory.")
                return f"خطأ: المشروع '{project_name}' غير موجود." # "Error: Project '{project_name}' not found."
            
            if self.projects[project_name]["owner"] != user_id:
                logger.warning(f"Update task status failed: User '{user_id}' is not the owner of project '{project_name}'.")
                return f"خطأ: لا يمكنك تحديث هذه المهمة لأنك لست مالك المشروع." # "Error: You cannot update this task as you are not the project owner."
            
            # In memory, task_id might be an index
            try:
                task_id_int = int(task_id)
                if task_id_int < 0 or task_id_int >= len(self.projects[project_name]["tasks"]):
                    logger.warning(f"Update task status failed: Task index '{task_id}' out of range for project '{project_name}'.")
                    return f"خطأ: مؤشر المهمة '{task_id}' خارج النطاق للمشروع '{project_name}'." # "Error: Task index '{task_id}' out of range for project '{project_name}'."
                
                now = datetime.datetime.now().isoformat()
                self.projects[project_name]["tasks"][task_id_int]["status"] = status
                self.projects[project_name]["tasks"][task_id_int]["updated_at"] = now
                self.projects[project_name]["updated_at"] = now
                
                logger.info(f"Status of task '{task_id}' in project '{project_name}' updated to '{status}' successfully in memory.")
                return f"تم تحديث حالة المهمة '{task_id}' في المشروع '{project_name}' إلى '{status}' بنجاح." # "Task '{task_id}' status in project '{project_name}' updated to '{status}' successfully."
            except (ValueError, IndexError):
                logger.warning(f"Update task status failed: Invalid task ID '{task_id}' for project '{project_name}'.")
                return f"خطأ: معرف المهمة '{task_id}' غير صالح للمشروع '{project_name}'." # "Error: Invalid task ID '{task_id}' for project '{project_name}'."

    def close(self):
        """Closes the database connection if it exists."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")
            self.conn = None

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