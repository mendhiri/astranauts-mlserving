# Impor pustaka standar Python
import os
import shutil # Meskipun tidak untuk dummy, mungkin berguna untuk manajemen file tes
import io
import uuid # Untuk nama file temporer unik
import time # Untuk timestamp pada data cache (jika PDF test menggunakannya)

# Impor untuk membuat gambar uji
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None # Akan dicek nanti
    ImageDraw = None
    ImageFont = None
    print("Peringatan: Pillow (PIL) tidak terinstal. Pembuatan gambar uji akan dilewati.")

# Impor fungsi dari modul-modul kita
from parser_gambar import ekstrak_teks_dari_gambar, DEFAULT_OPSI_PRAPROSES # Import default juga
# from parser_gambar import ekstrak_data_terstruktur_vision # This will be mocked
from parser_dokumen_teks import ekstrak_teks_dari_txt, ekstrak_teks_dari_docx
from parser_pdf import ekstrak_teks_dari_pdf
from pengekstrak_kata_kunci import ekstrak_data_keuangan_tahunan, format_ke_json, ekstrak_data_keuangan_dari_struktur_vision, DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT, normalisasi_nilai_keuangan

# Impor untuk mocking
import unittest # Diperlukan untuk mock jika tidak ada Testcase
from unittest.mock import patch

# --- Konfigurasi untuk Tes OCR Baru ---
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data_ocr')
TEST_IMAGE_PATH = os.path.join(TEST_DATA_DIR, "test_image_ocr.png")
# TEST_PDF_PATH = os.path.join(TEST_DATA_DIR, "test_document_ocr.pdf") # Placeholder

def setup_test_files():
    """Membuat direktori dan file yang dibutuhkan untuk tes OCR."""
    print("\n--- Menyiapkan File Tes OCR ---")
    if not os.path.exists(TEST_DATA_DIR):
        try:
            os.makedirs(TEST_DATA_DIR)
            print(f"Direktori tes dibuat: {TEST_DATA_DIR}")
        except Exception as e:
            print(f"Gagal membuat direktori tes {TEST_DATA_DIR}: {e}")
            return False # Gagal setup

    if Image is None:
        print("Pillow (PIL) tidak tersedia, tidak dapat membuat gambar tes.")
        return False # Gagal setup

    # Membuat gambar PNG sederhana dengan teks "Hello World Test 123"
    try:
        img = Image.new('RGB', (400, 100), color = (255, 255, 255))
        d = ImageDraw.Draw(img)
        try:
            # Mencoba font umum, jika gagal, gunakan font default
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
        d.text((10,10), "Hello World Test 123", fill=(0,0,0), font=font)
        img.save(TEST_IMAGE_PATH)
        print(f"Gambar tes dibuat: {TEST_IMAGE_PATH}")
        return True # Setup berhasil
    except Exception as e:
        print(f"Error saat membuat gambar tes {TEST_IMAGE_PATH}: {e}")
        return False # Gagal setup

    # Pembuatan PDF tes dilewati untuk saat ini sesuai instruksi.

def assert_contains_text(output_text, expected_substrings, test_name=""):
    """Helper untuk memeriksa apakah output mengandung semua substring yang diharapkan."""
    if not isinstance(output_text, str):
        print(f"Assertion GAGAL [{test_name}]: Output bukan string. Diterima: {type(output_text)}")
        return False
    all_found = True
    for sub in expected_substrings:
        if sub.lower() not in output_text.lower(): # Cek case-insensitive
            print(f"Assertion GAGAL [{test_name}]: Substring '{sub}' tidak ditemukan dalam output: '{output_text[:200]}...'")
            all_found = False
    if all_found:
        print(f"Assertion BERHASIL [{test_name}]: Semua substring yang diharapkan ditemukan.")
    return all_found

def run_image_ocr_tests():
    """Menjalankan semua tes OCR untuk gambar."""
    print("\n\n--- Menjalankan Tes OCR Gambar ---")
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"Gambar tes {TEST_IMAGE_PATH} tidak ditemukan. Melewati tes OCR gambar.")
        return

    # Test 1: Tesseract Direct
    print("\n--- Tes: Tesseract Direct ---")
    try:
        opsi_tesseract_test = {
            'denoising': None,
            'sharpening': False,
            'contrast': None,
            'binarization': {'method': 'adaptive_gaussian', 'block_size': 11, 'C': 2, 'invert': True}, # Minimal binarization
            'deskew': False,
            'remove_borders': False,
            'crop_final': False,
            'min_ocr_height': 0, # No resize
            'pyocr_lang': 'eng',
            'tesseract_config': r'--oem 3 --psm 3' # Try PSM 3 (default auto)
        }
        print(f"Opsi untuk Tesseract Direct (minimal preprocessing): {opsi_tesseract_test}")
        text_tess = ekstrak_teks_dari_gambar(TEST_IMAGE_PATH, mesin_ocr='tesseract', opsi_praproses=opsi_tesseract_test)
        assert_contains_text(text_tess, ["Hello", "World", "123"], "Tesseract Direct")
    except Exception as e:
        print(f"Error selama tes Tesseract Direct: {e}")

    # Test 2: EasyOCR
    print("\n--- Tes: EasyOCR ---")
    try:
        text_easy = ekstrak_teks_dari_gambar(TEST_IMAGE_PATH, mesin_ocr='easyocr')
        assert_contains_text(text_easy, ["Hello", "World", "123"], "EasyOCR")
    except ImportError: # Ditangani di parser_gambar, tapi bisa juga di sini jika easyocr = None
        print("EasyOCR tidak terinstal atau tidak dapat diimpor. Melewati tes EasyOCR.")
    except Exception as e:
        print(f"Error selama tes EasyOCR: {e}") # Termasuk runtime error jika model gagal load

    # Test 3: PyOCR dengan Tesseract
    print("\n--- Tes: PyOCR (Tesseract) ---")
    try:
        opsi_pyocr_tesseract_test = {
            'denoising': None,
            'sharpening': False,
            'contrast': None,
            'binarization': {'method': 'adaptive_gaussian', 'block_size': 11, 'C': 2, 'invert': True}, # Minimal binarization
            'deskew': False,
            'remove_borders': False,
            'crop_final': False,
            'min_ocr_height': 0, # No resize
            'pyocr_lang': 'eng', 
            'tesseract_config': r'--oem 3 --psm 3' # Match Tesseract Direct options
        }
        print(f"Opsi untuk PyOCR (Tesseract) (minimal preprocessing): {opsi_pyocr_tesseract_test}")
        text_pyocr_tess = ekstrak_teks_dari_gambar(TEST_IMAGE_PATH, mesin_ocr='pyocr_tesseract', opsi_praproses=opsi_pyocr_tesseract_test)
        assert_contains_text(text_pyocr_tess, ["Hello", "World", "123"], "PyOCR (Tesseract)")
    except ImportError: # Ditangani di parser_gambar
        print("PyOCR tidak terinstal. Melewati tes PyOCR (Tesseract).")
    except RuntimeError as e: 
        print(f"Runtime error PyOCR (Tesseract): {e}. Melewati tes. (Pastikan Tesseract terinstal dan ada di PATH)")
    except Exception as e:
        print(f"Error selama tes PyOCR (Tesseract): {e}")

    # Test 4: PyOCR dengan Cuneiform
    print("\n--- Tes: PyOCR (Cuneiform) ---")
    try:
        text_pyocr_cunei = ekstrak_teks_dari_gambar(TEST_IMAGE_PATH, mesin_ocr='pyocr_cuneiform')
        assert_contains_text(text_pyocr_cunei, ["Hello"], "PyOCR (Cuneiform)") # Cuneiform mungkin kurang akurat
    except ImportError: # Ditangani di parser_gambar
        print("PyOCR tidak terinstal. Melewati tes PyOCR (Cuneiform).")
    except RuntimeError as e:
        print(f"Runtime error PyOCR (Cuneiform): {e}. Melewati tes. (Pastikan Cuneiform terinstal dan ada di PATH)")
    except Exception as e:
        print(f"Error selama tes PyOCR (Cuneiform): {e}")
        
    # Test 5: Tes berbagai opsi pra-pemrosesan
    print("\n--- Tes: Opsi Pra-pemrosesan ---")
    try:
        opsi_custom1 = {
            'sharpening': True, 
            'contrast': {'alpha': 2.0, 'beta': 5},
            'denoising': {'type': 'median', 'kernel': 3}, # Memastikan tipe denoise ini ada
            'min_ocr_height': 800 # Lebih kecil dari default
        }
        # Add known good tesseract settings for these tests too
        opsi_custom1_full = {**opsi_custom1, 'pyocr_lang': 'eng', 'tesseract_config': r'--oem 3 --psm 3'}
        print(f"Menjalankan dengan opsi custom 1: {opsi_custom1_full}")
        text_custom1 = ekstrak_teks_dari_gambar(TEST_IMAGE_PATH, mesin_ocr='tesseract', opsi_praproses=opsi_custom1_full)
        if isinstance(text_custom1, str):
            print(f"Tes opsi pra-pemrosesan custom 1 SELESAI (output tipe: str). Output: {text_custom1[:100].replace(os.linesep, ' ')}...")
        else:
            print(f"Tes opsi pra-pemrosesan custom 1 GAGAL: output bukan str.")

        opsi_custom2 = {
            'remove_borders': True, # Fitur baru
            'deskew': False, # Non-default
            'binarization': {'method': 'adaptive_gaussian', 'block_size': 51, 'C': 5, 'invert': True} # Parameter beda
        }
        opsi_custom2_full = {**opsi_custom2, 'pyocr_lang': 'eng', 'tesseract_config': r'--oem 3 --psm 3'}
        print(f"Menjalankan dengan opsi custom 2: {opsi_custom2_full}")
        text_custom2 = ekstrak_teks_dari_gambar(TEST_IMAGE_PATH, mesin_ocr='tesseract', opsi_praproses=opsi_custom2_full)
        if isinstance(text_custom2, str):
            print(f"Tes opsi pra-pemrosesan custom 2 SELESAI (output tipe: str). Output: {text_custom2[:100].replace(os.linesep, ' ')}...")
        else:
            print(f"Tes opsi pra-pemrosesan custom 2 GAGAL: output bukan str.")
            
    except Exception as e:
        print(f"Error selama tes opsi pra-pemrosesan: {e}")

def run_pdf_ocr_tests():
    """Menjalankan semua tes OCR untuk PDF."""
    print("\n\n--- Menjalankan Tes OCR PDF ---")
    # from parser_pdf import ekstrak_teks_dari_pdf # Sudah diimpor di atas
    # from parser_gambar import ekstrak_teks_dari_gambar as ocr_image_func_for_pdf # Alias jika perlu
    
    # if not os.path.exists(TEST_PDF_PATH):
    #     print(f"File PDF tes {TEST_PDF_PATH} tidak ditemukan. Melewati tes OCR PDF.")
    #     return
    #
    # print("\n--- Tes: PDF dengan Tesseract Direct ---")
    # try:
    #     text_pdf_tess = ekstrak_teks_dari_pdf(TEST_PDF_PATH, 
    #                                         fungsi_ocr_untuk_gambar=ekstrak_teks_dari_gambar, 
    #                                         mesin_ocr='tesseract')
    #     assert_contains_text(text_pdf_tess, ["Hello", "World", "123"], "PDF (Tesseract)")
    # except Exception as e:
    #     print(f"Error selama tes PDF (Tesseract): {e}")
    #
    # print("\n--- Tes: PDF dengan EasyOCR ---")
    # try:
    #     text_pdf_easy = ekstrak_teks_dari_pdf(TEST_PDF_PATH, 
    #                                         fungsi_ocr_untuk_gambar=ekstrak_teks_dari_gambar, 
    #                                         mesin_ocr='easyocr')
    #     assert_contains_text(text_pdf_easy, ["Hello", "World", "123"], "PDF (EasyOCR)")
    # except ImportError:
    #     print("EasyOCR tidak terinstal. Melewati tes PDF (EasyOCR).")
    # except Exception as e:
    #     print(f"Error selama tes PDF (EasyOCR): {e}")
    print("Tes OCR PDF saat ini adalah placeholder karena pembuatan file PDF tes kompleks.")
    print("Harap uji secara manual atau perluas skrip ini jika file PDF tes tersedia.")


# --- Konfigurasi Lama (disimpan jika masih relevan untuk pengujian lain) ---
KATA_KUNCI_TARGET = [
    {'keyword': 'Pendapatan',
     'variations': ['income', 'total income', 'revenue', 'earnings', 'pendapatan', 'total pendapatan', 'penerimaan']},
    {'keyword': 'Saldo',
     'variations': ['balance', 'net balance', 'account balance', 'total balance', 'saldo', 'saldo bersih', 'saldo akun',
                    'total saldo']},
    {'keyword': 'Pengenal', 'variations': ['id', 'identifier', 'ref_no', 'nomor referensi', 'no ref']}
]

# --- Logika Pemrosesan Utama Lama (disimpan jika masih relevan) ---
def proses_dokumen(path_dokumen):
    print(f"\n--- Memproses (Lama): {path_dokumen} ---")
    teks_hasil_ekstraksi = ""
    ekstensi_file = os.path.splitext(path_dokumen)[1].lower()

    if not os.path.exists(path_dokumen):
        print(f"Berkas tidak ditemukan: {path_dokumen}. Melewati.")
        return

    try:
        if ekstensi_file == '.pdf':
            # Menggunakan mesin_ocr default dan opsi_praproses default dari parser_pdf
            teks_hasil_ekstraksi = ekstrak_teks_dari_pdf(path_dokumen, ekstrak_teks_dari_gambar)
        elif ekstensi_file in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']:
            # Menggunakan mesin_ocr default dan opsi_praproses default dari parser_gambar
            teks_hasil_ekstraksi = ekstrak_teks_dari_gambar(path_dokumen)
        elif ekstensi_file == '.txt':
            teks_hasil_ekstraksi = ekstrak_teks_dari_txt(path_dokumen)
        elif ekstensi_file == '.docx':
            teks_hasil_ekstraksi = ekstrak_teks_dari_docx(path_dokumen)
        else:
            print(f"Tipe berkas tidak didukung: {ekstensi_file}")
            return
    except Exception as e:
        print(f"Error saat parsing {path_dokumen}: {e}")
        teks_hasil_ekstraksi = f"Error: Parsing gagal dengan {type(e).__name__} - {e}"

    if not teks_hasil_ekstraksi.strip() or "Error:" in teks_hasil_ekstraksi:
        print(f"Ekstraksi teks gagal atau menghasilkan teks kosong untuk {path_dokumen}.")
        if "Error:" in teks_hasil_ekstraksi: print(f"Dilaporkan: '{teks_hasil_ekstraksi[:200]}...'")
    else:
        print(f"Berhasil mengekstrak teks (lama) (100 karakter pertama): {teks_hasil_ekstraksi[:100].replace(os.linesep, ' ')}...")

    try:
        kamus_hasil = ekstrak_data_keuangan_tahunan(teks_hasil_ekstraksi, KATA_KUNCI_TARGET)
        json_final = format_ke_json(kamus_hasil)
        print("Hasil Ekstraksi (JSON Lama):")
        print(json_final)
    except Exception as e:
        print(f"Error selama ekstraksi kata kunci atau format JSON (lama) untuk {path_dokumen}: {e}")
        json_error = format_ke_json({"error": f"Error kritis (lama): {str(e)}"})
        print(json_error)

# --- Eksekusi ---
if __name__ == "__main__":
    print("Memulai Tes Integrasi...")

    # 1. Setup file tes untuk OCR baru
    test_files_ready = setup_test_files()

    # 2. Jalankan tes OCR baru jika file siap
    if test_files_ready:
        run_image_ocr_tests()
        run_pdf_ocr_tests() # Akan menampilkan pesan placeholder
    else:
        print("\nTidak dapat menyiapkan file tes OCR. Melewati tes OCR gambar dan PDF.")

    # 3. Bagian NLTK dan pemrosesan dokumen lama (opsional, bisa di-disable jika tidak relevan lagi)
    print("\n\n--- Memeriksa Sumber Daya NLTK (untuk logika lama) ---")
    try:
        import nltk
        # Attempt to download 'punkt' first if initial checks in pengekstrak_kata_kunci failed for it
        # This is a bit redundant if pengekstrak_kata_kunci handles it, but as a fallback.
        try:
            nltk.data.find('tokenizers/punkt')
            print("NLTK 'punkt' resource found.")
        except nltk.downloader.DownloadError: # More specific error
            print("NLTK 'punkt' not found by find. Attempting download...")
            nltk.download('punkt', quiet=True)
        except LookupError: # General lookup error
            print("NLTK 'punkt' not found by find (LookupError). Attempting download...")
            nltk.download('punkt', quiet=True)


        from nltk.tokenize import word_tokenize
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer

        # These should ideally work now if pengekstrak_kata_kunci.py's init worked
        # or if the downloads above succeeded.
        WordNetLemmatizer().lemmatize("kucing")
        _ = stopwords.words('english') # Keep english as a basic check
        _ = word_tokenize("tes tokenisasi")
        print("Sumber daya NLTK tampaknya tersedia dan komponen dapat diinisialisasi dengan benar.")
    except Exception as e:
        print(f"Inisialisasi sumber daya/komponen NLTK gagal: {e}.")
        print("Mencoba mengunduh sumber daya NLTK yang mungkin hilang (jika belum dicoba oleh modul lain)...")
        try:
            # Re-attempt downloads; some might have been done by pengekstrak_kata_kunci
            nltk.download('punkt', quiet=True) 
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('omw-1.4', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True) # Often used with NLTK
            print("Percobaan pengunduhan sumber daya NLTK selesai. Jalankan ulang tes jika masih gagal, atau periksa pengaturan NLTK secara manual.")
        except Exception as unduh_exc:
            print(f"Pengunduhan NLTK gagal: {unduh_exc}. Tes terkait NLTK mungkin gagal.")
        # Tidak keluar, biarkan tes lain berjalan jika memungkinkan

    # 4. Logika pemrosesan dokumen lama
    # Daftar path_dokumen_uji diisi secara manual jika ingin menjalankan bagian ini.
    # Untuk CI/CD, ini bisa diisi dengan path ke file tes yang ada di repositori.
    path_dokumen_uji_lama = [] # Contoh: ["train_documents/astra_lapkeu.pdf"] 
                               # atau biarkan kosong jika tidak ingin menjalankan bagian ini.

    if not path_dokumen_uji_lama:
        print("\nTidak ada path dokumen yang dikonfigurasi untuk 'path_dokumen_uji_lama'.")
        print("Melewati bagian pemrosesan dokumen lama.")
    else:
        print(f"\n--- Memulai Pemrosesan Dokumen Lama untuk {len(path_dokumen_uji_lama)} dokumen ---")
        for path_doc in path_dokumen_uji_lama:
            if path_doc and os.path.exists(path_doc):
                proses_dokumen(path_doc) # Ini adalah fungsi proses_dokumen lama
            elif path_doc:
                print(f"\n--- Melewati (Lama): {path_doc} karena tidak ditemukan. ---")
            else:
                print("\n--- Melewati entri path dokumen (Lama) yang kosong. ---")

    print("\n--- Semua Tes Integrasi Selesai ---")


# --- Tes untuk Google Vision Pipeline (dengan Mock) ---

sample_structured_data_for_vision_test = [
    # Line 1: Jumlah Aset Lancar : 1.234.567
    {'text': 'Jumlah', 'bounds': [10, 10, 60, 22]}, # x_min, y_min, x_max, y_max
    {'text': 'Aset', 'bounds': [65, 10, 105, 22]},
    {'text': 'Lancar', 'bounds': [110, 10, 170, 22]},
    {'text': ':', 'bounds': [175, 10, 180, 22]},
    {'text': '1.234.567', 'bounds': [190, 10, 280, 22]},

    # Line 2: Laba Usaha 789.000 (value slightly further away)
    {'text': 'Laba', 'bounds': [10, 30, 60, 42]},
    {'text': 'Usaha', 'bounds': [65, 30, 125, 42]},
    {'text': '789.000', 'bounds': [200, 30, 290, 42]}, # Note: x_min is 200, keyword ends at 125

    # Line 3: Pendapatan (tanpa nilai numerik jelas di kanan)
    {'text': 'Pendapatan', 'bounds': [10, 50, 100, 62]},
    {'text': 'Lain-lain', 'bounds': [105, 50, 180, 62]},
    {'text': 'signifikan', 'bounds': [190, 50, 280, 62]},

    # Line 4: Ekuitas (Rp Ribu) 555.666
    {'text': 'Ekuitas', 'bounds': [10, 70, 80, 82]},
    {'text': '(Rp', 'bounds': [85, 70, 115, 82]}, 
    {'text': 'Ribu)', 'bounds': [120, 70, 160, 82]}, # Kata "Ribu)" akan diproses oleh normalisasi_nilai_keuangan
    {'text': '555.666', 'bounds': [170, 70, 250, 82]},
    
    # Line 5: Some other text
    {'text': 'Catatan', 'bounds': [10, 90, 70, 102]},
    {'text': 'atas', 'bounds': [75, 90, 115, 102]},
    {'text': 'laporan', 'bounds': [120, 90, 180, 102]},

    # Line 6: Variasi dengan tanda baca "Laba Bersih:" diikuti angka
    {'text': 'Laba', 'bounds': [10, 110, 50, 122]},
    {'text': 'Bersih:', 'bounds': [55, 110, 115, 122]}, # Ada ':' di akhir
    {'text': '987.654', 'bounds': [125, 110, 200, 122]},
]

@patch('parser_gambar.ekstrak_data_terstruktur_vision')
def test_financial_extraction_with_vision_mock(mock_ekstrak_vision):
    print("\n\n--- Menjalankan Tes Ekstraksi Keuangan dengan Mock Google Vision ---")
    
    # Konfigurasi mock untuk mengembalikan data sampel
    mock_ekstrak_vision.return_value = sample_structured_data_for_vision_test
    
    # Panggil fungsi yang sebenarnya melakukan ekstraksi dari parser_gambar (yang di-mock)
    # Ini hanya untuk menunjukkan alur, actual_structured_data akan sama dengan sample_structured_data_for_vision_test
    # Dalam implementasi nyata, Anda mungkin memanggil fungsi tingkat tinggi yang menggunakan ekstrak_data_terstruktur_vision
    # Di sini, kita langsung menggunakan data sampel untuk menguji pengekstrak_kata_kunci.
    # actual_structured_data = ekstrak_data_terstruktur_vision("dummy_image_path.png") 
    # assert actual_structured_data == sample_structured_data_for_vision_test # Verifikasi mock bekerja

    # Panggil fungsi utama yang ingin diuji dengan data sampel (output dari mock)
    hasil_ekstraksi = ekstrak_data_keuangan_dari_struktur_vision(
        sample_structured_data_for_vision_test, 
        DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT
    )

    print(f"Hasil Ekstraksi (Vision Mock): {format_ke_json(hasil_ekstraksi)}")

    # Nilai yang diharapkan (float)
    expected_aset_lancar = normalisasi_nilai_keuangan("1.234.567")
    expected_laba_usaha = normalisasi_nilai_keuangan("789.000")
    # Untuk "Ekuitas", kata kunci "Ekuitas" ditemukan, dan "555.666" adalah nilai.
    # "Ribu)" ada di antara kata kunci dan nilai, normalisasi_nilai_keuangan harusnya bisa handle "555.666 Ribu" jika "Ribu" tergabung.
    # Dalam sample_structured_data, "Ribu)" adalah token terpisah.
    # Pengekstrak kata kunci akan mengambil "555.666" dan normalisasi_nilai_keuangan akan memprosesnya.
    # Jika kita ingin "Ribu" diproses, teks "555.666 Ribu" harus menjadi satu item teks.
    # Atau, logika di pengekstrak_kata_kunci harus lebih canggih untuk menggabungkan unit dari token terpisah.
    # Saat ini, dengan token "555.666", normalisasi akan menghasilkan 555666.0.
    # Jika kita ingin efek "Ribu", sample data atau logika normalisasi/ekstraksi perlu disesuaikan.
    # Mari kita asumsikan untuk tes ini, "Ribu" tidak secara otomatis digabungkan dari token terpisah ke nilai.
    expected_ekuitas = normalisasi_nilai_keuangan("555.666") # Menjadi 555666.0

    # Untuk "Laba Bersih:", kata kunci adalah "Laba Bersih" (dari variasi "margin laba bersih", "laba bersih", dll.)
    # DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT punya {"kata_dasar": "Laba Tahun Berjalan", "variasi": ["laba tahun berjalan", ..., "laba bersih setelah pajak", ...]}
    # Dan juga {"kata_dasar": "Laba", "variasi": ["laba", ..., "laba bersih", ...]}
    # Kata "Laba Bersih:" akan cocok dengan variasi "laba bersih" dari kata_dasar "Laba".
    expected_laba_bersih = normalisasi_nilai_keuangan("987.654")


    assert hasil_ekstraksi.get("Jumlah Aset Lancar") == expected_aset_lancar, \
        f"Error: Jumlah Aset Lancar - Expected {expected_aset_lancar}, Got {hasil_ekstraksi.get('Jumlah Aset Lancar')}"
    print(f"Test 'Jumlah Aset Lancar': Expected {expected_aset_lancar}, Got {hasil_ekstraksi.get('Jumlah Aset Lancar')} -> {'BERHASIL' if hasil_ekstraksi.get('Jumlah Aset Lancar') == expected_aset_lancar else 'GAGAL'}")

    assert hasil_ekstraksi.get("Laba Usaha") == expected_laba_usaha, \
        f"Error: Laba Usaha - Expected {expected_laba_usaha}, Got {hasil_ekstraksi.get('Laba Usaha')}"
    print(f"Test 'Laba Usaha': Expected {expected_laba_usaha}, Got {hasil_ekstraksi.get('Laba Usaha')} -> {'BERHASIL' if hasil_ekstraksi.get('Laba Usaha') == expected_laba_usaha else 'GAGAL'}")

    # Cek Ekuitas
    # Perlu dipastikan kata dasar mana yang diharapkan match "Ekuitas"
    # DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT punya:
    # {"kata_dasar": "Jumlah Ekuitas", "variasi": ["jumlah ekuitas", "total ekuitas", "ekuitas"]},
    # {"kata_dasar": "Ekuitas", "variasi": ["ekuitas", "equity", "shareholders' equity", "modal"]},
    # Keduanya bisa match. Jika "Ekuitas" (dari daftar umum) yang match:
    assert hasil_ekstraksi.get("Ekuitas") == expected_ekuitas, \
        f"Error: Ekuitas - Expected {expected_ekuitas}, Got {hasil_ekstraksi.get('Ekuitas')}"
    print(f"Test 'Ekuitas': Expected {expected_ekuitas}, Got {hasil_ekstraksi.get('Ekuitas')} -> {'BERHASIL' if hasil_ekstraksi.get('Ekuitas') == expected_ekuitas else 'GAGAL'}")
    # Jika "Jumlah Ekuitas" yang match:
    # assert hasil_ekstraksi.get("Jumlah Ekuitas") == expected_ekuitas, \
    #     f"Error: Jumlah Ekuitas - Expected {expected_ekuitas}, Got {hasil_ekstraksi.get('Jumlah Ekuitas')}"
    # print(f"Test 'Jumlah Ekuitas': Expected {expected_ekuitas}, Got {hasil_ekstraksi.get('Jumlah Ekuitas')} -> {'BERHASIL' if hasil_ekstraksi.get('Jumlah Ekuitas') == expected_ekuitas else 'GAGAL'}")


    assert hasil_ekstraksi.get("Pendapatan") is None, \
        f"Error: Pendapatan - Expected None, Got {hasil_ekstraksi.get('Pendapatan')}"
    print(f"Test 'Pendapatan': Expected None, Got {hasil_ekstraksi.get('Pendapatan')} -> {'BERHASIL' if hasil_ekstraksi.get('Pendapatan') is None else 'GAGAL'}")

    # Cek untuk "Laba Bersih:" yang seharusnya match dengan kata_dasar "Laba" karena "laba bersih" adalah variasinya
    assert hasil_ekstraksi.get("Laba") == expected_laba_bersih, \
        f"Error: Laba (dari Laba Bersih:) - Expected {expected_laba_bersih}, Got {hasil_ekstraksi.get('Laba')}"
    print(f"Test 'Laba' (dari variasi Laba Bersih): Expected {expected_laba_bersih}, Got {hasil_ekstraksi.get('Laba')} -> {'BERHASIL' if hasil_ekstraksi.get('Laba') == expected_laba_bersih else 'GAGAL'}")
    
    print("--- Tes Ekstraksi Keuangan dengan Mock Google Vision Selesai ---")
# Panggil tes baru di main execution block

# --- Eksekusi ---
if __name__ == "__main__":
    print("Memulai Tes Integrasi...")

    # 1. Setup file tes untuk OCR baru
    test_files_ready = setup_test_files()

    # 2. Jalankan tes OCR baru jika file siap
    if test_files_ready:
        run_image_ocr_tests()
        run_pdf_ocr_tests() # Akan menampilkan pesan placeholder
    else:
        print("\nTidak dapat menyiapkan file tes OCR. Melewati tes OCR gambar dan PDF.")

    # 2.b Jalankan tes pipeline Vision (mocked)
    test_financial_extraction_with_vision_mock() # Panggil fungsi tes baru di sini

    # 3. Bagian NLTK dan pemrosesan dokumen lama (opsional, bisa di-disable jika tidak relevan lagi)
    print("\n\n--- Memeriksa Sumber Daya NLTK (untuk logika lama) ---")
