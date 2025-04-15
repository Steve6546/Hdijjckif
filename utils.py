"""
Utility functions for the AI Brain orchestration system.
"""

import base64
import io
import os
import uuid
import json
import hashlib
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union
from PIL import Image

# Set up logging
logger = logging.getLogger("brain_utils")
logger.setLevel(logging.INFO)

def encode_image_to_base64(image_path: str) -> str:
    """
    Convert an image file to base64 encoding.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Base64-encoded image string
    """
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def convert_pil_to_base64(pil_image: Image.Image) -> str:
    """
    Convert a PIL Image to base64 encoding.
    
    Args:
        pil_image (PIL.Image): PIL Image object
        
    Returns:
        str: Base64-encoded image string
    """
    buffered = io.BytesIO()
    pil_image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a maximum length with ellipsis.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def generate_session_id() -> str:
    """
    Generate a unique session ID.
    
    Returns:
        str: Unique session ID
    """
    timestamp = str(time.time())
    random_component = str(hash(timestamp))
    session_id = hashlib.md5(f"{timestamp}_{random_component}".encode()).hexdigest()
    return session_id

def format_agent_response(agent_name: str, response: str) -> str:
    """
    Format an agent's response for display.
    
    Args:
        agent_name (str): Name of the agent
        response (str): The agent's response
        
    Returns:
        str: Formatted response string
    """
    return f"### {agent_name}\n{response}"

def get_error_message(error: Exception) -> str:
    """
    Get a user-friendly error message.
    
    Args:
        error (Exception): The exception
        
    Returns:
        str: User-friendly error message
    """
    error_str = str(error).lower()
    if "api key" in error_str:
        return "Invalid or missing API key. Please check your OpenRouter API key."
    elif "rate limit" in error_str:
        return "Rate limit exceeded. Please try again later."
    elif "timeout" in error_str:
        return "Request timed out. The server might be busy, please try again."
    elif "unauthorized" in error_str or "authentication" in error_str:
        return "Authentication failed. Please check your API credentials."
    elif "not found" in error_str or "404" in error_str:
        return "The requested resource was not found. Please check your inputs."
    elif "bad request" in error_str or "400" in error_str:
        return "Invalid request. Please check your input parameters."
    else:
        logger.error(f"Unhandled error: {error_str}")
        return f"An error occurred: {str(error)}"
        
def save_interaction_log(
    session_id: str,
    input_text: str,
    agent_responses: Dict[str, str],
    integrated_response: str,
    image_provided: bool = False,
    processing_time: float = 0.0
) -> None:
    """
    Save interaction details to both file system logs and database.
    
    Args:
        session_id (str): Unique session identifier
        input_text (str): User's input text
        agent_responses (Dict[str, str]): Responses from individual agents
        integrated_response (str): The final integrated response
        image_provided (bool): Whether an image was part of the input
        processing_time (float): Total processing time in seconds
    """
    timestamp = datetime.now().isoformat()
    
    # Save to file system log
    try:
        log_entry = {
            "timestamp": timestamp,
            "session_id": session_id,
            "input": truncate_text(input_text, 500),
            "image_provided": image_provided,
            "agent_count": len(agent_responses),
            "agents_used": list(agent_responses.keys()),
            "response_length": len(integrated_response),
            "processing_time": processing_time
        }
        
        log_file = os.path.join("logs", "interactions.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        # Save detailed agent responses in a separate file
        detailed_log_file = os.path.join("logs", f"session_{session_id}.json")
        detailed_log = {
            "timestamp": timestamp,
            "session_id": session_id,
            "input_text": input_text,
            "image_provided": image_provided,
            "agent_responses": agent_responses,
            "integrated_response": integrated_response,
            "processing_time": processing_time
        }
        
        with open(detailed_log_file, "w") as f:
            json.dump(detailed_log, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to save interaction log to file system: {e}")
    
    # Save to database
    try:
        # Import here to avoid circular imports
        from database import store_interaction
        
        # Get agent models for each agent
        from agents import get_agent_details
        
        agent_models = {}
        for agent_name in agent_responses.keys():
            try:
                agent_details = get_agent_details(agent_name)
                agent_models[agent_name] = agent_details.get("model", "unknown")
            except Exception:
                agent_models[agent_name] = "unknown"
        
        # Store in database
        store_interaction(
            session_id=session_id,
            input_text=input_text,
            agent_responses=agent_responses,
            integrated_response=integrated_response,
            image_provided=image_provided,
            processing_time=processing_time,
            agent_models=agent_models
        )
        
    except Exception as e:
        logger.error(f"Failed to save interaction to database: {e}")
        
def analyze_agent_performance(agent_name: str, response: str) -> Dict[str, Any]:
    """
    Analyze an agent's performance based on response characteristics.
    
    Args:
        agent_name (str): Name of the agent
        response (str): The agent's response
        
    Returns:
        Dict[str, Any]: Performance metrics
    """
    return {
        "agent": agent_name,
        "response_length": len(response),
        "response_paragraphs": response.count("\n\n") + 1,
        "has_code_blocks": "```" in response,
        "has_lists": "- " in response or "* " in response,
        "timestamp": datetime.now().isoformat()
    }

import zipfile

def zip_files(file_paths: List[str], zip_name: str) -> bool:
    """
    Creates a zip archive containing the specified files.

    Args:
        file_paths: A list of paths to the files to be included in the zip.
        zip_name: The desired name (including path) for the output zip file.

    Returns:
        True if the zip file was created successfully, False otherwise.
    """
    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    # Add file to the zip using its base name to avoid including full path structure
                    zipf.write(file_path, os.path.basename(file_path))
                    logger.info(f"Added {file_path} to {zip_name}")
                else:
                    logger.warning(f"File not found, skipping: {file_path}")
        logger.info(f"Successfully created zip file: {zip_name}")
        return True
    except FileNotFoundError as e:
        logger.error(f"Error creating zip file {zip_name}: Input file not found - {e}")
        return False
    except zipfile.BadZipFile as e:
         logger.error(f"Error creating zip file {zip_name}: Bad zip file - {e}")
         return False
    except Exception as e:
        logger.error(f"Error creating zip file {zip_name}: {e}", exc_info=True)
        return False
