import os
import joblib
import pandas as pd
import numpy as np
from sklearn.exceptions import NotFittedError
from catboost import CatBoostClassifier # Import CatBoost
# from sklearn.preprocessing import LabelEncoder # Not directly used here if trainer handles it

# Path ke model dan preprocessor yang sudah dilatih
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'trained_models', 'incremental_risk_model.cbm') # CatBoost model path
PREPROCESSOR_PATH = os.path.join(BASE_DIR, 'trained_models', 'preprocessor.joblib') # Numeric preprocessor
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, 'trained_models', 'label_encoder.joblib')

MODEL = None
NUMERIC_PREPROCESSOR = None
LABEL_ENCODER = None

# These will be loaded from incremental_model_trainer constants for consistency
try:
    from .incremental_model_trainer import ALL_NUMERIC_FEATURES, CATEGORICAL_FEATURES
except ImportError: # Fallback for standalone execution or testing
    print("Warning: Could not import feature lists from incremental_model_trainer. Using placeholders.")
    ALL_NUMERIC_FEATURES = [] # Placeholder
    CATEGORICAL_FEATURES = ['Sektor'] # Placeholder

# Define the mapping from risk category to score
RISK_CATEGORY_TO_SCORE_MAP = {
    "Low": 20,
    "Medium": 50,
    "High": 80,
    # Default score for unknown or None categories
    None: np.nan # Or some other default like 0 or 50
}


def _load_resources():
    global MODEL, NUMERIC_PREPROCESSOR, LABEL_ENCODER
    
    if os.path.exists(MODEL_PATH):
        MODEL = CatBoostClassifier()
        MODEL.load_model(MODEL_PATH)
        print(f"Model CatBoost dimuat dari {MODEL_PATH}")
    else:
        print(f"PERINGATAN: File model CatBoost tidak ditemukan di {MODEL_PATH}. Prediksi ML tidak akan berfungsi.")
        MODEL = None

    if os.path.exists(PREPROCESSOR_PATH):
        NUMERIC_PREPROCESSOR = joblib.load(PREPROCESSOR_PATH)
        print(f"Preprocessor numerik dimuat dari {PREPROCESSOR_PATH}")
    else:
        print(f"PERINGATAN: File preprocessor numerik tidak ditemukan di {PREPROCESSOR_PATH}. Prediksi ML mungkin tidak akurat.")
        NUMERIC_PREPROCESSOR = None
    
    if os.path.exists(LABEL_ENCODER_PATH):
        LABEL_ENCODER = joblib.load(LABEL_ENCODER_PATH)
        print(f"LabelEncoder dimuat dari {LABEL_ENCODER_PATH}")
    else:
        print(f"PERINGATAN: File LabelEncoder tidak ditemukan di {LABEL_ENCODER_PATH}. Prediksi kategori mungkin gagal.")
        LABEL_ENCODER = None

_load_resources()

def predict_credit_risk_ml(financial_data_dict: dict, sector: str) -> dict:
    global MODEL, NUMERIC_PREPROCESSOR, LABEL_ENCODER, ALL_NUMERIC_FEATURES, CATEGORICAL_FEATURES

    default_return = {
        "risk_category": None,
        "risk_score": np.nan,
        "probabilities": None,
        "error": None
    }

    if MODEL is None or NUMERIC_PREPROCESSOR is None or LABEL_ENCODER is None:
        default_return["error"] = "Model ML, Preprocessor, atau LabelEncoder tidak dimuat. Prediksi tidak dapat dilakukan."
        return default_return

    input_df = pd.DataFrame([financial_data_dict])
    
    # --- Data Preparation for CatBoost ---
    # 1. Handle Categorical Features (ensure 'Sektor' is string)
    input_df['Sektor'] = str(sector) # Ensure sector is string
    for col in CATEGORICAL_FEATURES: # Ensure all expected categoricals are strings
        if col in input_df.columns:
            input_df[col] = input_df[col].astype(str)
        else: # If a categorical feature is missing (e.g. Sektor was not in financial_data_dict)
            if col == 'Sektor': # Should have been set above
                 pass
            else: # Other potential categorical features
                input_df[col] = 'Unknown' # Or np.nan, CatBoost handles string 'nan' or actual np.nan

    # 2. Handle Numeric Features (ensure all expected are present, fill with NaN for CatBoost)
    # These are the features the numeric_preprocessor was trained on.
    try:
        # Get the list of numeric features the preprocessor was actually trained on
        expected_numeric_cols_for_transform = NUMERIC_PREPROCESSOR.transformers_[0][2]
    except Exception: # Fallback if introspection fails (e.g. preprocessor is not ColumnTransformer)
        print("Warning: Could not reliably determine preprocessor's expected numeric features from its structure. Using ALL_NUMERIC_FEATURES.")
        expected_numeric_cols_for_transform = [f for f in ALL_NUMERIC_FEATURES if f in input_df.columns]
        if not expected_numeric_cols_for_transform: # If no common features, take all from input_df
            expected_numeric_cols_for_transform = [f for f in input_df.columns if f not in CATEGORICAL_FEATURES]


    # Ensure all expected numeric columns are in input_df, fill missing with np.nan
    for col in expected_numeric_cols_for_transform:
        if col not in input_df.columns:
            input_df[col] = np.nan
    
    # Select only the numeric columns expected by the preprocessor for transformation
    input_df_numeric_part = input_df[expected_numeric_cols_for_transform]

    try:
        processed_numeric_part = NUMERIC_PREPROCESSOR.transform(input_df_numeric_part)
        df_processed_numeric = pd.DataFrame(processed_numeric_part, columns=expected_numeric_cols_for_transform, index=input_df.index)
    except NotFittedError:
        default_return["error"] = "Preprocessor numerik belum dilatih."
        return default_return
    except ValueError as ve:
        default_return["error"] = f"ValueError saat pra-pemrosesan input numerik: {ve}"
        return default_return
    except Exception as e:
        default_return["error"] = f"Error tidak diketahui saat pra-pemrosesan numerik: {e}"
        return default_return

    # 3. Combine processed numeric features with original categorical features for CatBoost
    # Ensure only expected categorical features are selected
    categorical_features_for_model = [col for col in CATEGORICAL_FEATURES if col in input_df.columns]
    df_final_for_model = pd.concat([df_processed_numeric, input_df[categorical_features_for_model].reset_index(drop=True)], axis=1)
    
    # CatBoost needs to know which features are categorical by their names or indices
    # These indices are relative to the columns in df_final_for_model
    cat_feature_indices_pred = [df_final_for_model.columns.get_loc(col) for col in categorical_features_for_model if col in df_final_for_model.columns]

    try:
        prediction_encoded = MODEL.predict(df_final_for_model, cat_features=cat_feature_indices_pred)
        probabilities_array = MODEL.predict_proba(df_final_for_model, cat_features=cat_feature_indices_pred)
        
        # Prediction_encoded is likely [[index]], flatten and convert to int for label_encoder
        predicted_category_label = LABEL_ENCODER.inverse_transform(prediction_encoded.astype(int).flatten())[0]
        
        proba_dict = dict(zip(LABEL_ENCODER.classes_, probabilities_array[0]))
        
        # Map predicted category to numeric score
        predicted_score = RISK_CATEGORY_TO_SCORE_MAP.get(predicted_category_label, np.nan) # Default to NaN if category not in map
        
        return {
            "risk_category": predicted_category_label,
            "risk_score": predicted_score,
            "probabilities": proba_dict,
            "error": None
        }
    except NotFittedError:
         default_return["error"] = "Model CatBoost belum dilatih."
         return default_return
    except Exception as e:
        default_return["error"] = f"Error saat melakukan prediksi CatBoost: {e}"
        return default_return

if __name__ == '__main__':
    print("Contoh Prediksi menggunakan ML Credit Risk Predictor (CatBoost):")
    if MODEL is None or NUMERIC_PREPROCESSOR is None or LABEL_ENCODER is None:
        print("Model, Preprocessor Numerik, atau LabelEncoder tidak dimuat. Pastikan incremental_model_trainer.py telah dijalankan.")
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
