def calculate_common_financial_ratios(data_t):
    """
    Menghitung beberapa rasio keuangan umum yang sering digunakan dalam analisis kredit dan kesehatan keuangan.

    Args:
        data_t (dict): Data keuangan periode t (tahun berjalan).
                       Struktur: {'nama_item_keuangan': nilai, ...}

    Returns:
        dict: Dictionary yang berisi rasio-rasio keuangan yang dihitung.
              Mengembalikan dictionary dengan pesan error jika data tidak cukup.
    """
    required_keys = [
        "Jumlah liabilitas", "Jumlah ekuitas", # Untuk Debt-to-Equity
        "Jumlah aset lancar", "Jumlah liabilitas jangka pendek", # Untuk Current Ratio
        "Laba/rugi sebelum pajak penghasilan", "Beban bunga", # Untuk Interest Coverage Ratio
        "Laba/rugi tahun berjalan", "Pendapatan bersih" # Untuk Net Profit Margin
    ]

    # Cek apakah semua kunci yang dibutuhkan ada
    missing_keys = [key for key in required_keys if key not in data_t]
    if missing_keys:
        return {"error": f"Missing items in data_t for financial ratios: {', '.join(missing_keys)}"}

    try:
        # Konversi semua nilai yang akan digunakan ke float
        total_liabilities = float(data_t["Jumlah liabilitas"])
        total_equity = float(data_t["Jumlah ekuitas"])
        current_assets = float(data_t["Jumlah aset lancar"])
        current_liabilities = float(data_t["Jumlah liabilitas jangka pendek"])
        ebit = float(data_t["Laba/rugi sebelum pajak penghasilan"]) + float(data_t.get("Beban bunga", 0)) # Beban bunga bisa 0
        interest_expense = float(data_t.get("Beban bunga", 0)) # Beban bunga bisa 0
        net_income = float(data_t["Laba/rugi tahun berjalan"])
        sales = float(data_t["Pendapatan bersih"])
        
        # Pastikan ada beban bunga jika ebit digunakan untuk ICR
        if "Beban bunga" not in data_t and "Laba/rugi sebelum pajak penghasilan" in data_t :
             # Jika beban bunga tidak ada, ICR tidak bisa dihitung dengan cara standar
             # namun kita bisa asumsikan 0 jika memang tidak ada.
             # 'Beban bunga' sudah di-default ke 0 di atas.
             pass


    except ValueError as e:
        return {"error": f"ValueError, data tidak dapat dikonversi ke float untuk rasio: {e}"}
    except KeyError as e: # Seharusnya sudah ditangani oleh missing_keys, tapi sebagai fallback
        return {"error": f"KeyError during data extraction for ratios: {e}"}

    ratios = {}

    # 1. Debt-to-Equity Ratio
    if total_equity == 0:
        # Jika ekuitas nol, rasio ini tidak terdefinisi atau sangat tinggi jika ada utang.
        # Jika utang juga nol, bisa dianggap 0. Jika utang > 0, sangat berisiko.
        ratios["Debt-to-Equity Ratio"] = float('inf') if total_liabilities > 0 else 0.0
        ratios["Debt-to-Equity Ratio_note"] = "Total Equity is zero."
    else:
        ratios["Debt-to-Equity Ratio"] = total_liabilities / total_equity

    # 2. Current Ratio
    if current_liabilities == 0:
        # Jika liabilitas jangka pendek nol, likuiditas sangat baik.
        ratios["Current Ratio"] = float('inf') if current_assets > 0 else 0.0 # Atau bisa juga dianggap sangat tinggi
        ratios["Current Ratio_note"] = "Current Liabilities are zero."
    else:
        ratios["Current Ratio"] = current_assets / current_liabilities

    # 3. Interest Coverage Ratio (ICR)
    # ICR = EBIT / Beban Bunga
    if interest_expense == 0:
        # Jika tidak ada beban bunga, perusahaan tidak memiliki risiko pembayaran bunga.
        # ICR bisa dianggap sangat tinggi (tak terhingga) jika EBIT positif.
        # Jika EBIT juga 0 atau negatif, interpretasinya berbeda.
        if ebit > 0:
            ratios["Interest Coverage Ratio"] = float('inf')
            ratios["Interest Coverage Ratio_note"] = "No interest expense, EBIT is positive."
        elif ebit == 0:
            ratios["Interest Coverage Ratio"] = 0.0 # Atau tidak terdefinisi
            ratios["Interest Coverage Ratio_note"] = "No interest expense, EBIT is zero."
        else: # EBIT < 0
            ratios["Interest Coverage Ratio"] = float('-inf') # EBIT negatif, tidak ada beban bunga
            ratios["Interest Coverage Ratio_note"] = "No interest expense, EBIT is negative."
    else:
        ratios["Interest Coverage Ratio"] = ebit / interest_expense
        
    # 4. Net Profit Margin
    if sales == 0:
        ratios["Net Profit Margin"] = 0.0 # Tidak ada penjualan, tidak ada margin
        ratios["Net Profit Margin_note"] = "Sales are zero."
    else:
        ratios["Net Profit Margin"] = net_income / sales
        
    # Tambahan rasio yang mungkin berguna
    # 5. Gross Profit Margin
    if "Laba bruto" in data_t:
        try:
            gross_profit = float(data_t["Laba bruto"])
            if sales == 0:
                ratios["Gross Profit Margin"] = 0.0
                ratios["Gross Profit Margin_note"] = "Sales are zero."
            else:
                ratios["Gross Profit Margin"] = gross_profit / sales
        except (ValueError, KeyError):
            ratios["Gross Profit Margin_error"] = "Could not calculate due to missing/invalid 'Laba bruto'."


    # 6. Debt Ratio (Total Liabilities / Total Assets)
    if "Jumlah aset" in data_t:
        try:
            total_assets = float(data_t["Jumlah aset"])
            if total_assets == 0:
                ratios["Debt Ratio"] = float('inf') if total_liabilities > 0 else 0.0
                ratios["Debt Ratio_note"] = "Total Assets are zero."
            else:
                ratios["Debt Ratio"] = total_liabilities / total_assets
        except (ValueError, KeyError):
            ratios["Debt Ratio_error"] = "Could not calculate due to missing/invalid 'Jumlah aset'."


    return ratios

if __name__ == '__main__':
    data_t_astra_example = {
        "Jumlah liabilitas": 16289000000000.0,
        "Jumlah ekuitas": 84714000000000.0,
        "Jumlah aset lancar": 19238000000000.0,
        "Jumlah liabilitas jangka pendek": 14300000000000.0,
        "Laba/rugi sebelum pajak penghasilan": 22136000000000.0,
        "Beban bunga": 550000000000.0,
        "Laba/rugi tahun berjalan": 21661000000000.0,
        "Pendapatan bersih": 108249000000000.0,
        "Laba bruto": 10511000000000.0, # Untuk Gross Profit Margin
        "Jumlah aset": 101003000000000.0 # Untuk Debt Ratio
    }

    print("--- Menghitung Rasio Keuangan Umum ---")
    common_ratios = calculate_common_financial_ratios(data_t_astra_example)

    if "error" in common_ratios:
        print(f"Error menghitung rasio: {common_ratios['error']}")
    else:
        print("Rasio Keuangan Umum:")
        for ratio_name, ratio_value in common_ratios.items():
            if not ratio_name.endswith("_note") and not ratio_name.endswith("_error"):
                print(f"  {ratio_name}: {ratio_value:.4f}", end="")
                if f"{ratio_name}_note" in common_ratios:
                    print(f" ({common_ratios[f'{ratio_name}_note']})")
                else:
                    print()
            elif ratio_name.endswith("_error"):
                 print(f"  Error for {ratio_name.replace('_error', '')}: {ratio_value}")


    print("\n--- Test dengan Data Hilang (Beban Bunga) ---")
    data_missing_interest = data_t_astra_example.copy()
    del data_missing_interest["Beban bunga"] # Hapus Beban Bunga
     # Laba/rugi sebelum pajak penghasilan tetap ada
    
    ratios_no_interest_item = calculate_common_financial_ratios(data_missing_interest)
    if "error" in ratios_no_interest_item:
        # Jika 'Beban bunga' adalah required key dan dihapus, ini akan error.
        # Jika 'Beban bunga' opsional dan di-default ke 0, maka ICR akan dihitung.
        print(f"Error (Beban Bunga Dihapus): {ratios_no_interest_item['error']}")
    else:
        print("Rasio (Beban Bunga Dihapus):")
        print(f"  Interest Coverage Ratio: {ratios_no_interest_item.get('Interest Coverage Ratio', 'N/A'):.4f} ({ratios_no_interest_item.get('Interest Coverage Ratio_note', '')})")


    print("\n--- Test dengan Ekuitas Nol ---")
    data_zero_equity = data_t_astra_example.copy()
    data_zero_equity["Jumlah ekuitas"] = 0
    ratios_zero_equity = calculate_common_financial_ratios(data_zero_equity)
    if "error" not in ratios_zero_equity:
        print(f"  Debt-to-Equity Ratio: {ratios_zero_equity['Debt-to-Equity Ratio']} ({ratios_zero_equity.get('Debt-to-Equity Ratio_note')})")

    print("\n--- Test dengan Liabilitas Jangka Pendek Nol ---")
    data_zero_curr_liab = data_t_astra_example.copy()
    data_zero_curr_liab["Jumlah liabilitas jangka pendek"] = 0
    ratios_zero_curr_liab = calculate_common_financial_ratios(data_zero_curr_liab)
    if "error" not in ratios_zero_curr_liab:
        print(f"  Current Ratio: {ratios_zero_curr_liab['Current Ratio']} ({ratios_zero_curr_liab.get('Current Ratio_note')})")

    print("\n--- Test dengan Beban Bunga Nol (Secara Eksplisit) ---")
    data_zero_interest_exp = data_t_astra_example.copy()
    data_zero_interest_exp["Beban bunga"] = 0
    ratios_zero_interest_exp = calculate_common_financial_ratios(data_zero_interest_exp)
    if "error" not in ratios_zero_interest_exp:
        print(f"  Interest Coverage Ratio: {ratios_zero_interest_exp['Interest Coverage Ratio']} ({ratios_zero_interest_exp.get('Interest Coverage Ratio_note')})")
    
    print("\n--- Test dengan Penjualan Nol ---")
    data_zero_sales = data_t_astra_example.copy()
    data_zero_sales["Pendapatan bersih"] = 0
    data_zero_sales["Laba bruto"] = 0 # Jika sales 0, laba bruto juga 0
    data_zero_sales["Laba/rugi tahun berjalan"] = 0 # Asumsi laba juga 0
    ratios_zero_sales = calculate_common_financial_ratios(data_zero_sales)
    if "error" not in ratios_zero_sales:
        print(f"  Net Profit Margin: {ratios_zero_sales['Net Profit Margin']:.4f} ({ratios_zero_sales.get('Net Profit Margin_note')})")
        print(f"  Gross Profit Margin: {ratios_zero_sales['Gross Profit Margin']:.4f} ({ratios_zero_sales.get('Gross Profit Margin_note')})")

    print("\n--- Test dengan semua data finansial minimal yang hilang ---")
    data_completely_missing = {}
    ratios_completely_missing = calculate_common_financial_ratios(data_completely_missing)
    if "error" in ratios_completely_missing:
        print(f"Error (Data Sangat Minim): {ratios_completely_missing['error']}")