import fitz  # PyMuPDF
import io
from PIL import Image, ImageDraw, ImageFont
import os

# Attempt to import from local image_parser.py
try:
    from image_parser import extract_text_from_image
except ImportError:
    # This is a fallback for environments where image_parser might not be directly importable
    # In a real scenario, ensure image_parser.py is in PYTHONPATH or the same directory
    print("Warning: Could not import extract_text_from_image from image_parser. OCR for PDFs will fail.")
    print("Ensure image_parser.py is in the same directory or accessible via sys.path.")
    def extract_text_from_image(image_path: str) -> str:
        return f"Error: extract_text_from_image not available (image_parser.py not found or failed to import). Path: {image_path}"

def extract_text_from_pdf(pdf_file_path: str, ocr_image_parser_func: callable) -> str:
    """
    Extracts text from a PDF file. It tries direct text extraction first,
    and if that yields minimal text, it performs OCR on the page image.

    Args:
        pdf_file_path: The file path of the .pdf file.
        ocr_image_parser_func: A callable function (e.g., extract_text_from_image)
                               that takes an image file path and returns extracted text.

    Returns:
        The extracted text from all pages, or an error message if an error occurs.
    """
    all_text_parts = []
    pdf_document = None
    temp_image_path = "temp_page_image.png"

    try:
        pdf_document = fitz.open(pdf_file_path)
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)

            # Try direct text extraction
            direct_text = page.get_text().strip()

            if not direct_text:  # If direct text is empty or only whitespace
                # Render page as image for OCR
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")

                # Create PIL Image from bytes
                pil_image = Image.open(io.BytesIO(img_bytes))
                pil_image.save(temp_image_path) # Save to a temporary file

                ocr_text = ocr_image_parser_func(temp_image_path)
                all_text_parts.append(ocr_text.strip())

                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
            else:
                all_text_parts.append(direct_text)

        return "\n\n".join(all_text_parts) # Join with double newline to separate page contents

    except FileNotFoundError:
        return f"Error processing PDF file: File not found at {pdf_file_path}"
    except RuntimeError as fe: # Changed to RuntimeError for PyMuPDF operational errors
        return f"Error processing PDF file (PyMuPDF runtime error): {fe} for file {pdf_file_path}"
    except Exception as e:
        return f"Error processing PDF file: {e}"
    finally:
        if pdf_document:
            pdf_document.close()
        if os.path.exists(temp_image_path): # Ensure temp file is cleaned up in case of error
            os.remove(temp_image_path)


if __name__ == "__main__":
    # Ensure image_parser.extract_text_from_image is available for testing
    # The import at the top handles the case where it might not be found.
    # If it's not found, the ocr_image_parser_func will be a dummy that returns an error.

    # --- Test 1: Text-based PDF ---
    dummy_text_pdf_path = "dummy_text_pdf.pdf"
    try:
        doc = fitz.open()  # New PDF
        page = doc.new_page()
        page.insert_text(fitz.Point(50, 72), "This is a purely text-based PDF page.")
        page.insert_text(fitz.Point(50, 92), "It should be extracted directly.")
        doc.save(dummy_text_pdf_path)
        doc.close()
        print(f"Created dummy text PDF: {dummy_text_pdf_path}")

        extracted_text_pdf = extract_text_from_pdf(dummy_text_pdf_path, extract_text_from_image)
        print(f"Extracted text from text PDF:\n---\n{extracted_text_pdf}\n---\n")
    except Exception as e:
        print(f"Error in text PDF test case: {e}")

    # --- Test 2: Image-based PDF (simulated by creating an image and putting it in a PDF) ---
    dummy_image_pdf_path = "dummy_image_pdf.pdf"
    # Create a dummy image first (like in image_parser.py)
    dummy_actual_image_for_pdf = "actual_image_for_pdf.png"
    try:
        img = Image.new('RGB', (600, 150), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 30)
        except IOError:
            font = ImageFont.load_default()
        d.text((10, 10), "Text in an Image on a PDF page.", fill=(0, 0, 0), font=font)
        img.save(dummy_actual_image_for_pdf)
        print(f"Created dummy image for PDF: {dummy_actual_image_for_pdf}")

        # Now create a PDF with this image
        doc = fitz.open() # New PDF
        page = doc.new_page(width=600, height=150) # page dimensions to match image
        page.insert_image(page.rect, filename=dummy_actual_image_for_pdf)
        doc.save(dummy_image_pdf_path)
        doc.close()
        print(f"Created dummy image PDF: {dummy_image_pdf_path}")

        extracted_image_pdf = extract_text_from_pdf(dummy_image_pdf_path, extract_text_from_image)
        print(f"Extracted text from image PDF (should use OCR):\n---\n{extracted_image_pdf}\n---\n")

    except ImportError:
        print("Pillow or other libraries missing for image PDF test.")
    except Exception as e:
        print(f"Error in image PDF test case: {e}")


    # --- Test 3: Non-existent PDF file ---
    non_existent_pdf_path = "non_existent_document.pdf"
    extracted_text_error_pdf = extract_text_from_pdf(non_existent_pdf_path, extract_text_from_image)
    print(f"Testing PDF with non-existent file: '{extracted_text_error_pdf}'\n")

    # --- Test 4: Invalid PDF file (e.g., a text file) ---
    invalid_pdf_path = "dummy_text_file_as_pdf.txt"
    try:
        with open(invalid_pdf_path, "w") as f:
            f.write("This is not a PDF.")
        print(f"Created dummy invalid PDF file: {invalid_pdf_path}")
        extracted_text_invalid_pdf = extract_text_from_pdf(invalid_pdf_path, extract_text_from_image)
        print(f"Testing PDF with invalid file: '{extracted_text_invalid_pdf}'\n")
    except Exception as e:
        print(f"Error in invalid PDF test setup: {e}")


    # --- Clean up dummy files ---
    for f_path in [dummy_text_pdf_path, dummy_image_pdf_path, dummy_actual_image_for_pdf, invalid_pdf_path, "temp_page_image.png"]:
        if os.path.exists(f_path):
            try:
                os.remove(f_path)
                print(f"Cleaned up {f_path}")
            except Exception as e:
                print(f"Error cleaning up {f_path}: {e}")
