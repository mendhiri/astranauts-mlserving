# Impor pustaka standar Python
import os
# Impor shutil, PIL, docx, pymupdf tidak lagi diperlukan karena pembuatan file dummy dihapus

# Impor fungsi dari modul-modul kita yang sudah di-Indonesianisasi
from parser_gambar import ekstrak_teks_dari_gambar
from parser_dokumen_teks import ekstrak_teks_dari_txt, ekstrak_teks_dari_docx
from parser_pdf import ekstrak_teks_dari_pdf
from pengekstrak_kata_kunci import ekstrak_data_keuangan_tahunan, format_ke_json

# --- Konfigurasi ---
# DIREKTORI_FILE_UJI = "dokumen_uji_dummy" # Contoh, tidak digunakan lagi untuk pembuatan
KATA_KUNCI_TARGET = [
    {'keyword': 'Pendapatan',
     'variations': ['income', 'total income', 'revenue', 'earnings', 'pendapatan', 'total pendapatan', 'penerimaan']},
    {'keyword': 'Saldo',
     'variations': ['balance', 'net balance', 'account balance', 'total balance', 'saldo', 'saldo bersih', 'saldo akun',
                    'total saldo']},
    {'keyword': 'Pengenal', 'variations': ['id', 'identifier', 'ref_no', 'nomor referensi', 'no ref']}
]


# Catatan: 'variations' di atas masih dalam Bahasa Inggris untuk KATA_KUNCI_TARGET.
# Ini mungkin perlu disesuaikan jika teks dalam dokumen target juga dalam Bahasa Indonesia
# atau jika model pelumatan (lemmatizer) di pengekstrak_kata_kunci.py mendukung Bahasa Indonesia dengan baik.
# Untuk saat ini, kita asumsikan variasi pencarian bisa jadi campuran atau perlu penyesuaian lebih lanjut.

# --- Logika Pemrosesan Utama ---
def proses_dokumen(path_dokumen):
    # Mencetak informasi tentang dokumen yang sedang diproses
    print(f"\n--- Memproses: {path_dokumen} ---")
    teks_hasil_ekstraksi = ""
    # Mendapatkan ekstensi berkas untuk menentukan metode parsing
    ekstensi_file = os.path.splitext(path_dokumen)[1].lower()

    # Memeriksa apakah berkas ada sebelum diproses
    if not os.path.exists(path_dokumen):
        print(f"Berkas tidak ditemukan: {path_dokumen}. Melewati.")
        return

    try:
        # Memilih fungsi parser berdasarkan ekstensi berkas
        if ekstensi_file == '.pdf':
            # Untuk parser_pdf, ekstrak_teks_dari_gambar adalah fungsi OCR yang dibutuhkan
            teks_hasil_ekstraksi = ekstrak_teks_dari_pdf(path_dokumen, ekstrak_teks_dari_gambar)
        elif ekstensi_file in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']:
            teks_hasil_ekstraksi = ekstrak_teks_dari_gambar(path_dokumen)
        elif ekstensi_file == '.txt':
            teks_hasil_ekstraksi = ekstrak_teks_dari_txt(path_dokumen)
        elif ekstensi_file == '.docx':
            teks_hasil_ekstraksi = ekstrak_teks_dari_docx(path_dokumen)
        else:
            # Jika tipe berkas tidak didukung
            print(f"Tipe berkas tidak didukung: {ekstensi_file}")
            return
    except Exception as e:
        # Menangani kesalahan yang mungkin terjadi selama parsing
        print(f"Error saat parsing {path_dokumen}: {e}")
        # Menyimpan pesan error untuk diproses lebih lanjut jika perlu
        teks_hasil_ekstraksi = f"Error: Parsing gagal dengan {type(e).__name__} - {e}"

    # Memeriksa apakah hasil ekstraksi teks kosong atau mengandung error
    if not teks_hasil_ekstraksi.strip():
        print(f"Ekstraksi teks menghasilkan teks kosong untuk {path_dokumen}.")
    elif "Error:" in teks_hasil_ekstraksi:
        print(f"Ekstraksi teks gagal untuk {path_dokumen}.")
        print(f"Dilaporkan: '{teks_hasil_ekstraksi[:200]}...'")
    else:
        # Mencetak cuplikan teks yang berhasil diekstrak
        print(
            f"Berhasil mengekstrak teks (100 karakter pertama): {teks_hasil_ekstraksi[:100].replace(os.linesep, ' ')}...")

    try:
        # Meneruskan teks_hasil_ekstraksi (yang mungkin berisi pesan error dari parsing)
        # ke fungsi ekstraksi kata kunci.
        kamus_hasil = ekstrak_data_keuangan_tahunan(teks_hasil_ekstraksi, KATA_KUNCI_TARGET)
        json_final = format_ke_json(kamus_hasil)
        print("Hasil Ekstraksi (JSON):")
        print(json_final)
    except Exception as e:
        # Menangani kesalahan selama ekstraksi kata kunci atau format JSON
        print(f"Error selama ekstraksi kata kunci atau format JSON untuk {path_dokumen}: {e}")
        # JSON fallback jika semua gagal
        json_error = format_ke_json({"error": f"Error kritis dalam ekstraksi kata kunci/format JSON: {str(e)}"})
        print(json_error)


# --- Eksekusi ---
if __name__ == "__main__":
    print("Memulai Tes Integrasi (versi Indonesia)...")

    # Memastikan sumber daya NLTK tersedia (karena pengekstrak_kata_kunci bergantung padanya)
    try:
        import nltk
        from nltk.tokenize import word_tokenize
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer

        # Uji inisialisasi atau operasi sederhana
        WordNetLemmatizer().lemmatize("kucing")  # Menggunakan kata dalam Bahasa Indonesia untuk tes pelumat
        _ = stopwords.words('english')  # Kata henti masih menggunakan Bahasa Inggris dari pustaka NLTK
        _ = word_tokenize("tes tokenisasi")
        print("Sumber daya NLTK tampaknya tersedia dan komponen dapat diinisialisasi dengan benar.")

    except Exception as e:
        print(f"Inisialisasi sumber daya/komponen NLTK gagal: {e}.")
        print("Mencoba mengunduh sumber daya NLTK yang mungkin hilang...")
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('omw-1.4', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            print(
                "Percobaan pengunduhan sumber daya NLTK selesai. Jalankan ulang tes jika masih gagal, atau periksa pengaturan NLTK secara manual.")
        except Exception as unduh_exc:
            print(f"Percobaan pengunduhan NLTK gagal: {unduh_exc}")
        exit()  # Keluar jika sumber daya kritis dan tidak ditemukan/diunduh.

    # Logika pembuatan file dummy telah dihapus.
    # Untuk pengujian nyata, daftar path_dokumen_uji di bawah ini perlu diisi
    # dengan path ke berkas-berkas yang ada di sistem.
    # Contoh: path_dokumen_uji = ["/path/ke/dokumen1.pdf", "/path/ke/dokumen2.txt"]
    path_dokumen_uji = []

    if not path_dokumen_uji:
        print("\nTidak ada path dokumen yang dikonfigurasi untuk pengujian dalam 'path_dokumen_uji'.")
        print("Silakan edit skrip ini untuk menambahkan path ke dokumen yang akan diuji.")
    else:
        print(f"\nMenemukan {len(path_dokumen_uji)} dokumen untuk diproses.")
        for path_doc in path_dokumen_uji:
            if path_doc and os.path.exists(path_doc):
                proses_dokumen(path_doc)
            elif path_doc:
                print(f"\n--- Melewati: {path_doc} karena tidak ditemukan. ---")
            else:
                print("\n--- Melewati entri path dokumen yang kosong. ---")

    print("\nTes Integrasi Selesai.")
