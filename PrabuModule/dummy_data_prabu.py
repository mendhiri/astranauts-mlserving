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
    The features generated are MScore.YYYY.int from 2015 up to year_value.
    The target is MScore.{year_value+1}.int.

    Args:
        year_value (int): The base year for the features, e.g., 2018.
                          Features will be MScore.2015.int to MScore.2018.int.
        n_samples (int): The number of dummy company records to generate.

    Returns:
        pandas.DataFrame: A DataFrame containing the dummy data.
    """
    current_year = year_value
    target_year = current_year + 1

    dummy_data_dict = {}
    feature_cols = []

    # Generate MScore.YYYY.int features from 2015 up to current_year
    for year in range(2015, current_year + 1):
        col_name = f'MScore.{year}.int'
        dummy_data_dict[col_name] = np.random.randint(0, 2, size=n_samples)
        feature_cols.append(col_name)
    
    # Target variable for the next year
    target_col_name = f'MScore.{target_year}.int'
    dummy_data_dict[target_col_name] = np.random.randint(0, 2, size=n_samples)

    df = pd.DataFrame(dummy_data_dict)
            
    # Return the DataFrame with features and the target column
    return df[feature_cols + [target_col_name]]

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
