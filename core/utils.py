"""
Utility functions for the All-Agents-App
This module provides utility functions used throughout the application.
"""

import os
import logging
import json
import shutil
import subprocess
import time
import uuid
import re
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to ensure it's valid.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
    
    # Ensure the filename is not too long
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized

def create_directory(directory: str) -> bool:
    """
    Create a directory if it doesn't exist.
    
    Args:
        directory: The directory to create
        
    Returns:
        True if the directory was created or already exists, False otherwise
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        return False

def write_file(file_path: str, content: str) -> bool:
    """
    Write content to a file.
    
    Args:
        file_path: The path to the file
        content: The content to write
        
    Returns:
        True if the file was written successfully, False otherwise
    """
    try:
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if directory:
            create_directory(directory)
        
        # Write the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return True
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")
        return False

def read_file(file_path: str) -> Optional[str]:
    """
    Read content from a file.
    
    Args:
        file_path: The path to the file
        
    Returns:
        The file content, or None if the file could not be read
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def delete_file(file_path: str) -> bool:
    """
    Delete a file.
    
    Args:
        file_path: The path to the file
        
    Returns:
        True if the file was deleted successfully, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False

def list_files(directory: str, recursive: bool = False) -> List[str]:
    """
    List files in a directory.
    
    Args:
        directory: The directory to list files from
        recursive: Whether to list files recursively
        
    Returns:
        List of file paths
    """
    try:
        if recursive:
            result = []
            for root, _, files in os.walk(directory):
                for file in files:
                    result.append(os.path.join(root, file))
            return result
        else:
            return [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    except Exception as e:
        logger.error(f"Error listing files in {directory}: {e}")
        return []

def run_command(command: List[str], cwd: str = None, env: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Run a command and return the result.
    
    Args:
        command: The command to run
        cwd: The working directory
        env: Environment variables
        
    Returns:
        Dict containing the result of the operation
    """
    try:
        # Run the command
        process = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}: {e}")
        return {
            "status": "error",
            "returncode": e.returncode,
            "stdout": e.stdout,
            "stderr": e.stderr,
            "message": f"Command failed with return code {e.returncode}"
        }
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return {
            "status": "error",
            "message": f"Error running command: {str(e)}"
        }

def generate_id() -> str:
    """
    Generate a unique ID.
    
    Returns:
        Unique ID
    """
    return str(uuid.uuid4())[:8]

def parse_json(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse a JSON string.
    
    Args:
        json_str: The JSON string to parse
        
    Returns:
        Parsed JSON, or None if parsing failed
    """
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}")
        return None

def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON from text.
    
    Args:
        text: The text to extract JSON from
        
    Returns:
        Extracted JSON string, or None if no JSON was found
    """
    try:
        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find JSON object directly
        json_match = re.search(r'({.*})', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        return None
    except Exception as e:
        logger.error(f"Error extracting JSON from text: {e}")
        return None

def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def get_file_size(file_path: str) -> Optional[int]:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: The path to the file
        
    Returns:
        File size in bytes, or None if the file could not be accessed
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {e}")
        return None

def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes to a human-readable string.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        size_kb = size_bytes / 1024
        return f"{size_kb:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.1f} MB"
    else:
        size_gb = size_bytes / (1024 * 1024 * 1024)
        return f"{size_gb:.1f} GB"