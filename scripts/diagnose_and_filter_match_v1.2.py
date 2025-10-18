#!/usr/bin/env python3
"""
diagnose_and_filter_match_v1.2.py
Improved version with per-filter diagnostics and adaptive handling for missing columns.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

DEFAULTS = {
    "solarang_max": 115.0,
    "phaseang_max": 115.0,
    "alt_min": 70.0, "alt_max": 120.0,
    "gain_min": 13.0, "gain_max": 14.0,
    "temp_min": -45.0, "temp_max": -25.0,
    "xsm_min_points": 1,
}

def summarize_series(s, name):
    s_valid = s.dropna().astype(float)
    if len(s_valid) == 0:
        print(f"{name}: no valid data")
        return
    p = np.percentile(s_valid, [0,25,50,75,100])
    print(f"{name}: n={len(s_valid)}  min={p[0]:.3g}  p25={p[1]:.3g}  p50={p[2]:.3g}  p75={p[3]:.3g}  max={p[4]:.3g}")

def apply_thresholds(df, thr):
    mask = pd.Series(True, index=df.index)
    diag = {}

    def add_diag(name, cond):
        diag[name] = (~cond).sum()

    if "solarang_deg" in df.columns:
        cond = df["solarang_deg"].astype(float) <= thr["solarang_max"]
        add_diag("solar_angle", cond)
        mask &= cond
    if "phaseang_deg" in df.columns:
        cond = df["phaseang_deg"].astype(float) <= thr["phaseang_max"]
        add_diag("phase_angle", cond)
        mask &= cond
    if "sat_alt" in df.columns:
        cond = df["sat_alt"].between(thr["alt_min"], thr["alt_max"])
        add_diag("altitude", cond)
        mask &= cond
    if "gain_ev_ch" in df.columns and df["gain_ev_ch"].notna().any():
        cond = df["gain_ev_ch"].between(thr["gain_min"], thr["gain_max"])
        add_diag("gain", cond)
        mask &= cond
    else:
        print("⚠️  Gain column missing or empty — skipping filter.")
    if "temp_c" in df.columns and df["temp_c"].notna().any():
        cond = df["temp_c"].between(thr["temp_min"], thr["temp_max"])
        add_diag("temperature", cond)
        mask &= cond
    else:
        print("⚠️  Temperature column missing or empty — skipping filter.")
    if "xsm_points_used" in df.columns:
        cond = df["xsm_points_used"] >= thr["xsm_min_points"]
        add_diag("xsm_points", cond)
        mask &= cond
    if "xsm_mean_totalcounts" in df.columns and "xsm_totalcounts_min" in thr:
        cond = df["xsm_mean_totalcounts"] >= thr["xsm_totalcounts_min"]
        add_diag("xsm_counts", cond)
        mask &= cond

    print("\nRejection summary per filter:")
    for k, v in diag.items():
        print(f"  {k:15s} → {v} rows rejected")

    return mask

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 diagnose_and_filter_match_v1.2.py <match_csv> <output_dir>")
        return
    match_csv = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(match_csv)
    df.columns = [c.strip().lower() for c in df.columns]
    print(f"Loaded {len(df)} rows")

    print("\n--- Basic summaries ---")
    for col, label in {
        "solarang_deg": "Solar angle (deg)",
        "phaseang_deg": "Phase angle (deg)",
        "sat_alt": "Satellite altitude (km)",
        "gain_ev_ch": "Gain (eV/channel)",
        "temp_c": "Temperature (°C)",
        "xsm_points_used": "XSM points used",
        "xsm_mean_meancounts": "XSM mean of meanCounts",
        "xsm_mean_totalcounts": "XSM mean of totalCounts",
    }.items():
        if col in df.columns:
            summarize_series(df[col], label)
        else:
            print(f"{label}: <missing>")

    # adaptive suggestion
    suggested = DEFAULTS.copy()
    if "xsm_mean_totalcounts" in df.columns:
        p30 = np.percentile(df["xsm_mean_totalcounts"].dropna(), 30)
        suggested["xsm_totalcounts_min"] = p30
        print(f"\nSuggested XSM mean totalCounts >= {p30:.1f} (30th percentile)")

    # test both sets
    for name, thr in [("Default", DEFAULTS), ("Suggested", suggested)]:
        mask = apply_thresholds(df, thr)
        print(f"{name} → Accepted: {mask.sum()} / {len(df)} ({mask.mean()*100:.2f}%)")

    use = input("\nApply suggested thresholds? (y/n) [y]: ").strip().lower()
    thr = suggested if use in ("", "y", "yes") else DEFAULTS
    mask = apply_thresholds(df, thr)

    df_filtered, df_rejected = df[mask], df[~mask]
    print(f"\nFiltered: {len(df_filtered)} kept, {len(df_rejected)} rejected")

    df_filtered.to_csv(outdir / (match_csv.stem + "_filtered.csv"), index=False)
    df_rejected.to_csv(outdir / (match_csv.stem + "_rejected.csv"), index=False)

    print(f"✅ Saved filtered and rejected CSVs to {outdir}")

if __name__ == "__main__":
    main()
