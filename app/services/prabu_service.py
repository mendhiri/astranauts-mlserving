from typing import Dict, Any, Optional

try:
    from PrabuModule import altman_z_score, beneish_m_score, financial_ratios, ml_credit_risk_predictor
except ImportError:
    # Fallback jika PrabuModule dianggap sebagai bagian dari 'app' (misalnya app.PrabuModule)
    # atau jika sys.path dimodifikasi untuk menyertakan root.
    # Untuk tujuan pengembangan ini, kita akan mencoba membuatnya bekerja dengan asumsi
    # bahwa saat runtime, PrabuModule akan dapat diakses.
    # Jika ini dijalankan sebagai bagian dari FastAPI app, dan root ada di PYTHONPATH:
    import sys
    import os
    # Menambahkan direktori root proyek ke sys.path
    # Ini adalah praktik umum jika modul tidak diinstal sebagai package.
    # __file__ -> app/services/prabu_service.py
    # os.path.dirname(__file__) -> app/services
    # os.path.dirname(os.path.dirname(__file__)) -> app
    # os.path.dirname(os.path.dirname(os.path.dirname(__file__))) -> ROOT
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Sekarang coba impor lagi
    from PrabuModule import altman_z_score, beneish_m_score, financial_ratios, ml_credit_risk_predictor

# --- END Penyesuaian Impor ---


KEY_MAP_PRABU = {
    # Kunci adalah variasi yang mungkin dari Sarana, nilai adalah kunci standar yang diharapkan modul Prabu
    "Piutang Usaha": "Piutang usaha",
    "Pendapatan Bersih": "Pendapatan bersih",
    "Laba Bruto": "Laba bruto",
    "Jumlah Aset Tidak Lancar": "Jumlah aset tidak lancar",
    "Jumlah Aset": "Jumlah aset",
    "Beban Penyusutan": "Beban penyusutan",
    "Aset Tetap Bruto": "Aset tetap bruto",
    "Beban Penjualan": "Beban penjualan",
    "Beban Administrasi dan Umum": "Beban administrasi dan umum",
    "Jumlah Liabilitas": "Jumlah liabilitas",
    "Laba Tahun Berjalan": "Laba/rugi tahun berjalan",
    "Arus Kas Bersih yang Diperoleh dari Aktivitas Operasi": "Arus kas bersih yang diperoleh dari aktivitas operasi",
    "Jumlah Aset Lancar": "Jumlah aset lancar",
    "Aset Tetap": "Aset tetap",
    "Laba Ditahan": "Laba ditahan",
    "Laba Sebelum Pajak Penghasilan": "Laba/rugi sebelum pajak penghasilan",
    "Beban Bunga": "Beban bunga",
    "Jumlah Ekuitas": "Jumlah ekuitas",
    "Jumlah Liabilitas Jangka Pendek": "Jumlah liabilitas jangka pendek",

    # Variasi huruf besar
    "PIUTANG USAHA": "Piutang usaha",
    "PENDAPATAN BERSIH": "Pendapatan bersih",
    "LABA BRUTO": "Laba bruto",
    "JUMLAH ASET TIDAK LANCAR": "Jumlah aset tidak lancar",
    "JUMLAH ASET": "Jumlah aset",
    "BEBAN PENYUSUTAN": "Beban penyusutan",
    "ASET TETAP BRUTO": "Aset tetap bruto",
    "BEBAN PENJUALAN": "Beban penjualan",
    "BEBAN ADMINISTRASI DAN UMUM": "Beban administrasi dan umum",
    "JUMLAH LIABILITAS": "Jumlah liabilitas",
    "LABA TAHUN BERJALAN": "Laba/rugi tahun berjalan",
    "ARUS KAS BERSIH YANG DIPEROLEH DARI AKTIVITAS OPERASI": "Arus kas bersih yang diperoleh dari aktivitas operasi",
    "JUMLAH ASET LANCAR": "Jumlah aset lancar",
    "ASET TETAP": "Aset tetap",
    "LABA DITAHAN": "Laba ditahan",
    "LABA SEBELUM PAJAK PENGHASILAN": "Laba/rugi sebelum pajak penghasilan",
    "BEBAN BUNGA": "Beban bunga",
    "JUMLAH EKUITAS": "Jumlah ekuitas",
    "JUMLAH LIABILITAS JANGKA PENDEK": "Jumlah liabilitas jangka pendek",
    
    # Variasi lain yang mungkin muncul dari Sarana atau input manual
    "Total Aset Lancar": "Jumlah aset lancar",
    "Total Liabilitas Jangka Pendek": "Jumlah liabilitas jangka pendek",
    "Total Liabilitas": "Jumlah liabilitas",
    "Total Ekuitas": "Jumlah ekuitas",
    "Total Aset": "Jumlah aset",
    "Penjualan Bersih": "Pendapatan bersih",
    "Harga Pokok Penjualan": "Beban pokok pendapatan", # Perlu dipastikan apakah PrabuModule menggunakannya atau Laba Bruto
    "Laba Kotor": "Laba bruto",
    "EBIT (Laba Sebelum Bunga dan Pajak)": "Laba/rugi sebelum pajak penghasilan", # Ini perlu dihitung jika tidak ada, EBIT = EBT + Interest
    "EBT (Laba Sebelum Pajak)": "Laba/rugi sebelum pajak penghasilan",
    "Pajak Penghasilan": "Beban pajak penghasilan", # Tidak langsung dipakai, tapi bisa untuk validasi
    "Laba Bersih": "Laba/rugi tahun berjalan",
    "Arus Kas dari Aktivitas Operasi": "Arus kas bersih yang diperoleh dari aktivitas operasi",
    "Aset Tetap (Neto)": "Aset tetap",
    "Aset Tetap (Bruto)": "Aset tetap bruto",
    "Akumulasi Penyusutan": "Akumulasi penyusutan", # Tidak langsung dipakai di PrabuModule, tapi bisa untuk validasi
}

def _normalize_financial_data_keys(data_dict: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Menormalisasi kunci-kunci dalam dictionary data keuangan ke format standar
    yang diharapkan oleh modul-modul Prabu.
    """
    if not data_dict or not isinstance(data_dict, dict):
        return None

    normalized_dict = {}
    for key_input, value in data_dict.items():
        standard_key = KEY_MAP_PRABU.get(key_input, key_input)
        normalized_dict[standard_key] = value
    return normalized_dict

def run_prabu_analysis(
    data_t: Dict[str, Any],
    data_t_minus_1: Optional[Dict[str, Any]] = None,
    is_public_company: bool = True,
    market_value_equity_manual: Optional[float] = None,
    altman_model_type_override: Optional[str] = None, # e.g., "public_manufacturing", "private_manufacturing", "non_manufacturing_or_emerging_markets"
    sector: Optional[str] = None # Tambahkan parameter sector
) -> Dict[str, Any]:
    """
    Menjalankan analisis keuangan lengkap menggunakan modul Prabu.

    Args:
        data_t (dict): Data keuangan periode t (tahun berjalan) dari API request.
        data_t_minus_1 (dict, optional): Data keuangan periode t-1 dari API request.
        is_public_company (bool): Status perusahaan (publik/privat).
        market_value_equity_manual (float, optional): Nilai pasar ekuitas manual.
        altman_model_type_override (str, optional): Override tipe model Altman Z-Score.
        sector (str, optional): Sektor industri perusahaan.

    Returns:
        dict: Hasil analisis yang terstruktur, siap untuk PrabuAnalysisResponse.
    """
    norm_data_t = _normalize_financial_data_keys(data_t)
    norm_data_t_minus_1 = _normalize_financial_data_keys(data_t_minus_1)

    if not norm_data_t:
        return {"error": "Data keuangan periode t (data_t) tidak valid atau kosong setelah normalisasi."}

    altman_result = {}
    beneish_result = {}
    common_ratios_result = {}
    ml_credit_risk_pred_result = {} # Ganti nama untuk hasil prediksi ML
    
    # 1. Analisis Altman Z-Score
    # Tentukan model_type untuk Altman Z-Score
    # Prioritaskan override jika ada
    actual_altman_model_type = altman_model_type_override
    if not actual_altman_model_type:
        if is_public_company:
            # Default untuk publik bisa 'public_manufacturing' atau 'non_manufacturing_or_emerging_markets'.
            # Modul altman_z_score.py default ke 'public_manufacturing' jika tidak dispesifikkan lebih lanjut.
            # Kita bisa membiarkannya default atau memilih berdasarkan ketersediaan 'Pendapatan bersih' (Sales)
            # Jika Sales ada, model 'public_manufacturing' atau 'private_manufacturing' lebih cocok.
            # Jika tidak ada info industri, 'non_manufacturing_or_emerging_markets' bisa jadi pilihan aman
            # karena tidak menggunakan X5 (Sales/Total Assets)
            # Untuk sekarang, kita ikuti logika di get_altman_z_score_analysis yang akan memilih
            # 'public_manufacturing' jika is_public_company=True dan tidak ada override.
            # Jika ingin lebih presisi, router bisa mengirimkan info jenis industri (manufaktur/non-manufaktur)
            pass # Biarkan get_altman_z_score_analysis yang menentukan berdasarkan is_public_company
        else: # Perusahaan privat
            actual_altman_model_type = "private_manufacturing" 
            # Jika altman_model_type_override tidak ada, dan is_public_company False,
            # maka get_altman_z_score_analysis akan menggunakan "private_manufacturing"

    # Buat salinan data_t untuk dimodifikasi jika MVE manual digunakan, agar data asli tidak berubah.
    data_t_for_altman = norm_data_t.copy()
    # Modul altman_z_score.py dalam get_altman_z_score_analysis sudah menangani MVE manual
    # dengan mengganti "Jumlah ekuitas" sementara jika MVE manual diberikan dan modelnya publik.
    # Jadi, kita tidak perlu memodifikasi data_t_for_altman di sini secara eksplisit untuk MVE.
    
    altman_analysis = altman_z_score.get_altman_z_score_analysis(
        data_t=data_t_for_altman, # Menggunakan data yang sudah dinormalisasi
        is_public_company=is_public_company,
        market_value_equity_manual=market_value_equity_manual
        # model_type akan ditentukan di dalam get_altman_z_score_analysis
        # kecuali altman_model_type_override digunakan untuk mengganti logika defaultnya.
        # Namun, get_altman_z_score_analysis tidak menerima model_type secara langsung,
        # ia menentukannya sendiri. Jika kita ingin override, kita harus panggil calculate_altman_z_score.
    )
    
    # Jika ada altman_model_type_override, kita harus panggil calculate_altman_z_score langsung
    # dan membangun responsnya manual karena get_altman_z_score_analysis tidak menerima override model.
    if altman_model_type_override:
        # Perlu penyesuaian jika market_value_equity_manual digunakan dengan model override
        # calculate_altman_z_score menggunakan data_t["Jumlah ekuitas"] sebagai proxy MVE
        data_t_for_calc_altman = norm_data_t.copy()
        original_equity_val_override = None
        if market_value_equity_manual is not None and "Jumlah ekuitas" in data_t_for_calc_altman:
             original_equity_val_override = data_t_for_calc_altman["Jumlah ekuitas"]
             data_t_for_calc_altman["Jumlah ekuitas"] = market_value_equity_manual
        
        z_score_override, ratios_override = altman_z_score.calculate_altman_z_score(
            data_t_for_calc_altman, model_type=altman_model_type_override
        )
        
        if original_equity_val_override is not None: # Kembalikan
            data_t_for_calc_altman["Jumlah ekuitas"] = original_equity_val_override

        altman_interpretation_override = "Tidak dapat diinterpretasi."
        altman_zone_override = "Unknown"
        if z_score_override is not None and ratios_override and "interpretation_zones" in ratios_override:
            zones_info_override = ratios_override["interpretation_zones"]
            # Logika interpretasi zona dari altman_z_score.get_altman_z_score_analysis
            if altman_model_type_override == "public_manufacturing":
                if z_score_override > 2.99: altman_zone_override = "Safe Zone"
                elif z_score_override > 1.81: altman_zone_override = "Grey Zone"
                else: altman_zone_override = "Distress Zone"
            elif altman_model_type_override == "private_manufacturing":
                if z_score_override > 2.90: altman_zone_override = "Safe Zone"
                elif z_score_override > 1.23: altman_zone_override = "Grey Zone"
                else: altman_zone_override = "Distress Zone"
            elif altman_model_type_override == "non_manufacturing_or_emerging_markets":
                if z_score_override > 2.60: altman_zone_override = "Safe Zone"
                elif z_score_override > 1.10: altman_zone_override = "Grey Zone"
                else: altman_zone_override = "Distress Zone"
            altman_interpretation_override = f"Perusahaan berada di '{altman_zone_override}'. Model: {ratios_override.get('model_type', altman_model_type_override)}. Zona Detail: {zones_info_override}"
            if market_value_equity_manual is not None and "X4_note" in ratios_override: # Jika MVE manual dipakai
                 ratios_override["X4_note"] = "Using provided manual Market Value of Equity for X4."

        elif ratios_override and "error" in ratios_override:
            altman_interpretation_override = f"Error dalam perhitungan: {ratios_override['error']}"
            altman_zone_override = "Error"
            
        altman_result = {
            "z_score": z_score_override,
            "ratios": ratios_override, # Ini akan jadi PrabuRatios
            "interpretation": altman_interpretation_override,
            "zone": altman_zone_override,
            "model_used": altman_model_type_override,
            "error": ratios_override.get("error") if z_score_override is None else None
        }
    else: # Tidak ada override, gunakan hasil dari get_altman_z_score_analysis
        altman_result = {
            "z_score": altman_analysis.get("z_score"),
            "ratios": altman_analysis.get("ratios"), # Ini akan jadi PrabuRatios
            "interpretation": altman_analysis.get("interpretation"),
            "zone": altman_analysis.get("zone"),
            "model_used": altman_analysis.get("model_used"),
            "error": altman_analysis.get("error") # Error dari get_altman_z_score_analysis
        }

    # 2. Analisis Beneish M-Score
    if norm_data_t_minus_1:
        beneish_analysis = beneish_m_score.get_beneish_m_score_analysis(norm_data_t, norm_data_t_minus_1)
        beneish_result = {
            "m_score": beneish_analysis.get("m_score"),
            "ratios": beneish_analysis.get("ratios"), # Ini dict biasa {DSRI: val, ...}
            "interpretation": beneish_analysis.get("interpretation"),
            "error": beneish_analysis.get("error")
        }
    else:
        beneish_result = {
            "m_score": None,
            "ratios": None,
            "interpretation": "Data periode t-1 tidak tersedia untuk Beneish M-Score.",
            "error": "Data t-1 tidak disediakan."
        }

    # 3. Rasio Keuangan Umum
    # Menggunakan calculate_common_financial_ratios dari financial_ratios.py
    # Ini adalah subset dari rasio yang mungkin ada di credit_risk_predictor.get_financial_ratios_for_prabu
    # Untuk API, kita ingin rasio yang lebih komprehensif seperti yang ada di PrabuCommonRatios (definisi API model)
    # Kita bisa panggil get_financial_ratios_for_prabu dari credit_risk_predictor.py
    # karena itu yang digunakan untuk prediksi risiko kredit dan lebih lengkap.
    
    # common_ratios_from_module = financial_ratios.calculate_common_financial_ratios(norm_data_t)
    # common_ratios_result = common_ratios_from_module # Ini dict biasa, akan dipetakan ke PrabuCommonRatios

    # Menggunakan financial_ratios.calculate_common_financial_ratios yang ada.
    # Ini mungkin menghasilkan lebih sedikit rasio daripada get_financial_ratios_for_prabu sebelumnya,
    # karena calculate_common_financial_ratios hanya menerima data_t.
    # Jika rasio dari data_t_minus_1 diperlukan, fungsi ini perlu diperluas.
    if norm_data_t:
        comprehensive_ratios = financial_ratios.calculate_common_financial_ratios(norm_data_t)
    else:
        comprehensive_ratios = {"error": "Data keuangan (norm_data_t) tidak tersedia untuk perhitungan rasio."}

    if comprehensive_ratios and "error" not in comprehensive_ratios:
         # Perlu memastikan comprehensive_ratios tidak mengandung 'error' di level atasnya
         # Jika ada error parsial (misal, salah satu rasio None), itu tidak masalah.
         # Jika get_financial_ratios_for_prabu sendiri gagal total, ia mungkin return dict kosong atau None.
        common_ratios_result = comprehensive_ratios
        # Tambahkan field 'error' jika comprehensive_ratios kosong atau None, atau jika ada error internal.
        if not common_ratios_result:
            common_ratios_result = {"error": "Gagal menghitung rasio keuangan umum secara komprehensif."}
        # Jika ada error parsial, itu akan direfleksikan sebagai None di nilai rasio.
        # Model Pydantic PrabuCommonRatios harusnya bisa menangani ini.
    else:
        common_ratios_result = {"error": "Gagal menghitung rasio keuangan komprehensif."}

    # 4. Prediksi Risiko Kredit menggunakan Model ML
    if not sector:
        ml_credit_risk_pred_result = {
            "risk_category": None,
            "probabilities": None,
            "error": "Sektor tidak disediakan, prediksi ML tidak dapat dilakukan."
        }
    else:
        # Data input untuk prediksi ML adalah dictionary fitur keuangan.
        # ml_credit_risk_predictor.predict_credit_risk_ml mengharapkan dict fitur mentah.
        # Kita bisa menggunakan comprehensive_ratios yang sudah dihitung, atau norm_data_t
        # Tergantung bagaimana model ML dilatih. Jika dilatih pada rasio, gunakan comprehensive_ratios.
        # Jika dilatih pada data mentah yang kemudian di-preprocess, gunakan norm_data_t.
        # Berdasarkan incremental_model_trainer.py, model dilatih pada fitur-fitur yang ada di dataset CSV,
        # yang merupakan rasio dan fitur spesifik sektor, bukan item laporan keuangan mentah.
        # Jadi, kita perlu memastikan `comprehensive_ratios` (atau subsetnya yang relevan) diteruskan.
        # Fungsi `ml_credit_risk_predictor.predict_credit_risk_ml` sudah mengharapkan dict fitur.
        
        # `comprehensive_ratios` sudah merupakan dict fitur yang bisa langsung dipakai.
        # Ini juga mencakup fitur-fitur umum yang ada di GENERAL_FEATURES dari trainer.
        # Fitur spesifik sektor perlu ditambahkan ke dict ini jika belum ada.
        # Namun, `ml_credit_risk_predictor.py` akan menangani penambahan fitur yang tidak ada dengan NaN.
        # Jadi, kita bisa langsung pass `norm_data_t` yang berisi semua item keuangan mentah,
        # karena `ml_credit_risk_predictor.py` akan melakukan pra-pemrosesan (termasuk perhitungan rasio jika perlu, atau penggunaan fitur mentah).
        # Revisi: `ml_credit_risk_predictor` dan `incremental_model_trainer` menggunakan fitur-fitur yang sudah dihitung (rasio, dll)
        # Jadi, kita harus mengirimkan dict yang berisi nama fitur yang sama dengan yang digunakan saat pelatihan.
        # `comprehensive_ratios` adalah kandidat yang baik jika ingin menggunakan rasio saja.
        # Namun, untuk fleksibilitas fitur sektor, `norm_data_t` (yang berisi semua data mentah dari request) lebih cocok
        # karena `ml_credit_risk_predictor` akan melakukan seleksi/pemrosesan fitur yang diperlukan.
        
        ml_pred_result = ml_credit_risk_predictor.predict_credit_risk_ml(financial_data_dict=norm_data_t, sector=sector)
        ml_credit_risk_pred_result = ml_pred_result # Hasilnya sudah dict yang sesuai
    
    # Gabungkan semua hasil
    final_result = {
        "altman_z_score_analysis": altman_result,
        "beneish_m_score_analysis": beneish_result,
        "common_financial_ratios": common_ratios_result, # Ini adalah dict rasio
        "credit_risk_prediction": ml_credit_risk_pred_result # Menggunakan hasil prediksi ML
    }
    
    # Cek apakah ada error global yang perlu di-propagate jika salah satu komponen utama gagal
    if altman_result.get("error") and not altman_result.get("z_score"): # Jika Altman gagal total
        final_result["error"] = f"Analisis Altman Z-Score gagal: {altman_result['error']}"
    elif beneish_result.get("error") and not beneish_result.get("m_score") and norm_data_t_minus_1: # Jika Beneish gagal dan seharusnya bisa dihitung
        final_result["error"] = f"Analisis Beneish M-Score gagal: {beneish_result['error']}"
    elif ml_credit_risk_pred_result.get("error") and not ml_credit_risk_pred_result.get("risk_category"):
        final_result["error"] = f"Prediksi Risiko Kredit ML gagal: {ml_credit_risk_pred_result['error']}"
    # Error dari common_ratios akan ada di dalam field 'error' masing-masing.

    return final_result


if __name__ == '__main__':
    # Contoh data input (mirip dengan PrabuAnalysisRequest)
    sample_data_t = {
        "Pendapatan bersih": 108249000000000.0, 
        "Jumlah aset": 101003000000000.0, 
        "Jumlah liabilitas": 16289000000000.0, 
        "Laba/rugi tahun berjalan": 21661000000000.0, 
        "Jumlah aset lancar": 19238000000000.0, 
        "Jumlah liabilitas jangka pendek": 14300000000000.0, 
        "Laba ditahan": 65000000000000.0, 
        "Laba/rugi sebelum pajak penghasilan": 22136000000000.0, 
        "Beban bunga": 550000000000.0, 
        "Jumlah ekuitas": 84714000000000.0, 
        "Piutang usaha": 13200000000000.0, 
        "Laba bruto": 10511000000000.0, 
        "Aset tetap bruto": 66000000000000.0, 
        "Beban penyusutan": 2750000000000.0, 
        "Beban penjualan": 3300000000000.0, 
        "Beban administrasi dan umum": 2200000000000.0, 
        "Arus kas bersih yang diperoleh dari aktivitas operasi": 3135000000000.0, 
        "Aset tetap": 55000000000000.0, # Aset Tetap (Neto)
        "Jumlah aset tidak lancar": 81765000000000.0,
    }

    sample_data_t_minus_1 = {
        "Pendapatan bersih": 95000000000000.0, 
        "Jumlah aset": 93000000000000.0,
        "Jumlah liabilitas": 14800000000000.0,
        "Jumlah aset lancar": 1800000000000.0, # Typo di beneish_m_score.py example, harusnya lebih besar
        "Piutang usaha": 12000000000000.0, 
        "Laba bruto": 10000000000000.0,
        "Aset tetap bruto": 60000000000000.0, 
        "Beban penyusutan": 2500000000000.0, 
        "Beban penjualan": 3000000000000.0, 
        "Beban administrasi dan umum": 2000000000000.0,
        "Aset tetap": 50000000000000.0, # Aset Tetap (Neto)
        "Jumlah aset tidak lancar": 75000000000000.0
        # Data lain yang mungkin dibutuhkan oleh Beneish/rasio lain jika ada
    }
    # Koreksi Jumlah Aset Lancar t-1 agar lebih realistis
    sample_data_t_minus_1["Jumlah aset lancar"] = 18000000000000.0 


    print("--- Menjalankan Analisis Prabu Lengkap (Contoh) ---")
    
    # Skenario 1: Perusahaan publik, tanpa MVE manual, tanpa override model Altman
    analysis1 = run_prabu_analysis(
        data_t=sample_data_t,
        data_t_minus_1=sample_data_t_minus_1,
        is_public_company=True,
        sector="Pertambangan" # Tambahkan sektor
    )
    import json
    print("\nHasil Analisis Skenario 1 (Publik, default):")
    print(json.dumps(analysis1, indent=2, ensure_ascii=False))

    # Skenario 2: Perusahaan privat
    analysis2 = run_prabu_analysis(
        data_t=sample_data_t,
        data_t_minus_1=sample_data_t_minus_1,
        is_public_company=False, # Ini akan memicu model Altman untuk private manufacturing
        sector="Konstruksi" # Tambahkan sektor
    )
    print("\nHasil Analisis Skenario 2 (Privat):")
    print(json.dumps(analysis2, indent=2, ensure_ascii=False))

    # Skenario 3: Dengan MVE manual (hanya relevan jika perusahaan publik)
    analysis3 = run_prabu_analysis(
        data_t=sample_data_t,
        data_t_minus_1=sample_data_t_minus_1,
        is_public_company=True,
        market_value_equity_manual=90000000000000.0, # Contoh MVE
        sector="Agro" # Tambahkan sektor
    )
    print("\nHasil Analisis Skenario 3 (Publik, MVE Manual):")
    print(json.dumps(analysis3, indent=2, ensure_ascii=False))
    
    # Skenario 4: Dengan override model Altman ke non-manufacturing
    analysis4 = run_prabu_analysis(
        data_t=sample_data_t,
        data_t_minus_1=sample_data_t_minus_1,
        is_public_company=True, # Tidak terlalu relevan jika model di-override
        altman_model_type_override="non_manufacturing_or_emerging_markets",
        sector="Manufaktur Alat Berat" # Tambahkan sektor
    )
    print("\nHasil Analisis Skenario 4 (Override Altman ke Non-Manufacturing):")
    print(json.dumps(analysis4, indent=2, ensure_ascii=False))

    # Skenario 5: Tanpa data t-1 (Beneish tidak akan dihitung)
    analysis5 = run_prabu_analysis(
        data_t=sample_data_t,
        data_t_minus_1=None,
        is_public_company=True,
        sector="Logistik Alat Berat" # Tambahkan sektor
    )
    print("\nHasil Analisis Skenario 5 (Tanpa Data t-1):")
    print(json.dumps(analysis5, indent=2, ensure_ascii=False))
    
    # Skenario 6: Data t tidak lengkap (contoh: Pendapatan bersih hilang)
    sample_data_t_incomplete = sample_data_t.copy()
    del sample_data_t_incomplete["Pendapatan bersih"]
    analysis6 = run_prabu_analysis(
        data_t=sample_data_t_incomplete,
        data_t_minus_1=sample_data_t_minus_1,
        is_public_company=True,
        sector="Pertambangan" # Tambahkan sektor
    )
    print("\nHasil Analisis Skenario 6 (Data t Tidak Lengkap):")
    print(json.dumps(analysis6, indent=2, ensure_ascii=False))
    # Harapannya ada error di beberapa bagian, misal Altman (X5), Beneish (DSRI, GMI, SGAI), Common Ratios (NPM), Credit Risk (NPM, Sales Growth)

    # Skenario 7: Data t kosong
    analysis7 = run_prabu_analysis(
        data_t={},
        is_public_company=True,
        sector="Tidak Diketahui" # Sektor tidak valid/kosong
    )
    print("\nHasil Analisis Skenario 7 (Data t Kosong):")
    print(json.dumps(analysis7, indent=2, ensure_ascii=False))
    # Harapannya error global
