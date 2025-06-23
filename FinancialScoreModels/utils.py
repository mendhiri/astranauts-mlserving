import json

def load_sarana_output(file_path_t: str, file_path_t_minus_1: str = None) -> tuple[list, list | None]:
    """
    Memuat data output dari SaranaModule.
    Dapat memproses satu file JSON yang berisi data historis, atau dua file terpisah untuk t dan t-1.

    Struktur JSON yang diharapkan jika satu file (file_path_t):
    [
        {
            "nama_file": "nama_dokumen_perusahaan_A.pdf",
            "hasil_ekstraksi_historis": [
                {"tahun_laporan": 2023, "hasil_ekstraksi": {...data keuangan 2023...}},
                {"tahun_laporan": 2022, "hasil_ekstraksi": {...data keuangan 2022...}}
            ]
        },
        // ... entri perusahaan lain
    ]
    Atau, jika "hasil_ekstraksi_historis" tidak ada, bisa juga:
    [
        {
            "nama_file": "nama_dokumen_perusahaan_A_2023.pdf", // atau nama file umum
            "tahun_laporan": 2023, // Opsional, tapi berguna jika nama file tidak mencerminkan tahun
            "hasil_ekstraksi": {...data keuangan 2023...}
        }
        // ... entri lain, mungkin dari file berbeda jika file_path_t_minus_1 digunakan
    ]


    Args:
        file_path_t (str): Path ke file JSON output Sarana. Ini bisa berisi data untuk beberapa tahun
                           jika memiliki field `hasil_ekstraksi_historis` atau `tahun_laporan`.
        file_path_t_minus_1 (str, optional): Path ke file JSON output Sarana spesifik untuk periode t-1.
                                            Jika sama dengan `file_path_t` atau None, fungsi akan mencoba
                                            menemukan data t-1 dari `file_path_t`. Defaults to None.

    Returns:
        tuple[list, list | None]: Tuple berisi (data_list_t, data_list_t_minus_1).
                                  data_list_t_minus_1 akan None jika tidak ditemukan.
                                  Setiap elemen dalam list adalah dict dengan "nama_file" dan "hasil_ekstraksi".
    Raises:
        FileNotFoundError: Jika file_path_t tidak ditemukan.
        JSONDecodeError: Jika file bukan JSON yang valid.
    """
    try:
        with open(file_path_t, 'r', encoding='utf-8') as f:
            source_data_t_file = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File utama tidak ditemukan: {file_path_t}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Gagal membaca JSON dari file utama: {file_path_t} - Error: {e.msg}", e.doc, e.pos)

    source_data_t_minus_1_file = None
    if file_path_t_minus_1 and file_path_t_minus_1 != file_path_t:
        try:
            with open(file_path_t_minus_1, 'r', encoding='utf-8') as f:
                source_data_t_minus_1_file = json.load(f)
            if not isinstance(source_data_t_minus_1_file, list): # Pastikan list
                source_data_t_minus_1_file = [source_data_t_minus_1_file]
        except FileNotFoundError:
            print(f"Peringatan: File t-1 spesifik tidak ditemukan di {file_path_t_minus_1}.")
        except json.JSONDecodeError as e:
            print(f"Peringatan: Gagal membaca JSON dari file t-1 spesifik: {file_path_t_minus_1} - Error: {e.msg}")
            source_data_t_minus_1_file = None # Anggap tidak ada jika gagal parse

    # Pastikan source_data_t_file selalu list untuk iterasi
    if not isinstance(source_data_t_file, list):
        source_data_t_file = [source_data_t_file]

    processed_data_t = []
    processed_data_t_minus_1 = []
    
    # Proses source_data_t_file
    for entry in source_data_t_file:
        company_filename = entry.get("nama_file")
        if not company_filename:
            print(f"Peringatan: Entri JSON di file utama tidak memiliki 'nama_file', akan dilewati: {str(entry)[:100]}")
            continue

        historical_data = entry.get("hasil_ekstraksi_historis")
        if isinstance(historical_data, list) and historical_data:
            try:
                valid_data = [
                    d for d in historical_data 
                    if isinstance(d, dict) and "tahun_laporan" in d and "hasil_ekstraksi" in d and \
                       isinstance(d["tahun_laporan"], (int, str)) and str(d["tahun_laporan"]).isdigit()
                ]
                sorted_data = sorted(valid_data, key=lambda x: int(x["tahun_laporan"]), reverse=True)
                
                if sorted_data:
                    processed_data_t.append({
                        "nama_file": company_filename,
                        "hasil_ekstraksi": sorted_data[0]["hasil_ekstraksi"]
                    })
                    if len(sorted_data) > 1:
                        # Periksa apakah data t-1 untuk file ini sudah ada dari file t-1 spesifik
                        # Jika belum, baru tambahkan dari file utama
                        is_already_added_from_specific_file = False
                        if source_data_t_minus_1_file:
                            for item_tm1_specific in source_data_t_minus_1_file:
                                if item_tm1_specific.get("nama_file") == company_filename:
                                    is_already_added_from_specific_file = True
                                    break
                        if not is_already_added_from_specific_file:
                            processed_data_t_minus_1.append({
                                "nama_file": company_filename,
                                "hasil_ekstraksi": sorted_data[1]["hasil_ekstraksi"]
                            })
            except (ValueError, TypeError) as e:
                print(f"Peringatan: Gagal memproses data historis untuk {company_filename} dari file utama: {e}. Mencoba fallback.")
                if "hasil_ekstraksi" in entry: # Fallback ke hasil ekstraksi utama jika ada
                     processed_data_t.append({
                        "nama_file": company_filename,
                        "hasil_ekstraksi": entry["hasil_ekstraksi"]
                    })
        
        elif "hasil_ekstraksi" in entry:
            processed_data_t.append({
                "nama_file": company_filename,
                "hasil_ekstraksi": entry["hasil_ekstraksi"]
            })
        else:
            print(f"Peringatan: Entri JSON untuk {company_filename} di file utama tidak memiliki 'hasil_ekstraksi_historis' maupun 'hasil_ekstraksi'. Dilewati.")

    # Proses source_data_t_minus_1_file (dari file terpisah untuk t-1)
    # Ini akan menimpa data t-1 yang mungkin sudah diekstrak dari file_path_t jika nama_file sama
    if source_data_t_minus_1_file:
        # Buat dictionary dari processed_data_t_minus_1 untuk memudahkan update/penimpaan
        # Key: nama_file, Value: index dalam processed_data_t_minus_1
        existing_tm1_map = {item.get("nama_file"): idx for idx, item in enumerate(processed_data_t_minus_1)}

        for entry_tm1_specific in source_data_t_minus_1_file:
            company_filename_tm1 = entry_tm1_specific.get("nama_file")
            if not company_filename_tm1:
                print(f"Peringatan: Entri JSON di file t-1 spesifik tidak memiliki 'nama_file', akan dilewati: {str(entry_tm1_specific)[:100]}")
                continue

            financial_data_tm1 = None
            # Prioritaskan 'hasil_ekstraksi_historis' jika ada dan ambil yang terbaru dari sana
            historical_data_tm1_specific = entry_tm1_specific.get("hasil_ekstraksi_historis")
            if isinstance(historical_data_tm1_specific, list) and historical_data_tm1_specific:
                try:
                    valid_data_tm1 = [
                        d for d in historical_data_tm1_specific
                        if isinstance(d, dict) and "tahun_laporan" in d and "hasil_ekstraksi" in d and \
                        isinstance(d["tahun_laporan"], (int, str)) and str(d["tahun_laporan"]).isdigit()
                    ]
                    sorted_data_tm1 = sorted(valid_data_tm1, key=lambda x: int(x["tahun_laporan"]), reverse=True)
                    if sorted_data_tm1:
                        financial_data_tm1 = sorted_data_tm1[0]["hasil_ekstraksi"]
                except (ValueError, TypeError) as e:
                     print(f"Peringatan: Gagal memproses 'hasil_ekstraksi_historis' di file t-1 untuk {company_filename_tm1}: {e}.")
            
            # Jika tidak ada dari historis, ambil dari 'hasil_ekstraksi' utama di file t-1
            if financial_data_tm1 is None and "hasil_ekstraksi" in entry_tm1_specific:
                financial_data_tm1 = entry_tm1_specific["hasil_ekstraksi"]
            
            if financial_data_tm1:
                item_to_add = {
                    "nama_file": company_filename_tm1,
                    "hasil_ekstraksi": financial_data_tm1
                }
                # Jika sudah ada di processed_data_t_minus_1 (dari file utama), timpa
                if company_filename_tm1 in existing_tm1_map:
                    processed_data_t_minus_1[existing_tm1_map[company_filename_tm1]] = item_to_add
                else: # Jika belum ada, tambahkan baru
                    processed_data_t_minus_1.append(item_to_add)
            else:
                print(f"Peringatan: Entri JSON dari file t-1 spesifik untuk {company_filename_tm1} tidak memiliki data keuangan yang valid. Dilewati.")

    if not processed_data_t_minus_1:
        processed_data_t_minus_1 = None
            
    return processed_data_t, processed_data_t_minus_1

def get_company_financial_data(sarana_data_list: list | None, company_filename: str) -> dict | None:
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
    Fungsi ini sekarang mengasumsikan bahwa `data` adalah DOKUMEN KEUANGAN UNTUK SATU TAHUN SPESIFIK.
    Parameter `year_ago` dipertahankan untuk kompatibilitas, tetapi idealnya data t dan t-1
    harus dipisahkan sebelum memanggil fungsi ini, melalui `load_sarana_output` dan `get_company_financial_data`.

    Jika Sarana dimodifikasi untuk menyertakan sub-kamus per tahun dalam satu "hasil_ekstraksi" utama,
    fungsi ini atau pemanggilnya perlu diubah untuk menavigasi ke tahun yang benar.
    Untuk saat ini, `year_ago` > 0 tidak akan berfungsi kecuali `data` itu sendiri
    sudah merupakan data dari tahun lampau yang sesuai.

    Args:
        data (dict | None): Kamus data keuangan hasil ekstraksi Sarana untuk SATU PERIODE TERTENTU.
        key (str): Kata dasar item keuangan yang dicari (misalnya, "Pendapatan bersih").
        year_ago (int): Spesifikasi periode. 
                        0 untuk tahun data yang diberikan.
                        Jika > 0, fungsi ini akan mencoba mencari key dengan embel-embel "Tahun Lalu",
                        namun ini adalah pola lama. Idealnya, pemanggil sudah menyediakan data untuk tahun yang benar.
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
        # Pola lama: mencoba mencari variasi nama kunci untuk tahun lalu.
        # Ini kurang ideal. Lebih baik pemanggil sudah menyediakan data yang benar untuk t-1.
        val_tl_options = [
            f"{key} Tahun Lalu", 
            f"{key} t-1", # Kemungkinan format lain
            # Tambahkan variasi lain jika ada
        ]
        for opt_key in val_tl_options:
            if opt_key in data:
                val = data.get(opt_key)
                break
        if val is None:
            # Jika tidak ada key eksplisit untuk tahun lalu, dan kita diminta data tahun lalu,
            # tapi data yang diberikan adalah untuk tahun t, maka kita tidak bisa mendapatkannya dari sini.
            # Untuk kasus umum, jika year_ago != 0, kita asumsikan 'data' sudah merupakan data dari tahun lampau itu.
            # Jadi, kita tetap cari 'key' saja.
            # print(f"Peringatan: Diminta data tahun lalu untuk '{key}' tapi tidak ada kunci eksplisit tahun lalu. Menggunakan '{key}' dari data yang diberikan.")
            val = data.get(key) # Ini akan mengembalikan nilai dari 'data' yang diberikan, yang mungkin adalah data t, bukan t-1.
                                # Ini menjadi tanggung jawab pemanggil untuk menyediakan data yang benar.
    else: # year_ago > 1 atau < 0
        # Tidak didukung secara eksplisit dengan pola lama, asumsikan 'data' adalah untuk tahun yang benar.
        val = data.get(key)
            
    if isinstance(val, (int, float)):
        return float(val)
    # Coba konversi jika string angka (misal "1.234.567,89" atau "1,234,567.89")
    if isinstance(val, str):
        try:
            # Hapus titik sebagai pemisah ribuan, ganti koma desimal dengan titik
            cleaned_val = val.replace('.', '').replace(',', '.')
            return float(cleaned_val)
        except ValueError:
            # Jika gagal konversi, kembalikan None
            # print(f"Peringatan: Gagal mengkonversi nilai string '{val}' untuk kunci '{key}' menjadi float.")
            return None
    return None
