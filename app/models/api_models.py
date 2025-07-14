from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import datetime


class FinancialDataInput(BaseModel):
    """
    Model untuk input data keuangan per periode.
    Menggunakan Dict[str, Any] untuk fleksibilitas item keuangan.
    Contoh item yang diharapkan ada di dalam dict (lihat dokumentasi Prabu service).
    """
    data: Dict[str, Any] = Field(..., example={
                                 "Pendapatan bersih": 1000, "Jumlah aset": 2000, "dll...": 0})


class PrabuAnalysisRequest(BaseModel):
    data_t: Dict[str, Any] = Field(..., example={"Pendapatan bersih": 1000, "Jumlah aset": 2000, "Jumlah liabilitas": 500, "Laba/rugi tahun berjalan": 100, "Jumlah aset lancar": 800, "Jumlah liabilitas jangka pendek": 300, "Laba ditahan": 400, "Laba/rugi sebelum pajak penghasilan": 150,
                                   "Beban bunga": 10, "Jumlah ekuitas": 1500, "Piutang usaha": 200, "Laba bruto": 300, "Aset tetap bruto": 1000, "Beban penyusutan": 50, "Beban penjualan": 70, "Beban administrasi dan umum": 80, "Arus kas bersih yang diperoleh dari aktivitas operasi": 120, "Aset tetap": 900})
    data_t_minus_1: Optional[Dict[str, Any]] = Field(None, example={"Pendapatan bersih": 800, "Jumlah aset": 1800, "Laba/rugi tahun berjalan": 80, "Piutang usaha": 150, "Laba bruto": 250, "Aset tetap bruto": 900, "Beban penyusutan": 40, "Beban penjualan": 60,
                                                     "Beban administrasi dan umum": 70, "Arus kas bersih yang diperoleh dari aktivitas operasi": 100, "Aset tetap": 800, "Jumlah aset lancar": 700, "Jumlah liabilitas jangka pendek": 250, "Jumlah liabilitas": 400, "Jumlah ekuitas": 1400})
    is_public_company: bool = True
    market_value_equity_manual: Optional[float] = None
    altman_model_type_override: Optional[str] = Field(
        None, pattern=r"^(public_manufacturing|private_manufacturing|non_manufacturing_or_emerging_markets)$"),
    sector: Optional[str] = Field(
        None, example="Pertambangan", description="Sektor industri perusahaan untuk pemilihan model ML jika relevan")


class PrabuRatios(BaseModel):
    """Model untuk rasio-rasio yang digunakan dalam Altman Z-Score."""
    X1: Optional[float] = Field(
        None, alias="X1 (Working Capital / Total Assets)", description="Modal Kerja / Total Aset")
    X2: Optional[float] = Field(
        None, alias="X2 (Retained Earnings / Total Assets)", description="Laba Ditahan / Total Aset")
    X3: Optional[float] = Field(
        None, alias="X3 (EBIT / Total Assets)", description="EBIT / Total Aset")
    X4: Optional[float] = Field(None, alias="X4 (Market Value of Equity / Total Liabilities)",
                                description="Nilai Pasar Ekuitas / Total Liabilitas (atau Nilai Buku Ekuitas sbg proxy)")
    X4_note: Optional[str] = Field(
        None, description="Catatan terkait penggunaan Nilai Pasar atau Buku untuk X4")
    X5: Optional[float] = Field(None, alias="X5 (Sales / Total Assets)",
                                description="Penjualan / Total Aset (tidak digunakan di semua model Altman)")
    model_type: Optional[str] = Field(
        None, description="Tipe model Altman Z-Score yang digunakan")
    interpretation_zones: Optional[Dict[str, str]] = Field(
        None, description="Zona interpretasi skor untuk model yang digunakan")
    error: Optional[str] = Field(
        None, description="Pesan error jika perhitungan rasio gagal")

    class Config:
        populate_by_name = True  # Mengizinkan penggunaan alias


class PrabuAltmanAnalysis(BaseModel):
    """Hasil analisis Altman Z-Score."""
    z_score: Optional[float] = Field(None, description="Nilai Altman Z-Score")
    ratios: Optional[PrabuRatios] = Field(
        None, description="Rincian rasio Altman yang digunakan")  # Diubah dari Any ke PrabuRatios
    interpretation: Optional[str] = Field(
        None, description="Interpretasi hasil skor Z")
    zone: Optional[str] = Field(
        None, description="Zona risiko berdasarkan skor Z (Safe, Grey, Distress)")
    model_used: Optional[str] = Field(
        None, description="Model Altman Z-Score yang diaplikasikan")
    error: Optional[str] = Field(
        None, description="Pesan error jika analisis Altman gagal")


class PrabuBeneishAnalysis(BaseModel):
    """Hasil analisis Beneish M-Score."""
    m_score: Optional[float] = Field(None, description="Nilai Beneish M-Score")
    ratios: Optional[Dict[str, Optional[float]]] = Field(
        None, description="Rincian rasio Beneish (DSRI, GMI, dll.)")  # Float bisa None jika gagal hitung
    interpretation: Optional[str] = Field(
        None, description="Interpretasi hasil skor M (indikasi manipulasi)")
    error: Optional[str] = Field(
        None, description="Pesan error jika analisis Beneish gagal")


class PrabuCommonRatios(BaseModel):
    """Kumpulan rasio keuangan umum."""
    debt_to_equity_ratio: Optional[float] = Field(
        None, alias="Debt-to-Equity Ratio", description="Total Liabilitas / Total Ekuitas")
    current_ratio: Optional[float] = Field(
        None, alias="Current Ratio", description="Aset Lancar / Liabilitas Jangka Pendek")
    interest_coverage_ratio: Optional[float] = Field(
        None, alias="Interest Coverage Ratio", description="EBIT / Beban Bunga")
    net_profit_margin: Optional[float] = Field(
        None, alias="Net Profit Margin", description="Laba Bersih / Pendapatan Bersih")
    gross_profit_margin: Optional[float] = Field(
        None, alias="Gross Profit Margin", description="Laba Bruto / Pendapatan Bersih")
    debt_ratio: Optional[float] = Field(
        None, alias="Debt Ratio", description="Total Liabilitas / Total Aset")
    roe: Optional[float] = Field(
        None, alias="ROE (Return on Equity)", description="Laba Bersih / Total Ekuitas")
    roa_ebit: Optional[float] = Field(
        None, alias="ROA (Return on Assets - EBIT based)", description="EBIT / Total Aset")
    sales_growth: Optional[float] = Field(
        None, alias="Sales Growth", description="Pertumbuhan Pendapatan Bersih (t vs t-1)")
    error: Optional[str] = Field(
        None, description="Pesan error jika perhitungan rasio umum gagal")

    class Config:
        populate_by_name = True


class PrabuCreditRiskPrediction(BaseModel):
    """Hasil prediksi risiko kredit."""
    credit_risk_score: Optional[float] = Field(
        None, description="Skor risiko kredit (0-100, lebih tinggi = risiko lebih rendah)")
    risk_category: Optional[str] = Field(
        None, description="Kategori risiko (Low, Medium, High)")
    underlying_ratios: Optional[Dict[str, Optional[float]]] = Field(
        None, description="Rasio-rasio yang digunakan dalam model prediksi risiko")
    altman_z_score_used: Optional[float] = Field(
        None, description="Nilai Altman Z-Score yang digunakan dalam prediksi rule-based")
    beneish_m_score_used: Optional[float] = Field(
        None, description="Nilai Beneish M-Score yang digunakan dalam prediksi rule-based")
    error: Optional[str] = Field(
        None, description="Pesan error jika prediksi risiko kredit rule-based gagal")


class PrabuMLCreditRiskPrediction(BaseModel):
    """Hasil prediksi risiko kredit menggunakan model Machine Learning."""
    risk_category: Optional[str] = Field(
        None, description="Kategori risiko hasil prediksi ML (Low, Medium, High)")
    risk_score: Optional[float] = Field(
        None, description="Skor risiko numerik yang dihasilkan dari kategori (misal, Low=20, Medium=50, High=80)")
    probabilities: Optional[Dict[str, float]] = Field(
        None, description="Probabilitas untuk setiap kategori risiko")
    error: Optional[str] = Field(
        None, description="Pesan error jika prediksi risiko kredit ML gagal")


class PrabuAnalysisResponse(BaseModel):
    """Respons lengkap dari analisis Prabu."""
    altman_z_score_analysis: PrabuAltmanAnalysis
    beneish_m_score_analysis: PrabuBeneishAnalysis
    common_financial_ratios: PrabuCommonRatios
    # credit_risk_prediction_rule_based: Optional[PrabuCreditRiskPrediction] = None # Jika ingin mempertahankan yang lama
    credit_risk_prediction: PrabuMLCreditRiskPrediction  # Mengganti dengan prediksi ML
    error: Optional[str] = Field(
        None, description="Pesan error global dari keseluruhan analisis Prabu")

# Untuk Sarana, inputnya adalah UploadFile, jadi tidak perlu model Pydantic khusus untuk input file.
# Outputnya adalah dictionary, bisa kita definisikan jika strukturnya tetap.


class SaranaKeywordExtraction(BaseModel):
    """Data ekstraksi kata kunci untuk satu periode."""
    t: Optional[float] = Field(
        None, description="Nilai untuk periode t (tahun berjalan)")
    t_minus_1: Optional[float] = Field(
        None, description="Nilai untuk periode t-1 (tahun sebelumnya)")


class SaranaParseDocumentResponse(BaseModel):
    """Respons dari layanan parsing dokumen Sarana."""
    nama_file: str
    info_parsing: str = Field(
        description="Informasi mengenai proses parsing yang dilakukan")
    error_parsing: Optional[str] = Field(
        None, description="Pesan error jika terjadi kegagalan parsing")
    teks_ekstrak_mentah: Optional[str] = Field(
        None, description="Teks mentah hasil ekstraksi (jika output_format='text')")
    tahun_pelaporan_terdeteksi: Optional[str] = Field(
        None, description="Tahun pelaporan yang terdeteksi dari dokumen")
    pengali_global_terdeteksi: Optional[float] = Field(
        None, description="Pengali global (misal, ribuan, jutaan) yang terdeteksi")
    hasil_ekstraksi_kata_kunci: Optional[Dict[str, SaranaKeywordExtraction]] = Field(
        None, description="Hasil ekstraksi kata kunci keuangan dari teks (jika output_format='text')")
    hasil_ekstraksi_terstruktur: Optional[Dict[str, Any]] = Field(
        None, description="Hasil ekstraksi terstruktur dalam format JSON (jika output_format='structured_json')")


# Untuk Setia
class SetiaRiskIntelligenceRequest(BaseModel):
    """Request untuk analisis intelijen risiko Setia."""
    applicant_name: str = Field(..., example="PT Contoh Tbk",
                                description="Nama entitas/aplikan yang akan dianalisis")
    industry_main: Optional[str] = Field(
        None, example="Keuangan", description="Sektor industri utama")
    industry_sub: Optional[str] = Field(
        None, example="Perbankan (BUKU IV/III)", description="Sub-sektor industri")
    use_gcs_for_risk_data: bool = Field(
        False, description="Gunakan GCS untuk memuat data risiko industri (jika True)")
    gcs_bucket_name_override: Optional[str] = Field(
        None, description="Nama bucket GCS kustom untuk data risiko (override default jika ada)")


class SetiaSupportingSource(BaseModel):
    """Sumber pendukung untuk analisis Setia."""
    title: Optional[str] = Field(
        None, description="Judul sumber berita/artikel")
    url: Optional[str] = Field(None, description="URL sumber berita/artikel")


class SetiaRiskIntelligenceResponse(BaseModel):
    """Respons dari analisis intelijen risiko Setia."""
    groundedSummary: Optional[str] = Field(
        None, description="Ringkasan analisis berbasis berita terkini (grounded AI)")
    overallSentiment: Optional[str] = Field(
        None, description="Sentimen keseluruhan dari analisis berita")
    keyIssues: Optional[List[str]] = Field(
        [], description="Daftar isu kunci atau risiko yang teridentifikasi dari berita")
    supportingSources: Optional[List[SetiaSupportingSource]] = Field(
        [], description="Daftar sumber pendukung (berita/artikel)")
    industrySectorOutlook: Optional[str] = Field(
        None, description="Outlook risiko untuk sektor industri terkait")
    lastUpdateTimestamp: datetime.datetime = Field(
        description="Timestamp kapan analisis terakhir dilakukan (UTC)")
    error: Optional[str] = Field(
        None, description="Pesan error jika analisis Setia gagal")


# Tambahkan __all__ untuk kontrol impor jika diperlukan
__all__ = [
    "FinancialDataInput", "PrabuAnalysisRequest", "PrabuAnalysisResponse",
    "PrabuRatios", "PrabuAltmanAnalysis", "PrabuBeneishAnalysis", "PrabuCommonRatios",
    # Menambahkan PrabuMLCreditRiskPrediction
    "PrabuCreditRiskPrediction", "PrabuMLCreditRiskPrediction",
    "SaranaKeywordExtraction", "SaranaParseDocumentResponse",
    "SetiaRiskIntelligenceRequest", "SetiaSupportingSource", "SetiaRiskIntelligenceResponse"
]
