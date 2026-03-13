import pandas as pd
import numpy as np
import os

DATA_DIR = "data"  # Changed from backend/data to data

def analyze_csv(filepath):
    print(f"\n{'='*50}\nAnalyzing: {os.path.basename(filepath)}\n{'='*50}")
    try:
        df = pd.read_csv(filepath, low_memory=False)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return
        
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print("\nMissing Values:")
    missing = df.isnull().sum()
    print(missing[missing > 0].to_string() if missing.sum() > 0 else "None")
    
    print("\nData Types:")
    print(df.dtypes.to_string())
    
    print("\nSummary Statistics:")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        print(df[numeric_cols].describe().T[['count', 'mean', 'min', 'max']].to_string())
    
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        print("\nCategorical Column Unique Counts:")
        for col in categorical_cols:
            print(f"  {col}: {df[col].nunique()} unique values")
            if df[col].nunique() < 10:
                print(f"    Values: {df[col].unique().tolist()}")
                
    print("\nFirst 3 rows:")
    print(df.head(3).to_string())

for file in os.listdir(DATA_DIR):
    if file.endswith(".csv") or file.endswith(".xls"):
        analyze_csv(os.path.join(DATA_DIR, file))
