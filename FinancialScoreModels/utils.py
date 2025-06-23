import json

def load_financial_data(json_file_path):
    """
    Memuat data keuangan dari file JSON.
    Diasumsikan file JSON berisi list dengan satu dictionary,
    dan data keuangan ada di bawah kunci 'hasil_ekstraksi'.

    Args:
        json_file_path (str): Path ke file JSON.

    Returns:
        dict: Dictionary data keuangan jika berhasil, atau None jika gagal.
    """
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Asumsi struktur: [{ "nama_file": "...", "hasil_ekstraksi": {...} }]
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            if "hasil_ekstraksi" in data[0]:
                return data[0]["hasil_ekstraksi"]
            else:
                print(f"Error: Kunci 'hasil_ekstraksi' tidak ditemukan dalam elemen pertama di {json_file_path}")
                return None
        else:
            # Mencoba membaca jika JSON adalah dictionary langsung yang berisi hasil ekstraksi
            if isinstance(data, dict) and "hasil_ekstraksi" in data :
                 return data["hasil_ekstraksi"]
            elif isinstance(data,dict) and all(isinstance(val, (int, float, str)) or isinstance(val,dict) for val in data.values()):
                 # Jika file JSON adalah dictionary data keuangan langsung (tanpa 'hasil_ekstraksi')
                 # Ini berguna jika format JSON lebih sederhana
                 # Verifikasi sederhana bahwa ini mungkin dictionary data keuangan
                 # (semua value adalah angka/string atau dictionary lain)
                 # Ini mungkin perlu disesuaikan berdasarkan format JSON yang paling umum
                 # Untuk sekarang, kita prioritaskan format dengan 'hasil_ekstraksi'
                 # print(f"Warning: Membaca {json_file_path} sebagai dictionary data keuangan langsung karena 'hasil_ekstraksi' tidak ditemukan di level atas.")
                 # return data 
                 # Untuk konsistensi dengan format yang diharapkan, kembalikan None jika 'hasil_ekstraksi' tidak ada
                 print(f"Error: Format JSON tidak sesuai. Diharapkan list of dicts dengan 'hasil_ekstraksi' atau dict dengan 'hasil_ekstraksi'. Path: {json_file_path}")
                 return None


    except FileNotFoundError:
        print(f"Error: File tidak ditemukan di {json_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Gagal melakukan decode JSON dari {json_file_path}")
        return None
    except Exception as e:
        print(f"Error saat memuat data dari {json_file_path}: {e}")
        return None

if __name__ == '__main__':
    # Buat file JSON dummy untuk pengujian
    dummy_data_ok = [
        {
            "nama_file": "test_report.pdf",
            "hasil_ekstraksi": {
                "Pendapatan bersih": 1000.0,
                "Laba kotor": 500.0,
                "Beban usaha": 200.0
            }
        }
    ]
    dummy_data_direct_dict_he = {
        "nama_file": "test_report.pdf",
        "hasil_ekstraksi": {
            "Pendapatan bersih": 1000.0,
            "Laba kotor": 500.0
        }
    }
    dummy_data_direct_financial = {
         "Pendapatan bersih": 1000.0,
         "Laba kotor": 500.0
    }

    dummy_data_bad_format = {"data": "ini format salah"}
    dummy_data_empty_list = []


    with open("dummy_financial_ok.json", "w") as f:
        json.dump(dummy_data_ok, f)
    
    with open("dummy_financial_direct_he.json", "w") as f:
        json.dump(dummy_data_direct_dict_he, f)

    with open("dummy_financial_direct_financial.json", "w") as f:
        json.dump(dummy_data_direct_financial, f)

    with open("dummy_financial_bad.json", "w") as f:
        json.dump(dummy_data_bad_format, f)
    
    with open("dummy_financial_empty.json", "w") as f:
        json.dump(dummy_data_empty_list, f)

    print("--- Menguji load_financial_data ---")

    # Test case 1: File OK
    print("\nTest 1: File JSON format standar (list of dicts)")
    data1 = load_financial_data("dummy_financial_ok.json")
    if data1 and data1.get("Pendapatan bersih") == 1000.0:
        print("  Sukses memuat data standar.")
        print(f"  Data: {data1}")
    else:
        print("  Gagal memuat data standar atau data tidak sesuai.")

    # Test case 2: File tidak ditemukan
    print("\nTest 2: File tidak ditemukan")
    data2 = load_financial_data("tidak_ada_file.json")
    if data2 is None:
        print("  Sukses menangani file tidak ditemukan.")
    else:
        print("  Gagal menangani file tidak ditemukan.")

    # Test case 3: File JSON format salah (bukan list atau tidak ada 'hasil_ekstraksi')
    print("\nTest 3: File JSON format salah")
    data3 = load_financial_data("dummy_financial_bad.json")
    if data3 is None:
        print("  Sukses menangani format JSON salah.")
    else:
        print("  Gagal menangani format JSON salah.")
        print(f"  Data: {data3}")


    # Test case 4: File JSON format list kosong
    print("\nTest 4: File JSON format list kosong")
    data4 = load_financial_data("dummy_financial_empty.json")
    if data4 is None:
        print("  Sukses menangani list JSON kosong.")
    else:
        print("  Gagal menangani list JSON kosong.")
        print(f"  Data: {data4}")
        
    # Test case 5: File JSON format dictionary langsung dengan 'hasil_ekstraksi'
    print("\nTest 5: File JSON format dictionary dengan 'hasil_ekstraksi'")
    data5 = load_financial_data("dummy_financial_direct_he.json")
    if data5 and data5.get("Pendapatan bersih") == 1000.0:
        print("  Sukses memuat data dari dict dengan 'hasil_ekstraksi'.")
        print(f"  Data: {data5}")
    else:
        print("  Gagal memuat data dari dict dengan 'hasil_ekstraksi' atau data tidak sesuai.")
        if data5 is not None: print(f"  Data returned: {data5}")

    # Test case 6: File JSON format dictionary data keuangan langsung (tanpa 'hasil_ekstraksi')
    # Perubahan: Fungsi sekarang akan mengembalikan None jika 'hasil_ekstraksi' tidak ada
    # untuk menjaga konsistensi format yang diharapkan.
    print("\nTest 6: File JSON format dictionary data keuangan langsung (seharusnya gagal karena ekspektasi format)")
    data6 = load_financial_data("dummy_financial_direct_financial.json")
    if data6 is None:
        print("  Sukses (gagal memuat karena tidak ada 'hasil_ekstraksi' sesuai ekspektasi).")
    else:
        print("  Gagal (seharusnya tidak memuat data ini tanpa 'hasil_ekstraksi').")
        print(f"  Data: {data6}")


    # Hapus file dummy
    import os
    os.remove("dummy_financial_ok.json")
    os.remove("dummy_financial_direct_he.json")
    os.remove("dummy_financial_direct_financial.json")
    os.remove("dummy_financial_bad.json")
    os.remove("dummy_financial_empty.json")
    print("\nFile dummy telah dihapus.")