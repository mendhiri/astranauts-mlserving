from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class FinancialDataInput(BaseModel):
    """
    Model untuk input data keuangan per periode.
    Menggunakan Dict[str, Any] untuk fleksibilitas item keuangan.
    Contoh item yang diharapkan ada di dalam dict (lihat dokumentasi Prabu service).
    """
    data: Dict[str, Any] = Field(..., example={"Pendapatan bersih": 1000, "Jumlah aset": 2000, "dll...": 0})

class PrabuAnalysisRequest(BaseModel):
    data_t: Dict[str, Any] = Field(..., example={"Pendapatan bersih": 1000, "Jumlah aset": 2000, "Jumlah liabilitas": 500, "Laba tahun berjalan": 100, "Jumlah aset lancar": 800, "Jumlah liabilitas jangka pendek": 300, "Laba ditahan": 400, "Laba sebelum pajak penghasilan": 150, "Beban bunga": 10, "Jumlah ekuitas":1500, "Piutang usaha":200, "Laba bruto":300, "Aset tetap bruto":1000, "Beban penyusutan":50, "Beban penjualan":70, "Beban administrasi dan umum":80, "Arus kas bersih yang diperoleh dari aktivitas operasi":120, "Aset tetap":900})
    data_t_minus_1: Optional[Dict[str, Any]] = Field(None, example={"Pendapatan bersih": 800, "Jumlah aset": 1800, "Laba tahun berjalan": 80, "Piutang usaha":150, "Laba bruto":250, "Aset tetap bruto":900, "Beban penyusutan":40, "Beban penjualan":60, "Beban administrasi dan umum":70, "Arus kas bersih yang diperoleh dari aktivitas operasi":100, "Aset tetap":800, "Jumlah aset lancar": 700, "Jumlah liabilitas jangka pendek": 250, "Jumlah liabilitas": 400, "Jumlah ekuitas":1400})
    is_public_company: bool = True
    market_value_equity_manual: Optional[float] = None
    altman_model_type_override: Optional[str] = Field(None, pattern=r"^(public_manufacturing|private_manufacturing|non_manufacturing_or_emerging_markets)$")

class PrabuRatios(BaseModel):
    # Contoh, bisa sangat detail tergantung output prabu_service
    X1: Optional[float] = Field(None, alias="X1 (Working Capital / Total Assets)")
    X2: Optional[float] = Field(None, alias="X2 (Retained Earnings / Total Assets)")
    # ... tambahkan rasio lain dari Altman, Beneish, Common Ratios
    model_type: Optional[str] = None
    interpretation_zones: Optional[Dict[str, str]] = None
    error: Optional[str] = None

    class Config:
        populate_by_name = True # Mengizinkan penggunaan alias

class PrabuAltmanAnalysis(BaseModel):
    z_score: Optional[float] = None
    ratios: Optional[Any] = None # Bisa PrabuRatios atau Dict
    interpretation: Optional[str] = None
    zone: Optional[str] = None
    model_used: Optional[str] = None
    error: Optional[str] = None

class PrabuBeneishAnalysis(BaseModel):
    m_score: Optional[float] = None
    ratios: Optional[Dict[str, float]] = None
    interpretation: Optional[str] = None
    error: Optional[str] = None

class PrabuCommonRatios(BaseModel):
    debt_to_equity_ratio: Optional[float] = Field(None, alias="Debt-to-Equity Ratio")
    current_ratio: Optional[float] = Field(None, alias="Current Ratio")
    
    error: Optional[str] = None
    
    class Config:
        populate_by_name = True

class PrabuCreditRiskPrediction(BaseModel):
    credit_risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    underlying_ratios: Optional[Dict[str, Optional[float]]] = None # Dibuat lebih eksplisit
    altman_z_score_used: Optional[float] = None
    beneish_m_score_used: Optional[float] = None
    error: Optional[str] = None


class PrabuAnalysisResponse(BaseModel):
    altman_z_score_analysis: PrabuAltmanAnalysis
    beneish_m_score_analysis: PrabuBeneishAnalysis
    common_financial_ratios: Any # Bisa PrabuCommonRatios atau Dict jika ada error
    credit_risk_prediction: PrabuCreditRiskPrediction
    error: Optional[str] = None # Error global dari analisis Prabu

# Untuk Sarana, inputnya adalah UploadFile, jadi tidak perlu model Pydantic khusus untuk input file.
# Outputnya adalah dictionary, bisa kita definisikan jika strukturnya tetap.
class SaranaKeywordExtraction(BaseModel):
    t: Optional[Any] = None
    t_minus_1: Optional[Any] = None

class SaranaParseDocumentResponse(BaseModel):
    nama_file: str
    info_parsing: str
    error_parsing: Optional[str] = None
    teks_ekstrak_mentah: Optional[str] = None
    tahun_pelaporan_terdeteksi: Optional[str] = None
    pengali_global_terdeteksi: Optional[float] = None
    # hasil_ekstraksi_kata_kunci bisa Dict[str, SaranaKeywordExtraction] atau Dict[str, Dict]
    hasil_ekstraksi_kata_kunci: Optional[Dict[str, SaranaKeywordExtraction]] = None
    # Untuk output_format='structured_json'
    hasil_ekstraksi_terstruktur: Optional[Dict[str, Any]] = None


# Untuk Setia
class SetiaRiskIntelligenceRequest(BaseModel):
    applicant_name: str = Field(..., example="PT Contoh Tbk")
    industry_main: Optional[str] = Field(None, example="Keuangan")
    industry_sub: Optional[str] = Field(None, example="Perbankan (BUKU IV/III)")
    use_gcs_for_risk_data: bool = False
    gcs_bucket_name_override: Optional[str] = None

class SetiaSupportingSource(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None

class SetiaRiskIntelligenceResponse(BaseModel):
    groundedSummary: Optional[str] = None
    overallSentiment: Optional[str] = None
    keyIssues: Optional[List[str]] = []
    supportingSources: Optional[List[SetiaSupportingSource]] = []
    industrySectorOutlook: Optional[str] = None
    lastUpdateTimestamp: datetime.datetime
    error: Optional[str] = None

# Tambahkan __all__ untuk kontrol impor jika diperlukan
__all__ = ["FinancialDataInput", "PrabuAnalysisRequest", "PrabuAnalysisResponse", "SaranaParseDocumentResponse", "SetiaRiskIntelligenceRequest", "SetiaRiskIntelligenceResponse"]
