# Modul PRABU - Prediksi Risiko Kredit dengan Incremental Learning

## 1. Gambaran Umum

Modul PRABU ini telah ditingkatkan untuk menyediakan fungsionalitas prediksi risiko kredit menggunakan pendekatan Machine Learning (ML). Fitur utama dari versi ini adalah kemampuan **pembelajaran inkremental (incremental learning)**, yang memungkinkan model untuk terus belajar dan beradaptasi seiring waktu dengan masuknya data historis baru dan data dari berbagai sektor industri.

Tujuan utamanya adalah untuk memprediksi kategori risiko kredit (`Low`, `Medium`, `High`) untuk sebuah perusahaan berdasarkan data keuangan dan informasi sektornya.

## 2. Komponen Utama

*   **`incremental_model_trainer.py`**:
    *   Skrip inti yang bertanggung jawab untuk seluruh siklus hidup model ML.
    *   Fungsi untuk memuat dataset dari file CSV.
    *   Fungsi untuk melakukan pra-pemrosesan data, termasuk menangani nilai yang hilang (NaN), melakukan scaling pada fitur numerik, dan one-hot encoding pada fitur kategorikal seperti 'Sektor'.
    *   Fungsi `train_initial_model()`: Untuk melatih model dari awal menggunakan batch data pertama.
    *   Fungsi `update_model_incrementally()`: Untuk memperbarui model yang sudah ada dengan data baru (data historis atau data dari sektor baru) menggunakan teknik `partial_fit`.
    *   Menyimpan dan memuat artefak model (model itu sendiri, preprocessor, dan daftar kelas target) ke/dari direktori `trained_models/`.

*   **`ml_credit_risk_predictor.py`**:
    *   Modul yang menyediakan fungsi `predict_credit_risk_ml(financial_data_dict, sector)` untuk melakukan prediksi pada data input baru.
    *   Memuat model dan preprocessor yang sudah dilatih dari direktori `trained_models/`.
    *   Mengembalikan prediksi kategori risiko beserta probabilitas untuk setiap kelas.

*   **`datasets/`**:
    *   Direktori ini berisi contoh dataset sintetis dalam format CSV.
    *   Setiap file CSV merepresentasikan data untuk satu perusahaan dalam satu sektor tertentu (misalnya, `tambang_jaya_pertambangan.csv`).
    *   Dataset ini digunakan untuk mendemonstrasikan alur kerja pelatihan dan prediksi.

*   **`trained_models/`**:
    *   Direktori ini secara otomatis dibuat oleh `incremental_model_trainer.py`.
    *   Berisi file-file berikut setelah pelatihan:
        *   `incremental_risk_model.joblib`: Model `SGDClassifier` yang telah dilatih.
        *   `preprocessor.joblib`: Objek `ColumnTransformer` (dari scikit-learn) yang digunakan untuk pra-pemrosesan data.
        *   `classes.npy`: Array NumPy berisi daftar kelas target unik (misalnya, ['High', 'Low', 'Medium']) yang dipelajari model.

## 3. Model ML yang Digunakan

Implementasi saat ini menggunakan `SGDClassifier` dari pustaka `scikit-learn`. Model ini dipilih karena dukungannya terhadap metode `partial_fit`, yang memungkinkannya untuk dilatih secara inkremental tanpa perlu memuat seluruh dataset setiap kali ada data baru.

Model ini dikonfigurasi untuk:
*   Menggunakan `loss='log_loss'` untuk memungkinkan output probabilitas.
*   `class_weight='balanced'` untuk menangani potensi ketidakseimbangan kelas dalam data.
*   `warm_start=True` agar pemanggilan `fit` atau `partial_fit` berikutnya melanjutkan dari state sebelumnya.

## 4. Struktur Dataset yang Diharapkan

Model dan preprocessor mengharapkan data input dalam format tabular (misalnya, dari file CSV) dengan kolom-kolom berikut:

*   **Fitur Umum**: Serangkaian rasio keuangan standar atau metrik yang relevan untuk semua sektor (misalnya, `CurrentRatio`, `DebtToEquityRatio`, `NetProfitMargin`, dll.).
*   **Fitur Spesifik Sektor**: Kolom-kolom yang hanya relevan untuk sektor tertentu (misalnya, `Mining_ProductionVolume` untuk Pertambangan, `Construction_OrderBookValue` untuk Konstruksi).
    *   Untuk data dari sektor tertentu, fitur spesifik sektor lain yang tidak relevan harus diisi dengan nilai kosong atau `NaN`. Preprocessor akan menangani ini dengan mengimputasinya (misalnya, menjadi 0).
*   **`Sektor` (Kategorikal)**: Kolom teks yang menunjukkan sektor industri perusahaan (misalnya, "Pertambangan", "Konstruksi", "Agro"). Ini akan di-one-hot-encode oleh preprocessor.
*   **`RiskCategory` (Target)**: Kolom target untuk pelatihan, berisi label kategori risiko seperti "Low", "Medium", atau "High".
*   Kolom identifikasi lainnya seperti `UniqueID`, `NamaPerusahaan`, `PeriodeTahun`, `PeriodeKuartal` dapat ada dalam CSV tetapi akan diabaikan selama pelatihan model (sesuai konfigurasi `remainder='drop'` pada `ColumnTransformer`).

Lihat file CSV di direktori `PrabuModule/datasets/` untuk contoh konkret.

## 5. Alur Kerja Pelatihan dan Pembaruan

### a. Pelatihan Awal
1.  **Siapkan Data Awal**: Kumpulkan data dari satu atau beberapa sektor/periode awal dalam format CSV seperti yang dijelaskan di atas. Letakkan di subdirektori dalam `PrabuModule/datasets/` atau sesuaikan path di skrip.
2.  **Jalankan Skrip Pelatih**: Eksekusi `python PrabuModule/incremental_model_trainer.py`.
    *   Skrip contoh `if __name__ == '__main__':` akan memuat data, membaginya, dan memanggil `train_initial_model()`.
    *   Ini akan membuat dan menyimpan `incremental_risk_model.joblib`, `preprocessor.joblib`, dan `classes.npy` di `PrabuModule/trained_models/`.
    *   Pastikan untuk menghapus file model/preprocessor lama jika Anda ingin melatih ulang dari awal pada data yang berbeda. Skrip contoh sudah melakukan ini.

### b. Pembaruan Inkremental
1.  **Siapkan Data Baru**: Kumpulkan data baru (bisa data historis dari sektor yang sudah ada, atau data dari sektor yang benar-benar baru). Pastikan formatnya konsisten.
2.  **Panggil Fungsi Pembaruan**:
    *   Muat model dan preprocessor yang ada menggunakan `joblib.load()`.
    *   Muat data baru ke dalam DataFrame pandas.
    *   Panggil fungsi `incremental_model_trainer.update_model_incrementally(df_new_data, model, preprocessor)`.
    *   Ini akan memperbarui model menggunakan `partial_fit` dan menyimpan kembali model yang telah diperbarui.
    *   Contoh pemanggilan ini juga ada di bagian `if __name__ == '__main__':` pada `incremental_model_trainer.py`.

## 6. Cara Melakukan Prediksi

### a. Melalui REST API
Setelah modul ini terintegrasi dengan layanan FastAPI (`app/services/prabu_service.py` dan `app/routers/prabu_router.py`), prediksi dapat dilakukan dengan mengirimkan request ke endpoint `/prabu/analyze`. Request body harus menyertakan data keuangan (`data_t`) dan `sector`.

### b. Langsung dari Modul Python
Anda dapat menggunakan fungsi `predict_credit_risk_ml` dari modul `PrabuModule.ml_credit_risk_predictor`:

```python
from PrabuModule import ml_credit_risk_predictor
import importlib

# Reload untuk memastikan model & preprocessor terbaru dari disk dimuat (penting jika baru saja diupdate)
importlib.reload(ml_credit_risk_predictor)
ml_credit_risk_predictor._load_resources()


# Contoh data input (dictionary fitur, tanpa target)
data_sample = {
    'CurrentRatio': 1.8, 
    'DebtToEquityRatio': 0.6, 
    'NetProfitMargin': 0.12,
    # ... (fitur umum lainnya)
    'Mining_ProductionVolume': 4500, # Fitur spesifik jika sektornya Pertambangan
    # ... (fitur spesifik sektor lainnya jika ada)
}
sektor_sample = 'Pertambangan'

hasil_prediksi = ml_credit_risk_predictor.predict_credit_risk_ml(data_sample, sektor_sample)

if hasil_prediksi['error']:
    print(f"Error prediksi: {hasil_prediksi['error']}")
else:
    print(f"Kategori Risiko: {hasil_prediksi['risk_category']}")
    print(f"Probabilitas: {hasil_prediksi['probabilities']}")
```
Pastikan `ml_credit_risk_predictor.py` dapat menemukan file model dan preprocessor yang sudah dilatih di `PrabuModule/trained_models/`.

## 7. Catatan dan Pengembangan Lebih Lanjut

*   **Kualitas Data**: Kinerja model sangat bergantung pada kualitas dan representativitas data pelatihan. Dataset sintetis yang digunakan saat ini hanya untuk demonstrasi. Untuk penggunaan nyata, diperlukan data keuangan riil yang beragam dan akurat.
*   **Evaluasi Model**: Laporan klasifikasi sederhana disediakan. Untuk evaluasi yang lebih robust, pertimbangkan metrik lain, validasi silang (jika melatih ulang secara periodik), dan pemantauan kinerja model seiring waktu.
*   **Hyperparameter Tuning**: Parameter `SGDClassifier` (seperti `alpha`, `learning_rate`, `eta0`) belum dioptimalkan. Tuning dapat meningkatkan kinerja.
*   **Fitur Historis Eksplisit**: Saat ini, data historis digunakan untuk memperbarui model secara umum. Untuk menangkap tren waktu secara lebih eksplisit, pertimbangkan pembuatan fitur berbasis waktu (misalnya, perubahan rasio YoY, rata-rata bergerak).
*   **Model Alternatif**: Meskipun `SGDClassifier` baik untuk incremental learning, model lain seperti pohon keputusan yang diupdate (misalnya, dengan melatih ulang pada data gabungan secara periodik) atau ensemble yang lebih canggih bisa dieksplorasi.
*   **Penanganan Drift Konsep**: Jika hubungan antara fitur dan risiko kredit berubah secara signifikan dari waktu ke waktu (concept drift), model mungkin perlu dilatih ulang sepenuhnya atau menggunakan teknik adaptasi drift yang lebih canggih.
```
