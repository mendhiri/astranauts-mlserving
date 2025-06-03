import os
import shutil # For cleaning up dummy files
from PIL import Image, ImageDraw, ImageFont # To create dummy images
import docx # To create dummy docx
import fitz # PyMuPDF, to create dummy PDFs

# Import functions from our modules
from image_parser import extract_text_from_image
from text_document_parser import extract_text_from_txt, extract_text_from_docx
from pdf_parser import extract_text_from_pdf
from keyword_extractor import extract_keywords_and_values, format_to_json

# --- Configuration ---
DUMMY_FILES_DIR = "dummy_test_docs"
TARGET_KEYWORDS = [
    {'keyword': 'Income', 'variations': ['income', 'revenue', 'earnings']},
    {'keyword': 'Balance', 'variations': ['balance', 'account balance']},
    {'keyword': 'Identifier', 'variations': ['id', 'identifier', 'ref_no']}
]

# --- Helper function to create dummy files ---
def create_dummy_files():
    if os.path.exists(DUMMY_FILES_DIR):
        shutil.rmtree(DUMMY_FILES_DIR)
    os.makedirs(DUMMY_FILES_DIR, exist_ok=True)

    dummy_content = {
        "text": "Report for Q1. Total Income: $150,000. Account Balance is $75,000. Ref_No: Test001.",
        "image_text": "Image data. Income $5000. Balance $200. ID X99." # Text for image/scanned PDF
    }

    created_paths = []

    # 1. Create Dummy TXT file
    txt_path = os.path.join(DUMMY_FILES_DIR, "dummy.txt")
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(dummy_content["text"])
        print(f"Created: {txt_path}")
        created_paths.append(txt_path)
    except Exception as e:
        print(f"Error creating {txt_path}: {e}")
        created_paths.append(None)


    # 2. Create Dummy DOCX file
    docx_path = os.path.join(DUMMY_FILES_DIR, "dummy.docx")
    try:
        doc = docx.Document()
        doc.add_paragraph(dummy_content["text"])
        doc.save(docx_path)
        print(f"Created: {docx_path}")
        created_paths.append(docx_path)
    except Exception as e:
        print(f"Error creating {docx_path}: {e}")
        created_paths.append(None)

    # 3. Create Dummy Image file (PNG)
    img_path = os.path.join(DUMMY_FILES_DIR, "dummy.png")
    try:
        img = Image.new('RGB', (500, 100), color = (255, 255, 255)) # Increased width for full text
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            print("Arial font not found for dummy image, using default. Text rendering might be basic.")
            font = ImageFont.load_default()
        d.text((10,10), dummy_content["image_text"], fill=(0,0,0), font=font)
        img.save(img_path)
        print(f"Created: {img_path}")
        created_paths.append(img_path)
    except Exception as e:
        print(f"Error creating dummy image {img_path}: {e}. OCR test for image might be affected.")
        created_paths.append(None)


    # 4. Create Dummy Text-based PDF
    pdf_text_path = os.path.join(DUMMY_FILES_DIR, "dummy_text.pdf")
    try:
        pdf_doc_text = fitz.open() # New PDF
        page_text = pdf_doc_text.new_page()
        # Simple text insertion; for more complex, use page.insert_textbox for auto-wrapping
        page_text.insert_text((50, 72), dummy_content["text"])
        pdf_doc_text.save(pdf_text_path)
        pdf_doc_text.close()
        print(f"Created: {pdf_text_path}")
        created_paths.append(pdf_text_path)
    except Exception as e:
        print(f"Error creating {pdf_text_path}: {e}")
        created_paths.append(None)

    # 5. Create Dummy Image-based PDF (PDF from the PNG image)
    pdf_image_path = os.path.join(DUMMY_FILES_DIR, "dummy_image.pdf")
    # Check if the pre-requisite image file (img_path) was created successfully
    if created_paths[2] and os.path.exists(created_paths[2]):
        try:
            pdf_doc_image = fitz.open() # New PDF
            # Use the successfully created img_path from created_paths[2]
            img_for_pdf = fitz.open(created_paths[2])
            rect = img_for_pdf[0].rect
            pdf_page = pdf_doc_image.new_page(width=rect.width, height=rect.height)
            # page.insert_image(rect, filename=img_path) is more direct for image files
            pdf_page.insert_image(rect, filename=created_paths[2])
            pdf_doc_image.save(pdf_image_path)
            pdf_doc_image.close()
            img_for_pdf.close()
            print(f"Created: {pdf_image_path}")
            created_paths.append(pdf_image_path)
        except Exception as e:
            print(f"Error creating {pdf_image_path}: {e}")
            created_paths.append(None)
    else:
        print(f"Skipped creating {pdf_image_path} as dummy image was not available or failed creation.")
        created_paths.append(None)

    return created_paths

# --- Main processing logic ---
def process_document(doc_path):
    print(f"\n--- Processing: {doc_path} ---")
    extracted_text = ""
    file_extension = os.path.splitext(doc_path)[1].lower()

    if not os.path.exists(doc_path):
        print(f"File not found: {doc_path}. Skipping.")
        return

    try:
        if file_extension == '.pdf':
            extracted_text = extract_text_from_pdf(doc_path, extract_text_from_image)
        elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']:
            extracted_text = extract_text_from_image(doc_path)
        elif file_extension == '.txt':
            extracted_text = extract_text_from_txt(doc_path)
        elif file_extension == '.docx':
            extracted_text = extract_text_from_docx(doc_path)
        else:
            print(f"Unsupported file type: {file_extension}")
            return
    except Exception as e:
        print(f"Error parsing {doc_path}: {e}")
        # To ensure that an error during parsing still results in a "known" error string
        # for keyword extraction to process (and report as error).
        extracted_text = f"Error: Parsing failed with {type(e).__name__} - {e}"


    if not extracted_text.strip():
        print(f"Text extraction produced empty text for {doc_path}.")
        # Even if empty, try to run keyword extraction to see how it handles it (should be None for all)
        # extracted_text will be ""
    elif "Error:" in extracted_text: # Check if parsing itself returned an error message
         print(f"Text extraction failed for {doc_path}.")
         print(f"Reported: '{extracted_text[:200]}...'") # Print the error from parsing
         # Proceed to keyword extraction, which should then report this error.
    else:
        print(f"Successfully extracted text (first 100 chars): {extracted_text[:100].replace(os.linesep, ' ')}...")


    try:
        # Pass the extracted_text (which might be an error string from parsing)
        # to keyword extraction.
        results_dict = extract_keywords_and_values(extracted_text, TARGET_KEYWORDS)
        final_json = format_to_json(results_dict)
        print("Extraction Results (JSON):")
        print(final_json)
    except Exception as e:
        print(f"Error during keyword extraction or JSON formatting for {doc_path}: {e}")
        # Fallback JSON if everything else fails
        error_json = format_to_json({"error": f"Critical error in keyword extraction/JSON formatting: {str(e)}"})
        print(error_json)


# --- Execution ---
if __name__ == "__main__":
    print("Starting Integration Test...")
    # Ensure NLTK resources are available (as keyword_extractor relies on them)
    # This is a simplified check; a more robust one would be in keyword_extractor itself or main app.
    try:
        import nltk
        from nltk.tokenize import word_tokenize # Uses punkt, punkt_tab
        from nltk.corpus import stopwords # Uses stopwords
        from nltk.stem import WordNetLemmatizer # Uses wordnet

        # Test initialization or a simple operation
        WordNetLemmatizer().lemmatize("cats")
        _ = stopwords.words('english')
        _ = word_tokenize("test")
        print("NLTK resources seem to be available and components initialize correctly.")

    except Exception as e: # Catch broader exceptions during init as well (LookupError, or others)
        print(f"NLTK resource/component initialization failed: {e}.")
        print("Attempting to download potentially missing NLTK resources...")
        # Simplified download attempt for common resources
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('omw-1.4', quiet=True) # Often needed with wordnet
            nltk.download('punkt_tab', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True) # Though not directly tested by init here
            print("NLTK resources download attempt complete. Please re-run the test if it still fails, or check NLTK setup manually.")
        except Exception as download_exc:
            print(f"NLTK download attempt failed: {download_exc}")
        exit() # Exit if resources are critical and not found/downloaded.


    dummy_file_paths = create_dummy_files()

    valid_files_to_process = [p for p in dummy_file_paths if p and os.path.exists(p)]
    print(f"\nFound {len(valid_files_to_process)} valid dummy files to process out of {len(dummy_file_paths)} attempts.")

    for doc_path in dummy_file_paths:
        if doc_path and os.path.exists(doc_path):
             process_document(doc_path)
        elif doc_path: # Path was generated but file doesn't exist (e.g. image PDF if image creation failed)
            print(f"\n--- Skipping: {doc_path} as it was not successfully created or found. ---")


    # Clean up dummy files
    if os.path.exists(DUMMY_FILES_DIR):
        # shutil.rmtree(DUMMY_FILES_DIR) # Comment out to inspect files
        print(f"\nDummy files and directory '{DUMMY_FILES_DIR}' retained for inspection.")
        # print(f"\nCleaned up dummy files and directory: {DUMMY_FILES_DIR}")

    print("\nIntegration Test Finished.")
# Removed extraneous ``` from the end of the file.
