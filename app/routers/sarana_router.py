from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import os
import shutil # Untuk menyimpan file upload temporer
import uuid

# Impor layanan Sarana dan model Pydantic
from ..services import sarana_service
from ..models.api_models import SaranaParseDocumentResponse

router = APIRouter()

# Direktori temporer untuk menyimpan file upload
# Sebaiknya ini dikonfigurasi atau menggunakan library tempfile Python untuk keamanan yang lebih baik
# Untuk sekarang, kita buat di root proyek agar mudah diakses dan dibersihkan.
TEMP_UPLOAD_DIR_SARANA = "temp_sarana_uploads" 
os.makedirs(TEMP_UPLOAD_DIR_SARANA, exist_ok=True)
# Subdirektori untuk halaman PDF yang di-OCR juga dibuat oleh sarana_service jika menggunakan PyMuPDF
# SARANA_PDF_OCR_TEMP_DIR = os.path.join(TEMP_UPLOAD_DIR_SARANA, "pdf_ocr_pages")
# os.makedirs(SARANA_PDF_OCR_TEMP_DIR, exist_ok=True)


@router.post("/parse-document", summary="Parse Dokumen Keuangan Sarana", response_model=SaranaParseDocumentResponse)
async def parse_document_endpoint(
    file: UploadFile = File(..., description="File dokumen yang akan di-parse (PDF, DOCX, TXT, XLSX, CSV, PNG, JPG, dll.)."),
    file_type: Optional[str] = Form(None, description="Tipe file eksplisit (misal, 'pdf', 'png'). Jika None, akan dideteksi dari ekstensi."),
    ocr_engine: str = Form('tesseract', description="Mesin OCR untuk gambar/PDF: 'tesseract', 'easyocr', 'ollama'."),
    pdf_parsing_method: str = Form('pymupdf', description="Metode parsing PDF: 'pymupdf', 'pdfplumber'."),
    output_format: str = Form('text', description="Format output: 'text' atau 'structured_json' (structured_json hanya untuk gambar via ollama)."),
    jenis_pengaju: str = Form('korporat', description="Jenis pengaju: 'korporat' atau 'individu'."),
    # Parameter tambahan untuk Ollama jika output_format='structured_json' untuk gambar
    ollama_json_prompt_template: Optional[str] = Form(None, description="Template prompt JSON kustom untuk Ollama (jika output structured_json dari gambar)."),
    ollama_vision_model_name: str = Form("llama3.2-vision", description="Model vision Ollama."),
    ollama_llm_model_json_name: str = Form("llama3", description="Model LLM Ollama untuk ekstraksi JSON."),
    ollama_api_base_url_param: Optional[str] = Form(None, description="Base URL Ollama API kustom.")
):
    """
    Endpoint untuk mem-parsing dokumen keuangan menggunakan modul Sarana.
    Mendukung berbagai format file dan opsi parsing.
    """
    # Buat nama file unik untuk menghindari konflik jika ada upload bersamaan
    # atau jika nama file asli mengandung karakter yang tidak aman.
    original_filename = file.filename if file.filename else "unknown_file"
    safe_filename_base = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in original_filename)
    unique_filename = f"{uuid.uuid4().hex}_{safe_filename_base}"
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR_SARANA, unique_filename)
    
    try:
        # Simpan file yang di-upload ke direktori temporer
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Panggil layanan Sarana dengan path file temporer
        parsed_result_dict = sarana_service.parse_financial_document(
            file_path=temp_file_path,
            file_type=file_type,
            ocr_engine_for_images_and_pdf=ocr_engine,
            pdf_parsing_method=pdf_parsing_method,
            output_format=output_format,
            jenis_pengaju=jenis_pengaju, # Teruskan parameter jenis_pengaju
            ollama_prompt_for_json_extraction=ollama_json_prompt_template,
            ollama_vision_model=ollama_vision_model_name,
            ollama_llm_model_for_json=ollama_llm_model_json_name,
            ollama_api_base_url=ollama_api_base_url_param
            # sarana_cache_dir bisa ditambahkan jika ingin mengonfigurasi dari API
        )

        if parsed_result_dict.get("error_parsing"):
             raise HTTPException(status_code=422, detail=f"Error parsing dokumen: {parsed_result_dict['error_parsing']}")

        # Konversi hasil dictionary ke model Pydantic SaranaParseDocumentResponse
        return SaranaParseDocumentResponse(**parsed_result_dict)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        # print(f"ERROR in Sarana router (/parse-document): {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal saat parsing dokumen Sarana: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e_remove:
                print(f"Warning (SaranaRouter): Gagal menghapus file temporer {temp_file_path}: {e_remove}")
        if hasattr(file, 'file') and file.file and not file.file.closed:
            file.file.close()


@router.get("/health", summary="Health Check Sarana Router")
async def sarana_health():
    """Cek kesehatan untuk router Sarana."""
    return {"status": "ok", "message": "Sarana router is healthy"}
