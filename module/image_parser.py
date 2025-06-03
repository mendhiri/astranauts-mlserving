import pytesseract
from PIL import Image, ImageDraw, ImageFont

def extract_text_from_image(image_path: str) -> str:
    """
    Extracts text from an image using Tesseract OCR.

    Args:
        image_path: The file path of the image.

    Returns:
        The extracted text, or an error message if an error occurs.
    """
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text
    except FileNotFoundError:
        return f"Error processing image: File not found at {image_path}"
    except pytesseract.TesseractNotFoundError:
        return "Error processing image: Tesseract OCR is not installed or not found in your PATH."
    except Exception as e:
        return f"Error processing image: {e}"

if __name__ == "__main__":
    # Create a dummy image for testing
    dummy_image_path = "dummy_image.png"
    try:
        img = Image.new('RGB', (400, 100), color = (255, 255, 255))
        d = ImageDraw.Draw(img)

        # Attempt to load a default font
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default()
            print("Arial font not found, using default font. Text rendering might be basic.")

        d.text((10,10), "Hello World", fill=(0,0,0), font=font)
        img.save(dummy_image_path)

        print(f"Created dummy image: {dummy_image_path}")
        extracted_text = extract_text_from_image(dummy_image_path)
        print(f"Extracted text: '{extracted_text.strip()}'")

    except ImportError:
        print("Pillow library is not installed. Cannot create dummy image.")
    except Exception as e:
        print(f"Error creating dummy image or extracting text: {e}")

    # Test with a non-existent file
    non_existent_image_path = "non_existent_image.png"
    extracted_text_error = extract_text_from_image(non_existent_image_path)
    print(f"Testing with non-existent file: '{extracted_text_error}'")
