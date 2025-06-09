# Impor pustaka yang diperlukan
import docx
# Impor os tidak diperlukan lagi karena __main__ dihapus

# Fungsi untuk mengekstrak teks dari berkas .txt
def ekstrak_teks_dari_txt(path_file_txt: str) -> str:
    """
    Mengekstrak teks dari berkas .txt.

    Args:
        path_file_txt: Path berkas ke file .txt.

    Returns:
        Teks yang diekstrak, atau pesan error jika terjadi kesalahan.
    """
    try:
        # Buka berkas dalam mode baca ('r') dengan encoding UTF-8
        with open(path_file_txt, 'r', encoding='utf-8') as berkas:
            isi_teks = berkas.read()
        return isi_teks
    except FileNotFoundError:
        # Tangani error jika berkas tidak ditemukan
        return f"Error memproses berkas TXT: Berkas tidak ditemukan di {path_file_txt}"
    except Exception as e:
        # Tangani error umum lainnya
        return f"Error memproses berkas TXT: {e}"

# Fungsi untuk mengekstrak teks dari berkas .docx
def ekstrak_teks_dari_docx(path_file_docx: str) -> str:
    """
    Mengekstrak teks dari berkas .docx.

    Args:
        path_file_docx: Path berkas ke file .docx.

    Returns:
        Teks yang diekstrak, atau pesan error jika terjadi kesalahan.
    """
    try:
        # Buat objek Document dari path berkas
        dokumen_docx = docx.Document(path_file_docx)
        teks_lengkap = []
        # Iterasi melalui semua paragraf dalam dokumen
        for paragraf in dokumen_docx.paragraphs:
            teks_lengkap.append(paragraf.text)
        # Gabungkan teks dari semua paragraf
        return '\n'.join(teks_lengkap)
    except FileNotFoundError:
        # Tangani error jika berkas tidak ditemukan
        return f"Error memproses berkas DOCX: Berkas tidak ditemukan di {path_file_docx}"
    except Exception as e:
        # Tangani error umum lainnya
        return f"Error memproses berkas DOCX: {e}"