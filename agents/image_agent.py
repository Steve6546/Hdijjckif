# agents/image_agent.py
import logging
from PIL import Image, ImageFilter
import io
import os

logger = logging.getLogger(__name__)

# Define a directory to save temporary/output images
OUTPUT_IMAGE_DIR = "processed_images"
os.makedirs(OUTPUT_IMAGE_DIR, exist_ok=True)

class ImageAgent:
    """
    Agent responsible for handling image processing tasks.
    """
    def process(self, query: str, image_bytes: bytes) -> dict:
        """
        Processes a query related to image editing.

        Args:
            query: The input text query describing the edit.
            image_bytes: The raw bytes of the image to edit.

        Returns:
            A dictionary containing the result:
            - {"message": "Success/Error message"}
            - {"image_path": "path/to/output/image.jpg"}
        """
        query_lower = query.lower()
        logger.info(f"ImageAgent processing query: '{query}'")

        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Ensure image is in RGB for consistent processing
            if img.mode != 'RGB':
                img = img.convert('RGB')

            output_filename = f"output_{os.urandom(4).hex()}.jpg" # Generate unique filename
            output_path = os.path.join(OUTPUT_IMAGE_DIR, output_filename)

            if "تغيير لون الشعر" in query or "change hair color" in query_lower:
                # Placeholder: In a real scenario, this would involve complex segmentation and color mapping
                logger.warning("Hair color change is a placeholder.")
                # For demonstration, maybe just save the original image with a message
                # img.save(output_path, "JPEG")
                return {"message": "تم تغيير لون الشعر إلى أبيض! (وظيفة تجريبية)"} # "Hair color changed to white! (Demo function)"

            elif "إضافة تأثير" in query or "add effect" in query_lower:
                if "ضبابي" in query or "blur" in query_lower:
                    logger.info(f"Applying blur filter to image.")
                    blurred = img.filter(ImageFilter.BLUR)
                    blurred.save(output_path, "JPEG")
                    logger.info(f"Saved blurred image to {output_path}")
                    return {"image_path": output_path}
                else:
                    logger.warning(f"Unsupported effect requested in query: '{query}'")
                    return {"message": "التأثير المطلوب غير مدعوم."} # "Requested effect not supported."

            elif "تعديل صورة" in query or "edit image" in query_lower:
                 # Generic edit placeholder - perhaps apply a simple filter like sharpen
                 logger.info("Applying sharpen filter as default edit.")
                 sharpened = img.filter(ImageFilter.SHARPEN)
                 sharpened.save(output_path, "JPEG")
                 logger.info(f"Saved sharpened image to {output_path}")
                 return {"image_path": output_path}
                 # return {"message": "تم تعديل الصورة بنجاح!"} # "Image edited successfully!"

            else:
                logger.warning(f"ImageAgent does not support query: '{query}'")
                return {"message": "طلب تعديل الصورة هذا غير مدعوم."} # "This image editing request is not supported."

        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            return {"message": f"حدث خطأ أثناء معالجة الصورة: {e}"} # "An error occurred during image processing: {e}"

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
