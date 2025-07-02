import ollama
import json
import re
import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Impor daftar kata kunci default dari pengekstrak_kata_kunci
from .pengekstrak_kata_kunci import DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT as DEFAULT_FINANCIAL_KEYWORDS_FROM_SARANA

# Gunakan 'kata_dasar' dari konstanta yang diimpor untuk DEFAULT_FINANCIAL_KEYWORDS.
# Ini memastikan konsistensi dengan nama item yang diharapkan dalam output JSON terstruktur.
DEFAULT_FINANCIAL_KEYWORDS = [item['kata_dasar'] for item in DEFAULT_FINANCIAL_KEYWORDS_FROM_SARANA]

def extract_financial_data_from_image_ollama(
    image_path: str,
    prompt_template_for_json_extraction: str = None,
    vision_model_name: str = "llama3.2-vision",
    llm_model_name: str = "llama3", # Model untuk ekstraksi JSON
    ollama_base_url: str = None, # Untuk base URL Ollama API (misalnya "http://localhost:11434")
    target_keywords: list[str] = None,
    vision_model_prompt: str = None,
    timeout_seconds: int = 120
) -> dict:
    """
    Mengekstrak data keuangan dari sebuah gambar menggunakan serangkaian panggilan ke Ollama.
    Proses ini melibatkan dua tahap utama:
    1.  **Ekstraksi Teks Mentah**: Model vision Ollama (misalnya, `llama3.2-vision`) digunakan untuk
        melakukan OCR pada gambar dan mengekstrak semua teks yang terlihat.
    2.  **Strukturisasi ke JSON**: Model bahasa Ollama (misalnya, `llama3`) kemudian mengambil teks mentah ini
        dan, berdasarkan prompt yang mendetail, menstrukturkan informasi keuangan yang relevan
        ke dalam format JSON. Prompt ini mengarahkan model untuk mengidentifikasi item keuangan,
        nilai-nilainya untuk tahun berjalan dan tahun sebelumnya, melakukan normalisasi angka,
        dan memperhatikan potensi pengali global (misalnya, "dalam jutaan").

    Args:
        image_path (str): Path absolut atau relatif ke file gambar (misalnya, .png, .jpg)
                          yang berisi data laporan keuangan.
        prompt_template_for_json_extraction (str, optional):
            Template prompt kustom yang akan digunakan untuk memandu LLM dalam menstrukturkan
            data ke JSON. Jika `None`, sebuah template default yang komprehensif akan digunakan.
            Template ini harus menyertakan placeholder seperti `{keywords_list_str}` dan
            `{text_to_process}`.
        vision_model_name (str): Nama model vision Ollama yang akan digunakan untuk OCR.
                                 Default: "llama3.2-vision".
        llm_model_name (str): Nama model bahasa Ollama yang akan digunakan untuk ekstraksi JSON.
                              Default: "llama3".
        ollama_base_url (str, optional): Base URL dari Ollama API jika tidak berjalan pada
                                       default (`http://localhost:11434`). Ini akan digunakan untuk
                                       kedua klien Ollama (vision dan LLM).
        target_keywords (list[str], optional):
            Daftar kata kunci keuangan spesifik yang ingin diekstrak. Jika `None`,
            `DEFAULT_FINANCIAL_KEYWORDS` (berasal dari `DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT` di `pengekstrak_kata_kunci.py`)
            akan digunakan. Daftar ini dimasukkan ke dalam prompt LLM untuk memfokuskan ekstraksi.
        vision_model_prompt (str, optional):
            Prompt kustom untuk model vision Ollama saat melakukan ekstraksi teks mentah.
            Jika `None`, prompt default yang berfokus pada OCR akurat dokumen keuangan
            akan digunakan.
        timeout_seconds (int): Waktu maksimum (dalam detik) untuk menunggu respons dari setiap
                               panggilan ke server Ollama. Default: 120 detik.

    Returns:
        dict: Sebuah dictionary Python yang mewakili data keuangan yang berhasil diekstrak
              dan di-parse dari JSON. Strukturnya diharapkan berupa:
              `{"Nama Akun": {"current_year": Nilai, "previous_year": Nilai}, ...}`.
              Jika terjadi error pada tahap mana pun (misalnya, file tidak ditemukan,
              error API Ollama, gagal parsing JSON), dictionary akan berisi key `"error"`
              dengan deskripsi masalah, dan mungkin key lain seperti `"details"`,
              `"additional_info"`, atau `"raw_llm_output"` untuk debugging.
    """
    if not os.path.exists(image_path):
        return {"error": f"File gambar tidak ditemukan di {image_path}"}

    current_keywords = target_keywords if target_keywords is not None else DEFAULT_FINANCIAL_KEYWORDS
    
    # Konfigurasi klien Ollama
    ollama_client_params = {}
    if ollama_base_url:
        ollama_client_params['host'] = ollama_base_url # ollama.Client menggunakan 'host'
    if timeout_seconds:
        ollama_client_params['timeout'] = timeout_seconds
        
    ollama_client = ollama.Client(**ollama_client_params)

    # Konfigurasi ChatOllama (Langchain)
    chat_ollama_params = {"model": llm_model_name, "temperature": 0}
    if ollama_base_url:
        chat_ollama_params['base_url'] = ollama_base_url # ChatOllama menggunakan 'base_url'
    # Timeout untuk ChatOllama bisa diatur via config jika perlu, tapi kita jaga sederhana dulu

    try:
        # Langkah 1: Ekstrak teks mentah dari gambar menggunakan model vision Ollama
        actual_vision_prompt = vision_model_prompt
        if not actual_vision_prompt:
            # Modified default vision prompt to be more focused
            actual_vision_prompt = (
                "Prioritaskan ekstraksi teks yang berkaitan dengan item dan angka keuangan dari dokumen ini. "
                "Fokus pada tabel, angka, dan istilah keuangan yang relevan. "
                "Ekstrak teks seakurat mungkin dari area tersebut."
            )
        
        print(f"INFO: Mengirim gambar {os.path.basename(image_path)} ke model vision Ollama ({vision_model_name}) dengan prompt terfokus...")
        vision_response = ollama_client.chat(
            model=vision_model_name,
            messages=[{
                "role": "user",
                "content": actual_vision_prompt,
                "images": [image_path]
            }]
        )

        if not (vision_response and vision_response.get('message') and vision_response['message'].get('content')):
            return {"error": "Tidak ada konten teks yang diekstrak oleh model vision Ollama."}

        raw_text_from_image = vision_response['message']['content'].strip()
        print(f"INFO: Teks mentah berhasil diekstrak dari gambar (awal 500 char):\n{raw_text_from_image[:500]}...")

        # Langkah 2: Gunakan model bahasa Ollama untuk menstrukturkan teks mentah menjadi JSON
        print(f"INFO: Memulai strukturisasi teks menjadi JSON menggunakan Ollama LLM ({llm_model_name})...")
        
        actual_json_prompt_template = prompt_template_for_json_extraction
        if not actual_json_prompt_template:
            # Modified default JSON extraction prompt to be more focused and efficient
            actual_json_prompt_template = """
            Anda adalah sistem AI yang bertugas mengekstrak DATA KEUANGAN UTAMA dari teks yang diberikan.
            Fokus HANYA pada item keuangan dari DAFTAR KATA KUNCI TARGET dan nilai-nilainya.
            Output HARUS berupa JSON yang valid.

            DAFTAR KATA KUNCI TARGET:
            {keywords_list_str}

            Teks untuk Diproses (hasil OCR, mungkin mengandung teks non-keuangan):
            {text_to_process}

            Instruksi Ekstraksi JSON:
            1.  **Fokus Utama**: Ekstrak HANYA item dari DAFTAR KATA KUNCI TARGET. Abaikan semua teks lain.
            2.  **Nilai**: Untuk setiap item target, temukan nilai untuk 'current_year' dan 'previous_year'. Jika salah satu tidak ada, gunakan null. Jika item tidak ada dalam teks, jangan sertakan item tersebut dalam JSON.
            3.  **Normalisasi Angka**:
                *   Hilangkan pemisah ribuan (misalnya, '1.234.567,89' menjadi '1234567.89').
                *   Angka dalam tanda kurung `(123)` atau `(123,45)` berarti negatif (misalnya, -123 atau -123.45).
                *   Pastikan nilai akhir adalah numerik (float atau integer).
            4.  **Pengali Global**: Jika teks menyebutkan pengali (misal "dalam jutaan", "in thousands", "dalam ribuan"), KALIKAN SEMUA NILAI dengan pengali tersebut. Jika ada, sebutkan pengali yang digunakan dalam metadata output jika memungkinkan, atau pastikan nilai sudah dikalikan.
            5.  **Format JSON Output**:
                *   Struktur: `{{ "Nama Akun Target": {{ "current_year": nilai_angka, "previous_year": nilai_angka_atau_null }} }}`.
                *   Gunakan nama dari DAFTAR KATA KUNCI TARGET sebagai key utama.
                *   HANYA sertakan item yang ditemukan.
            6.  **Efisiensi**: Jangan sertakan penjelasan atau teks tambahan dalam output Anda. HANYA blok kode JSON. Mulai dengan ```json dan akhiri dengan ```.

            JSON Hasil Ekstraksi (FOKUS HANYA PADA DATA KEUANGAN DARI KATA KUNCI TARGET):
            """

        # Membuat string daftar kata kunci untuk prompt.
        # Kita bisa menyertakan variasi di sini jika dirasa membantu LLM,
        # namun untuk output JSON, kita ingin 'kata_dasar'.
        # Prompt di atas sudah menginstruksikan untuk menggunakan 'kata_dasar' sebagai key.
        keywords_string_for_prompt = "\n".join([f"- {kw}" for kw in current_keywords])
        
        llm = ChatOllama(**chat_ollama_params)
        prompt_for_llm = ChatPromptTemplate.from_template(actual_json_prompt_template)
        chain_for_json_extraction = prompt_for_llm | llm | StrOutputParser()

        # Panggil LLM untuk menstrukturkan data
        structured_response_str = chain_for_json_extraction.invoke({
            "keywords_list_str": keywords_string_for_prompt,
            "text_to_process": raw_text_from_image
        })
        print(f"INFO: Respons terstruktur dari LLM (awal 500 char):\n{structured_response_str[:500]}...")

        # Langkah 3: Parse string JSON dari output LLM
        # LLM mungkin mengembalikan JSON yang diapit ```json ... ``` atau penjelasan lain.
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", structured_response_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Jika tidak ada blok ```json```, coba asumsikan seluruh string adalah JSON
            # Ini mungkin memerlukan pembersihan lebih lanjut jika ada teks non-JSON
            json_str = structured_response_str.strip()
            # Hapus potensi komentar atau teks sebelum/sesudah JSON
            if not json_str.startswith("{") and "[" not in json_str : # Basic check if it looks like JSON
                 # Coba cari JSON pertama yang valid jika ada teks lain
                first_brace = json_str.find('{')
                first_bracket = json_str.find('[')
                
                start_index = -1
                if first_brace != -1 and first_bracket != -1:
                    start_index = min(first_brace, first_bracket)
                elif first_brace != -1:
                    start_index = first_brace
                elif first_bracket != -1:
                    start_index = first_bracket

                if start_index != -1:
                    json_str = json_str[start_index:]
                    # Cari akhir JSON yang sesuai (lebih kompleks, untuk sekarang ambil sampai akhir)
                    # Ini bisa diperbaiki dengan pencocokan kurung yang lebih baik

        try:
            # Normalisasi lebih lanjut string JSON sebelum parsing
            # Hapus komentar // dan /* */
            json_str = re.sub(r"//.*?\n", "\n", json_str)
            json_str = re.sub(r"/\*.*?\*/", "", json_str, flags=re.DOTALL)
            # Hapus trailing commas (penyebab umum error JSON)
            json_str = re.sub(r",\s*([\}\]])", r"\1", json_str)

            parsed_json = json.loads(json_str)
            print("INFO: JSON berhasil di-parse.")
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"ERROR: Gagal mem-parsing JSON dari output LLM: {e}")
            print(f"String JSON yang gagal di-parse: {json_str}")
            return {"error": "Gagal mem-parse JSON dari output LLM.", "details": str(e), "raw_llm_output": structured_response_str}

    except ollama.ResponseError as e:
        return {"error": f"Ollama API error: {e.status_code} - {e.error}", "details": str(e)}
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"ERROR: Terjadi kesalahan tak terduga ({error_type}): {error_msg}")
        # Periksa apakah error terkait dengan koneksi ke Ollama
        if "Connection refused" in error_msg or "Failed to connect" in error_msg or "Max retries exceeded with url" in error_msg:
            additional_info = "Pastikan server Ollama berjalan dan dapat diakses. "
            if ollama_model:
                 additional_info += f"Juga pastikan model '{ollama_model}' (vision) dan 'llama3' (LLM) telah diunduh (misalnya, `ollama pull {ollama_model}` dan `ollama pull llama3`)."
            return {"error": f"Gagal terhubung ke Ollama atau model tidak ditemukan. {additional_info}", "details": error_msg}
        return {"error": f"Kesalahan tidak terduga selama ekstraksi: {error_type}", "details": error_msg}


if __name__ == '__main__':
    # Contoh penggunaan:
    # Pastikan Anda memiliki gambar bernama 'test_financial_image.png' di direktori yang sama
    # atau ganti dengan path gambar yang valid.
    # Juga, pastikan server Ollama berjalan dengan model llama3.2-vision dan llama3.
    
    # Buat file gambar dummy jika tidak ada untuk pengujian
    dummy_image_path = "dummy_financial_statement.png"
    if not os.path.exists(dummy_image_path):
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (800, 600), color = (255, 255, 255))
            d = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 15)
            except IOError:
                font = ImageFont.load_default()
            
            d.text((10,10), "Laporan Laba Rugi PT Contoh Jaya", fill=(0,0,0), font=font)
            d.text((10,40), "Untuk Tahun yang Berakhir 31 Desember", fill=(0,0,0), font=font)
            
            d.text((50,80), "Pendapatan Bersih", fill=(0,0,0), font=font)
            d.text((400,80), "2023", fill=(0,0,0), font=font)
            d.text((550,80), "2022", fill=(0,0,0), font=font)
            
            d.text((50,110), "Penjualan", fill=(0,0,0), font=font)
            d.text((400,110), "1.000.000.000", fill=(0,0,0), font=font)
            d.text((550,110), "800.000.000", fill=(0,0,0), font=font)

            d.text((50,140), "Harga Pokok Penjualan", fill=(0,0,0), font=font)
            d.text((400,140), "(600.000.000)", fill=(0,0,0), font=font)
            d.text((550,140), "(500.000.000)", fill=(0,0,0), font=font)

            d.text((50,170), "Laba Kotor", fill=(0,0,0), font=font)
            d.text((400,170), "400.000.000", fill=(0,0,0), font=font)
            d.text((550,170), "300.000.000", fill=(0,0,0), font=font)

            d.text((50,200), "Beban Usaha", fill=(0,0,0), font=font)
            d.text((400,200), "(150.000.000)", fill=(0,0,0), font=font)
            d.text((550,200), "(100.000.000)", fill=(0,0,0), font=font)

            d.text((50,230), "Laba Bersih", fill=(0,0,0), font=font)
            d.text((400,230), "250.000.000", fill=(0,0,0), font=font)
            d.text((550,230), "200.000.000", fill=(0,0,0), font=font)
            
            d.text((10,280), "Catatan: Dalam ribuan Rupiah", fill=(0,0,0), font=font) # Contoh pengali

            img.save(dummy_image_path)
            print(f"INFO: Berhasil membuat file gambar dummy: {dummy_image_path}")
            image_to_process = dummy_image_path
        except ImportError:
            print("PERINGATAN: PIL (Pillow) tidak terinstal. Tidak dapat membuat gambar dummy. Harap sediakan gambar manual.")
            image_to_process = None # Tidak ada gambar untuk diproses
        except Exception as e_img:
            print(f"ERROR: Gagal membuat gambar dummy: {e_img}")
            image_to_process = None
    else:
        image_to_process = dummy_image_path
        print(f"INFO: Menggunakan gambar yang sudah ada: {image_to_process}")

    if image_to_process:
        print(f"\nMemulai ekstraksi data keuangan dari gambar: {image_to_process}...")
        # Anda bisa mencoba dengan host Ollama kustom jika perlu:
        # custom_ollama_host = "http://my-ollama-server:11434"
        # extracted_data = extract_financial_data_from_image_ollama(image_to_process, ollama_host=custom_ollama_host)
        
        extracted_data = extract_financial_data_from_image_ollama(image_to_process)

        if "error" in extracted_data:
            print(f"\n--- Hasil Ekstraksi Gagal ---")
            print(f"Error: {extracted_data['error']}")
            if "details" in extracted_data:
                print(f"Detail: {extracted_data['details']}")
            if "raw_llm_output" in extracted_data:
                print(f"Output Mentah LLM:\n{extracted_data['raw_llm_output']}")
        else:
            print(f"\n--- Hasil Ekstraksi Sukses ---")
            print(json.dumps(extracted_data, indent=4, ensure_ascii=False))

            # Validasi sederhana
            if "Laba Bersih" in extracted_data or "Laba/rugi tahun berjalan" in extracted_data:
                print("\nINFO: 'Laba Bersih' atau 'Laba/rugi tahun berjalan' ditemukan dalam hasil.")
            else:
                print("\nPERINGATAN: 'Laba Bersih' atau 'Laba/rugi tahun berjalan' TIDAK ditemukan. Periksa output JSON dan prompt.")
            
            if extracted_data: # Jika tidak kosong
                first_key = list(extracted_data.keys())[0]
                if isinstance(extracted_data[first_key], dict) and "current_year" in extracted_data[first_key]:
                     print(f"INFO: Struktur data untuk item pertama ('{first_key}') tampak benar (memiliki 'current_year').")
                else:
                    print(f"PERINGATAN: Struktur data untuk item pertama ('{first_key}') mungkin tidak sesuai harapan.")
            else:
                print("PERINGATAN: Hasil ekstraksi JSON kosong.")

    else:
        print("\nTidak ada gambar untuk diproses. Silakan sediakan gambar laporan keuangan.")

if __name__ == '__main__':
    # --- Contoh Penggunaan ---
    print("Memulai skrip contoh untuk extract_financial_data_from_image_ollama...")

    # Path ke gambar dummy atau gambar asli Anda
    # Ganti dengan path yang sesuai jika dummy_financial_statement.png tidak ada
    example_image_path = "dummy_financial_statement.png" 

    # Buat file gambar dummy jika tidak ada untuk pengujian
    if not os.path.exists(example_image_path):
        print(f"File gambar '{example_image_path}' tidak ditemukan, mencoba membuat gambar dummy...")
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (900, 700), color = (255, 255, 255))
            d = ImageDraw.Draw(img)
            try:
                # Coba font yang umum ada, fallback ke default jika tidak ketemu
                font_path = "arial.ttf" if os.path.exists("arial.ttf") else ("verdana.ttf" if os.path.exists("verdana.ttf") else None)
                font_l = ImageFont.truetype(font_path, 24) if font_path else ImageFont.load_default()
                font_m = ImageFont.truetype(font_path, 18) if font_path else ImageFont.load_default()
                font_s = ImageFont.truetype(font_path, 14) if font_path else ImageFont.load_default()
            except IOError:
                print("Peringatan: Font Arial/Verdana tidak ditemukan, menggunakan font default PIL.")
                font_l = ImageFont.load_default()
                font_m = ImageFont.load_default()
                font_s = ImageFont.load_default()

            d.text((20,20), "PT MAJU MUNDUR SEJAHTERA", fill=(0,0,0), font=font_l)
            d.text((20,60), "LAPORAN POSISI KEUANGAN KONSOLIDASIAN", fill=(0,0,0), font=font_m)
            d.text((20,90), "Per 31 Desember 2023 dan 2022", fill=(0,0,0), font=font_m)
            d.text((20,120), "(Dalam jutaan Rupiah, kecuali dinyatakan lain)", fill=(0,0,0), font=s)

            header_y = 160
            col1_x, col2_x, col3_x = 20, 500, 700
            d.text((col2_x, header_y), "2023", fill=(0,0,0), font=font_m)
            d.text((col3_x, header_y), "2022", fill=(0,0,0), font=font_m)

            current_y = header_y + 40
            financial_items = [
                ("ASET", None, None, font_m),
                ("  Aset Lancar", None, None, font_m),
                ("    Kas dan setara kas", "1.250.000", "1.100.000", font_s),
                ("    Piutang usaha", "3.500.000", "3.200.000", font_s),
                ("    Persediaan", "2.000.000", "1.800.000", font_s),
                ("  Jumlah aset lancar", "6.750.000", "6.100.000", font_m),
                ("  Aset Tidak Lancar", None, None, font_m),
                ("    Aset tetap - bersih", "10.000.000", "9.500.000", font_s),
                ("  Jumlah aset tidak lancar", "10.000.000", "9.500.000", font_m),
                ("JUMLAH ASET", "16.750.000", "15.600.000", font_m),
                ("LIABILITAS DAN EKUITAS", None, None, font_m),
                ("  Liabilitas Jangka Pendek", None, None, font_m),
                ("    Utang usaha", "2.000.000", "1.900.000", font_s),
                ("  Jumlah liabilitas jangka pendek", "2.000.000", "1.900.000", font_m),
                ("  Ekuitas", None, None, font_m),
                ("    Modal saham", "5.000.000", "5.000.000", font_s),
                ("    Laba ditahan", "9.750.000", "8.700.000", font_s),
                ("  Jumlah ekuitas", "14.750.000", "13.700.000", font_m),
                ("JUMLAH LIABILITAS DAN EKUITAS", "16.750.000", "15.600.000", font_m),
            ]

            for item_data in financial_items:
                name, val2023, val2022, item_font = item_data
                d.text((col1_x, current_y), name, fill=(0,0,0), font=item_font)
                if val2023:
                    d.text((col2_x, current_y), val2023, fill=(0,0,0), font=item_font)
                if val2022:
                    d.text((col3_x, current_y), val2022, fill=(0,0,0), font=item_font)
                current_y += 30
            
            img.save(example_image_path)
            print(f"INFO: Berhasil membuat file gambar dummy: {example_image_path}")
        except ImportError:
            print("PERINGATAN: PIL (Pillow) tidak terinstal. Tidak dapat membuat gambar dummy. Harap sediakan gambar manual.")
            example_image_path = None 
        except Exception as e_img_create:
            print(f"ERROR: Gagal membuat gambar dummy: {e_img_create}")
            example_image_path = None
    else:
        print(f"INFO: Menggunakan gambar yang sudah ada: {example_image_path}")

    if example_image_path:
        print(f"\nMemulai ekstraksi data keuangan dari gambar: {example_image_path}...")
        
        # Anda bisa mencoba dengan Ollama base URL kustom jika perlu, misalnya:
        # custom_ollama_url = "http://my-ollama-server.local:11434" 
        # extracted_financial_data = extract_financial_data_from_image_ollama(example_image_path, ollama_base_url=custom_ollama_url)
        
        extracted_financial_data = extract_financial_data_from_image_ollama(example_image_path)

        print("\n--- Hasil Ekstraksi ---")
        if "error" in extracted_financial_data:
            print(f"Status: GAGAL")
            print(f"Pesan Error: {extracted_financial_data['error']}")
            if extracted_financial_data.get("details"):
                print(f"Detail Error: {extracted_financial_data['details']}")
            if extracted_financial_data.get("additional_info"):
                print(f"Info Tambahan: {extracted_financial_data['additional_info']}")
            if extracted_financial_data.get("raw_llm_output"):
                print(f"Output Mentah LLM (sebelum parsing JSON):\n{extracted_financial_data['raw_llm_output'][:1000]}...")
            if extracted_financial_data.get("problematic_json_string"):
                print(f"String JSON Bermasalah:\n{extracted_financial_data['problematic_json_string'][:1000]}...")
        else:
            print(f"Status: SUKSES")
            print("Data JSON yang Diekstrak:")
            print(json.dumps(extracted_financial_data, indent=4, ensure_ascii=False))

            # Validasi sederhana (sesuaikan dengan konten gambar dummy Anda)
            if "Jumlah aset lancar" in extracted_financial_data and \
               isinstance(extracted_financial_data["Jumlah aset lancar"], dict) and \
               "current_year" in extracted_financial_data["Jumlah aset lancar"] and \
               extracted_financial_data["Jumlah aset lancar"]["current_year"] is not None:
                print("\nINFO: 'Jumlah aset lancar' dengan nilai 'current_year' berhasil diekstrak.")
                # Cek apakah pengali "jutaan" diterapkan (nilai seharusnya besar)
                if extracted_financial_data["Jumlah aset lancar"]["current_year"] > 1000000: # Asumsi 6.750.000 * 1.000.000
                     print("INFO: Nilai 'Jumlah aset lancar' tampak sudah dikalikan dengan pengali (jutaan).")
                else:
                     print("PERINGATAN: Nilai 'Jumlah aset lancar' mungkin belum dikalikan dengan pengali (jutaan). Periksa prompt dan output.")
            else:
                print("\nPERINGATAN: 'Jumlah aset lancar' atau nilai 'current_year'-nya tidak ditemukan/valid. Periksa output JSON.")
            
            if not extracted_financial_data:
                 print("PERINGATAN: Hasil ekstraksi JSON kosong padahal tidak ada error.")

    else:
        print("\nTidak ada gambar untuk diproses. Harap sediakan gambar laporan keuangan yang valid.")

    print("\nSkrip contoh selesai.")