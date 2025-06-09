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
    # ASTRA
    {"kata_dasar": "Jumlah aset lancar", "variasi": ["Jumlah aset lancar", "Total aset lancar"]},
    {"kata_dasar": "Jumlah aset tidak lancar", "variasi": ["Jumlah aset tidak lancar", "Total aset tidak lancar"]},
    {"kata_dasar": "Jumlah liabilitas jangka pendek", "variasi": ["Jumlah liabilitas jangka pendek", "Total liabilitas jangka pendek"]},
    {"kata_dasar": "Jumlah liabilitas jangka panjang", "variasi": ["Jumlah liabilitas jangka panjang", "Total liabilitas jangka panjang"]},
    {"kata_dasar": "Jumlah liabilitas", "variasi": ["Jumlah liabilitas", "Total liabilitas"]},
    {"kata_dasar": "Jumlah ekuitas", "variasi": ["Jumlah ekuitas", "Total ekuitas"]},
    {"kata_dasar": "Pendapatan bersih", "variasi": ["Pendapatan bersih", "Penjualan bersih"]},
    {"kata_dasar": "Beban pokok pendapatan", "variasi": ["Beban pokok pendapatan", "Harga pokok penjualan"]},
    {"kata_dasar": "Laba bruto", "variasi": ["Laba bruto", "Laba kotor"]},
    {"kata_dasar": "Laba sebelum pajak penghasilan", "variasi": ["Laba sebelum pajak penghasilan", "Laba/(rugi) sebelum pajak penghasilan"]},
    {"kata_dasar": "Laba tahun berjalan", "variasi": ["Laba tahun berjalan", "Laba bersih tahun berjalan"]},
    {"kata_dasar": "Beban penjualan", "variasi": ["Beban penjualan"]},
    {"kata_dasar": "Beban umum dan administrasi", "variasi": ["Beban umum dan administrasi"]},
    {"kata_dasar": "Penghasilan bunga", "variasi": ["Penghasilan bunga"]},
    {"kata_dasar": "Biaya keuangan", "variasi": ["Biaya keuangan"]},
    {"kata_dasar": "Keuntungan selisih kurs, bersih", "variasi": ["Keuntungan selisih kurs, bersih", "Keuntungan selisih kurs bersih"]},
    {"kata_dasar": "Penghasilan dividen", "variasi": ["Penghasilan dividen"]},
    {"kata_dasar": "Penghasilan lain-lain, bersih", "variasi": ["Penghasilan lain-lain, bersih", "Penghasilan lain lain bersih"]},
    {"kata_dasar": "Beban pajak penghasilan", "variasi": ["Beban pajak penghasilan"]},

    # PROFITABILITY
    {"kata_dasar": "Margin Laba Bersih", "variasi": ["margin laba bersih", "net profit margin", "margin keuntungan bersih"]},
    {"kata_dasar": "Margin Operasi", "variasi": ["margin operasi", "operating margin", "ebit margin", "margin ebit"]},
    {"kata_dasar": "Return on Assets", "variasi": ["return on assets", "roa", "pengembalian atas aset", "rasio pengembalian aset"]},
    {"kata_dasar": "Return on Equity", "variasi": ["return on equity", "roe", "pengembalian atas ekuitas", "rasio pengembalian ekuitas"]},
    {"kata_dasar": "Margin EBITDA", "variasi": ["margin ebitda", "ebitda margin", "margin laba sebelum bunga pajak dan depresiasi"]},

    # LIQUIDITY
    {"kata_dasar": "Rasio Lancar", "variasi": ["rasio lancar", "current ratio", "current asset ratio"]},
    {"kata_dasar": "Rasio Cepat", "variasi": ["rasio cepat", "quick ratio", "acid test ratio"]},
    {"kata_dasar": "Rasio Kas", "variasi": ["rasio kas", "cash ratio"]},

    # LEVERAGE & SOLVENCY
    {"kata_dasar": "Rasio Hutang terhadap Ekuitas", "variasi": ["rasio hutang terhadap ekuitas", "debt to equity ratio", "debt/equity ratio", "der"]},
    {"kata_dasar": "Rasio Penutup Bunga", "variasi": ["rasio penutup bunga", "interest coverage ratio", "rasio cakupan bunga"]},
    {"kata_dasar": "Debt Service Coverage Ratio", "variasi": ["debt service coverage ratio", "dscr", "rasio cakupan layanan hutang"]},
    {"kata_dasar": "Liabilitas terhadap Aset", "variasi": ["liabilitas terhadap aset", "liabilities to assets", "rasio liabilitas terhadap aset"]},

    # EFFICIENCY
    {"kata_dasar": "Perputaran Aset", "variasi": ["perputaran aset", "asset turnover ratio", "rasio perputaran aset"]},
    {"kata_dasar": "Perputaran Persediaan", "variasi": ["perputaran persediaan", "inventory turnover", "rasio perputaran persediaan"]},
    {"kata_dasar": "Perputaran Piutang", "variasi": ["perputaran piutang", "receivables turnover", "rasio perputaran piutang"]},

    # GROWTH TRENDS
    {"kata_dasar": "Pertumbuhan Pendapatan", "variasi": ["pertumbuhan pendapatan", "revenue growth rate", "growth of revenue"]},
    {"kata_dasar": "Pertumbuhan EBIT", "variasi": ["pertumbuhan ebit", "ebit growth rate", "pertumbuhan laba operasi"]},
    {"kata_dasar": "Pertumbuhan Laba Bersih", "variasi": ["pertumbuhan laba bersih", "net income growth", "pertumbuhan net income"]},

    # CASH FLOW QUALITY
    {"kata_dasar": "Arus Kas Operasi terhadap Laba Bersih", "variasi": ["arus kas operasi terhadap laba bersih", "cfo to net income", "cash from ops to net income"]},
    {"kata_dasar": "Arus Kas Bebas", "variasi": ["arus kas bebas", "free cash flow", "fcf"]},

    # ALTMAN Z-SCORE COMPONENTS
    {"kata_dasar": "Modal Kerja terhadap Total Aset", "variasi": ["modal kerja terhadap total aset", "working capital to total assets", "working capital / total assets"]},
    {"kata_dasar": "Laba Ditahan terhadap Total Aset", "variasi": ["laba ditahan terhadap total aset", "retained earnings to total assets", "retained earnings / total assets"]},
    {"kata_dasar": "EBIT terhadap Total Aset", "variasi": ["ebit terhadap total aset", "ebit to total assets", "ebit / total assets"]},
    {"kata_dasar": "Nilai Pasar Ekuitas terhadap Total Liabilitas", "variasi": ["nilai pasar ekuitas terhadap total liabilitas", "market value of equity to total liabilities", "market value of equity / total liabilities"]},
    {"kata_dasar": "Penjualan terhadap Total Aset", "variasi": ["penjualan terhadap total aset", "sales to total assets", "sales / total assets"]},
    {"kata_dasar": "Nilai Z-Score", "variasi": ["z-score", "altman z-score", "hasil z-score"]},

    # PIOTROSKI F-SCORE
    {"kata_dasar": "ROA Positif", "variasi": ["roa positif", "positive roa"]},
    {"kata_dasar": "CFO Positif", "variasi": ["cfo positif", "positive cfo", "arus kas operasi positif"]},
    {"kata_dasar": "Peningkatan ROA", "variasi": ["peningkatan roa", "roa improvement"]},
    {"kata_dasar": "CFO Lebih Besar dari Laba Bersih", "variasi": ["cfo lebih besar dari laba bersih", "cfo > net income"]},
    {"kata_dasar": "Penurunan Leverage YoY", "variasi": ["penurunan leverage yoy", "lower leverage yoy"]},
    {"kata_dasar": "Peningkatan Rasio Lancar YoY", "variasi": ["peningkatan rasio lancar yoy", "higher current ratio yoy"]},
    {"kata_dasar": "Tidak Ada Dilusi Ekuitas", "variasi": ["tidak ada dilusi ekuitas", "no equity dilution"]},
    {"kata_dasar": "Peningkatan Margin Kotor YoY", "variasi": ["peningkatan margin kotor yoy", "higher gross margin yoy"]},
    {"kata_dasar": "Peningkatan Perputaran Aset YoY", "variasi": ["peningkatan perputaran aset yoy", "higher asset turnover yoy"]},
    {"kata_dasar": "Nilai F-Score", "variasi": ["f-score", "piotroski f-score", "hasil f-score"]},

    # M-SCORE INDICATORS
    {"kata_dasar": "DSRI", "variasi": ["dsri", "days sales in receivables index"]},
    {"kata_dasar": "GMI", "variasi": ["gmi", "gross margin index"]},
    {"kata_dasar": "AQI", "variasi": ["aqi", "asset quality index"]},
    {"kata_dasar": "SGI", "variasi": ["sgi", "sales growth index"]},
    {"kata_dasar": "DEPI", "variasi": ["depi", "depreciation index"]},
    {"kata_dasar": "SGAI", "variasi": ["sgai", "sales general and administrative expenses index"]},
    {"kata_dasar": "LVGI", "variasi": ["lvgi", "leverage index"]},
    {"kata_dasar": "TATA", "variasi": ["tata", "total accruals to total assets"]},
    {"kata_dasar": "Nilai M-Score", "variasi": ["m-score", "beneish m-score", "hasil m-score"]},
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
    Mengonversi string angka keuangan (misal "Rp1.234.567,89 (Ribu)") ke float.
    Menangani format Indonesia, tanda kurung untuk negatif, dan satuan.
    """
    if not string_nilai or not isinstance(string_nilai, str):
        return None

    nilai_str_bersih = string_nilai.lower()
    nilai_str_bersih = nilai_str_bersih.replace("rp", "").strip()

    # Tentukan pengali berdasarkan satuan
    pengali = 1.0
    if "triliun" in nilai_str_bersih:
        pengali = 1_000_000_000_000.0
        nilai_str_bersih = nilai_str_bersih.replace("triliun", "").strip()
    elif "miliar" in nilai_str_bersih or " milyar" in nilai_str_bersih:  # Spasi sebelum milyar
        pengali = 1_000_000_000.0
        nilai_str_bersih = nilai_str_bersih.replace("miliar", "").replace("milyar", "").strip()
    elif "juta" in nilai_str_bersih:
        pengali = 1_000_000.0
        nilai_str_bersih = nilai_str_bersih.replace("juta", "").strip()
    elif "ribu" in nilai_str_bersih:
        pengali = 1_000.0
        nilai_str_bersih = nilai_str_bersih.replace("ribu", "").strip()

    # Penanganan angka negatif dalam tanda kurung
    negatif = False
    if nilai_str_bersih.startswith("(") and nilai_str_bersih.endswith(")"):
        negatif = True
        nilai_str_bersih = nilai_str_bersih[1:-1]

    # Hapus karakter non-numerik kecuali koma (desimal) dan titik (ribuan)
    # Pertama, standarisasi: hapus titik (pemisah ribuan), ganti koma (pemisah desimal) dengan titik
    nilai_str_bersih = nilai_str_bersih.replace(".", "")  # Hapus pemisah ribuan (titik)
    nilai_str_bersih = nilai_str_bersih.replace(",", ".")  # Ganti pemisah desimal (koma) dengan titik

    # Hapus karakter non-numerik yang mungkin masih tersisa selain titik desimal
    nilai_str_bersih = re.sub(r"[^0-9.]", "", nilai_str_bersih)

    if not nilai_str_bersih:  # Jika string menjadi kosong setelah pembersihan
        return None

    try:
        nilai_float = float(nilai_str_bersih)
        hasil_akhir = nilai_float * pengali
        return -hasil_akhir if negatif else hasil_akhir
    except ValueError:
        return None  # Gagal konversi ke float


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

    lines = [line.lower() for line in ocr_text.splitlines()]
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


def ekstrak_data_keuangan_tahunan(teks_dokumen: str, daftar_kata_kunci: list[dict] | None = None) -> dict:
    if daftar_kata_kunci is None:
        daftar_kata_kunci = DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT
    
    # Initialize all kata_dasar from daftar_kata_kunci to None
    data_hasil_ekstraksi = {info["kata_dasar"]: None for info in daftar_kata_kunci}
    
    if not teks_dokumen or not isinstance(teks_dokumen, str):
        return data_hasil_ekstraksi

    # Pre-process lines: lowercase and strip whitespace
    lines = [line.strip() for line in teks_dokumen.lower().splitlines()]
    
    # tahun_pelaporan = identifikasi_tahun_pelaporan(teks_dokumen) # Not used for value selection yet

    MAX_LINES_TO_SEARCH_AFTER_KEYWORD = 3 # Max non-empty lines to check after the keyword's line

    for info_kata_kunci in daftar_kata_kunci:
        kata_dasar_target = info_kata_kunci["kata_dasar"]
        nilai_final_untuk_kata_dasar = None # Stores the single value found for this kata_dasar

        for variasi in info_kata_kunci["variasi"]:
            variasi_lower = variasi.lower()
            
            for line_idx, current_line_content in enumerate(lines):
                if not current_line_content: # Skip empty lines (already stripped)
                    continue

                keyword_pos = current_line_content.find(variasi_lower)
                if keyword_pos != -1:
                    # Keyword found in current_line_content
                    
                    # 1. Search on the remainder of the same line
                    text_after_keyword_on_same_line = current_line_content[keyword_pos + len(variasi_lower):]
                    # Split carefully to handle various spacing
                    tokens_on_same_line = [t for t in text_after_keyword_on_same_line.split(' ') if t] 
                    for token in tokens_on_same_line:
                        normalized_val = normalisasi_nilai_keuangan(token)
                        if normalized_val is not None:
                            nilai_final_untuk_kata_dasar = normalized_val
                            break # Found value on same line, stop token search
                    
                    if nilai_final_untuk_kata_dasar is not None:
                        # Found value for this variasi, no need to check subsequent lines for this keyword instance
                        break # Break from line_idx loop (move to next variasi or next kata_dasar)

                    # 2. If not found on same line, search on subsequent non-empty lines
                    lines_searched_count = 0
                    for lookahead_idx in range(line_idx + 1, len(lines)):
                        if lines_searched_count >= MAX_LINES_TO_SEARCH_AFTER_KEYWORD:
                            break # Searched enough subsequent lines

                        next_line_content = lines[lookahead_idx]
                        if not next_line_content: # Skip empty lines
                            continue
                        
                        lines_searched_count += 1 # Count a non-empty line search

                        # Stop if another keyword (not related to current kata_dasar_target) is found
                        if is_another_keyword_present(next_line_content, kata_dasar_target, daftar_kata_kunci):
                            break # Stop downward search for this instance of variasi

                        # Split carefully
                        tokens_on_next_line = [t for t in next_line_content.split(' ') if t]
                        for token in tokens_on_next_line:
                            normalized_val = normalisasi_nilai_keuangan(token)
                            if normalized_val is not None:
                                nilai_final_untuk_kata_dasar = normalized_val
                                break # Found value on subsequent line, stop token search
                        
                        if nilai_final_untuk_kata_dasar is not None:
                            break # Break from lookahead_idx loop (found value on subsequent lines)
                
                if nilai_final_untuk_kata_dasar is not None:
                    # Value found for this variasi, break from iterating lines for this variasi
                    break 
            
            if nilai_final_untuk_kata_dasar is not None:
                # Value found for this kata_dasar_target using one of its variasi
                break # Break from variasi loop (move to next kata_dasar_target)
        
        # Assign the found value (or None if not found) to the specific kata_dasar_target
        data_hasil_ekstraksi[kata_dasar_target] = nilai_final_untuk_kata_dasar
        
    return data_hasil_ekstraksi