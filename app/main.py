from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import os # Diperlukan jika blok if __name__ == "__main__" digunakan

# Import router
from .routers import prabu_router, sarana_router, setia_router

app = FastAPI(
    title="Layanan Analisis Risiko Terintegrasi",
    description="API untuk analisis risiko keuangan (Prabu), pemrosesan dokumen (Sarana), dan intelijen risiko (Setia).",
    version="0.1.0",
    docs_url="/docs", 
    redoc_url="/redoc" 
)

# Middleware (contoh, bisa ditambahkan sesuai kebutuhan, misal CORS)
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Atur domain yang diizinkan, atau lebih spesifik
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Sertakan router-router
app.include_router(prabu_router.router, prefix="/prabu", tags=["Prabu - Analisis Keuangan"])
app.include_router(sarana_router.router, prefix="/sarana", tags=["Sarana - Pemrosesan Dokumen"])
app.include_router(setia_router.router, prefix="/setia", tags=["Setia - Intelijen Risiko"])

# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    # Redirect ke halaman dokumentasi API (/docs)
    return RedirectResponse(url="/docs")

# Contoh endpoint sederhana untuk health check
@app.get("/health", tags=["Utilities"])
async def health_check():
    return {"status": "ok", "message": "API is running"}

# Blok if __name__ == "__main__": bisa berguna untuk pengembangan lokal yang sangat cepat.
# Namun, umumnya Uvicorn dijalankan dari CLI: uvicorn app.main:app --reload
# Jika Anda ingin menyertakannya:
# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8008)) # Ganti port jika 8000 bentrok
#     print(f"Starting Uvicorn server on http://0.0.0.0:{port}")
#     uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
