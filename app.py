from fastapi import FastAPI, File, UploadFile
import os
import subprocess
import uvicorn
from ai_agents import MasterAgent, UpdateAgent, SecurityAgent
import threading
import time
import logging
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("app")

app = FastAPI()

try:
    master = MasterAgent()
    update_agent = UpdateAgent(master)
    security_agent = SecurityAgent(master)

    # Run update checks and security checks in separate threads
    update_thread = threading.Thread(target=update_agent.run_hourly_updates)
    security_thread = threading.Thread(target=security_agent.start_monitoring)

    update_thread.daemon = True
    security_thread.daemon = True

    update_thread.start()
    security_thread.start()

    logger.info("Update and security threads started.")

except ValueError as e:
    logger.error(f"Configuration error: {e}")
    # Handle the error appropriately, e.g., exit the application
    exit()
except Exception as e:
    logger.error(f"An error occurred during initialization: {e}")
    exit()


@app.get("/")
def read_root():
    return {"message": "المشروع يعمل بسلاسة! التحديثات تتم تلقائيا..."}

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    logger.info(f"Analyzing image: {file.filename}")
    # Simulate image analysis
    await file.read()  # Read the file (required)
    analysis_results = {"filename": file.filename, "analysis": "Image analysis complete (simulated)."}
    return analysis_results

@app.post("/createWebsite")
async def create_website():
    return {"message": "Creating website (simulated)."}

@app.post("/smartUpdates")
async def smart_updates():
    return {"message": "Running smart updates (simulated)."}

@app.post("/manageAgents")
async def manage_agents():
    return {"message": "Managing agents (simulated)."}

@app.post("/auto-update")
def auto_update():
    master.update_project()
    return {"status": "تحديث نجح"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
