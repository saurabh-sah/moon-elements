#!/usr/bin/env python3
"""
plot_lunar_tracks.py
Visualize accepted vs rejected CLASS footprints on a simple lunar map.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def plot_tracks(filtered_csv, rejected_csv, out_png=None):
    df_f = pd.read_csv(filtered_csv)
    df_r = pd.read_csv(rejected_csv)

    # Use boresight lat/lon if available
    lat_f, lon_f = df_f["bore_lat"], df_f["bore_lon"]
    lat_r, lon_r = df_r["bore_lat"], df_r["bore_lon"]

    plt.figure(figsize=(10, 5))
    plt.title("CLASS Footprints — Accepted vs Rejected", fontsize=14)
    plt.xlabel("Longitude (°E)")
    plt.ylabel("Latitude (°N)")
    plt.grid(True, ls=":", lw=0.5)

    # Wrap longitudes into −180 … 180 range
    lon_f = ((lon_f + 180) % 360) - 180
    lon_r = ((lon_r + 180) % 360) - 180

    plt.scatter(lon_r, lat_r, s=6, c="lightgray", label="Rejected")
    plt.scatter(lon_f, lat_f, s=8, c="darkorange", label="Accepted", alpha=0.8)

    plt.legend()
    plt.xlim(-180, 180)
    plt.ylim(-90, 90)

    if out_png:
        plt.savefig(out_png, dpi=200, bbox_inches="tight")
        print(f"✅ Saved map → {out_png}")
    else:
        plt.show()

if __name__ == "__main__":
    filtered = Path("/home/saurabh/moon_project/metadata/filtered/match_CLASS_XSM_20250801_filtered.csv")
    rejected = Path("/home/saurabh/moon_project/metadata/filtered/match_CLASS_XSM_20250801_rejected.csv")
    out_png = Path("/home/saurabh/moon_project/plots/CLASS_tracks_20250801.png")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plot_tracks(filtered, rejected, out_png)
