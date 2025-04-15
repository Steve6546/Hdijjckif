import os
import subprocess
import time
import logging
from github import Github
from openrouter import OpenRouterClient
from abc import ABC, abstractmethod

class AgentBase(ABC):
    @abstractmethod
    def analyze(self, data):
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/ai_agents.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ai_agents")

class MasterAgent:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_name = os.getenv("GITHUB_REPO")  # Use GITHUB_REPO env variable
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY") # Add OpenRouter API Key
        if not self.github_token or not self.repo_name or not self.openrouter_api_key:
            logger.error("GITHUB_TOKEN, GITHUB_REPO or OPENROUTER_API_KEY environment variables not set.")
            raise ValueError("GITHUB_TOKEN, GITHUB_REPO and OPENROUTER_API_KEY must be set.")
        try:
            self.g = Github(self.github_token)
            self.repo = self.g.get_repo(self.repo_name)
            self.client = OpenRouterClient(api_key=self.openrouter_api_key) # Initialize OpenRouter Client
            logger.info(f"Successfully connected to GitHub repository: {self.repo_name}")
        except Exception as e:
            logger.error(f"Error connecting to GitHub: {e}")
            raise

    def check_for_updates(self):
        try:
            latest_commit = self.repo.get_commits()[0].sha
            current_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
            if latest_commit != current_commit:
                logger.info("New commit found. Updating project...")
                self.update_project()
            else:
                logger.info("No new commits found.")
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")

    def update_project(self):
        try:
            logger.info("Checking for actual updates before pulling...")
            # Check if there are any changes to pull
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
            if result.stdout:
                logger.info("Pulling latest changes from GitHub...")
                subprocess.run(["git", "pull", "origin", "main"], check=True, capture_output=True, text=True)
                logger.info("Restarting the application...")
                subprocess.run(["replit", "restart"], check=True, capture_output=True, text=True)
                logger.info("Project updated and restarted successfully.")
            else:
                logger.info("No updates found. Skipping pull and restart.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error updating project: {e.stderr}")
        except Exception as e:
            logger.error(f"Error updating project: {e}")

    def run_security_checks(self):
        # Placeholder for security checks
        logger.info("Running security checks...")
        # Implement security checks here (e.g., check for unauthorized file modifications)
        logger.info("Security checks completed.")

class UpdateAgent:
    def __init__(self, master_agent):
        self.master_agent = master_agent

    def run_hourly_updates(self):
        while True:
            self.master_agent.check_for_updates()
            time.sleep(3600)  # Check every hour

class SecurityAgent:
    def __init__(self, master_agent):
        self.master_agent = master_agent

    def start_monitoring(self):
        while True:
            self.master_agent.run_security_checks()
            time.sleep(600)  # Check every 10 minutes

if __name__ == "__main__":
    # Example usage (for testing purposes)
    try:
        master = MasterAgent()
        update_agent = UpdateAgent(master)
        security_agent = SecurityAgent(master)

        # Run update checks and security checks in separate threads
        import threading
        update_thread = threading.Thread(target=update_agent.run_hourly_updates)
        security_thread = threading.Thread(target=security_agent.start_monitoring)

        update_thread.daemon = True
        security_thread.daemon = True

        update_thread.start()
        security_thread.start()

        # Keep the main thread alive
        while True:
            time.sleep(3600)
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")