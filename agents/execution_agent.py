"""
Execution Agent for the All-Agents-App
This agent is responsible for executing commands and running code.
"""

import os
import logging
import subprocess
import tempfile
import time
import json
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExecutionAgent:
    """
    Agent responsible for executing commands and running code.
    Provides a secure environment for code execution.
    """
    
    def __init__(self, workspace_dir: str = "runtime/temp"):
        """
        Initialize the execution agent.
        
        Args:
            workspace_dir: Directory for temporary files and execution
        """
        self.workspace_dir = os.path.abspath(workspace_dir)
        os.makedirs(self.workspace_dir, exist_ok=True)
        logger.info(f"ExecutionAgent initialized with workspace directory: {self.workspace_dir}")
        
        # Dictionary to store running processes
        self.running_processes = {}
    
    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a shell command.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Create a temporary directory for execution
            with tempfile.TemporaryDirectory(dir=self.workspace_dir) as temp_dir:
                logger.info(f"Executing command: {command}")
                
                # Run the command
                process = subprocess.run(
                    command,
                    shell=True,
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout
                )
                
                return {
                    "status": "success" if process.returncode == 0 else "error",
                    "returncode": process.returncode,
                    "stdout": process.stdout,
                    "stderr": process.stderr
                }
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout} seconds: {command}")
            return {
                "status": "error",
                "message": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Error executing command: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error executing command: {str(e)}"
            }
    
    def execute_python_code(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute Python code.
        
        Args:
            code: Python code to execute
            timeout: Timeout in seconds
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Create a temporary directory for execution
            with tempfile.TemporaryDirectory(dir=self.workspace_dir) as temp_dir:
                # Create a Python file
                script_path = os.path.join(temp_dir, "script.py")
                with open(script_path, "w") as f:
                    f.write(code)
                
                logger.info(f"Executing Python code from {script_path}")
                
                # Run the Python script
                process = subprocess.run(
                    ["python", script_path],
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout
                )
                
                return {
                    "status": "success" if process.returncode == 0 else "error",
                    "returncode": process.returncode,
                    "stdout": process.stdout,
                    "stderr": process.stderr
                }
        except subprocess.TimeoutExpired:
            logger.error(f"Python code execution timed out after {timeout} seconds")
            return {
                "status": "error",
                "message": f"Python code execution timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Error executing Python code: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error executing Python code: {str(e)}"
            }
    
    def execute_javascript_code(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute JavaScript code using Node.js.
        
        Args:
            code: JavaScript code to execute
            timeout: Timeout in seconds
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Create a temporary directory for execution
            with tempfile.TemporaryDirectory(dir=self.workspace_dir) as temp_dir:
                # Create a JavaScript file
                script_path = os.path.join(temp_dir, "script.js")
                with open(script_path, "w") as f:
                    f.write(code)
                
                logger.info(f"Executing JavaScript code from {script_path}")
                
                # Run the JavaScript script
                process = subprocess.run(
                    ["node", script_path],
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout
                )
                
                return {
                    "status": "success" if process.returncode == 0 else "error",
                    "returncode": process.returncode,
                    "stdout": process.stdout,
                    "stderr": process.stderr
                }
        except subprocess.TimeoutExpired:
            logger.error(f"JavaScript code execution timed out after {timeout} seconds")
            return {
                "status": "error",
                "message": f"JavaScript code execution timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Error executing JavaScript code: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error executing JavaScript code: {str(e)}"
            }
    
    def start_process(self, command: str, cwd: str = None) -> Dict[str, Any]:
        """
        Start a long-running process.
        
        Args:
            command: Command to execute
            cwd: Working directory
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Use the provided working directory or create a temporary one
            if cwd is None:
                cwd = tempfile.mkdtemp(dir=self.workspace_dir)
            else:
                os.makedirs(cwd, exist_ok=True)
            
            logger.info(f"Starting process: {command}")
            
            # Start the process
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Generate a process ID
            process_id = str(int(time.time()))
            
            # Store the process
            self.running_processes[process_id] = {
                "process": process,
                "command": command,
                "cwd": cwd,
                "start_time": time.time()
            }
            
            logger.info(f"Started process with ID {process_id}")
            return {
                "status": "success",
                "message": f"Process started with ID {process_id}",
                "process_id": process_id
            }
        except Exception as e:
            logger.error(f"Error starting process: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error starting process: {str(e)}"
            }
    
    def stop_process(self, process_id: str) -> Dict[str, Any]:
        """
        Stop a running process.
        
        Args:
            process_id: ID of the process to stop
            
        Returns:
            Dict containing the result of the operation
        """
        if process_id not in self.running_processes:
            logger.warning(f"Process with ID {process_id} not found")
            return {
                "status": "error",
                "message": f"Process with ID {process_id} not found"
            }
        
        try:
            # Get the process
            process_info = self.running_processes[process_id]
            process = process_info["process"]
            
            # Terminate the process
            process.terminate()
            
            # Wait for the process to terminate
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Process didn't terminate within timeout, kill it
                process.kill()
                process.wait()
            
            # Get the output
            stdout, stderr = process.communicate()
            
            # Remove from running processes
            del self.running_processes[process_id]
            
            logger.info(f"Stopped process with ID {process_id}")
            return {
                "status": "success",
                "message": f"Process with ID {process_id} stopped",
                "returncode": process.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
        except Exception as e:
            logger.error(f"Error stopping process: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error stopping process: {str(e)}"
            }
    
    def get_process_status(self, process_id: str) -> Dict[str, Any]:
        """
        Get the status of a running process.
        
        Args:
            process_id: ID of the process
            
        Returns:
            Dict containing the status of the process
        """
        if process_id not in self.running_processes:
            logger.warning(f"Process with ID {process_id} not found")
            return {
                "status": "error",
                "message": f"Process with ID {process_id} not found"
            }
        
        try:
            # Get the process
            process_info = self.running_processes[process_id]
            process = process_info["process"]
            
            # Check if the process is still running
            if process.poll() is None:
                # Process is still running
                return {
                    "status": "success",
                    "process_status": "running",
                    "command": process_info["command"],
                    "cwd": process_info["cwd"],
                    "start_time": process_info["start_time"],
                    "elapsed_time": time.time() - process_info["start_time"]
                }
            else:
                # Process has terminated
                stdout, stderr = process.communicate()
                
                # Remove from running processes
                del self.running_processes[process_id]
                
                return {
                    "status": "success",
                    "process_status": "terminated",
                    "command": process_info["command"],
                    "cwd": process_info["cwd"],
                    "start_time": process_info["start_time"],
                    "elapsed_time": time.time() - process_info["start_time"],
                    "returncode": process.returncode,
                    "stdout": stdout,
                    "stderr": stderr
                }
        except Exception as e:
            logger.error(f"Error getting process status: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error getting process status: {str(e)}"
            }
    
    def list_processes(self) -> Dict[str, Any]:
        """
        List all running processes.
        
        Returns:
            Dict containing the list of running processes
        """
        try:
            processes = {}
            
            # Check each process
            for process_id, process_info in list(self.running_processes.items()):
                process = process_info["process"]
                
                # Check if the process is still running
                if process.poll() is None:
                    # Process is still running
                    processes[process_id] = {
                        "status": "running",
                        "command": process_info["command"],
                        "cwd": process_info["cwd"],
                        "start_time": process_info["start_time"],
                        "elapsed_time": time.time() - process_info["start_time"]
                    }
                else:
                    # Process has terminated
                    stdout, stderr = process.communicate()
                    
                    # Remove from running processes
                    del self.running_processes[process_id]
                    
                    processes[process_id] = {
                        "status": "terminated",
                        "command": process_info["command"],
                        "cwd": process_info["cwd"],
                        "start_time": process_info["start_time"],
                        "elapsed_time": time.time() - process_info["start_time"],
                        "returncode": process.returncode,
                        "stdout": stdout,
                        "stderr": stderr
                    }
            
            return {
                "status": "success",
                "processes": processes
            }
        except Exception as e:
            logger.error(f"Error listing processes: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error listing processes: {str(e)}"
            }
    
    def cleanup(self):
        """
        Stop all running processes and clean up.
        """
        for process_id in list(self.running_processes.keys()):
            self.stop_process(process_id)
        
        logger.info("All processes stopped")