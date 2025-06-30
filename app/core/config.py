import os
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

# Tentukan base directory proyek (root)
# Ini mengasumsikan config.py ada di app/core/config.py
# Jadi, ../../ akan mengarah ke root direktori proyek
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # Informasi Aplikasi Dasar
    APP_NAME: str = "SATRIA"
    API_VERSION: str = "v1"
    DEBUG_MODE: bool = False # Default ke False untuk produksi

    # Path Direktori (relatif terhadap root proyek)
    # Ini bisa berguna jika layanan perlu mengakses file-file ini secara langsung.
    # Namun, untuk aplikasi yang siap cloud, path ini mungkin tidak relevan
    # atau perlu diubah menjadi URL GCS/S3 atau mekanisme lain.
    OUTPUT_DIR: Path = PROJECT_ROOT_DIR / "Output"
    TRAIN_DOCUMENTS_DIR: Path = PROJECT_ROOT_DIR / "train_documents"
    # Direktori untuk file upload temporer Sarana (jika ingin dikonfigurasi terpusat)
    # Jika tidak, router Sarana akan membuatnya secara lokal (temp_sarana_uploads)
    SARANA_TEMP_UPLOAD_DIR: Path = PROJECT_ROOT_DIR / "temp_sarana_uploads"

    # Konfigurasi Layanan Setia (Contoh)
    SETIA_GCS_BUCKET_NAME: Optional[str] = None # Nama bucket GCS untuk risk_data.json Setia
    # GCP_PROJECT: Optional[str] = None # Sudah otomatis terdeteksi di Cloud Functions/Run
    # GCP_LOCATION: str = "asia-southeast1" # Lokasi default untuk Vertex AI

    # Konfigurasi Database (Contoh jika diperlukan nanti)
    # DATABASE_URL: Optional[str] = "sqlite:///./test.db" 
    # POSTGRES_USER: Optional[str] = None
    # POSTGRES_PASSWORD: Optional[str] = None
    # POSTGRES_SERVER: Optional[str] = None
    # POSTGRES_PORT: Optional[str] = "5432"
    # POSTGRES_DB: Optional[str] = None
    
    # Untuk memuat variabel dari file .env
    # Pydantic-settings akan otomatis mencoba memuat dari file .env di direktori yang sama
    # dengan file settings ini, atau dari path yang ditentukan di Config.
    class Config:
        env_file = ".env" # Nama file environment default
        env_file_encoding = 'utf-8'
        extra = 'ignore' # Abaikan variabel lingkungan ekstra yang tidak didefinisikan di Settings

# Buat instance settings yang akan diimpor oleh bagian lain aplikasi
settings = Settings()

# Pastikan direktori yang dikonfigurasi ada (opsional, tergantung kebutuhan)
# Ini mungkin lebih baik dilakukan saat startup aplikasi di main.py atau oleh layanan terkait.
# Contoh:
# os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
# os.makedirs(settings.TRAIN_DOCUMENTS_DIR, exist_ok=True)
# os.makedirs(settings.SARANA_TEMP_UPLOAD_DIR, exist_ok=True)

if __name__ == "__main__":
    # Untuk menguji pemuatan konfigurasi
    print(f"App Name: {settings.APP_NAME}")
    print(f"API Version: {settings.API_VERSION}")
    print(f"Debug Mode: {settings.DEBUG_MODE}")
    print(f"Output Directory: {settings.OUTPUT_DIR}")
    print(f"Train Documents Directory: {settings.TRAIN_DOCUMENTS_DIR}")
    print(f"Sarana Temp Upload Dir: {settings.SARANA_TEMP_UPLOAD_DIR}")
    print(f"Setia GCS Bucket: {settings.SETIA_GCS_BUCKET_NAME}") # Akan None jika tidak di .env

    # Contoh membuat file .env untuk diuji:
    # echo "DEBUG_MODE=True" > .env
    # echo "SETIA_GCS_BUCKET_NAME=my-setia-bucket" >> .env
    # Lalu jalankan python app/core/config.py
    # Jangan lupa hapus .env setelah pengujian jika tidak ingin ada di repo.

    # Pastikan direktori dibuat untuk pengujian jika blok ini dijalankan
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.TRAIN_DOCUMENTS_DIR, exist_ok=True)
    os.makedirs(settings.SARANA_TEMP_UPLOAD_DIR, exist_ok=True)
    print(f"Direktori Output ({settings.OUTPUT_DIR}) seharusnya sudah ada/dibuat.")
    print(f"Direktori Train Docs ({settings.TRAIN_DOCUMENTS_DIR}) seharusnya sudah ada/dibuat.")
    print(f"Direktori Sarana Temp ({settings.SARANA_TEMP_UPLOAD_DIR}) seharusnya sudah ada/dibuat.")
