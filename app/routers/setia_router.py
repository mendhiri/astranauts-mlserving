from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
import os

# Impor layanan Setia dan model Pydantic
from ..services import setia_service
from ..models.api_models import SetiaRiskIntelligenceRequest, SetiaRiskIntelligenceResponse

router = APIRouter()

# Health check endpoint
@router.get("/health", summary="Setia Health Check")
async def setia_health_check():
    """Health check untuk module Setia"""
    return {"status": "ok", "module": "Setia", "message": "Sentiment analysis module is running"}

@router.post("/sentiment", summary="Sentiment Analysis", response_model=SetiaRiskIntelligenceResponse)
async def sentiment_analysis_endpoint(
    request_data: SetiaRiskIntelligenceRequest
):
    """
    Endpoint untuk analisis sentimen menggunakan modul Setia.
    Menggabungkan analisis berita terkini dengan data risiko industri.
    """
    actual_gcs_bucket_name = None
    if request_data.use_gcs_for_risk_data:
        actual_gcs_bucket_name = request_data.gcs_bucket_name_override or os.environ.get("SETIA_RISK_DATA_BUCKET_NAME")

    try:
        analysis_result_dict = setia_service.get_setia_risk_intelligence(
            applicant_name=request_data.applicant_name,
            industry_main=request_data.industry_main,
            industry_sub=request_data.industry_sub,
            use_gcs_for_risk_data=request_data.use_gcs_for_risk_data,
            gcs_bucket_name=actual_gcs_bucket_name
        )

        if analysis_result_dict.get("error"):
            raise HTTPException(status_code=503, detail=f"Kesalahan pada layanan Setia: {analysis_result_dict['error']}")
            
        return SetiaRiskIntelligenceResponse(**analysis_result_dict)
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/news", summary="News Monitoring and Analysis")
async def news_monitoring_endpoint(
    request_data: SetiaRiskIntelligenceRequest
):
    """
    Endpoint khusus untuk monitoring dan analisis berita.
    """
    try:
        analysis_result = setia_service.get_setia_risk_intelligence(
            applicant_name=request_data.applicant_name,
            industry_main=request_data.industry_main,
            industry_sub=request_data.industry_sub,
            use_gcs_for_risk_data=False  # Focus only on news analysis
        )

        if analysis_result.get("error"):
            raise HTTPException(status_code=503, detail=f"Error: {analysis_result['error']}")
            
        # Return only news-related data
        return {
            "applicant_name": analysis_result.get("applicantName"),
            "grounded_summary": analysis_result.get("groundedSummary"),
            "overall_sentiment": analysis_result.get("overallSentiment"),
            "key_issues": analysis_result.get("keyIssues"),
            "supporting_sources": analysis_result.get("supportingSources"),
            "analysis_timestamp": analysis_result.get("analysisTimestamp")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News analysis error: {str(e)}")

@router.post("/external-risk", summary="External Risk Assessment")
async def external_risk_assessment_endpoint(
    request_data: SetiaRiskIntelligenceRequest
):
    """
    Endpoint untuk penilaian risiko eksternal berdasarkan data industri.
    """
    try:
        analysis_result = setia_service.get_setia_risk_intelligence(
            applicant_name=request_data.applicant_name,
            industry_main=request_data.industry_main,
            industry_sub=request_data.industry_sub,
            use_gcs_for_risk_data=request_data.use_gcs_for_risk_data,
            gcs_bucket_name=request_data.gcs_bucket_name_override or os.environ.get("SETIA_RISK_DATA_BUCKET_NAME")
        )

        if analysis_result.get("error"):
            raise HTTPException(status_code=503, detail=f"Error: {analysis_result['error']}")
            
        # Return only external risk data
        return {
            "applicant_name": analysis_result.get("applicantName"),
            "industry_sector_outlook": analysis_result.get("industrySectorOutlook"),
            "overall_sentiment": analysis_result.get("overallSentiment"),
            "analysis_timestamp": analysis_result.get("analysisTimestamp")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"External risk assessment error: {str(e)}")
        # print(f"ERROR in Setia router (/risk-intelligence): {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal yang tidak terduga saat analisis Setia: {str(e)}")


@router.get("/health", summary="Health Check Setia Router")
async def setia_health():
    """Cek kesehatan untuk router Setia."""
    return {"status": "ok", "message": "Setia router is healthy"}
