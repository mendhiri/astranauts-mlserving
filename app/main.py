from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os

# Import router
from .routers import prabu_router, sarana_router, setia_router

app = FastAPI(
    title="Astranauts - Layanan Analisis Risiko Terintegrasi",
    description="API untuk analisis risiko keuangan (Prabu), pemrosesan dokumen (Sarana), dan intelijen risiko (Setia).",
    version="1.0.0",
    docs_url="/docs", 
    redoc_url="/redoc" 
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API versioning
app.include_router(prabu_router.router, prefix="/api/v1/prabu", tags=["Prabu - Credit Scoring"])
app.include_router(sarana_router.router, prefix="/api/v1/sarana", tags=["Sarana - OCR & NLP"])
app.include_router(setia_router.router, prefix="/api/v1/setia", tags=["Setia - Sentiment Analysis"])

# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Astranauts API", "version": "1.0.0", "docs": "/docs"}

# Global health check
@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "message": "Astranauts API is running", "version": "1.0.0"}

# API v1 health check
@app.get("/api/v1/health", tags=["Health Check"])
async def api_v1_health_check():
    return {"status": "ok", "message": "API v1 is running", "version": "1.0.0"}

# Cloud Run health check (for deployment)
@app.get("/api/health", tags=["Health Check"])
async def cloud_run_health_check():
    return {"status": "healthy", "message": "Service is ready"}

# For Cloud Run deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # Cloud Run uses PORT env var
    print(f"Starting Uvicorn server on http://0.0.0.0:{port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
