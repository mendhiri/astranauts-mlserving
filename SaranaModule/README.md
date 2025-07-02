# SARANA Module (SATRIA Document Processing)

## Deskripsi

SARANA Module adalah komponen inti dari aplikasi SATRIA yang berfokus pada transformasi dokumen keuangan menjadi data terstruktur yang siap untuk dianalisis. Modul ini dirancang untuk menangani berbagai jenis dokumen yang diajukan oleh pengguna, seperti laporan keuangan, laporan laba rugi, neraca, rekening koran, dan dokumen pendukung lainnya.

Tujuan utama SARANA Module adalah untuk mengotomatisasi proses ekstraksi data dari dokumen, yang secara tradisional memakan waktu dan rentan terhadap kesalahan jika dilakukan secara manual. Dengan data yang terstruktur dan akurat, proses analisis keuangan selanjutnya dapat dilakukan dengan lebih efisien dan konsisten.

## Fungsi Utama

1.  **Penerimaan Dokumen:** Menerima input dokumen keuangan dari pengguna dalam berbagai format (misalnya, PDF, JPG, PNG).
2.  **Pemrosesan Awal Dokumen:** Melakukan pra-pemrosesan pada dokumen seperti peningkatan kualitas gambar, segmentasi halaman, dan deteksi tata letak.
3.  **Ekstraksi Teks dengan OCR:** Menggunakan teknologi *Optical Character Recognition* (OCR) untuk mengubah gambar teks dalam dokumen menjadi teks digital yang dapat dibaca mesin.
4.  **Pemahaman Konten dengan NLP:** Menerapkan teknik *Natural Language Processing* (NLP) untuk memahami struktur dan makna dari teks yang telah diekstraksi. Ini termasuk:
    *   Identifikasi entitas penting (misalnya, nama perusahaan, tanggal, item baris keuangan).
    *   Klasifikasi jenis dokumen.
    *   Ekstraksi tabel dan data tabular.
    *   Normalisasi data (misalnya, format tanggal, angka).
5.  **Strukturisasi Data:** Mengubah data yang diekstraksi menjadi format terstruktur (misalnya, JSON, CSV, atau format basis data) yang dapat dengan mudah digunakan oleh modul lain, khususnya PRABU Module untuk analisis risiko kredit.
6.  **Validasi Data (Opsional):** Dapat mencakup langkah-langkah validasi dasar untuk memastikan kualitas data yang diekstraksi.

## Teknologi yang Digunakan

*   **Optical Character Recognition (OCR):** Teknologi untuk mengubah berbagai jenis dokumen, seperti dokumen kertas yang dipindai, file PDF, atau gambar yang diambil oleh kamera digital menjadi data yang dapat diedit dan dicari. Contoh *engine* OCR yang mungkin digunakan termasuk Tesseract, Google Cloud Vision AI, AWS Textract, atau Azure Computer Vision.
*   **Natural Language Processing (NLP):** Cabang dari kecerdasan buatan yang berkaitan dengan interaksi antara komputer dan bahasa manusia. Teknik NLP digunakan untuk menganalisis, memahami, dan menghasilkan bahasa manusia secara bermakna. Pustaka NLP yang umum digunakan termasuk spaCy, NLTK, Stanford CoreNLP, atau model berbasis transformer seperti BERT.

## Manfaat

*   **Efisiensi:** Mengurangi waktu dan upaya manual yang diperlukan untuk memasukkan dan memproses data keuangan.
*   **Akurasi:** Meningkatkan akurasi data dengan mengurangi kesalahan manusia dalam entri data.
*   **Skalabilitas:** Mampu memproses volume dokumen yang besar secara konsisten.
*   **Konsistensi:** Memastikan format data yang seragam untuk analisis lebih lanjut.
*   **Dasar untuk Analisis Lanjutan:** Menyediakan data input yang berkualitas tinggi untuk model prediktif di PRABU Module.

## Cara Kerja (Alur Umum)

1.  Pengguna mengunggah dokumen keuangan melalui antarmuka aplikasi.
2.  SARANA Module menerima dokumen dan memulai pipeline pemrosesan.
3.  Dokumen dipra-pemrosesan untuk meningkatkan kualitas ekstraksi.
4.  Mesin OCR mengekstrak teks mentah dari dokumen.
5.  Algoritma NLP menganalisis teks mentah untuk mengidentifikasi dan mengekstrak informasi keuangan yang relevan.
6.  Informasi yang diekstraksi distrukturkan ke dalam format output yang ditentukan.
7.  Data terstruktur disimpan dan/atau diteruskan ke PRABU Module.

## Ketergantungan

*   Modul ini mungkin memerlukan konfigurasi atau pelatihan model OCR dan NLP tergantung pada kompleksitas dan variasi dokumen yang akan diproses.
*   Kualitas output sangat bergantung pada kualitas dokumen input.
