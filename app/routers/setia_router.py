from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
import os # Diperlukan untuk os.environ.get

# Impor layanan Setia dan model Pydantic
from ..services import setia_service
from ..models.api_models import SetiaRiskIntelligenceRequest, SetiaRiskIntelligenceResponse

router = APIRouter()

@router.post("/risk-intelligence", summary="Analisis Intelijen Risiko Setia", response_model=SetiaRiskIntelligenceResponse)
async def get_risk_intelligence_endpoint(
    request_data: SetiaRiskIntelligenceRequest
):
    """
    Endpoint untuk mendapatkan analisis intelijen risiko menggunakan modul Setia.
    Menggabungkan analisis berita terkini (grounded AI) dengan data risiko industri.

    Menerima parameter dalam body request sesuai model `SetiaRiskIntelligenceRequest`.
    """
    actual_gcs_bucket_name = None
    if request_data.use_gcs_for_risk_data:
        actual_gcs_bucket_name = request_data.gcs_bucket_name_override or os.environ.get("SETIA_RISK_DATA_BUCKET_NAME")
        # Layanan Setia akan menangani jika actual_gcs_bucket_name tetap None meskipun use_gcs_for_risk_data True.

    try:
        # Panggil fungsi utama dari layanan Setia
        analysis_result_dict = setia_service.get_setia_risk_intelligence(
            applicant_name=request_data.applicant_name,
            industry_main=request_data.industry_main,
            industry_sub=request_data.industry_sub,
            use_gcs_for_risk_data=request_data.use_gcs_for_risk_data,
            gcs_bucket_name=actual_gcs_bucket_name
        )

        # Periksa apakah layanan mengembalikan error spesifik yang ingin kita tangani sebagai HTTP error
        if analysis_result_dict.get("error"):
            # Contoh: Jika error karena Vertex AI tidak tersedia atau masalah konfigurasi GCS
            # Kita bisa menggunakan status kode yang berbeda tergantung jenis errornya.
            # 503 Service Unavailable jika layanan eksternal tidak siap.
            # 422 Unprocessable Entity jika input valid tapi tidak bisa diproses karena kondisi tertentu.
            raise HTTPException(status_code=503, detail=f"Kesalahan pada layanan Setia: {analysis_result_dict['error']}")
            
        # Konversi hasil dictionary ke model Pydantic SetiaRiskIntelligenceResponse
        return SetiaRiskIntelligenceResponse(**analysis_result_dict)
        
    except HTTPException as http_exc: # Re-raise HTTPException yang sudah ada
        raise http_exc
    except Exception as e:
        # Tangani error tak terduga lainnya
        # print(f"ERROR in Setia router (/risk-intelligence): {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal yang tidak terduga saat analisis Setia: {str(e)}")


@router.get("/health", summary="Health Check Setia Router")
async def setia_health():
    """Cek kesehatan untuk router Setia."""
    return {"status": "ok", "message": "Setia router is healthy"}
