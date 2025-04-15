import logging
from ultralytics import YOLO
from PIL import Image
import os
from typing import List, Dict, Any

logger = logging.getLogger("image_analyzer_analysis")

# --- Model Loading ---
# Load the YOLOv5 model once when the module is imported.
# This assumes the model file ('yolov5s.pt') will be downloaded automatically
# by Ultralytics on first use or is placed in a known location.
# Using a smaller model like 'yolov5s' for faster loading/inference initially.
MODEL_NAME = 'yolov5s.pt'
MODEL_PATH = os.getenv("YOLO_MODEL_PATH", MODEL_NAME) # Allow overriding path via env var

try:
    logger.info(f"Attempting to load YOLO model: {MODEL_PATH}")
    # Check if the model file exists locally before loading, Ultralytics might handle download
    # if not os.path.exists(MODEL_PATH):
    #     logger.warning(f"Model file {MODEL_PATH} not found locally. Ultralytics will attempt download.")
    model = YOLO(MODEL_PATH)
    # Perform a dummy inference to ensure the model is fully loaded/initialized if needed
    # model(Image.new('RGB', (64, 64)), verbose=False)
    logger.info(f"Successfully loaded YOLO model: {MODEL_PATH}")
except Exception as e:
    logger.error(f"Failed to load YOLO model '{MODEL_PATH}': {e}", exc_info=True)
    # Depending on requirements, you might want to raise the exception
    # or set model to None and handle it gracefully later.
    model = None
    # raise RuntimeError(f"Could not load YOLO model: {e}") from e

# --- Object Detection Function ---
def perform_object_detection(image_path: str) -> List[Dict[str, Any]]:
    """
    Performs object detection on an image using the pre-loaded YOLOv5 model.

    Args:
        image_path: The path to the image file.

    Returns:
        A list of dictionaries, where each dictionary represents a detected object
        with keys like 'label', 'confidence', and 'bbox'. Returns an empty list
        if the model failed to load or an error occurs during detection.
    """
    if model is None:
        logger.error("YOLO model is not loaded. Cannot perform object detection.")
        return []

    logger.info(f"Performing object detection on image: {image_path}")
    try:
        # Open image to ensure it's valid before passing to model
        img = Image.open(image_path)
        img.verify() # Verify image integrity
        # Re-open after verify
        img = Image.open(image_path)

        # Perform inference
        results = model(img, verbose=False) # verbose=False to reduce console output

        detections = []
        # Process results - results[0] contains detections for the first image
        if results and results[0].boxes:
            boxes = results[0].boxes.cpu().numpy() # Get boxes on CPU in numpy format
            for box in boxes:
                class_id = int(box.cls[0])
                label = model.names[class_id] # Get label name from model's class names
                confidence = float(box.conf[0])
                bbox_coords = box.xyxy[0].tolist() # Get bounding box coordinates [x1, y1, x2, y2]

                detections.append({
                    "label": label,
                    "confidence": round(confidence, 4), # Round confidence
                    "bbox": [round(coord) for coord in bbox_coords] # Round coordinates
                })
            logger.info(f"Detected {len(detections)} objects in {image_path}.")
        else:
             logger.info(f"No objects detected in {image_path}.")

        return detections

    except FileNotFoundError:
        logger.error(f"Image file not found at path: {image_path}")
        return []
    except Exception as e:
        logger.error(f"Error during object detection for {image_path}: {e}", exc_info=True)
        return []

# --- Example Usage (for testing) ---
if __name__ == "__main__":
    # Create a dummy image for testing if needed, or use a test image path
    test_image_path = "test_image.jpg" # Replace with a valid image path
    if not os.path.exists(test_image_path):
        try:
            logger.info(f"Creating dummy test image: {test_image_path}")
            dummy_img = Image.new('RGB', (640, 480), color = 'red')
            dummy_img.save(test_image_path)
        except Exception as e:
            logger.error(f"Failed to create dummy test image: {e}")
            test_image_path = None # Prevent error below

    if model and test_image_path and os.path.exists(test_image_path):
        print(f"\nTesting object detection on: {test_image_path}")
        detected_objects = perform_object_detection(test_image_path)
        if detected_objects:
            print("Detected objects:")
            for obj in detected_objects:
                print(f"  - Label: {obj['label']}, Confidence: {obj['confidence']:.4f}, BBox: {obj['bbox']}")
        else:
            print("No objects detected or an error occurred.")
        # Clean up dummy image
        # if "dummy" in test_image_path: os.remove(test_image_path)
    else:
        print("\nSkipping detection test: Model not loaded or test image path invalid.")