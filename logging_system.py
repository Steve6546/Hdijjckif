import sqlite3
import datetime
import logging
import os

# Configure basic logging for the module itself
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("logging_system")

class Logger:
    """Handles logging activities to an SQLite database."""
    def __init__(self, db_path="activity.db"):
        """
        Initializes the Logger, connects to the database, and ensures the table exists.

        Args:
            db_path (str): The path to the SQLite database file. Defaults to "activity.db".
        """
        self.db_path = db_path
        self.conn = None
        try:
            # Ensure the directory for the db exists if it's not in the root
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logger.info(f"Created directory for database: {db_dir}")

            self.conn = sqlite3.connect(self.db_path, check_same_thread=False) # Allow access from multiple threads (FastAPI runs in threads)
            self.create_table()
            logger.info(f"Successfully connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database {self.db_path}: {e}")
            # Depending on the application's needs, you might want to raise the exception
            # or handle it differently (e.g., disable logging)
            raise  # Re-raise the exception to signal a critical failure during init
        except OSError as e:
            logger.error(f"OS error creating directory for database {self.db_path}: {e}")
            raise

    def create_table(self):
        """Creates the 'activities' table if it doesn't already exist."""
        try:
            with self.conn: # Use context manager for automatic commit/rollback
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        action TEXT NOT NULL,
                        result TEXT
                    )
                """)
            logger.info("Ensured 'activities' table exists.")
        except sqlite3.Error as e:
            logger.error(f"Error creating table 'activities': {e}")
            # Handle error appropriately, maybe raise it

    def log_activity(self, action: str, result: str):
        """
        Logs an activity to the database.

        Args:
            action (str): A description of the action performed.
            result (str): The result or outcome of the action.
        """
        timestamp = datetime.datetime.now().isoformat()
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO activities (timestamp, action, result)
                    VALUES (?, ?, ?)
                """, (timestamp, action, str(result))) # Ensure result is string
            logger.debug(f"Logged activity: Action='{action}', Result='{result}'")
        except sqlite3.Error as e:
            logger.error(f"Error logging activity: {e}")
            # Handle error appropriately

    def get_logs(self, limit: int = 50):
        """
        Retrieves recent activity logs from the database.

        Args:
            limit (int): The maximum number of log entries to retrieve. Defaults to 50.

        Returns:
            list: A list of dictionaries, where each dictionary represents a log entry.
                  Returns an empty list if an error occurs.
        """
        try:
            with self.conn:
                cursor = self.conn.execute("""
                    SELECT id, timestamp, action, result
                    FROM activities
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                # Fetch column names from cursor.description
                columns = [description[0] for description in cursor.description]
                # Fetch all rows and map them to dictionaries
                logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
                logger.debug(f"Retrieved {len(logs)} log entries.")
                return logs
        except sqlite3.Error as e:
            logger.error(f"Error retrieving logs: {e}")
            return [] # Return empty list on error

    def get_all_logs(self):
        """
        Retrieves ALL activity logs from the database, ordered by timestamp descending.
        Use with caution on large databases.

        Returns:
            list: A list of dictionaries representing log entries, or empty list on error.
        """
        try:
            with self.conn:
                cursor = self.conn.execute("""
                    SELECT id, timestamp, action, result
                    FROM activities
                    ORDER BY timestamp DESC
                """)
                columns = [description[0] for description in cursor.description]
                logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
                logger.debug(f"Retrieved all {len(logs)} log entries.")
                return logs
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all logs: {e}")
            return []

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

# Example usage (optional, for testing)
if __name__ == "__main__":
    try:
        test_logger = Logger("test_activity.db")
        test_logger.log_activity("Test Action", "Test Result Successful")
        test_logger.log_activity("Another Test", "Outcome: OK")
        recent_logs = test_logger.get_logs(10)
        print("Recent Logs:")
        for log in recent_logs:
            print(log)
        test_logger.close()
        # Clean up the test database file
        # os.remove("test_activity.db")
        # print("Test database removed.")
    except Exception as e:
        print(f"An error occurred during test: {e}")