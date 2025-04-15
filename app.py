# app.py (Main FastAPI Application - v3.0)
import logging
import os
from datetime import timedelta
from typing import List, Dict, Any

# FastAPI imports
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# Import core components from the project
from ai_agents import MasterAgent # The refactored MasterAgent v3.0
from auth_manager import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_active_admin_user, # Added for admin endpoint
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from cache_manager import CacheManager
from logging_system import Logger as ActivityLogger # Keep using alias
from ai_dev_studio.engine import AIEngine # Import the new AIEngine
from dotenv import load_dotenv # Import dotenv

# --- Basic Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
app_logger = logging.getLogger("app")

# --- Initialization ---
app = FastAPI(
    title="نظام الوكلاء الذكي المتكامل 3.0", # "Integrated Smart Agent System 3.0"
    version="3.0.0"
)

# Initialize core components
try:
    # Load environment variables
    load_dotenv()
    app_logger.info("Environment variables loaded successfully.")

    master = MasterAgent() # Contains logger, AI agent, Project agent
    cache = CacheManager() # Initialize Redis Cache Manager
    ai_engine = AIEngine() # Initialize the AI Engine for Dev Studio
    # Removed old Update/Security agent initializations and threads
    app_logger.info("MasterAgent, CacheManager, and AIEngine initialized successfully.")
except Exception as e:
    app_logger.critical(f"CRITICAL ERROR during initialization: {e}", exc_info=True)
    # Exit if core components fail
    exit(1)

# --- Request Models ---
class QueryInput(BaseModel):
    query: str

class Token(BaseModel):
    access_token: str
    token_type: str

class CodeGenerationInput(BaseModel):
    prompt: str

# --- API Endpoints ---

@app.post("/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Handles user login and returns a JWT access token.
    Uses OAuth2PasswordRequestForm for standard form data input (username, password).
    """
    app_logger.info(f"Login attempt for user: {form_data.username}")
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        app_logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        # Use username from authenticated user dict
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    app_logger.info(f"Login successful for user: {form_data.username}. Token issued.")
    return {"access_token": access_token, "token_type": "bearer"}

# --- AI Dev Studio Endpoints ---

@app.post("/api/studio/generate_code", tags=["AI Dev Studio"])
async def generate_code(
    data: CodeGenerationInput,
    current_user: str = Depends(get_current_user)
):
    """
    Generates a code snippet based on a user prompt using the AIEngine.
    Requires authentication.
    """
    prompt = data.prompt
    app_logger.info(f"Received code generation request from user '{current_user}': '{prompt[:50]}...'")

    try:
        generated_code = ai_engine.generate_code(prompt)
        # Log the activity
        master.logger.log_activity(
            action=f"Code Generation Request by {current_user}: {prompt[:50]}...",
            result=f"Code generated (length: {len(generated_code)} chars)"
        )
        app_logger.info("Code generation successful.")
        return {"generated_code": generated_code}
    except Exception as e:
        app_logger.error(f"Error during code generation for user '{current_user}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Code generation failed: {e}")


@app.post("/api/query", tags=["Agent Interaction"])
async def handle_query(data: QueryInput, current_user: str = Depends(get_current_user)):
    """
    Main endpoint for processing user queries after authentication.
    Integrates caching.
    """
    query = data.query
    app_logger.info(f"Received query from user '{current_user}': '{query}'")

    # --- Caching Logic ---
    cache_key = f"query:{current_user}:{query}" # User-specific cache key
    cached_result = None
    if cache.redis_connection: # Check if cache is available
        cached_result = cache.get(cache_key)

    if cached_result:
        app_logger.info(f"Cache hit for user '{current_user}', query: '{query}'")
        # Log cache hit using the master agent's logger instance
        master.logger.log_activity(action=f"Cache Hit by {current_user}: {query}", result="FROM CACHE")
        # Decode bytes response from cache
        return {"answer": cached_result.decode('utf-8')}
    else:
        app_logger.info(f"Cache miss for user '{current_user}', query: '{query}'. Processing...")
        # If not in cache, process the query via MasterAgent
        # MasterAgent's process_query now handles logging internally
        response = await master.process_query(query, user_id=current_user)

        # Store the result in cache if connection is available
        if cache.redis_connection:
            cache.set(cache_key, response, expire=300) # Cache for 5 minutes

        return {"answer": response}

@app.get("/api/logs", tags=["Admin & Logging"])
async def get_logs(
    # Use the specific admin dependency here
    current_admin_user: str = Depends(get_current_active_admin_user)
):
    """
    Retrieves all activity logs. Requires admin privileges.
    """
    app_logger.info(f"Admin user '{current_admin_user}' requested all activity logs.")
    try:
        # Use the get_all_logs method added to the logger
        logs = master.logger.get_all_logs()
        return logs
    except Exception as e:
        app_logger.error(f"Error retrieving all logs for admin '{current_admin_user}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve activity logs.")

# --- Root Endpoint ---
@app.get("/", tags=["General"])
def read_root():
    """Provides a basic status message."""
    return {"message": "Integrated Smart Agent System v3.0 is running."}

# --- Cleanup ---
@app.on_event("shutdown")
def shutdown_event():
    """Closes the activity logger connection on application shutdown."""
    app_logger.info("Application shutting down...")
    if hasattr(master.logger, 'close'):
        master.logger.close()
        app_logger.info("Activity logger closed.")
    # Add cleanup for other resources if needed (e.g., Redis pool if explicitly managed)

# --- Main Execution ---
if __name__ == "__main__":
    # Load environment variables (e.g., SECRET_KEY, REDIS_HOST) from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        app_logger.info("Attempted to load environment variables from .env file.")
    except ImportError:
        app_logger.warning("python-dotenv not installed, cannot load .env file.")
    except Exception as e:
         app_logger.warning(f"Error loading .env file: {e}")

    # Run the FastAPI app with uvicorn
    # Consider environment variables for host and port as well
    app_host = os.getenv("HOST", "0.0.0.0")
    app_port = int(os.getenv("PORT", 8000))
    app_logger.info(f"Starting Uvicorn server on {app_host}:{app_port}")
    import uvicorn # Import here to avoid making it a top-level requirement if not running directly
    uvicorn.run(app, host=app_host, port=app_port)

# Removed old endpoints: /api/upload, /api/edit_image
# Remove old test code from main block
