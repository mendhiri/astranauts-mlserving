def calculate_altman_z_score(data_t, model_type="public_manufacturing"):
    """
    Menghitung Altman Z-Score untuk memprediksi kebangkrutan perusahaan.

    Args:
        data_t (dict): Data keuangan periode t (tahun berjalan).
                       Struktur: {'nama_item_keuangan': nilai, ...}
        model_type (str): Jenis model Z-Score yang digunakan. Pilihan:
                          "public_manufacturing" (default): Untuk perusahaan manufaktur publik.
                          "private_manufacturing": Untuk perusahaan manufaktur swasta.
                          "non_manufacturing_or_emerging_markets": Untuk perusahaan non-manufaktur atau pasar berkembang.

    Returns:
        tuple: (float, dict) -> Nilai Altman Z-Score dan dictionary rasio-rasio Altman.
               Mengembalikan (None, None) jika ada data keuangan penting yang hilang.
    """
    required_keys = [
        "Jumlah aset lancar", "Jumlah aset", "Laba ditahan",
        "Laba/rugi sebelum pajak penghasilan", "Beban bunga", # Untuk EBIT
        "Jumlah ekuitas", # Sebagai proxy Market Value of Equity jika tidak ada data pasar
        "Jumlah liabilitas", "Pendapatan bersih",
        "Jumlah liabilitas jangka pendek"
    ]

    for key in required_keys:
        if key not in data_t:
            return None, {"error": f"Missing item in data_t for Z-Score: {key}"}

    try:
        working_capital = float(data_t["Jumlah aset lancar"]) - float(data_t["Jumlah liabilitas jangka pendek"])
        total_assets = float(data_t["Jumlah aset"])
        retained_earnings = float(data_t["Laba ditahan"])
        ebit = float(data_t["Laba/rugi sebelum pajak penghasilan"]) + float(data_t["Beban bunga"])
        # Menggunakan Nilai Buku Ekuitas sebagai proxy untuk Nilai Pasar Ekuitas
        # Jika nilai pasar ekuitas tersedia, itu harus digunakan.
        market_value_equity = float(data_t["Jumlah ekuitas"])
        total_liabilities = float(data_t["Jumlah liabilitas"])
        sales = float(data_t["Pendapatan bersih"])

    except KeyError as e:
        return None, {"error": f"KeyError during Z-Score data extraction: {e}"}
    except ValueError as e:
        return None, {"error": f"ValueError, data Z-Score tidak dapat dikonversi ke float: {e}"}

    if total_assets == 0:
        return None, {"error": "Total Assets cannot be zero for Z-Score calculation."}
    
    ratios = {}

    # X1 = Modal Kerja / Total Aset
    x1 = working_capital / total_assets
    ratios["X1 (Working Capital / Total Assets)"] = x1

    # X2 = Laba Ditahan / Total Aset
    x2 = retained_earnings / total_assets
    ratios["X2 (Retained Earnings / Total Assets)"] = x2

    # X3 = EBIT / Total Aset
    x3 = ebit / total_assets
    ratios["X3 (EBIT / Total Assets)"] = x3

    # X4 = Nilai Pasar Ekuitas / Total Liabilitas
    # Menggunakan Nilai Buku Ekuitas jika Nilai Pasar tidak tersedia
    if total_liabilities == 0:
        # Jika tidak ada liabilitas, perusahaan sangat sehat dari sisi leverage.
        # Z-score akan sangat tinggi. Untuk menghindari infinity, bisa diberi nilai besar atau disesuaikan.
        # Altman tidak secara eksplisit menangani ini, tetapi rasio yg sangat tinggi akan menaikkan Z.
        # Memberi nilai yang cukup tinggi namun terbatas jika market_value_equity > 0
        x4 = 10.0 if market_value_equity > 0 else 0.0 
    else:
        x4 = market_value_equity / total_liabilities
    ratios["X4 (Market Value of Equity / Total Liabilities)"] = x4
    ratios["X4_note"] = "Using Book Value of Equity as proxy for Market Value"


    # X5 = Penjualan / Total Aset
    x5 = sales / total_assets
    ratios["X5 (Sales / Total Assets)"] = x5

    z_score = None
    if model_type == "public_manufacturing":
        # Z-Score untuk Perusahaan Manufaktur Publik (Original Model 1968)
        # Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5 (atau 0.999*X5)
        z_score = (1.2 * x1) + (1.4 * x2) + (3.3 * x3) + (0.6 * x4) + (0.999 * x5)
        ratios["model_type"] = "Public Manufacturing (1968)"
        ratios["interpretation_zones"] = {
            "Safe Zone": "> 2.99",
            "Grey Zone": "1.81 - 2.99",
            "Distress Zone": "< 1.81"
        }
    elif model_type == "private_manufacturing":
        # Z'-Score untuk Perusahaan Manufaktur Swasta (Revised Model 1983)
        # Mengganti Market Value of Equity dengan Book Value of Equity di X4
        # Z' = 0.717*X1 + 0.847*X2 + 3.107*X3 + 0.420*X4 (Book Value) + 0.998*X5
        # Karena kita sudah menggunakan Book Value untuk X4, kita bisa langsung pakai koefisien ini
        z_score = (0.717 * x1) + (0.847 * x2) + (3.107 * x3) + (0.420 * x4) + (0.998 * x5)
        ratios["model_type"] = "Private Manufacturing (1983)"
        ratios["interpretation_zones"] = {
            "Safe Zone": "> 2.90", # Beberapa sumber menyebut 2.60
            "Grey Zone": "1.23 - 2.90", # Beberapa sumber 1.10 - 2.60
            "Distress Zone": "< 1.23" # Beberapa sumber < 1.10
        }
    elif model_type == "non_manufacturing_or_emerging_markets":
        # Z"-Score untuk Perusahaan Non-Manufaktur / Jasa / Pasar Berkembang (Model 1995, tanpa X5)
        # Z" = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4 (Book Value)
        # Model ini juga menambahkan konstanta 3.25 di beberapa formulasi, tapi ada yang tidak.
        # Versi yang lebih umum dikutip: Z" = 3.25 + 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4
        z_score = 3.25 + (6.56 * x1) + (3.26 * x2) + (6.72 * x3) + (1.05 * x4)
        ratios["model_type"] = "Non-Manufacturing/Emerging Markets (1995)"
        ratios["interpretation_zones"] = {
            "Safe Zone": "> 2.60", # Beberapa sumber menyebut 2.90
            "Grey Zone": "1.10 - 2.60",
            "Distress Zone": "< 1.10"
        }
    else:
        return None, {"error": f"Invalid model_type for Z-Score: {model_type}. Valid types are 'public_manufacturing', 'private_manufacturing', 'non_manufacturing_or_emerging_markets'."}

    return z_score, ratios

def get_altman_z_score_analysis(data_t, is_public_company=True, market_value_equity_manual=None):
    """
    Menganalisis perusahaan menggunakan Altman Z-Score.

    Args:
        data_t (dict): Data keuangan periode t (tahun berjalan).
        is_public_company (bool): True jika perusahaan publik (menggunakan model manufaktur publik atau non-manufaktur),
                                  False jika perusahaan manufaktur swasta.
        market_value_equity_manual (float, optional): Nilai pasar ekuitas manual jika tersedia.
                                                      Jika None, akan menggunakan nilai buku ekuitas.

    Returns:
        dict: Hasil analisis Altman Z-Score, termasuk skor, rasio, dan interpretasi.
    """
    if data_t is None:
        return {
            "z_score": None,
            "ratios": None,
            "interpretation": "Data tidak lengkap untuk menghitung Altman Z-Score.",
            "error": "Data t tidak disediakan."
        }

    # Tentukan model_type berdasarkan status perusahaan
    # Ini adalah penyederhanaan. Idealnya, pengguna bisa memilih model yang lebih spesifik.
    if is_public_company:
        # Untuk perusahaan publik, kita bisa default ke 'public_manufacturing' atau 'non_manufacturing_or_emerging_markets'.
        # Keputusan ini bisa bergantung pada ketersediaan data atau jenis industri.
        # Jika 'Pendapatan bersih' ada, kita bisa condong ke model yang menggunakan X5 (sales).
        # Untuk contoh ini, kita akan default ke 'public_manufacturing' jika tidak ada info lain.
        # Jika ingin lebih canggih, bisa cek jenis industri dari data atau input tambahan.
        model_type = "public_manufacturing" 
        # Alternatif: jika ada cara untuk menentukan non-manufaktur, gunakan:
        # model_type = "non_manufacturing_or_emerging_markets"
    else:
        model_type = "private_manufacturing"

    # Jika market_value_equity_manual disediakan, coba masukkan ke data_t jika belum ada atau berbeda.
    # Fungsi calculate_altman_z_score akan menggunakan "Jumlah ekuitas" sebagai proxy jika MVE tidak ada.
    # Jika kita ingin MVE_manual benar-benar digunakan, kita harus memastikan itu ada di `data_t`
    # dengan nama kunci yang diharapkan oleh `calculate_altman_z_score` (misalnya, "Nilai Pasar Ekuitas")
    # atau memodifikasi `calculate_altman_z_score` untuk menerimanya secara langsung.
    # Untuk saat ini, `calculate_altman_z_score` menggunakan "Jumlah ekuitas" sebagai proxy.
    # Jika `market_value_equity_manual` diberikan, kita bisa menggunakannya untuk mengganti "Jumlah ekuitas"
    # khusus untuk perhitungan X4 jika modelnya adalah 'public_manufacturing'.
    # Namun, `calculate_altman_z_score` saat ini secara internal mengambil `market_value_equity` dari `data_t["Jumlah ekuitas"]`.
    # Jadi, jika `market_value_equity_manual` diberikan, kita harus mengganti `data_t["Jumlah ekuitas"]` sementara.
    
    original_equity_value = None
    if market_value_equity_manual is not None and model_type == "public_manufacturing":
        if "Jumlah ekuitas" in data_t:
            original_equity_value = data_t["Jumlah ekuitas"]
            data_t["Jumlah ekuitas"] = market_value_equity_manual # Ganti sementara untuk X4
            # Tambahkan catatan bahwa MVE manual digunakan jika perlu di `ratios` nanti
            # (calculate_altman_z_score sudah punya X4_note untuk proxy book value)

    z_score, ratios = calculate_altman_z_score(data_t, model_type=model_type)

    # Kembalikan nilai ekuitas asli jika diubah
    if original_equity_value is not None and "Jumlah ekuitas" in data_t:
        data_t["Jumlah ekuitas"] = original_equity_value


    interpretation = "Tidak dapat diinterpretasi karena skor tidak dihitung."
    zone = "Unknown"

    if z_score is not None and ratios is not None and "interpretation_zones" in ratios:
        zones_info = ratios["interpretation_zones"]
        if model_type == "public_manufacturing":
            if z_score > 2.99: zone = "Safe Zone"
            elif z_score > 1.81: zone = "Grey Zone"
            else: zone = "Distress Zone"
        elif model_type == "private_manufacturing":
            if z_score > 2.90: zone = "Safe Zone" # Sesuai implementasi di calculate_altman_z_score
            elif z_score > 1.23: zone = "Grey Zone"
            else: zone = "Distress Zone"
        elif model_type == "non_manufacturing_or_emerging_markets":
            if z_score > 2.60: zone = "Safe Zone" # Sesuai implementasi di calculate_altman_z_score
            elif z_score > 1.10: zone = "Grey Zone"
            else: zone = "Distress Zone"
        
        interpretation = f"Perusahaan berada di '{zone}'. Model: {ratios.get('model_type', model_type)}. Zona Detail: {zones_info}"
        if market_value_equity_manual is not None and model_type == "public_manufacturing":
             ratios["X4_note"] = "Using provided manual Market Value of Equity for X4."


    elif ratios and "error" in ratios:
        interpretation = f"Error dalam perhitungan: {ratios['error']}"
        zone = "Error"

    return {
        "z_score": z_score,
        "ratios": ratios,
        "interpretation": interpretation,
        "zone": zone,
        "model_used": model_type
    }