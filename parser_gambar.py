# Impor pustaka yang diperlukan
import pytesseract
from PIL import Image
import cv2  # Impor OpenCV
import numpy as np  # Impor NumPy
import re  # Untuk membersihkan teks hasil OCR
import easyocr


# Fungsi helper untuk konversi ke skala abu
def konversi_ke_skala_abu(gambar_cv):
    """Mengonversi gambar OpenCV ke skala abu."""
    # Periksa jumlah channel. Jika sudah grayscale (2D), tidak perlu konversi.
    if len(gambar_cv.shape) == 2:
        return gambar_cv
    # Jika memiliki 3 channel (BGR) atau 4 channel (BGRA), konversi ke grayscale.
    elif len(gambar_cv.shape) == 3 and gambar_cv.shape[2] in [3, 4]:
        if gambar_cv.shape[2] == 3:  # BGR
            return cv2.cvtColor(gambar_cv, cv2.COLOR_BGR2GRAY)
        elif gambar_cv.shape[2] == 4:  # BGRA
            return cv2.cvtColor(gambar_cv, cv2.COLOR_BGRA2GRAY)
    # Jika format tidak terduga, kembalikan seperti semula dengan peringatan (atau bisa raise error)
    print("Peringatan: Format gambar tidak terduga untuk konversi skala abu.")
    return gambar_cv


# Fungsi helper untuk menghilangkan derau (noise)
def hilangkan_derau(gambar_cv_skala_abu, ukuran_kernel=3):
    """Menerapkan filter Median Blur untuk menghilangkan derau."""
    # Median blur efektif untuk derau 'salt and pepper'
    return cv2.medianBlur(gambar_cv_skala_abu, ukuran_kernel)


def binarisasi_adaptif(gambar_cv_skala_abu):
    return cv2.adaptiveThreshold(
        gambar_cv_skala_abu, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 2
    )


# Fungsi helper untuk mencoba pelurusan kemiringan (deskew)
def coba_pelurusan_kemiringan(gambar_cv_biner):
    """Mencoba meluruskan kemiringan gambar. Implementasi dasar."""
    # Dapatkan koordinat piksel putih (teks)
    coords = np.column_stack(np.where(gambar_cv_biner > 0))
    # Dapatkan sudut kemiringan menggunakan minAreaRect
    # Perlu diperhatikan, minAreaRect mengembalikan (center (x,y), (width, height), angle of rotation)
    # Sudut berkisar antara [-90, 0); jika objek tegak, sudutnya 0. Jika objek horizontal, sudutnya -90.
    if coords.shape[0] < 5:  # Perlu setidaknya 5 poin untuk fitEllipse/minAreaRect
        print("Peringatan: Tidak cukup poin untuk mendeteksi kemiringan, melewati pelurusan.")
        return gambar_cv_biner

    rect = cv2.minAreaRect(coords)
    sudut = rect[-1]  # Sudut rotasi

    # Logika untuk menyesuaikan sudut dari cv2.minAreaRect
    # Jika sudut kurang dari -45, itu berarti objek lebih condong ke vertikal.
    # Jika sudut lebih dari -45 (mendekati 0), objek lebih condong ke horizontal.
    if sudut < -45:
        sudut = -(90 + sudut)  # Menyesuaikan untuk rotasi yang benar
    else:
        sudut = -sudut  # Membalikkan sudut

    # Jika sudut terlalu kecil, mungkin tidak perlu rotasi
    if abs(sudut) < 0.1:  # Threshold bisa disesuaikan
        return gambar_cv_biner

    (tinggi, lebar) = gambar_cv_biner.shape[:2]
    pusat = (lebar // 2, tinggi // 2)

    # Dapatkan matriks rotasi
    M = cv2.getRotationMatrix2D(pusat, sudut, 1.0)
    # Lakukan rotasi affine
    # borderMode=cv2.BORDER_REPLICATE digunakan untuk mengisi piksel di batas
    # borderValue bisa digunakan dengan cv2.BORDER_CONSTANT untuk mengisi dengan warna tertentu (misal putih jika background putih)
    terlurus = cv2.warpAffine(gambar_cv_biner, M, (lebar, tinggi),
                              flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return terlurus


def resize_for_ocr(img, min_height=1000):
    h, w = img.shape[:2]
    if h < min_height:
        scale = min_height / h
        return cv2.resize(img, (int(w*scale), min_height), interpolation=cv2.INTER_CUBIC)
    return img


def crop_margin(gambar_biner):
    coords = cv2.findNonZero(gambar_biner)
    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        return gambar_biner[y:y+h, x:x+w]
    return gambar_biner

def adjust_contrast(img, alpha=1.5, beta=0):
    """Meningkatkan kontras gambar. Alpha > 1 meningkatkan kontras, beta untuk brightness."""
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

def sharpen_image(img):
    """Menajamkan gambar dengan kernel sharpening."""
    kernel = np.array([[0, -1, 0],
                       [-1, 5,-1],
                       [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)

def set_dpi(pil_img, dpi=300):
    """Set DPI pada gambar PIL sebelum OCR (hanya metadata, tidak resize)."""
    pil_img.info['dpi'] = (dpi, dpi)
    return pil_img

def preset_preprocessing(img_cv, preset='scanned'):
    """
    Preset preprocessing untuk berbagai skenario:
    - 'scanned': Untuk dokumen hasil scan (default)
    - 'text_heavy': Untuk dokumen teks berat (misal laporan keuangan)
    - 'printed': Untuk teks cetak jelas
    """
    # Grayscale
    img = konversi_ke_skala_abu(img_cv)
    # Denoising
    img = cv2.fastNlMeansDenoising(img, h=15)
    # Sharpen
    img = sharpen_image(img)
    # Contrast
    img = adjust_contrast(img, alpha=1.8 if preset == 'text_heavy' else 1.5)
    # Thresholding
    img = binarisasi_adaptif(img)
    # Deskew
    img = coba_pelurusan_kemiringan(img)
    # Crop border
    img = crop_margin(img)
    # Resize for OCR
    img = resize_for_ocr(img, min_height=1500 if preset == 'scanned' else 1000)
    return img


def bersihkan_teks(teks: str) -> str:
    """Membersihkan teks hasil OCR: menghapus spasi/enter berlebih dan baris kosong."""
    # Gabungkan baris, hapus spasi berlebih, dan normalisasi whitespace
    lines = [re.sub(r'\s+', ' ', l).strip() for l in teks.splitlines()]
    lines = [l for l in lines if l]  # Hapus baris kosong
    return ' '.join(lines)

# Definisikan fungsi utama untuk mengekstrak teks dari gambar
def ekstrak_teks_dari_gambar(path_gambar: str, engine: str = 'easyocr', preset: str = 'scanned', dpi: int = 600) -> str:
    """
    Mengekstrak teks dari gambar menggunakan Tesseract OCR atau EasyOCR setelah pra-pemrosesan.
    Args:
        path_gambar: Path berkas ke gambar.
        engine: 'pytesseract' (default) atau 'easyocr'.
        preset: preset preprocessing ('scanned', 'text_heavy', 'printed')
        dpi: DPI untuk metadata gambar (default 300)
    Returns:
        Teks yang diekstrak, sudah dibersihkan, atau pesan error jika gagal.
    """
    try:
        gambar_pil = Image.open(path_gambar)
        gambar_pil = set_dpi(gambar_pil, dpi=dpi)
        gambar_cv = np.array(gambar_pil)
        if gambar_cv.ndim == 3:
            if gambar_cv.shape[2] == 3:
                gambar_cv = cv2.cvtColor(gambar_cv, cv2.COLOR_RGB2BGR)
            elif gambar_cv.shape[2] == 4:
                gambar_cv = cv2.cvtColor(gambar_cv, cv2.COLOR_RGBA2BGR)
        gambar_untuk_ocr = preset_preprocessing(gambar_cv, preset=preset)

        if engine == 'easyocr':
            try:
                import easyocr
            except ImportError:
                return "Error: easyocr belum terinstal. Install dengan 'pip install easyocr'."
            reader = easyocr.Reader(['id', 'en'], gpu=True)
            hasil = reader.readtext(gambar_untuk_ocr, detail=0, paragraph=True)
            hasil_teks = ' '.join(hasil)
        else:
            custom_config = r'--oem 3 --psm 6'
            hasil_teks = pytesseract.image_to_string(gambar_untuk_ocr, lang='ind+eng', config=custom_config)

        return bersihkan_teks(hasil_teks)
    except Exception as e:
        return f"Error OCR: {e}"