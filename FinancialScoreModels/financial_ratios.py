from .utils import safe_division, get_value

# --- Rasio untuk Beneish M-Score ---
# Referensi utama untuk formula Beneish M-Score dan variabelnya:
# Beneish, M. D. (1999). The Detection of Earnings Manipulation. Financial Analysts Journal, 55(5), 24–36.
# Tambahan referensi interpretasi dan variasi: CFA Institute materials, Investopedia.

def calculate_dsri(data_t: dict, data_t_minus_1: dict) -> float | None:
    """
    Menghitung Days' Sales in Receivables Index (DSRI).
    DSRI = (Net Receivables_t / Sales_t) / (Net Receivables_t-1 / Sales_t-1)
    Peningkatan signifikan pada DSRI dapat mengindikasikan potensi penggelembungan pendapatan.
    """
    receivables_t = get_value(data_t, "Piutang usaha", 0)
    sales_t = get_value(data_t, "Pendapatan bersih", 0)
    
    receivables_t_minus_1 = get_value(data_t_minus_1, "Piutang usaha", 0)
    sales_t_minus_1 = get_value(data_t_minus_1, "Pendapatan bersih", 0)

    if any(v is None for v in [receivables_t, sales_t, receivables_t_minus_1, sales_t_minus_1]):
        return None
    if sales_t == 0 or sales_t_minus_1 == 0: # Hindari pembagian dengan nol jika penjualan 0
        return None

    # Asumsi hari dalam setahun adalah 365 untuk konsistensi.
    # Beberapa formula menggunakan hari aktual dalam periode.
    # DSR_t = (Receivables_t / Sales_t)
    # DSR_t_minus_1 = (Receivables_t_minus_1 / Sales_t_minus_1)
    # DSRI = DSR_t / DSR_t_minus_1
    
    # Langsung hitung indeksnya:
    # DSRI = (Receivables_t / Sales_t) / (Receivables_t_minus_1 / Sales_t_minus_1)
    # DSRI = (Receivables_t * Sales_t_minus_1) / (Sales_t * Receivables_t_minus_1)

    numerator = safe_division(receivables_t, sales_t)
    denominator = safe_division(receivables_t_minus_1, sales_t_minus_1)
    
    return safe_division(numerator, denominator)

def calculate_gmi(data_t: dict, data_t_minus_1: dict) -> float | None:
    """
    Menghitung Gross Margin Index (GMI).
    GMI = [(Sales_t-1 - COGS_t-1) / Sales_t-1] / [(Sales_t - COGS_t) / Sales_t]
        = (Gross Profit_t-1 / Sales_t-1) / (Gross Profit_t / Sales_t)
    GMI > 1 menunjukkan penurunan margin kotor, yang bisa menjadi tanda negatif.
    """
    sales_t = get_value(data_t, "Pendapatan bersih", 0)
    gross_profit_t = get_value(data_t, "Laba bruto", 0)
    
    sales_t_minus_1 = get_value(data_t_minus_1, "Pendapatan bersih", 0)
    gross_profit_t_minus_1 = get_value(data_t_minus_1, "Laba bruto", 0)

    if any(v is None for v in [sales_t, gross_profit_t, sales_t_minus_1, gross_profit_t_minus_1]):
        return None
    if sales_t == 0 or sales_t_minus_1 == 0:
        return None
        
    gm_t_minus_1 = safe_division(gross_profit_t_minus_1, sales_t_minus_1)
    gm_t = safe_division(gross_profit_t, sales_t)
    
    return safe_division(gm_t_minus_1, gm_t)

def calculate_aqi(data_t: dict, data_t_minus_1: dict) -> float | None:
    """
    Menghitung Asset Quality Index (AQI).
    AQI = [1 – (Current Assets_t + Net PP&E_t) / Total Assets_t] / 
          [1 – (Current Assets_t-1 + Net PP&E_t-1) / Total Assets_t-1]
    Ini mengukur proporsi aset selain aset lancar dan PP&E (aset tidak produktif/lunak).
    AQI > 1 dapat mengindikasikan peningkatan upaya kapitalisasi atau penundaan pengakuan beban.
    """
    ca_t = get_value(data_t, "Jumlah aset lancar", 0)
    ppe_net_t = get_value(data_t, "Aset tetap", 0) # Aset Tetap Bersih (Net PP&E)
    total_assets_t = get_value(data_t, "Jumlah aset", 0)

    ca_t_minus_1 = get_value(data_t_minus_1, "Jumlah aset lancar", 0)
    ppe_net_t_minus_1 = get_value(data_t_minus_1, "Aset tetap", 0)
    total_assets_t_minus_1 = get_value(data_t_minus_1, "Jumlah aset", 0)

    if any(v is None for v in [ca_t, ppe_net_t, total_assets_t, ca_t_minus_1, ppe_net_t_minus_1, total_assets_t_minus_1]):
        return None
    if total_assets_t == 0 or total_assets_t_minus_1 == 0:
        return None

    # Proporsi aset lunak tahun t = 1 - ((CA_t + PPE_Net_t) / TA_t)
    soft_assets_ratio_t_num = total_assets_t - (ca_t + ppe_net_t)
    soft_assets_ratio_t = safe_division(soft_assets_ratio_t_num, total_assets_t)

    # Proporsi aset lunak tahun t-1 = 1 - ((CA_t-1 + PPE_Net_t-1) / TA_t-1)
    soft_assets_ratio_t_minus_1_num = total_assets_t_minus_1 - (ca_t_minus_1 + ppe_net_t_minus_1)
    soft_assets_ratio_t_minus_1 = safe_division(soft_assets_ratio_t_minus_1_num, total_assets_t_minus_1)
    
    if soft_assets_ratio_t is None or soft_assets_ratio_t_minus_1 is None:
        return None

    return safe_division(soft_assets_ratio_t, soft_assets_ratio_t_minus_1)


def calculate_sgi(data_t: dict, data_t_minus_1: dict) -> float | None:
    """
    Menghitung Sales Growth Index (SGI).
    SGI = Sales_t / Sales_t-1
    Pertumbuhan penjualan yang tinggi, meskipun positif, bisa juga dikaitkan dengan tekanan untuk
    mempertahankan pertumbuhan yang dapat mendorong manipulasi.
    """
    sales_t = get_value(data_t, "Pendapatan bersih", 0)
    sales_t_minus_1 = get_value(data_t_minus_1, "Pendapatan bersih", 0)
    
    return safe_division(sales_t, sales_t_minus_1)

def calculate_depi(data_t: dict, data_t_minus_1: dict) -> float | None:
    """
    Menghitung Depreciation Index (DEPI).
    DEPI = Depreciation Rate_t-1 / Depreciation Rate_t
    Dimana Depreciation Rate = Depreciation_t / (Depreciation_t + Net PP&E_t)
    DEPI > 1 menunjukkan bahwa tingkat penyusutan aset melambat, yang mungkin
    mengindikasikan perusahaan merevisi umur manfaat aset ke atas atau menggunakan metode
    yang menurunkan beban penyusutan untuk meningkatkan laba.
    """
    dep_expense_t = get_value(data_t, "Beban penyusutan", 0)
    ppe_net_t = get_value(data_t, "Aset tetap", 0) # Aset Tetap Bersih
    
    dep_expense_t_minus_1 = get_value(data_t_minus_1, "Beban penyusutan", 0)
    ppe_net_t_minus_1 = get_value(data_t_minus_1, "Aset tetap", 0)

    if any(v is None for v in [dep_expense_t, ppe_net_t, dep_expense_t_minus_1, ppe_net_t_minus_1]):
        return None

    dep_rate_t_denom = dep_expense_t + ppe_net_t
    dep_rate_t = safe_division(dep_expense_t, dep_rate_t_denom)

    dep_rate_t_minus_1_denom = dep_expense_t_minus_1 + ppe_net_t_minus_1
    dep_rate_t_minus_1 = safe_division(dep_expense_t_minus_1, dep_rate_t_minus_1_denom)
    
    if dep_rate_t is None or dep_rate_t_minus_1 is None:
        return None

    return safe_division(dep_rate_t_minus_1, dep_rate_t)

def calculate_sgai(data_t: dict, data_t_minus_1: dict) -> float | None:
    """
    Menghitung Sales, General, and Administrative Expenses Index (SGAI).
    SGAI = (SGA Expenses_t / Sales_t) / (SGA Expenses_t-1 / Sales_t-1)
    Peningkatan SGAI (nilai > 1) mungkin menunjukkan inefisiensi, tetapi dalam konteks manipulasi,
    perusahaan yang memanipulasi laba mungkin menunjukkan peningkatan yang tidak proporsional
    dalam beban ini relatif terhadap penjualan.
    """
    # Coba dapatkan Beban Penjualan dan Beban Adm & Umum secara terpisah, lalu jumlahkan.
    # Jika tidak ada, gunakan Beban Usaha sebagai proxy.
    s_exp_t = get_value(data_t, "Beban penjualan", 0)
    ga_exp_t = get_value(data_t, "Beban administrasi dan umum", 0)
    sga_t = None
    if s_exp_t is not None and ga_exp_t is not None:
        sga_t = s_exp_t + ga_exp_t
    elif get_value(data_t, "Beban usaha", 0) is not None: # Fallback ke Beban Usaha
        sga_t = get_value(data_t, "Beban usaha", 0)
            
    sales_t = get_value(data_t, "Pendapatan bersih", 0)

    s_exp_tm1 = get_value(data_t_minus_1, "Beban penjualan", 0)
    ga_exp_tm1 = get_value(data_t_minus_1, "Beban administrasi dan umum", 0)
    sga_t_minus_1 = None
    if s_exp_tm1 is not None and ga_exp_tm1 is not None:
        sga_t_minus_1 = s_exp_tm1 + ga_exp_tm1
    elif get_value(data_t_minus_1, "Beban usaha", 0) is not None: # Fallback ke Beban Usaha
        sga_t_minus_1 = get_value(data_t_minus_1, "Beban usaha", 0)
            
    sales_t_minus_1 = get_value(data_t_minus_1, "Pendapatan bersih", 0)

    if any(v is None for v in [sga_t, sales_t, sga_t_minus_1, sales_t_minus_1]):
        return None
    if sales_t == 0 or sales_t_minus_1 == 0:
        return None

    sga_ratio_t = safe_division(sga_t, sales_t)
    sga_ratio_t_minus_1 = safe_division(sga_t_minus_1, sales_t_minus_1)
    
    return safe_division(sga_ratio_t, sga_ratio_t_minus_1)

def calculate_lvgi(data_t: dict, data_t_minus_1: dict) -> float | None:
    """
    Menghitung Leverage Index (LVGI).
    LVGI = (Total Liabilities_t / Total Assets_t) / (Total Liabilities_t-1 / Total Assets_t-1)
    LVGI > 1 menunjukkan peningkatan leverage, yang bisa menjadi sinyal negatif.
    """
    total_liabilities_t = get_value(data_t, "Jumlah liabilitas", 0)
    total_assets_t = get_value(data_t, "Jumlah aset", 0)
    
    total_liabilities_t_minus_1 = get_value(data_t_minus_1, "Jumlah liabilitas", 0)
    total_assets_t_minus_1 = get_value(data_t_minus_1, "Jumlah aset", 0)

    if any(v is None for v in [total_liabilities_t, total_assets_t, total_liabilities_t_minus_1, total_assets_t_minus_1]):
        return None

    lev_t = safe_division(total_liabilities_t, total_assets_t)
    lev_t_minus_1 = safe_division(total_liabilities_t_minus_1, total_assets_t_minus_1)

    return safe_division(lev_t, lev_t_minus_1)

def calculate_tata(data_t: dict) -> float | None:
    """
    Menghitung Total Accruals to Total Assets (TATA).
    TATA = (Net Income_t – Cash Flow From Operations_t) / Total Assets_t
    Laba Tahun Berjalan digunakan sebagai proxy untuk Net Income.
    Akrual yang tinggi bisa mengindikasikan manipulasi laba.
    """
    net_income_t = get_value(data_t, "Laba tahun berjalan", 0)
    cfo_t = get_value(data_t, "Arus kas bersih yang diperoleh dari aktivitas operasi", 0)
    total_assets_t = get_value(data_t, "Jumlah aset", 0)

    if any(v is None for v in [net_income_t, cfo_t, total_assets_t]):
        return None
    
    total_accruals = net_income_t - cfo_t
    return safe_division(total_accruals, total_assets_t)


# --- Rasio untuk Altman Z-Score ---
# Referensi utama:
# Altman, E. I. (1968). Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy. The Journal of Finance, 23(4), 589-609.
# Altman, E. I. (2000). Predicting financial distress of companies: revisiting the Z-score and ZETA models. Stern School of Business, New York University.

def calculate_x1_working_capital_to_total_assets(data_t: dict) -> float | None:
    """
    Menghitung X1 untuk Altman Z-Score.
    X1 = (Current Assets - Current Liabilities) / Total Assets
       = Working Capital / Total Assets
    Mengukur likuiditas aset relatif terhadap ukuran perusahaan.
    """
    current_assets = get_value(data_t, "Jumlah aset lancar", 0)
    current_liabilities = get_value(data_t, "Jumlah liabilitas jangka pendek", 0)
    total_assets = get_value(data_t, "Jumlah aset", 0)

    if any(v is None for v in [current_assets, current_liabilities, total_assets]):
        return None
        
    working_capital = current_assets - current_liabilities
    return safe_division(working_capital, total_assets)

def calculate_x2_retained_earnings_to_total_assets(data_t: dict) -> float | None:
    """
    Menghitung X2 untuk Altman Z-Score.
    X2 = Retained Earnings / Total Assets
    Mengukur profitabilitas kumulatif perusahaan.
    """
    retained_earnings = get_value(data_t, "Laba ditahan", 0)
    total_assets = get_value(data_t, "Jumlah aset", 0)
    
    return safe_division(retained_earnings, total_assets)

def calculate_x3_ebit_to_total_assets(data_t: dict) -> float | None:
    """
    Menghitung X3 untuk Altman Z-Score.
    X3 = Earnings Before Interest and Taxes (EBIT) / Total Assets
    Mengukur efisiensi operasi terlepas dari faktor pajak dan leverage.
    EBIT diestimasi sebagai Laba Sebelum Pajak + Beban Bunga.
    """
    ebt = get_value(data_t, "Laba sebelum pajak penghasilan", 0)
    interest_expense = get_value(data_t, "Beban bunga", 0)
    total_assets = get_value(data_t, "Jumlah aset", 0)

    if ebt is None or total_assets is None:
        return None
    
    ebit = ebt
    if interest_expense is not None: # Jika Beban Bunga ada, tambahkan kembali
        ebit += interest_expense 
        
    return safe_division(ebit, total_assets)

def calculate_x4_market_value_equity_to_total_liabilities(data_t: dict, market_value_equity: float = None) -> float | None:
    """
    Menghitung X4 untuk Altman Z-Score.
    Untuk perusahaan publik: X4 = Market Value of Equity / Total Liabilities.
    Untuk perusahaan privat: X4 = Book Value of Equity / Total Liabilities.
    Mengukur seberapa jauh aset perusahaan dapat menurun sebelum liabilitas melebihi aset.
    """
    total_liabilities = get_value(data_t, "Jumlah liabilitas", 0)
    
    equity_val_for_ratio = None
    if market_value_equity is not None: # Jika nilai pasar disediakan (untuk publik)
        equity_val_for_ratio = market_value_equity
    else: # Gunakan nilai buku ekuitas (untuk privat atau jika pasar tidak ada utk publik)
        equity_val_for_ratio = get_value(data_t, "Jumlah ekuitas", 0)

    return safe_division(equity_val_for_ratio, total_liabilities)

def calculate_x5_sales_to_total_assets(data_t: dict) -> float | None:
    """
    Menghitung X5 untuk Altman Z-Score.
    X5 = Sales / Total Assets
    Mengukur kemampuan aset perusahaan untuk menghasilkan penjualan (asset turnover).
    """
    sales = get_value(data_t, "Pendapatan bersih", 0)
    total_assets = get_value(data_t, "Jumlah aset", 0)
    
    return safe_division(sales, total_assets)
