"""
Project Orchestrator for the All-Agents-App
This module coordinates the creation and management of projects.
"""

import os
import logging
import json
import shutil
import subprocess
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectOrchestrator:
    """
    Coordinates the creation and management of projects.
    Acts as the central brain for project generation.
    """
    
    def __init__(self, ai_agent=None, base_dir: str = "runtime/generated_projects"):
        """
        Initialize the project orchestrator.
        
        Args:
            ai_agent: AI agent for generating code and content
            base_dir: Base directory for generated projects
        """
        self.ai_agent = ai_agent
        self.base_dir = os.path.abspath(base_dir)
        
        # Ensure the base directory exists
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"ProjectOrchestrator initialized with base directory: {self.base_dir}")
        
        # Dictionary to store active projects
        self.active_projects = {}
    
    def create_project(self, project_name: str, project_type: str, description: str) -> Dict[str, Any]:
        """
        Create a new project.
        
        Args:
            project_name: Name of the project
            project_type: Type of project (e.g., web, api, mobile)
            description: Description of the project
            
        Returns:
            Dict containing project information
        """
        # Generate a unique project ID
        project_id = str(uuid.uuid4())[:8]
        
        # Create a sanitized project name for the directory
        sanitized_name = "".join(c if c.isalnum() else "_" for c in project_name)
        project_dir = os.path.join(self.base_dir, f"{sanitized_name}_{project_id}")
        
        # Create the project directory
        os.makedirs(project_dir, exist_ok=True)
        
        # Create project metadata
        project_metadata = {
            "id": project_id,
            "name": project_name,
            "type": project_type,
            "description": description,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "directory": project_dir,
            "status": "created"
        }
        
        # Save project metadata
        with open(os.path.join(project_dir, "project.json"), "w") as f:
            json.dump(project_metadata, f, indent=2)
        
        # Add to active projects
        self.active_projects[project_id] = project_metadata
        
        logger.info(f"Created project '{project_name}' with ID {project_id} in {project_dir}")
        return project_metadata
    
    def generate_project_structure(self, project_id: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the project structure based on the provided structure definition.
        
        Args:
            project_id: ID of the project
            structure: Dictionary defining the project structure
            
        Returns:
            Dict containing the result of the operation
        """
        if project_id not in self.active_projects:
            logger.error(f"Project with ID {project_id} not found")
            return {"status": "error", "message": f"Project with ID {project_id} not found"}
        
        project = self.active_projects[project_id]
        project_dir = project["directory"]
        
        try:
            # Create directories
            for directory in structure.get("directories", []):
                dir_path = os.path.join(project_dir, directory)
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            
            # Create files
            for file_info in structure.get("files", []):
                file_path = os.path.join(project_dir, file_info["path"])
                
                # Ensure the parent directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Write the file content
                with open(file_path, "w") as f:
                    f.write(file_info["content"])
                
                logger.info(f"Created file: {file_path}")
            
            # Update project status
            project["status"] = "structure_generated"
            
            # Save updated project metadata
            with open(os.path.join(project_dir, "project.json"), "w") as f:
                json.dump(project, f, indent=2)
            
            return {"status": "success", "message": f"Project structure generated for {project['name']}"}
            
        except Exception as e:
            logger.error(f"Error generating project structure: {e}", exc_info=True)
            return {"status": "error", "message": f"Error generating project structure: {str(e)}"}
    
    def install_dependencies(self, project_id: str, package_manager: str = "pip") -> Dict[str, Any]:
        """
        Install dependencies for the project.
        
        Args:
            project_id: ID of the project
            package_manager: Package manager to use (pip, npm, etc.)
            
        Returns:
            Dict containing the result of the operation
        """
        if project_id not in self.active_projects:
            logger.error(f"Project with ID {project_id} not found")
            return {"status": "error", "message": f"Project with ID {project_id} not found"}
        
        project = self.active_projects[project_id]
        project_dir = project["directory"]
        
        try:
            # Check for requirements file based on package manager
            if package_manager == "pip":
                req_file = os.path.join(project_dir, "requirements.txt")
                if os.path.exists(req_file):
                    # Create a virtual environment
                    venv_dir = os.path.join(project_dir, "venv")
                    subprocess.run(["python", "-m", "venv", venv_dir], check=True)
                    
                    # Install dependencies
                    if os.name == "nt":  # Windows
                        pip_path = os.path.join(venv_dir, "Scripts", "pip")
                    else:  # Unix/Linux
                        pip_path = os.path.join(venv_dir, "bin", "pip")
                    
                    subprocess.run([pip_path, "install", "-r", req_file], check=True)
                    logger.info(f"Installed Python dependencies for project {project_id}")
                else:
                    logger.warning(f"No requirements.txt found for project {project_id}")
            
            elif package_manager == "npm":
                package_file = os.path.join(project_dir, "package.json")
                if os.path.exists(package_file):
                    # Install dependencies
                    subprocess.run(["npm", "install"], cwd=project_dir, check=True)
                    logger.info(f"Installed Node.js dependencies for project {project_id}")
                else:
                    logger.warning(f"No package.json found for project {project_id}")
            
            # Update project status
            project["status"] = "dependencies_installed"
            
            # Save updated project metadata
            with open(os.path.join(project_dir, "project.json"), "w") as f:
                json.dump(project, f, indent=2)
            
            return {"status": "success", "message": f"Dependencies installed for {project['name']}"}
            
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}", exc_info=True)
            return {"status": "error", "message": f"Error installing dependencies: {str(e)}"}
    
    def run_project(self, project_id: str, command: str = None) -> Dict[str, Any]:
        """
        Run the project.
        
        Args:
            project_id: ID of the project
            command: Command to run the project (if None, will try to determine automatically)
            
        Returns:
            Dict containing the result of the operation
        """
        if project_id not in self.active_projects:
            logger.error(f"Project with ID {project_id} not found")
            return {"status": "error", "message": f"Project with ID {project_id} not found"}
        
        project = self.active_projects[project_id]
        project_dir = project["directory"]
        
        try:
            # If no command provided, try to determine automatically
            if not command:
                # Check for common run scripts
                if os.path.exists(os.path.join(project_dir, "run.sh")):
                    command = "sh run.sh"
                elif os.path.exists(os.path.join(project_dir, "app.py")):
                    # Use the virtual environment if it exists
                    venv_dir = os.path.join(project_dir, "venv")
                    if os.path.exists(venv_dir):
                        if os.name == "nt":  # Windows
                            python_path = os.path.join(venv_dir, "Scripts", "python")
                        else:  # Unix/Linux
                            python_path = os.path.join(venv_dir, "bin", "python")
                        command = f"{python_path} app.py"
                    else:
                        command = "python app.py"
                elif os.path.exists(os.path.join(project_dir, "package.json")):
                    # Check if there's a start script in package.json
                    with open(os.path.join(project_dir, "package.json"), "r") as f:
                        package_json = json.load(f)
                    
                    if "scripts" in package_json and "start" in package_json["scripts"]:
                        command = "npm start"
                    else:
                        command = "npm run dev"
            
            if not command:
                logger.error(f"Could not determine how to run project {project_id}")
                return {"status": "error", "message": "Could not determine how to run project"}
            
            # Run the command
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Update project status
            project["status"] = "running"
            project["process_id"] = process.pid
            
            # Save updated project metadata
            with open(os.path.join(project_dir, "project.json"), "w") as f:
                json.dump(project, f, indent=2)
            
            # Wait a bit to check if the process is still running
            time.sleep(2)
            if process.poll() is not None:
                # Process has already terminated
                stdout, stderr = process.communicate()
                logger.error(f"Process terminated with exit code {process.returncode}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                
                project["status"] = "error"
                
                # Save updated project metadata
                with open(os.path.join(project_dir, "project.json"), "w") as f:
                    json.dump(project, f, indent=2)
                
                return {
                    "status": "error",
                    "message": f"Process terminated with exit code {process.returncode}",
                    "stdout": stdout,
                    "stderr": stderr
                }
            
            logger.info(f"Started project {project_id} with command: {command}")
            return {
                "status": "success",
                "message": f"Project {project['name']} is running",
                "process_id": process.pid,
                "command": command
            }
            
        except Exception as e:
            logger.error(f"Error running project: {e}", exc_info=True)
            return {"status": "error", "message": f"Error running project: {str(e)}"}
    
    def stop_project(self, project_id: str) -> Dict[str, Any]:
        """
        Stop a running project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dict containing the result of the operation
        """
        if project_id not in self.active_projects:
            logger.error(f"Project with ID {project_id} not found")
            return {"status": "error", "message": f"Project with ID {project_id} not found"}
        
        project = self.active_projects[project_id]
        
        if "process_id" not in project:
            logger.warning(f"No process ID found for project {project_id}")
            return {"status": "warning", "message": "No process ID found for project"}
        
        try:
            # Try to terminate the process
            process_id = project["process_id"]
            
            if os.name == "nt":  # Windows
                subprocess.run(["taskkill", "/F", "/PID", str(process_id)], check=False)
            else:  # Unix/Linux
                subprocess.run(["kill", str(process_id)], check=False)
            
            # Update project status
            project["status"] = "stopped"
            del project["process_id"]
            
            # Save updated project metadata
            with open(os.path.join(project["directory"], "project.json"), "w") as f:
                json.dump(project, f, indent=2)
            
            logger.info(f"Stopped project {project_id}")
            return {"status": "success", "message": f"Project {project['name']} stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping project: {e}", exc_info=True)
            return {"status": "error", "message": f"Error stopping project: {str(e)}"}
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """
        Delete a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dict containing the result of the operation
        """
        if project_id not in self.active_projects:
            logger.error(f"Project with ID {project_id} not found")
            return {"status": "error", "message": f"Project with ID {project_id} not found"}
        
        project = self.active_projects[project_id]
        project_dir = project["directory"]
        
        try:
            # Stop the project if it's running
            if project.get("status") == "running" and "process_id" in project:
                self.stop_project(project_id)
            
            # Delete the project directory
            shutil.rmtree(project_dir)
            
            # Remove from active projects
            del self.active_projects[project_id]
            
            logger.info(f"Deleted project {project_id}")
            return {"status": "success", "message": f"Project {project['name']} deleted"}
            
        except Exception as e:
            logger.error(f"Error deleting project: {e}", exc_info=True)
            return {"status": "error", "message": f"Error deleting project: {str(e)}"}
    
    def get_project_info(self, project_id: str) -> Dict[str, Any]:
        """
        Get information about a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dict containing project information
        """
        if project_id not in self.active_projects:
            logger.error(f"Project with ID {project_id} not found")
            return {"status": "error", "message": f"Project with ID {project_id} not found"}
        
        return self.active_projects[project_id]
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all active projects.
        
        Returns:
            List of project information dictionaries
        """
        return list(self.active_projects.values())
    
    def generate_project_from_description(self, description: str) -> Dict[str, Any]:
        """
        Generate a complete project from a description using AI.
        
        Args:
            description: Description of the project
            
        Returns:
            Dict containing the result of the operation
        """
        if not self.ai_agent:
            logger.error("No AI agent provided for project generation")
            return {"status": "error", "message": "No AI agent provided for project generation"}
        
        try:
            # Extract project name and type from description
            project_name_prompt = f"Extract a short project name from this description: {description}"
            project_name = self.ai_agent.generate(project_name_prompt).strip()
            
            project_type_prompt = f"What type of project is this (web, api, mobile, etc.)? Description: {description}"
            project_type = self.ai_agent.generate(project_type_prompt).strip()
            
            # Create the project
            project = self.create_project(project_name, project_type, description)
            project_id = project["id"]
            
            # Generate project structure
            structure_prompt = f"""
            Generate a complete project structure for the following project:
            
            Name: {project_name}
            Type: {project_type}
            Description: {description}
            
            Return a JSON object with the following structure:
            {{
                "directories": ["list", "of", "directories"],
                "files": [
                    {{
                        "path": "path/to/file.ext",
                        "content": "content of the file"
                    }}
                ]
            }}
            
            Include all necessary files for a complete, working project.
            """
            
            structure_json = self.ai_agent.generate(structure_prompt)
            
            # Parse the JSON structure
            try:
                # Extract JSON from the response (in case there's additional text)
                import re
                json_match = re.search(r'```json\n(.*?)\n```', structure_json, re.DOTALL)
                if json_match:
                    structure_json = json_match.group(1)
                else:
                    # Try to find JSON object directly
                    json_match = re.search(r'({.*})', structure_json, re.DOTALL)
                    if json_match:
                        structure_json = json_match.group(1)
                
                structure = json.loads(structure_json)
            except Exception as e:
                logger.error(f"Error parsing structure JSON: {e}", exc_info=True)
                # Fallback to a basic structure
                structure = {
                    "directories": ["src", "tests", "docs"],
                    "files": [
                        {
                            "path": "README.md",
                            "content": f"# {project_name}\n\n{description}"
                        }
                    ]
                }
            
            # Generate the project structure
            self.generate_project_structure(project_id, structure)
            
            # Determine if we need to install dependencies
            has_requirements = any(f["path"] == "requirements.txt" for f in structure.get("files", []))
            has_package_json = any(f["path"] == "package.json" for f in structure.get("files", []))
            
            if has_requirements:
                self.install_dependencies(project_id, "pip")
            
            if has_package_json:
                self.install_dependencies(project_id, "npm")
            
            # Update project status
            project = self.active_projects[project_id]
            project["status"] = "generated"
            
            # Save updated project metadata
            with open(os.path.join(project["directory"], "project.json"), "w") as f:
                json.dump(project, f, indent=2)
            
            logger.info(f"Generated project {project_id} from description")
            return {
                "status": "success",
                "message": f"Project {project_name} generated successfully",
                "project": project
            }
            
        except Exception as e:
            logger.error(f"Error generating project from description: {e}", exc_info=True)
            return {"status": "error", "message": f"Error generating project from description: {str(e)}"}