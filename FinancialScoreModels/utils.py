import json

def load_sarana_output(file_path_t: str, file_path_t_minus_1: str = None) -> tuple[list, list | None]:
    """
    Memuat data output dari SaranaModule.

    Args:
        file_path_t (str): Path ke file JSON output Sarana untuk periode t (tahun berjalan).
        file_path_t_minus_1 (str, optional): Path ke file JSON output Sarana untuk periode t-1 (tahun sebelumnya).
                                            Defaults to None.

    Returns:
        tuple[list, list | None]: Tuple berisi (data_t, data_t_minus_1). 
                                  data_t_minus_1 akan None jika file_path_t_minus_1 tidak diberikan.
                                  Setiap elemen data adalah list of dictionaries dari file JSON.
    Raises:
        FileNotFoundError: Jika salah satu file tidak ditemukan.
        JSONDecodeError: Jika file bukan JSON yang valid.
    """
    try:
        with open(file_path_t, 'r', encoding='utf-8') as f:
            data_t = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File tidak ditemukan: {file_path_t}")
    except json.JSONDecodeError:
        raise json.JSONDecodeError(f"Gagal membaca JSON dari file: {file_path_t}", "", 0)

    data_t_minus_1 = None
    if file_path_t_minus_1:
        try:
            with open(file_path_t_minus_1, 'r', encoding='utf-8') as f:
                data_t_minus_1 = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File tidak ditemukan: {file_path_t_minus_1}")
        except json.JSONDecodeError:
            raise json.JSONDecodeError(f"Gagal membaca JSON dari file: {file_path_t_minus_1}", "", 0)
            
    # Pastikan outputnya selalu list, bahkan jika hanya satu perusahaan/dokumen
    if not isinstance(data_t, list):
        data_t = [data_t]
    if data_t_minus_1 is not None and not isinstance(data_t_minus_1, list):
        data_t_minus_1 = [data_t_minus_1]
        
    return data_t, data_t_minus_1

def get_company_financial_data(sarana_data_list: list, company_filename: str) -> dict | None:
    """
    Mengambil data keuangan untuk satu perusahaan berdasarkan nama file dari list output Sarana.

    Args:
        sarana_data_list (list): List of dictionaries, output dari SaranaModule (hasil load_sarana_output).
        company_filename (str): Nama file perusahaan yang ingin diambil datanya 
                                (harus cocok dengan kunci "nama_file" dalam JSON).

    Returns:
        dict | None: Dictionary berisi data keuangan ("hasil_ekstraksi") perusahaan tersebut, 
                     atau None jika tidak ditemukan.
    """
    if not sarana_data_list:
        return None
    for company_data in sarana_data_list:
        if company_data.get("nama_file") == company_filename:
            return company_data.get("hasil_ekstraksi")
    return None

def safe_division(numerator, denominator):
    """
    Melakukan pembagian dengan aman.

    Args:
        numerator (float | int | None): Pembilang.
        denominator (float | int | None): Penyebut.

    Returns:
        float | None: Hasil pembagian, atau None jika pembilang/penyebut adalah None
                      atau jika penyebut adalah nol.
    """
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator

def get_value(data: dict, key: str, year_ago: int = 0):
    """
    Mengambil nilai dari kamus data keuangan.
    Mengambil nilai dari kamus data keuangan yang telah diekstrak oleh Sarana.
    Fungsi ini dirancang untuk kompatibilitas dengan struktur output Sarana saat ini
    yang mungkin hanya memiliki satu nilai per kata kunci, atau menggunakan kata kunci
    eksplisit seperti "NamaItem Tahun Lalu" jika data komparatif diekstrak sebagai item terpisah.

    Catatan: Untuk analisis yang memerlukan data t dan t-1 secara konsisten (seperti Beneish M-Score),
    pendekatan yang lebih disarankan adalah memproses dua laporan keuangan terpisah (tahun t dan t-1)
    melalui Sarana dan kemudian memuat kedua output JSON tersebut. Fungsi ini lebih bersifat fallback
    atau untuk kasus di mana data komparatif mungkin ada dalam satu laporan dengan label "Tahun Lalu".

    Args:
        data (dict | None): Kamus data keuangan hasil ekstraksi Sarana untuk satu periode.
        key (str): Kata dasar item keuangan yang dicari (misalnya, "Pendapatan bersih").
        year_ago (int): Spesifikasi periode. 
                        0 untuk tahun berjalan (t) - akan mencari `key`.
                        1 untuk tahun lalu (t-1) - akan mencari `f"{key} Tahun Lalu"`.
                        Defaults to 0.

    Returns:
        float | None: Nilai float dari item keuangan jika ditemukan dan valid, 
                      selain itu None.
    """
    if data is None:
        return None
        
    val = None
    if year_ago == 0:
        val = data.get(key)
    elif year_ago == 1:
        # Mencoba mengambil dari kata kunci eksplisit "Tahun Lalu"
        # Ini adalah asumsi sementara; idealnya struktur data akan lebih baik
        # dalam membedakan nilai t dan t-1.
        val_tl = data.get(f"{key} Tahun Lalu")
        if val_tl is not None:
            val = val_tl
        # Jika Sarana dimodifikasi untuk output array [nilai_t, nilai_t_minus_1]
        # elif isinstance(data.get(key), list) and len(data.get(key)) > 1:
        #     val = data.get(key)[1] 
        # Logika ini perlu disesuaikan dengan output aktual Sarana nanti.
            
    if isinstance(val, (int, float)):
        return float(val)
    return None
