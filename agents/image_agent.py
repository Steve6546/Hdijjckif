# agents/image_agent.py
import logging
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import io
import os
import time
import numpy as np
from typing import Dict, Any, Optional, Tuple, List, Union

logger = logging.getLogger(__name__)

# Define a directory to save temporary/output images
OUTPUT_IMAGE_DIR = "processed_images"
os.makedirs(OUTPUT_IMAGE_DIR, exist_ok=True)

class ImageAgent:
    """
    Agent responsible for handling image processing tasks.
    Supports various image filters and transformations.
    Can also use AI for image analysis when connected to an AI model.
    """
    def __init__(self, ai_agent=None):
        """
        Initialize the ImageAgent with supported filters and operations.
        
        Args:
            ai_agent: Optional AI agent for image analysis and description
        """
        # Store AI agent if provided
        self.ai_agent = ai_agent
        
        # Define supported filters and their corresponding functions
        self.supported_filters = {
            "blur": self._apply_blur,
            "sharpen": self._apply_sharpen,
            "grayscale": self._apply_grayscale,
            "sepia": self._apply_sepia,
            "invert": self._apply_invert,
            "edge_enhance": self._apply_edge_enhance,
            "emboss": self._apply_emboss,
            "contour": self._apply_contour,
            "brightness": self._adjust_brightness,
            "contrast": self._adjust_contrast,
            "saturation": self._adjust_saturation,
        }
        
        # Define supported operations
        self.supported_operations = {
            "resize": self._resize_image,
            "crop": self._crop_image,
            "rotate": self._rotate_image,
            "flip": self._flip_image,
            "mirror": self._mirror_image,
        }
        
        logger.info("ImageAgent initialized with supported filters and operations.")
    
    def process(self, query: str, image_bytes: bytes) -> Dict[str, Any]:
        """
        Processes a query related to image editing.

        Args:
            query: The input text query describing the edit.
            image_bytes: The raw bytes of the image to edit.

        Returns:
            A dictionary containing the result:
            - {"message": "Success/Error message"}
            - {"image_path": "path/to/output/image.jpg"}
            - {"image_bytes": bytes} (optional, for direct use)
        """
        query_lower = query.lower()
        logger.info(f"ImageAgent processing query: '{query}'")

        try:
            # Open the image from bytes
            img = Image.open(io.BytesIO(image_bytes))
            
            # Ensure image is in RGB for consistent processing
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Generate a unique filename based on timestamp and random bytes
            timestamp = int(time.time())
            output_filename = f"output_{timestamp}_{os.urandom(2).hex()}.jpg"
            output_path = os.path.join(OUTPUT_IMAGE_DIR, output_filename)
            
            # Process based on query content
            result = self._process_query(query, query_lower, img, output_path)
            
            # Add metadata to result
            if "image_path" in result and not "message" in result:
                result["message"] = "تمت معالجة الصورة بنجاح" # "Image processed successfully"
                
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            return {"message": f"حدث خطأ أثناء معالجة الصورة: {e}"} # "An error occurred during image processing: {e}"
    
    def _process_query(self, query: str, query_lower: str, img: Image.Image, output_path: str) -> Dict[str, Any]:
        """
        Process the query and apply the appropriate image transformation.
        
        Args:
            query: The original query string
            query_lower: Lowercase version of the query for easier matching
            img: The PIL Image object to process
            output_path: Where to save the processed image
            
        Returns:
            Dictionary with result information
        """
        # Check for filter applications
        for filter_name, filter_func in self.supported_filters.items():
            filter_terms = {
                "blur": ["ضبابي", "blur", "blurry"],
                "sharpen": ["حاد", "sharpen", "شحذ"],
                "grayscale": ["رمادي", "grayscale", "black and white", "أبيض وأسود"],
                "sepia": ["سيبيا", "sepia", "قديم", "vintage"],
                "invert": ["عكس", "invert", "negative", "سلبي"],
                "edge_enhance": ["تعزيز الحواف", "edge enhance", "حواف"],
                "emboss": ["نقش", "emboss", "بارز"],
                "contour": ["كونتور", "contour", "محيط"],
                "brightness": ["سطوع", "brightness", "إضاءة"],
                "contrast": ["تباين", "contrast"],
                "saturation": ["تشبع", "saturation", "إشباع"],
            }
            
            # Check if any of the terms for this filter are in the query
            if any(term in query_lower or term in query for term in filter_terms[filter_name]):
                # For adjustments that need a value parameter
                if filter_name in ["brightness", "contrast", "saturation"]:
                    # Try to extract a value from the query (default to 1.5 for increase, 0.5 for decrease)
                    value = 1.5  # Default to increase
                    
                    decrease_terms = ["تقليل", "خفض", "decrease", "reduce", "lower"]
                    if any(term in query_lower or term in query for term in decrease_terms):
                        value = 0.5  # Set to decrease
                    
                    # Apply the filter with the determined value
                    processed_img = filter_func(img, value)
                else:
                    # Apply standard filter
                    processed_img = filter_func(img)
                
                # Save the processed image
                processed_img.save(output_path, "JPEG")
                logger.info(f"Applied {filter_name} filter and saved to {output_path}")
                return {"image_path": output_path}
        
        # Check for operations
        for op_name, op_func in self.supported_operations.items():
            op_terms = {
                "resize": ["تغيير الحجم", "resize", "scale"],
                "crop": ["اقتصاص", "crop", "قص"],
                "rotate": ["تدوير", "rotate", "دوران"],
                "flip": ["قلب", "flip", "عكس رأسي"],
                "mirror": ["مرآة", "mirror", "عكس أفقي"],
            }
            
            # Check if any of the terms for this operation are in the query
            if any(term in query_lower or term in query for term in op_terms[op_name]):
                # Handle operation-specific parameters
                if op_name == "resize":
                    # Default to 50% resize if no specific size mentioned
                    width, height = img.size
                    new_width, new_height = width // 2, height // 2
                    
                    # Try to extract specific dimensions if provided
                    # This is a simplified example - in a real system you'd use more sophisticated parsing
                    if "50%" in query or "نصف" in query:
                        new_width, new_height = width // 2, height // 2
                    elif "25%" in query or "ربع" in query:
                        new_width, new_height = width // 4, height // 4
                    elif "75%" in query or "ثلاثة أرباع" in query:
                        new_width, new_height = int(width * 0.75), int(height * 0.75)
                    elif "200%" in query or "ضعف" in query or "double" in query:
                        new_width, new_height = width * 2, height * 2
                        
                    processed_img = op_func(img, (new_width, new_height))
                    
                elif op_name == "rotate":
                    # Default rotation angle
                    angle = 90
                    
                    # Try to extract rotation angle
                    if "90" in query:
                        angle = 90
                    elif "180" in query:
                        angle = 180
                    elif "270" in query or "-90" in query:
                        angle = 270
                    elif "45" in query:
                        angle = 45
                    
                    processed_img = op_func(img, angle)
                    
                elif op_name == "crop":
                    # Default to center crop of 50%
                    width, height = img.size
                    crop_width, crop_height = width // 2, height // 2
                    left = (width - crop_width) // 2
                    top = (height - crop_height) // 2
                    right = left + crop_width
                    bottom = top + crop_height
                    
                    # Simple crop parameter extraction (could be more sophisticated)
                    if "center" in query_lower or "وسط" in query:
                        # Use default center crop
                        pass
                    elif "top" in query_lower or "أعلى" in query:
                        top = 0
                        bottom = crop_height
                    elif "bottom" in query_lower or "أسفل" in query:
                        top = height - crop_height
                        bottom = height
                    elif "left" in query_lower or "يسار" in query:
                        left = 0
                        right = crop_width
                    elif "right" in query_lower or "يمين" in query:
                        left = width - crop_width
                        right = width
                    
                    processed_img = op_func(img, (left, top, right, bottom))
                    
                else:
                    # For operations without parameters
                    processed_img = op_func(img)
                
                # Save the processed image
                processed_img.save(output_path, "JPEG")
                logger.info(f"Applied {op_name} operation and saved to {output_path}")
                return {"image_path": output_path}
        
        # If no specific operation was matched, apply a default enhancement
        logger.info("No specific operation matched. Applying default enhancement.")
        enhanced = self._apply_auto_enhance(img)
        enhanced.save(output_path, "JPEG")
        logger.info(f"Applied auto enhancement and saved to {output_path}")
        return {
            "image_path": output_path,
            "message": "تم تطبيق تحسين تلقائي على الصورة" # "Auto enhancement applied to image"
        }
    
    # --- Filter Implementation Methods ---
    
    def _apply_blur(self, img: Image.Image, radius: int = 2) -> Image.Image:
        """Apply a blur filter to the image."""
        return img.filter(ImageFilter.GaussianBlur(radius=radius))
    
    def _apply_sharpen(self, img: Image.Image) -> Image.Image:
        """Apply a sharpen filter to the image."""
        return img.filter(ImageFilter.SHARPEN)
    
    def _apply_grayscale(self, img: Image.Image) -> Image.Image:
        """Convert the image to grayscale."""
        return ImageOps.grayscale(img).convert('RGB')  # Convert back to RGB for consistency
    
    def _apply_sepia(self, img: Image.Image) -> Image.Image:
        """Apply a sepia tone filter to the image."""
        # Convert to grayscale first
        gray = ImageOps.grayscale(img)
        
        # Apply sepia tone
        sepia = Image.new('RGB', img.size, (255, 240, 192))
        return Image.blend(gray.convert('RGB'), sepia, 0.5)
    
    def _apply_invert(self, img: Image.Image) -> Image.Image:
        """Invert the colors of the image."""
        return ImageOps.invert(img)
    
    def _apply_edge_enhance(self, img: Image.Image) -> Image.Image:
        """Enhance edges in the image."""
        return img.filter(ImageFilter.EDGE_ENHANCE)
    
    def _apply_emboss(self, img: Image.Image) -> Image.Image:
        """Apply an emboss filter to the image."""
        return img.filter(ImageFilter.EMBOSS)
    
    def _apply_contour(self, img: Image.Image) -> Image.Image:
        """Apply a contour filter to the image."""
        return img.filter(ImageFilter.CONTOUR)
    
    def _adjust_brightness(self, img: Image.Image, factor: float = 1.5) -> Image.Image:
        """Adjust the brightness of the image."""
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)
    
    def _adjust_contrast(self, img: Image.Image, factor: float = 1.5) -> Image.Image:
        """Adjust the contrast of the image."""
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)
    
    def _adjust_saturation(self, img: Image.Image, factor: float = 1.5) -> Image.Image:
        """Adjust the color saturation of the image."""
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(factor)
    
    def _apply_auto_enhance(self, img: Image.Image) -> Image.Image:
        """Apply automatic enhancement to the image."""
        # Apply a series of enhancements with moderate values
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageEnhance.Brightness(img).enhance(1.1)
        img = ImageEnhance.Color(img).enhance(1.2)
        img = ImageEnhance.Sharpness(img).enhance(1.3)
        return img
    
    # --- Operation Implementation Methods ---
    
    def _resize_image(self, img: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """Resize the image to the specified dimensions."""
        return img.resize(size, Image.LANCZOS)
    
    def _crop_image(self, img: Image.Image, box: Tuple[int, int, int, int]) -> Image.Image:
        """Crop the image to the specified box (left, top, right, bottom)."""
        return img.crop(box)
    
    def _rotate_image(self, img: Image.Image, angle: float) -> Image.Image:
        """Rotate the image by the specified angle in degrees."""
        return img.rotate(angle, expand=True)
    
    def _flip_image(self, img: Image.Image) -> Image.Image:
        """Flip the image vertically (top to bottom)."""
        return img.transpose(Image.FLIP_TOP_BOTTOM)
    
    def _mirror_image(self, img: Image.Image) -> Image.Image:
        """Mirror the image horizontally (left to right)."""
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    
    def get_supported_operations(self) -> Dict[str, List[str]]:
        """
        Returns a dictionary of supported operations and filters.
        
        Returns:
            Dict with 'filters' and 'operations' keys listing supported functions
        """
        operations = {
            "filters": list(self.supported_filters.keys()),
            "operations": list(self.supported_operations.keys())
        }
        
        # Add AI capabilities if AI agent is available
        if self.ai_agent:
            operations["ai_capabilities"] = ["describe_image", "analyze_image"]
            
        return operations
        
    def describe_image(self, image: Image.Image) -> str:
        """
        Use AI to describe the image content.
        
        Args:
            image: PIL Image object to describe
            
        Returns:
            str: Description of the image
        """
        if not self.ai_agent:
            return "AI agent not available for image description"
            
        try:
            # Convert image to bytes for base64 encoding
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()
            
            # For now, return a simple description since we don't have image input in the API yet
            prompt = "This is an image. Please describe what might be in it based on the context."
            description = self.ai_agent.generate(prompt)
            
            return description
        except Exception as e:
            logger.error(f"Error describing image: {e}")
            return f"Error describing image: {str(e)}"

# Example Usage (for testing purposes)
if __name__ == '__main__':
    # Create a dummy image file for testing
    try:
        dummy_image = Image.new('RGB', (60, 30), color = 'red')
        img_byte_arr = io.BytesIO()
        dummy_image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        image_agent = ImageAgent()

        # Test blur
        result_blur = image_agent.process("إضافة تأثير ضبابي", img_byte_arr)
        print("Blur Result:", result_blur)
        if 'image_path' in result_blur:
             print(f"Check for output file: {result_blur['image_path']}")

        # Test hair color (placeholder)
        result_hair = image_agent.process("تغيير لون الشعر إلى أبيض", img_byte_arr)
        print("Hair Color Result:", result_hair)

        # Test unsupported
        result_unsupported = image_agent.process("اقتصاص الصورة", img_byte_arr)
        print("Unsupported Result:", result_unsupported)

    except Exception as e:
        print(f"Error during ImageAgent test: {e}")
