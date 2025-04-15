import os
import shutil
import uuid
import logging
from typing import List, Dict, Set

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    UploadFile,
    File,
    HTTPException,
    Path
)
from fastapi.responses import JSONResponse

# Import the analysis function and results store function
from .analysis import perform_object_detection
from .results_store import save_detection_result

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("image_analyzer_backend")

TEMP_UPLOAD_DIRECTORY = "image_analyzer_backend/temp_uploads"

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        logger.info("ConnectionManager initialized.")

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client '{client_id}' connected via WebSocket.")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client '{client_id}' disconnected.")

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(message)
            logger.debug(f"Sent text message to client '{client_id}'.")
        else:
             logger.warning(f"Attempted to send text message to disconnected client '{client_id}'.")

    async def send_personal_json(self, data: dict, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(data)
            logger.debug(f"Sent JSON data to client '{client_id}'.")
        else:
            logger.warning(f"Attempted to send JSON data to disconnected client '{client_id}'.")

# --- FastAPI Application ---
app = FastAPI(title="Image Analysis Backend", version="1.0.0")
manager = ConnectionManager()

# Ensure temporary upload directory exists
os.makedirs(TEMP_UPLOAD_DIRECTORY, exist_ok=True)
logger.info(f"Ensured temporary upload directory exists: {TEMP_UPLOAD_DIRECTORY}")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str = Path(...)):
    """Handles WebSocket connections for real-time updates."""
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection open, optionally handle incoming messages
            data = await websocket.receive_text()
            logger.info(f"Received message from {client_id}: {data}")
            # Example: Echo back or process commands
            # await manager.send_personal_message(f"Message text was: {data}", client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}", exc_info=True)
        manager.disconnect(client_id)
        # Optionally close the websocket explicitly if needed
        # await websocket.close(code=1011)


@app.post("/upload_image/{client_id}")
async def upload_image(
    client_id: str = Path(...),
    file: UploadFile = File(...)
):
    """Handles image uploads, saves temporarily, and triggers analysis (placeholder)."""
    logger.info(f"Received image upload '{file.filename}' from client '{client_id}'.")

    if not file.content_type.startswith("image/"):
        logger.warning(f"Upload rejected for client '{client_id}': File '{file.filename}' is not an image ({file.content_type}).")
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")

    # Create a unique temporary filename to avoid collisions
    file_extension = os.path.splitext(file.filename)[1]
    temp_filename = f"{uuid.uuid4()}{file_extension}"
    temp_file_path = os.path.join(TEMP_UPLOAD_DIRECTORY, temp_filename)

    try:
        # Save the uploaded file temporarily
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Temporarily saved uploaded image as '{temp_filename}' for client '{client_id}'.")

        # --- Trigger Analysis ---
        detection_results = perform_object_detection(temp_file_path)
        logger.info(f"Analysis complete for '{temp_filename}'. Found {len(detection_results)} objects.")
        # ------------------------

        # --- Save results for reporting ---
        try:
            save_detection_result(file.filename, detection_results)
        except Exception as store_e:
            # Log error saving results, but don't fail the request
            logger.error(f"Failed to save detection results for {file.filename}: {store_e}", exc_info=True)
        # --------------------------------

        # --- Send results via WebSocket ---
        try:
            # Structure the message payload
            payload = {
                "type": "analysis_result",
                "filename": file.filename, # Include original filename for context
                "data": detection_results
            }
            await manager.send_personal_json(payload, client_id)
            logger.info(f"Sent detection results to client '{client_id}' via WebSocket.")
        except Exception as ws_e:
            # Log if sending results via WebSocket fails, but don't necessarily fail the HTTP request
            logger.error(f"Failed to send results via WebSocket to client '{client_id}': {ws_e}", exc_info=True)
        # ----------------------------------

        # --- Clean up temporary file ---
        # It's good practice to remove the temp file after analysis
        try:
            os.remove(temp_file_path)
            logger.info(f"Removed temporary file: {temp_file_path}")
        except OSError as e:
            logger.error(f"Error removing temporary file {temp_file_path}: {e}")
        # -----------------------------

        return JSONResponse(content={
            "message": "Image uploaded and analysis triggered.",
            "filename": file.filename,
            # "results_summary": f"Detected {len(detection_results)} objects." # Optionally include summary
        })

    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Failed to process upload for client '{client_id}', file '{file.filename}': {e}", exc_info=True)
        # Clean up temp file if analysis failed after saving
        if os.path.exists(temp_file_path):
             try:
                 os.remove(temp_file_path)
                 logger.info(f"Cleaned up temporary file after error: {temp_file_path}")
             except OSError as e:
                 logger.error(f"Error removing temporary file {temp_file_path} during error handling: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save or process uploaded image.")
    finally:
        # Ensure the UploadFile resource is closed
        await file.close()


# --- Main Execution ---
if __name__ == "__main__":
    # Note: Run this from the project root directory for correct relative paths
    # Example: uvicorn image_analyzer_backend.main:app --reload --port 8001
    import uvicorn
    logger.info("Starting Image Analysis Backend server...")
    # Running on a different port (e.g., 8001) to avoid conflict with the main app (port 8000)
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True, app_dir="image_analyzer_backend")