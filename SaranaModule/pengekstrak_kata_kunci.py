# Impor pustaka yang diperlukan
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize  # Tambahkan sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re
import json
import unicodedata  # Untuk normalisasi lanjutan jika diperlukan

# Global variables for NLTK resources
pelumat = None
kata_henti = None

def inisialisasi_nltk_resources():
    """Menginisialisasi dan mengunduh sumber daya NLTK yang diperlukan jika belum ada."""
    global pelumat, kata_henti
    
    # 1. Stopwords
    try:
        kata_henti = set(stopwords.words('indonesian'))
        print("Berhasil memuat stopwords Bahasa Indonesia.")
    except LookupError:
        print("Resource 'stopwords' (indonesian) tidak ditemukan. Mencoba mengunduh...")
        try:
            nltk.download('stopwords', quiet=True)
            kata_henti = set(stopwords.words('indonesian'))
            print("Berhasil mengunduh dan memuat stopwords Bahasa Indonesia.")
        except Exception as e_ind: # Fallback to English if Indonesian still fails
            print(f"Gagal memuat stopwords Bahasa Indonesia setelah unduh: {e_ind}. Menggunakan stopwords Bahasa Inggris.")
            try:
                kata_henti = set(stopwords.words('english'))
                print("Berhasil memuat stopwords Bahasa Inggris sebagai fallback.")
            except Exception as e_eng:
                print(f"Gagal memuat stopwords Bahasa Inggris: {e_eng}. Kata henti akan kosong.")
                kata_henti = set() # Empty set as last resort
    except Exception as e_initial_load: # Catch other potential errors during initial load
        print(f"Error tak terduga saat memuat stopwords: {e_initial_load}. Kata henti akan kosong.")
        kata_henti = set()


    # 2. WordNetLemmatizer and its data ('wordnet' and 'omw-1.4')
    try:
        pelumat = WordNetLemmatizer()
        pelumat.lemmatize("test") # Test lemmatization to trigger download if necessary
        print("WordNetLemmatizer berhasil diinisialisasi.")
    except LookupError:
        print("Resource 'wordnet' atau 'omw-1.4' tidak ditemukan untuk WordNetLemmatizer. Mencoba mengunduh...")
        try:
            nltk.download('wordnet', quiet=True)
            nltk.download('omw-1.4', quiet=True) # Needed for lemmatizing in languages other than English
            pelumat = WordNetLemmatizer()
            pelumat.lemmatize("test") # Re-test
            print("Berhasil mengunduh data WordNet dan menginisialisasi WordNetLemmatizer.")
        except Exception as e:
            print(f"Gagal menginisialisasi WordNetLemmatizer setelah unduh: {e}. Pelumat tidak akan berfungsi.")
            # Define a dummy lemmatizer if initialization fails
            class DummyLemmatizer:
                def lemmatize(self, word, pos=None): return word
            pelumat = DummyLemmatizer()
            print("Menggunakan DummyLemmatizer sebagai fallback.")
    except Exception as e_init_lemma:
        print(f"Error tak terduga saat inisialisasi WordNetLemmatizer: {e_init_lemma}. Pelumat tidak akan berfungsi.")
        class DummyLemmatizer:
            def lemmatize(self, word, pos=None): return word
        pelumat = DummyLemmatizer()
        print("Menggunakan DummyLemmatizer sebagai fallback.")

    # 3. Punkt (for word_tokenize)
    try:
        word_tokenize("test sentence")
        print("Tokenizer 'punkt' tampaknya tersedia.")
    except LookupError:
        print("Resource 'punkt' untuk tokenizer tidak ditemukan. Mencoba mengunduh...")
        try:
            nltk.download('punkt', quiet=True)
            word_tokenize("test sentence") # Re-test
            print("Berhasil mengunduh 'punkt'. Tokenizer siap digunakan.")
        except Exception as e:
            print(f"Gagal mengunduh atau menguji 'punkt' setelah unduh: {e}. Tokenisasi mungkin gagal.")
    except Exception as e_init_punkt:
        print(f"Error tak terduga saat memeriksa tokenizer 'punkt': {e_init_punkt}. Tokenisasi mungkin gagal.")


# Panggil fungsi inisialisasi saat modul dimuat
inisialisasi_nltk_resources()

# Definisi daftar kata kunci keuangan dalam Bahasa Indonesia
DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT = [
    # ASET 
    {"kata_dasar": "Jumlah aset lancar", "variasi": ["Jumlah aset lancar", "Total aset lancar", "Aset lancar"]},
    {"kata_dasar": "Jumlah aset tidak lancar", "variasi": ["Jumlah aset tidak lancar", "Total aset tidak lancar", "Aset tidak lancar"]},
    {"kata_dasar": "Jumlah liabilitas jangka pendek", "variasi": ["Jumlah liabilitas jangka pendek", "Total liabilitas jangka pendek", "Liabilitas jangka pendek"]},
    {"kata_dasar": "Jumlah liabilitas jangka panjang", "variasi": ["Jumlah liabilitas jangka panjang", "Total liabilitas jangka panjang", "Liabilitas jangka panjang"]},
    {"kata_dasar": "Jumlah liabilitas", "variasi": ["Jumlah liabilitas", "Total liabilitas", "Liabilitas"]},
    {"kata_dasar": "Jumlah ekuitas", "variasi": ["Jumlah ekuitas", "Total ekuitas", "Ekuitas"]},
    {"kata_dasar": "Jumlah liabilitas dan ekuitas", "variasi": ["Jumlah liabilitas dan ekuitas", "Total liabilitas dan ekuitas", "Liabilitas dan ekuitas"]},
    {"kata_dasar": "Pendapatan bersih", "variasi": ["Pendapatan bersih", "Penjualan bersih", "Total pendapatan", "Total penjualan"]},
    {"kata_dasar": "Beban pokok pendapatan", "variasi": ["Beban pokok pendapatan", "Harga pokok penjualan", "Hpp"]},
    {"kata_dasar": "Laba bruto", "variasi": ["Laba bruto", "Laba kotor", "Gross profit"]},
    {"kata_dasar": "Laba sebelum pajak penghasilan", "variasi": ["Laba sebelum pajak penghasilan", "Laba/(rugi) sebelum pajak penghasilan", "Laba sebelum pajak", "Laba sebelum pajak penghasilan dan beban pajak"]},
    {"kata_dasar": "Beban pajak penghasilan", "variasi": ["Beban pajak penghasilan", "Pajak penghasilan", "Tax expense"]},
    {"kata_dasar": "Laba tahun berjalan", "variasi": ["Laba tahun berjalan", "Laba bersih tahun berjalan", "Laba bersih", "Net income", "Laba periode berjalan"]},
    {"kata_dasar": "Jumlah aset", "variasi": ["Jumlah aset", "Total aset", "Total aktiva"]},
    {"kata_dasar": "Piutang usaha", "variasi": ["Piutang usaha", "Piutang Dagang", "Piutang usaha Pihak Ketiga", "Net Receivables", "Trade Receivables"]},
    # {"kata_dasar": "Aset tetap", "variasi": ["Aset tetap", "Total Aset tetap", "Property, Plant, Equipment, Net", "Aset tetap Bersih"]},
    {"kata_dasar": "Aset tetap bruto", "variasi": ["Aset tetap, setelah dikurangi akumulasi depresiasi sebesar", "Aset tetap, setelah dikurangi"]},
    {"kata_dasar": "Akumulasi penyusutan", "variasi": ["Akumulasi penyusutan", "Accumulated Depreciation"]},
    {"kata_dasar": "Modal kerja bersih", "variasi": ["Modal kerja bersih", "Working Capital", "Modal Kerja"]}, # Dihitung sbg Aset Lancar - Liabilitas Jk Pendek
    {"kata_dasar": "Laba ditahan", "variasi": ["Laba ditahan", "Saldo laba", "Retained earnings", "Saldo laba yang belum ditentukan penggunaannya"]},
    {"kata_dasar": "Beban bunga", "variasi": ["Beban bunga", "Interest expense", "Biaya keuangan", "Biaya bunga", "Beban keuangan"]},
    {"kata_dasar": "Beban penyusutan", "variasi": ["Beban penyusutan", "Beban depresiasi", "Depresiasi dan amortisasi", "Depreciation and amortization expense"]},
    {"kata_dasar": "Beban penjualan", "variasi": ["Beban penjualan", "Selling expenses"]},
    {"kata_dasar": "Beban administrasi dan umum", "variasi": ["Beban administrasi dan umum", "General and administrative expenses", "Beban umum dan administrasi"]},
    {"kata_dasar": "Beban usaha", "variasi": ["Beban usaha", "Beban operasi", "Total beban usaha"]}, # Bisa mencakup SGA + Penyusutan

    # Istilah untuk tahun lalu (digunakan jika Sarana tidak bisa otomatis membedakan t dan t-1)
    # Ini adalah pendekatan sementara dan mungkin tidak ideal.
    {"kata_dasar": "Piutang usaha tahun lalu", "variasi": ["Piutang usaha tahun lalu", "Piutang dagang tahun sebelumnya"]},
    {"kata_dasar": "Pendapatan bersih tahun lalu", "variasi": ["Pendapatan bersih tahun lalu", "Penjualan tahun lalu"]},
    {"kata_dasar": "Laba kotor tahun lalu", "variasi": ["Laba kotor tahun lalu", "Laba bruto tahun lalu"]},
    {"kata_dasar": "Aset tidak lancar selain PPE tahun lalu", "variasi": ["Aset tidak lancar selain PPE tahun lalu"]}, # Perlu dihitung
    {"kata_dasar": "Total aset tahun lalu", "variasi": ["Total aset tahun lalu", "Jumlah aset tahun lalu"]},
    {"kata_dasar": "Beban penyusutan tahun lalu", "variasi": ["Beban penyusutan tahun lalu"]},
    {"kata_dasar": "Aset tetap bruto tahun lalu", "variasi": ["Aset tetap bruto tahun lalu"]},
    {"kata_dasar": "Beban SGA tahun lalu", "variasi": ["Beban SGA tahun lalu", "Beban penjualan, umum, dan administrasi tahun lalu"]},
    {"kata_dasar": "Total liabilitas tahun lalu", "variasi": ["Total liabilitas tahun lalu", "Jumlah liabilitas tahun lalu"]}
]

# Catatan: 'keyword' di kamus target diubah ke 'kata_dasar' agar konsisten dengan nama variabel.
# 'variations' diubah ke 'variasi'.

# Fungsi untuk memformat kamus Python menjadi string JSON
def format_ke_json(kamus_data: dict, indentasi: int = 4) -> str:
    """Memformat kamus Python menjadi string JSON."""
    try:
        return json.dumps(kamus_data, indent=indentasi, ensure_ascii=False)
    except TypeError as e:
        return f"Error memformat ke JSON: {e}. Pastikan semua item dalam kamus dapat diserialisasi JSON."
    except Exception as e:
        return f"Terjadi error tak terduga saat format JSON: {e}"


# Fungsi untuk pra-pemrosesan teks (tokenisasi, lowercase, stopwords, lemmatisasi)
def praproses_teks(teks_mentah: str) -> list[str]:
    """Melakukan tokenisasi, mengubah ke huruf kecil, menghapus kata henti, dan melumatkan teks."""
    if not teks_mentah or pelumat is None or kata_henti is None: # Check if NLTK resources are available
        return []
    try:
        token_kata = word_tokenize(teks_mentah.lower())
    except Exception as e:
        print(f"Gagal melakukan tokenisasi kata: {e}. Pastikan resource 'punkt' NLTK tersedia.")
        return []
        
    # Pelumatan mungkin kurang optimal untuk Bahasa Indonesia dengan WordNetLemmatizer default NLTK.
    # Pertimbangkan stemmer Bahasa Indonesia jika akurasi menjadi masalah.
    token_terproses = []
    for token in token_kata:
        if token.isalnum() and token not in kata_henti:
            try:
                token_terproses.append(pelumat.lemmatize(token))
            except Exception as e_lemma:
                # This might happen if lemmatizer failed init but wasn't replaced by dummy
                print(f"Error saat lemmatisasi token '{token}': {e_lemma}. Menggunakan token asli.")
                token_terproses.append(token) 
    return token_terproses


# Fungsi untuk normalisasi nilai keuangan
def normalisasi_nilai_keuangan(string_nilai: str) -> float | None:
    """
    Mengonversi string angka keuangan (misal "Rp1.234.567,89") ke float.
    Menangani format Indonesia dan tanda kurung untuk negatif.
    Handles various formats of thousand and decimal separators.
    Tidak lagi menangani satuan (ribu, juta, dll.) secara eksplisit di sini,
    tapi pembersihan awal dilakukan.
    """
    if not string_nilai or not isinstance(string_nilai, str):
        return None

    nilai_str_bersih = str(string_nilai).lower() # Ensure it's a string
    # Hapus "rp" dan spasi di awal/akhir
    nilai_str_bersih = nilai_str_bersih.replace("rp", "").strip()

    # Hapus kata-kata satuan umum (sebagai tindakan pencegahan)
    # Ini penting agar tidak mengganggu konversi ke float jika satuan tidak sengaja tertinggal.
    # Loop ini sebaiknya ada, meskipun deteksi_pengali_global juga ada.
    for satuan_kata in ["ribu", "juta", "miliar", "milyar", "triliun", "trilyun"]:
        # Tambahkan spasi sebelum satuan_kata untuk menghindari penggantian dalam kata lain
        # dan pastikan .strip() setelahnya.
        nilai_str_bersih = re.sub(r'\b' + re.escape(satuan_kata) + r'\b', '', nilai_str_bersih).strip()
        
    # Penanganan angka negatif dalam tanda kurung
    negatif = False
    if nilai_str_bersih.startswith("(") and nilai_str_bersih.endswith(")"):
        negatif = True
        nilai_str_bersih = nilai_str_bersih[1:-1].strip()

    # Deteksi pemisah
    num_dots = nilai_str_bersih.count('.')
    num_commas = nilai_str_bersih.count(',')

    # Kasus 1: Ada koma dan titik (misal, "1.234,56" atau "1,234.56")
    if num_dots > 0 and num_commas > 0:
        # Asumsi: jika ada koma dan titik, salah satunya adalah pemisah desimal, yang lain ribuan.
        # Jika koma terakhir: format Indonesia "1.234,56"
        if nilai_str_bersih.rfind(',') > nilai_str_bersih.rfind('.'):
            nilai_str_bersih = nilai_str_bersih.replace(".", "")  # Hapus titik (ribuan)
            nilai_str_bersih = nilai_str_bersih.replace(",", ".")  # Koma jadi desimal
        # Jika titik terakhir: format US/UK "1,234.56"
        else:
            nilai_str_bersih = nilai_str_bersih.replace(",", "")  # Hapus koma (ribuan)
            # Titik sudah menjadi pemisah desimal
    # Kasus 2: Hanya ada koma (misal, "1,234" atau "1,234,567")
    elif num_commas > 0 and num_dots == 0:
        # Jika lebih dari satu koma, atau satu koma tapi diikuti >3 digit setelahnya (heuristic),
        # anggap koma sebagai pemisah ribuan. Contoh "1,234" atau "1,234,567".
        # Untuk "19,238" (kasus dari issue), ini akan menghapus koma.
        # Untuk "19,2" (sembilan belas koma dua), ini juga akan menghapus koma jika tidak hati-hati.
        # Perlu diperbaiki: jika ada satu koma dan setelah koma ada <= 3 digit yang bukan semua nol,
        # itu bisa jadi desimal.
        # Contoh: "19,238" -> 19238. "19,2" -> 19.2. "19,000" -> 19000
        
        parts = nilai_str_bersih.split(',')
        if len(parts) > 1: # Ada koma
            # Jika bagian terakhir setelah koma adalah 3 digit DAN ada lebih dari satu koma (e.g., 1,234,567)
            # ATAU jika bagian terakhir BUKAN 3 digit (e.g. 1,2 or 1,23 or 1,2345)
            # ini menunjukkan koma bisa jadi desimal atau ribuan.
            # Aturan sederhana: jika ada koma, dan bagian setelah koma terakhir BUKAN persis 3 digit,
            # maka koma itu adalah desimal.
            # Jika bagian setelah koma terakhir ADALAH 3 digit, dan ada koma lain sebelumnya, itu ribuan.
            # Jika hanya satu koma dan diikuti 3 digit, ini ambigu. "19,238". Sesuai issue, ini ribuan.
            
            # Strategi baru untuk Kasus 2 (hanya koma):
            # Jika ada lebih dari satu koma, semua adalah pemisah ribuan.
            if num_commas > 1:
                nilai_str_bersih = nilai_str_bersih.replace(",", "")
            else: # Hanya satu koma
                # Periksa jumlah digit setelah koma.
                # Jika "12,345" (kasus issue), ini adalah ribuan.
                # Jika "12,3" atau "12,34", ini adalah desimal.
                # Jika "12,3456", ini desimal (non-standar, tapi float() akan handle).
                last_segment = parts[-1]
                # Jika segmen terakhir BUKAN 3 digit, maka koma adalah desimal.
                # Atau jika segmen terakhir adalah 3 digit tapi tidak ada segmen lain sebelumnya (misal ",123" tidak valid)
                if len(last_segment) != 3 or len(parts) == 1: # e.g. "12,3" or "12,34" or "12,3456"
                    nilai_str_bersih = nilai_str_bersih.replace(",", ".")
                else: # e.g. "12,345" or "123,456" (jika num_commas > 1 sudah ditangani)
                      # Ini berarti satu koma diikuti 3 digit -> ribuan. "19,238"
                    nilai_str_bersih = nilai_str_bersih.replace(",", "")
        # else: tidak ada koma, tidak perlu apa-apa
            
    # Kasus 3: Hanya ada titik (misal, "1.234" atau "1.234.567" atau "123.45")
    elif num_dots > 0 and num_commas == 0:
        # Jika lebih dari satu titik, semua adalah pemisah ribuan.
        if num_dots > 1:
            nilai_str_bersih = nilai_str_bersih.replace(".", "")
        # Jika hanya satu titik, itu adalah pemisah desimal (misal, "123.45"). Tidak perlu diubah.
        # "1234" (tanpa titik) juga tidak perlu diubah.
        # "1.234" (satu titik, diikuti 3 digit). Ini adalah ribuan menurut konvensi umum Eropa.
        # Namun, float("1.234") di Python adalah 1.234.
        # Agar konsisten dengan "19,238" (ribuan), maka "1.234" juga harus jadi 1234.
        parts = nilai_str_bersih.split('.')
        if num_dots == 1 and len(parts[-1]) == 3 and len(parts[0]) > 0 : # e.g. "1.234", "12.345"
             # Cek apakah bagian pertama bukan kosong, misal ".234" bukan ribuan
            is_thousand_separator_candidate = True
            # Heuristik tambahan: jika setelah titik ada non-digit, mungkin ini bukan ribuan "version1.222"
            if not parts[-1].isdigit() or not parts[0].isdigit(): # memastikan kedua sisi adalah angka
                 is_thousand_separator_candidate = False

            if is_thousand_separator_candidate:
                nilai_str_bersih = nilai_str_bersih.replace(".", "") # Anggap ribuan
            # else: biarkan sebagai desimal, contoh "123.4" atau "file.ext" (akan gagal nanti)
        # Jika num_dots > 1, sudah dihapus. Jika num_dots == 1 dan bukan format ribuan X.YYY, biarkan.

    # Setelah normalisasi separator, bersihkan karakter non-numerik yang mungkin masih tersisa
    # (selain titik desimal dan tanda minus di awal).
    # Regex ini mengizinkan angka, satu titik desimal opsional, dan satu tanda minus opsional di awal.
    # Pertama, simpan tanda minus jika ada di awal
    awal_minus = False
    if nilai_str_bersih.startswith('-'):
        awal_minus = True
        nilai_str_bersih = nilai_str_bersih[1:]

    # Hapus semua karakter yang bukan digit atau titik desimal tunggal
    nilai_str_bersih = re.sub(r"[^\d.]", "", nilai_str_bersih)
    
    # Jika ada lebih dari satu titik setelah pembersihan di atas, itu error, float() akan gagal.
    # Contoh: jika input "1.2.3.abc" -> "1.2.3" -> float() gagal.
    # Jika input "abc.def" -> "." -> float() gagal.

    if awal_minus:
        nilai_str_bersih = "-" + nilai_str_bersih

    if not nilai_str_bersih or nilai_str_bersih == "-": # Jika string menjadi kosong atau hanya "-"
        return None

    try:
        nilai_float = float(nilai_str_bersih)
        return -nilai_float if negatif and nilai_float >= 0 else nilai_float
    except ValueError:
        # print(f"DEBUG: Gagal konversi ke float: '{string_nilai}' -> '{original_cleaned_string_for_debug}' -> '{nilai_str_bersih}'")
        return None


# Fungsi untuk mengidentifikasi tahun pelaporan dari teks
def identifikasi_tahun_pelaporan(teks_dokumen: str, jumlah_karakter_awal: int = 7000) -> str | None:
    """
    Mengidentifikasi tahun pelaporan 4 digit (misal 2000-2099) dari bagian awal teks dokumen.
    Memprioritaskan tahun yang paling baru jika beberapa ditemukan dalam konteks yang relevan.
    """
    if not teks_dokumen:
        return None

    teks_pencarian = teks_dokumen[:jumlah_karakter_awal].lower()

    # Pola regex untuk mencari tahun 4 digit (misalnya 2000-2099)
    pola_tahun_kontekstual = re.compile(
        r"(?:laporan\s*(?:konsolidasi\s*)?(?:posisi\s*)?(?:keuangan\s*)?(?:tahunan\s*)?(?:konsolidasian\s*)?(?:interim\s*)?untuk\s+tahun\s+yang\s+berakhir\s+(?:pada\s+tanggal\s+|pada\s+)?(?:31\s+desember\s+)?([12][0-9]{3}))"
        r"|(?:periode\s+(?:tiga\s+bulan\s+|enam\s+bulan\s+|sembilan\s+bulan\s+|dua\s+belas\s+bulan\s+)?(?:yang\s+berakhir\s+)?(?:pada\s+tanggal\s+|pada\s+)?(?:31\s+desember\s+|31\s+maret\s+|30\s+juni\s+|30\s+september\s+)?([12][0-9]{3}))"
        r"|(?:tahun\s+buku\s+([12][0-9]{3}))"
        r"|(?:per\s+(?:tanggal\s+)?(?:31\s+desember\s+|31\s+maret\s+|30\s+juni\s+|30\s+september\s+)?([12][0-9]{3}))"
        # Ganti look-behind variable-width dengan non-capturing group
        r"|(?:^|[^RpUSD\d.,])\b([12][0-9]{3})\b(?![\d.,%])"
    )

    kandidat_tahun = []
    for match in pola_tahun_kontekstual.finditer(teks_pencarian):
        for group in match.groups():
            if group:
                try:
                    tahun_int = int(group)
                    if 2000 <= tahun_int <= 2099:
                        kandidat_tahun.append(tahun_int)
                except ValueError:
                    continue

    if not kandidat_tahun:
        pola_tahun_umum = re.compile(r"\b([22][0-9]{3})\b")
        for match_umum in pola_tahun_umum.finditer(teks_pencarian):
            try:
                tahun_int = int(match_umum.group(1))
                if 2000 <= tahun_int <= 2099:
                    kandidat_tahun.append(tahun_int)
            except ValueError:
                continue

    if kandidat_tahun:
        return str(max(kandidat_tahun))

    return None


def deteksi_pengali_global(teks_dokumen: str) -> float:
    """
    Mendeteksi pengali global (misalnya ribuan, jutaan) dari bagian awal dokumen.
    Biasanya dinyatakan sebagai "(Dinyatakan dalam ribuan Rupiah)".

    Args:
        teks_dokumen: String isi dokumen.

    Returns:
        Float pengali yang terdeteksi (misalnya 1000.0 untuk ribuan) atau 1.0 jika tidak ada.
    """
    if not teks_dokumen or not isinstance(teks_dokumen, str):
        return 1.0

    # Kamus pengali
    pengali_map = {
        'ribu': 1000.0,
        'juta': 1_000_000.0,
        'miliar': 1_000_000_000.0,
        'triliun': 1_000_000_000_000.0
    }

    # Pola regex untuk mencari deklarasi pengali.
    # - (?i) untuk case-insensitive.
    # - \s* menangani spasi opsional.
    # - (?:dalam\s+)?opsional "dalam".
    # - (ribu|juta|miliar|triliun) menangkap unit pengali.
    # - \s*(?:mata\s+uang\s+)?Rupiah opsional "mata uang Rupiah" atau hanya "Rupiah".
    # - \)? opsional kurung tutup.
    pola_pengali = re.compile(
        r"(?i)\(?(?:Dinyatakan\s+(?:dalam\s+)?|Dalam\s+|Disajikan\s+dalam\s+)(ribu|juta|miliar|triliun)\s*(?:mata\s+uang\s+)?(?:Rupiah|Rp)?\)?",
        re.IGNORECASE
    )

    # Cari hanya di bagian awal dokumen (misalnya 1000 karakter pertama)
    teks_pencarian = teks_dokumen[:1000]

    match = pola_pengali.search(teks_pencarian)

    if match:
        unit_terdeteksi = match.group(1).lower() # Ambil grup pertama (unit) dan ubah ke lowercase
        return pengali_map.get(unit_terdeteksi, 1.0) # Kembalikan nilai dari map, default 1.0

    return 1.0 # Default jika tidak ditemukan


def is_potentially_numeric(text: str) -> bool:
    """
    Checks if the string contains at least one digit and possibly typical numeric characters.
    This is a heuristic. normalisasi_nilai_keuangan does the thorough check.
    """
    if not isinstance(text, str):
        return False
    # Allows for digits, dots, commas, parentheses (for negative), and currency symbols/units briefly
    # Checks for at least one digit, and not two or more letters (e.g. "Rp", "USD" are ok, but "Table" is not)
    if not re.search(r'\d', text): # Must contain at least one digit
        return False
    if re.search(r'[a-zA-Z]{3,}', text): # Contains three or more consecutive letters, likely not a number
        return False
    # Allows things like (1.234,56) or 1.234.567 or 1,234.56 or USD100 or 100EUR etc.
    # Further check for patterns that are clearly not numbers like "A1" "B2" if needed,
    # but normalisasi_nilai_keuangan should handle most non-numeric cases.
    return True


def ekstrak_data_keuangan_dari_struktur_vision(
    structured_ocr_data: list[dict], 
    daftar_kata_kunci: list[dict] | None = None
) -> dict:
    """
    Mengekstrak data keuangan dari output terstruktur Google Vision API.
    Diasumsikan data yang masuk sudah difilter untuk halaman "Entitas Induk".

    Args:
        structured_ocr_data: List dict {'text': 'word', 'bounds': [x_min, y_min, x_max, y_max]}.
        daftar_kata_kunci: Daftar kata kunci untuk diekstrak. Menggunakan default jika None.

    Returns:
        Dict berisi data keuangan yang diekstrak {kata_dasar: nilai}.
    """
    if daftar_kata_kunci is None:
        daftar_kata_kunci = DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT
    
    data_hasil_ekstraksi = {}
    if not structured_ocr_data: # Jika tidak ada data terstruktur, kembalikan hasil kosong
        print("INFO: Tidak ada data OCR terstruktur yang diberikan ke ekstraktor.")
        return data_hasil_ekstraksi

    # Parameter untuk pencarian spasial
    MAX_HORIZONTAL_DISTANCE_FACTOR = 5  # Faktor pengali lebar kata kunci untuk jarak horizontal maksimal
    VERTICAL_ALIGNMENT_TOLERANCE_FACTOR = 0.7 # Faktor pengali tinggi kata kunci untuk toleransi alignment vertikal

    for info_kata_kunci in daftar_kata_kunci:
        kata_dasar_target = info_kata_kunci["kata_dasar"]
        nilai_ditemukan_final = None
        nilai_ditemukan_final_kedekatan = float('inf') # Untuk mencari nilai terdekat

        for variasi in info_kata_kunci["variasi"]:
            variasi_lower = variasi.lower()
            kata_variasi = variasi_lower.split()
            jumlah_kata_variasi = len(kata_variasi)

            for i in range(len(structured_ocr_data) - jumlah_kata_variasi + 1):
                # Coba match variasi (bisa multi-kata)
                match_ditemukan = True
                teks_tergabung_variasi = []
                for k in range(jumlah_kata_variasi):
                    struktur_item_variasi = structured_ocr_data[i+k]
                    teks_tergabung_variasi.append(struktur_item_variasi['text'].lower())
                    # Periksa apakah kata dalam variasi cocok, hilangkan tanda baca di akhir kata untuk perbandingan
                    # Ini penting karena OCR mungkin menangkap "pendapatan," atau "aset:"
                    kata_ocr_cleaned = re.sub(r'[^\w\s]', '', struktur_item_variasi['text'].lower())
                    kata_variasi_cleaned = re.sub(r'[^\w\s]', '', kata_variasi[k])
                    
                    if kata_ocr_cleaned != kata_variasi_cleaned:
                        match_ditemukan = False
                        break
                
                if match_ditemukan:
                    # Variasi ditemukan, dapatkan BBox dari kata terakhir variasi
                    keyword_bounds_first_word = structured_ocr_data[i]['bounds']
                    keyword_bounds_last_word = structured_ocr_data[i + jumlah_kata_variasi - 1]['bounds']
                    
                    y_min_keyword = keyword_bounds_last_word[1]
                    y_max_keyword = keyword_bounds_last_word[3]
                    x_max_keyword = keyword_bounds_last_word[2]
                    
                    keyword_height = y_max_keyword - y_min_keyword
                    keyword_width = x_max_keyword - keyword_bounds_first_word[0] # Lebar keseluruhan variasi

                    # Cari nilai numerik di sebelah kanan pada baris yang sama (kurang lebih)
                    for j, struktur_item_value in enumerate(structured_ocr_data):
                        # Hindari memproses kata kunci itu sendiri sebagai nilai
                        if i <= j < i + jumlah_kata_variasi:
                            continue

                        # NEW: Skip if text is empty or only whitespace
                        if not struktur_item_value['text'].strip():
                            continue

                        if not is_potentially_numeric(struktur_item_value['text']):
                            continue

                        value_bounds = struktur_item_value['bounds']
                        y_min_value = value_bounds[1]
                        y_max_value = value_bounds[3]
                        x_min_value = value_bounds[0]
                        
                        # 1. Cek Alignment Vertikal (kurang lebih pada baris yang sama)
                        # Pusat vertikal kata kunci dan nilai harus cukup dekat
                        center_y_keyword = (y_min_keyword + y_max_keyword) / 2
                        center_y_value = (y_min_value + y_max_value) / 2
                        vertical_distance_centers = abs(center_y_keyword - center_y_value)
                        
                        # Toleransi berdasarkan tinggi kata kunci
                        # Jika jarak vertikal antar pusat < toleransi tinggi kata kunci, anggap sejajar
                        is_vertically_aligned = vertical_distance_centers < (keyword_height * VERTICAL_ALIGNMENT_TOLERANCE_FACTOR)

                        # 2. Cek Posisi Horizontal (nilai di sebelah kanan kata kunci)
                        is_to_the_right = x_min_value > x_max_keyword

                        # 3. Cek Kedekatan Horizontal
                        horizontal_distance = x_min_value - x_max_keyword
                        # Jarak horizontal maksimal yang diizinkan, berdasarkan lebar kata kunci
                        # Ini membantu menghindari pengambilan angka yang terlalu jauh
                        max_allowed_horizontal_distance = keyword_width * MAX_HORIZONTAL_DISTANCE_FACTOR
                        
                        is_horizontally_close = 0 < horizontal_distance < max_allowed_horizontal_distance

                        if is_vertically_aligned and is_to_the_right and is_horizontally_close:
                            nilai_ternormalisasi = normalisasi_nilai_keuangan(struktur_item_value['text'])
                            if nilai_ternormalisasi is not None:
                                # Jika ini nilai valid pertama, atau lebih dekat dari yang sebelumnya
                                if horizontal_distance < nilai_ditemukan_final_kedekatan:
                                    nilai_ditemukan_final = nilai_ternormalisasi
                                    nilai_ditemukan_final_kedekatan = horizontal_distance
                                    # print(f"Kandidat untuk '{variasi}': {struktur_item_value['text']} -> {nilai_ternormalisasi} (Jarak: {horizontal_distance:.2f})")


        if nilai_ditemukan_final is not None:
             # Jika sudah ada nilai untuk kata dasar ini dari variasi lain, jangan timpa kecuali ada logika prioritas
             # Untuk saat ini, kita ambil yang terakhir ditemukan jika ada beberapa variasi yang cocok.
             # Seharusnya, kita bisa memilih berdasarkan keyakinan atau variasi mana yang lebih spesifik.
            data_hasil_ekstraksi[kata_dasar_target] = nilai_ditemukan_final
            # Reset kedekatan untuk kata dasar berikutnya
            nilai_ditemukan_final_kedekatan = float('inf') 

    return data_hasil_ekstraksi


# Fungsi helper untuk memeriksa apakah kata kunci lain ada di baris teks
def is_another_keyword_present(line_text: str, current_kata_dasar: str, daftar_kata_kunci: list[dict]) -> bool:
    """
    Memeriksa apakah ada kata kunci (dari daftar_kata_kunci) yang BUKAN current_kata_dasar
    terdapat dalam line_text.
    """
    for kw_info in daftar_kata_kunci:
        if kw_info["kata_dasar"] == current_kata_dasar:
            continue  # Lewati kata kunci saat ini
        for v in kw_info["variasi"]:
            if v.lower() in line_text.lower():
                return True
    return False


def ekstrak_data_keuangan_dari_teks_ocr_refined(
    ocr_text: str, 
    daftar_kata_kunci: list[dict] | None = None
) -> dict:
    """
    Mengekstrak data keuangan dari teks OCR mentah dengan logika pencarian yang lebih canggih.
    Mencari nilai pada baris yang sama dengan kata kunci, atau pada baris-baris berikutnya,
    dengan memperhatikan kemungkinan adanya kata kunci lain.

    Args:
        ocr_text: String teks hasil OCR.
        daftar_kata_kunci: Daftar kata kunci untuk diekstrak. 
                           Menggunakan DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT jika None.

    Returns:
        Dict berisi data keuangan yang diekstrak {kata_dasar: nilai}.
    """
    if daftar_kata_kunci is None:
        daftar_kata_kunci = DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT
    
    extracted_data = {}
    if not ocr_text or not isinstance(ocr_text, str):
        return extracted_data

    # Normalisasi teks OCR
    ocr_text = ocr_text.replace("\n", " ")
    ocr_text = re.sub(r"\s+", " ", ocr_text).strip() # Tambahkan strip() untuk menghapus spasi di awal/akhir

    lines = [line.lower() for line in ocr_text.splitlines() if line.strip()] # Pastikan tidak ada baris kosong setelah split
    MAX_LINES_TO_SEARCH_AFTER_KEYWORD = 5 # Batas pencarian ke bawah setelah kata kunci

    for info_kata_kunci in daftar_kata_kunci:
        kata_dasar_target = info_kata_kunci["kata_dasar"]
        variasi_list = info_kata_kunci["variasi"]
        list_of_values_found = [] # Initialize for each new keyword

        for variasi in variasi_list:
            if len(list_of_values_found) >= 2:
                break # Found two values from a previous variation of the same base keyword
            
            variasi_lower = variasi.lower()
            
            for line_index, line_content in enumerate(lines):
                if len(list_of_values_found) >= 2:
                    break # Already found two values for this kata_dasar_target

                if variasi_lower in line_content:
                    is_best_match_for_spot = True
                    for other_info_kata_kunci in daftar_kata_kunci:
                        for other_variasi in other_info_kata_kunci["variasi"]:
                            other_variasi_lower = other_variasi.lower()
                            if variasi_lower != other_variasi_lower and \
                               variasi_lower in other_variasi_lower and \
                               other_variasi_lower in line_content:
                                is_best_match_for_spot = False
                                break
                        if not is_best_match_for_spot:
                            break
                    
                    if not is_best_match_for_spot:
                        continue

                    # 1. Search on the same line
                    try:
                        start_index_after_variasi = line_content.find(variasi_lower) + len(variasi_lower)
                        substring_kanan = line_content[start_index_after_variasi:]
                        tokens_kanan = substring_kanan.split()
                        
                        for token in tokens_kanan:
                            if len(list_of_values_found) >= 2:
                                break
                            nilai_normal = normalisasi_nilai_keuangan(token)
                            if nilai_normal is not None:
                                list_of_values_found.append(nilai_normal)
                        
                        # No need to break here from the line_index loop, 
                        # as we might find more values on subsequent lines for the same keyword instance
                        # if we haven't found two yet.

                    except Exception:
                        pass # Continue if any error in processing this part of the line

                    # 2. Search on subsequent lines (if len(list_of_values_found) < 2)
                    if len(list_of_values_found) < 2:
                        for i in range(1, MAX_LINES_TO_SEARCH_AFTER_KEYWORD + 1):
                            if len(list_of_values_found) >= 2:
                                break 
                            
                            next_line_index = line_index + i
                            if next_line_index < len(lines):
                                current_search_line = lines[next_line_index].strip()
                                
                                if not current_search_line: # Skip empty lines
                                    continue
                                
                                if is_another_keyword_present(current_search_line, kata_dasar_target, daftar_kata_kunci):
                                    break # Stop downward search for this keyword instance

                                tokens_search_line = current_search_line.split()
                                for token in tokens_search_line:
                                    if len(list_of_values_found) >= 2:
                                        break
                                    nilai_normal = normalisasi_nilai_keuangan(token)
                                    if nilai_normal is not None:
                                        list_of_values_found.append(nilai_normal)
                                
                                if len(list_of_values_found) >= 2: # Break from searching more lines
                                    break 
                            else:
                                break # End of document lines
                
                if len(list_of_values_found) >= 2:
                     break # Break from iterating lines for current variasi if 2 values found

            if len(list_of_values_found) >= 2:
                break # Break from iterating variasi_list if 2 values found for kata_dasar_target
        
        # After iterating through variations and lines for a kata_dasar_target:
        if list_of_values_found:
            val1 = list_of_values_found[0]
            val2 = list_of_values_found[1] if len(list_of_values_found) > 1 else None
            extracted_data[kata_dasar_target] = {'val1': val1, 'val2': val2}

    return extracted_data


def ekstrak_data_keuangan_tahunan(
    teks_dokumen: str, 
    daftar_kata_kunci: list[dict] | None = None, 
    pengali_global: float = 1.0
) -> dict:
    if daftar_kata_kunci is None:
        daftar_kata_kunci = DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT
    
    # Initialize all kata_dasar from daftar_kata_kunci to store dict {'t': None, 't-1': None}
    data_hasil_ekstraksi = {
        info["kata_dasar"]: {'t': None, 't-1': None} 
        for info in daftar_kata_kunci
    }
    
    if not teks_dokumen or not isinstance(teks_dokumen, str):
        return data_hasil_ekstraksi

    # Langkah 1: Pra-pemrosesan teks_dokumen untuk menggabungkan baris yang terpisah secara tidak wajar.
    # Heuristik: Jika sebuah baris diakhiri dengan \n dan baris berikutnya dimulai dengan huruf kecil,
    # atau jika baris berikutnya dimulai dengan spasi diikuti huruf kecil (menandakan kelanjutan yang indent),
    # maka \n tersebut kemungkinan adalah pemisah karena layout, bukan akhir kalimat.
    # Kita juga ingin mempertahankan \n yang diikuti oleh angka (misalnya, daftar bernomor atau nilai di baris baru).
    # Atau \n yang diikuti oleh huruf besar (awal kalimat baru atau item baru).
    
    # Langkah 1: Pra-pemrosesan teks_dokumen - Mengubah semua newline menjadi spasi dan menormalkan spasi.
    processed_text = teks_dokumen.replace("\n", " ")
    processed_text = re.sub(r"\s+", " ", processed_text).strip().lower()
    
    MAX_VALUES_TO_CAPTURE = 2
    MAX_TOKENS_AFTER_KEYWORD_TO_SEARCH = 25 # Tingkatkan sedikit jarak pencarian token

    for info_kata_kunci in daftar_kata_kunci:
        kata_dasar_target = info_kata_kunci["kata_dasar"]
        ditemukan_nilai_untuk_kata_dasar_ini = False

        for variasi in info_kata_kunci["variasi"]:
            if ditemukan_nilai_untuk_kata_dasar_ini:
                break

            variasi_lower = variasi.lower()
            current_search_pos = 0

            # Kasus khusus untuk "Arus kas bersih yang diperoleh dari aktivitas investasi"
            if kata_dasar_target == "Arus kas bersih yang diperoleh dari aktivitas investasi" and \
               variasi_lower == "arus kas bersih yang diperoleh dari aktivitas investasi":
                
                # Pola regex: "frasa_awal" diikuti oleh teks apapun (non-greedy), lalu dua angka, 
                # lalu teks apapun lagi, lalu "frasa_akhir"
                # Grup 1 & 2 akan menangkap angka-angkanya.
                # Kita buat lebih fleksibel untuk menangkap angka di antara frasa awal dan akhir.
                # Frasa awal: "arus kas bersih yang diperoleh dari"
                # Frasa akhir: "aktivitas investasi"
                # Teks di antaranya bisa: ANGKA1 ANGKA2 "net cash flows provided from"
                
                # Pola untuk menangkap blok teks antara "dari" dan "aktivitas investasi"
                # dan kemudian mengekstrak angka dari blok tersebut.
                # Kita mencari angka *setelah* "dari" dan *sebelum* "aktivitas investasi" jika terpisah.
                
                # Pola 1: Mencari "arus kas bersih yang diperoleh dari [ANGKA1] [ANGKA2] ... aktivitas investasi"
                # Ini akan menangkap angka yang berada di antara frasa awal dan akhir yang dipisahkan oleh teks lain.
                # re.escape melindungi dari karakter khusus regex dalam frasa.
                # ([\s\S]*?) menangkap semua karakter termasuk newline (jika ada sisa) secara non-greedy.
                # ((?:\(?\s*[\d.,]+\s*\)?\s*){1,2}) akan mencoba menangkap satu atau dua angka.
                
                # Pola yang lebih sederhana: cari frasa awal, lalu cari frasa akhir setelahnya.
                # Kemudian ekstrak angka dari teks DI ANTARA match frasa awal dan match frasa akhir.
                
                part1 = "arus kas bersih yang diperoleh dari"
                part2 = "aktivitas investasi"
                
                # Cari posisi akhir dari part1
                idx1_end = -1
                search_regex_start = 0
                match1 = None
                
                # Loop untuk menemukan semua kemunculan part1, karena bisa jadi ada beberapa.
                while True:
                    temp_match1 = re.search(re.escape(part1), processed_text[search_regex_start:])
                    if not temp_match1:
                        break # Tidak ada lagi part1
                    
                    # match1_start_global = search_regex_start + temp_match1.start() # Tidak digunakan saat ini
                    idx1_end_global = search_regex_start + temp_match1.end()

                    # Cari part2 setelah idx1_end_global
                    # Batasi pencarian part2 dalam jarak tertentu dari part1, misal 150 karakter
                    search_window_for_part2 = processed_text[idx1_end_global : min(len(processed_text), idx1_end_global + 150)]
                    match2 = re.search(re.escape(part2), search_window_for_part2)

                    if match2:
                        # Kedua bagian ditemukan
                        text_between_parts = search_window_for_part2[:match2.start()]
                        
                        # Periksa apakah ini pasangan yang salah (misalnya, part1 dari operasi, part2 dari investasi)
                        if "aktivitas operasi" in text_between_parts and kata_dasar_target == "Arus kas bersih yang diperoleh dari aktivitas investasi":
                            search_regex_start = idx1_end_global # Lanjutkan pencarian part1 berikutnya
                            continue # Coba pasangan part1/part2 berikutnya
                        
                        # Ekstrak angka dari text_between_parts
                        potential_values = re.findall(r"\(?\s*([\d.,]+)\s*\)?", text_between_parts)
                        
                        values_found_for_this_instance = []
                        for val_str in potential_values:
                            norm_val = normalisasi_nilai_keuangan(val_str)
                            if norm_val is not None:
                                values_found_for_this_instance.append(norm_val * pengali_global)
                                if len(values_found_for_this_instance) >= MAX_VALUES_TO_CAPTURE:
                                    break
                        
                        if values_found_for_this_instance:
                            # Pastikan kita tidak mengambil nilai yang terlalu sedikit jika ada banyak angka sampah
                            # Hanya ambil jika setidaknya satu nilai valid ditemukan dan kita belum menemukan untuk kata dasar ini.
                            # Atau jika kita menemukan lebih banyak/lebih baik. Untuk sekarang, ambil yang pertama.
                            data_hasil_ekstraksi[kata_dasar_target]['t'] = values_found_for_this_instance[0]
                            if len(values_found_for_this_instance) > 1:
                                data_hasil_ekstraksi[kata_dasar_target]['t-1'] = values_found_for_this_instance[1]
                            else:
                                data_hasil_ekstraksi[kata_dasar_target]['t-1'] = None
                            ditemukan_nilai_untuk_kata_dasar_ini = True
                            break # Keluar dari loop while True (pencarian part1)
                    
                    search_regex_start = idx1_end_global # Lanjutkan pencarian part1 setelah match saat ini
                
                if ditemukan_nilai_untuk_kata_dasar_ini:
                    break # Keluar dari loop variasi
                else:
                    continue # Lanjut ke variasi berikutnya jika regex khusus ini tidak berhasil

            # Logika pencarian standar (jika bukan kasus khusus atau kasus khusus gagal)
            while current_search_pos < len(processed_text):
                keyword_pos = processed_text.find(variasi_lower, current_search_pos)
                if keyword_pos == -1:
                    break # Tidak ada lagi kemunculan variasi ini

                values_found_for_this_instance = []
                text_after_keyword = processed_text[keyword_pos + len(variasi_lower):]
                potential_value_tokens = re.split(r'\s+', text_after_keyword.strip())
                
                tokens_checked = 0
                for token_idx, token in enumerate(potential_value_tokens):
                    if not token or tokens_checked >= MAX_TOKENS_AFTER_KEYWORD_TO_SEARCH:
                        break
                    tokens_checked += 1

                    normalized_val = normalisasi_nilai_keuangan(token)
                    if normalized_val is not None:
                        text_between_keyword_and_value = " ".join(potential_value_tokens[:token_idx])
                        if is_another_keyword_present(text_between_keyword_and_value, kata_dasar_target, daftar_kata_kunci):
                            break 
                        values_found_for_this_instance.append(normalized_val * pengali_global)
                        if len(values_found_for_this_instance) >= MAX_VALUES_TO_CAPTURE:
                            break
                
                if values_found_for_this_instance:
                    data_hasil_ekstraksi[kata_dasar_target]['t'] = values_found_for_this_instance[0]
                    if len(values_found_for_this_instance) > 1:
                        data_hasil_ekstraksi[kata_dasar_target]['t-1'] = values_found_for_this_instance[1]
                    else:
                        data_hasil_ekstraksi[kata_dasar_target]['t-1'] = None
                    ditemukan_nilai_untuk_kata_dasar_ini = True
                    break 
                
                current_search_pos = keyword_pos + len(variasi_lower)
            
            if ditemukan_nilai_untuk_kata_dasar_ini:
                break 
        
    return data_hasil_ekstraksi