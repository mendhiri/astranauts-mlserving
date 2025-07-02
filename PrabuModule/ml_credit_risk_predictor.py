import os
import joblib
import pandas as pd
import numpy as np
from sklearn.exceptions import NotFittedError

# Path ke model dan preprocessor yang sudah dilatih
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'trained_models', 'incremental_risk_model.joblib')
PREPROCESSOR_PATH = os.path.join(BASE_DIR, 'trained_models', 'preprocessor.joblib')

MODEL = None
PREPROCESSOR = None
ALL_NUMERIC_FEATURES_FROM_TRAINER = [] 
CATEGORICAL_FEATURES_FROM_TRAINER = [] 
EXPECTED_COLS_FOR_TRANSFORM = []

def _load_resources():
    global MODEL, PREPROCESSOR, ALL_NUMERIC_FEATURES_FROM_TRAINER, CATEGORICAL_FEATURES_FROM_TRAINER, EXPECTED_COLS_FOR_TRANSFORM
    
    if os.path.exists(MODEL_PATH):
        MODEL = joblib.load(MODEL_PATH)
        print(f"Model ML dimuat dari {MODEL_PATH}")
    else:
        print(f"PERINGATAN: File model tidak ditemukan di {MODEL_PATH}. Prediksi ML tidak akan berfungsi.")
        MODEL = None

    if os.path.exists(PREPROCESSOR_PATH):
        PREPROCESSOR = joblib.load(PREPROCESSOR_PATH)
        print(f"Preprocessor dimuat dari {PREPROCESSOR_PATH}")
        
        try:
            num_features_idx = -1
            cat_features_idx = -1

            for i, transformer_tuple in enumerate(PREPROCESSOR.transformers_):
                name, _, _ = transformer_tuple
                if name == 'num':
                    num_features_idx = i
                elif name == 'cat':
                    cat_features_idx = i
            
            if num_features_idx != -1:
                ALL_NUMERIC_FEATURES_FROM_TRAINER = PREPROCESSOR.transformers_[num_features_idx][2]
            else:
                 print("Transformer 'num' tidak ditemukan di preprocessor.")
                 ALL_NUMERIC_FEATURES_FROM_TRAINER = []

            if cat_features_idx != -1:
                CATEGORICAL_FEATURES_FROM_TRAINER = PREPROCESSOR.transformers_[cat_features_idx][2]
            else:
                print("Transformer 'cat' tidak ditemukan di preprocessor.")
                CATEGORICAL_FEATURES_FROM_TRAINER = []
                
            EXPECTED_COLS_FOR_TRANSFORM = ALL_NUMERIC_FEATURES_FROM_TRAINER + CATEGORICAL_FEATURES_FROM_TRAINER
            
            print(f"Preprocessor mengharapkan fitur numerik: {ALL_NUMERIC_FEATURES_FROM_TRAINER}")
            print(f"Preprocessor mengharapkan fitur kategorikal: {CATEGORICAL_FEATURES_FROM_TRAINER}")
        except Exception as e:
            print(f"Gagal mengintrospeksi fitur dari preprocessor: {e}. Daftar fitur mungkin tidak akurat.")
            try:
                from .incremental_model_trainer import ALL_NUMERIC_FEATURES, CATEGORICAL_FEATURES
                ALL_NUMERIC_FEATURES_FROM_TRAINER = ALL_NUMERIC_FEATURES
                CATEGORICAL_FEATURES_FROM_TRAINER = CATEGORICAL_FEATURES
                EXPECTED_COLS_FOR_TRANSFORM = ALL_NUMERIC_FEATURES + CATEGORICAL_FEATURES
            except ImportError:
                 print("Gagal impor fallback konfigurasi fitur dari incremental_model_trainer.")
    else:
        print(f"PERINGATAN: File preprocessor tidak ditemukan di {PREPROCESSOR_PATH}. Prediksi ML tidak akan berfungsi.")
        PREPROCESSOR = None
        try:
            from .incremental_model_trainer import ALL_NUMERIC_FEATURES, CATEGORICAL_FEATURES
            ALL_NUMERIC_FEATURES_FROM_TRAINER = ALL_NUMERIC_FEATURES
            CATEGORICAL_FEATURES_FROM_TRAINER = CATEGORICAL_FEATURES
            EXPECTED_COLS_FOR_TRANSFORM = ALL_NUMERIC_FEATURES + CATEGORICAL_FEATURES
        except ImportError:
             print("Gagal impor fallback konfigurasi fitur dari incremental_model_trainer.")

_load_resources()

def predict_credit_risk_ml(financial_data_dict: dict, sector: str) -> dict:
    global MODEL, PREPROCESSOR, EXPECTED_COLS_FOR_TRANSFORM

    if MODEL is None or PREPROCESSOR is None:
        return {
            "risk_category": None,
            "probabilities": None,
            "error": "Model ML atau preprocessor tidak dimuat. Prediksi tidak dapat dilakukan."
        }

    input_df = pd.DataFrame([financial_data_dict])
    input_df['Sektor'] = sector 

    # Create a DataFrame with the expected columns, filled with NaN initially
    # Then populate with values from input_df
    # This ensures correct column order and presence for the preprocessor
    df_for_transform = pd.DataFrame(columns=EXPECTED_COLS_FOR_TRANSFORM)
    for col in EXPECTED_COLS_FOR_TRANSFORM:
        if col in input_df.columns:
            # Use .loc to assign to the single row of df_for_transform
            df_for_transform.loc[0, col] = input_df.loc[0, col]
        elif col in ALL_NUMERIC_FEATURES_FROM_TRAINER : 
            df_for_transform.loc[0, col] = np.nan
        elif col in CATEGORICAL_FEATURES_FROM_TRAINER:
             # For 'Sektor', it's already added. If other categoricals were expected but missing:
            df_for_transform.loc[0, col] = None 
    
    # If EXPECTED_COLS_FOR_TRANSFORM was empty (e.g. preprocessor load failed badly)
    if not EXPECTED_COLS_FOR_TRANSFORM and not input_df.empty:
        # Fallback: try to use whatever columns are in input_df that might match general/categorical lists
        # This is risky and might not align with what the preprocessor was trained on.
        print("Peringatan: EXPECTED_COLS_FOR_TRANSFORM kosong. Mencoba menggunakan kolom dari input.")
        cols_to_use = [c for c in input_df.columns if c in ALL_NUMERIC_FEATURES_FROM_TRAINER or c in CATEGORICAL_FEATURES_FROM_TRAINER]
        if not cols_to_use:
             return {"risk_category": None, "probabilities": None, "error": "Tidak ada fitur yang cocok untuk pra-pemrosesan."}
        df_for_transform = input_df[cols_to_use]


    try:
        processed_input = PREPROCESSOR.transform(df_for_transform)
    except NotFittedError:
        return {"risk_category": None, "probabilities": None, "error": "Preprocessor belum dilatih."}
    except ValueError as ve:
        return {"risk_category": None, "probabilities": None, "error": f"ValueError saat pra-pemrosesan input: {ve}"}
    except KeyError as ke:
        print(f"KeyError saat pra-pemrosesan: {ke}. Ini mungkin karena df_for_transform tidak memiliki semua kolom yang diharapkan oleh PREPROCESSOR.transform, atau urutannya salah.")
        print(f"Kolom di df_for_transform: {df_for_transform.columns.tolist()}")
        print(f"Kolom yang diharapkan (numerik): {ALL_NUMERIC_FEATURES_FROM_TRAINER}")
        print(f"Kolom yang diharapkan (kategorikal): {CATEGORICAL_FEATURES_FROM_TRAINER}")
        return {"risk_category": None, "probabilities": None, "error": f"KeyError saat pra-pemrosesan input: {ke}. Periksa daftar fitur yang diharapkan."}
    except Exception as e:
        return {"risk_category": None, "probabilities": None, "error": f"Error tidak diketahui saat pra-pemrosesan: {e}"}

    try:
        prediction = MODEL.predict(processed_input)
        probabilities = MODEL.predict_proba(processed_input)
        model_classes = MODEL.classes_
        proba_dict = dict(zip(model_classes, probabilities[0]))
        
        return {
            "risk_category": prediction[0],
            "probabilities": proba_dict,
            "error": None
        }
    except NotFittedError:
         return {"risk_category": None, "probabilities": None, "error": "Model ML belum dilatih."}
    except Exception as e:
        return {
            "risk_category": None,
            "probabilities": None,
            "error": f"Error saat melakukan prediksi ML: {e}"
        }

if __name__ == '__main__':
    print("Contoh Prediksi menggunakan ML Credit Risk Predictor:")
    if MODEL is None or PREPROCESSOR is None:
        print("Model atau Preprocessor tidak dimuat. Jalankan incremental_model_trainer.py terlebih dahulu untuk melatih dan menyimpan model.")
    else:
        sample_data_pertambangan = {
            'CurrentRatio': 1.5, 'DebtToEquityRatio': 0.8, 'NetProfitMargin': 0.1,
            'ROA': 0.05, 'ROE': 0.12, 'InterestCoverageRatio': 5.0,
            'SalesGrowth': 0.1, 'AssetTurnover': 1.0, 'QuickRatio': 1.0, 'OperatingMargin': 0.15,
            'Mining_ProductionVolume': 3000, 'Mining_ReserveLife': 10, 'Mining_CashCostPerUnit': 30,
            'Mining_CommodityPriceExposure': 0.7, 'Mining_CapexIntensity': 0.1
        }
        result_tambang = predict_credit_risk_ml(sample_data_pertambangan, sector='Pertambangan')
        print(f"\nHasil Prediksi untuk Pertambangan: {result_tambang}")

        sample_data_konstruksi = {
            'CurrentRatio': 1.2, 'DebtToEquityRatio': 1.5, 'NetProfitMargin': 0.05,
            'ROA': 0.03, 'ROE': 0.08, 'InterestCoverageRatio': 3.0,
            'SalesGrowth': 0.05, 'AssetTurnover': 1.2, 'QuickRatio': 0.8, 'OperatingMargin': 0.07,
            'Construction_OrderBookValue': 2000, 'Construction_ProjectCompletionRate': 0.8,
            'Construction_BacklogToRevenueRatio': 1.5, 
            'Construction_DebtServiceCoverageRatio_Project': 1.5, 
            'Construction_SubcontractorRiskExposure': 0.4
        }
        result_konstruksi = predict_credit_risk_ml(sample_data_konstruksi, sector='Konstruksi')
        print(f"\nHasil Prediksi untuk Konstruksi: {result_konstruksi}")

        sample_data_minimal = {
            'CurrentRatio': 1.0, 'DebtToEquityRatio': 2.0, 'NetProfitMargin': 0.02,
            'ROA': 0.01, 'ROE': 0.03
        }
        result_minimal_agro = predict_credit_risk_ml(sample_data_minimal, sector='Agro')
        print(f"\nHasil Prediksi untuk Agro (data minimal): {result_minimal_agro}")
