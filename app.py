# app.py (Main FastAPI Application - v3.0)
import logging
import os
import io
from datetime import timedelta
from typing import List, Dict, Any, Optional

# FastAPI imports
from fastapi import FastAPI, Request, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize core components
try:
    # Load environment variables
    load_dotenv()
    app_logger.info("Environment variables loaded successfully.")

    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("processed_images", exist_ok=True)
    app_logger.info("Ensured required directories exist.")

    master = MasterAgent() # Contains logger, AI agent, Project agent, Image agent
    cache = CacheManager() # Initialize Redis Cache Manager
    ai_engine = AIEngine() # Initialize the AI Engine for Dev Studio
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

class ImageProcessingInput(BaseModel):
    query: str
    image_path: str

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

@app.post("/api/upload", tags=["File Management"])
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: str = Depends(get_current_user)
):
    """
    Handles multiple file uploads.
    Requires authentication.
    """
    app_logger.info(f"Received file upload request from user '{current_user}': {len(files)} files")
    
    try:
        uploaded_files = []
        for file in files:
            # Create a unique filename to avoid collisions
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{current_user}_{os.urandom(4).hex()}{file_extension}"
            file_path = os.path.join("uploads", unique_filename)
            
            # Save the file
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
            
            uploaded_files.append({
                "original_name": file.filename,
                "saved_as": unique_filename,
                "path": file_path,
                "size": len(contents)
            })
        
        # Log the activity
        master.logger.log_activity(
            action=f"File Upload by {current_user}: {len(files)} files",
            result=f"Files saved: {', '.join([f['original_name'] for f in uploaded_files])}"
        )
        
        app_logger.info(f"Successfully uploaded {len(files)} files for user '{current_user}'")
        return {"message": f"تم تحميل {len(files)} ملفات بنجاح", "files": uploaded_files}
    
    except Exception as e:
        app_logger.error(f"Error during file upload for user '{current_user}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

@app.post("/api/edit_image", tags=["Image Processing"])
async def edit_image(
    file: UploadFile = File(...),
    query: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    """
    Processes an image according to the specified query.
    Requires authentication.
    """
    app_logger.info(f"Received image edit request from user '{current_user}': '{query}'")
    
    try:
        # Read the image file
        image_bytes = await file.read()
        
        # Process the image using the MasterAgent's image processing capability
        result = await master.process_image(query, image_bytes, current_user)
        
        # Check if the result contains an image path or just a message
        if "image_path" in result:
            # Return the processed image
            with open(result["image_path"], "rb") as img_file:
                processed_image = img_file.read()
            
            # Determine content type based on file extension
            file_extension = os.path.splitext(result["image_path"])[1].lower()
            content_type = "image/jpeg"  # Default
            if file_extension == ".png":
                content_type = "image/png"
            elif file_extension == ".gif":
                content_type = "image/gif"
            
            app_logger.info(f"Returning processed image for user '{current_user}'")
            return StreamingResponse(
                io.BytesIO(processed_image),
                media_type=content_type,
                headers={"X-Message": result.get("message", "Image processed successfully")}
            )
        else:
            # Return just the message
            app_logger.info(f"Returning message for user '{current_user}': {result.get('message', 'Unknown error')}")
            return JSONResponse(content=result)
    
    except Exception as e:
        app_logger.error(f"Error during image processing for user '{current_user}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image processing failed: {e}")

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Root Endpoint ---
@app.get("/", tags=["General"], response_class=HTMLResponse)
def read_root():
    """Serves the main HTML page."""
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content

@app.get("/openrouter", tags=["General"], response_class=HTMLResponse)
def openrouter_demo():
    """Serves the OpenRouter demo page."""
    with open("static/openrouter_demo.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content

@app.get("/api/info", tags=["General"])
def get_api_info():
    """Provides a basic status message about the API."""
    return {
        "message": "Integrated Smart Agent System v3.0 is running.",
        "version": "3.0.0",
        "endpoints": {
            "query": "/api/query",
            "image_processing": "/api/edit_image",
            "file_upload": "/api/upload",
            "code_generation": "/api/studio/generate_code",
            "logs": "/api/logs (admin only)"
        }
    }

# --- Cleanup ---
@app.on_event("shutdown")
def shutdown_event():
    """Closes connections and performs cleanup on application shutdown."""
    app_logger.info("Application shutting down...")
    
    # Close MasterAgent connections (includes logger and project agent)
    if hasattr(master, 'close'):
        master.close()
        app_logger.info("MasterAgent resources closed.")
    
    # Close Redis cache connection if needed
    if cache.redis_connection:
        # Redis connections are typically managed by the connection pool
        # but we can explicitly close if needed
        app_logger.info("Redis cache connections will be closed by the pool.")

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
