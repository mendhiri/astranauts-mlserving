from .financial_ratios import (
    calculate_dsri, calculate_gmi, calculate_aqi, calculate_sgi,
    calculate_depi, calculate_sgai, calculate_lvgi, calculate_tata
)

def calculate_beneish_variables(data_t: dict, data_t_minus_1: dict) -> dict:
    """
    Menghitung 8 variabel yang dibutuhkan untuk Beneish M-Score.

    Args:
        data_t (dict): Data keuangan perusahaan untuk periode t (tahun berjalan),
                       hasil dari `get_company_financial_data`.
        data_t_minus_1 (dict): Data keuangan perusahaan untuk periode t-1 (tahun sebelumnya),
                               hasil dari `get_company_financial_data`.

    Returns:
        dict: Kamus berisi nilai untuk 8 variabel Beneish (DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA).
              Nilai individual dalam kamus bisa None jika data yang diperlukan tidak lengkap.
    """
    variables = {}
    variables['DSRI'] = calculate_dsri(data_t, data_t_minus_1)
    variables['GMI'] = calculate_gmi(data_t, data_t_minus_1)
    variables['AQI'] = calculate_aqi(data_t, data_t_minus_1)
    variables['SGI'] = calculate_sgi(data_t, data_t_minus_1)
    variables['DEPI'] = calculate_depi(data_t, data_t_minus_1)
    variables['SGAI'] = calculate_sgai(data_t, data_t_minus_1)
    variables['LVGI'] = calculate_lvgi(data_t, data_t_minus_1)
    variables['TATA'] = calculate_tata(data_t)
    
    return variables

def calculate_beneish_m_score(beneish_vars: dict) -> float | None:
    """
    Menghitung Beneish M-Score berdasarkan 8 variabelnya.
    Formula: M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI 
                 + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
                 (Catatan: beberapa sumber menggunakan -0.327*LVGI, sumber lain +0.327*LVGI.
                  Paper asli Beneish (1999) "The Detection of Earnings Manipulation" menggunakan TATA, bukan LVGI.
                  Model 8 variabel yang umum dirujuk adalah:
                  M = -4.84 + 0.92*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI - 0.327*LVGI + 4.679*TATA
                  Namun, ada juga versi 5 variabel. Kita akan implementasi yang 8 variabel dengan koefisien yang umum.
                  Formula yang lebih sering dikutip (misal oleh CFA Institute) adalah:
                  M-score = -4.84 + 0.920(DSRI) + 0.528(GMI) + 0.404(AQI) + 0.892(SGI) + 0.115(DEPI) – 0.172(SGAI) + 4.679(TATA) – 0.327(LVGI)
                  Paper asli Beneish (1999) tidak menyertakan LVGI, TATA dihitung berbeda.
                  Model 8 variabel yang sering dirujuk:
                  M = -4.84 + 0.920 DSRI + 0.528 GMI + 0.404 AQI + 0.892 SGI + 0.115 DEPI – 0.172 SGAI + 4.679 Accruals – 0.327 LVGI
                  Accruals = (Income before extraordinary items – CFO) / Total Assets (ini adalah TATA kita)
                  Jadi, formula yang akan dipakai:
                  M = -4.84 + 0.92*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI 
                        - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
    
    Referensi formula dan koefisien:
    Beneish, M. D. (1999). The Detection of Earnings Manipulation. Financial Analysts Journal, 55(5), 24–36.
    Serta berbagai sumber akademis dan praktis yang merujuk pada model 8 variabel ini.

    Args:
        beneish_vars (dict): Kamus berisi nilai DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA.
                             Kunci harus sesuai dengan nama variabel tersebut.

    Returns:
        float | None: Nilai Beneish M-Score. Mengembalikan None jika salah satu dari 8 variabel
                      yang dibutuhkan tidak ada (None) dalam `beneish_vars`.
    """
    required_vars = ['DSRI', 'GMI', 'AQI', 'SGI', 'DEPI', 'SGAI', 'TATA', 'LVGI']
    if any(beneish_vars.get(var) is None for var in required_vars):
        return None

    m_score = (
        -4.84 +
        (0.920 * beneish_vars['DSRI']) +
        (0.528 * beneish_vars['GMI']) +
        (0.404 * beneish_vars['AQI']) +
        (0.892 * beneish_vars['SGI']) +
        (0.115 * beneish_vars['DEPI']) -
        (0.172 * beneish_vars['SGAI']) +
        (4.679 * beneish_vars['TATA']) -  # Perhatikan TATA positif
        (0.327 * beneish_vars['LVGI'])
    )
    return m_score

def interpret_beneish_m_score(score: float) -> str:
    """
    Memberikan interpretasi kualitatif untuk Beneish M-Score.
    Umumnya, skor > -1.78 (atau -2.22 pada beberapa studi) mengindikasikan potensi manipulasi.
    Kita akan gunakan threshold -1.78.

    Args:
        score (float | None): Nilai Beneish M-Score. Bisa None jika tidak dapat dihitung.

    Returns:
        str: Interpretasi skor.
    """
    if score is None:
        return "Tidak dapat dihitung (data tidak lengkap)."
    
    # Threshold umum:
    # < -2.22 : Kemungkinan kecil sebagai manipulator
    # > -2.22 : Kemungkinan besar sebagai manipulator
    # Beberapa literatur menggunakan -1.78. Kita gunakan -1.78 sebagai batas yang lebih sering dikutip.
    if score < -1.78:
        return f"Skor M = {score:.3f}. Indikasi rendah terhadap manipulasi laba."
    else:
        return f"Skor M = {score:.3f}. Potensi indikasi manipulasi laba (Perlu investigasi lebih lanjut)."

def get_beneish_m_score_analysis(data_t: dict, data_t_minus_1: dict) -> dict:
    """
    Menjalankan analisis Beneish M-Score lengkap.

    Args:
        data_t (dict): Data keuangan perusahaan untuk periode t (tahun berjalan).
        data_t_minus_1 (dict): Data keuangan perusahaan untuk periode t-1 (tahun sebelumnya).

    Returns:
        dict: Kamus yang berisi:
              - "beneish_variables": dict dari 8 variabel Beneish dan nilainya.
              - "m_score": float nilai Beneish M-Score (atau None).
              - "interpretation": str interpretasi dari skor M.
    """
    if data_t is None or data_t_minus_1 is None:
        return {
            "beneish_variables": None,
            "m_score": None,
            "interpretation": "Data tidak lengkap untuk satu atau kedua periode."
        }
        
    beneish_vars = calculate_beneish_variables(data_t, data_t_minus_1)
    m_score = calculate_beneish_m_score(beneish_vars)
    interpretation = interpret_beneish_m_score(m_score)
    
    return {
        "beneish_variables": beneish_vars,
        "m_score": m_score,
        "interpretation": interpretation
    }
