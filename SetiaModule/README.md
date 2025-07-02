# SETIA Module (System for External Threat Identification and Analysis)

## Deskripsi

SETIA Module adalah komponen pendukung penting dalam aplikasi SATRIA yang berfokus pada pemantauan dan analisis data eksternal untuk mendeteksi potensi risiko reputasi atau keuangan yang mungkin tidak tercakup dalam dokumen keuangan internal. Modul ini secara proaktif mencari informasi dari berbagai sumber publik di internet, seperti portal berita, media sosial, forum diskusi, dan platform online lainnya.

Tujuan utama SETIA Module adalah untuk memperkaya profil risiko calon nasabah atau nasabah yang sudah ada dengan informasi terkini dan relevan dari dunia luar. Ini membantu PT SANF mendapatkan gambaran yang lebih holistik dan mengantisipasi potensi masalah yang dapat mempengaruhi kemampuan bayar atau integritas nasabah.

## Fungsi Utama

1.  **Konfigurasi Sumber Data:** Memungkinkan pengguna untuk mengkonfigurasi sumber-sumber data eksternal yang ingin dipantau (misalnya, daftar situs berita tertentu, kata kunci untuk pencarian di media sosial).
2.  **Pengumpulan Data (Data Crawling/Scraping):**
    *   Secara otomatis mengumpulkan data dari sumber-sumber yang telah ditentukan.
    *   Menggunakan teknik *web crawling* dan *web scraping* untuk mengekstrak informasi yang relevan.
3.  **Pemrosesan Teks dan Analisis Sentimen:**
    *   Menerapkan teknik Natural Language Processing (NLP) untuk memproses teks yang dikumpulkan.
    *   Melakukan analisis sentimen untuk menentukan apakah pemberitaan atau diskusi mengenai entitas tertentu (calon nasabah/nasabah) cenderung positif, negatif, atau netral.
4.  **Deteksi Entitas dan Topik:**
    *   Mengidentifikasi penyebutan nama perusahaan, individu terkait, atau topik-topik spesifik yang relevan dengan risiko keuangan atau reputasi (misalnya, keterlibatan dalam kasus hukum, berita negatif signifikan, kesulitan keuangan yang diberitakan).
5.  **Peringatan Dini (Alerting):**
    *   Menghasilkan peringatan atau notifikasi jika terdeteksi adanya informasi negatif atau berisiko tinggi yang signifikan terkait dengan entitas yang dipantau.
6.  **Integrasi dengan Profil Risiko:**
    *   Menyediakan ringkasan temuan atau tautan ke informasi relevan yang dapat diintegrasikan ke dalam profil risiko nasabah secara keseluruhan.
    *   Membantu analis kredit dalam mempertimbangkan faktor-faktor eksternal saat melakukan evaluasi.
7.  **Visualisasi Data (Opsional):** Dapat menyajikan temuan dalam bentuk dasbor atau laporan visual untuk memudahkan pemahaman tren atau isu penting.

## Teknologi yang Digunakan

*   **Web Crawling/Scraping Frameworks:** Alat atau pustaka untuk mengotomatiskan pengumpulan data dari website.
    *   Contoh: Scrapy, BeautifulSoup, Selenium.
*   **Natural Language Processing (NLP):** Teknik untuk analisis teks, termasuk analisis sentimen, *Named Entity Recognition* (NER), dan *Topic Modeling*.
    *   Contoh pustaka: spaCy, NLTK, VaderSentiment, model-model transformer.
*   **AI Grounded Search:** Mengacu pada penggunaan teknik AI untuk meningkatkan relevansi dan efektivitas pencarian informasi. Ini bisa melibatkan penggunaan *embeddings* untuk pencarian semantik atau model klasifikasi untuk menyaring konten yang relevan.
*   **Sistem Basis Data:** Untuk menyimpan data yang dikumpulkan dan hasil analisisnya (misalnya, Elasticsearch untuk pencarian teks, basis data relasional atau NoSQL untuk data terstruktur).
*   **Platform Pemrosesan Data (Opsional):** Untuk menangani volume data yang besar, mungkin diperlukan platform seperti Apache Spark atau sistem antrian pesan (message queue) seperti Kafka.

## Manfaat

*   **Deteksi Risiko Dini:** Mengidentifikasi potensi risiko reputasi atau keuangan sebelum menjadi masalah besar atau terungkap melalui jalur formal.
*   **Penilaian Risiko Komprehensif:** Melengkapi analisis risiko berbasis dokumen internal dengan wawasan dari sumber eksternal.
*   **Pengambilan Keputusan yang Lebih Informatif:** Memberikan konteks tambahan kepada analis kredit.
*   **Perlindungan Reputasi:** Membantu PT SANF menghindari asosiasi dengan entitas yang memiliki risiko reputasi tinggi.
*   **Pemantauan Berkelanjutan:** Dapat digunakan untuk memantau nasabah yang sudah ada (ongoing monitoring) terhadap perubahan kondisi eksternal.

## Cara Kerja (Alur Umum)

1.  Analis atau sistem mengidentifikasi entitas (misalnya, nama perusahaan calon nasabah) yang perlu dipantau.
2.  SETIA Module melakukan pencarian dan pengumpulan data dari sumber-sumber eksternal yang telah dikonfigurasi terkait entitas tersebut.
3.  Data teks yang dikumpulkan diproses menggunakan NLP: pembersihan teks, analisis sentimen, identifikasi entitas dan topik.
4.  Sistem mengevaluasi sentimen dan relevansi informasi yang ditemukan.
5.  Jika terdeteksi risiko signifikan (misalnya, berita negatif yang kuat, sentimen sangat negatif), sistem dapat menghasilkan peringatan.
6.  Hasil analisis dan tautan ke sumber informasi relevan disediakan untuk analis kredit sebagai bahan pertimbangan tambahan.

## Ketergantungan

*   Akses ke internet dan kemampuan untuk melakukan *crawling/scraping* (memperhatikan robots.txt dan ketentuan layanan situs sumber).
*   Kualitas analisis sangat bergantung pada kualitas dan relevansi sumber data yang dipantau.
*   Perlu penyesuaian dan pemeliharaan berkelanjutan terhadap *crawler* karena struktur website sering berubah.
*   Pertimbangan etika dan privasi dalam pengumpulan dan penggunaan data dari sumber publik.
