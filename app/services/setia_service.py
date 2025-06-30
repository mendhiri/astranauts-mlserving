import os
import json
import datetime

# Conditional imports for Vertex AI and Google Cloud Storage
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Tool, Part, HarmCategory, HarmBlockThreshold
    from vertexai.language_models import TextGenerationModel # Older model, if needed
    from google.cloud import storage
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    # Define dummy classes or functions if Vertex AI is not available,
    # so the service can still be imported and potentially run with mock data.
    class GenerativeModel:
        def __init__(self, model_name, tools=None): self.model_name = model_name
        def generate_content(self, prompt): return type('obj', (object,), {'text': json.dumps({"summary": "Vertex AI not available. Mock response.", "sentiment": "Neutral", "key_issues": ["Vertex AI SDK not installed"], "sources": []}) })()
    class Tool: pass
    class Part: pass
    class GoogleSearchRetrieval: pass # Dummy for Tool
    class storage: # Dummy storage
        class Client:
            def bucket(self, bucket_name): return self # Dummy bucket
            def blob(self, blob_name): return self # Dummy blob
            def download_as_text(self): return "{}" # Dummy empty JSON string for risk_data

    print("WARNING (SetiaService): Vertex AI SDK or Google Cloud Storage SDK not found. Setia service will use mock data or fail for AI features.")


# Path ke data risiko lokal
RISK_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "risk_data.json")

# Inisialisasi klien bisa dilakukan di sini jika diinginkan untuk reuse dalam satu instance layanan
# Namun, untuk Cloud Function style, inisialisasi per panggilan juga umum.
# Untuk FastAPI, lebih baik inisialisasi saat startup aplikasi atau lazy load dengan singleton pattern.
# Untuk sekarang, kita akan coba lazy load di dalam fungsi utama.

_storage_client = None
_vertex_ai_initialized = False
_risk_data_cache = None # Cache untuk risk_data.json

def _get_storage_client():
    global _storage_client
    if not VERTEX_AI_AVAILABLE: # Implies storage might also not be configured for real use
        print("INFO (SetiaService): Using dummy storage client as Vertex AI is not available.")
        return storage.Client() # Returns dummy client

    if _storage_client is None:
        try:
            _storage_client = storage.Client()
            print("INFO (SetiaService): Google Cloud Storage client initialized.")
        except Exception as e:
            print(f"ERROR (SetiaService): Failed to initialize Google Cloud Storage client: {e}")
            # Fallback to dummy client to allow basic operation without GCS
            _storage_client = storage.Client() # Dummy if real one fails
    return _storage_client

def _initialize_vertex_ai():
    global _vertex_ai_initialized
    if not VERTEX_AI_AVAILABLE:
        print("INFO (SetiaService): Vertex AI SDK not available. Skipping Vertex AI initialization.")
        _vertex_ai_initialized = True # Mark as "initialized" to avoid retries
        return

    if not _vertex_ai_initialized:
        try:
            project_id = os.environ.get('GCP_PROJECT')
            location = os.environ.get('GCP_LOCATION', "asia-southeast1") # Default location
            if not project_id:
                print("WARNING (SetiaService): GCP_PROJECT environment variable not set. Vertex AI might not work correctly.")
            
            vertexai.init(project=project_id, location=location)
            _vertex_ai_initialized = True
            print(f"INFO (SetiaService): Vertex AI initialized for project '{project_id}' in location '{location}'.")
        except Exception as e:
            print(f"ERROR (SetiaService): Failed to initialize Vertex AI: {e}. AI features will be degraded.")
            # Potentially set _vertex_ai_initialized to True even on failure to prevent repeated init attempts,
            # or allow retries if it's a transient issue. For now, prevent retries on init failure.
            _vertex_ai_initialized = True # Avoid re-init attempts on persistent error

def _load_risk_data_from_local() -> dict:
    """Loads risk data from the local JSON file."""
    global _risk_data_cache
    if _risk_data_cache is not None:
        return _risk_data_cache
    
    try:
        if not os.path.exists(RISK_DATA_PATH):
            print(f"ERROR (SetiaService): Local risk_data.json not found at {RISK_DATA_PATH}")
            _risk_data_cache = {} # Cache empty dict on error
            return _risk_data_cache

        with open(RISK_DATA_PATH, 'r', encoding='utf-8') as f:
            _risk_data_cache = json.load(f)
        print(f"INFO (SetiaService): Risk data loaded successfully from local file: {RISK_DATA_PATH}")
        return _risk_data_cache
    except Exception as e:
        print(f"ERROR (SetiaService): Failed to load risk data from local file {RISK_DATA_PATH}: {e}")
        _risk_data_cache = {} # Cache empty dict on error
        return _risk_data_cache

def _get_risk_data_gcs(bucket_name: str, blob_name: str = 'risk_data.json') -> dict:
    """Placeholder to read risk data from GCS if needed in the future."""
    # This function is not used by default if local file is preferred.
    # Kept for compatibility with original Cloud Function structure if GCS becomes primary.
    global _risk_data_cache
    if _risk_data_cache is not None: # Check cache first
        return _risk_data_cache

    if not VERTEX_AI_AVAILABLE: # If Vertex AI is off, assume GCS is also for mock/local
        print("INFO (SetiaService): GCS access for risk data skipped as Vertex AI is not available. Attempting local load.")
        return _load_risk_data_from_local()

    storage_client_instance = _get_storage_client()
    if isinstance(storage_client_instance, type) and hasattr(storage_client_instance, 'bucket'): # Check if it's the dummy
         pass # It's the dummy client, proceed to load local.

    try:
        print(f"INFO (SetiaService): Reading risk data from GCS bucket '{bucket_name}', blob '{blob_name}'.")
        bucket = storage_client_instance.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        risk_data_content = blob.download_as_text()
        _risk_data_cache = json.loads(risk_data_content)
        print("INFO (SetiaService): Risk data read successfully from GCS.")
        return _risk_data_cache
    except Exception as e:
        print(f"ERROR (SetiaService): Failed to read risk data from GCS (bucket: {bucket_name}, blob: {blob_name}): {e}")
        print("INFO (SetiaService): Falling back to loading risk data from local file.")
        return _load_risk_data_from_local() # Fallback to local


def get_setia_risk_intelligence(
    applicant_name: str,
    industry_main: str | None,
    industry_sub: str | None,
    use_gcs_for_risk_data: bool = False, # Default to local risk data
    gcs_bucket_name: str | None = None # Required if use_gcs_for_risk_data is True
) -> dict:
    """
    Provides risk intelligence analysis for an applicant.
    Combines grounded AI analysis with predefined risk data.
    """
    if not VERTEX_AI_AVAILABLE:
        # Return a mock/error response if Vertex AI components are not available
        return {
            "error": "Vertex AI components are not available. Service is degraded.",
            "groundedSummary": "AI analysis skipped due to missing dependencies.",
            "overallSentiment": "Unknown",
            "keyIssues": [],
            "supportingSources": [],
            "industrySectorOutlook": "Unknown (dependencies missing)",
            "lastUpdateTimestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    _initialize_vertex_ai() # Ensure Vertex AI is initialized

    # --- 1. Baca Data Risiko ---
    # Default to local, but allow GCS if specified and configured
    risk_data = {}
    if use_gcs_for_risk_data:
        if not gcs_bucket_name:
            error_msg = "GCS bucket name not provided for risk data, but GCS usage was requested."
            print(f"ERROR (SetiaService): {error_msg}")
            # Fallback to local if GCS is requested but not configured
            risk_data = _load_risk_data_from_local()
            if not risk_data: # If local also fails
                 risk_data = {"error": error_msg, "risiko_industri": {}}
        else:
            risk_data = _get_risk_data_gcs(gcs_bucket_name)
    else:
        risk_data = _load_risk_data_from_local()
        
    if "error" in risk_data: # If loading risk data failed (either GCS or local)
        sector_outlook = f"Gagal memuat data risiko: {risk_data['error']}"
    elif not risk_data.get("risiko_industri"): # If "risiko_industri" key is missing or empty
        sector_outlook = "Data risiko industri tidak ditemukan atau kosong."
    else:
        try:
            # Ensure industry_main and industry_sub are valid before accessing
            if industry_main and industry_sub:
                sector_outlook = risk_data.get("risiko_industri", {}).get(industry_main, {}).get(industry_sub, "Tidak Diketahui")
            elif industry_main: # Only main industry provided
                # Decide how to handle this: return all sub-sectors or a general outlook for main industry?
                # For now, let's assume specific sub-sector is needed.
                sector_outlook = f"Sub-industri tidak disediakan untuk industri utama: {industry_main}."
            else: # No industry info
                sector_outlook = "Informasi industri tidak disediakan."
        except Exception as e_risk_lookup:
            print(f"ERROR (SetiaService): Gagal mencari risiko industri: {e_risk_lookup}")
            sector_outlook = "Gagal memproses data risiko industri."


    # --- 2. Panggil Vertex AI Grounding ---
    grounded_analysis_content = {}
    if not _vertex_ai_initialized or not VERTEX_AI_AVAILABLE: # Double check
        print("WARNING (SetiaService): Vertex AI not initialized or not available. Skipping grounded analysis.")
        grounded_analysis_content = { "summary": "Analisis AI tidak dapat dilakukan (Vertex AI tidak siap).", "sentiment": "Error", "key_issues": [], "sources": [] }
    else:
        try:
            print(f"INFO (SetiaService): Requesting grounded analysis for: {applicant_name}")
            
            # Define the grounding tool (Google Search Retrieval)
            google_search_retrieval = Part.from_tool_config(
                tool_config=Tool(google_search_retrieval=GoogleSearchRetrieval()).to_tool_config()
            )
            
            # Initialize the Generative Model
            # Using a newer model like gemini-1.5-pro or gemini-1.5-flash
            model = GenerativeModel(
                "gemini-1.5-flash-001", # Or "gemini-1.5-pro-001"
                # tools=[Tool(google_search_retrieval=GoogleSearchRetrieval())] # Old way
            )
            
            prompt = f"""
            You are a financial risk analyst. Analyze recent news and information about the company "{applicant_name}" in Indonesia using Google Search.
            Based on your analysis, provide a response in a valid JSON format with the following keys:
            - "summary": A concise summary of the key findings related to potential risks or positive indicators.
            - "sentiment": Overall sentiment towards the company (e.g., "Positive", "Neutral", "Negative", "Mixed").
            - "key_issues": A list of strings, where each string is a key issue or risk identified. If none, provide an empty list.
            - "sources": A list of up to 3-5 relevant source objects, each with "title" and "url". If none, provide an empty list.

            Focus on information relevant for credit risk assessment.
            Ensure the output is ONLY the JSON object, starting with {{ and ending with }}.
            """
            
            # Generate content with grounding
            # The new way to use tools is by passing them in the `tools` parameter of `generate_content`
            # or by including them in the `contents` list as `Part` objects.
            # For simple Google Search grounding, it's often enabled by default or with a simple tool config.
            # The `google_search_retrieval` object can be passed in the `contents` list.
            
            # Simpler approach if grounding is default for the model or if the model understands the prompt to use search:
            # response = model.generate_content(prompt)

            # Explicitly passing the tool for grounding:
            response = model.generate_content(
                [prompt, google_search_retrieval], # Passing the tool instance
                # generation_config={"temperature": 0.1} # Optional: control creativity
                # safety_settings={ # Optional: adjust safety settings
                #    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                #    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                #    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                #    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                # }
            )

            cleaned_response_text = response.text.strip()
            # Remove markdown JSON block markers if present
            if cleaned_response_text.startswith("```json"):
                cleaned_response_text = cleaned_response_text[len("```json"):]
            if cleaned_response_text.endswith("```"):
                cleaned_response_text = cleaned_response_text[:-len("```")]
            cleaned_response_text = cleaned_response_text.strip()
            
            grounded_analysis_content = json.loads(cleaned_response_text)
            print("INFO (SetiaService): Grounded analysis successful.")

        except Exception as e:
            print(f"ERROR (SetiaService): Grounded analysis failed: {e}")
            print(f"DEBUG (SetiaService): Raw Vertex AI response text that caused error (if any): {response.text if 'response' in locals() and hasattr(response, 'text') else 'N/A'}")
            grounded_analysis_content = { "summary": f"Gagal menghasilkan analisis AI. Error: {e}", "sentiment": "Error", "key_issues": [], "sources": [] }

    # --- 3. Susun & Kembalikan Hasil Akhir ---
    final_output = {
        "groundedSummary": grounded_analysis_content.get("summary"),
        "overallSentiment": grounded_analysis_content.get("sentiment"),
        "keyIssues": grounded_analysis_content.get("key_issues", []), # Default to empty list
        "supportingSources": grounded_analysis_content.get("sources", []), # Default to empty list
        "industrySectorOutlook": sector_outlook,
        "lastUpdateTimestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    print("INFO (SetiaService): Request processing completed.")
    return final_output


if __name__ == '__main__':
    print("--- Contoh Penggunaan Setia Service ---")
    
    # Konfigurasi untuk pengujian lokal (sesuaikan jika perlu)
    # Pastikan GOOGLE_APPLICATION_CREDENTIALS dan GCP_PROJECT sudah di-set di environment Anda jika menguji fitur AI.
    # Jika tidak, fitur AI akan di-skip atau menggunakan mock.
    
    if not VERTEX_AI_AVAILABLE:
        print("PERINGATAN: Vertex AI SDK tidak tersedia. Fitur AI akan di-mock atau dilewati.")
        # Set dummy env vars if needed for the code paths to run without real creds
        os.environ['GCP_PROJECT'] = 'dummy-project' 
        # No need to set GOOGLE_APPLICATION_CREDENTIALS as it won't be used by dummy clients

    applicant = "PT Bank Central Asia Tbk" # Contoh perusahaan publik
    main_industry = "Keuangan"
    sub_industry = "Perbankan (BUKU IV/III)"

    print(f"\nMendapatkan analisis risiko untuk: {applicant}")
    print(f"Industri Utama: {main_industry}, Sub-Industri: {sub_industry}")

    # Skenario 1: Menggunakan data risiko lokal (default)
    analysis_result_local_risk = get_setia_risk_intelligence(
        applicant_name=applicant,
        industry_main=main_industry,
        industry_sub=sub_industry
    )
    print("\n--- Hasil Analisis (Data Risiko Lokal) ---")
    print(json.dumps(analysis_result_local_risk, indent=2, ensure_ascii=False))

    # Skenario 2: Mencoba menggunakan GCS untuk data risiko (jika BUCKET_NAME di-set)
    # Untuk pengujian lokal, ini mungkin gagal jika bucket tidak ada atau tidak bisa diakses.
    # Fungsi akan fallback ke data lokal jika GCS gagal.
    gcs_bucket_for_risk = os.environ.get("SETIA_RISK_DATA_BUCKET_NAME") # Contoh nama env var
    if gcs_bucket_for_risk and VERTEX_AI_AVAILABLE: # Hanya coba GCS jika Vertex AI juga ada (indikasi env production-like)
        print(f"\nMencoba mendapatkan analisis risiko dengan data dari GCS Bucket: {gcs_bucket_for_risk}")
        analysis_result_gcs_risk = get_setia_risk_intelligence(
            applicant_name=applicant,
            industry_main=main_industry,
            industry_sub=sub_industry,
            use_gcs_for_risk_data=True,
            gcs_bucket_name=gcs_bucket_for_risk
        )
        print("\n--- Hasil Analisis (Data Risiko dari GCS atau Fallback Lokal) ---")
        print(json.dumps(analysis_result_gcs_risk, indent=2, ensure_ascii=False))
    else:
        if not VERTEX_AI_AVAILABLE:
             print("\nINFO: Tes GCS untuk data risiko dilewati karena Vertex AI tidak tersedia (mengindikasikan lingkungan non-cloud).")
        else:
             print(f"\nINFO: Env var SETIA_RISK_DATA_BUCKET_NAME tidak di-set. Melewati tes GCS untuk data risiko.")


    # Skenario 3: Perusahaan dengan nama berbeda, industri berbeda
    applicant_2 = "PT Telekomunikasi Indonesia Tbk"
    main_industry_2 = "Teknologi & Komunikasi"
    sub_industry_2 = "Telekomunikasi"
    print(f"\nMendapatkan analisis risiko untuk: {applicant_2}")
    analysis_result_2 = get_setia_risk_intelligence(applicant_2, main_industry_2, sub_industry_2)
    print("\n--- Hasil Analisis (Applicant 2) ---")
    print(json.dumps(analysis_result_2, indent=2, ensure_ascii=False))

    # Skenario 4: Industri tidak ditemukan
    print(f"\nMendapatkan analisis risiko untuk: {applicant} (Industri Tidak Dikenal)")
    analysis_result_unknown_industry = get_setia_risk_intelligence(applicant, "Industri Fiksi", "Sub Fiksi")
    print("\n--- Hasil Analisis (Industri Tidak Dikenal) ---")
    print(json.dumps(analysis_result_unknown_industry, indent=2, ensure_ascii=False))
    
    # Skenario 5: Tanpa informasi industri
    print(f"\nMendapatkan analisis risiko untuk: {applicant} (Tanpa Info Industri)")
    analysis_result_no_industry = get_setia_risk_intelligence(applicant, None, None)
    print("\n--- Hasil Analisis (Tanpa Info Industri) ---")
    print(json.dumps(analysis_result_no_industry, indent=2, ensure_ascii=False))

    if not VERTEX_AI_AVAILABLE:
        print("\nCATATAN: Karena Vertex AI SDK tidak tersedia, semua analisis AI yang ditampilkan adalah mock atau hasil error.")
        print("Untuk fungsionalitas penuh, pastikan SDK Google Cloud terinstal dan terkonfigurasi dengan benar.")
