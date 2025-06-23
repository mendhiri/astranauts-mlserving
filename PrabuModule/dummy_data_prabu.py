import pandas as pd
import numpy as np

# Define the year for the features
year = 2018
next_year = year + 1

# Define the number of dummy companies
num_companies = 100

# Define possible sectors and countries (align with one-hot encoding in the notebook)
sectors = [
    'Automobiles and Components', 'Banks', 'Capital Goods', 'Commercial and Professional Services',
    'Consumer Durables and Apparel', 'Consumer Services', 'Diversified Financials',
    'Energy', 'Food Beverage and Tobacco', 'Food and Staples Retailing',
    'Health Care Equipment and Services', 'Household and Personal Products',
    'Insurance', 'Materials', 'Media and Entertainment', 'Pharmaceuticals Biotechnology and Life Sciences',
    'Real Estate', 'Retailing', 'Semiconductors and Semiconductor Equipment',
    'Software and Services', 'Technology Hardware and Equipment',
    'Telecommunication Services', 'Transportation', 'Utilities'
]

countries = [
    'France', 'Germany', 'Italy', 'Netherlands', 'Spain', 'United Kingdom', 'Other_European_Countries',
    'North_America', 'Asia_Pacific', 'Rest_of_the_World'
]

# Generate dummy data
data = {
    f'MScore.{year}.int': np.random.randint(0, 2, size=num_companies),
    f'Turnover.{year}': np.random.uniform(100000, 10000000, size=num_companies),
    f'EBIT.{year}': np.random.uniform(-50000, 500000, size=num_companies),
    f'PLTax.{year}': np.random.uniform(-20000, 200000, size=num_companies),
    f'Leverage.{year}': np.random.uniform(0, 1, size=num_companies),
    f'ROE.{year}': np.random.uniform(-0.5, 0.5, size=num_companies),
    f'TAsset.{year}': np.random.uniform(500000, 50000000, size=num_companies),
    # Target variable for the next year
    f'MScore.{next_year}.int': np.random.randint(0, 2, size=num_companies)
}

# Add one-hot encoded sectors
for sector in sectors:
    data[sector] = np.random.randint(0, 2, size=num_companies)
# Ensure at least one sector is 1 for each company, or make it more realistic if needed
# For simplicity, this basic version might have rows with all 0s or multiple 1s for sectors.
# A more robust way would be to assign one sector per company:
assigned_sectors = np.random.choice(sectors, size=num_companies)
for sector in sectors:
    data[sector] = (assigned_sectors == sector).astype(int)


# Add one-hot encoded countries
assigned_countries = np.random.choice(countries, size=num_companies)
for country in countries:
    data[country] = (assigned_countries == country).astype(int)

# Create DataFrame
df_dummy = pd.DataFrame(data)

# Display a sample of the dummy data
print("Sample of Dummy Data:")
print(df_dummy.head())

# Save to CSV (optional)
# df_dummy.to_csv('dummy_prabu_input.csv', index=False)
# print("\nDummy data saved to dummy_prabu_input.csv")

def get_dummy_data(year_value=2018, n_samples=100):
    """
    Generates a Pandas DataFrame with dummy data for PRABU model testing.

    Args:
        year_value (int): The base year for the features.
        n_samples (int): The number of dummy company records to generate.

    Returns:
        pandas.DataFrame: A DataFrame containing the dummy data.
    """
    current_year = year_value
    target_year = current_year + 1

    # Define possible sectors and countries
    # These should ideally match the columns used during training of PrabuModel.joblib
    # Listing them explicitly based on common one-hot encoding practices
    _sectors = [
        'Automobiles and Components', 'Banks', 'Capital Goods', 'Commercial and Professional Services',
        'Consumer Durables and Apparel', 'Consumer Services', 'Diversified Financials',
        'Energy', 'Food Beverage and Tobacco', 'Food and Staples Retailing',
        'Health Care Equipment and Services', 'Household and Personal Products',
        'Insurance', 'Materials', 'Media and Entertainment', 'Pharmaceuticals Biotechnology and Life Sciences',
        'Real Estate', 'Retailing', 'Semiconductors and Semiconductor Equipment',
        'Software and Services', 'Technology Hardware and Equipment',
        'Telecommunication Services', 'Transportation', 'Utilities'
    ]

    _countries = [
        'France', 'Germany', 'Italy', 'Netherlands', 'Spain', 'United Kingdom', 
        'Other_European_Countries', 'North_America', 'Asia_Pacific', 'Rest_of_the_World'
    ] # Assuming these were the categories

    # Generate base financial data
    dummy_data_dict = {
        f'MScore.{current_year}.int': np.random.randint(0, 2, size=n_samples),
        f'Turnover.{current_year}': np.random.uniform(100000, 20000000, size=n_samples),
        f'EBIT.{current_year}': np.random.uniform(-100000, 1000000, size=n_samples),
        f'PLTax.{current_year}': np.random.uniform(-50000, 500000, size=n_samples),
        f'Leverage.{current_year}': np.random.uniform(0.05, 0.8, size=n_samples),
        f'ROE.{current_year}': np.random.uniform(-0.2, 0.3, size=n_samples),
        f'TAsset.{current_year}': np.random.uniform(500000, 100000000, size=n_samples),
        # Target variable for the next year (can be used for evaluation if needed)
        f'MScore.{target_year}.int': np.random.randint(0, 2, size=n_samples)
    }

    # Generate one-hot encoded sectors
    assigned_sec = np.random.choice(_sectors, size=n_samples)
    for sector_name in _sectors:
        dummy_data_dict[sector_name] = (assigned_sec == sector_name).astype(int)

    # Generate one-hot encoded countries
    assigned_ctry = np.random.choice(_countries, size=n_samples)
    for country_name in _countries:
        dummy_data_dict[country_name] = (assigned_ctry == country_name).astype(int)

    df = pd.DataFrame(dummy_data_dict)
    
    # Define feature columns expected by the model (excluding the target for next year)
    # This order should ideally match the training data column order if the model is sensitive to it
    # For many scikit-learn models, column order doesn't matter as long as names are consistent.
    feature_cols = [f'MScore.{current_year}.int', f'Turnover.{current_year}', 
                    f'EBIT.{current_year}', f'PLTax.{current_year}', 
                    f'Leverage.{current_year}', f'ROE.{current_year}', f'TAsset.{current_year}'] + \
                   _sectors + _countries
    
    # Ensure all expected columns are present, fill with 0 if any somehow missed (should not happen with above logic)
    for col in feature_cols:
        if col not in df:
            df[col] = 0
            
    # Return the DataFrame with features and the target column (for potential evaluation)
    return df[feature_cols + [f'MScore.{target_year}.int']]

if __name__ == '__main__':
    # Example of how to use the function
    year_to_predict_for = 2019 # This means features are from 2018
    base_year = year_to_predict_for - 1
    
    dummy_df = get_dummy_data(year_value=base_year, n_samples=50)
    print(f"Generated dummy data for base year {base_year} to predict for {year_to_predict_for}:")
    print(dummy_df.head())
    print(f"\nShape of the dataframe: {dummy_df.shape}")
    print(f"\nColumns: {dummy_df.columns.tolist()}")

    # Features that would be fed into the model
    X_dummy_test = dummy_df.drop(columns=[f'MScore.{year_to_predict_for}.int'])
    # Target (if you want to evaluate dummy predictions)
    y_dummy_test = dummy_df[f'MScore.{year_to_predict_for}.int']
    
    print("\nShape of X_dummy_test (features for model):", X_dummy_test.shape)
    print("Shape of y_dummy_test (target labels):", y_dummy_test.shape)
