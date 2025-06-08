# Impor pustaka yang diperlukan
from typing import Any
import pymupdf
import io
from PIL import Image
import os
import concurrent.futures  # Untuk pemrosesan paralel
import uuid  # Untuk nama file temporer unik
import time  # Untuk timestamp pada data cache

# Impor fungsi-fungsi cache dari utilitas_cache.py
from utilitas_cache import buat_kunci_cache_file, simpan_ke_cache, ambil_dari_cache

# Usahakan impor dari parser_gambar.py lokal
try:
    from parser_gambar import ekstrak_teks_dari_gambar
except ImportError:
    print("Peringatan: Tidak dapat mengimpor ekstrak_teks_dari_gambar dari parser_gambar. OCR untuk PDF akan gagal.")
    print("Pastikan parser_gambar.py ada di direktori yang sama atau dapat diakses via sys.path.")


    def ekstrak_teks_dari_gambar(path_gambar: str) -> str:
        return f"Error: ekstrak_teks_dari_gambar tidak tersedia (parser_gambar.py tidak ditemukan atau gagal impor). Path: {path_gambar}"


# Fungsi worker untuk melakukan OCR pada satu halaman secara paralel
def ocr_satu_halaman_worker_paralel(nomor_halaman_asli: int, data_pixmap_bytes_png: bytes,
                                    fungsi_ocr_gambar: callable, mesin_ocr: str, 
                                    opsi_praproses: dict) -> tuple[int, str] | tuple[int, Any] | None:
    """
    Worker untuk memproses OCR satu halaman PDF.
    Merender pixmap bytes menjadi gambar, menyimpannya sementara, lalu melakukan OCR.

    Args:
        nomor_halaman_asli: Nomor halaman asli untuk pengurutan.
        data_pixmap_bytes_png: Bytes dari pixmap halaman dalam format PNG.
        fungsi_ocr_gambar: Fungsi yang akan dipanggil untuk OCR gambar.

    Returns:
        Tuple berisi (nomor_halaman_asli, teks_hasil_ocr).
    """
    path_gambar_temporer_worker = f"temp_page_ocr_{nomor_halaman_asli}_{uuid.uuid4()}.png"
    teks_hasil_ocr = ""
    try:
        gambar_pil = Image.open(io.BytesIO(data_pixmap_bytes_png))
        gambar_pil.save(path_gambar_temporer_worker)
        # Panggil fungsi OCR dengan parameter tambahan
        teks_hasil_ocr = fungsi_ocr_gambar(path_gambar_temporer_worker, 
                                           mesin_ocr=mesin_ocr, 
                                           opsi_praproses=opsi_praproses)
        return nomor_halaman_asli, teks_hasil_ocr.strip()
    except Exception as e:
        print(f"Error di worker OCR untuk halaman {nomor_halaman_asli}: {e}")
        return nomor_halaman_asli, f"Error OCR halaman {nomor_halaman_asli}: {e}"
    finally:
        if os.path.exists(path_gambar_temporer_worker):
            try:
                os.remove(path_gambar_temporer_worker)
            except Exception as e_rm:
                print(f"Gagal menghapus file temporer worker {path_gambar_temporer_worker}: {e_rm}")


# Fungsi utama untuk mengekstrak teks dari berkas PDF dengan caching dan pemrosesan paralel
def ekstrak_teks_dari_pdf(path_file_pdf: str, fungsi_ocr_untuk_gambar: callable,
                          mesin_ocr: str = 'tesseract', opsi_praproses: dict = None,
                          direktori_cache_kustom: str | None = None) -> str:
    """
    Mengekstrak teks dari berkas PDF dengan caching. Menggunakan ekstraksi teks langsung jika memungkinkan,
    dan pemrosesan OCR paralel untuk halaman berbasis gambar. Hasil disimpan dan diambil dari cache.

    Args:
        path_file_pdf: Path berkas ke file .pdf.
        fungsi_ocr_untuk_gambar: Fungsi callable untuk OCR gambar (seharusnya parser_gambar.ekstrak_teks_dari_gambar).
        mesin_ocr: Nama mesin OCR yang akan digunakan (misalnya, 'tesseract', 'easyocr').
        opsi_praproses: Dictionary opsi pra-pemrosesan untuk diteruskan ke fungsi OCR gambar.
        direktori_cache_kustom: Path opsional ke direktori cache. Jika None, default dari utilitas_cache akan digunakan.

    Returns:
        Teks yang diekstrak dari semua halaman, atau pesan error.
    """
    # Coba ambil dari cache terlebih dahulu
    kunci_cache_dokumen = buat_kunci_cache_file(path_file_pdf)
    if kunci_cache_dokumen:  # Hanya lanjut jika kunci cache berhasil dibuat (file ada)
        data_cache = ambil_dari_cache(kunci_cache_dokumen, direktori_cache_kustom)
        if data_cache is not None and isinstance(data_cache, dict) and 'teks_dokumen' in data_cache:
            print(f"Mengambil hasil dari cache untuk: {os.path.basename(path_file_pdf)}")
            return data_cache['teks_dokumen']
    else:  # Jika file tidak ditemukan saat buat kunci cache, langsung return error
        return f"Error memproses berkas PDF: Berkas tidak ditemukan di {path_file_pdf} (saat membuat kunci cache)."

    print(f"Cache tidak ditemukan atau tidak valid untuk {os.path.basename(path_file_pdf)}, memproses dari awal.")
    dokumen_pdf = None
    try:
        dokumen_pdf = pymupdf.open(path_file_pdf)
        jumlah_halaman = len(dokumen_pdf)
        semua_bagian_teks = [None] * jumlah_halaman
        halaman_perlu_ocr_data = []

        for nomor_halaman in range(jumlah_halaman):
            halaman = dokumen_pdf.load_page(nomor_halaman)
            teks_langsung = halaman.get_text("text").strip()
            if teks_langsung:
                semua_bagian_teks[nomor_halaman] = teks_langsung
            else:
                pix = halaman.get_pixmap()
                data_pixmap_bytes_png = pix.tobytes("png")
                halaman_perlu_ocr_data.append((nomor_halaman, data_pixmap_bytes_png))

        if halaman_perlu_ocr_data:
            maks_worker = min(8, os.cpu_count() + 4 if os.cpu_count() else 4)
            with concurrent.futures.ThreadPoolExecutor(max_workers=maks_worker) as executor:
                futures_ocr = [
                    executor.submit(ocr_satu_halaman_worker_paralel, 
                                    no_hlm, 
                                    data_bytes, 
                                    fungsi_ocr_untuk_gambar,
                                    mesin_ocr,      # Teruskan mesin_ocr
                                    opsi_praproses  # Teruskan opsi_praproses
                                   )
                    for no_hlm, data_bytes in halaman_perlu_ocr_data]

                for future in concurrent.futures.as_completed(futures_ocr):
                    try:
                        no_hlm_hasil, teks_ocr_hasil = future.result()
                        semua_bagian_teks[no_hlm_hasil] = teks_ocr_hasil
                    except Exception as e_future:
                        print(f"Error saat mengambil hasil dari future OCR: {e_future}")
                        # Mencoba mencari nomor halaman dari argumen future secara manual tidak standar/mudah.
                        # Worker dirancang untuk selalu mengembalikan nomor halaman, jadi error harusnya ditangani di sana.
                        # Jika error terjadi sebelum worker mengembalikan, kita tidak tahu halaman mana yang gagal di sini.
                        # Untuk sementara, kita bisa menandai bahwa ada error, tapi tidak pada halaman spesifik.
                        # Atau, jika ada cara untuk mendapatkan argumen awal future, bisa digunakan.
                        # Dalam kasus ini, karena worker mengembalikan nomor halaman bahkan saat error, ini seharusnya aman.

        teks_final_hasil_ekstraksi = []
        for i, teks_bagian in enumerate(semua_bagian_teks):
            if teks_bagian is None:
                teks_final_hasil_ekstraksi.append(f"[Error: Halaman {i + 1} PDF tidak dapat diproses]")
            else:
                teks_final_hasil_ekstraksi.append(teks_bagian)

        hasil_gabungan = "\n\n".join(teks_final_hasil_ekstraksi)

        # Simpan hasil ke cache
        if kunci_cache_dokumen:  # Pastikan kunci ada
            print(f"Menyimpan hasil ke cache untuk: {os.path.basename(path_file_pdf)}")
            data_untuk_disimpan = {'teks_dokumen': hasil_gabungan, 'timestamp_pembuatan_cache': time.time()}
            simpan_ke_cache(kunci_cache_dokumen, data_untuk_disimpan, direktori_cache_kustom)

        return hasil_gabungan

    except FileNotFoundError:  # Seharusnya sudah ditangani oleh pemeriksaan kunci cache, tapi sebagai fallback
        return f"Error memproses berkas PDF: Berkas tidak ditemukan di {path_file_pdf}"
    except Exception as e:
        return f"Error umum memproses berkas PDF '{os.path.basename(path_file_pdf)}': {e}"
    finally:
        if dokumen_pdf:
            dokumen_pdf.close()
