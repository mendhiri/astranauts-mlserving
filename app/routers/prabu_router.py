from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional

# Impor layanan Prabu dan model Pydantic
from ..services import prabu_service 
from ..models.api_models import PrabuAnalysisRequest, PrabuAnalysisResponse

router = APIRouter()

# Health check endpoint
@router.get("/health", summary="Prabu Health Check")
async def prabu_health_check():
    """Health check untuk module Prabu"""
    return {"status": "ok", "module": "Prabu", "message": "Credit scoring module is running"}

@router.post("/calculate", summary="Comprehensive Financial Analysis", response_model=PrabuAnalysisResponse)
async def calculate_comprehensive_score(
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
            sector=request_data.sector
        )
        
        if analysis_result_dict.get("error"):
            raise HTTPException(status_code=500, detail=f"Kesalahan pada layanan Prabu: {analysis_result_dict['error']}")

        return PrabuAnalysisResponse(**analysis_result_dict)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/altman-z", summary="Altman Z-Score Analysis")
async def calculate_altman_z_score(
    request_data: PrabuAnalysisRequest
):
    """
    Endpoint khusus untuk menghitung Altman Z-Score saja.
    """
    try:
        # Extract only Altman Z analysis
        analysis_result = prabu_service.run_prabu_analysis(
            data_t=request_data.data_t,
            data_t_minus_1=request_data.data_t_minus_1,
            is_public_company=request_data.is_public_company,
            market_value_equity_manual=request_data.market_value_equity_manual,
            altman_model_type_override=request_data.altman_model_type_override,
            sector=request_data.sector
        )
        
        if analysis_result.get("error"):
            raise HTTPException(status_code=500, detail=f"Error: {analysis_result['error']}")
            
        # Return only Altman Z analysis
        return {
            "altman_analysis": analysis_result.get("altman_analysis"),
            "applicant_name": analysis_result.get("applicant_name"),
            "timestamp": analysis_result.get("timestamp")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/m-score", summary="Beneish M-Score Analysis")
async def calculate_beneish_m_score(
    request_data: PrabuAnalysisRequest
):
    """
    Endpoint khusus untuk menghitung Beneish M-Score saja.
    """
    try:
        analysis_result = prabu_service.run_prabu_analysis(
            data_t=request_data.data_t,
            data_t_minus_1=request_data.data_t_minus_1,
            is_public_company=request_data.is_public_company,
            market_value_equity_manual=request_data.market_value_equity_manual,
            altman_model_type_override=request_data.altman_model_type_override,
            sector=request_data.sector
        )
        
        if analysis_result.get("error"):
            raise HTTPException(status_code=500, detail=f"Error: {analysis_result['error']}")
            
        # Return only Beneish M analysis
        return {
            "beneish_analysis": analysis_result.get("beneish_analysis"),
            "applicant_name": analysis_result.get("applicant_name"),
            "timestamp": analysis_result.get("timestamp")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/metrics", summary="Financial Ratios and Metrics")
async def calculate_financial_metrics(
    request_data: PrabuAnalysisRequest
):
    """
    Endpoint khusus untuk menghitung rasio keuangan dan metrik saja.
    """
    try:
        analysis_result = prabu_service.run_prabu_analysis(
            data_t=request_data.data_t,
            data_t_minus_1=request_data.data_t_minus_1,
            is_public_company=request_data.is_public_company,
            market_value_equity_manual=request_data.market_value_equity_manual,
            altman_model_type_override=request_data.altman_model_type_override,
            sector=request_data.sector
        )
        
        if analysis_result.get("error"):
            raise HTTPException(status_code=500, detail=f"Error: {analysis_result['error']}")
            
        # Return only financial ratios
        return {
            "financial_ratios": analysis_result.get("financial_ratios"),
            "applicant_name": analysis_result.get("applicant_name"),
            "timestamp": analysis_result.get("timestamp")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
        # print(f"ERROR in Prabu router: {type(e).__name__} - {e}") # Untuk logging di server
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal yang tidak terduga saat analisis Prabu: {str(e)}")


@router.get("/health", summary="Health Check Prabu Router")
async def prabu_health():
    """Cek kesehatan untuk router Prabu."""
    return {"status": "ok", "message": "Prabu router is healthy"}
