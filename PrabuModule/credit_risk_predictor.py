# from FinancialScoreModels.utils import get_value # get_value tidak ada di utils.py

def get_financial_ratios_for_prabu(financial_data_t: dict, financial_data_t_minus_1: dict = None) -> dict:
    """
    Menghitung rasio keuangan dasar yang mungkin berguna untuk prediksi risiko kredit.
    Ini adalah contoh, bisa ditambahkan lebih banyak rasio sesuai kebutuhan.
    Diasumsikan financial_data_t memiliki struktur: {"Nama Akun": {"current_year": V, "previous_year": V}}
    Diasumsikan financial_data_t_minus_1 (jika ada) memiliki struktur: {"Nama Akun": V_tm1}
    """
    ratios = {}

    # Helper untuk mengambil nilai dari dictionary data keuangan tunggal (sudah spesifik perusahaan)
    def _get_value(data_dict, key, default=None):
        if not isinstance(data_dict, dict):
            return default
        # Coba ambil nilai float langsung, jika gagal atau tidak ada, kembalikan default
        try:
            value = data_dict.get(key)
            if value is not None:
                return float(value)
            return default
        except (ValueError, TypeError):
            # Jika konversi gagal atau nilai tidak sesuai, kembalikan default
            return default

    # Rasio Likuiditas
    current_assets = _get_value(financial_data_t, "Jumlah aset lancar")
    current_liabilities = _get_value(financial_data_t, "Jumlah liabilitas jangka pendek")
    if current_assets is not None and current_liabilities is not None and current_liabilities > 0:
        ratios['current_ratio'] = current_assets / current_liabilities
    else:
        ratios['current_ratio'] = None # Atau bisa juga 0 atau float('inf') tergantung kebijakan

    # Rasio Leverage
    total_liabilities = _get_value(financial_data_t, "Jumlah liabilitas")
    total_equity = _get_value(financial_data_t, "Jumlah ekuitas")
    if total_liabilities is not None and total_equity is not None:
        if total_equity > 0: # Ekuitas positif
            ratios['debt_to_equity_ratio'] = total_liabilities / total_equity
        elif total_equity == 0: # Ekuitas nol
            ratios['debt_to_equity_ratio'] = float('inf') if total_liabilities > 0 else 0 # Jika utang > 0, rasio tak hingga
        else: # Ekuitas negatif
            # Interpretasi bisa rumit, seringkali dianggap sebagai sinyal buruk.
            # Rasio bisa menjadi negatif jika utang positif, atau positif jika utang juga negatif (jarang).
            # Untuk penyederhanaan, bisa di-cap atau ditandai.
            ratios['debt_to_equity_ratio'] = total_liabilities / total_equity # Akan menghasilkan nilai negatif jika TL positif
    else:
        ratios['debt_to_equity_ratio'] = None
    
    total_assets_for_debt_ratio = _get_value(financial_data_t, "Jumlah aset")
    if total_liabilities is not None and total_assets_for_debt_ratio is not None and total_assets_for_debt_ratio > 0:
        ratios['debt_ratio'] = total_liabilities / total_assets_for_debt_ratio
    else:
        ratios['debt_ratio'] = None

    # Rasio Profitabilitas
    net_income = _get_value(financial_data_t, "Laba tahun berjalan")
    sales = _get_value(financial_data_t, "Pendapatan bersih")
    if net_income is not None and sales is not None and sales > 0:
        ratios['net_profit_margin'] = net_income / sales
    else:
        ratios['net_profit_margin'] = None # Atau 0 jika sales 0

    if net_income is not None and total_equity is not None:
        if total_equity > 0:
            ratios['roe'] = net_income / total_equity
        # Jika ekuitas <= 0, ROE bisa sangat besar atau tidak bermakna, bisa di-handle sebagai None atau nilai ekstrem
        else: 
            ratios['roe'] = None # Atau nilai ekstrem jika diperlukan
    else:
        ratios['roe'] = None
        
    ebt = _get_value(financial_data_t, "Laba sebelum pajak penghasilan")
    # "Beban bunga" dari parser keuangan umumnya adalah nilai positif yang merepresentasikan biaya.
    # Jika disimpan sebagai negatif (misalnya, pendapatan bunga > beban bunga), maka perlu penyesuaian.
    # Asumsi di sini: "Beban bunga" adalah biaya bunga (angka positif) atau 0.
    interest_expense_val = _get_value(financial_data_t, "Beban bunga", default=0.0) # Default 0 jika tidak ada
    
    ebit = None
    if ebt is not None:
        # EBIT = Laba Sebelum Pajak (EBT) + Beban Bunga
        # Pastikan interest_expense_val adalah nilai absolut jika ada kemungkinan negatif dari sumber data,
        # atau jika sumber data secara konsisten memberikan nilai positif untuk beban.
        # Jika "Beban bunga" adalah biaya, maka itu adalah pengurang EBT untuk mendapatkan Net Income (setelah pajak).
        # Jadi, EBT sudah memperhitungkan bunga. EBIT = EBT + Beban Bunga.
        ebit = ebt + interest_expense_val 
            
    total_assets_for_roa = _get_value(financial_data_t, "Jumlah aset")
    if ebit is not None and total_assets_for_roa is not None and total_assets_for_roa > 0:
        ratios['roa_ebit'] = ebit / total_assets_for_roa # Return on Assets from EBIT
    else:
        ratios['roa_ebit'] = None
        
    # Sales Growth (jika data t-1 ada)
    if financial_data_t_minus_1:
        sales_tm1 = _get_value(financial_data_t_minus_1, "Pendapatan bersih")
        if sales is not None and sales_tm1 is not None and sales_tm1 != 0: # sales dari financial_data_t
            ratios['sales_growth'] = (sales - sales_tm1) / abs(sales_tm1) # Gunakan abs untuk penyebut jika bisa negatif
        else:
            ratios['sales_growth'] = None # Atau 0 jika sales_tm1 adalah 0 dan sales > 0
    else:
        # Jika financial_data_t_minus_1 tidak disediakan, kita tidak bisa menghitung sales growth
        # kecuali financial_data_t sendiri memiliki data tahun sebelumnya (tidak diasumsikan di sini).
        ratios['sales_growth'] = None
            
    # Catatan: Fungsi ini tidak lagi mencoba mengambil "previous_year" dari financial_data_t
    # karena financial_data_t dan financial_data_t_minus_1 sekarang adalah input terpisah.
    # Beneish M Score dan Altman Z Score akan di-pass secara terpisah ke fungsi prediksi utama.
    # For now, this function only calculates basic ratios.
    # Integration with Beneish/Altman will be handled by the main prediction function.

    return ratios

def predict_credit_risk_v2(financial_data_t: dict, 
                           financial_data_t_minus_1: dict = None,
                           beneish_score_input: float = None, 
                           altman_z_score_input: float = None,
                           altman_is_public: bool = True) -> dict:
    """
    Memprediksi skor risiko kredit berdasarkan data keuangan menggunakan pendekatan berbasis aturan.
    Ini adalah versi pengganti yang tidak menggunakan model .joblib.

    Args:
        financial_data_t (dict): Data keuangan perusahaan untuk periode t.
        financial_data_t_minus_1 (dict, optional): Data keuangan perusahaan untuk periode t-1.
        beneish_score_input (float, optional): Skor Beneish M yang sudah dihitung.
        altman_z_score_input (float, optional): Skor Altman Z yang sudah dihitung.
        altman_is_public (bool): Menunjukkan apakah skor Altman dihitung untuk perusahaan publik.

    Returns:
        dict: Berisi "credit_risk_score" (0-100) dan "risk_category" (str).
    """
    ratios = get_financial_ratios_for_prabu(financial_data_t, financial_data_t_minus_1)
    
    score = 50  # Skor dasar (netral)
    max_score_possible = 100
    min_score_possible = 0
    
    # --- Aturan untuk menyesuaikan skor ---
    # Skor lebih tinggi = risiko lebih rendah
    # Skor lebih rendah = risiko lebih tinggi
    # Bobot penyesuaian bersifat contoh dan mungkin perlu kalibrasi lebih lanjut.

    # 1. Berdasarkan Altman Z-Score (jika ada)
    # Bobot: Aman (+25), Bahaya (-30), Abu-abu (-10)
    if altman_z_score_input is not None:
        if altman_is_public: # Zona untuk perusahaan publik
            if altman_z_score_input > 2.99: # Zona Aman
                score += 25
            elif altman_z_score_input <= 1.81: # Zona Bahaya
                score -= 30
            else: # Zona Abu-abu
                score -= 10
        else: # Zona untuk perusahaan privat
            if altman_z_score_input > 2.90: # Zona Aman
                score += 25
            elif altman_z_score_input <= 1.23: # Zona Bahaya
                score -= 30
            else: # Zona Abu-abu
                score -= 10
                
    # 2. Berdasarkan Beneish M-Score (jika ada)
    # Bobot: Potensi manipulasi (-20), Kemungkinan kecil manipulasi (+10)
    if beneish_score_input is not None:
        if beneish_score_input > -1.78: # Potensi manipulasi (skor lebih besar dari -1.78)
            score -= 20
        else: # Kemungkinan kecil manipulasi
            score += 10
            
    # 3. Berdasarkan Rasio Keuangan (contoh sederhana)
    # Current Ratio: Likuiditas. Ideal > 1.5 atau 2. Sangat rendah (<1) berisiko.
    # Bobot: <1 (-15), >2 (+10)
    if ratios.get('current_ratio') is not None:
        if ratios['current_ratio'] < 1.0:
            score -= 15 
        elif ratios['current_ratio'] > 2.0:
            score += 10
            
    # Debt-to-Equity Ratio: Leverage. Terlalu tinggi berisiko.
    # Bobot: >2 (-15), <0.5 (+5)
    if ratios.get('debt_to_equity_ratio') is not None:
        if ratios['debt_to_equity_ratio'] > 2.0: 
            score -= 15
        elif ratios['debt_to_equity_ratio'] < 0.5: 
            score += 5

    # Net Profit Margin: Profitabilitas.
    # Bobot: <2% (-10), >10% (+10)
    if ratios.get('net_profit_margin') is not None:
        if ratios['net_profit_margin'] < 0.02: 
            score -= 10
        elif ratios['net_profit_margin'] > 0.1: 
            score += 10
            
    # ROE (Return on Equity): Profitabilitas relatif terhadap ekuitas.
    # Bobot: <5% (-10), >15% (+10)
    if ratios.get('roe') is not None:
        if ratios['roe'] < 0.05: 
            score -= 10
        elif ratios['roe'] > 0.15: 
            score += 10

    # Sales Growth (jika ada): Pertumbuhan penjualan.
    # Bobot: < -5% (-10), > 15% (+5)
    if ratios.get('sales_growth') is not None:
        if ratios['sales_growth'] < -0.05: 
            score -= 10
        elif ratios['sales_growth'] > 0.15: 
            score += 5
            
    # Batasi skor antara 0 dan 100
    credit_risk_score = max(min_score_possible, min(score, max_score_possible))
    
    # Tentukan Kategori Risiko
    risk_category = ""
    if credit_risk_score >= 70:
        risk_category = "Low Risk"
    elif credit_risk_score >= 40:
        risk_category = "Medium Risk"
    else:
        risk_category = "High Risk"
        
    return {
        "credit_risk_score": credit_risk_score,
        "risk_category": risk_category,
        "underlying_ratios": ratios, # Opsional: kembalikan rasio untuk transparansi
        "altman_z_score_used": altman_z_score_input,
        "beneish_m_score_used": beneish_score_input
    }

if __name__ == '__main__':
    # Contoh penggunaan (untuk pengujian cepat)
    dummy_data_t = {
        "Jumlah aset lancar": 2000, "Jumlah liabilitas jangka pendek": 1000,
        "Jumlah liabilitas": 1500, "Jumlah ekuitas": 2500, "Jumlah aset": 4000,
        "Laba tahun berjalan": 300, "Pendapatan bersih": 3000,
        "Laba sebelum pajak penghasilan": 400, "Beban bunga": 50,
        "Piutang usaha": 500, "Laba bruto": 1000, "Aset tetap": 1500,
        "Beban penyusutan": 150, 
        "Beban penjualan": 300, "Beban administrasi dan umum": 200, # SGA = 500
        "Arus kas bersih yang diperoleh dari aktivitas operasi": 250,
        "Laba ditahan": 1200
    }
    dummy_data_t_minus_1 = {
        "Jumlah aset lancar": 1800, "Jumlah liabilitas jangka pendek": 900,
        "Jumlah liabilitas": 1400, "Jumlah ekuitas": 2000, "Jumlah aset": 3400,
        "Laba tahun berjalan": 200, "Pendapatan bersih": 2500,
        "Laba sebelum pajak penghasilan": 300, "Beban bunga": 40,
        "Piutang usaha": 400, "Laba bruto": 800, "Aset tetap": 1300,
        "Beban penyusutan": 120, 
        "Beban penjualan": 250, "Beban administrasi dan umum": 150, # SGA = 400
    }

    # Skenario 1: Data lengkap, skor Altman & Beneish baik
    print("--- Skenario 1 ---")
    prediction1 = predict_credit_risk_v2(dummy_data_t, dummy_data_t_minus_1, beneish_score_input=-2.0, altman_z_score_input=3.5)
    print(f"Skor Risiko Kredit: {prediction1['credit_risk_score']}, Kategori: {prediction1['risk_category']}")
    # print(f"Rasio: {prediction1['underlying_ratios']}")

    # Skenario 2: Data kurang baik, skor Altman & Beneish buruk
    print("\n--- Skenario 2 ---")
    dummy_data_t_buruk = dummy_data_t.copy()
    dummy_data_t_buruk["Jumlah aset lancar"] = 800
    dummy_data_t_buruk["Laba tahun berjalan"] = 50
    prediction2 = predict_credit_risk_v2(dummy_data_t_buruk, dummy_data_t_minus_1, beneish_score_input=-1.0, altman_z_score_input=1.0)
    print(f"Skor Risiko Kredit: {prediction2['credit_risk_score']}, Kategori: {prediction2['risk_category']}")

    # Skenario 3: Tanpa skor Altman & Beneish
    print("\n--- Skenario 3 ---")
    prediction3 = predict_credit_risk_v2(dummy_data_t, dummy_data_t_minus_1)
    print(f"Skor Risiko Kredit: {prediction3['credit_risk_score']}, Kategori: {prediction3['risk_category']}")
    
    # Skenario 4: Perusahaan Privat dengan Altman Z
    print("\n--- Skenario 4 ---")
    prediction4 = predict_credit_risk_v2(dummy_data_t, dummy_data_t_minus_1, beneish_score_input=-2.5, altman_z_score_input=2.0, altman_is_public=False)
    print(f"Skor Risiko Kredit: {prediction4['credit_risk_score']}, Kategori: {prediction4['risk_category']}")

    # Skenario 5: Data t-1 tidak ada
    print("\n--- Skenario 5 (tanpa data t-1) ---")
    prediction5 = predict_credit_risk_v2(dummy_data_t, None, beneish_score_input=-2.0, altman_z_score_input=3.5)
    print(f"Skor Risiko Kredit: {prediction5['credit_risk_score']}, Kategori: {prediction5['risk_category']}")
    # print(f"Rasio: {prediction5['underlying_ratios']}")
    
    # Skenario 6: Current Ratio buruk, NPM buruk
    print("\n--- Skenario 6 (CR & NPM buruk) ---")
    dummy_data_t_s6 = dummy_data_t.copy()
    dummy_data_t_s6["Jumlah aset lancar"] = 800 # CR = 0.8
    dummy_data_t_s6["Laba tahun berjalan"] = 30 # NPM = 0.01
    prediction6 = predict_credit_risk_v2(dummy_data_t_s6, dummy_data_t_minus_1)
    print(f"Skor Risiko Kredit: {prediction6['credit_risk_score']}, Kategori: {prediction6['risk_category']}")

    # Skenario 7: Leverage sangat tinggi
    print("\n--- Skenario 7 (Leverage Tinggi) ---")
    dummy_data_t_s7 = dummy_data_t.copy()
    dummy_data_t_s7["Jumlah liabilitas"] = 6000 # DtE = 6000/2500 = 2.4
    dummy_data_t_s7["Jumlah aset"] = 8500 # agar liabilitas + ekuitas = aset
    prediction7 = predict_credit_risk_v2(dummy_data_t_s7, dummy_data_t_minus_1)
    print(f"Skor Risiko Kredit: {prediction7['credit_risk_score']}, Kategori: {prediction7['risk_category']}")
    # print(f"Rasio: {prediction7['underlying_ratios']}")

    # Skenario 8: Skor Beneish mengindikasikan manipulasi kuat
    print("\n--- Skenario 8 (Beneish Manipulasi) ---")
    prediction8 = predict_credit_risk_v2(dummy_data_t, dummy_data_t_minus_1, beneish_score_input=0.0, altman_z_score_input=3.5)
    print(f"Skor Risiko Kredit: {prediction8['credit_risk_score']}, Kategori: {prediction8['risk_category']}")
    
    # Skenario 9: Skor Altman zona bahaya kuat
    print("\n--- Skenario 9 (Altman Bahaya) ---")
    prediction9 = predict_credit_risk_v2(dummy_data_t, dummy_data_t_minus_1, beneish_score_input=-2.0, altman_z_score_input=1.0)
    print(f"Skor Risiko Kredit: {prediction9['credit_risk_score']}, Kategori: {prediction9['risk_category']}")

    # Skenario 10: Semua bagus
    print("\n--- Skenario 10 (Semua Bagus) ---")
    good_data_t = {
        "Jumlah aset lancar": 3000, "Jumlah liabilitas jangka pendek": 1000, # CR = 3
        "Jumlah liabilitas": 1500, "Jumlah ekuitas": 3500, "Jumlah aset": 5000, # DtE = 1500/3500 = 0.42
        "Laba tahun berjalan": 750, "Pendapatan bersih": 5000, # NPM = 0.15
        "Laba sebelum pajak penghasilan": 900, "Beban bunga": 50, # EBIT = 950
        "Arus kas bersih yang diperoleh dari aktivitas operasi": 800,
        "Laba ditahan": 2000, "Piutang usaha": 600, "Laba bruto": 2000, 
        "Aset tetap": 1800, "Beban penyusutan": 100, 
        "Beban penjualan": 500, "Beban administrasi dan umum": 300,
    }
    good_data_t_minus_1 = {
        "Pendapatan bersih": 4000, # Sales growth = (5000-4000)/4000 = 0.25
         # data lain bisa sama atau sedikit berbeda, tidak terlalu krusial untuk contoh ini
        "Jumlah aset lancar": 2800, "Jumlah liabilitas jangka pendek": 900, 
        "Jumlah liabilitas": 1400, "Jumlah ekuitas": 3000, "Jumlah aset": 4400, 
        "Laba tahun berjalan": 600, 
        "Laba sebelum pajak penghasilan": 700, "Beban bunga": 40, 
        "Piutang usaha": 500, "Laba bruto": 1800, "Aset tetap": 1600, 
        "Beban penyusutan": 90,  
        "Beban penjualan": 450, "Beban administrasi dan umum": 250, 
    }
    prediction10 = predict_credit_risk_v2(good_data_t, good_data_t_minus_1, beneish_score_input=-2.5, altman_z_score_input=4.0)
    print(f"Skor Risiko Kredit: {prediction10['credit_risk_score']}, Kategori: {prediction10['risk_category']}")
    # print(f"Rasio: {prediction10['underlying_ratios']}")
    # print(f"Altman: {prediction10['altman_z_score_used']}, Beneish: {prediction10['beneish_m_score_used']}")

    # Skenario 11: Semua Buruk
    print("\n--- Skenario 11 (Semua Buruk) ---")
    bad_data_t = {
        "Jumlah aset lancar": 800, "Jumlah liabilitas jangka pendek": 1000, # CR = 0.8
        "Jumlah liabilitas": 3000, "Jumlah ekuitas": 500, "Jumlah aset": 3500, # DtE = 3000/500 = 6
        "Laba tahun berjalan": -200, "Pendapatan bersih": 2000, # NPM = -0.1
        "Laba sebelum pajak penghasilan": -150, "Beban bunga": 100, # EBIT = -50
        "Arus kas bersih yang diperoleh dari aktivitas operasi": -50,
        "Laba ditahan": -500, "Piutang usaha": 700, "Laba bruto": 300, 
        "Aset tetap": 2500, "Beban penyusutan": 300, 
        "Beban penjualan": 800, "Beban administrasi dan umum": 400,
    }
    bad_data_t_minus_1 = {
        "Pendapatan bersih": 2200, # Sales growth = (2000-2200)/2200 = -0.09
        "Jumlah aset lancar": 900, "Jumlah liabilitas jangka pendek": 950, 
        "Jumlah liabilitas": 2800, "Jumlah ekuitas": 600, "Jumlah aset": 3400, 
        "Laba tahun berjalan": -100, 
        "Laba sebelum pajak penghasilan": -80, "Beban bunga": 90, 
        "Piutang usaha": 650, "Laba bruto": 350, "Aset tetap": 2400, 
        "Beban penyusutan": 280,  
        "Beban penjualan": 750, "Beban administrasi dan umum": 380, 
    }
    prediction11 = predict_credit_risk_v2(bad_data_t, bad_data_t_minus_1, beneish_score_input=0.5, altman_z_score_input=0.5)
    print(f"Skor Risiko Kredit: {prediction11['credit_risk_score']}, Kategori: {prediction11['risk_category']}")
    # print(f"Rasio: {prediction11['underlying_ratios']}")
    # print(f"Altman: {prediction11['altman_z_score_used']}, Beneish: {prediction11['beneish_m_score_used']}")

    # Skenario 12: Ekuitas 0 atau negatif (untuk debt_to_equity)
    print("\n--- Skenario 12 (Ekuitas Nol/Negatif) ---")
    zero_equity_data_t = bad_data_t.copy()
    zero_equity_data_t["Jumlah ekuitas"] = 0
    prediction12_zero = predict_credit_risk_v2(zero_equity_data_t, bad_data_t_minus_1)
    print(f"Ekuitas Nol - Skor: {prediction12_zero['credit_risk_score']}, Kategori: {prediction12_zero['risk_category']}, DtE: {prediction12_zero['underlying_ratios'].get('debt_to_equity_ratio')}")
    
    neg_equity_data_t = bad_data_t.copy()
    neg_equity_data_t["Jumlah ekuitas"] = -100
    prediction12_neg = predict_credit_risk_v2(neg_equity_data_t, bad_data_t_minus_1)
    print(f"Ekuitas Negatif - Skor: {prediction12_neg['credit_risk_score']}, Kategori: {prediction12_neg['risk_category']}, DtE: {prediction12_neg['underlying_ratios'].get('debt_to_equity_ratio')}")

    # Skenario 13: Sales 0 (untuk net profit margin)
    print("\n--- Skenario 13 (Sales Nol) ---")
    zero_sales_data_t = bad_data_t.copy()
    zero_sales_data_t["Pendapatan bersih"] = 0
    prediction13 = predict_credit_risk_v2(zero_sales_data_t, bad_data_t_minus_1)
    print(f"Sales Nol - Skor: {prediction13['credit_risk_score']}, Kategori: {prediction13['risk_category']}, NPM: {prediction13['underlying_ratios'].get('net_profit_margin')}")
