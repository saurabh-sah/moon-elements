#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plot CLASS-XSM matched or filtered data as 2D density map and contours.

Author: Saurabh + ChatGPT AstroCollab
Date: 2025-10-10
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path

# =========================================================
# ✅ User configuration
# =========================================================
# input_csv = Path("/home/saurabh/moon_project/metadata/filtered/match_CLASS_XSM_20250801_filtered.csv")
input_csv = Path("/home/saurabh/moon_project/metadata/filtered_subsets/match_CLASS_XSM_20250801_prime.csv")
output_dir = Path("/home/saurabh/moon_project/plots/Aug_25/")
output_dir.mkdir(parents=True, exist_ok=True)

# Choose which columns to use for the plot
x_col = "sat_lon"
y_col = "sat_lat"
color_col = "xsm_mean_totalcounts"  # can also try xsm_mean_meancounts

# =========================================================
# ✅ Load data
# =========================================================
print(f"Loading data → {input_csv}")
df = pd.read_csv(input_csv)

# Drop NaN values in key columns
df = df[[x_col, y_col, color_col]].dropna()
if df.empty:
    raise ValueError("No valid data to plot after dropping NaNs.")

print(f"Loaded {len(df)} points for density plot")

# =========================================================
# ✅ Create 2D histogram (density map)
# =========================================================
xbins, ybins = 200, 200  # adjust resolution for smoothness
H, xedges, yedges = np.histogram2d(
    df[x_col], df[y_col],
    bins=[xbins, ybins],
    weights=df[color_col]
)

counts, _, _ = np.histogram2d(
    df[x_col], df[y_col],
    bins=[xbins, ybins]
)

# Normalize weighted map by counts
Ht = np.divide(H, counts, out=np.zeros_like(H), where=counts > 0)

# Clean data
Ht = np.nan_to_num(Ht, nan=0.0)
Ht = np.clip(Ht, 0, None)

# =========================================================
# ✅ Plot density heatmap + contour overlay
# =========================================================
fig, ax = plt.subplots(figsize=(10, 8))

# Plot density image
img = ax.imshow(
    Ht.T,
    origin="lower",
    extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
    aspect="auto",
    cmap="inferno"
)

# Safe contour levels
vmin, vmax = np.nanmin(Ht), np.nanmax(Ht)
if vmax > vmin:
    levels = np.linspace(vmin, vmax, 8)
    levels = np.sort(np.unique(levels))
    CS = ax.contour(
        xedges[:-1] + 0.5 * (xedges[1] - xedges[0]),
        yedges[:-1] + 0.5 * (yedges[1] - yedges[0]),
        Ht.T,
        levels=levels,
        colors='white',
        linewidths=0.8
    )
    ax.clabel(CS, inline=True, fontsize=8, fmt="%.1f")
else:
    print("⚠️  Flat data, skipping contour plot.")

# =========================================================
# ✅ Axis formatting
# =========================================================
ax.set_xlabel("Lunar Longitude (°)", fontsize=12)
ax.set_ylabel("Lunar Latitude (°)", fontsize=12)
ax.set_title("CLASS-XSM Matched Observation Density", fontsize=14)
ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
ax.yaxis.set_major_locator(ticker.MaxNLocator(10))
ax.grid(color='gray', linestyle='--', linewidth=0.3, alpha=0.4)

# Add colorbar
cbar = plt.colorbar(img, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label(f"Mean {color_col}", fontsize=12)

# Save figure
out_png = output_dir / f"density_contour_{input_csv.stem}.png"
plt.tight_layout()
plt.savefig(out_png, dpi=300)
plt.close()

print(f"✅ Saved density plot → {out_png}")
