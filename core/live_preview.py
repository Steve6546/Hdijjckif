"""
Live Preview for the All-Agents-App
This module handles the live preview of projects.
"""

import os
import logging
import subprocess
import time
import json
import socket
import threading
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LivePreview:
    """
    Handles the live preview of projects.
    Supports running web servers and displaying the output.
    """
    
    def __init__(self, base_dir: str = "."):
        """
        Initialize the live preview.
        
        Args:
            base_dir: Base directory for projects
        """
        self.base_dir = os.path.abspath(base_dir)
        logger.info(f"LivePreview initialized with base directory: {self.base_dir}")
        
        # Dictionary to store running processes
        self.running_processes = {}
        
        # Dictionary to store server information
        self.servers = {}
    
    def find_free_port(self, start_port: int = 8000, end_port: int = 9000) -> int:
        """
        Find a free port in the given range.
        
        Args:
            start_port: Start of port range
            end_port: End of port range
            
        Returns:
            Free port number
        """
        for port in range(start_port, end_port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        
        raise RuntimeError(f"No free ports found in range {start_port}-{end_port}")
    
    def start_server(self, project_id: str, project_dir: str, server_type: str = "auto", port: int = None) -> Dict[str, Any]:
        """
        Start a server for the project.
        
        Args:
            project_id: ID of the project
            project_dir: Directory of the project
            server_type: Type of server to start (auto, python, node, etc.)
            port: Port to use (if None, will find a free port)
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Ensure project directory exists
            project_dir = os.path.join(self.base_dir, project_dir)
            if not os.path.exists(project_dir):
                logger.error(f"Project directory not found: {project_dir}")
                return {
                    "status": "error",
                    "message": f"Project directory not found: {project_dir}"
                }
            
            # Find a free port if not specified
            if port is None:
                port = self.find_free_port()
            
            # Determine server type if auto
            if server_type == "auto":
                if os.path.exists(os.path.join(project_dir, "app.py")):
                    server_type = "python"
                elif os.path.exists(os.path.join(project_dir, "package.json")):
                    server_type = "node"
                else:
                    logger.error(f"Could not determine server type for {project_dir}")
                    return {
                        "status": "error",
                        "message": f"Could not determine server type for {project_dir}"
                    }
            
            # Start the server based on type
            if server_type == "python":
                # Check if there's a virtual environment
                venv_path = os.path.join(project_dir, "venv")
                if os.path.exists(venv_path):
                    if os.name == "nt":  # Windows
                        python_path = os.path.join(venv_path, "Scripts", "python")
                    else:  # Unix/Linux
                        python_path = os.path.join(venv_path, "bin", "python")
                else:
                    python_path = "python"
                
                # Check if it's a Flask app
                if os.path.exists(os.path.join(project_dir, "app.py")):
                    with open(os.path.join(project_dir, "app.py"), "r") as f:
                        content = f.read()
                    
                    if "flask" in content.lower():
                        # It's a Flask app
                        cmd = [python_path, "app.py"]
                        env = os.environ.copy()
                        env["FLASK_APP"] = "app.py"
                        env["FLASK_ENV"] = "development"
                        env["FLASK_RUN_PORT"] = str(port)
                        env["FLASK_RUN_HOST"] = "0.0.0.0"
                    elif "fastapi" in content.lower():
                        # It's a FastAPI app
                        cmd = [python_path, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", str(port)]
                    else:
                        # Generic Python app
                        cmd = [python_path, "app.py", "--port", str(port)]
                else:
                    # Generic Python app
                    cmd = [python_path, "app.py", "--port", str(port)]
            
            elif server_type == "node":
                # Check if there's a start script in package.json
                package_json_path = os.path.join(project_dir, "package.json")
                if os.path.exists(package_json_path):
                    with open(package_json_path, "r") as f:
                        package_json = json.load(f)
                    
                    if "scripts" in package_json and "start" in package_json["scripts"]:
                        cmd = ["npm", "start"]
                    elif "scripts" in package_json and "dev" in package_json["scripts"]:
                        cmd = ["npm", "run", "dev"]
                    else:
                        # Generic Node.js app
                        cmd = ["node", "index.js"]
                else:
                    # Generic Node.js app
                    cmd = ["node", "index.js"]
                
                # Set environment variables for port
                env = os.environ.copy()
                env["PORT"] = str(port)
            
            else:
                logger.error(f"Unsupported server type: {server_type}")
                return {
                    "status": "error",
                    "message": f"Unsupported server type: {server_type}"
                }
            
            # Start the server process
            process = subprocess.Popen(
                cmd,
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env if 'env' in locals() else None
            )
            
            # Store the process
            self.running_processes[project_id] = process
            
            # Store server information
            server_info = {
                "project_id": project_id,
                "project_dir": project_dir,
                "server_type": server_type,
                "port": port,
                "url": f"http://localhost:{port}",
                "process_id": process.pid,
                "start_time": time.time()
            }
            
            self.servers[project_id] = server_info
            
            # Start a thread to monitor the process output
            def monitor_output():
                while process.poll() is None:
                    line = process.stdout.readline()
                    if line:
                        logger.info(f"[{project_id}] {line.strip()}")
                    
                    error_line = process.stderr.readline()
                    if error_line:
                        logger.error(f"[{project_id}] {error_line.strip()}")
                
                # Process has terminated
                stdout, stderr = process.communicate()
                if stdout:
                    logger.info(f"[{project_id}] {stdout}")
                if stderr:
                    logger.error(f"[{project_id}] {stderr}")
                
                logger.info(f"Server for project {project_id} has terminated with exit code {process.returncode}")
                
                # Remove from running processes and servers
                if project_id in self.running_processes:
                    del self.running_processes[project_id]
                if project_id in self.servers:
                    del self.servers[project_id]
            
            # Start the monitoring thread
            threading.Thread(target=monitor_output, daemon=True).start()
            
            # Wait a bit for the server to start
            time.sleep(2)
            
            # Check if the process is still running
            if process.poll() is not None:
                # Process has already terminated
                stdout, stderr = process.communicate()
                logger.error(f"Server for project {project_id} failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                
                # Remove from running processes and servers
                if project_id in self.running_processes:
                    del self.running_processes[project_id]
                if project_id in self.servers:
                    del self.servers[project_id]
                
                return {
                    "status": "error",
                    "message": f"Server failed to start with exit code {process.returncode}",
                    "stdout": stdout,
                    "stderr": stderr
                }
            
            logger.info(f"Started server for project {project_id} on port {port}")
            return {
                "status": "success",
                "message": f"Server started on port {port}",
                "server_info": server_info
            }
            
        except Exception as e:
            logger.error(f"Error starting server: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error starting server: {str(e)}"
            }
    
    def stop_server(self, project_id: str) -> Dict[str, Any]:
        """
        Stop a running server.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dict containing the result of the operation
        """
        if project_id not in self.running_processes:
            logger.warning(f"No running server found for project {project_id}")
            return {
                "status": "warning",
                "message": f"No running server found for project {project_id}"
            }
        
        try:
            # Get the process
            process = self.running_processes[project_id]
            
            # Terminate the process
            process.terminate()
            
            # Wait for the process to terminate
            process.wait(timeout=5)
            
            # Remove from running processes and servers
            del self.running_processes[project_id]
            if project_id in self.servers:
                del self.servers[project_id]
            
            logger.info(f"Stopped server for project {project_id}")
            return {
                "status": "success",
                "message": f"Server for project {project_id} stopped"
            }
            
        except subprocess.TimeoutExpired:
            # Process didn't terminate within timeout, kill it
            process.kill()
            
            # Remove from running processes and servers
            del self.running_processes[project_id]
            if project_id in self.servers:
                del self.servers[project_id]
            
            logger.warning(f"Had to forcefully kill server for project {project_id}")
            return {
                "status": "warning",
                "message": f"Server for project {project_id} forcefully killed"
            }
            
        except Exception as e:
            logger.error(f"Error stopping server: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error stopping server: {str(e)}"
            }
    
    def get_server_info(self, project_id: str) -> Dict[str, Any]:
        """
        Get information about a running server.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dict containing server information
        """
        if project_id not in self.servers:
            logger.warning(f"No server information found for project {project_id}")
            return {
                "status": "warning",
                "message": f"No server information found for project {project_id}"
            }
        
        return {
            "status": "success",
            "server_info": self.servers[project_id]
        }
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """
        List all running servers.
        
        Returns:
            List of server information dictionaries
        """
        return list(self.servers.values())
    
    def cleanup(self):
        """
        Stop all running servers.
        """
        for project_id in list(self.running_processes.keys()):
            self.stop_server(project_id)
        
        logger.info("All servers stopped")