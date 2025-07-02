from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional

# Impor layanan Prabu dan model Pydantic
from ..services import prabu_service 
from ..models.api_models import PrabuAnalysisRequest, PrabuAnalysisResponse

router = APIRouter()

@router.post("/analyze", summary="Analisis Risiko Keuangan Prabu", response_model=PrabuAnalysisResponse)
async def analyze_financial_data(
    request_data: PrabuAnalysisRequest
):
    """
    Endpoint untuk melakukan analisis keuangan lengkap menggunakan modul Prabu.
    Termasuk skor Altman Z, Beneish M, rasio keuangan umum, dan prediksi risiko kredit.

    Menerima data keuangan dalam body request sesuai model `PrabuAnalysisRequest`.
    """
    try:
        # Panggil fungsi utama dari layanan Prabu
        analysis_result_dict = prabu_service.run_prabu_analysis(
            data_t=request_data.data_t,
            data_t_minus_1=request_data.data_t_minus_1,
            is_public_company=request_data.is_public_company,
            market_value_equity_manual=request_data.market_value_equity_manual,
            altman_model_type_override=request_data.altman_model_type_override,
            sector=request_data.sector # Tambahkan sector
        )
        
        # Jika layanan Prabu mengembalikan dictionary yang mengandung 'error' di level atas,
        # ini menandakan masalah pada keseluruhan proses analisis di layanan.
        if analysis_result_dict.get("error"):
            # Kita bisa memilih untuk mengembalikan HTTP 500 atau 422 tergantung sifat errornya.
            # Jika error karena input tidak valid setelah validasi Pydantic (seharusnya tidak terjadi di sini), itu 422.
            # Jika error karena proses internal di layanan, 500 lebih cocok.
            raise HTTPException(status_code=500, detail=f"Kesalahan pada layanan Prabu: {analysis_result_dict['error']}")

        # Konversi hasil dictionary ke model Pydantic PrabuAnalysisResponse
        # Ini juga akan memvalidasi apakah output dari service sesuai dengan skema response.
        # Pydantic akan mencoba mencocokkan field berdasarkan nama.
        # Perlu dipastikan bahwa keys dalam analysis_result_dict cocok dengan field di PrabuAnalysisResponse
        # dan sub-modelnya (PrabuAltmanAnalysis, dll.)
        # Jika ada error parsial (misal, Altman error tapi Beneish OK), ini akan ditangani di dalam sub-model.
        return PrabuAnalysisResponse(**analysis_result_dict)

    except HTTPException as http_exc: # Re-raise HTTPException yang sudah ada
        raise http_exc
    except Exception as e:
        # Tangani error tak terduga lainnya
        # print(f"ERROR in Prabu router: {type(e).__name__} - {e}") # Untuk logging di server
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal yang tidak terduga saat analisis Prabu: {str(e)}")


@router.get("/health", summary="Health Check Prabu Router")
async def prabu_health():
    """Cek kesehatan untuk router Prabu."""
    return {"status": "ok", "message": "Prabu router is healthy"}
