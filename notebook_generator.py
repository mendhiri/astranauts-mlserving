import nbformat as nbf
import os

# Attempt to install nbformat if not present - useful for isolated execution
try:
    import nbformat as nbf
except ImportError:
    print("nbformat not found. Attempting to install...")
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "nbformat"])
        import nbformat as nbf
        print("nbformat installed successfully.")
    except Exception as e:
        print(f"Failed to install nbformat: {e}")
        print("Please install nbformat manually: pip install nbformat")
        exit()


nb = nbf.v4.new_notebook()

# Cell 1: Title (Markdown)
cell1_md = """# Document Text Parser and Keyword Extractor

This notebook allows you to parse text from various document types (images, TXT, DOCX, PDF) and extract predefined keywords and their associated values. The output is provided in JSON format.
"""
nb['cells'] = [nbf.v4.new_markdown_cell(cell1_md)]

# Cell 2: Setup (Code)
cell2_code = """\
# Install necessary libraries (if not already installed)
# This step assumes that libraries like Pillow, Pytesseract, PyMuPDF, python-docx, NLTK, spaCy
# were installed as per the project setup.
# Also, ensure Tesseract OCR is installed on your system.

# Import custom modules (assuming they are in the same directory or Python path)
import os
import json
# Make sure the following .py files are in the same directory as this notebook
# or are installed in your Python environment.
from image_parser import extract_text_from_image
from text_document_parser import extract_text_from_txt, extract_text_from_docx
# pdf_parser's extract_text_from_pdf needs the extract_text_from_image from image_parser
from pdf_parser import extract_text_from_pdf
from keyword_extractor import preprocess_text, extract_keywords_and_values, format_to_json

# Download NLTK resources if not already present (optional, can be run once)
# import nltk
# required_nltk_resources = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger', 'punkt_tab']
# for resource in required_nltk_resources:
#     try:
#         # Adjust path based on typical NLTK structure
#         if resource in ['punkt', 'punkt_tab']:
#             nltk.data.find(f'tokenizers/{resource}')
#         elif resource == 'averaged_perceptron_tagger':
#             nltk.data.find(f'taggers/{resource}')
#         else: # stopwords, wordnet
#             nltk.data.find(f'corpora/{resource}')
#         print(f"NLTK resource '{resource}' found.")
#     except nltk.downloader.DownloadError:
#         print(f"NLTK resource '{resource}' not found. Downloading...")
#         nltk.download(resource, quiet=True)
#     except Exception as e: # General catch for other lookup errors (e.g. if path changes)
#          print(f"Could not verify NLTK resource {resource}, attempting download: {e}")
#          try:
#              nltk.download(resource, quiet=True)
#          except Exception as download_e:
#              print(f"Failed to download NLTK resource {resource}: {download_e}")


print("Setup Complete. Necessary modules imported.")
"""
nb['cells'].append(nbf.v4.new_code_cell(cell2_code))

# Cell 3: Configuration (Code)
cell3_code = """\
# --- User Configuration ---

# 1. Specify the path to your document
# IMPORTANT: Replace this with the actual path to YOUR document.
# Example for Linux/macOS: document_path = "/home/user/docs/mydoc.pdf"
# Example for Windows: document_path = r"C:\\Users\\user\\Documents\\mydoc.docx" # Note the double backslashes
document_path = "path/to/your/document.pdf"  # <--- !!! CHANGE THIS TO YOUR FILE !!!

# 2. Define keywords to extract
# Each item is a dictionary with 'keyword' (canonical name) and 'variations' (list of strings to search for)
# The variations will be lemmatized for matching.
target_keywords_config = [
    {'keyword': 'Income', 'variations': ['income', 'total income', 'revenue', 'earnings']},
    {'keyword': 'Balance', 'variations': ['balance', 'net balance', 'account balance', 'total balance']},
    {'keyword': 'Date', 'variations': ['date', 'document date', 'statement date', 'issue date']},
    # Add more keywords as needed, for example:
    # {'keyword': 'InvoiceNumber', 'variations': ['invoice number', 'invoice no', 'inv #']},
    # {'keyword': 'TotalAmount', 'variations': ['total amount', 'total due', 'grand total']},
]

# --- End of User Configuration ---

if document_path == "path/to/your/document.pdf":
    print("WARNING: 'document_path' is set to its default placeholder.")
    print("Please update 'document_path' in the cell above to point to your actual file.")
elif not os.path.exists(document_path):
    print(f"ERROR: Document not found at the specified path: {document_path}")
    print("Please verify the 'document_path' and ensure the file exists.")
else:
    print(f"Configuration loaded. Processing document: {document_path}")
    print(f"Keywords to search for: {[kw['keyword'] for kw in target_keywords_config]}")

"""
nb['cells'].append(nbf.v4.new_code_cell(cell3_code))

# Cell 4: Document Parsing (Code)
cell4_code = """\
extracted_text = ""
# Ensure document_path is defined and valid before proceeding
if 'document_path' not in locals() or document_path == "path/to/your/document.pdf" or not os.path.exists(document_path):
    if 'document_path' in locals() and document_path == "path/to/your/document.pdf":
        extracted_text = "Error: 'document_path' is still set to its default placeholder. Please update it in the Configuration cell."
    elif 'document_path' not in locals():
         extracted_text = "Error: 'document_path' is not defined. Please define it in the Configuration cell."
    else: # File does not exist
        extracted_text = f"Error: Document not found at path '{document_path}'. Please verify the path in the Configuration cell."
    print(extracted_text)
else:
    file_extension = os.path.splitext(document_path)[1].lower()
    print(f"Detected file type: {file_extension}")
    try:
        if file_extension == '.pdf':
            extracted_text = extract_text_from_pdf(document_path, extract_text_from_image)
        elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']:
            extracted_text = extract_text_from_image(document_path)
        elif file_extension == '.txt':
            extracted_text = extract_text_from_txt(document_path)
        elif file_extension == '.docx':
            extracted_text = extract_text_from_docx(document_path)
        else:
            extracted_text = (f"Error: Unsupported file type: {file_extension}. "
                              f"Supported types: PDF, JPG, JPEG, PNG, TIFF, BMP, GIF, TXT, DOCX.")
    except Exception as e:
        extracted_text = f"Error during parsing document '{os.path.basename(document_path)}': {str(e)}"

if "Error:" not in extracted_text:
    print(f"Document parsing complete. Total characters extracted: {len(extracted_text)}")
    # Display a snippet of extracted text (optional, can be long)
    # print("\n--- Extracted Text Snippet (first 500 chars) ---")
    # print(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
    # print("--- End of Snippet ---")
else:
    print(extracted_text) # Print the error message from parsing or path check
"""
nb['cells'].append(nbf.v4.new_code_cell(cell4_code))

# Cell 5: Keyword Extraction (Code)
cell5_code = """\
results_dict = {}
if 'extracted_text' not in locals():
    print("Error: 'extracted_text' variable not found. Document parsing cell might not have been run or failed critically.")
    results_dict = {"error": "extracted_text not available."}
elif "Error:" not in extracted_text and extracted_text.strip(): # Check if text is not empty and no prior error
    try:
        # Ensure target_keywords_config is defined
        if 'target_keywords_config' not in locals():
            results_dict = {"error": "target_keywords_config is not defined. Please check the Configuration cell."}
            print(results_dict["error"])
        else:
            results_dict = extract_keywords_and_values(extracted_text, target_keywords_config)

        print("\n--- Extracted Keywords and Values (Dictionary) ---")
        # Pretty print the dictionary
        if "error" not in results_dict:
            for key, value in results_dict.items():
                print(f"- {key}: {value}")
        elif results_dict["error"]: # Print error if it's there
             print(results_dict["error"])


    except Exception as e:
        error_message = f"Error during keyword extraction: {str(e)}"
        print(error_message)
        results_dict = {"error": error_message}
elif not extracted_text.strip() and "Error:" not in extracted_text: # Text was empty but no error
    print("\nText extracted was empty or whitespace. Skipping keyword extraction.")
    results_dict = {"info": "Text extracted was empty, no keywords to find."}
else: # An error string is in extracted_text from parsing
    print("\nSkipping keyword extraction due to parsing error or invalid configuration.")
    results_dict = {"error": extracted_text} # Use the error from extracted_text
"""
nb['cells'].append(nbf.v4.new_code_cell(cell5_code))

# Cell 6: Format Output as JSON (Code)
cell6_code = """\
final_json_output = ""
try:
    # Ensure results_dict is defined
    if 'results_dict' not in locals():
        results_dict = {"error": "results_dict is not defined. Keyword extraction may have failed or was skipped."}
        print(results_dict["error"])

    final_json_output = format_to_json(results_dict)
    print("\n--- Final Output (JSON) ---")
    print(final_json_output)
except Exception as e:
    error_message = f"Error formatting to JSON: {str(e)}"
    print(error_message)
    # Fallback to manual JSON string for error to avoid circular error if format_to_json itself fails
    final_json_output = f'{{\n  "error": "{error_message.replace("\"", "'")}"\n}}'


# Optional: Save JSON to a file
# output_json_filename = "extracted_data.json"
# if 'document_path' in locals() and document_path != "path/to/your/document.pdf" and os.path.exists(document_path):
#     base_name = os.path.splitext(os.path.basename(document_path))[0]
#     output_json_filename = f"{base_name}_extracted_data.json"
# else:
#     print("\nSkipping save to JSON file because document_path is not valid or not set.")
#
# if 'final_json_output' in locals() and "error" not in results_dict.get("error", "").lower() and results_dict:
#     try:
#         with open(output_json_filename, 'w', encoding='utf-8') as f:
#             f.write(final_json_output)
#         print(f"\nJSON output also saved to: {output_json_filename}")
#     except Exception as e:
#         print(f"\nError saving JSON to file '{output_json_filename}': {str(e)}")
# elif 'output_json_filename' in locals() : # attempt to save only if filename was defined
#      print(f"\nJSON output not saved to '{output_json_filename}' due to previous errors or empty data.")
"""
nb['cells'].append(nbf.v4.new_code_cell(cell6_code))

# Cell 7: Notes on Efficiency for Large PDFs (Markdown)
cell7_md = """## Notes on Efficiency for Large PDFs

Processing very large PDF files (e.g., 50+ pages, especially if they are scanned and require OCR for many pages) can be time-consuming and memory-intensive.

*   **Page-by-Page Processing**: The current `extract_text_from_pdf` function processes page by page. For OCR, each page is converted to an image and then processed. This is inherently sequential for a single call.
*   **Memory**: Storing all extracted text in memory might be an issue for extremely large documents. If you encounter `MemoryError`, consider modifying the scripts to process data in chunks or stream to a file, though this adds complexity.
*   **OCR Speed**: Tesseract OCR speed depends on image quality, resolution, language, and system resources. Pre-processing images (e.g., binarization, noise removal) can sometimes help but is not implemented here.
*   **Timeout**: Very long OCR processes might lead to timeouts in some environments.

**Potential Optimizations (Advanced)**:
*   **Selective OCR**: The current `pdf_parser` already attempts direct text extraction first, which is good. For mixed PDFs, this avoids unnecessary OCR.
*   **Parallel Processing**: For PDFs with many scanned pages, one could parallelize the OCR of individual pages using Python's `multiprocessing` or `concurrent.futures` libraries. This would require changes to `pdf_parser.py` to:
    *   Split the PDF into individual pages (or ranges of pages).
    *   Create a pool of worker processes.
    *   Each worker would OCR its assigned page(s).
    *   Collect and correctly order the results.
*   **Image Pre-processing for OCR**: For scanned documents, image pre-processing like deskewing, binarization, or noise removal might improve OCR accuracy and speed. Libraries like OpenCV can be used for this.
*   **Downsampling High-Resolution Images**: If scanned pages are at a very high resolution (e.g., >300-600 DPI), downsampling them before OCR might speed up the process with minimal accuracy loss. This needs careful tuning.
*   **Alternative OCR Engines**: While Tesseract is powerful and free, other engines (some commercial, some cloud-based like Google Cloud Vision AI, AWS Textract) might offer better performance, accuracy, or language support for specific use cases.
*   **Caching**: If the same documents are processed repeatedly, caching extracted text could save significant time.

This notebook provides a foundational approach. For production-scale processing of very large or complex documents, implementing some of these optimizations and conducting thorough performance testing would be crucial.
"""
nb['cells'].append(nbf.v4.new_markdown_cell(cell7_md))

# Write the notebook to a file
notebook_filename = 'document_parser_and_keyword_extractor.ipynb'
try:
    with open(notebook_filename, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)
    print(f"Jupyter Notebook '{notebook_filename}' generated successfully in the current directory: {os.getcwd()}")
except Exception as e:
    print(f"Error writing notebook file '{notebook_filename}': {str(e)}")
# Trailing comments removed. The script should end after the print statement.
