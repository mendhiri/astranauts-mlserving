import json

def load_financial_data(json_file_path):
    """
    Memuat data keuangan dari file JSON.
    File JSON diharapkan berisi list dari dictionary, di mana setiap dictionary 
    mewakili satu perusahaan dan memiliki kunci 'nama_file' dan 'hasil_ekstraksi'.

    Args:
        json_file_path (str): Path ke file JSON.

    Returns:
        list: List of dictionaries, di mana setiap dictionary berisi data keuangan 
              satu perusahaan. Mengembalikan list kosong jika gagal atau format tidak sesuai.
    """
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Memastikan data adalah list dan setiap elemen adalah dictionary
        # yang mengandung 'nama_file' dan 'hasil_ekstraksi'
        if isinstance(data, list) and all(isinstance(item, dict) and "nama_file" in item and "hasil_ekstraksi" in item for item in data):
            # Ekstrak hanya bagian yang relevan jika perlu, atau kembalikan apa adanya
            # Untuk saat ini, kita kembalikan list item seperti yang ada di file,
            # karena get_company_financial_data akan memprosesnya.
            return data 
        elif isinstance(data, list) and not data: # Jika list kosong
            print(f"Info: File JSON di {json_file_path} adalah list kosong.")
            return []
        else:
            # Handle kasus di mana JSON mungkin adalah dictionary tunggal yang mewakili satu perusahaan
            # (mirip format lama tapi sekarang diharapkan di dalam list)
            if isinstance(data, dict) and "nama_file" in data and "hasil_ekstraksi" in data:
                print(f"Warning: File JSON di {json_file_path} adalah dictionary tunggal. Dibungkus dalam list.")
                return [data] # Kembalikan sebagai list dengan satu elemen

            print(f"Error: Format JSON tidak sesuai di {json_file_path}. Diharapkan list of dicts, masing-masing dengan 'nama_file' dan 'hasil_ekstraksi'.")
            return []

    except FileNotFoundError:
        print(f"Error: File tidak ditemukan di {json_file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Gagal melakukan decode JSON dari {json_file_path}")
        return []
    except Exception as e:
        print(f"Error saat memuat data dari {json_file_path}: {e}")
        return []

def get_company_financial_data(all_financial_data: list, company_file_name: str):
    """
    Mencari dan mengembalikan data keuangan untuk perusahaan tertentu dari list data keuangan.

    Args:
        all_financial_data (list): List of dictionaries, output dari load_financial_data.
        company_file_name (str): Nama file (identifier) perusahaan yang dicari.

    Returns:
        dict: Dictionary data keuangan ('hasil_ekstraksi') untuk perusahaan yang ditemukan, 
              atau None jika tidak ditemukan.
    """
    if not isinstance(all_financial_data, list):
        print("Error: Input all_financial_data harus berupa list.")
        return None
        
    for company_data in all_financial_data:
        if isinstance(company_data, dict) and company_data.get("nama_file") == company_file_name:
            return company_data.get("hasil_ekstraksi")
    
    print(f"Info: Data untuk perusahaan dengan nama file '{company_file_name}' tidak ditemukan.")
    return None


if __name__ == '__main__':
    # Buat file JSON dummy untuk pengujian
    dummy_data_list_ok = [
        {
            "nama_file": "company_A.pdf",
            "hasil_ekstraksi": {"Pendapatan bersih": 1000.0, "Laba kotor": 500.0}
        },
        {
            "nama_file": "company_B.xlsx",
            "hasil_ekstraksi": {"Pendapatan bersih": 2000.0, "Laba kotor": 1200.0}
        }
    ]
    dummy_data_single_dict_valid_structure = { # Ini akan dibungkus list oleh load_financial_data
        "nama_file": "company_C.pdf",
        "hasil_ekstraksi": {"Pendapatan bersih": 1500.0, "Laba kotor": 700.0}
    }
    dummy_data_bad_format_list = [ # List tapi elemennya tidak punya struktur yang benar
        {"nama_file": "company_D.pdf"}, # hasil_ekstraksi hilang
        {"hasil_ekstraksi": {"Pendapatan bersih": 3000}} # nama_file hilang
    ]
    dummy_data_not_a_list = {"data": "ini bukan list"}
    dummy_data_empty_list_file = []


    with open("dummy_list_ok.json", "w") as f:
        json.dump(dummy_data_list_ok, f)
    with open("dummy_single_dict_valid.json", "w") as f:
        json.dump(dummy_data_single_dict_valid_structure, f)
    with open("dummy_bad_list.json", "w") as f:
        json.dump(dummy_data_bad_format_list, f)
    with open("dummy_not_list.json", "w") as f:
        json.dump(dummy_data_not_a_list, f)
    with open("dummy_empty_list_file.json", "w") as f:
        json.dump(dummy_data_empty_list_file, f)


    print("--- Menguji load_financial_data (baru) ---")
    # Test 1: File list OK
    print("\nTest 1: File JSON format list of dicts (benar)")
    loaded_data1 = load_financial_data("dummy_list_ok.json")
    if isinstance(loaded_data1, list) and len(loaded_data1) == 2 and loaded_data1[0]["nama_file"] == "company_A.pdf":
        print("  Sukses memuat list data standar.")
        # print(f"  Data: {loaded_data1}")
    else:
        print("  Gagal memuat list data standar atau data tidak sesuai.")

    # Test 2: File tidak ditemukan
    print("\nTest 2: File tidak ditemukan")
    loaded_data2 = load_financial_data("tidak_ada_file.json")
    if isinstance(loaded_data2, list) and not loaded_data2: # Harusnya list kosong
        print("  Sukses menangani file tidak ditemukan (return list kosong).")
    else:
        print("  Gagal menangani file tidak ditemukan.")

    # Test 3: File JSON format salah (bukan list atau struktur elemen salah)
    print("\nTest 3a: File JSON format list tapi elemen salah")
    loaded_data3a = load_financial_data("dummy_bad_list.json")
    if isinstance(loaded_data3a, list) and not loaded_data3a: # Harusnya list kosong
        print("  Sukses menangani format list dengan elemen salah (return list kosong).")
    else:
        print("  Gagal menangani format list dengan elemen salah.")
        print(f"  Data: {loaded_data3a}")

    print("\nTest 3b: File JSON bukan list")
    loaded_data3b = load_financial_data("dummy_not_list.json")
    if isinstance(loaded_data3b, list) and not loaded_data3b: # Harusnya list kosong
        print("  Sukses menangani format JSON bukan list (return list kosong).")
    else:
        print("  Gagal menangani format JSON bukan list.")
        print(f"  Data: {loaded_data3b}")
        
    # Test 4: File JSON format list kosong
    print("\nTest 4: File JSON format list kosong")
    loaded_data4 = load_financial_data("dummy_empty_list_file.json")
    if isinstance(loaded_data4, list) and not loaded_data4:
        print("  Sukses menangani list JSON kosong (return list kosong).")
    else:
        print("  Gagal menangani list JSON kosong.")
        print(f"  Data: {loaded_data4}")
        
    # Test 5: File JSON format dictionary tunggal (akan dibungkus list)
    print("\nTest 5: File JSON format dictionary tunggal valid")
    loaded_data5 = load_financial_data("dummy_single_dict_valid.json")
    if isinstance(loaded_data5, list) and len(loaded_data5) == 1 and loaded_data5[0]["nama_file"] == "company_C.pdf":
        print("  Sukses memuat dictionary tunggal (dibungkus list).")
    else:
        print("  Gagal memuat dictionary tunggal atau data tidak sesuai.")
        if loaded_data5 is not None: print(f"  Data returned: {loaded_data5}")

    print("\n--- Menguji get_company_financial_data ---")
    # Data sudah dimuat dari Test 1 (loaded_data1)
    
    # Test 6: Cari perusahaan yang ada
    print("\nTest 6: Cari perusahaan 'company_A.pdf' (ada)")
    company_a_data = get_company_financial_data(loaded_data1, "company_A.pdf")
    if company_a_data and company_a_data.get("Pendapatan bersih") == 1000.0:
        print("  Sukses mendapatkan data company_A.")
        print(f"  Data Company A: {company_a_data}")
    else:
        print("  Gagal mendapatkan data company_A atau data tidak sesuai.")

    # Test 7: Cari perusahaan yang tidak ada
    print("\nTest 7: Cari perusahaan 'company_X.pdf' (tidak ada)")
    company_x_data = get_company_financial_data(loaded_data1, "company_X.pdf")
    if company_x_data is None:
        print("  Sukses menangani perusahaan tidak ditemukan (return None).")
    else:
        print("  Gagal menangani perusahaan tidak ditemukan.")
        print(f"  Data: {company_x_data}")

    # Test 8: Input bukan list ke get_company_financial_data
    print("\nTest 8: Input bukan list ke get_company_financial_data")
    invalid_input_data = get_company_financial_data({"not": "a list"}, "company_A.pdf")
    if invalid_input_data is None:
        print("  Sukses menangani input bukan list (return None).")
    else:
        print("  Gagal menangani input bukan list.")

    # Test 9: List kosong ke get_company_financial_data
    print("\nTest 9: List kosong ke get_company_financial_data")
    empty_list_data = get_company_financial_data([], "company_A.pdf")
    if empty_list_data is None: # Harusnya None karena tidak ditemukan
        print("  Sukses menangani list kosong (return None).")
    else:
        print("  Gagal menangani list kosong.")


    # Hapus file dummy
    import os
    os.remove("dummy_list_ok.json")
    os.remove("dummy_single_dict_valid.json")
    os.remove("dummy_bad_list.json")
    os.remove("dummy_not_list.json")
    os.remove("dummy_empty_list_file.json")
    print("\nSemua file dummy telah dihapus.")