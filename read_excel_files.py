import pandas as pd
import os

# Get all Excel files in the current directory
excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]

# Dictionary to store all dataframes
dfs = {}

# Read each Excel file
for file in excel_files:
    print(f"\nReading {file}...")
    try:
        # Read the Excel file
        df = pd.read_excel(file)
        
        # Store in dictionary
        dfs[file] = df
        
        # Print basic information
        print(f"Shape: {df.shape}")
        print("Columns:", df.columns.tolist())
        print("\nFirst few rows:")
        print(df.head())
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"Error reading {file}: {str(e)}")

# Now you can access any dataframe using dfs['filename.xlsx']
# For example: dfs['FX_monthly.xlsx'] 