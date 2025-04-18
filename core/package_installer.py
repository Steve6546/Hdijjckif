"""
Package Installer for the All-Agents-App
This module handles the installation of packages for projects.
"""

import os
import logging
import subprocess
import json
import sys
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PackageInstaller:
    """
    Handles the installation of packages for projects.
    Supports Python (pip) and Node.js (npm) packages.
    """
    
    def __init__(self, base_dir: str = "."):
        """
        Initialize the package installer.
        
        Args:
            base_dir: Base directory for installations
        """
        self.base_dir = os.path.abspath(base_dir)
        logger.info(f"PackageInstaller initialized with base directory: {self.base_dir}")
    
    def create_virtual_environment(self, project_dir: str, venv_name: str = "venv") -> Dict[str, Any]:
        """
        Create a Python virtual environment.
        
        Args:
            project_dir: Project directory
            venv_name: Name of the virtual environment
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Ensure project directory exists
            project_dir = os.path.join(self.base_dir, project_dir)
            os.makedirs(project_dir, exist_ok=True)
            
            # Create virtual environment
            venv_path = os.path.join(project_dir, venv_name)
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
            
            logger.info(f"Created virtual environment at {venv_path}")
            return {
                "status": "success",
                "message": f"Created virtual environment at {venv_path}",
                "venv_path": venv_path
            }
            
        except Exception as e:
            logger.error(f"Error creating virtual environment: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error creating virtual environment: {str(e)}"
            }
    
    def install_python_packages(self, project_dir: str, packages: List[str], venv_name: str = "venv") -> Dict[str, Any]:
        """
        Install Python packages in a virtual environment.
        
        Args:
            project_dir: Project directory
            packages: List of packages to install
            venv_name: Name of the virtual environment
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Ensure project directory exists
            project_dir = os.path.join(self.base_dir, project_dir)
            os.makedirs(project_dir, exist_ok=True)
            
            # Check if virtual environment exists
            venv_path = os.path.join(project_dir, venv_name)
            if not os.path.exists(venv_path):
                # Create virtual environment
                result = self.create_virtual_environment(project_dir, venv_name)
                if result["status"] != "success":
                    return result
            
            # Get path to pip
            if os.name == "nt":  # Windows
                pip_path = os.path.join(venv_path, "Scripts", "pip")
            else:  # Unix/Linux
                pip_path = os.path.join(venv_path, "bin", "pip")
            
            # Install packages
            for package in packages:
                subprocess.run([pip_path, "install", package], check=True)
            
            logger.info(f"Installed Python packages: {', '.join(packages)}")
            return {
                "status": "success",
                "message": f"Installed Python packages: {', '.join(packages)}",
                "packages": packages
            }
            
        except Exception as e:
            logger.error(f"Error installing Python packages: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error installing Python packages: {str(e)}"
            }
    
    def install_from_requirements(self, project_dir: str, requirements_file: str = "requirements.txt", venv_name: str = "venv") -> Dict[str, Any]:
        """
        Install Python packages from a requirements file.
        
        Args:
            project_dir: Project directory
            requirements_file: Path to requirements file (relative to project directory)
            venv_name: Name of the virtual environment
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Ensure project directory exists
            project_dir = os.path.join(self.base_dir, project_dir)
            os.makedirs(project_dir, exist_ok=True)
            
            # Check if requirements file exists
            requirements_path = os.path.join(project_dir, requirements_file)
            if not os.path.exists(requirements_path):
                logger.error(f"Requirements file not found: {requirements_path}")
                return {
                    "status": "error",
                    "message": f"Requirements file not found: {requirements_path}"
                }
            
            # Check if virtual environment exists
            venv_path = os.path.join(project_dir, venv_name)
            if not os.path.exists(venv_path):
                # Create virtual environment
                result = self.create_virtual_environment(project_dir, venv_name)
                if result["status"] != "success":
                    return result
            
            # Get path to pip
            if os.name == "nt":  # Windows
                pip_path = os.path.join(venv_path, "Scripts", "pip")
            else:  # Unix/Linux
                pip_path = os.path.join(venv_path, "bin", "pip")
            
            # Install packages from requirements file
            subprocess.run([pip_path, "install", "-r", requirements_path], check=True)
            
            logger.info(f"Installed Python packages from {requirements_path}")
            return {
                "status": "success",
                "message": f"Installed Python packages from {requirements_path}"
            }
            
        except Exception as e:
            logger.error(f"Error installing from requirements: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error installing from requirements: {str(e)}"
            }
    
    def install_node_packages(self, project_dir: str, packages: List[str], dev: bool = False) -> Dict[str, Any]:
        """
        Install Node.js packages.
        
        Args:
            project_dir: Project directory
            packages: List of packages to install
            dev: Whether to install as dev dependencies
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Ensure project directory exists
            project_dir = os.path.join(self.base_dir, project_dir)
            os.makedirs(project_dir, exist_ok=True)
            
            # Check if package.json exists
            package_json_path = os.path.join(project_dir, "package.json")
            if not os.path.exists(package_json_path):
                # Create a basic package.json
                subprocess.run(["npm", "init", "-y"], cwd=project_dir, check=True)
            
            # Install packages
            cmd = ["npm", "install"]
            if dev:
                cmd.append("--save-dev")
            cmd.extend(packages)
            
            subprocess.run(cmd, cwd=project_dir, check=True)
            
            logger.info(f"Installed Node.js packages: {', '.join(packages)}")
            return {
                "status": "success",
                "message": f"Installed Node.js packages: {', '.join(packages)}",
                "packages": packages
            }
            
        except Exception as e:
            logger.error(f"Error installing Node.js packages: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error installing Node.js packages: {str(e)}"
            }
    
    def install_from_package_json(self, project_dir: str) -> Dict[str, Any]:
        """
        Install Node.js packages from package.json.
        
        Args:
            project_dir: Project directory
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Ensure project directory exists
            project_dir = os.path.join(self.base_dir, project_dir)
            os.makedirs(project_dir, exist_ok=True)
            
            # Check if package.json exists
            package_json_path = os.path.join(project_dir, "package.json")
            if not os.path.exists(package_json_path):
                logger.error(f"package.json not found: {package_json_path}")
                return {
                    "status": "error",
                    "message": f"package.json not found: {package_json_path}"
                }
            
            # Install packages from package.json
            subprocess.run(["npm", "install"], cwd=project_dir, check=True)
            
            logger.info(f"Installed Node.js packages from {package_json_path}")
            return {
                "status": "success",
                "message": f"Installed Node.js packages from {package_json_path}"
            }
            
        except Exception as e:
            logger.error(f"Error installing from package.json: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error installing from package.json: {str(e)}"
            }
    
    def detect_and_install_dependencies(self, project_dir: str) -> Dict[str, Any]:
        """
        Detect and install dependencies for a project.
        
        Args:
            project_dir: Project directory
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Ensure project directory exists
            project_dir = os.path.join(self.base_dir, project_dir)
            os.makedirs(project_dir, exist_ok=True)
            
            results = []
            
            # Check for Python dependencies
            requirements_path = os.path.join(project_dir, "requirements.txt")
            if os.path.exists(requirements_path):
                result = self.install_from_requirements(project_dir)
                results.append(result)
            
            # Check for Node.js dependencies
            package_json_path = os.path.join(project_dir, "package.json")
            if os.path.exists(package_json_path):
                result = self.install_from_package_json(project_dir)
                results.append(result)
            
            if not results:
                logger.warning(f"No dependency files found in {project_dir}")
                return {
                    "status": "warning",
                    "message": f"No dependency files found in {project_dir}"
                }
            
            # Check if any installations failed
            if any(result["status"] == "error" for result in results):
                return {
                    "status": "error",
                    "message": "Some dependencies failed to install",
                    "results": results
                }
            
            logger.info(f"Successfully installed all dependencies for {project_dir}")
            return {
                "status": "success",
                "message": f"Successfully installed all dependencies for {project_dir}",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error detecting and installing dependencies: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error detecting and installing dependencies: {str(e)}"
            }