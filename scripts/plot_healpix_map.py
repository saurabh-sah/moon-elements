

#!/usr/bin/env python3
"""
plot_healpix_map.py (Version 3: Vectorized and Corrected)

This version uses a faster, vectorized approach to eliminate loops and fix
the TypeError during HEALPix gridding.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import healpy as hp
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
RESULTS_CSV = Path("/home/saurabh/moon_project/results/batch_run/final_abundance_ratios_complete.csv")
OUTPUT_DIR = Path("/home/saurabh/moon_project/plots/")
NSIDE = 128

def create_advanced_healpix_map(data_df, column_to_map, label, cmap):
    """Creates and saves a more accurate HEALPix map using a vectorized method."""
    
    # Define the columns for the 5 points of each footprint
    lat_cols = ['bore_lat', 'v0_lat', 'v1_lat', 'v2_lat', 'v3_lat']
    lon_cols = ['bore_lon', 'v0_lon', 'v1_lon', 'v2_lon', 'v3_lon']
    
    # Drop rows where any of the required data is missing
    all_cols_to_check = [column_to_map] + lat_cols + lon_cols
    df_plot = data_df.dropna(subset=all_cols_to_check)
    
    print(f"Gridding data for {label} using advanced vectorized method (NSIDE={NSIDE})...")
    
    # --- 1. Vectorized Data Preparation ---
    # Get all latitude and longitude values and flatten them into single, long 1D arrays
    all_lats = df_plot[lat_cols].values.flatten()
    all_lons = df_plot[lon_cols].values.flatten()
    
    # Get the ratio value for each observation
    ratio_values = df_plot[column_to_map].values
    
    # Repeat each observation's ratio value 5 times to match the 5 points
    all_ratios = np.repeat(ratio_values, 5)

    # --- 2. Vectorized HEALPix Gridding ---
    # Convert all points to HEALPix coordinates in a single operation
    theta = np.deg2rad(90.0 - all_lats)
    phi = np.deg2rad(all_lons)
    
    pixel_indices = hp.ang2pix(NSIDE, theta, phi)
    
    # --- 3. Vectorized Averaging ---
    npix = hp.nside2npix(NSIDE)
    grid_sum = np.zeros(npix)
    grid_count = np.zeros(npix, dtype=int)
    
    # Use np.add.at for a fast, vectorized way to sum values into the grid cells
    np.add.at(grid_sum, pixel_indices, all_ratios)
    np.add.at(grid_count, pixel_indices, 1)

    # Calculate the average and handle empty pixels
    with np.errstate(divide='ignore', invalid='ignore'):
        healpix_map = grid_sum / grid_count
    healpix_map[grid_count == 0] = hp.UNSEEN

    # --- 4. Plotting (Unchanged) ---
    print(f"Plotting Mollweide projection map for {label}...")
    hp.mollview(
        healpix_map, title=f"Lunar Map: {label} (Area-Weighted HEALPix)",
        unit=label, cmap=cmap, norm='hist'
    )
    hp.graticule()
    
    output_path = OUTPUT_DIR / f"lunar_healpix_map_advanced_{column_to_map}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Advanced HEALPix map saved to {output_path}")
    plt.close()

# --- Main Execution (Unchanged) ---
if __name__ == "__main__":
    if not RESULTS_CSV.exists():
        print(f"Error: Did you run merge_results.py first? File not found: {RESULTS_CSV}")
    else:
        OUTPUT_DIR.mkdir(exist_ok=True)
        df = pd.read_csv(RESULTS_CSV)
        create_advanced_healpix_map(df, 'mg_si_ratio', 'Mg/Si Ratio', 'viridis')
        create_advanced_healpix_map(df, 'al_si_ratio', 'Al/Si Ratio', 'plasma')
        print("\nAll advanced HEALPix maps created successfully.")