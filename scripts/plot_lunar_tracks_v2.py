import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
import seaborn as sns # <-- NEW: For density plotting

# Suppress the known Matplotlib 3D warning globally
warnings.filterwarnings("ignore", module="matplotlib.projections")

def plot_tracks_with_density(filtered_csv, rejected_csv, out_png=None):
    """
    Visualizes accepted vs rejected CLASS footprints and overlays a 
    density contour map for the accepted points (Exposure Map visualization).
    """
    try:
        df_f = pd.read_csv(filtered_csv)
        df_r = pd.read_csv(rejected_csv)
    except FileNotFoundError as e:
        print(f"❌ Error reading files: {e}")
        return

    # --- Data Preparation ---
    lat_f, lon_f = df_f["bore_lat"], df_f["bore_lon"]
    lat_r, lon_r = df_r["bore_lat"], df_r["bore_lon"]

    # Wrap longitudes into −180 … 180 range
    lon_f = ((lon_f + 180) % 360) - 180
    lon_r = ((lon_r + 180) % 360) - 180
    
    # Extract date for title
    date_tag = Path(filtered_csv).stem.split('_')[-2] # e.g., extracts 20250801

    # --- Plotting Setup ---
    plt.figure(figsize=(10, 6))
    ax = plt.gca() # Get current axes

    ax.set_title(f"CLASS Footprints & Density Map ({date_tag})", fontsize=14)
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.grid(True, ls=":", lw=0.5, alpha=0.5)
    ax.set_aspect('equal', adjustable='box')


    # 1. Plot Rejected Points (Background context)
    ax.scatter(lon_r, lat_r, s=6, c="lightgray", alpha=0.6, label=f"Rejected ({len(df_r)})", zorder=1)

    # 2. Plot Density Contours (NEW: Heatmap for accepted points)
    # This visualizes where the orbital coverage is highest (highest exposure)
    try:
        sns.kdeplot(
            x=lon_f, 
            y=lat_f, 
            ax=ax, 
            cmap="viridis", # Color map (you can change this to 'hot', 'Reds', etc.)
            fill=True, 
            alpha=0.4, 
            levels=10, 
            zorder=0, # Plot underneath scatter points
            label="Exposure Density"
        )
    except Exception as e:
         # Handle case where too few points might crash kdeplot
         print(f"Warning: Could not generate density plot: {e}. Skipping heatmap.")
    
    # 3. Plot Accepted Points (Foreground)
    ax.scatter(lon_f, lat_f, s=8, c="darkorange", alpha=0.9, 
               label=f"Accepted ({len(df_f)})", zorder=2)
    
    # Custom legend due to density plot interaction
    legend_elements = [
        plt.scatter([], [], s=8, c="darkorange", alpha=0.9, label=f"Accepted ({len(df_f)})"),
        plt.scatter([], [], s=6, c="lightgray", alpha=0.6, label=f"Rejected ({len(df_r)})")
    ]
    ax.legend(handles=legend_elements, loc='lower left')


    # --- Output ---
    if out_png:
        plt.savefig(out_png, dpi=300, bbox_inches="tight")
        print(f"\n✅ Saved visualization map with density → {out_png}")
        plt.close() 
    else:
        plt.show()

if __name__ == "__main__":
    # --- Define Inputs/Outputs ---
    BASE = Path("/home/saurabh/moon_project/metadata/filtered/")
    PLOT_DIR = Path("/home/saurabh/moon_project/plots/")
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    
    date_tag = "20250801"
    
    filtered = BASE / f"match_CLASS_XSM_{date_tag}_filtered.csv"
    rejected = BASE / f"match_CLASS_XSM_{date_tag}_rejected.csv"
    out_png = PLOT_DIR / f"CLASS_tracks_density_{date_tag}.png"
    
    print(f"Attempting to plot data for date: {date_tag}")
    
    plot_tracks_with_density(filtered, rejected, out_png)
