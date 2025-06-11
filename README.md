# SARANA Module: Ekstraksi Data Keuangan Otomatis dari Dokumen

## Deskripsi
SARANA (Sistem Analisis dan Ekstraksi Otomatis Narasi & Angka) adalah modul Python untuk ekstraksi data keuangan dari dokumen PDF, gambar, dan teks menggunakan pipeline OCR & NLP yang dioptimalkan. Cocok untuk analisis laporan keuangan, audit, dan riset data finansial.

## Tujuan
- Mengotomatisasi ekstraksi kata kunci dan angka keuangan dari dokumen tidak terstruktur.
- Mendukung berbagai format input: PDF, gambar (JPG/PNG), dan teks.
- Menyediakan pipeline pra-pemrosesan gambar dan pilihan engine OCR.
- Hasil parsing rapi, siap analisis, dan mudah dievaluasi.

## Fitur Utama
- **Pipeline pra-pemrosesan gambar**: grayscale, denoising, sharpening, thresholding adaptif, deskew, border removal, contrast adjustment, resize (DPI 300/600), preset profile.
- **Opsi engine OCR**: Tesseract (pytesseract) & EasyOCR.
- **Pembersihan hasil teks**: normalisasi spasi, penghapusan karakter aneh, dsb.
- **Ekstraksi kata kunci keuangan**: mendukung bahasa Indonesia & Inggris, regex robust untuk layout tabel/teks tidak terstruktur.
- **Integrasi dengan pipeline NLP**: tokenisasi, stemming, dsb.
- **Output JSON siap analisis**.

## Alur Kerja
1. **Input**: PDF/gambar/teks →
2. **Pra-pemrosesan gambar** (jika input gambar) →
3. **OCR** (pilih engine) →
4. **Pembersihan teks** →
5. **Ekstraksi kata kunci & angka keuangan** →
6. **Output JSON**

## Instalasi
1. **Clone repo & masuk folder**
   ```bash
   git clone https://github.com/astranauts/SARANA.git
   cd SARANA
   ```
2. **Install dependensi Python**
   ```bash
   pip install -r requirements.txt
   ```
3. **Install Tesseract (untuk macOS/Linux/Windows)**
   - macOS: `brew install tesseract`
   - Ubuntu: `sudo apt-get install tesseract-ocr`
   - Windows: [Download installer](https://github.com/tesseract-ocr/tesseract)
4. **Install resource NLTK** (jika error)
   ```python
   import nltk
   nltk.download('punkt')
   ```

## Preset Pipeline Pra-pemrosesan
- **default**: grayscale, denoise, sharpen, threshold, deskew, border removal, contrast, resize (DPI 300)
- **fast**: grayscale, threshold, resize (DPI 150)
- **highres**: semua fitur, resize (DPI 600)
- **custom**: atur sendiri via argumen fungsi

## Contoh Penggunaan
```python
from SaranaModule import parser_gambar
# Ekstraksi dari gambar dengan preset 'default' dan engine 'tesseract'
text = parser_gambar.ekstrak_teks_gambar('file.jpg', preset='default', engine='tesseract')

from SaranaModule import pengekstrak_kata_kunci
# Ekstraksi kata kunci keuangan
hasil = pengekstrak_kata_kunci.ekstrak_kata_kunci(text)
```

## Tips & Troubleshooting
- **Error Tesseract not found**: pastikan sudah install & path tesseract dikenali OS.
- **Error NLTK resource**: jalankan `nltk.download('punkt')` di Python shell.
- **Hasil OCR kurang akurat**: coba preset lain, atau engine easyocr.
- **Ekstraksi tabel/angka tidak rapi**: gunakan pipeline pra-pemrosesan lengkap & cek daftar kata kunci.

## Pengembangan Lanjutan
- Integrasi ekstraksi tabel otomatis (Camelot, Tabula, dsb).
- Peningkatan post-processing angka (normalisasi ribuan/desimal).
- Penambahan preset pipeline & auto-tuning.
- Evaluasi akurasi ekstraksi (lihat `evaluasi_akurasi.py`).

## Lisensi
MIT License © 2025 The Beyonders

## Kontak & Kontribusi
- Tim The Beyonders
