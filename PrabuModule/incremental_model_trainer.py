import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report
from sklearn.exceptions import NotFittedError
import joblib
import os
import glob
from sklearn.impute import SimpleImputer

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'trained_models')
MODEL_PATH = os.path.join(MODEL_DIR, 'incremental_risk_model.joblib')
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, 'preprocessor.joblib')
CLASSES_PATH = os.path.join(MODEL_DIR, 'classes.npy')

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
CATEGORICAL_FEATURES = ['Sektor']
TARGET_COLUMN = 'RiskCategory'

def load_data_from_csv(file_path):
    return pd.read_csv(file_path)

def load_all_datasets(dataset_folder='PrabuModule/datasets'):
    all_files = glob.glob(os.path.join(dataset_folder, "*.csv"))
    if not all_files:
        print("Tidak ada file CSV ditemukan di folder dataset.")
        return pd.DataFrame()
    
    df_list = []
    for f in all_files:
        try:
            df_list.append(pd.read_csv(f))
        except Exception as e:
            print(f"Gagal membaca file {f}: {e}")
    
    if not df_list:
        print("Tidak ada data yang berhasil dimuat dari file CSV.")
        return pd.DataFrame()
        
    return pd.concat(df_list, ignore_index=True)

def get_preprocessor(df_for_fitting_preprocessor):
    if os.path.exists(PREPROCESSOR_PATH):
        print("Memuat preprocessor yang sudah ada...")
        return joblib.load(PREPROCESSOR_PATH)

    print("Membuat preprocessor baru...")
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value=0)),
        ('scaler', StandardScaler())
    ])
    categorical_transformer = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    # Filter ALL_NUMERIC_FEATURES to only include those present in df_for_fitting_preprocessor
    # This is crucial if df_for_fitting_preprocessor is a subset and doesn't have all possible sector features yet
    existing_numeric_features_in_df = [col for col in ALL_NUMERIC_FEATURES if col in df_for_fitting_preprocessor.columns]

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, existing_numeric_features_in_df),
            ('cat', categorical_transformer, CATEGORICAL_FEATURES)
        ],
        remainder='drop' 
    )
    
    print(f"Melatih preprocessor pada kolom: {existing_numeric_features_in_df + CATEGORICAL_FEATURES}")
    # Fit preprocessor only on the columns that exist in the provided dataframe.
    # OneHotEncoder will learn categories from 'Sektor'. StandardScaler from existing numeric features.
    preprocessor.fit(df_for_fitting_preprocessor[existing_numeric_features_in_df + CATEGORICAL_FEATURES])
    
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    print(f"Preprocessor baru disimpan di {PREPROCESSOR_PATH}")
    return preprocessor

def train_initial_model(df_initial_data, force_retrain_preprocessor=False):
    if df_initial_data.empty:
        print("Data awal kosong, tidak bisa melatih model.")
        return None, None

    X = df_initial_data.copy()
    y = X.pop(TARGET_COLUMN)
    
    if force_retrain_preprocessor and os.path.exists(PREPROCESSOR_PATH):
        os.remove(PREPROCESSOR_PATH)
        print("Preprocessor lama dihapus untuk pelatihan ulang.")
        
    preprocessor = get_preprocessor(df_initial_data) 
    
    # Use the actual features list the preprocessor was trained on
    # This can be derived from the preprocessor object itself for consistency
    # For ColumnTransformer, feature_names_in_ might be useful or inspecting transformers_
    processed_feature_names = []
    for name, trans, columns in preprocessor.transformers_:
        if hasattr(trans, 'get_feature_names_out'):
            if name == 'cat': # OneHotEncoder
                 # Need to pass original categorical column names to get_feature_names_out
                processed_feature_names.extend(trans.get_feature_names_out(CATEGORICAL_FEATURES))
            else: # StandardScaler (after imputer)
                processed_feature_names.extend(trans.get_feature_names_out(columns)) # columns here are existing_numeric_features_in_df
        else: # If no get_feature_names_out (e.g. 'drop' or older sklearn)
            processed_feature_names.extend(columns)


    # Transform using only the features the preprocessor expects
    # The preprocessor was fitted on existing_numeric_features_in_df + CATEGORICAL_FEATURES
    # So, X must provide these columns.
    training_features = [col for col in ALL_NUMERIC_FEATURES if col in X.columns] + CATEGORICAL_FEATURES
    X_processed = preprocessor.transform(X[training_features])
    
    classes = np.unique(y)
    np.save(CLASSES_PATH, classes)
    print(f"Kelas target disimpan: {classes}")

    model = SGDClassifier(loss='log_loss', random_state=42, class_weight='balanced', warm_start=True)
    
    print("Melatih model awal...")
    model.fit(X_processed, y) 
    
    joblib.dump(model, MODEL_PATH)
    print(f"Model awal disimpan di {MODEL_PATH}")
    
    y_pred = model.predict(X_processed)
    print("Laporan Klasifikasi pada Data Pelatihan Awal:")
    print(classification_report(y, y_pred, labels=classes, zero_division=0)) # ensure all classes are in report
    
    return model, preprocessor

def update_model_incrementally(df_new_data, model=None, preprocessor=None):
    if df_new_data.empty:
        print("Data baru kosong, tidak ada pembaruan model.")
        return model

    X_new = df_new_data.copy()
    y_new = X_new.pop(TARGET_COLUMN)

    if preprocessor is None:
        if os.path.exists(PREPROCESSOR_PATH):
            preprocessor = joblib.load(PREPROCESSOR_PATH)
        else:
            print("Preprocessor tidak ditemukan. Latih model awal terlebih dahulu.")
            return None
    
    # Transform using only the features the preprocessor expects
    update_features = [col for col in ALL_NUMERIC_FEATURES if col in X_new.columns] + CATEGORICAL_FEATURES
    X_new_processed = preprocessor.transform(X_new[update_features])

    if model is None:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            print("Memuat model yang sudah ada untuk pembaruan...")
        else:
            print("Model tidak ditemukan. Latih model awal terlebih dahulu.")
            return None
            
    if not hasattr(model, 'partial_fit'):
        print("Model yang dimuat tidak mendukung partial_fit.")
        return model

    if os.path.exists(CLASSES_PATH):
        classes = np.load(CLASSES_PATH, allow_pickle=True)
    else:
        print("File kelas target tidak ditemukan.")
        classes = np.unique(y_new) 

    print("Memperbarui model secara inkremental...")
    try:
        if not hasattr(model, 'coef_'): 
             print("Model belum pernah dilatih, menggunakan partial_fit dengan classes.")
             model.partial_fit(X_new_processed, y_new, classes=classes)
        else:
             model.partial_fit(X_new_processed, y_new)
    except NotFittedError:
        print("Model belum pernah dilatih (NotFittedError), menggunakan partial_fit dengan classes.")
        model.partial_fit(X_new_processed, y_new, classes=classes)
    except ValueError as ve:
        print(f"ValueError selama partial_fit: {ve}")
        return model 

    joblib.dump(model, MODEL_PATH)
    print(f"Model yang diperbarui disimpan di {MODEL_PATH}")

    y_pred_new = model.predict(X_new_processed)
    print("Laporan Klasifikasi pada Data Baru (setelah pembaruan):")
    # Ensure all known classes are passed to labels for consistent report
    all_known_classes = np.load(CLASSES_PATH, allow_pickle=True) if os.path.exists(CLASSES_PATH) else np.unique(y_new)
    print(classification_report(y_new, y_pred_new, labels=all_known_classes, zero_division=0))
    
    return model

def predict_risk(data_input_dict, model=None, preprocessor=None):
    if model is None:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
        else:
            print("Model tidak ditemukan untuk prediksi.")
            return None, None
            
    if preprocessor is None:
        if os.path.exists(PREPROCESSOR_PATH):
            preprocessor = joblib.load(PREPROCESSOR_PATH)
        else:
            print("Preprocessor tidak ditemukan untuk prediksi.")
            return None, None

    df_input = pd.DataFrame([data_input_dict])
    
    # Ensure all columns preprocessor was trained on are present for transform
    # These are `preprocessor.feature_names_in_` or derived from its transformers
    # For simplicity, we use the list derived when preprocessor was fitted.
    # This requires careful handling if preprocessor was fit on a subset of ALL_NUMERIC_FEATURES.
    
    # Get the actual numeric feature names the preprocessor was fitted with
    # This is a bit tricky as ColumnTransformer might not directly expose this easily for all its sub-transformers
    # A robust way is to save this list when `get_preprocessor` fits.
    # For now, we assume `existing_numeric_features_in_df` from `get_preprocessor` is what we need.
    # However, `get_preprocessor` is only called during training.
    # A better way: save the list of columns used to fit the preprocessor.
    # Let's assume PREPROCESSOR_FEATURES_LIST_PATH for this.
    
    # Simplified: ensure all ALL_NUMERIC_FEATURES and CATEGORICAL_FEATURES are available, fill with NaN if missing.
    # The imputer in the preprocessor should handle these NaNs.
    for col in ALL_NUMERIC_FEATURES: # All possible numeric features
        if col not in df_input.columns:
            df_input[col] = np.nan 
    for col in CATEGORICAL_FEATURES: # All categorical features
        if col not in df_input.columns:
            df_input[col] = None # Or a placeholder that OneHotEncoder can ignore or handle

    # The preprocessor expects specific columns in a specific order based on its fitting.
    # We need to provide df_input with columns that preprocessor.transformers_ expects.
    # `existing_numeric_features_in_df` was used to fit. We need this list for transform.
    # This is a common challenge with sklearn ColumnTransformer if not all features are always present.
    
    # Let's try to get the features the preprocessor *expects* for numeric part
    try:
        num_features_expected = preprocessor.transformers_[0][2] # Columns for 'num' transformer
        cat_features_expected = preprocessor.transformers_[1][2] # Columns for 'cat' transformer
        expected_cols_for_transform = num_features_expected + cat_features_expected
    except Exception: # Fallback if introspection fails
        print("Warning: Could not reliably determine preprocessor's expected features. Falling back to ALL_NUMERIC + CATEGORICAL")
        expected_cols_for_transform = [col for col in ALL_NUMERIC_FEATURES if col in df_input.columns] + CATEGORICAL_FEATURES


    try:
        # Ensure df_input has all columns in expected_cols_for_transform, in that order
        # Fill missing ones with NaN or appropriate placeholder
        df_for_transform = pd.DataFrame(columns=expected_cols_for_transform)
        for col in expected_cols_for_transform:
            if col in df_input.columns:
                df_for_transform[col] = df_input[col]
            elif col in ALL_NUMERIC_FEATURES: # If it's a numeric feature expected but missing
                 df_for_transform[col] = np.nan
            elif col in CATEGORICAL_FEATURES: # If it's a categorical feature expected but missing
                 df_for_transform[col] = None # Imputer/OneHot should handle

        # If df_for_transform is empty due to no matching columns (edge case)
        if df_for_transform.empty and not df_input.empty :
             df_for_transform = df_input[expected_cols_for_transform].copy()


        data_processed = preprocessor.transform(df_for_transform)
    except NotFittedError:
        print("Preprocessor belum dilatih.")
        return None, None
    except ValueError as ve:
        print(f"Error saat memproses data input: {ve}")
        return None, None
    except KeyError as ke:
        print(f"Error KeyError saat memproses data input: {ke}. Kolom mungkin hilang dari input atau preprocessor.")
        return None, None


    try:
        prediction = model.predict(data_processed)
        proba = model.predict_proba(data_processed)
        model_classes = model.classes_
        proba_dict = dict(zip(model_classes, proba[0]))
        return prediction[0], proba_dict
    except NotFittedError:
        print("Model belum dilatih (NotFittedError).")
        return None, None
    except Exception as e:
        print(f"Error saat prediksi: {e}")
        return None, None

if __name__ == '__main__':
    print("Menjalankan contoh alur kerja incremental_model_trainer...")
    if os.path.exists(MODEL_PATH): os.remove(MODEL_PATH)
    if os.path.exists(PREPROCESSOR_PATH): os.remove(PREPROCESSOR_PATH)
    if os.path.exists(CLASSES_PATH): os.remove(CLASSES_PATH)
    print("Model, preprocessor, dan file kelas lama (jika ada) telah dihapus untuk demo.")

    all_data = load_all_datasets()

    if all_data.empty:
        print("Tidak ada data untuk dijalankan. Keluar.")
    else:
        print(f"Total data dimuat: {len(all_data)} baris.")
        
        # For reliable preprocessor fitting, ensure all Sektor categories are seen
        # and a good representation of numeric features.
        # Using all_data to fit preprocessor initially is safer.
        # Then, split for train/update.
        
        # Create preprocessor based on all available data to learn all columns and categories
        # We will save it, then potentially overwrite it in train_initial_model if force_retrain_preprocessor is True
        # but the preprocessor there will be fit only on df_initial.
        # It's better to ensure preprocessor is fit once on a dataset that has all possible columns.
        
        # Let's refine: get_preprocessor should be robust.
        # It will try to load. If not found, it creates based on df_for_fitting_preprocessor.
        # So, the first call to get_preprocessor (via train_initial_model) defines it.
        
        if len(all_data) >= 10: # Ensure enough data for a meaningful split
             df_initial = all_data.sample(n=min(len(all_data), 15), random_state=42) # Use a small, diverse initial set
             df_new_incremental = all_data.drop(df_initial.index)
        elif len(all_data) > 0:
            df_initial = all_data 
            df_new_incremental = pd.DataFrame() 
        else:
            df_initial = pd.DataFrame()
            df_new_incremental = pd.DataFrame()

        print(f"Data awal untuk pelatihan: {len(df_initial)} baris.")
        print(f"Data baru untuk pembaruan inkremental: {len(df_new_incremental)} baris.")

        if not df_initial.empty:
            model, preprocessor = train_initial_model(df_initial, force_retrain_preprocessor=True)

            if model and preprocessor and not df_new_incremental.empty:
                print("\n--- Memperbarui model dengan data inkremental ---")
                # Split df_new_incremental into smaller chunks to simulate multiple updates
                chunk_size = 10
                num_chunks = int(np.ceil(len(df_new_incremental) / chunk_size))
                for i in range(num_chunks):
                    chunk = df_new_incremental.iloc[i*chunk_size : (i+1)*chunk_size]
                    print(f"\nMengupdate dengan chunk {i+1}/{num_chunks} ({len(chunk)} baris)")
                    model = update_model_incrementally(chunk, model=model, preprocessor=preprocessor)
            elif not df_new_incremental.empty:
                 print("Pelatihan model awal gagal, pembaruan inkremental dilewati.")


            if model and preprocessor:
                print("\n--- Melakukan prediksi pada sampel data ---")
                sample_source_df = df_new_incremental if not df_new_incremental.empty else df_initial
                if not sample_source_df.empty:
                    sample_input_series = sample_source_df.iloc[0]
                    sample_input_dict = sample_input_series.drop(TARGET_COLUMN).to_dict()
                    
                    print(f"Input untuk prediksi (dari {sample_input_series['NamaPerusahaan']} - {sample_input_series['Sektor']} - {sample_input_series['PeriodeTahun']}):")
                    # print(sample_input_dict) # Can be very long
                    
                    predicted_category, probabilities = predict_risk(sample_input_dict, model, preprocessor)
                    print(f"Prediksi Kategori Risiko: {predicted_category}")
                    print(f"Probabilitas: {probabilities}")
                    print(f"Kategori Sebenarnya: {sample_input_series[TARGET_COLUMN]}")
                else:
                    print("Tidak ada data sampel untuk prediksi.")
            else:
                print("Model atau preprocessor tidak tersedia untuk prediksi.")
        else:
            print("Tidak ada data awal yang cukup untuk melatih model.")
