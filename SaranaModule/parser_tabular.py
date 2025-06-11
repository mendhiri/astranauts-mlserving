# Impor pustaka yang diperlukan
import pandas as pd

def ekstrak_data_dari_xlsx(path_file_xlsx: str) -> str:
    """
    Mengekstrak data dari berkas .xlsx dan mengembalikannya sebagai string.
    Setiap baris dalam file Excel akan menjadi baris dalam string,
    dengan sel-sel dipisahkan oleh tab.

    Args:
        path_file_xlsx: Path berkas ke file .xlsx.

    Returns:
        String yang berisi data dari XLSX, atau pesan error jika terjadi kesalahan.
    """
    try:
        df = pd.read_excel(path_file_xlsx, header=None, engine='openpyxl')
        # Ubah DataFrame menjadi string dengan sel dipisahkan tab dan baris dipisahkan newline
        # astype(str) untuk memastikan semua data dikonversi ke string sebelum join
        return '\n'.join(['\t'.join(map(str, row)) for row in df.values.tolist()])
    except FileNotFoundError:
        return f"Error memproses berkas XLSX: Berkas tidak ditemukan di {path_file_xlsx}"
    except Exception as e:
        return f"Error memproses berkas XLSX: {e}"

def ekstrak_data_dari_csv(path_file_csv: str) -> str:
    """
    Mengekstrak data dari berkas .csv dan mengembalikannya sebagai string.
    Setiap baris dalam file CSV akan menjadi baris dalam string,
    dengan sel-sel dipisahkan oleh koma (atau pemisah asli CSV).

    Args:
        path_file_csv: Path berkas ke file .csv.

    Returns:
        String yang berisi data dari CSV, atau pesan error jika terjadi kesalahan.
    """
    try:
        df = pd.read_csv(path_file_csv, header=None)
        # Ubah DataFrame menjadi string dengan sel dipisahkan tab dan baris dipisahkan newline
        # Ini akan membuat output CSV konsisten dengan format XLSX (tab-separated)
        return '\n'.join(['\t'.join(map(str, row)) for row in df.values.tolist()])
    except FileNotFoundError:
        return f"Error memproses berkas CSV: Berkas tidak ditemukan di {path_file_csv}"
    except pd.errors.EmptyDataError:
        return f"Error memproses berkas CSV: Berkas kosong atau tidak ada data di {path_file_csv}"
    except Exception as e:
        return f"Error memproses berkas CSV: {e}"