from .financial_ratios import (
    calculate_x1_working_capital_to_total_assets,
    calculate_x2_retained_earnings_to_total_assets,
    calculate_x3_ebit_to_total_assets,
    calculate_x4_market_value_equity_to_total_liabilities,
    calculate_x5_sales_to_total_assets
)
from .utils import get_value

def calculate_altman_variables(data_t: dict, is_public_company: bool = True, market_value_equity_manual: float = None) -> dict:
    """
    Menghitung variabel yang dibutuhkan untuk Altman Z-Score.

    Args:
        data_t (dict): Data keuangan perusahaan untuk periode t (tahun berjalan),
                       hasil dari `get_company_financial_data`.
        is_public_company (bool): True jika perusahaan publik (memengaruhi formula Z-Score dan X4).
                                   Defaults to True.
        market_value_equity_manual (float, optional): Nilai pasar ekuitas yang dimasukkan manual
                                                      (khususnya untuk X4 perusahaan publik). 
                                                      Jika None, dan `is_public_company` True, maka X4
                                                      akan None (karena tidak ada di lapkeu standar).
                                                      Jika `is_public_company` False, argumen ini diabaikan
                                                      dan nilai buku ekuitas digunakan untuk X4.
                                                      Defaults to None.
    Returns:
        dict: Kamus berisi nilai untuk variabel Altman (X1, X2, X3, X4, X5).
              Nilai individual bisa None jika data yang diperlukan tidak lengkap.
    """
    variables = {}
    variables['X1'] = calculate_x1_working_capital_to_total_assets(data_t)
    variables['X2'] = calculate_x2_retained_earnings_to_total_assets(data_t)
    variables['X3'] = calculate_x3_ebit_to_total_assets(data_t)
    
    if is_public_company:
        # Untuk perusahaan publik, X4 menggunakan Market Value of Equity.
        # Jika tidak disediakan secara manual, maka akan None karena tidak ada di lapkeu standar.
        variables['X4'] = calculate_x4_market_value_equity_to_total_liabilities(data_t, market_value_equity=market_value_equity_manual)
    else:
        # Untuk perusahaan non-publik, X4 menggunakan Book Value of Equity.
        # Fungsi calculate_x4 akan otomatis menggunakan book value jika market_value_equity_manual adalah None.
        variables['X4'] = calculate_x4_market_value_equity_to_total_liabilities(data_t, market_value_equity=None) # Paksa pakai book value
        
    variables['X5'] = calculate_x5_sales_to_total_assets(data_t)
    
    return variables

def calculate_altman_z_score(altman_vars: dict, is_public_company: bool = True) -> float | None:
    """
    Menghitung Altman Z-Score.
    - Model Asli (1968) untuk Perusahaan Manufaktur Publik:
      Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5 
      (dimana X4 = Market Value of Equity / Book Value of Total Liabilities)
    - Model Revisi (1983) untuk Perusahaan Privat Manufaktur:
      Z' = 0.717*X1 + 0.847*X2 + 3.107*X3 + 0.420*X4 + 0.998*X5
      (dimana X4 = Book Value of Equity / Book Value of Total Liabilities)
    - Model untuk Perusahaan Non-Manufaktur (1983) (tidak diimplementasikan di sini secara spesifik,
      namun model publik sering digunakan sebagai generalisasi atau model privat jika non-publik).
      Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4_book
      (X5 dihilangkan karena variabilitas penjualan antar industri non-manufaktur)


    
    Referensi formula:
    - Altman, E. I. (1968). Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy.
    - Altman, E. I. (2000). Predicting financial distress of companies: revisiting the Z-score and ZETA models.

    Args:
        altman_vars (dict): Kamus berisi nilai X1, X2, X3, X4, X5.
                            Kunci harus sesuai dengan nama variabel tersebut.
        is_public_company (bool): True jika menggunakan formula untuk perusahaan publik (manufaktur).
                                   False jika menggunakan formula untuk perusahaan privat (manufaktur).
                                   Defaults to True.

    Returns:
        float | None: Nilai Altman Z-Score. Mengembalikan None jika salah satu variabel
                      yang dibutuhkan (X1-X5 untuk publik/privat) tidak ada (None).
                      Untuk model publik, jika X4 (berbasis market value) adalah None, skor juga None.
    """
    required_vars = ['X1', 'X2', 'X3', 'X4', 'X5']
    if any(altman_vars.get(var) is None for var in required_vars):
        # Khusus untuk model non-manufaktur, X5 tidak wajib. Tapi kita tidak implementasi itu dulu.
        return None

    if is_public_company:
        # Model asli untuk perusahaan publik manufaktur
        # Jika X4 (Market Value) tidak ada, skor tidak bisa dihitung dengan model ini.
        if altman_vars['X4'] is None: 
            return None # Atau mungkin bisa fallback ke model privat jika diinginkan? Untuk saat ini, None.
        z_score = (
            (1.2 * altman_vars['X1']) +
            (1.4 * altman_vars['X2']) +
            (3.3 * altman_vars['X3']) +
            (0.6 * altman_vars['X4']) + # X4 di sini adalah Market Value Equity / Total Liabilities
            (1.0 * altman_vars['X5'])
        )
    else:
        # Model untuk perusahaan privat manufaktur (menggunakan Book Value Equity untuk X4)
        z_score = (
            (0.717 * altman_vars['X1']) +
            (0.847 * altman_vars['X2']) +
            (3.107 * altman_vars['X3']) +
            (0.420 * altman_vars['X4']) + # X4 di sini adalah Book Value Equity / Total Liabilities
            (0.998 * altman_vars['X5'])
        )
    return z_score

def interpret_altman_z_score(score: float, is_public_company: bool = True) -> str:
    """
    Memberikan interpretasi kualitatif untuk Altman Z-Score.
    Zona interpretasi sedikit berbeda untuk model perusahaan publik dan privat.

    Args:
        score (float | None): Nilai Altman Z-Score. Bisa None jika tidak dapat dihitung.
        is_public_company (bool): True jika skor dihitung menggunakan model untuk perusahaan publik.
                                   Defaults to True.

    Returns:
        str: Interpretasi skor (Zona Aman, Zona Abu-abu, Zona Bahaya).
    """
    if score is None:
        return "Tidak dapat dihitung (data tidak lengkap atau X4 Market Value tidak ada untuk publik)."

    if is_public_company:
        # Interpretasi untuk Z-Score Perusahaan Publik Manufaktur
        if score > 2.99:
            return f"Skor Z = {score:.3f}. Zona Aman (Risiko kebangkrutan rendah)."
        elif score > 1.81:
            return f"Skor Z = {score:.3f}. Zona Abu-abu (Perlu perhatian, risiko kebangkrutan sedang)."
        else:
            return f"Skor Z = {score:.3f}. Zona Bahaya (Risiko kebangkrutan tinggi)."
    else:
        # Interpretasi untuk Z'-Score Perusahaan Privat Manufaktur
        if score > 2.90: # Beberapa sumber menggunakan 2.6 atau 2.9
            return f"Skor Z' = {score:.3f}. Zona Aman (Risiko kebangkrutan rendah)."
        elif score > 1.23: # Beberapa sumber menggunakan 1.1
            return f"Skor Z' = {score:.3f}. Zona Abu-abu (Perlu perhatian, risiko kebangkrutan sedang)."
        else:
            return f"Skor Z' = {score:.3f}. Zona Bahaya (Risiko kebangkrutan tinggi)."

def get_altman_z_score_analysis(data_t: dict, is_public_company: bool = True, market_value_equity_manual: float = None) -> dict:
    """
    Menjalankan analisis Altman Z-Score lengkap.

    Args:
        data_t (dict): Data keuangan perusahaan untuk periode t (tahun berjalan).
        is_public_company (bool): Flag apakah menggunakan model untuk perusahaan publik atau privat.
                                   Defaults to True.
        market_value_equity_manual (float, optional): Nilai pasar ekuitas manual, jika tersedia
                                                      (terutama untuk model perusahaan publik).
                                                      Defaults to None.

    Returns:
        dict: Kamus yang berisi:
              - "altman_variables": dict dari 5 variabel Altman dan nilainya.
              - "z_score": float nilai Altman Z-Score (atau None).
              - "interpretation": str interpretasi dari skor Z.
              - "model_type": str deskripsi model yang digunakan ("Publik Manufaktur" atau "Privat Manufaktur").
    """
    if data_t is None:
        return {
            "altman_variables": None,
            "z_score": None,
            "interpretation": "Data keuangan periode t tidak tersedia."
        }
        
    altman_vars = calculate_altman_variables(data_t, is_public_company, market_value_equity_manual)
    z_score = calculate_altman_z_score(altman_vars, is_public_company)
    interpretation = interpret_altman_z_score(z_score, is_public_company)
    
    return {
        "altman_variables": altman_vars,
        "z_score": z_score,
        "interpretation": interpretation,
        "model_type": "Publik Manufaktur" if is_public_company else "Privat Manufaktur"
    }
