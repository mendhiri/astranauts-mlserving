# Astranauts API - Integrated Risk Analysis Services

Astranauts API adalah layanan analisis risiko terintegrasi yang terdiri dari tiga modul utama:

- **PRABU** - Analisis Risiko Keuangan & Credit Scoring
- **SARANA** - OCR & NLP untuk Pemrosesan Dokumen
- **SETIA** - Analisis Sentimen & Intelijen Risiko

## 🚀 Quick Start

### Prasyarat

1. Python 3.11+
2. Google Cloud Project dengan billing diaktifkan
3. Tesseract OCR (untuk modul Sarana)

### Instalasi Lokal

1. **Clone repository**
   ```bash
   git clone https://github.com/raihanpka/astranauts.git
   cd astranauts
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file dengan konfigurasi Anda
   ```

4. **Setup Google Cloud OAuth2**
   - Download `credentials.json` dari Google Cloud Console
   - Letakkan di root directory project

5. **Jalankan API server**
   ```bash
   # Development
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   
   # Production
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

### Deployment ke Cloud Run

1. **Setup Google Cloud SDK**
   ```bash
   gcloud auth login
   gcloud config set project astranauts-461014
   ```

2. **Deploy menggunakan script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

## 📚 API Documentation

Setelah server berjalan, akses dokumentasi API di:
- **Interactive Docs**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## 🎯 API Endpoints

### Base URLs

```javascript
const API_CONFIG = {
  BASE_URL: {
    development: "http://localhost:8080",
    production: "https://astranauts-api-XXXXX.run.app",
  },
  
  MODULE_URLS: {
    PRABU: "/api/v1/prabu",
    SARANA: "/api/v1/sarana", 
    SETIA: "/api/v1/setia",
  }
};
```

### PRABU - Credit Scoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/prabu/health` | GET | Health check |
| `/api/v1/prabu/calculate` | POST | Comprehensive financial analysis |
| `/api/v1/prabu/altman-z` | POST | Altman Z-Score analysis |
| `/api/v1/prabu/m-score` | POST | Beneish M-Score analysis |
| `/api/v1/prabu/metrics` | POST | Financial ratios and metrics |

### SARANA - OCR & NLP

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/sarana/health` | GET | Health check |
| `/api/v1/sarana/document/parse` | POST | Parse financial documents |
| `/api/v1/sarana/ocr/upload` | POST | OCR file upload |
| `/api/v1/sarana/extract` | POST | Extract structured data |

### SETIA - Sentiment Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/setia/health` | GET | Health check |
| `/api/v1/setia/sentiment` | POST | Comprehensive sentiment analysis |
| `/api/v1/setia/news` | POST | News monitoring |
| `/api/v1/setia/external-risk` | POST | External risk assessment |

## 🧪 Testing

```bash
# Test all endpoints
python test_api.py

# Test specific module
curl http://localhost:8080/api/v1/prabu/health
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud Project ID | Yes |
| `ENVIRONMENT` | Environment (development/production) | No |
| `PORT` | Server port | No (default: 8080) |
| `SETIA_RISK_DATA_BUCKET_NAME` | GCS bucket for risk data | No |
| `OLLAMA_API_BASE_URL` | Ollama API URL | No |

### Google Cloud Setup

1. **Enable APIs**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   ```

2. **Create OAuth2 Credentials**
   - Go to APIs & Services > Credentials
   - Create OAuth 2.0 Client ID (Desktop Application)
   - Download as `credentials.json`

## 🔒 Authentication

API menggunakan Google Cloud OAuth2 untuk autentikasi:

1. **Development**: OAuth2 dengan browser flow
2. **Production**: Service Account credentials

## 📁 Project Structure

```
astranauts/
├── app/                    # FastAPI application
│   ├── main.py            # Application entry point
│   ├── routers/           # API route handlers
│   ├── services/          # Business logic
│   └── models/            # Pydantic models
├── PrabuModule/           # Credit scoring module
├── SaranaModule/          # OCR & NLP module  
├── SetiaModule/           # Sentiment analysis module
├── notebook/              # Jupyter notebooks
├── Output/                # Output files
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── deploy.sh             # Deployment script
└── README.md             # This file
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Error pada Module**
   ```bash
   export PYTHONPATH=/path/to/astranauts:$PYTHONPATH
   ```

2. **Google Cloud Authentication Error**
   - Pastikan `credentials.json` tersedia
   - Pastikan project ID benar di `.env`

3. **Port Already in Use**
   ```bash
   # Gunakan port berbeda
   uvicorn app.main:app --port 8081
   ```

### Logs

```bash
# Development logs
uvicorn app.main:app --log-level debug

# Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision"
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

[MIT License](LICENSE)

## 📞 Support

Untuk dukungan teknis, silakan buat issue di repository GitHub atau hubungi tim development.
