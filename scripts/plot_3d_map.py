#!/usr/bin/env python3
"""
plot_3d_map.py

This script takes the final CSV file of abundance ratios and generates an
interactive 3D scatter plot of the data on a sphere, saved as an HTML file.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURE YOUR FILE PATHS HERE ---
# ==============================================================================
# The final CSV file produced by the batch analysis script
RESULTS_CSV = Path("/home/saurabh/moon_project/results/batch_run/final_abundance_ratios.csv")

# Where to save the final interactive map
OUTPUT_DIR = Path("/home/saurabh/moon_project/plots/")
# ==============================================================================


def create_3d_map(data_df, column_to_map, label, colorscale):
    """Creates and saves an interactive 3D map for a given data column."""
    
    # --- 1. Filter out bad data and convert to 3D coordinates ---
    # Drop any rows with missing location or ratio data
    df_plot = data_df[['latitude', 'longitude', column_to_map]].dropna()
    
    # Convert latitude and longitude from degrees to radians
    lat_rad = np.deg2rad(df_plot['latitude'])
    lon_rad = np.deg2rad(df_plot['longitude'])
    
    # Convert spherical coordinates to Cartesian (x, y, z) for plotting on a sphere
    x = np.cos(lat_rad) * np.cos(lon_rad)
    y = np.cos(lat_rad) * np.sin(lon_rad)
    z = np.sin(lat_rad)
    
 # 1. Prepare the custom data for the hover text
    custom_data = np.stack((df_plot['latitude'], df_plot['longitude']), axis=-1)

    # 2. Define the data trace with a hover template
    trace = go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        # Define the hover text format
        customdata=custom_data,
        hovertemplate=(
            f"<b>Latitude</b>: %{{customdata[0]:.2f}}<br>"
            f"<b>Longitude</b>: %{{customdata[1]:.2f}}<br>"
            f"<b>{label}</b>: %{{marker.color:.3f}}"
            "<extra></extra>" # Removes the trace name from the tooltip
        ),
        marker=dict(
            size=3.5,
            color=df_plot[column_to_map],
            colorscale=colorscale,
            colorbar=dict(title=label),
            showscale=True
        )
    )
    
    # --- 3. Define the Layout ---
    layout = go.Layout(
        title=f"Interactive 3D Lunar Abundance Map: {label}",
        scene=dict(
            xaxis=dict(title='X', showticklabels=False, backgroundcolor="rgb(10, 10, 10)"),
            yaxis=dict(title='Y', showticklabels=False, backgroundcolor="rgb(10, 10, 10)"),
            zaxis=dict(title='Z', showticklabels=False, backgroundcolor="rgb(10, 10, 10)"),
            aspectmode='data' # This ensures the plot is a sphere, not an ellipsoid
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    
    # --- 4. Create Figure and Save to HTML ---
    fig = go.Figure(data=[trace], layout=layout)
    
    output_path = OUTPUT_DIR / f"lunar_3d_map_{column_to_map}.html"
    fig.write_html(str(output_path))
    print(f"✅ Interactive 3D map saved to {output_path}")

# --- Main Execution ---
if __name__ == "__main__":
    if not RESULTS_CSV.exists():
        print(f"Error: Final results file not found at {RESULTS_CSV}")
    else:
        OUTPUT_DIR.mkdir(exist_ok=True)
        df = pd.read_csv(RESULTS_CSV)
        
        # Create a map for the Mg/Si ratio
        create_3d_map(df, 'mg_si_ratio', 'Mg/Si Ratio', 'Viridis')
        
        # Create a map for the Al/Si ratio
        create_3d_map(df, 'al_si_ratio', 'Al/Si Ratio', 'Plasma')
        
        print("\nAll 3D maps created successfully.")