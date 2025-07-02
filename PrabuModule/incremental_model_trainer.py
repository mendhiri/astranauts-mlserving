import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from catboost import CatBoostClassifier
from sklearn.metrics import classification_report
from sklearn.exceptions import NotFittedError
import joblib
import os
import glob
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'trained_models')
MODEL_PATH = os.path.join(MODEL_DIR, 'incremental_risk_model.cbm') # Changed extension for CatBoost native format
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, 'preprocessor.joblib')
CLASSES_PATH = os.path.join(MODEL_DIR, 'classes.npy')
LABEL_ENCODER_PATH = os.path.join(MODEL_DIR, 'label_encoder.joblib')


# Pastikan direktori model ada
os.makedirs(MODEL_DIR, exist_ok=True)

# Definisi fitur
GENERAL_FEATURES = [
    'CurrentRatio', 'DebtToEquityRatio', 'NetProfitMargin', 'ROA', 'ROE',
    'InterestCoverageRatio', 'SalesGrowth', 'AssetTurnover', 'QuickRatio', 'OperatingMargin'
]

SECTOR_SPECIFIC_FEATURES_MAP = {
    'Pertambangan': [
        'Mining_ProductionVolume', 'Mining_ReserveLife', 'Mining_CashCostPerUnit',
        'Mining_CommodityPriceExposure', 'Mining_CapexIntensity'
    ],
    'Konstruksi': [
        'Construction_OrderBookValue', 'Construction_ProjectCompletionRate',
        'Construction_BacklogToRevenueRatio', 'Construction_DebtServiceCoverageRatio_Project',
        'Construction_SubcontractorRiskExposure'
    ],
    'Agro': [
        'Agro_PlantedArea', 'Agro_YieldPerHectare', 'Agro_CommodityPriceVolatility',
        'Agro_AgeOfPlantation', 'Agro_StorageCapacityUtilization'
    ],
    'Manufaktur Alat Berat': [
        'Manufacturing_ProductionCapacity', 'Manufacturing_InventoryTurnoverDays_FG',
        'Manufacturing_OrderBacklog', 'Manufacturing_RDExpenditureAsPercentageOfSales',
        'Manufacturing_SupplierConcentrationRisk'
    ],
    'Logistik Alat Berat': [
        'Logistics_FleetSize', 'Logistics_FleetUtilizationRate', 'Logistics_AverageFleetAge',
        'Logistics_MaintenanceCostRatio', 'Logistics_ClientConcentrationRisk'
    ]
}

ALL_SECTOR_SPECIFIC_NUMERIC_FEATURES = list(set(f for features in SECTOR_SPECIFIC_FEATURES_MAP.values() for f in features))
ALL_NUMERIC_FEATURES = GENERAL_FEATURES + ALL_SECTOR_SPECIFIC_NUMERIC_FEATURES
CATEGORICAL_FEATURES = ['Sektor'] # CatBoost will handle this
TARGET_COLUMN = 'RiskCategory'

def load_data_from_csv(file_path):
    df = pd.read_csv(file_path)
    # Ensure categorical features are treated as strings, CatBoost handles NaN in them
    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df

def load_all_datasets(dataset_folder='PrabuModule/datasets'):
    all_files = glob.glob(os.path.join(dataset_folder, "*.csv"))
    if not all_files:
        print("Tidak ada file CSV ditemukan di folder dataset.")
        return pd.DataFrame()
    
    df_list = []
    for f in all_files:
        try:
            df_temp = load_data_from_csv(f) # Use the modified load_data_from_csv
            df_list.append(df_temp)
        except Exception as e:
            print(f"Gagal membaca file {f}: {e}")
    
    if not df_list:
        print("Tidak ada data yang berhasil dimuat dari file CSV.")
        return pd.DataFrame()
        
    combined_df = pd.concat(df_list, ignore_index=True)
    # Ensure all numeric features are present, fill with NaN if not (CatBoost handles NaN)
    for col in ALL_NUMERIC_FEATURES:
        if col not in combined_df.columns:
            combined_df[col] = np.nan
    return combined_df

def get_preprocessor(df_for_fitting_preprocessor):
    # This preprocessor will now only handle numeric features: impute and scale.
    # Categorical features will be handled by CatBoost directly.
    if os.path.exists(PREPROCESSOR_PATH):
        print("Memuat preprocessor numerik yang sudah ada...")
        return joblib.load(PREPROCESSOR_PATH)

    print("Membuat preprocessor numerik baru...")
    # CatBoost will handle NaNs internally. We only scale numeric features.
    numeric_transformer = Pipeline(steps=[
        # ('imputer', SimpleImputer(strategy='mean')), # Removed: CatBoost will handle NaN
        ('scaler', StandardScaler())
    ])

    # Filter ALL_NUMERIC_FEATURES to only include those present in df_for_fitting_preprocessor
    existing_numeric_features_in_df = [col for col in ALL_NUMERIC_FEATURES if col in df_for_fitting_preprocessor.columns]
    
    if not existing_numeric_features_in_df:
        print("Tidak ada fitur numerik yang ditemukan dalam data untuk melatih preprocessor.")
        # Return a dummy preprocessor or handle this case as an error
        return None 

    # We only define transformers for numeric features. Categorical features are passed to CatBoost.
    # `remainder='passthrough'` would keep other columns, but we'll manage feature set manually for CatBoost.
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, existing_numeric_features_in_df)
        ],
        remainder='drop' # Drop any other columns not specified (e.g. UniqueID, etc.)
    )
    
    print(f"Melatih preprocessor numerik pada kolom: {existing_numeric_features_in_df}")
    preprocessor.fit(df_for_fitting_preprocessor[existing_numeric_features_in_df])
    
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    print(f"Preprocessor numerik baru disimpan di {PREPROCESSOR_PATH}")
    return preprocessor

def get_label_encoder(y_series):
    if os.path.exists(LABEL_ENCODER_PATH):
        print("Memuat LabelEncoder yang sudah ada...")
        le = joblib.load(LABEL_ENCODER_PATH)
    else:
        print("Membuat LabelEncoder baru...")
        le = LabelEncoder()
        le.fit(y_series)
        joblib.dump(le, LABEL_ENCODER_PATH)
        np.save(CLASSES_PATH, le.classes_) # Save string class names
        print(f"LabelEncoder baru disimpan di {LABEL_ENCODER_PATH}")
        print(f"Kelas target (string) disimpan: {le.classes_}")
    return le

def train_initial_model(df_initial_data, force_retrain_preprocessor=False, force_retrain_labelencoder=False):
    if df_initial_data.empty:
        print("Data awal kosong, tidak bisa melatih model.")
        return None, None, None

    X = df_initial_data.drop(columns=[TARGET_COLUMN], errors='ignore')
    y_raw = df_initial_data[TARGET_COLUMN]
    
    if force_retrain_preprocessor and os.path.exists(PREPROCESSOR_PATH):
        os.remove(PREPROCESSOR_PATH)
        print("Preprocessor numerik lama dihapus untuk pelatihan ulang.")
    
    if force_retrain_labelencoder:
        if os.path.exists(LABEL_ENCODER_PATH): os.remove(LABEL_ENCODER_PATH)
        if os.path.exists(CLASSES_PATH): os.remove(CLASSES_PATH)
        print("LabelEncoder dan file kelas lama dihapus untuk pelatihan ulang.")

    label_encoder = get_label_encoder(y_raw)
    y = label_encoder.transform(y_raw) # y is now numerically encoded
    
    # Preprocessor for numeric features
    numeric_preprocessor = get_preprocessor(X)
    
    # Identify numeric and categorical features for CatBoost
    # Numeric features are those handled by the preprocessor
    numeric_features_for_model = [col for col in ALL_NUMERIC_FEATURES if col in X.columns]
    # Categorical features are specified by name
    categorical_features_for_model = [col for col in CATEGORICAL_FEATURES if col in X.columns]

    # Prepare data for CatBoost: Apply numeric preprocessing, keep categorical as is (CatBoost handles them)
    X_processed_numeric = pd.DataFrame(numeric_preprocessor.transform(X[numeric_features_for_model]), columns=numeric_features_for_model, index=X.index)
    X_final_for_model = pd.concat([X_processed_numeric, X[categorical_features_for_model].reset_index(drop=True)], axis=1)
    
    # CatBoost needs to know which features are categorical by their names or indices in X_final_for_model
    cat_feature_indices = [X_final_for_model.columns.get_loc(col) for col in categorical_features_for_model]

    model = CatBoostClassifier(
        iterations=200,  # example value
        learning_rate=0.1, # example value
        depth=6,           # example value
        loss_function='MultiClass',
        eval_metric='MultiClass',
        random_seed=42,
        logging_level='Silent',
        # class_weights= # Can be set if classes are imbalanced, e.g. compute from y_raw
    )
    
    print("Melatih model awal CatBoost...")
    model.fit(
        X_final_for_model, y,
        cat_features=cat_feature_indices,
        # verbose=10 # To see training progress
    )
    
    model.save_model(MODEL_PATH, format="cbm") # Save in CatBoost binary format
    print(f"Model awal CatBoost disimpan di {MODEL_PATH}")
    
    y_pred_encoded = model.predict(X_final_for_model)
    y_pred_labels = label_encoder.inverse_transform(y_pred_encoded.flatten().astype(int)) # Ensure 1D for inverse_transform

    print("Laporan Klasifikasi pada Data Pelatihan Awal:")
    print(classification_report(y_raw, y_pred_labels, labels=label_encoder.classes_, zero_division=0))
    
    return model, numeric_preprocessor, label_encoder


def update_model_incrementally(df_new_data, existing_model_path=None, preprocessor=None, label_encoder=None):
    if df_new_data.empty:
        print("Data baru kosong, tidak ada pembaruan model.")
        return None # Or return the existing model if passed

    X_new = df_new_data.drop(columns=[TARGET_COLUMN], errors='ignore')
    y_new_raw = df_new_data[TARGET_COLUMN]

    if preprocessor is None:
        if os.path.exists(PREPROCESSOR_PATH):
            preprocessor = joblib.load(PREPROCESSOR_PATH)
        else:
            print("Preprocessor numerik tidak ditemukan. Latih model awal terlebih dahulu.")
            return None
    
    if label_encoder is None:
        if os.path.exists(LABEL_ENCODER_PATH):
            label_encoder = joblib.load(LABEL_ENCODER_PATH)
        else: # Should not happen if train_initial_model was called
            print("LabelEncoder tidak ditemukan. Latih model awal terlebih dahulu.")
            return None
    
    # Check for new classes in y_new_raw and update label_encoder if necessary
    # This is complex for incremental updates if CatBoost model structure (output layer) can't change easily.
    # For simplicity, CatBoost's `fit` with `init_model` expects same classes.
    # If new classes appear, a full retrain or a more complex strategy is needed.
    # Here, we assume classes are known from initial training or we retrain label_encoder.
    # For now, let's assume new data doesn't introduce new classes not seen by label_encoder.
    # If it does, label_encoder.transform will fail.
    try:
        y_new_encoded = label_encoder.transform(y_new_raw)
    except ValueError as e:
        print(f"Data baru mengandung kelas target yang tidak dikenal: {e}. Model tidak dapat diperbarui secara langsung dengan kelas baru ini.")
        # Option: retrain label_encoder and model from scratch with all data.
        # Option: ignore new data with unknown classes for this update.
        return joblib.load(existing_model_path) if existing_model_path and os.path.exists(existing_model_path) else None


    numeric_features_for_model = [col for col in ALL_NUMERIC_FEATURES if col in X_new.columns]
    categorical_features_for_model = [col for col in CATEGORICAL_FEATURES if col in X_new.columns]

    X_new_processed_numeric = pd.DataFrame(preprocessor.transform(X_new[numeric_features_for_model]), columns=numeric_features_for_model, index=X_new.index)
    X_new_final_for_model = pd.concat([X_new_processed_numeric, X_new[categorical_features_for_model].reset_index(drop=True)], axis=1)

    cat_feature_indices = [X_new_final_for_model.columns.get_loc(col) for col in categorical_features_for_model]

    # Load existing model to continue training
    if existing_model_path and os.path.exists(existing_model_path):
        print(f"Memuat model CatBoost dari {existing_model_path} untuk pembaruan...")
        updated_model = CatBoostClassifier()
        updated_model.load_model(existing_model_path)
    else:
        print("Model awal tidak ditemukan untuk pembaruan. Ini seharusnya tidak terjadi jika alur diikuti.")
        # Fallback: train a new model just on this new data (not ideal for 'incremental')
        # Or, better, require train_initial_model to be run first.
        return None 

    print("Memperbarui model CatBoost secara inkremental (melanjutkan pelatihan)...")
    updated_model.fit(
        X_new_final_for_model, y_new_encoded,
        cat_features=cat_feature_indices,
        init_model=updated_model, # Use the loaded model as a starting point
        # verbose=10
    )

    updated_model.save_model(existing_model_path) # Overwrite the model with the updated one
    print(f"Model CatBoost yang diperbarui disimpan di {existing_model_path}")

    y_pred_encoded = updated_model.predict(X_new_final_for_model)
    y_pred_labels = label_encoder.inverse_transform(y_pred_encoded.flatten().astype(int))
    
    print("Laporan Klasifikasi pada Data Baru (setelah pembaruan):")
    print(classification_report(y_new_raw, y_pred_labels, labels=label_encoder.classes_, zero_division=0))
    
    return updated_model


def predict_risk(data_input_dict, model_path=MODEL_PATH, preprocessor_path=PREPROCESSOR_PATH, label_encoder_path=LABEL_ENCODER_PATH):
    model = CatBoostClassifier()
    if os.path.exists(model_path):
        model.load_model(model_path)
    else:
        print("Model CatBoost tidak ditemukan untuk prediksi.")
        return None, None
            
    if os.path.exists(preprocessor_path):
        preprocessor = joblib.load(preprocessor_path)
    else:
        print("Preprocessor numerik tidak ditemukan untuk prediksi.")
        return None, None
        
    if os.path.exists(label_encoder_path):
        label_encoder = joblib.load(label_encoder_path)
    else:
        print("LabelEncoder tidak ditemukan untuk prediksi.")
        return None, None

    df_input = pd.DataFrame([data_input_dict])
    
    # Ensure 'Sektor' is string, fill other NAs for numeric features for preprocessor
    for col in CATEGORICAL_FEATURES:
        if col in df_input.columns:
            df_input[col] = df_input[col].astype(str)
        else: # If a categorical feature like Sektor is missing from input
            df_input[col] = 'Unknown' # Or some placeholder CatBoost can handle

    # Ensure all ALL_NUMERIC_FEATURES are present, fill with NaN if missing, preprocessor's imputer will handle this
    numeric_features_in_input = []
    for col in ALL_NUMERIC_FEATURES: 
        if col not in df_input.columns:
            df_input[col] = np.nan 
        if col in df_input.columns: # Check again because it might have been added
             numeric_features_in_input.append(col)
    
    # Get the list of numeric features the preprocessor was actually trained on
    # This should be stored or inferred reliably from the preprocessor object
    try:
        # Example: if preprocessor is ColumnTransformer, get feature names from its 'num' part
        # This part needs to be robust. Assuming preprocessor.transformers_[0][2] holds the list.
        # For safety, let's use the features present in input that are also in ALL_NUMERIC_FEATURES
        expected_numeric_cols_for_transform = preprocessor.transformers_[0][2]
    except AttributeError: # If preprocessor is not a ColumnTransformer or structure is different
        print("Warning: Could not reliably determine preprocessor's expected numeric features. Using intersection of input and ALL_NUMERIC_FEATURES.")
        expected_numeric_cols_for_transform = [f for f in numeric_features_in_input if f in ALL_NUMERIC_FEATURES]


    df_input_numeric_processed = pd.DataFrame(preprocessor.transform(df_input[expected_numeric_cols_for_transform]), columns=expected_numeric_cols_for_transform, index=df_input.index)
    
    # Categorical features for the model
    categorical_features_for_model = [col for col in CATEGORICAL_FEATURES if col in df_input.columns]
    df_input_final = pd.concat([df_input_numeric_processed, df_input[categorical_features_for_model].reset_index(drop=True)], axis=1)
    
    # Ensure column order matches training if CatBoost is sensitive (usually not if using feature names)
    # For `cat_features` indices, they are based on X_final_for_model during training.
    # So, the order of columns in df_input_final should ideally match that.
    # However, CatBoost `predict` can often handle DataFrames with feature names directly.
    
    # Get categorical feature indices for prediction time based on df_input_final columns
    cat_feature_indices_pred = [df_input_final.columns.get_loc(col) for col in categorical_features_for_model if col in df_input_final.columns]

    try:
        prediction_encoded = model.predict(df_input_final, cat_features=cat_feature_indices_pred)
        proba = model.predict_proba(df_input_final, cat_features=cat_feature_indices_pred)
        
        # Prediction is likely [[index]], flatten and convert to int for label_encoder
        predicted_label = label_encoder.inverse_transform(prediction_encoded.astype(int).flatten())[0]
        
        proba_dict = dict(zip(label_encoder.classes_, proba[0]))
        return predicted_label, proba_dict
    except NotFittedError:
        print("Model CatBoost belum dilatih (NotFittedError).")
        return None, None
    except Exception as e:
        print(f"Error saat prediksi CatBoost: {e}")
        return None, None

if __name__ == '__main__':
    print("Menjalankan contoh alur kerja incremental_model_trainer dengan CatBoost...")
    # Clean up old model files for a fresh run
    if os.path.exists(MODEL_PATH): os.remove(MODEL_PATH)
    if os.path.exists(PREPROCESSOR_PATH): os.remove(PREPROCESSOR_PATH)
    if os.path.exists(CLASSES_PATH): os.remove(CLASSES_PATH)
    if os.path.exists(LABEL_ENCODER_PATH): os.remove(LABEL_ENCODER_PATH)
    print("Model, preprocessor, label encoder, dan file kelas lama (jika ada) telah dihapus untuk demo.")

    all_data = load_all_datasets()

    if all_data.empty:
        print("Tidak ada data untuk dijalankan. Keluar.")
    else:
        print(f"Total data dimuat: {len(all_data)} baris.")
        
        # Example: Split data for initial training and incremental updates
        # This is a simplified split. In reality, data might arrive chronologically or by other means.
        if len(all_data) >= 10:
             df_initial = all_data.sample(frac=0.7, random_state=42)
             df_new_incremental = all_data.drop(df_initial.index)
        elif len(all_data) > 0:
            df_initial = all_data 
            df_new_incremental = pd.DataFrame() 
        else: # Should be caught by all_data.empty()
            df_initial = pd.DataFrame()
            df_new_incremental = pd.DataFrame()

        print(f"Data awal untuk pelatihan: {len(df_initial)} baris.")
        print(f"Data baru untuk pembaruan inkremental: {len(df_new_incremental)} baris.")

        trained_model = None
        if not df_initial.empty:
            # Force retrain preprocessor and label encoder for the first run
            trained_model, preproc, lbl_enc = train_initial_model(
                df_initial, 
                force_retrain_preprocessor=True, 
                force_retrain_labelencoder=True
            )

            if trained_model and not df_new_incremental.empty:
                print("\n--- Memperbarui model dengan data inkremental ---")
                # Simulate incremental update with the rest of the data
                # In a real scenario, df_new_incremental might be a stream or smaller batches
                trained_model = update_model_incrementally(
                    df_new_incremental, 
                    existing_model_path=MODEL_PATH, # Pass the path to the saved initial model
                    preprocessor=preproc, 
                    label_encoder=lbl_enc
                )
            elif not df_new_incremental.empty:
                 print("Pelatihan model awal gagal, pembaruan inkremental dilewati.")

            if trained_model: # Check if model is available (either initial or updated)
                print("\n--- Melakukan prediksi pada sampel data ---")
                # Use a sample from the incremental data if available, else from initial
                sample_source_df = df_new_incremental if not df_new_incremental.empty else df_initial
                if not sample_source_df.empty:
                    sample_input_series = sample_source_df.drop(columns=[TARGET_COLUMN], errors='ignore').iloc[0]
                    sample_actual_category = sample_source_df[TARGET_COLUMN].iloc[0]
                    
                    sample_input_dict = sample_input_series.to_dict()
                    
                    # For 'Sektor', ensure it's part of the dict if it was a named series index or similar
                    if 'Sektor' not in sample_input_dict and 'Sektor' in sample_input_series.index:
                         sample_input_dict['Sektor'] = sample_input_series['Sektor']
                    elif 'Sektor' not in sample_input_dict and 'Sektor' in df_initial.columns : # Fallback if series lost it
                         sample_input_dict['Sektor'] = df_initial[df_initial.index == sample_input_series.name]['Sektor'].iloc[0]


                    print(f"Input untuk prediksi (data dari baris acak):")
                    # print(sample_input_dict) 
                    
                    # Make sure 'Sektor' key exists in the sample_input_dict for predict_risk
                    if 'Sektor' not in sample_input_dict:
                        print("Peringatan: 'Sektor' tidak ada dalam input dictionary untuk prediksi. Ini mungkin menyebabkan error.")
                        # Attempt to add it if it's an index or known from the source series
                        if isinstance(sample_input_series.name, tuple) and 'Sektor' in sample_input_series.name.index: # MultiIndex
                             sample_input_dict['Sektor'] = sample_input_series.name['Sektor']
                        # This part might need more robust handling based on how sample_input_series is structured

                    predicted_category, probabilities = predict_risk(sample_input_dict) # Uses default paths
                    print(f"Prediksi Kategori Risiko: {predicted_category}")
                    print(f"Probabilitas: {probabilities}")
                    print(f"Kategori Sebenarnya: {sample_actual_category}")
                else:
                    print("Tidak ada data sampel untuk prediksi.")
            else:
                print("Model tidak tersedia untuk prediksi (mungkin gagal dilatih atau diperbarui).")
        else:
            print("Tidak ada data awal yang cukup untuk melatih model.")
