# Impor pustaka yang diperlukan
import pytesseract
from PIL import Image
import cv2  # Impor OpenCV
import numpy as np  # Impor NumPy
import re  # Untuk membersihkan teks hasil OCR

try:
    import easyocr
except ImportError:
    easyocr = None  # Akan ditangani di logika OCR

try:
    import pyocr
    import pyocr.builders
except ImportError:
    pyocr = None  # Akan ditangani di logika OCR


DEFAULT_OPSI_PRAPROSES = {
    'dpi_target': 300,
    'min_ocr_height': 1000,
    'denoising': {'type': 'fastNlMeans', 'h': 10},
    'sharpening': False,
    'contrast': {'alpha': 1.5, 'beta': 0},
    'binarization': {'method': 'adaptive_gaussian', 'block_size': 31, 'C': 2, 'invert': True},
    'deskew': True,
    'remove_borders': False,
    'crop_final': True,
    'easyocr_gpu': False,
    'pyocr_lang': 'ind+eng',
    'tesseract_config': r'--oem 3 --psm 6'
}


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

def set_dpi(pil_img, dpi_target=300): # Parameter name changed for clarity
    """Set DPI pada gambar PIL sebelum OCR (hanya metadata, tidak resize)."""
    pil_img.info['dpi'] = (dpi_target, dpi_target)
    return pil_img

def remove_borders_cv(img_biner_white_text): # Expects white text on black background
    """Menghapus potensi border dari gambar biner (teks putih, background hitam)."""
    contours, _ = cv2.findContours(img_biner_white_text, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img_biner_white_text

    img_h, img_w = img_biner_white_text.shape[:2]
    output_img = img_biner_white_text.copy()

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # Heuristic untuk border-like contours:
        is_border_candidate = False
        # Cek apakah kontur besar dan dekat dengan tepi gambar
        if w * h > (img_h * img_w * 0.05): # Minimal 5% area gambar (disesuaikan dari 10%)
            if (x < 10 or y < 10 or (x + w) > (img_w - 10) or (y + h) > (img_h - 10)):
                is_border_candidate = True
        
        if is_border_candidate:
            area = cv2.contourArea(contour)
            # Jika kontur memiliki fill ratio tinggi, kemungkinan itu adalah border halaman scan
            if area / (w * h + 1e-6) > 0.8: 
                cv2.drawContours(output_img, [contour], -1, 0, thickness=cv2.FILLED) # Fill dengan hitam
    return output_img

# Fungsi preset_preprocessing akan dihapus dan logikanya diintegrasikan ke ekstrak_teks_dari_gambar


def bersihkan_teks(teks: str) -> str:
    """Membersihkan teks hasil OCR: menghapus spasi/enter berlebih dan baris kosong."""
    # Gabungkan baris, hapus spasi berlebih, dan normalisasi whitespace
    lines = [re.sub(r'\s+', ' ', l).strip() for l in teks.splitlines()]
    lines = [l for l in lines if l]  # Hapus baris kosong
    return ' '.join(lines)

# Definisikan fungsi utama untuk mengekstrak teks dari gambar
def ekstrak_teks_dari_gambar(path_gambar: str, mesin_ocr: str = 'tesseract', opsi_praproses: dict = None) -> str:
    """
    Mengekstrak teks dari gambar menggunakan berbagai mesin OCR setelah pra-pemrosesan yang dapat dikonfigurasi.
    Args:
        path_gambar: Path berkas ke gambar.
        mesin_ocr: 'tesseract', 'easyocr', 'pyocr_tesseract', 'pyocr_cuneiform'.
        opsi_praproses: Dictionary untuk mengontrol langkah-langkah pra-pemrosesan.
                        Jika None, DEFAULT_OPSI_PRAPROSES akan digunakan.
    Returns:
        Teks yang diekstrak, sudah dibersihkan, atau pesan error jika gagal.
    """
    final_options = DEFAULT_OPSI_PRAPROSES.copy()
    if opsi_praproses is not None:
        final_options.update(opsi_praproses)
    # Gunakan final_options untuk semua konfigurasi selanjutnya
    opsi_praproses = final_options

    try:
        gambar_pil = Image.open(path_gambar)
        gambar_pil = set_dpi(gambar_pil, dpi_target=opsi_praproses['dpi_target']) # Menggunakan opsi_praproses
        
        # Konversi PIL ke OpenCV (BGR)
        gambar_cv = np.array(gambar_pil)
        if gambar_cv.ndim == 3: # Hanya konversi jika berwarna
            if gambar_cv.shape[2] == 3: # RGB
                gambar_cv = cv2.cvtColor(gambar_cv, cv2.COLOR_RGB2BGR)
            elif gambar_cv.shape[2] == 4: # RGBA
                gambar_cv = cv2.cvtColor(gambar_cv, cv2.COLOR_RGBA2BGR)
        # Jika gambar_cv sudah grayscale dari PIL (misal .convert('L')), ndim akan 2
        
        # Mulai Preprocessing
        # 1. Konversi ke Grayscale (sudah dihandle oleh fungsi konversi_ke_skala_abu jika perlu)
        #    Fungsi konversi_ke_skala_abu sudah menangani gambar yang mungkin sudah grayscale.
        processed_img = konversi_ke_skala_abu(gambar_cv)

        # 2. Denoising
        denoising_opt = opsi_praproses.get('denoising')
        if denoising_opt and isinstance(denoising_opt, dict):
            denoise_type = denoising_opt.get('type')
            if denoise_type == 'fastNlMeans':
                processed_img = cv2.fastNlMeansDenoising(processed_img, h=denoising_opt.get('h', 10))
            elif denoise_type == 'median':
                processed_img = cv2.medianBlur(processed_img, denoising_opt.get('kernel', 3))
        
        # 3. Sharpening
        if opsi_praproses.get('sharpening'):
            processed_img = sharpen_image(processed_img)

        # 4. Contrast Adjustment
        contrast_opt = opsi_praproses.get('contrast')
        if contrast_opt and isinstance(contrast_opt, dict):
            processed_img = adjust_contrast(processed_img, alpha=contrast_opt.get('alpha', 1.5), beta=contrast_opt.get('beta', 0))

        # 5. Binarization
        bin_opt = opsi_praproses['binarization']
        invert_binarization = bin_opt.get('invert', True) # Teks putih = 255
        
        if bin_opt['method'] == 'adaptive_gaussian':
            thresh_type = cv2.THRESH_BINARY_INV if invert_binarization else cv2.THRESH_BINARY
            processed_img = cv2.adaptiveThreshold(
                processed_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                thresh_type, bin_opt['block_size'], bin_opt['C']
            )
        elif bin_opt['method'] == 'otsu':
            thresh_type = cv2.THRESH_BINARY_INV if invert_binarization else cv2.THRESH_BINARY
            _, processed_img = cv2.threshold(processed_img, 0, 255, thresh_type + cv2.THRESH_OTSU)
        # Pastikan teks adalah putih (255) dan background hitam (0) untuk langkah selanjutnya
        # Jika invert_binarization adalah False (teks hitam), kita invert di sini
        if not invert_binarization: # Jika teks hitam (0) dan bg putih (255)
             processed_img = cv2.bitwise_not(processed_img) # Invert agar teks jadi putih

        # 6. Deskew
        if opsi_praproses.get('deskew'):
            processed_img = coba_pelurusan_kemiringan(processed_img) # Harapannya ini bekerja dengan teks putih

        # 7. Remove Borders
        if opsi_praproses.get('remove_borders'):
            processed_img = remove_borders_cv(processed_img) # Fungsi ini mengharapkan teks putih

        # 8. Crop Final
        if opsi_praproses.get('crop_final'):
            processed_img = crop_margin(processed_img) # crop_margin juga harus bekerja dengan teks putih

        # 9. Resize for OCR
        # resize_for_ocr diaplikasikan pada gambar biner yang sudah diproses
        processed_img = resize_for_ocr(processed_img, min_height=opsi_praproses['min_ocr_height'])
        
        # Simpan gambar yang telah diproses untuk debugging jika perlu (opsional)
        # cv2.imwrite("processed_for_ocr.png", processed_img)

        # (Logika OCR akan ditambahkan/diperbarui di sini)
        gambar_untuk_ocr = processed_img # Ini adalah gambar final untuk OCR

        if mesin_ocr == 'easyocr':
            if easyocr is None:
                return "Error: easyocr tidak terinstal. Install dengan 'pip install easyocr'."
            # easyocr.Reader initialization should happen only once if possible,
            # but for now, it's here for simplicity.
            reader = easyocr.Reader(['id', 'en'], gpu=opsi_praproses['easyocr_gpu'])
            # EasyOCR biasanya menerima path file atau array numpy (BGR atau Grayscale)
            # Karena gambar_untuk_ocr adalah grayscale (single channel), EasyOCR harusnya bisa handle.
            hasil = reader.readtext(gambar_untuk_ocr, detail=0, paragraph=True)
            hasil_teks = ' '.join(hasil)
        elif mesin_ocr == 'tesseract':
            # Pytesseract bekerja dengan gambar PIL
            pil_img_for_tesseract = Image.fromarray(gambar_untuk_ocr)
            hasil_teks = pytesseract.image_to_string(
                pil_img_for_tesseract,
                lang=opsi_praproses.get('pyocr_lang', 'ind+eng'), 
                config=opsi_praproses['tesseract_config']
            )
        elif mesin_ocr == 'pyocr_tesseract':
            if pyocr is None:
                return "Error: pyocr tidak terinstal. Install dengan 'pip install pyocr'."
            tools = pyocr.get_available_tools()
            if not tools:
                return "Error: Tidak ada tool PyOCR yang tersedia."
            
            tool_tesseract = None
            for tool_item in tools:
                if 'Tesseract' in tool_item.get_name(): # More robust check
                    tool_tesseract = tool_item
                    break
            
            if tool_tesseract is None:
                return "Error: Tool Tesseract untuk PyOCR tidak ditemukan."
            
            # PyOCR expects PIL Image
            pil_img_for_pyocr = Image.fromarray(gambar_untuk_ocr)
            hasil_teks = tool_tesseract.image_to_string(
                pil_img_for_pyocr,
                lang=opsi_praproses['pyocr_lang'],
                builder=pyocr.builders.TextBuilder()
            )
        elif mesin_ocr == 'pyocr_cuneiform':
            if pyocr is None:
                return "Error: pyocr tidak terinstal. Install dengan 'pip install pyocr'."
            tools = pyocr.get_available_tools()
            if not tools:
                return "Error: Tidak ada tool PyOCR yang tersedia."

            tool_cuneiform = None
            for tool_item in tools:
                if 'Cuneiform' in tool_item.get_name().lower(): # Check for Cuneiform (case-insensitive)
                    tool_cuneiform = tool_item
                    break
            
            if tool_cuneiform is None:
                # Specific message for Cuneiform as it's less common
                return "Error: Tool Cuneiform untuk PyOCR tidak ditemukan. Pastikan Cuneiform terinstal dan dapat diakses oleh PyOCR."

            # PyOCR expects PIL Image
            pil_img_for_pyocr = Image.fromarray(gambar_untuk_ocr)
            hasil_teks = tool_cuneiform.image_to_string(
                pil_img_for_pyocr,
                lang=opsi_praproses['pyocr_lang'], 
                builder=pyocr.builders.TextBuilder()
            )
        else:
            return f"Mesin OCR '{mesin_ocr}' tidak dikenal."

        return bersihkan_teks(hasil_teks)
    except Exception as e:
        return f"Error OCR atau pra-pemrosesan: {e}"