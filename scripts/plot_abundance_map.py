#!/usr/bin/env python3
"""
plot_abundance_map.py

This script takes the final CSV file of abundance ratios and generates a
2D elemental map overlaid on a lunar albedo base map.
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# --- CONFIGURE YOUR FILE PATHS HERE ---
# ==============================================================================
# The final CSV file produced by the batch analysis script
RESULTS_CSV = Path("/home/saurabh/moon_project/results/batch_run/final_abundance_ratios.csv")

# The path to your lunar base map image
# UPDATE THIS PATH to where you saved the 'image_a626a3.png' file
BASE_MAP_IMAGE = Path("/home/saurabh/moon_project/maps/WAC_GLOBAL_E000N0000_008P.IMG")

# Where to save the final map
OUTPUT_DIR = Path("/home/saurabh/moon_project/plots/")
# ==============================================================================

def create_map(data_df, column_to_map, label, cmap):
    """Creates and saves a gridded map for a given data column."""
    
    # --- 1. Define the Grid ---
    # We'll use a 1-degree resolution grid
    lon_bins = np.arange(-180, 181, 1)
    lat_bins = np.arange(-90, 91, 1)
    
    # Initialize empty grids to store the sum of ratios and the count of points
    grid_sum = np.zeros((len(lat_bins)-1, len(lon_bins)-1))
    grid_count = np.zeros_like(grid_sum)

    # --- 2. Bin the Data ---
    # For each data point, find which grid cell it belongs to and add its value
    for index, row in data_df.iterrows():
        # np.digitize finds the index of the bin the value belongs to
        lat_idx = np.digitize(row['latitude'], lat_bins) - 1
        lon_idx = np.digitize(row['longitude'], lon_bins) - 1
        
        # Check if the indices are valid
        if 0 <= lat_idx < grid_sum.shape[0] and 0 <= lon_idx < grid_sum.shape[1]:
            value = row[column_to_map]
            if np.isfinite(value):
                grid_sum[lat_idx, lon_idx] += value
                grid_count[lat_idx, lon_idx] += 1
                
    # --- 3. Calculate the Average ---
    # Avoid division by zero for empty cells
    with np.errstate(divide='ignore', invalid='ignore'):
        grid_average = grid_sum / grid_count
    
    # Set empty cells to NaN so they won't be plotted
    grid_average[grid_count == 0] = np.nan

    # --- 4. Plotting ---
    print(f"Plotting map for {label}...")
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    
    # Load and display the base map image
    lunar_map = mpimg.imread(BASE_MAP_IMAGE)
    ax.imshow(lunar_map, extent=[-180, 180, -90, 90], cmap='gray')
    
    # Overlay our gridded data on top with transparency
    # Use vmin/vmax to set a consistent color scale based on the data's percentiles
    vmin, vmax = np.nanpercentile(grid_average, [5, 95])
    im = ax.imshow(
        grid_average, 
        extent=[-180, 180, -90, 90], 
        origin='lower', 
        cmap=cmap,
        alpha=0.65, # Transparency
        vmin=vmin,
        vmax=vmax
    )
    
    # Add colorbar, labels, and title
    cbar = fig.colorbar(im, ax=ax, orientation='vertical', shrink=0.8)
    cbar.set_label(label)
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title(f"Lunar Elemental Abundance Map: {label}")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    
    # Save the figure
    output_path = OUTPUT_DIR / f"lunar_map_{column_to_map}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Map saved to {output_path}")
    plt.close(fig)

# --- Main Execution ---
if __name__ == "__main__":
    if not RESULTS_CSV.exists():
        print(f"Error: Final results file not found at {RESULTS_CSV}")
        sys.exit(1)
    if not BASE_MAP_IMAGE.exists():
        print(f"Error: Base map image not found at {BASE_MAP_IMAGE}")
        print("Please download the map and/or update the path at the top of the script.")
        sys.exit(1)
        
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(RESULTS_CSV)
    
    # Create a map for the Mg/Si ratio
    create_map(df, 'mg_si_ratio', 'Mg/Si Ratio', 'viridis')
    
    # Create a map for the Al/Si ratio
    create_map(df, 'al_si_ratio', 'Al/Si Ratio', 'plasma')
    
    print("\nAll maps created successfully.")