import pandas as pd
import shutil
from datetime import datetime
from search_query_cleaning import clean_name

def clean_all_names_in_csv(csv_path='roblox_top10_history.csv'):
    """
    One-off script to clean all names in the CSV file and save the cleaned version.
    Creates a backup of the original file before modifying.
    """
    # Create backup of original file
    backup_path = f"{csv_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(csv_path, backup_path)
    print(f"Created backup at: {backup_path}")
    
    # Read and clean the data
    df = pd.read_csv(csv_path)
    original_names = df['name'].tolist()
    df['name'] = df['name'].apply(clean_name)
    
    # Save cleaned data
    df.to_csv(csv_path, index=False)
    
    # Print some statistics
    changed_count = sum(1 for orig, cleaned in zip(original_names, df['name']) if orig != cleaned)
    print(f"\nCleaning complete:")
    print(f"Total rows processed: {len(df)}")
    print(f"Names that were changed: {changed_count}")
    print(f"\nSample of changes:")
    for orig, cleaned in zip(original_names[:5], df['name'][:5]):
        if orig != cleaned:
            print(f"Original: {orig}")
            print(f"Cleaned:  {cleaned}")
            print()

if __name__ == "__main__":
    clean_all_names_in_csv() 