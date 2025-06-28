import os
import json
import datetime
import vertexai
from vertexai.generative_models import GenerativeModel, Tool, GoogleSearchRetrieval
from google.cloud import storage

# Tidak ada inisialisasi klien di global scope. Semua dilakukan di dalam handler.

def setia_risk_intelligence_api(request):
    """
    Entry point utama dari Cloud Function.
    Menggabungkan semua logika untuk keandalan maksimum saat startup.
    """
    headers = {'Access-Control-Allow-Origin': '*'}
    if request.method != 'POST':
        return ('Method Not Allowed', 405, headers)
    
    request_json = request.get_json(silent=True)
    if not request_json or 'applicant_name' not in request_json:
        return ('Invalid JSON or missing applicant_name', 400, headers)

    # --- 1. Inisialisasi Klien (Lazy, hanya saat dibutuhkan) ---
    try:
        print("Initializing clients...")
        storage_client = storage.Client()
        
        project_id = os.environ.get('GCP_PROJECT')
        location = "asia-southeast1"
        vertexai.init(project=project_id, location=location)
        print("Clients initialized successfully.")
    except Exception as e:
        print(f"FATAL: Client initialization failed: {e}")
        return (f"Server error: Could not initialize clients. Error: {e}", 500, headers)

    # --- 2. Baca Data Risiko dari GCS ---
    try:
        print("Reading risk data from GCS...")
        bucket_name = os.environ.get('BUCKET_NAME', 'BUCKET_TIDAK_DITEMUKAN')
        if bucket_name == 'BUCKET_TIDAK_DITEMUKAN':
            raise ValueError("BUCKET_NAME environment variable not set.")
            
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob('risk_data.json')
        risk_data = json.loads(blob.download_as_text())
        print("Risk data read successfully.")
    except Exception as e:
        print(f"ERROR: Failed to read from GCS: {e}")
        return (f"Gagal membaca data dari GCS: {e}", 500, headers)

    # --- 3. Panggil Vertex AI Grounding ---
    applicant_name = request_json['applicant_name']
    grounded_analysis = {}
    try:
        print(f"Requesting grounded analysis for: {applicant_name}")
        tools = [Tool(google_search_retrieval=GoogleSearchRetrieval())]
        model = GenerativeModel("gemini-1.5-flash-001", tools=tools)
        prompt = f"""
        Analisis berita terkini tentang perusahaan "{applicant_name}" di Indonesia dari Google Search.
        Berdasarkan analisis Anda, berikan respons dalam format JSON yang valid dengan kunci "summary", "sentiment", "key_issues", dan "sources" (list of objects with "title" and "url").
        """
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        grounded_analysis = json.loads(cleaned_response)
        print("Grounded analysis successful.")
    except Exception as e:
        print(f"ERROR: Grounded analysis failed: {e}")
        grounded_analysis = { "summary": f"Gagal menghasilkan analisis AI. Error: {e}", "sentiment": "Error", "key_issues": [], "sources": [] }

    # --- 4. Susun & Kembalikan Hasil Akhir ---
    try:
        industry_main = request_json.get('industry_main')
        industry_sub = request_json.get('industry_sub')
        sector_outlook = risk_data.get("risiko_industri", {}).get(industry_main, {}).get(industry_sub, "Tidak Diketahui")
    except Exception:
        sector_outlook = "Gagal memproses risiko industri"

    final_output = {
        "groundedSummary": grounded_analysis.get("summary"),
        "overallSentiment": grounded_analysis.get("sentiment"),
        "keyIssues": grounded_analysis.get("key_issues"),
        "supportingSources": grounded_analysis.get("sources", []),
        "industrySectorOutlook": sector_outlook,
        "lastUpdateTimestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    print("Request completed successfully.")
    return (json.dumps(final_output, indent=2), 200, headers)