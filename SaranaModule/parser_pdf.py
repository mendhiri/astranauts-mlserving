# Impor pustaka yang diperlukan
from typing import Any
import pymupdf
import pdfplumber
import io
from PIL import Image
import os
import concurrent.futures  # Untuk pemrosesan paralel
import uuid  # Untuk nama file temporer unik
import time  # Untuk timestamp pada data cache

# Impor fungsi-fungsi cache dari utilitas_cache.py
from SaranaModule.utilitas_cache import buat_kunci_cache_file, simpan_ke_cache, ambil_dari_cache

# Usahakan impor dari parser_gambar.py lokal
try:
    from SaranaModule.parser_gambar import ekstrak_teks_dari_gambar
except ImportError:
    print("Peringatan: Tidak dapat mengimpor ekstrak_teks_dari_gambar dari parser_gambar. OCR untuk PDF akan gagal.")
    print("Pastikan parser_gambar.py ada di direktori yang sama atau dapat diakses via sys.path.")


    def ekstrak_teks_dari_gambar(path_gambar: str) -> str:
        return f"Error: ekstrak_teks_dari_gambar tidak tersedia (parser_gambar.py tidak ditemukan atau gagal impor). Path: {path_gambar}"


# Fungsi worker untuk melakukan OCR pada satu halaman secara paralel
def ocr_satu_halaman_worker_paralel(nomor_halaman_asli: int, data_pixmap_bytes_png: bytes,
                                    fungsi_ocr_gambar: callable, mesin_ocr: str,
                                    opsi_praproses: dict, prompt_ollama: str) -> tuple[int, str] | tuple[int, Any] | None:
    """
    Worker untuk memproses OCR satu halaman PDF.
    Merender pixmap bytes menjadi gambar, menyimpannya sementara, lalu melakukan OCR.

    Args:
        nomor_halaman_asli (int): Nomor halaman asli untuk pengurutan.
        data_pixmap_bytes_png (bytes): Bytes dari pixmap halaman dalam format PNG.
        fungsi_ocr_gambar (callable): Fungsi yang akan dipanggil untuk OCR gambar (misalnya, `ekstrak_teks_dari_gambar`).
        mesin_ocr (str): Nama mesin OCR yang akan digunakan ('tesseract', 'ollama', dll.).
        opsi_praproses (dict): Opsi pra-pemrosesan untuk mesin OCR non-Ollama.
        prompt_ollama (str): Prompt yang akan digunakan jika `mesin_ocr` adalah 'ollama'.

    Returns:
        tuple[int, str]: Tuple berisi (nomor_halaman_asli, teks_hasil_ocr).
                         Jika error, teks_hasil_ocr akan berisi pesan error.
    """
    # Membuat nama file temporer yang unik untuk setiap worker dan halaman
    # Menggunakan uuid4().hex untuk nama yang lebih pendek dan aman untuk sistem file
    nama_file_temp_worker = f"temp_pdf_page_{nomor_halaman_asli}_{uuid.uuid4().hex}.png"
    path_gambar_temporer_worker = os.path.join(".", nama_file_temp_worker) # Simpan di direktori kerja saat ini

    teks_hasil_ocr = ""
    try:
        # Buka gambar dari bytes dan simpan ke file temporer
        gambar_pil = Image.open(io.BytesIO(data_pixmap_bytes_png))
        gambar_pil.save(path_gambar_temporer_worker)
        
        print(f"INFO (Worker Halaman {nomor_halaman_asli}): Melakukan OCR pada '{path_gambar_temporer_worker}' menggunakan mesin '{mesin_ocr}'...")

        # Panggil fungsi OCR yang sesuai dengan parameter yang benar
        if mesin_ocr == 'ollama':
            hasil_ocr_mentah = fungsi_ocr_gambar(
                path_gambar_temporer_worker,
                mesin_ocr=mesin_ocr,
                prompt_ollama=prompt_ollama # Teruskan prompt_ollama untuk Ollama
            )
        else:
            # Untuk Tesseract, EasyOCR, dll., gunakan opsi_praproses
            hasil_ocr_mentah = fungsi_ocr_gambar(
                path_gambar_temporer_worker,
                mesin_ocr=mesin_ocr,
                opsi_praproses=opsi_praproses # Teruskan opsi_praproses untuk mesin lain
            )
        
        # Gabungkan hasil jika berupa list (umumnya dari parser_gambar)
        if isinstance(hasil_ocr_mentah, list):
            teks_hasil_ocr = '\n'.join(hasil_ocr_mentah).strip()
        else:
            teks_hasil_ocr = str(hasil_ocr_mentah).strip() # Pastikan string jika bukan list

        print(f"INFO (Worker Halaman {nomor_halaman_asli}): OCR selesai, teks diekstrak (awal 100 char): '{teks_hasil_ocr[:100]}...'")
        return nomor_halaman_asli, teks_hasil_ocr

    except Exception as e_ocr_worker:
        # Log error yang lebih detail
        error_msg = f"Error di worker OCR untuk halaman {nomor_halaman_asli} ({path_gambar_temporer_worker}): {type(e_ocr_worker).__name__} - {e_ocr_worker}"
        print(f"ERROR: {error_msg}")
        return nomor_halaman_asli, f"Error OCR halaman {nomor_halaman_asli}: {e_ocr_worker}"
    finally:
        # Selalu coba hapus file temporer
        if os.path.exists(path_gambar_temporer_worker):
            try:
                os.remove(path_gambar_temporer_worker)
            except Exception as e_rm_worker:
                print(f"PERINGATAN: Gagal menghapus file temporer worker '{path_gambar_temporer_worker}': {e_rm_worker}")


# Fungsi utama untuk mengekstrak teks dari berkas PDF dengan caching dan pemrosesan paralel
def ekstrak_teks_dari_pdf(path_file_pdf: str, fungsi_ocr_untuk_gambar: callable,
                          mesin_ocr: str = 'tesseract', opsi_praproses: dict = None,
                          direktori_cache_kustom: str | None = None,
                          prompt_ollama: str = "get all the data from the image") -> str:
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
        
        # Helper function to check for keywords
        def is_entitas_induk_page(page_text_content: str) -> bool:
            if not page_text_content:
                return False
            # Check within the first 200 chars, case-insensitive
            search_area = page_text_content[:200].lower()
            return "entitas induk" in search_area or "parent entity" in search_area

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
                                    opsi_praproses, # Teruskan opsi_praproses
                                    prompt_ollama   # Teruskan prompt_ollama
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

        # NEW FILTERING LOGIC STARTS HERE
        teks_final_dari_entitas_induk_saja = []
        for i, teks_halaman_tunggal in enumerate(semua_bagian_teks):
            if teks_halaman_tunggal is None:
                # print(f"Peringatan: Halaman {i + 1} PDF tidak memiliki konten setelah diproses.")
                continue # Skip pages with no content

            if is_entitas_induk_page(teks_halaman_tunggal):
                teks_final_dari_entitas_induk_saja.append(teks_halaman_tunggal)
            # else:
                # print(f"INFO: Halaman {i+1} dilewati karena bukan 'Entitas Induk'.")

        # If no "Entitas Induk" pages found, return empty string
        if not teks_final_dari_entitas_induk_saja:
            print(f"INFO: Tidak ada halaman 'Entitas Induk' yang ditemukan dalam {os.path.basename(path_file_pdf)}.")
            hasil_gabungan = "" 
        else:
            hasil_gabungan = "\n\n".join(teks_final_dari_entitas_induk_saja)

        # Simpan hasil ke cache (either combined "Entitas Induk" text or empty string)
        if kunci_cache_dokumen:
            print(f"Menyimpan hasil (hanya Entitas Induk atau kosong) ke cache untuk: {os.path.basename(path_file_pdf)}")
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

# Fungsi untuk mengekstrak teks dari PDF menggunakan pdfplumber
def ekstrak_teks_dari_pdf_pdfplumber(path_file_pdf: str) -> str:
    """
    Mengekstrak teks dari berkas PDF menggunakan pdfplumber.
    Fokus pada ekstraksi teks mentah dari semua halaman.

    Args:
        path_file_pdf: Path berkas ke file .pdf.

    Returns:
        Teks yang diekstrak dari semua halaman, atau pesan error.
    """
    print(f"INFO: Memulai ekstraksi teks dari '{os.path.basename(path_file_pdf)}' menggunakan pdfplumber.")
    semua_teks_halaman = []
    try:
        with pdfplumber.open(path_file_pdf) as pdf:
            if not pdf.pages:
                print(f"PERINGATAN: Tidak ada halaman ditemukan dalam PDF '{os.path.basename(path_file_pdf)}' oleh pdfplumber.")
                return ""
            
            for i, page in enumerate(pdf.pages):
                # Coba ekstrak teks; jika halaman tidak ada teks, extract_text() akan mengembalikan None atau string kosong
                teks_halaman = page.extract_text(x_tolerance=3, y_tolerance=3, layout=False, x_density=7.25, y_density=13)
                if teks_halaman:
                    semua_teks_halaman.append(teks_halaman.strip())
                else:
                    # Jika extract_text tidak menghasilkan apa-apa, mungkin halaman adalah gambar.
                    # Untuk saat ini, kita tidak melakukan OCR di sini, hanya teks.
                    print(f"INFO: Halaman {i+1} di '{os.path.basename(path_file_pdf)}' tidak menghasilkan teks via pdfplumber.extract_text(). Mungkin halaman berbasis gambar.")
            
            if not semua_teks_halaman:
                print(f"PERINGATAN: Tidak ada teks yang berhasil diekstrak dari '{os.path.basename(path_file_pdf)}' menggunakan pdfplumber.")
                return ""

        hasil_gabungan_pdfplumber = "\n\n".join(semua_teks_halaman)
        print(f"INFO: Ekstraksi teks dengan pdfplumber dari '{os.path.basename(path_file_pdf)}' selesai. Total karakter: {len(hasil_gabungan_pdfplumber)}")
        return hasil_gabungan_pdfplumber

    except FileNotFoundError:
        return f"Error memproses berkas PDF dengan pdfplumber: Berkas tidak ditemukan di {path_file_pdf}"
    except Exception as e:
        return f"Error umum memproses berkas PDF '{os.path.basename(path_file_pdf)}' dengan pdfplumber: {type(e).__name__} - {e}"


# Fungsi utama untuk mengekstrak teks dari berkas PDF dengan caching dan pemrosesan paralel
def ekstrak_teks_dari_pdf(path_file_pdf: str, fungsi_ocr_untuk_gambar: callable,
                          mesin_ocr: str = 'tesseract', opsi_praproses: dict = None,
                          direktori_cache_kustom: str | None = None,
                          prompt_ollama: str = "get all the data from the image",
                          metode_parsing: str = 'pymupdf') -> str: # Tambahkan parameter metode_parsing
    """
    Mengekstrak teks dari berkas PDF dengan caching. Menggunakan ekstraksi teks langsung jika memungkinkan,
    dan pemrosesan OCR paralel untuk halaman berbasis gambar (jika metode_parsing='pymupdf').
    Jika metode_parsing='pdfplumber', akan menggunakan pdfplumber untuk ekstraksi teks.
    Hasil disimpan dan diambil dari cache.

    Args:
        path_file_pdf: Path berkas ke file .pdf.
        fungsi_ocr_untuk_gambar: Fungsi callable untuk OCR gambar (untuk PyMuPDF).
        mesin_ocr: Nama mesin OCR yang akan digunakan (untuk PyMuPDF).
        opsi_praproses: Dictionary opsi pra-pemrosesan (untuk PyMuPDF).
        direktori_cache_kustom: Path opsional ke direktori cache.
        prompt_ollama: Prompt untuk Ollama OCR (untuk PyMuPDF).
        metode_parsing: Metode parsing PDF ('pymupdf' atau 'pdfplumber').

    Returns:
        Teks yang diekstrak dari semua halaman, atau pesan error.
    """
    # Modifikasi kunci cache untuk menyertakan metode parsing
    kunci_cache_dokumen = buat_kunci_cache_file(path_file_pdf, extra_key_info=f"method:{metode_parsing}")

    if kunci_cache_dokumen:
        data_cache = ambil_dari_cache(kunci_cache_dokumen, direktori_cache_kustom)
        if data_cache is not None and isinstance(data_cache, dict) and 'teks_dokumen' in data_cache:
            print(f"Mengambil hasil dari cache untuk: {os.path.basename(path_file_pdf)} (Metode: {metode_parsing})")
            return data_cache['teks_dokumen']
    else:
        return f"Error memproses berkas PDF: Berkas tidak ditemukan di {path_file_pdf} (saat membuat kunci cache)."

    print(f"Cache tidak ditemukan atau tidak valid untuk {os.path.basename(path_file_pdf)} (Metode: {metode_parsing}), memproses dari awal.")

    hasil_teks_final = ""

    if metode_parsing == 'pdfplumber':
        hasil_teks_final = ekstrak_teks_dari_pdf_pdfplumber(path_file_pdf)
        # Untuk pdfplumber, kita tidak melakukan filter "entitas induk" di sini,
        # karena pdfplumber diasumsikan mengekstrak teks dari PDF yang tidak memerlukan OCR per halaman
        # dan filter entitas induk lebih relevan untuk output OCR yang mungkin berisik.
        # Jika diperlukan, filter bisa ditambahkan setelah pemanggilan ini.
    
    elif metode_parsing == 'pymupdf':
        dokumen_pdf_pymupdf = None
        try:
            dokumen_pdf_pymupdf = pymupdf.open(path_file_pdf)
            jumlah_halaman = len(dokumen_pdf_pymupdf)
            
            def is_entitas_induk_page(page_text_content: str) -> bool:
                if not page_text_content: return False
                search_area = page_text_content[:200].lower()
                return "entitas induk" in search_area or "parent entity" in search_area

            semua_bagian_teks = [None] * jumlah_halaman
            halaman_perlu_ocr_data = []

            for nomor_halaman in range(jumlah_halaman):
                halaman = dokumen_pdf_pymupdf.load_page(nomor_halaman)
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
                                        no_hlm, data_bytes, fungsi_ocr_untuk_gambar,
                                        mesin_ocr, opsi_praproses, prompt_ollama)
                        for no_hlm, data_bytes in halaman_perlu_ocr_data]

                    for future in concurrent.futures.as_completed(futures_ocr):
                        try:
                            no_hlm_hasil, teks_ocr_hasil = future.result()
                            semua_bagian_teks[no_hlm_hasil] = teks_ocr_hasil
                        except Exception as e_future:
                            print(f"Error saat mengambil hasil dari future OCR: {e_future}")
            
            teks_final_dari_entitas_induk_saja = []
            for i, teks_halaman_tunggal in enumerate(semua_bagian_teks):
                if teks_halaman_tunggal is None: continue
                if is_entitas_induk_page(teks_halaman_tunggal):
                    teks_final_dari_entitas_induk_saja.append(teks_halaman_tunggal)
            
            if not teks_final_dari_entitas_induk_saja:
                print(f"INFO (PyMuPDF): Tidak ada halaman 'Entitas Induk' yang ditemukan dalam {os.path.basename(path_file_pdf)}.")
                hasil_teks_final = "" 
            else:
                hasil_teks_final = "\n\n".join(teks_final_dari_entitas_induk_saja)

        except FileNotFoundError:
            return f"Error (PyMuPDF): Berkas tidak ditemukan di {path_file_pdf}"
        except Exception as e:
            return f"Error umum (PyMuPDF) '{os.path.basename(path_file_pdf)}': {e}"
        finally:
            if dokumen_pdf_pymupdf:
                dokumen_pdf_pymupdf.close()
    else:
        return f"Error: Metode parsing '{metode_parsing}' tidak dikenal. Pilih 'pymupdf' atau 'pdfplumber'."

    # Simpan hasil ke cache (untuk kedua metode)
    if kunci_cache_dokumen: # Periksa lagi karena bisa jadi None jika file tidak ada di awal
        print(f"Menyimpan hasil ke cache untuk: {os.path.basename(path_file_pdf)} (Metode: {metode_parsing})")
        data_untuk_disimpan = {'teks_dokumen': hasil_teks_final, 'timestamp_pembuatan_cache': time.time()}
        simpan_ke_cache(kunci_cache_dokumen, data_untuk_disimpan, direktori_cache_kustom)
    
    return hasil_teks_final
