def calculate_beneish_m_score(data_t, data_t_minus_1):
    """
    Menghitung Beneish M-Score untuk mendeteksi potensi manipulasi laporan keuangan.

    Args:
        data_t (dict): Data keuangan periode t (tahun berjalan).
                       Struktur: {'nama_item_keuangan': nilai, ...}
        data_t_minus_1 (dict): Data keuangan periode t-1 (tahun sebelumnya).
                               Struktur: {'nama_item_keuangan': nilai, ...}

    Returns:
        tuple: (float, dict) -> Nilai Beneish M-Score dan dictionary rasio-rasio Beneish.
               Mengembalikan (None, None) jika ada data keuangan penting yang hilang.
    """
    required_keys_t = [
        "Piutang usaha", "Pendapatan bersih", "Laba bruto",
        "Jumlah aset tidak lancar", "Jumlah aset", "Beban penyusutan",
        "Aset tetap bruto", "Beban penjualan", "Beban administrasi dan umum",
        "Jumlah liabilitas", "Laba tahun berjalan",
        "Arus kas bersih yang diperoleh dari aktivitas operasi",
        "Jumlah aset lancar", "Aset tetap" # Aset tetap netto
    ]
    required_keys_t_minus_1 = [
        "Piutang usaha", "Pendapatan bersih", "Laba bruto",
        "Jumlah aset tidak lancar", "Jumlah aset", "Beban penyusutan",
        "Aset tetap bruto", "Beban penjualan", "Beban administrasi dan umum",
        "Jumlah liabilitas",
        "Jumlah aset lancar", "Aset tetap" # Aset tetap netto
    ]

    for key in required_keys_t:
        if key not in data_t:
            # print(f"Error: Data keuangan periode t tidak lengkap. Item yang hilang: {key}")
            return None, {"error": f"Missing item in data_t: {key}"}
    for key in required_keys_t_minus_1:
        if key not in data_t_minus_1:
            # print(f"Error: Data keuangan periode t-1 tidak lengkap. Item yang hilang: {key}")
            return None, {"error": f"Missing item in data_t_minus_1: {key}"}

    try:
        # Periode t
        receivables_t = float(data_t["Piutang usaha"])
        sales_t = float(data_t["Pendapatan bersih"])
        gross_profit_t = float(data_t["Laba bruto"])
        # non_current_assets_t = float(data_t["Jumlah aset tidak lancar"]) # Digunakan di AQI jika Aset tetap tidak ada
        total_assets_t = float(data_t["Jumlah aset"])
        depreciation_t = float(data_t["Beban penyusutan"])
        ppe_gross_t = float(data_t["Aset tetap bruto"])
        sga_expenses_t = float(data_t["Beban penjualan"]) + float(data_t["Beban administrasi dan umum"])
        total_liabilities_t = float(data_t["Jumlah liabilitas"])
        net_income_t = float(data_t["Laba tahun berjalan"])
        cfo_t = float(data_t["Arus kas bersih yang diperoleh dari aktivitas operasi"])
        current_assets_t = float(data_t["Jumlah aset lancar"])
        ppe_net_t = float(data_t["Aset tetap"])


        # Periode t-1
        receivables_t_minus_1 = float(data_t_minus_1["Piutang usaha"])
        sales_t_minus_1 = float(data_t_minus_1["Pendapatan bersih"])
        gross_profit_t_minus_1 = float(data_t_minus_1["Laba bruto"])
        # non_current_assets_t_minus_1 = float(data_t_minus_1["Jumlah aset tidak lancar"])
        total_assets_t_minus_1 = float(data_t_minus_1["Jumlah aset"])
        depreciation_t_minus_1 = float(data_t_minus_1["Beban penyusutan"])
        ppe_gross_t_minus_1 = float(data_t_minus_1["Aset tetap bruto"])
        sga_expenses_t_minus_1 = float(data_t_minus_1["Beban penjualan"]) + float(data_t_minus_1["Beban administrasi dan umum"])
        total_liabilities_t_minus_1 = float(data_t_minus_1["Jumlah liabilitas"])
        current_assets_t_minus_1 = float(data_t_minus_1["Jumlah aset lancar"])
        ppe_net_t_minus_1 = float(data_t_minus_1["Aset tetap"])


    except KeyError as e:
        # Seharusnya sudah ditangani oleh pemeriksaan di atas, tapi sebagai fallback
        return None, {"error": f"KeyError during data extraction: {e}"}
    except ValueError as e:
        return None, {"error": f"ValueError, data tidak dapat dikonversi ke float: {e}"}


    ratios = {}

    # 1. DSRI (Days' Sales in Receivables Index)
    if sales_t == 0 or sales_t_minus_1 == 0 or receivables_t_minus_1 == 0 or (receivables_t_minus_1 / sales_t_minus_1) == 0:
        dsri = 1.0
    else:
        dsri = (receivables_t / sales_t) / (receivables_t_minus_1 / sales_t_minus_1)
    ratios["DSRI"] = dsri

    # 2. GMI (Gross Margin Index)
    if sales_t == 0 or sales_t_minus_1 == 0:
        gm_t = 0.0
        gm_t_minus_1 = 0.0
    else:
        gm_t = gross_profit_t / sales_t
        gm_t_minus_1 = gross_profit_t_minus_1 / sales_t_minus_1
    
    if gm_t == 0:
        gmi = 1.0
    else:
        gmi = gm_t_minus_1 / gm_t
    ratios["GMI"] = gmi

    # 3. AQI (Asset Quality Index)
    # AQI = [1 – (CurrentAssets_t + Net_PPE_t) / TotalAssets_t] / [1 – (CurrentAssets_t-1 + Net_PPE_t-1) / TotalAssets_t-1]
    # Net_PPE_t adalah Aset tetap (Net)
    if total_assets_t == 0 or total_assets_t_minus_1 == 0:
        aqi = 1.0
    else:
        # proporsi aset non-produktif (aset selain CA dan Net PPE)
        asset_quality_component_t = 1 - ((current_assets_t + ppe_net_t) / total_assets_t)
        asset_quality_component_t_minus_1 = 1 - ((current_assets_t_minus_1 + ppe_net_t_minus_1) / total_assets_t_minus_1)
        
        if asset_quality_component_t_minus_1 == 0:
            # Jika di periode t-1 semua aset adalah Current Asset + PPE Net,
            # dan di periode t ada aset non-produktif, ini adalah peningkatan risiko.
            # Untuk menghindari pembagian dengan nol dan mencerminkan ini, kita bisa set AQI ke nilai tinggi jika asset_quality_component_t > 0
            # Namun, untuk konsistensi, jika denominator 0, kita set ke 1 (netral) atau nilai yang menunjukkan perubahan signifikan.
            # Beneish paper implies if the denominator is zero and numerator is non-zero this is a red flag.
            # For now, setting to 1.0 to avoid extreme values from division by a very small number if not exactly zero.
            aqi = 1.0 if asset_quality_component_t == 0 else 2.0 # Default 1, jika ada perubahan signifikan bisa > 1
        else:
            aqi = asset_quality_component_t / asset_quality_component_t_minus_1
    ratios["AQI"] = aqi

    # 4. SGI (Sales Growth Index)
    if sales_t_minus_1 == 0:
        sgi = 1.0 if sales_t == 0 else 2.0 # Jika sales t-1 nol dan sales t > 0, pertumbuhan besar
    else:
        sgi = sales_t / sales_t_minus_1
    ratios["SGI"] = sgi

    # 5. DEPI (Depreciation Index)
    # DEPI = (RatePenyusutan_t-1) / (RatePenyusutan_t)
    # RatePenyusutan = Penyusutan / (Penyusutan + PPE_Gross)
    # RatePenyusutan = Penyusutan / PPE_Net (alternatif jika PPE Gross tidak ada, tapi PPE Gross lebih tepat)
    # Menggunakan PPE Gross sesuai formula asli
    if (depreciation_t_minus_1 + ppe_gross_t_minus_1) == 0:
        depi_rate_t_minus_1 = 0 # Tidak ada aset yg disusutkan atau tidak ada penyusutan
    else:
        depi_rate_t_minus_1 = depreciation_t_minus_1 / (depreciation_t_minus_1 + ppe_gross_t_minus_1)

    if (depreciation_t + ppe_gross_t) == 0:
        depi_rate_t = 0 # Tidak ada aset yg disusutkan atau tidak ada penyusutan
    else:
        depi_rate_t = depreciation_t / (depreciation_t + ppe_gross_t)

    if depi_rate_t == 0:
        # Jika rate penyusutan tahun ini 0, dan tahun lalu tidak 0, DEPI akan besar (menunjukkan penurunan rate penyusutan)
        depi = 1.0 if depi_rate_t_minus_1 == 0 else 2.0 # Default 1, jika ada perubahan signifikan bisa > 1
    else:
        depi = depi_rate_t_minus_1 / depi_rate_t
    ratios["DEPI"] = depi

    # 6. SGAI (Sales, General, and Administrative Expenses Index)
    if sales_t == 0 or sales_t_minus_1 == 0 :
        sgai = 1.0
    else:
        sgai_ratio_t = sga_expenses_t / sales_t
        sgai_ratio_t_minus_1 = sga_expenses_t_minus_1 / sales_t_minus_1
        if sgai_ratio_t_minus_1 == 0:
            sgai = 1.0 if sgai_ratio_t == 0 else 2.0 # Default 1, jika ada perubahan signifikan bisa > 1
        else:
            sgai = sgai_ratio_t / sgai_ratio_t_minus_1
    ratios["SGAI"] = sgai

    # 7. LVGI (Leverage Index)
    if total_assets_t == 0 or total_assets_t_minus_1 == 0:
        lvgi = 1.0
    else:
        leverage_t = total_liabilities_t / total_assets_t
        leverage_t_minus_1 = total_liabilities_t_minus_1 / total_assets_t_minus_1
        if leverage_t_minus_1 == 0:
            lvgi = 1.0 if leverage_t == 0 else 2.0 # Default 1, jika ada perubahan signifikan bisa > 1
        else:
            lvgi = leverage_t / leverage_t_minus_1
    ratios["LVGI"] = lvgi

    # 8. TATA (Total Accruals to Total Assets)
    if total_assets_t == 0:
        tata = 0.0
    else:
        tata = (net_income_t - cfo_t) / total_assets_t
    ratios["TATA"] = tata

    m_score = -4.84 + (0.920 * dsri) + (0.528 * gmi) + (0.404 * aqi) + \
              (0.892 * sgi) + (0.115 * depi) - (0.172 * sgai) + \
              (4.679 * tata) - (0.327 * lvgi)
    
    # Alternatif M-Score (8-variable model without LVGI, common in some literature)
    # m_score_alt = -4.84 + (0.920 * dsri) + (0.528 * gmi) + (0.404 * aqi) + \
    #               (0.892 * sgi) + (0.115 * depi) - (0.172 * sgai) + (4.679 * tata)
    # ratios["M_SCORE_NO_LVGI"] = m_score_alt


    return m_score, ratios

def get_beneish_m_score_analysis(data_t, data_t_minus_1):
    """
    Menganalisis perusahaan menggunakan Beneish M-Score.

    Args:
        data_t (dict): Data keuangan periode t (tahun berjalan).
        data_t_minus_1 (dict): Data keuangan periode t-1 (tahun sebelumnya).

    Returns:
        dict: Hasil analisis Beneish M-Score, termasuk skor, rasio, dan interpretasi.
    """
    if data_t is None or data_t_minus_1 is None:
        return {
            "m_score": None,
            "ratios": None,
            "interpretation": "Data tidak lengkap untuk menghitung Beneish M-Score.",
            "error": "Data t atau t-1 tidak disediakan."
        }

    m_score, ratios = calculate_beneish_m_score(data_t, data_t_minus_1)
    interpretation = "Tidak dapat diinterpretasi karena skor tidak dihitung."

    if m_score is not None:
        if m_score > -1.78:
            interpretation = "Kemungkinan besar perusahaan adalah manipulator (manipulator threshold)."
        elif m_score > -2.22: # Threshold umum, beberapa literatur menggunakan -2.22
            interpretation = "Zona abu-abu, perlu investigasi lebih lanjut."
        else:
            interpretation = "Kemungkinan kecil perusahaan adalah manipulator."
    elif ratios and "error" in ratios:
        interpretation = f"Error dalam perhitungan: {ratios['error']}"


    return {
        "m_score": m_score,
        "ratios": ratios,
        "interpretation": interpretation
    }

if __name__ == '__main__':
    data_t_example = {
        "Piutang usaha": 13200000000000.0, "Pendapatan bersih": 108249000000000.0, "Laba bruto": 10511000000000.0,
        "Jumlah aset tidak lancar": 81765000000000.0, "Jumlah aset": 101003000000000.0, 
        "Beban penyusutan": 2750000000000.0, "Aset tetap bruto": 66000000000000.0, 
        "Beban penjualan": 3300000000000.0, "Beban administrasi dan umum": 2200000000000.0,
        "Jumlah liabilitas": 16289000000000.0, "Laba tahun berjalan": 21661000000000.0,
        "Arus kas bersih yang diperoleh dari aktivitas operasi": 3135000000000.0,
        "Jumlah aset lancar": 19238000000000.0, "Aset tetap": 55000000000000.0
    }
    data_t_minus_1_example = {
        "Piutang usaha": 12000000000000.0, "Pendapatan bersih": 95000000000000.0, "Laba bruto": 10000000000000.0,
        "Jumlah aset tidak lancar": 75000000000000.0, "Jumlah aset": 93000000000000.0, 
        "Beban penyusutan": 2500000000000.0, "Aset tetap bruto": 60000000000000.0, 
        "Beban penjualan": 3000000000000.0, "Beban administrasi dan umum": 2000000000000.0,
        "Jumlah liabilitas": 14800000000000.0, "Laba tahun berjalan": 19600000000000.0, # Laba tahun berjalan t-1 tidak dipakai di formula M-score
        "Arus kas bersih yang diperoleh dari aktivitas operasi": 2800000000000.0, # CFO t-1 tidak dipakai
        "Jumlah aset lancar": 1800000000000.0, "Aset tetap": 50000000000000.0
    }

    print("Contoh Perhitungan Normal:")
    m_score_val, beneish_ratios = calculate_beneish_m_score(data_t_example, data_t_minus_1_example)

    if m_score_val is not None:
        print(f"Beneish M-Score: {m_score_val:.4f}")
        print("Rasio Beneish:")
        for ratio_name, ratio_value in beneish_ratios.items():
            if ratio_name != "error":
                 print(f"  {ratio_name}: {ratio_value:.4f}")
        if m_score_val > -1.78:
             print("Interpretasi: Kemungkinan besar perusahaan adalah manipulator.")
        elif m_score_val > -2.22:
             print("Interpretasi: Zona abu-abu, perlu investigasi lebih lanjut.")
        else:
             print("Interpretasi: Kemungkinan kecil perusahaan adalah manipulator.")
    else:
        print(f"Tidak dapat menghitung Beneish M-Score: {beneish_ratios.get('error', 'Alasan tidak diketahui')}")

    # Test case dengan data hilang
    print("\nTest dengan Data Hilang:")
    data_t_missing = data_t_example.copy()
    del data_t_missing["Piutang usaha"]
    m_score_missing, ratios_missing = calculate_beneish_m_score(data_t_missing, data_t_minus_1_example)
    if m_score_missing is None:
        print(f"Berhasil menangani data hilang: {ratios_missing.get('error')}")
    else:
        print("Gagal menangani data hilang.")

    # Test case dengan sales_t = 0
    print("\nTest dengan Sales t = 0:")
    data_t_zero_sales = data_t_example.copy()
    data_t_zero_sales["Pendapatan bersih"] = 0
    data_t_zero_sales["Laba bruto"] = 0 # Jika sales 0, gross profit juga 0
    m_score_zero_s_t, ratios_zero_s_t = calculate_beneish_m_score(data_t_zero_sales, data_t_minus_1_example)
    if m_score_zero_s_t is not None:
        print(f"M-Score (Sales t=0): {m_score_zero_s_t:.4f}")
        print(f"  DSRI: {ratios_zero_s_t['DSRI']:.4f}, GMI: {ratios_zero_s_t['GMI']:.4f}, SGAI: {ratios_zero_s_t['SGAI']:.4f}")
    else:
        print(f"Gagal menghitung (Sales t=0): {ratios_zero_s_t.get('error')}")

    # Test case dengan sales_t-1 = 0
    print("\nTest dengan Sales t-1 = 0:")
    data_t_minus_1_zero_sales = data_t_minus_1_example.copy()
    data_t_minus_1_zero_sales["Pendapatan bersih"] = 0
    data_t_minus_1_zero_sales["Laba bruto"] = 0
    m_score_zero_s_tm1, ratios_zero_s_tm1 = calculate_beneish_m_score(data_t_example, data_t_minus_1_zero_sales)
    if m_score_zero_s_tm1 is not None:
        print(f"M-Score (Sales t-1=0): {m_score_zero_s_tm1:.4f}")
        print(f"  DSRI: {ratios_zero_s_tm1['DSRI']:.4f}, GMI: {ratios_zero_s_tm1['GMI']:.4f}, SGI: {ratios_zero_s_tm1['SGI']:.4f}, SGAI: {ratios_zero_s_tm1['SGAI']:.4f}")
    else:
        print(f"Gagal menghitung (Sales t-1=0): {ratios_zero_s_tm1.get('error')}")

    # Test AQI denominator = 0
    # asset_quality_component_t_minus_1 = 1 - ((current_assets_t_minus_1 + ppe_net_t_minus_1) / total_assets_t_minus_1)
    # Make this zero: (current_assets_t_minus_1 + ppe_net_t_minus_1) / total_assets_t_minus_1 = 1
    # So, current_assets_t_minus_1 + ppe_net_t_minus_1 = total_assets_t_minus_1
    print("\nTest dengan AQI denominator t-1 = 0:")
    data_t_minus_1_aqi_zero = data_t_minus_1_example.copy()
    data_t_minus_1_aqi_zero["Jumlah aset lancar"] = data_t_minus_1_aqi_zero["Jumlah aset"] - data_t_minus_1_aqi_zero["Aset tetap"]
    # Ensure total_assets_t_minus_1 is not zero
    if data_t_minus_1_aqi_zero["Jumlah aset"] == 0: data_t_minus_1_aqi_zero["Jumlah aset"] = 1000 # dummy value if it was zero
    
    m_score_aqi, ratios_aqi = calculate_beneish_m_score(data_t_example, data_t_minus_1_aqi_zero)
    if m_score_aqi is not None:
        print(f"M-Score (AQI denom t-1=0): {m_score_aqi:.4f}")
        print(f"  AQI: {ratios_aqi['AQI']:.4f}")
    else:
        print(f"Gagal menghitung (AQI denom t-1=0): {ratios_aqi.get('error')}")

    # Test DEPI rate t = 0
    print("\nTest dengan DEPI rate t = 0:")
    data_t_depi_zero = data_t_example.copy()
    data_t_depi_zero["Beban penyusutan"] = 0 
    # Assuming ppe_gross_t is not zero
    m_score_depi, ratios_depi = calculate_beneish_m_score(data_t_depi_zero, data_t_minus_1_example)
    if m_score_depi is not None:
        print(f"M-Score (DEPI rate t=0): {m_score_depi:.4f}")
        print(f"  DEPI: {ratios_depi['DEPI']:.4f}")
    else:
        print(f"Gagal menghitung (DEPI rate t=0): {ratios_depi.get('error')}")

    # Test LVGI denominator t-1 = 0
    print("\nTest dengan LVGI denominator t-1 = 0 (Total Assets t-1 = 0):")
    data_t_minus_1_lvgi_zero_assets = data_t_minus_1_example.copy()
    data_t_minus_1_lvgi_zero_assets["Jumlah aset"] = 0
    m_score_lvgi_assets, ratios_lvgi_assets = calculate_beneish_m_score(data_t_example, data_t_minus_1_lvgi_zero_assets)
    if m_score_lvgi_assets is not None:
        print(f"M-Score (LVGI Total Assets t-1=0): {m_score_lvgi_assets:.4f}")
        print(f"  LVGI: {ratios_lvgi_assets['LVGI']:.4f}")
    else:
        print(f"Gagal menghitung (LVGI Total Assets t-1=0): {ratios_lvgi_assets.get('error')}")

    print("\nTest dengan LVGI leverage t-1 = 0 (Total Liabilities t-1 = 0):")
    data_t_minus_1_lvgi_zero_liab = data_t_minus_1_example.copy()
    data_t_minus_1_lvgi_zero_liab["Jumlah liabilitas"] = 0
    m_score_lvgi_liab, ratios_lvgi_liab = calculate_beneish_m_score(data_t_example, data_t_minus_1_lvgi_zero_liab)
    if m_score_lvgi_liab is not None:
        print(f"M-Score (LVGI Liab t-1=0): {m_score_lvgi_liab:.4f}")
        print(f"  LVGI: {ratios_lvgi_liab['LVGI']:.4f}")
    else:
        print(f"Gagal menghitung (LVGI Liab t-1=0): {ratios_lvgi_liab.get('error')}")