# Impor pustaka yang diperlukan
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize  # Tambahkan sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re
import json
import unicodedata  # Untuk normalisasi lanjutan jika diperlukan

# Inisialisasi pelumat dan daftar kata henti
pelumat = WordNetLemmatizer()
try:
    kata_henti = set(stopwords.words('indonesian'))
    print("Menggunakan stopwords Bahasa Indonesia.")
except IOError:
    print("Stopwords Bahasa Indonesia tidak ditemukan, menggunakan stopwords Bahasa Inggris sebagai fallback.")
    kata_henti = set(stopwords.words('english'))

# Definisi daftar kata kunci keuangan dalam Bahasa Indonesia
DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT = [
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

    # ASTRA
    {"kata_dasar": "Jumlah Aset Lancar", "variasi": ["jumlah aset lancar", "aset lancar", "total aset lancar"]},
    {"kata_dasar": "Jumlah Aset Tidak Lancar", "variasi": ["jumlah aset tidak lancar", "aset tidak lancar", "total aset tidak lancar"]},
    {"kata_dasar": "Jumlah Aset", "variasi": ["jumlah aset", "total aset"]},
    {"kata_dasar": "Jumlah Liabilitas Jangka Pendek", "variasi": ["jumlah liabilitas jangka pendek", "liabilitas jangka pendek", "total liabilitas jangka pendek"]},
    {"kata_dasar": "Jumlah Liabilitas Jangka Panjang", "variasi": ["jumlah liabilitas jangka panjang", "liabilitas jangka panjang", "total liabilitas jangka panjang"]},
    {"kata_dasar": "Jumlah Liabilitas", "variasi": ["jumlah liabilitas", "total liabilitas"]},
    {"kata_dasar": "Jumlah Ekuitas", "variasi": ["jumlah ekuitas", "total ekuitas", "ekuitas"]},
    {"kata_dasar": "Pendapatan Usaha", "variasi": ["pendapatan usaha", "penjualan bersih", "pendapatan bersih usaha"]},
    {"kata_dasar": "Beban Pokok Pendapatan", "variasi": ["beban pokok pendapatan", "harga pokok penjualan"]},
    {"kata_dasar": "Laba Bruto", "variasi": ["laba bruto", "laba kotor"]},
    {"kata_dasar": "Laba Usaha", "variasi": ["laba usaha", "laba operasional", "penghasilan operasional"]},
    {"kata_dasar": "Laba Sebelum Pajak", "variasi": ["laba sebelum pajak", "penghasilan sebelum pajak", "laba/(rugi) sebelum pajak penghasilan"]},
    {"kata_dasar": "Laba Tahun Berjalan", "variasi": ["laba tahun berjalan", "laba bersih tahun berjalan", "penghasilan bersih tahun berjalan", "laba bersih setelah pajak", "laba periode berjalan", "laba bersih komprehensif tahun berjalan"]},

    # Tambahkan kata kunci umum
    {"kata_dasar": "Laba", "variasi": ["laba", "profit", "earnings", "net income", "laba bersih", "laba kotor", "laba operasional", "laba sebelum pajak"]},
    {"kata_dasar": "Pendapatan", "variasi": ["pendapatan", "revenue", "income", "sales", "penjualan", "penerimaan"]},
    {"kata_dasar": "Biaya", "variasi": ["biaya", "cost", "expenses", "beban", "pengeluaran"]},
    {"kata_dasar": "Aset", "variasi": ["aset", "assets", "resources", "resources"]},
    {"kata_dasar": "Liabilitas", "variasi": ["liabilitas", "liabilities", "hutang", "utang"]},
    {"kata_dasar": "Ekuitas", "variasi": ["ekuitas", "equity", "shareholders' equity", "modal"]},
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
    if not teks_mentah:
        return []
    token_kata = word_tokenize(teks_mentah.lower())
    # Pelumatan mungkin kurang optimal untuk Bahasa Indonesia dengan WordNetLemmatizer default NLTK.
    # Pertimbangkan stemmer Bahasa Indonesia jika akurasi menjadi masalah.
    token_terproses = [
        pelumat.lemmatize(token) for token in token_kata if token.isalnum() and token not in kata_henti
    ]
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


def ekstrak_data_keuangan_tahunan(teks_dokumen: str, daftar_kata_kunci: list[dict] | None = None) -> dict:
    if daftar_kata_kunci is None:
        daftar_kata_kunci = DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT
    data_hasil_ekstraksi = {}
    if not teks_dokumen:
        return data_hasil_ekstraksi

    tahun_pelaporan = identifikasi_tahun_pelaporan(teks_dokumen)
    tahun_sebelumnya_str = str(int(tahun_pelaporan) - 1) if tahun_pelaporan else None

    baris_dokumen = teks_dokumen.lower().splitlines()
    for info_kata_kunci in daftar_kata_kunci:
        kata_dasar_target = info_kata_kunci["kata_dasar"]
        nilai_ditemukan = None
        for variasi in info_kata_kunci["variasi"]:
            variasi_lower = variasi.lower()
            for i, baris in enumerate(baris_dokumen):
                if variasi_lower in baris:
                    # Cari angka di baris yang sama atau baris berikutnya
                    pola_angka = re.compile(r"[\d\.,]+")
                    angka_ditemukan = pola_angka.findall(baris)
                    if not angka_ditemukan and i+1 < len(baris_dokumen):
                        angka_ditemukan = pola_angka.findall(baris_dokumen[i+1])
                    if angka_ditemukan:
                        nilai_ternormalisasi = normalisasi_nilai_keuangan(angka_ditemukan[0])
                        if nilai_ternormalisasi is not None:
                            nilai_ditemukan = nilai_ternormalisasi
                            break
            if nilai_ditemukan is not None:
                break
        data_hasil_ekstraksi[kata_dasar_target] = nilai_ditemukan
    return data_hasil_ekstraksi