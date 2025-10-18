print("works!")
#!/usr/bin/env python3
"""
Merges the final abundance ratios with the original metadata file
to create a complete dataset including footprint vertex coordinates.
"""
from pathlib import Path
import pandas as pd

# --- File Paths ---
PRIME_CSV = Path("/home/saurabh/moon_project/metadata/filtered_subsets/match_CLASS_XSM_20250801_prime.csv")
RESULTS_CSV = Path("/home/saurabh/moon_project/results/batch_run/final_abundance_ratios.csv")
OUTPUT_CSV = Path("/home/saurabh/moon_project/results/batch_run/final_abundance_ratios_complete.csv")

# --- Main ---
if __name__ == "__main__":
    print("Loading data files...")
    df_results = pd.read_csv(RESULTS_CSV)
    df_prime = pd.read_csv(PRIME_CSV)
    
    # Create a matching 'obs_id' column in the prime dataframe
    df_prime.columns = [c.strip().lower() for c in df_prime.columns]
    df_prime['obs_id'] = df_prime['class_filepath'].apply(lambda x: Path(x).stem)
    
    # Select only the columns we need to merge
    columns_to_merge = [
        'obs_id', 'bore_lat', 'bore_lon',
        'v0_lat', 'v0_lon', 'v1_lat', 'v1_lon',
        'v2_lat', 'v2_lon', 'v3_lat', 'v3_lon'
    ]
    df_prime_subset = df_prime[columns_to_merge]
    
    # Merge the two dataframes based on the observation ID
    df_complete = pd.merge(df_results, df_prime_subset, on='obs_id')
    
    # Save the new complete file
    df_complete.to_csv(OUTPUT_CSV, index=False)
    
    print(f"✅ Merged data successfully and saved to: {OUTPUT_CSV}")
    print(f"New file has {len(df_complete)} rows and includes vertex coordinates.")