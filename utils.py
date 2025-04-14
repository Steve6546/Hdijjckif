"""
Utility functions for the AI Brain orchestration system.
"""

import base64
import io
from typing import Optional
from PIL import Image
import hashlib
import time

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
    if "API key" in str(error).lower():
        return "Invalid or missing API key. Please check your OpenRouter API key."
    elif "rate limit" in str(error).lower():
        return "Rate limit exceeded. Please try again later."
    elif "timeout" in str(error).lower():
        return "Request timed out. The server might be busy, please try again."
    else:
        return f"An error occurred: {str(error)}"
