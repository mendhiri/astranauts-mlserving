# Impor pustaka yang diperlukan
import os
import hashlib  # Untuk membuat hash sebagai kunci cache
import json  # Untuk menyimpan dan membaca data cache dalam format JSON
import time  # Untuk mendapatkan timestamp

# Konstanta untuk nama direktori cache default
NAMA_DIREKTORI_CACHE_DEFAULT = ".cache_parser_dokumen"  # Indonesianized name


# Fungsi untuk membuat kunci cache yang unik berdasarkan path file dan timestamp modifikasi
def buat_kunci_cache_file(path_file: str) -> str | None:
    """
    Membuat kunci cache unik untuk sebuah file berdasarkan path absolut dan timestamp modifikasi terakhirnya.

    Args:
        path_file: Path ke file yang akan dibuatkan kunci cache.

    Returns:
        String hexdigest SHA256 sebagai kunci cache, atau None jika file tidak ditemukan.
    """
    try:
        # Dapatkan path absolut untuk konsistensi
        path_absolut = os.path.abspath(path_file)
        # Dapatkan timestamp modifikasi terakhir file
        timestamp_modifikasi = os.path.getmtime(path_file)

        # Buat string unik yang akan di-hash
        string_untuk_hash = f"{path_absolut}|{timestamp_modifikasi}"

        # Buat objek hash SHA256
        hash_objek = hashlib.sha256(string_untuk_hash.encode('utf-8'))

        # Kembalikan hexdigest dari hash sebagai kunci cache
        return hash_objek.hexdigest()
    except FileNotFoundError:
        print(f"Peringatan: Berkas tidak ditemukan di {path_file} saat membuat kunci cache.")
        return None
    except Exception as e:
        print(f"Error saat membuat kunci cache untuk {path_file}: {e}")
        return None


# Fungsi untuk menyimpan data ke cache
def simpan_ke_cache(kunci_cache: str, data_untuk_cache: dict, direktori_cache_param: str | None = None) -> bool:
    """
    Menyimpan data ke file cache dalam format JSON.

    Args:
        kunci_cache: Kunci unik untuk item cache ini.
        data_untuk_cache: Dictionary yang akan disimpan ke cache.
                          Disarankan menyertakan 'timestamp_pembuatan_cache': time.time() di dalamnya.
        direktori_cache_param: Path ke direktori cache. Jika None, gunakan default.

    Returns:
        True jika penyimpanan berhasil, False jika gagal.
    """
    if not kunci_cache:
        print("Error: Kunci cache tidak valid untuk penyimpanan.")
        return False

    direktori_cache = direktori_cache_param if direktori_cache_param is not None else NAMA_DIREKTORI_CACHE_DEFAULT

    try:
        # Buat direktori cache jika belum ada, exist_ok=True berarti tidak error jika sudah ada
        os.makedirs(direktori_cache, exist_ok=True)

        # Tentukan path lengkap untuk file cache
        path_file_cache: str = os.path.join(direktori_cache, f"{kunci_cache}.json")

        # Simpan data sebagai JSON ke file cache
        with open(path_file_cache, 'w', encoding='utf-8') as f_cache:
            json.dump(data_untuk_cache, f_cache, ensure_ascii=False, indent=4)
        return True
    except OSError as e:  # Lebih spesifik untuk error pembuatan direktori atau file I/O
        print(f"Error OS saat menyimpan ke cache ({path_file_cache}): {e}")
        return False
    except TypeError as e:  # Error jika data_untuk_cache tidak bisa di-serialize ke JSON
        print(f"Error tipe saat serialisasi JSON untuk cache ({kunci_cache}): {e}")
        return False
    except Exception as e:
        print(f"Error tak terduga saat menyimpan ke cache ({kunci_cache}): {e}")
        return False


# Fungsi untuk mengambil data dari cache
def ambil_dari_cache(kunci_cache: str, direktori_cache_param: str | None = None) -> dict | None:
    """
    Mengambil data dari file cache jika ada dan valid.

    Args:
        kunci_cache: Kunci unik untuk item cache yang dicari.
        direktori_cache_param: Path ke direktori cache. Jika None, gunakan default.

    Returns:
        Dictionary yang tersimpan di cache jika ditemukan dan valid, jika tidak maka None.
    """
    if not kunci_cache:
        # print("Info: Kunci cache tidak valid untuk pengambilan.") # Bisa di-uncomment untuk debugging
        return None

    direktori_cache = direktori_cache_param if direktori_cache_param is not None else NAMA_DIREKTORI_CACHE_DEFAULT
    path_file_cache = os.path.join(direktori_cache, f"{kunci_cache}.json")

    if not os.path.exists(path_file_cache):
        return None  # Cache tidak ditemukan

    try:
        with open(path_file_cache, 'r', encoding='utf-8') as f_cache:
            data_dari_cache = json.load(f_cache)
        return data_dari_cache
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON dari file cache {path_file_cache}: {e}. File mungkin rusak.")
        return None
    except Exception as e:
        print(f"Error tak terduga saat mengambil dari cache ({kunci_cache}): {e}")
        return None


# Fungsi (opsional) untuk membersihkan cache lama
def bersihkan_cache_lama(direktori_cache_param: str | None = None,
                         batas_usia_detik: int = 30 * 24 * 60 * 60):  # Default 30 hari
    """
    Membersihkan file cache yang lebih tua dari batas_usia_detik.
    Pembersihan berdasarkan timestamp modifikasi file cache itu sendiri.

    Args:
        direktori_cache_param: Path ke direktori cache. Jika None, gunakan default.
        batas_usia_detik: Batas usia maksimum file cache dalam detik.
    """
    direktori_cache = direktori_cache_param if direktori_cache_param is not None else NAMA_DIREKTORI_CACHE_DEFAULT

    if not os.path.isdir(direktori_cache):
        print(f"Info: Direktori cache '{direktori_cache}' tidak ditemukan, tidak ada yang dibersihkan.")
        return

    print(
        f"Memulai pembersihan cache lama di '{direktori_cache}' untuk file lebih tua dari {batas_usia_detik / (24 * 60 * 60):.0f} hari...")
    jumlah_dihapus = 0
    waktu_sekarang = time.time()

    try:
        for nama_file in os.listdir(direktori_cache):
            if nama_file.endswith(".json"):  # Hanya proses file JSON cache
                path_file_penuh = os.path.join(direktori_cache, nama_file)
                try:
                    timestamp_modifikasi_file = os.path.getmtime(path_file_penuh)
                    if (waktu_sekarang - timestamp_modifikasi_file) > batas_usia_detik:
                        os.remove(path_file_penuh)
                        print(f"Menghapus cache lama: {nama_file}")
                        jumlah_dihapus += 1
                except Exception as e_file:  # Error saat memproses satu file (misal, permission)
                    print(f"Error saat memproses file cache {path_file_penuh} untuk pembersihan: {e_file}")
        print(f"Pembersihan cache selesai. {jumlah_dihapus} file cache lama dihapus.")
    except Exception as e:
        print(f"Error selama proses pembersihan cache: {e}")