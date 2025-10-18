#!/usr/bin/env python3
"""
match_class_xsm_v1.py
Matches CLASS exposures with corresponding XSM solar data in the same UTC window.
"""

import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path

# === File paths ===
class_csv = Path("/home/saurabh/moon_project/metadata/metadata_CLASS/AUG_25/metadata_CLASS_01.csv")
xsm_csv   = Path("/home/saurabh/moon_project/metadata/metadata_XSM/Aug_25/metadata_XSM_ch2_xsm_20250801_v1_level1.csv")
output_csv = class_csv.parent.parent.parent / "matched/match_CLASS_XSM_20250801.csv"

# === Read Data ===
df_class = pd.read_csv(class_csv)
df_xsm   = pd.read_csv(xsm_csv)

# === Normalize Column Names ===
df_class.columns = [c.strip().lower() for c in df_class.columns]
df_xsm.columns   = [c.strip().lower() for c in df_xsm.columns]

# === Time Parsing Function ===
def parse_time(s):
    """Parse ISO UTC string safely into datetime (UTC tz-aware)."""
    if pd.isna(s): 
        return pd.NaT
    s = str(s).strip().replace("Z", "")
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except Exception:
        return pd.NaT

# === Parse relevant times ===
df_class["start_dt"] = df_class["start_time"].apply(parse_time)
df_class["end_dt"]   = df_class["end_time"].apply(parse_time)
df_xsm["utc_dt"]     = df_xsm["utc_from_met"].apply(parse_time)

# === Sort XSM data for faster slicing ===
df_xsm = df_xsm.sort_values("utc_dt")

print(f"CLASS rows: {len(df_class)}, XSM rows: {len(df_xsm)}")

# === Prepare matching ===
matched_rows = []

for _, row in df_class.iterrows():
    start_t = row["start_dt"]
    end_t   = row["end_dt"]
    if pd.isna(start_t) or pd.isna(end_t):
        continue

    # Select XSM rows within this time window
    mask = (df_xsm["utc_dt"] >= start_t) & (df_xsm["utc_dt"] <= end_t)
    subset = df_xsm.loc[mask]

    if len(subset) == 0:
        # no overlapping solar data
        mean_mc = std_mc = min_mc = max_mc = None
        mean_tc = std_tc = None
        xsm_points = 0
    else:
        mean_mc = subset["meancounts"].mean()
        std_mc  = subset["meancounts"].std()
        min_mc  = subset["meancounts"].min()
        max_mc  = subset["meancounts"].max()
        mean_tc = subset["totalcounts"].mean()
        std_tc  = subset["totalcounts"].std()
        xsm_points = len(subset)

    matched_rows.append({
        "class_filename": row.get("filename"),
        "class_filepath": row.get("filepath"),
        "start_time": row.get("start_time"),
        "end_time": row.get("end_time"),
        "mid_time": row.get("mid_time"),
        "exposure_s": row.get("exposure_s"),
        "temp_c": row.get("temp_c"),
        "gain_ev_ch": row.get("gain_ev_ch"),
        "sat_alt": row.get("sat_alt"),
        "sat_lat": row.get("sat_lat"),
        "sat_lon": row.get("sat_lon"),
        "bore_lat": row.get("bore_lat"),
        "bore_lon": row.get("bore_lon"),
        "solarang_deg": row.get("solarang_deg"),
        "phaseang_deg": row.get("phaseang_deg"),
        "program": row.get("program"),
        "version": row.get("version"),
        "dataset": row.get("dataset"),
        "scd_fltr": row.get("scd_fltr"),
        "scd_used": row.get("scd_used"),
        "v0_lat": row.get("v0_lat"),
        "v0_lon": row.get("v0_lon"),
        "v1_lat": row.get("v1_lat"),
        "v1_lon": row.get("v1_lon"),
        "v2_lat": row.get("v2_lat"),
        "v2_lon": row.get("v2_lon"),
        "v3_lat": row.get("v3_lat"),
        "v3_lon": row.get("v3_lon"),
        # XSM matched statistics
        "XSM_mean_meanCounts": mean_mc,
        "XSM_std_meanCounts": std_mc,
        "XSM_min_meanCounts": min_mc,
        "XSM_max_meanCounts": max_mc,
        "XSM_mean_totalCounts": mean_tc,
        "XSM_std_totalCounts": std_tc,
        "XSM_points_used": xsm_points
    })

# === Create dataframe ===
df_match = pd.DataFrame(matched_rows)
# Save outputs
df_match.columns = [str(c).strip().replace("\n", "_").replace("\r", "_") for c in df_match.columns]

# Convert every column safely to plain Python type
for col in df_match.columns:
    if df_match[col].dtype == "object":
        df_match[col] = df_match[col].astype(str).replace({',': ';'})  # Replace commas with semicolons to avoid header shifts


# === Save ===
df_match.to_csv(output_csv, index=False)
print(f"✅ Saved matched file → {output_csv}")
print(df_match.head(5))
