import json
import os
import logging
import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("image_analyzer_results_store")

# Define the directory where detection logs will be stored
# Using a subdirectory within the main project logs/ seems reasonable
RESULTS_DIR = "logs/detection_results"
os.makedirs(RESULTS_DIR, exist_ok=True) # Ensure the directory exists

def _get_daily_log_path(log_date: Optional[datetime.date] = None) -> str:
    """Constructs the path for the log file for a given date."""
    if log_date is None:
        log_date = datetime.date.today()
    filename = f"detections_{log_date.strftime('%Y-%m-%d')}.jsonl" # Use .jsonl for line-delimited JSON
    return os.path.join(RESULTS_DIR, filename)

def save_detection_result(image_filename: str, detections: List[Dict[str, Any]]):
    """
    Saves a single detection result to the daily log file (JSON Lines format).

    Args:
        image_filename: The original name of the analyzed image.
        detections: A list of detected objects from the analysis function.
    """
    log_path = _get_daily_log_path()
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "image_filename": image_filename,
        "detections": detections
    }
    try:
        # Append as a new line (JSON Lines format)
        with open(log_path, "a") as f:
            json.dump(log_entry, f)
            f.write("\n") # Add newline separator
        logger.info(f"Saved detection result for '{image_filename}' to {log_path}")
    except IOError as e:
        logger.error(f"Error saving detection result to {log_path}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error saving detection result: {e}", exc_info=True)


def get_results_for_day(log_date: datetime.date) -> List[Dict[str, Any]]:
    """
    Retrieves all detection results logged on a specific date.

    Args:
        log_date: The date for which to retrieve logs.

    Returns:
        A list of log entry dictionaries for the specified date.
        Returns an empty list if the file doesn't exist or an error occurs.
    """
    log_path = _get_daily_log_path(log_date)
    results = []
    if not os.path.exists(log_path):
        logger.warning(f"Detection log file not found for date {log_date}: {log_path}")
        return results

    try:
        with open(log_path, "r") as f:
            for line in f:
                try:
                    # Remove trailing newline and parse JSON
                    log_entry = json.loads(line.strip())
                    results.append(log_entry)
                except json.JSONDecodeError as json_e:
                    logger.error(f"Skipping invalid JSON line in {log_path}: {json_e} - Line: '{line.strip()}'")
        logger.info(f"Retrieved {len(results)} detection results from {log_path}")
        return results
    except IOError as e:
        logger.error(f"Error reading detection results from {log_path}: {e}", exc_info=True)
        return [] # Return empty list on error
    except Exception as e:
         logger.error(f"Unexpected error reading detection results: {e}", exc_info=True)
         return []


# --- Example Usage (for testing) ---
if __name__ == "__main__":
    print("Testing results store...")
    test_date = datetime.date.today()
    test_detections = [
        {"label": "person", "confidence": 0.95, "bbox": [10, 10, 50, 100]},
        {"label": "car", "confidence": 0.88, "bbox": [100, 50, 200, 150]}
    ]

    # Test saving
    print(f"\nSaving test result for today ({test_date})...")
    save_detection_result("test_image_1.jpg", test_detections)
    save_detection_result("test_image_2.jpg", [{"label": "dog", "confidence": 0.75, "bbox": [20, 30, 40, 50]}])

    # Test reading
    print(f"\nReading results for today ({test_date})...")
    today_results = get_results_for_day(test_date)
    if today_results:
        print(f"Found {len(today_results)} results:")
        for entry in today_results:
            print(f"  - Image: {entry['image_filename']}, Detections: {len(entry['detections'])}")
    else:
        print("No results found for today or error reading file.")

    # Test reading for a non-existent date (optional)
    # yesterday = test_date - datetime.timedelta(days=1)
    # print(f"\nReading results for yesterday ({yesterday})...")
    # yesterday_results = get_results_for_day(yesterday)
    # print(f"Found {len(yesterday_results)} results for yesterday.")