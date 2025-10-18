#!/usr/bin/env python3
"""
plot_healpix_map.py

This script uses the HEALPix algorithm to create a scientifically accurate,
equal-area map of the lunar abundance ratios.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import healpy as hp
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
RESULTS_CSV = Path("/home/saurabh/moon_project/results/batch_run/final_abundance_ratios.csv")
OUTPUT_DIR = Path("/home/saurabh/moon_project/plots/")
# HEALPix resolution parameter. Higher nside = more, smaller pixels. 64 is a good start.
NSIDE = 64

def create_healpix_map(data_df, column_to_map, label, cmap):
    """Creates and saves a HEALPix map for a given data column."""
    
    df_plot = data_df[['latitude', 'longitude', column_to_map]].dropna()
    
    # --- 1. HEALPix Gridding ---
    print(f"Gridding data for {label} using HEALPix (NSIDE={NSIDE})...")
    
    # Get the total number of pixels for our chosen resolution
    npix = hp.nside2npix(NSIDE)
    
    # Create empty arrays to hold the sum of values and the count of points in each pixel
    grid_sum = np.zeros(npix)
    grid_count = np.zeros(npix, dtype=int)
    
    # Convert latitude and longitude to the spherical coordinates (theta, phi) that healpy expects
    # healpy's theta is the 'colatitude' (0 at N pole, 180 at S pole)
    # healpy's phi is the longitude
    theta = np.deg2rad(90.0 - df_plot['latitude'])
    phi = np.deg2rad(df_plot['longitude'])
    
    # Get the HEALPix pixel index for each data point
    pixel_indices = hp.ang2pix(NSIDE, theta, phi)
    
    # --- 2. Averaging Overlaps ---
    # This loop automatically handles averaging the overlapping data points
    for i, pix_idx in enumerate(pixel_indices):
        grid_sum[pix_idx] += df_plot[column_to_map].iloc[i]
        grid_count[pix_idx] += 1
        
    # Calculate the average value for each pixel
    with np.errstate(divide='ignore', invalid='ignore'):
        healpix_map = grid_sum / grid_count
        
    # For pixels with no data, healpy expects a special value (UNSEEN)
    healpix_map[grid_count == 0] = hp.UNSEEN

    # --- 3. Plotting ---
    print(f"Plotting Mollweide projection map for {label}...")
    
    # Create the plot using healpy's mollview
    # This creates a full sky map in a Mollweide projection, which is area-preserving
    hp.mollview(
        healpix_map,
        title=f"Lunar Elemental Abundance Map: {label} (HEALPix)",
        unit=label,
        cmap=cmap,
        norm='hist' # Adjusts the color scale to highlight features
    )
    hp.graticule() # Adds a coordinate grid
    
    # Save the figure
    output_path = OUTPUT_DIR / f"lunar_healpix_map_{column_to_map}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ HEALPix map saved to {output_path}")
    plt.close()

# --- Main Execution ---
if __name__ == "__main__":
    if not RESULTS_CSV.exists():
        print(f"Error: Final results file not found at {RESULTS_CSV}")
    else:
        OUTPUT_DIR.mkdir(exist_ok=True)
        df = pd.read_csv(RESULTS_CSV)
        
        create_healpix_map(df, 'mg_si_ratio', 'Mg/Si Ratio', 'viridis')
        create_healpix_map(df, 'al_si_ratio', 'Al/Si Ratio', 'plasma')
        
        print("\nAll HEALPix maps created successfully.")