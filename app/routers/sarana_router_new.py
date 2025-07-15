from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import os
import shutil
import uuid

# Impor layanan Sarana dan model Pydantic
from ..services import sarana_service
from ..models.api_models import SaranaParseDocumentResponse

router = APIRouter()

# Direktori temporer untuk menyimpan file upload
TEMP_UPLOAD_DIR_SARANA = "temp_sarana_uploads" 
os.makedirs(TEMP_UPLOAD_DIR_SARANA, exist_ok=True)

# Health check endpoint
@router.get("/health", summary="Sarana Health Check")
async def sarana_health_check():
    """Health check untuk module Sarana"""
    return {"status": "ok", "module": "Sarana", "message": "OCR & NLP module is running"}

@router.post("/document/parse", summary="Parse Financial Documents", response_model=SaranaParseDocumentResponse)
async def parse_document_endpoint(
    file: UploadFile = File(..., description="File dokumen yang akan di-parse"),
    file_type: Optional[str] = Form(None, description="Tipe file eksplisit"),
    ocr_engine: str = Form('tesseract', description="Mesin OCR: 'tesseract', 'easyocr', 'ollama'"),
    pdf_parsing_method: str = Form('pymupdf', description="Metode parsing PDF: 'pymupdf', 'pdfplumber'"),
    output_format: str = Form('text', description="Format output: 'text' atau 'structured_json'"),
    jenis_pengaju: str = Form('korporat', description="Jenis pengaju: 'korporat' atau 'individu'"),
    # Parameter tambahan untuk Ollama
    ollama_json_prompt_template: Optional[str] = Form(None, description="Template prompt JSON kustom untuk Ollama"),
    ollama_vision_model_name: str = Form("llama3.2-vision", description="Model vision Ollama"),
    ollama_llm_model_json_name: str = Form("llama3", description="Model LLM Ollama untuk ekstraksi JSON"),
    ollama_api_base_url_param: Optional[str] = Form(None, description="Base URL Ollama API kustom")
):
    """
    Endpoint untuk mem-parsing dokumen keuangan menggunakan modul Sarana.
    Mendukung berbagai format file dan opsi parsing.
    """
    # Buat nama file unik
    original_filename = file.filename if file.filename else "unknown_file"
    safe_filename_base = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in original_filename)
    unique_filename = f"{uuid.uuid4().hex}_{safe_filename_base}"
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR_SARANA, unique_filename)
    
    try:
        # Simpan file yang di-upload ke direktori temporer
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Panggil layanan Sarana
        parsing_result_dict = sarana_service.parse_document_sarana(
            file_path=temp_file_path,
            file_type=file_type,
            ocr_engine=ocr_engine,
            pdf_parsing_method=pdf_parsing_method,
            output_format=output_format,
            jenis_pengaju=jenis_pengaju,
            ollama_json_prompt_template=ollama_json_prompt_template,
            ollama_vision_model_name=ollama_vision_model_name,
            ollama_llm_model_json_name=ollama_llm_model_json_name,
            ollama_api_base_url_param=ollama_api_base_url_param
        )

        if parsing_result_dict.get("error"):
            raise HTTPException(status_code=422, detail=f"Error dalam parsing dokumen: {parsing_result_dict['error']}")

        return SaranaParseDocumentResponse(**parsing_result_dict)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Bersihkan file temporer
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.post("/ocr/upload", summary="OCR File Upload")
async def ocr_upload_endpoint(
    file: UploadFile = File(..., description="File untuk OCR (gambar/PDF)"),
    ocr_engine: str = Form('tesseract', description="Mesin OCR: 'tesseract', 'easyocr', 'ollama'")
):
    """
    Endpoint khusus untuk OCR file upload.
    """
    original_filename = file.filename if file.filename else "unknown_file"
    safe_filename_base = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in original_filename)
    unique_filename = f"{uuid.uuid4().hex}_{safe_filename_base}"
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR_SARANA, unique_filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Simplified OCR processing
        parsing_result = sarana_service.parse_document_sarana(
            file_path=temp_file_path,
            ocr_engine=ocr_engine,
            output_format='text'
        )

        if parsing_result.get("error"):
            raise HTTPException(status_code=422, detail=f"OCR Error: {parsing_result['error']}")

        return {
            "status": "success",
            "filename": original_filename,
            "ocr_engine": ocr_engine,
            "extracted_text": parsing_result.get("extracted_text", ""),
            "processing_time": parsing_result.get("processing_time_seconds", 0)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing error: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.post("/extract", summary="Extract Data from Document")
async def extract_data_endpoint(
    file: UploadFile = File(..., description="File untuk ekstraksi data"),
    extraction_type: str = Form('financial', description="Tipe ekstraksi: 'financial', 'general'"),
    output_format: str = Form('structured_json', description="Format output: 'text' atau 'structured_json'")
):
    """
    Endpoint untuk ekstraksi data terstruktur dari dokumen.
    """
    original_filename = file.filename if file.filename else "unknown_file"
    safe_filename_base = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in original_filename)
    unique_filename = f"{uuid.uuid4().hex}_{safe_filename_base}"
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR_SARANA, unique_filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Data extraction processing
        extraction_result = sarana_service.parse_document_sarana(
            file_path=temp_file_path,
            output_format=output_format,
            jenis_pengaju='korporat' if extraction_type == 'financial' else 'individu'
        )

        if extraction_result.get("error"):
            raise HTTPException(status_code=422, detail=f"Extraction Error: {extraction_result['error']}")

        return {
            "status": "success",
            "filename": original_filename,
            "extraction_type": extraction_type,
            "extracted_data": extraction_result.get("extracted_text", ""),
            "processing_time": extraction_result.get("processing_time_seconds", 0)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data extraction error: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
