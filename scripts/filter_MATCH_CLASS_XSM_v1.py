#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 1.5 – Spatial & Instrumental Filtering for CLASS–XSM Matched Data
Author : Saurabh  |  Project : ISRO Lunar XRF Mapping

Purpose:
    Filter out CLASS–XSM matched spectra based on solar illumination,
    spacecraft geometry, and detector health parameters.
"""

import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# 🧭  USER INPUTS
# ---------------------------------------------------------------------------
input_csv  = Path("/home/saurabh/moon_project/metadata/matched/match_CLASS_XSM_20250801.csv")
output_dir = Path("/home/saurabh/moon_project/metadata/filtered/")
output_dir.mkdir(parents=True, exist_ok=True)

# Output files
filtered_csv  = output_dir / f"{input_csv.stem}_filtered.csv"
rejected_csv  = output_dir / f"{input_csv.stem}_rejected.csv"

# ---------------------------------------------------------------------------
# ⚙️  LOAD DATA
# ---------------------------------------------------------------------------
print(f"Reading {input_csv} ...")
df = pd.read_csv(input_csv)

print(f"Initial rows : {len(df):,}")

# Make sure column names are consistent (handle case-insensitive or trimmed)
df.columns = [c.strip().lower() for c in df.columns]

# ---------------------------------------------------------------------------
# 📊  FILTER CONDITIONS
# ---------------------------------------------------------------------------

# Default thresholds (tune as needed)
solarang_max = 120.0       # degrees
phaseang_max = 120.0       # degrees
alt_min, alt_max = 80.0, 110.0  # km
gain_min, gain_max = 13.0, 14.0 # eV/channel
temp_min, temp_max = -40.0, -33.0  # °C

# Add derived flags to inspect later
df["flag_solar"] = df["solarang_deg"] <= solarang_max
df["flag_phase"] = df["phaseang_deg"] <= phaseang_max
if "sat_alt" in df.columns:
    df["flag_alt"] = df["sat_alt"].between(alt_min, alt_max)
else:
    df["flag_alt"] = True
df["flag_gain"] = df["gain_ev_ch"].between(gain_min, gain_max)
df["flag_temp"] = df["temp_c"].between(temp_min, temp_max)

# Combine all boolean filters
good_mask = (
    df["flag_solar"]
    & df["flag_phase"]
    & df["flag_alt"]
    & df["flag_gain"]
    & df["flag_temp"]
)

# ---------------------------------------------------------------------------
# ✂️  SPLIT FILTERED AND REJECTED
# ---------------------------------------------------------------------------
df_filtered = df[good_mask].copy()
df_rejected = df[~good_mask].copy()

print(f"Filtered rows  : {len(df_filtered):,}")
print(f"Rejected rows  : {len(df_rejected):,}")

# ---------------------------------------------------------------------------
# 💾  SAVE RESULTS
# ---------------------------------------------------------------------------
df_filtered.to_csv(filtered_csv, index=False, encoding="utf-8", lineterminator="\n")
df_rejected.to_csv(rejected_csv, index=False, encoding="utf-8", lineterminator="\n")

print(f"Saved filtered data   ➜ {filtered_csv}")
print(f"Saved rejected data   ➜ {rejected_csv}")

# ---------------------------------------------------------------------------
# 🧾  SUMMARY STATISTICS
# ---------------------------------------------------------------------------
summary = {
    "solar_angle_mean": df_filtered["solarang_deg"].mean(),
    "phase_angle_mean": df_filtered["phaseang_deg"].mean(),
    "altitude_mean_km": df_filtered.get("sat_alt", pd.Series(dtype=float)).mean(),
    "temp_mean_C": df_filtered["temp_c"].mean(),
    "gain_mean_eV_ch": df_filtered["gain_ev_ch"].mean(),
}

print("\nQuality summary of filtered dataset:")
for k, v in summary.items():
    print(f"  {k:<20} : {v:.3f}")

print("\n✅ Step 1.5 completed successfully.\n")
