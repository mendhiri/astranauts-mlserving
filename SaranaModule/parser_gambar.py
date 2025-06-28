# Impor pustaka yang diperlukan
import pytesseract
from pytesseract import Output
from PIL import Image
import cv2  # Impor OpenCV
import numpy as np  # Impor NumPy
import re  # Untuk membersihkan teks hasil OCR
import io
import os
from dotenv import load_dotenv

try:
    import easyocr
except ImportError:
    easyocr = None  # Akan ditangani di logika OCR

try:
    import pyocr
    import pyocr.builders
except ImportError:
    pyocr = None  # Akan ditangani di logika OCR

try:
    import ollama # Impor ollama untuk fungsionalitas OCR dengan Ollama
except ImportError:
    ollama = None # Akan ditangani di logika OCR jika Ollama tidak terinstal


DEFAULT_OPSI_PRAPROSES = {
    'dpi_target': 600,
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
    'tesseract_config': r'--oem 3 --psm 3'  # Changed from psm 6 to psm 3
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
        return cv2.resize(img, (int(w * scale), min_height), interpolation=cv2.INTER_CUBIC)
    return img


def crop_margin(gambar_biner):
    coords = cv2.findNonZero(gambar_biner)
    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        return gambar_biner[y:y + h, x:x + w]
    return gambar_biner


def adjust_contrast(img, alpha=1.5, beta=0):
    """Meningkatkan kontras gambar. Alpha > 1 meningkatkan kontras, beta untuk brightness."""
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)


def sharpen_image(img):
    """Menajamkan gambar dengan kernel sharpening."""
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)


def set_dpi(pil_img, dpi_target=300):  # Parameter name changed for clarity
    """Set DPI pada gambar PIL sebelum OCR (hanya metadata, tidak resize)."""
    pil_img.info['dpi'] = (dpi_target, dpi_target)
    return pil_img


def remove_borders_cv(img_biner_white_text):  # Expects white text on black background
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
        if w * h > (img_h * img_w * 0.05):  # Minimal 5% area gambar (disesuaikan dari 10%)
            if (x < 10 or y < 10 or (x + w) > (img_w - 10) or (y + h) > (img_h - 10)):
                is_border_candidate = True

        if is_border_candidate:
            area = cv2.contourArea(contour)
            # Jika kontur memiliki fill ratio tinggi, kemungkinan itu adalah border halaman scan
            if area / (w * h + 1e-6) > 0.8:
                cv2.drawContours(output_img, [contour], -1, 0, thickness=cv2.FILLED)  # Fill dengan hitam
    return output_img


# Fungsi preset_preprocessing akan dihapus dan logikanya diintegrasikan ke ekstrak_teks_dari_gambar

def bersihkan_satu_baris(line_text: str) -> str:
    """Membersihkan satu baris teks hasil OCR: menghapus spasi berlebih."""
    cleaned_line = re.sub(r'\s+', ' ', line_text).strip()
    return cleaned_line

def ocr_dengan_ollama(path_gambar: str, prompt_pengguna: str = "get all the data from the image") -> list[str]:
    """
    Mengekstrak teks dari gambar menggunakan Ollama dengan model Llama 3.2-Vision.
    Args:
        path_gambar: Path ke file gambar.
        prompt_pengguna: Prompt yang akan diberikan ke model Ollama.
    Returns:
        Sebuah list string, di mana setiap string adalah baris teks yang terdeteksi.
        Mengembalikan list kosong jika terjadi error atau tidak ada teks terdeteksi.
    """
    if ollama is None:
        print("ERROR: Pustaka Ollama tidak terinstal. Tidak dapat melakukan OCR dengan Ollama. Silakan install dengan `pip install ollama`.")
        return []
    
    try:
        if not os.path.exists(path_gambar):
            print(f"ERROR: File gambar tidak ditemukan di {path_gambar} untuk Ollama OCR.")
            return []

        # Pastikan model vision yang diinginkan ada, jika tidak beri tahu pengguna
        # Ini hanya contoh, idealnya daftar model diambil dari ollama.list() jika perlu pengecekan dinamis
        # Untuk sekarang, kita asumsikan pengguna tahu model 'llama3.2-vision' perlu ada.
        
        print(f"INFO: Memulai OCR dengan Ollama model 'llama3.2-vision' untuk gambar: {os.path.basename(path_gambar)}")
        response = ollama.chat(
            model="llama3.2-vision", # Model spesifik untuk vision
            messages=[{
                "role": "user",
                "content": prompt_pengguna,
                "images": [path_gambar]
            }],
            # Pertimbangkan menambahkan timeout di sini jika library ollama mendukungnya secara langsung
            # atau jika menggunakan ollama.Client, timeout bisa diset di sana.
        )
        
        if response and response.get('message') and response['message'].get('content'):
            extracted_text = response['message']['content'].strip()
            print(f"INFO: Teks berhasil diekstrak oleh Ollama (awal 200 char): {extracted_text[:200]}...")
            return extracted_text.splitlines() # Kembalikan sebagai list baris
        else:
            print("INFO: Tidak ada konten teks yang diekstrak oleh Ollama.")
            return []
            
    except ollama.ResponseError as e: # Menangkap error spesifik dari API Ollama
        print(f"ERROR: Ollama API error saat OCR: Status {e.status_code} - {e.error}")
        if e.status_code == 404: # Model not found
             print("PASTIKAN MODEL 'llama3.2-vision' TELAH DIUNDUH DI OLLAMA SERVER (ollama pull llama3.2-vision).")
        return []
    except Exception as e: # Menangkap error umum lainnya (misal, koneksi)
        error_type = type(e).__name__
        print(f"ERROR: Terjadi kesalahan ({error_type}) saat melakukan OCR dengan Ollama: {e}")
        if "Connection refused" in str(e) or "Failed to connect" in str(e) or "Max retries exceeded with url" in str(e):
            print("PASTIKAN OLLAMA SERVER BERJALAN DAN DAPAT DIAKSES.")
        return []

# Definisikan fungsi utama untuk mengekstrak teks dari gambar
def ekstrak_teks_dari_gambar(path_gambar: str, mesin_ocr: str = 'tesseract', opsi_praproses: dict = None, prompt_ollama: str = "get all the data from the image") -> list[str]:
    """
    Mengekstrak teks dari gambar menggunakan berbagai mesin OCR. 
    Jika 'ollama' dipilih, pra-pemrosesan gambar umumnya dilewati karena model vision modern
    seringkali bekerja lebih baik dengan gambar asli.

    Args:
        path_gambar (str): Path berkas ke gambar.
        mesin_ocr (str): Pilihan mesin OCR: 
                         'tesseract', 'easyocr', 'pyocr_tesseract', 'pyocr_cuneiform', 'ollama'.
                         Default ke 'tesseract'.
        opsi_praproses (dict, optional): Dictionary untuk mengontrol langkah-langkah pra-pemrosesan
                                         jika mesin_ocr BUKAN 'ollama'. Jika None, 
                                         DEFAULT_OPSI_PRAPROSES akan digunakan.
        prompt_ollama (str, optional): Prompt yang akan digunakan jika `mesin_ocr` adalah 'ollama'.
                                      Default: "get all the data from the image".

    Returns:
        list[str]: Sebuah list string, di mana setiap string adalah baris teks yang terdeteksi dan dibersihkan.
                   Mengembalikan list kosong jika terjadi error atau tidak ada teks terdeteksi.
    """
    final_options = DEFAULT_OPSI_PRAPROSES.copy()
    if opsi_praproses is not None:
        final_options.update(opsi_praproses)
    # Gunakan final_options untuk semua konfigurasi selanjutnya
    opsi_praproses = final_options

    try:
        # Initialize lines_result for storing list of strings
        lines_result: list[str] = []

        gambar_pil = Image.open(path_gambar)
        gambar_pil = set_dpi(gambar_pil, dpi_target=opsi_praproses['dpi_target'])  # Menggunakan opsi_praproses

        # Konversi PIL ke OpenCV (BGR)
        gambar_cv = np.array(gambar_pil)
        if gambar_cv.ndim == 3:  # Hanya konversi jika berwarna
            if gambar_cv.shape[2] == 3:  # RGB
                gambar_cv = cv2.cvtColor(gambar_cv, cv2.COLOR_RGB2BGR)
            elif gambar_cv.shape[2] == 4:  # RGBA
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
            processed_img = adjust_contrast(processed_img, alpha=contrast_opt.get('alpha', 1.5),
                                            beta=contrast_opt.get('beta', 0))

        # 5. Binarization
        bin_opt = opsi_praproses['binarization']
        invert_binarization = bin_opt.get('invert', True)  # Teks putih = 255

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
        if not invert_binarization:  # Jika teks hitam (0) dan bg putih (255)
            processed_img = cv2.bitwise_not(processed_img)  # Invert agar teks jadi putih

        # 6. Deskew
        if opsi_praproses.get('deskew'):
            processed_img = coba_pelurusan_kemiringan(processed_img)  # Harapannya ini bekerja dengan teks putih

        # 7. Remove Borders
        if opsi_praproses.get('remove_borders'):
            processed_img = remove_borders_cv(processed_img)  # Fungsi ini mengharapkan teks putih

        # 8. Crop Final
        if opsi_praproses.get('crop_final'):
            processed_img = crop_margin(processed_img)  # crop_margin juga harus bekerja dengan teks putih

        # 9. Resize for OCR
        # resize_for_ocr diaplikasikan pada gambar biner yang sudah diproses
        processed_img = resize_for_ocr(processed_img, min_height=opsi_praproses['min_ocr_height'])

        # Simpan gambar yang telah diproses untuk debugging jika perlu (opsional)
        # cv2.imwrite("processed_for_ocr.png", processed_img)

        # (Logika OCR akan ditambahkan/diperbarui di sini)
        
        # --- Pemilihan Mesin OCR ---
        if mesin_ocr == 'ollama':
            if ollama is None: # Cek lagi di sini untuk keamanan ganda
                print("ERROR: Pustaka Ollama tidak terinstal. Tidak dapat menggunakan 'ollama' sebagai mesin OCR.")
                return []

            # Untuk Ollama, pra-pemrosesan gambar yang kompleks biasanya tidak diperlukan atau bahkan
            # dapat menurunkan kualitas input untuk model vision. Model vision modern lebih suka gambar asli.
            # Kita akan menggunakan path_gambar asli. Jika path_gambar tidak valid (misal, dari stream),
            # gambar_pil (yang sudah di-set DPI) bisa disimpan ke file temporer.

            temp_ollama_input_path = None
            image_to_use_for_ollama = path_gambar

            if not os.path.exists(path_gambar):
                # Jika path_gambar asli tidak valid, coba simpan gambar_pil yang sudah ada
                temp_ollama_input_path = f"temp_ollama_ocr_input_{uuid.uuid4().hex}.png"
                try:
                    print(f"INFO: path_gambar asli ('{path_gambar}') tidak ditemukan. Menyimpan gambar dari memori ke '{temp_ollama_input_path}' untuk Ollama.")
                    gambar_pil.save(temp_ollama_input_path) # gambar_pil adalah Image.open(path_gambar) di awal
                    image_to_use_for_ollama = temp_ollama_input_path
                except Exception as e_save_temp:
                    print(f"ERROR: Gagal menyimpan gambar temporer untuk Ollama: {e_save_temp}")
                    return []
            
            lines_result = ocr_dengan_ollama(image_to_use_for_ollama, prompt_pengguna=prompt_ollama)
            
            if temp_ollama_input_path and os.path.exists(temp_ollama_input_path):
                try:
                    os.remove(temp_ollama_input_path)
                except Exception as e_rm_temp:
                    print(f"PERINGATAN: Gagal menghapus file temporer Ollama '{temp_ollama_input_path}': {e_rm_temp}")
            
        # --- Blok untuk mesin OCR lainnya (Tesseract, EasyOCR, dll.) yang menggunakan pra-pemrosesan ---
        else:
            # Untuk mesin OCR tradisional, gunakan gambar yang telah diproses (`processed_img`)
            gambar_untuk_ocr = processed_img 

            if mesin_ocr == 'easyocr':
                if easyocr is None:
                    print("Error: easyocr tidak terinstal. Install dengan 'pip install easyocr'.")
                    return []

                reader = easyocr.Reader(['id', 'en'], gpu=opsi_praproses['easyocr_gpu'])
                raw_results = reader.readtext(gambar_untuk_ocr, detail=1, paragraph=False)

                if not raw_results:
                    return []

                text_blocks = []
                for (bbox, text, conf) in raw_results:
                    if text.strip():
                        text_blocks.append({
                            'text': text,
                            'x_min': int(bbox[0][0]),
                            'y_min': int(bbox[0][1])
                        })

                text_blocks.sort(key=lambda b: (b['y_min'], b['x_min']))

                reconstructed_lines = []
                current_line_elements = []
                Y_TOLERANCE = 10

                for block in text_blocks:
                    if not current_line_elements:
                        current_line_elements.append(block)
                    else:
                        last_block_y_min = current_line_elements[-1]['y_min']
                        if abs(block['y_min'] - last_block_y_min) <= Y_TOLERANCE:
                            current_line_elements.append(block)
                        else:
                            line_text = ' '.join([elem['text'] for elem in current_line_elements])
                            cleaned_line = bersihkan_satu_baris(line_text)  # Use new cleaner
                            if cleaned_line:
                                reconstructed_lines.append(cleaned_line)
                            current_line_elements = [block]

                if current_line_elements:
                    line_text = ' '.join([elem['text'] for elem in current_line_elements])
                    cleaned_line = bersihkan_satu_baris(line_text)  # Use new cleaner
                    if cleaned_line:
                        reconstructed_lines.append(cleaned_line)

                lines_result = reconstructed_lines

            elif mesin_ocr == 'tesseract':
                pil_img_for_tesseract = Image.fromarray(gambar_untuk_ocr)
                data = pytesseract.image_to_data(
                    pil_img_for_tesseract,
                    lang=opsi_praproses.get('pyocr_lang', 'ind+eng'),
                    config=opsi_praproses['tesseract_config'],
                    output_type=Output.DICT
                )

                lines_data = {}
                n_boxes = len(data['level'])
                for i in range(n_boxes):
                    if data['level'][i] == 5:
                        word_text = data['text'][i].strip()
                        if word_text:
                            line_key = (data['page_num'][i], data['block_num'][i], data['par_num'][i], data['line_num'][i])
                            if line_key not in lines_data:
                                lines_data[line_key] = []
                            lines_data[line_key].append(word_text)

                reconstructed_lines = []
                sorted_line_keys = sorted(lines_data.keys())

                for key in sorted_line_keys:
                    line_text = ' '.join(lines_data[key])
                    cleaned_line = bersihkan_satu_baris(line_text)  # Use new cleaner
                    if cleaned_line:
                        reconstructed_lines.append(cleaned_line)

                lines_result = reconstructed_lines

            elif mesin_ocr == 'pyocr_tesseract':
                if pyocr is None:
                    print("Error: pyocr tidak terinstal. Install dengan 'pip install pyocr'.")
                    return []
                tools = pyocr.get_available_tools()
                if not tools:
                    print("Error: Tidak ada tool PyOCR yang tersedia.")
                    return []

                tool_tesseract = None
                for tool_item in tools:
                    if 'Tesseract' in tool_item.get_name():
                        tool_tesseract = tool_item
                        break

                if tool_tesseract is None:
                    print("Error: Tool Tesseract untuk PyOCR tidak ditemukan.")
                    return []

                pil_img_for_pyocr = Image.fromarray(gambar_untuk_ocr)
                raw_text_output = tool_tesseract.image_to_string(
                    pil_img_for_pyocr,
                    lang=opsi_praproses['pyocr_lang'],
                    builder=pyocr.builders.TextBuilder()
                )
                raw_lines = raw_text_output.splitlines()
                cleaned_lines = [bersihkan_satu_baris(line) for line in raw_lines]
                lines_result = [line for line in cleaned_lines if line]  # Filter empty lines

            elif mesin_ocr == 'pyocr_cuneiform':
                if pyocr is None:
                    print("Error: pyocr tidak terinstal. Install dengan 'pip install pyocr'.")
                    return []
                tools = pyocr.get_available_tools()
                if not tools:
                    print("Error: Tidak ada tool PyOCR yang tersedia.")
                    return []

                tool_cuneiform = None
                for tool_item in tools:
                    if 'Cuneiform' in tool_item.get_name().lower():
                        tool_cuneiform = tool_item
                        break

                if tool_cuneiform is None:
                    print("Error: Tool Cuneiform untuk PyOCR tidak ditemukan.")
                    return []

                pil_img_for_pyocr = Image.fromarray(gambar_untuk_ocr)
                raw_text_output = tool_cuneiform.image_to_string(
                    pil_img_for_pyocr,
                    lang=opsi_praproses['pyocr_lang'],
                    builder=pyocr.builders.TextBuilder()
                )
                raw_lines = raw_text_output.splitlines()
                cleaned_lines = [bersihkan_satu_baris(line) for line in raw_lines]
                lines_result = [line for line in cleaned_lines if line]  # Filter empty lines

            else:
                print(f"Mesin OCR '{mesin_ocr}' tidak dikenal.")
                return []

        return lines_result  # Each branch now populates lines_result

    except FileNotFoundError:  # Specific exception for file not found
        print(f"ERROR: File gambar tidak ditemukan di path: {path_gambar}")
        return []
    except Exception as e:
        print(f"Error OCR atau pra-pemrosesan: {e}")
        return []