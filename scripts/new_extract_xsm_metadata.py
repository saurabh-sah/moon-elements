

#!/usr/bin/env python3
"""
extract_xsm_metadata_fixed_v5.py
Robust extraction of XSM per-second metadata into CSV without misaligned headers.

Paths customized for your setup:
  Input:  /home/saurabh/moon_project/data/XSM/xsm_2025_08/ch2_xsm_20250801_v1/xsm/data/2025/08/01/raw/ch2_xsm_20250801_v1_level1.fits
  Output: /home/saurabh/moon_project/metadata/metadata_XSM/Aug_25/
"""

import csv
from pathlib import Path
import re
from astropy.io import fits
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

# === Your specific paths ===
xsm_file = Path("/home/saurabh/moon_project/data/XSM/xsm_2025_08/ch2_xsm_20250801_v1/xsm/data/2025/08/01/raw/ch2_xsm_20250801_v1_level1.fits")
output_dir = Path("/home/saurabh/moon_project/metadata/metadata_XSM/Aug_25/")
output_dir.mkdir(parents=True, exist_ok=True)

# === Utility: Convert MET → UTC ===
def met_to_utc_str(met_seconds):
    epoch = datetime(2017, 1, 1, tzinfo=timezone.utc)
    dt = epoch + timedelta(seconds=float(met_seconds))
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

# # === Utility: Handle DataArray ===
def safe_stack_dataarray(data_array_column):
    """Converts mixed-type DataArray column into consistent 2D float array."""
    try:
        arr = np.asarray(data_array_column)
        if arr.ndim == 2 and np.issubdtype(arr.dtype, np.number):
            return arr.astype(np.float64)
    except Exception:
        pass
    rows = []
    for row in data_array_column:
        if isinstance(row, (bytes, bytearray, memoryview)):
            r = np.frombuffer(row, dtype=np.uint8).astype(np.float64)
        else:
            r = np.asarray(row, dtype=np.float64)
        rows.append(r)
    lengths = [len(r) for r in rows]
    if len(set(lengths)) != 1:
        raise ValueError(f"Inconsistent DataArray lengths: {sorted(set(lengths))}")
    return np.vstack(rows)

# === Main extraction ===
def extract_xsm_metadata(xsm_path, out_dir):
    with fits.open(xsm_path, memmap=True) as hdul:
        hdr = hdul[1].header
        tbl = hdul[1].data

        # 1️⃣ Header-level metadata
        header_metadata = {
            "DATE_OBS": hdr.get("DATE-OBS"),
            "DATE_END": hdr.get("DATE-END"),
            "TSTART": hdr.get("TSTART"),
            "TSTOP": hdr.get("TSTOP"),
            "TELAPSE": hdr.get("TELAPSE"),
            "MJDREF": hdr.get("MJDREF"),
            "MISSION": hdr.get("MISSION"),
            "TELESCOP": hdr.get("TELESCOP"),
            "INSTRUME": hdr.get("INSTRUME"),
            "ORIGIN": hdr.get("ORIGIN"),
            "CREATOR": hdr.get("CREATOR"),
            "XSMDASVE": hdr.get("XSMDASVE"),
            "FILENAME": hdr.get("FILENAME"),
            "FILE_DATE": hdr.get("DATE"),
            "EXTVER": hdr.get("EXTVER"),
        }

        hdr_str = hdr.tostring(sep="\n")
        l0_files = re.findall(r"l0file\s*=\s*(\S+)", hdr_str)
        header_metadata["HISTORY_L0FILES"] = ";".join(l0_files)

        # 2️⃣ Table data
        met = np.asarray(tbl["Time"])
        utcstring = np.asarray(tbl["UTCString"]).astype(str)
        framenum = np.asarray(tbl["FrameNumber"]).astype(int)
        bdh = np.asarray(tbl["BDHTime"]) if "BDHTime" in tbl.columns.names else np.full_like(met, np.nan)
        xsm_time = np.asarray(tbl["XSMTime"]) if "XSMTime" in tbl.columns.names else np.full_like(met, np.nan)
        decflag = np.asarray(tbl["DecodingStatusFlag"]).astype(int)
        spectra2d = safe_stack_dataarray(tbl["DataArray"])
        nrows, nchan = spectra2d.shape

        # 3️⃣ Per-second stats
        mean_counts = np.mean(spectra2d, axis=1)
        total_counts = np.sum(spectra2d, axis=1)
        std_counts = np.std(spectra2d, axis=1)
        max_counts = np.max(spectra2d, axis=1)
        median_counts = np.median(spectra2d, axis=1)
        frac_255 = np.sum(spectra2d == 255, axis=1) / float(nchan)

        # 4️⃣ Convert MET → UTC
        utc_from_met = [met_to_utc_str(x) for x in met]

        # 5️⃣ Build DataFrame (only 1D arrays)
        df = pd.DataFrame({
            "UTC": utcstring,
            "UTC_from_MET": utc_from_met,
            "MET": met,
            "FrameNumber": framenum,
            "BDHTime": bdh,
            "XSMTime": xsm_time,
            "DecodingFlag": decflag,
            "MeanCounts": mean_counts,
            "TotalCounts": total_counts,
            "StdCounts": std_counts,
            "MaxCounts": max_counts,
            "MedianCounts": median_counts,
            "Frac255": frac_255,
        })

        # # 6️⃣ Add header metadata (broadcast)
        for key, val in header_metadata.items():
            df[key] = val
        df["GoodFrame"] = (df["DecodingFlag"] == 0)
        df["SourceFile"] = xsm_path.name
        df["NChannels"] = nchan

        print(f"✅ File: {xsm_path.name}")
        print(f"Rows: {len(df)}, Channels: {nchan}")
        print("Columns:", list(df.columns)[:12], "...")
        print(df.head(5).to_string(index=False))

        # 7️⃣ Save outputs
        df.columns = [str(c).strip().replace("\n", "_").replace("\r", "_") for c in df.columns]

    # Convert every column safely to plain Python type
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).replace({',': ';'})  # Replace commas with semicolons to avoid header shifts

        # Save robustly
        out_csv = out_dir / f"metadata_XSM_{xsm_path.stem}.csv"
        df.to_csv(out_csv, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8', lineterminator='\n')
        print(f"✅ CSV written cleanly → {out_csv}")
        print(f"✅ Saved detailed CSV → {out_csv}")

        summary = pd.DataFrame([{
            "File": xsm_path.name,
            "Rows": nrows,
            "NChannels": nchan,
            "TELAPSE": header_metadata.get("TELAPSE"),
            "Mean_total_counts_day": float(np.mean(total_counts)),
            "Max_total_counts_day": float(np.max(total_counts)),
        }])
        summary_path = out_dir / f"2metadata_XSM_{xsm_path.stem}_summary.csv"
        summary.to_csv(summary_path, index=False)
        print(f"✅ Saved summary CSV → {summary_path}")

# === Run ===
if __name__ == "__main__":
    extract_xsm_metadata(xsm_file, output_dir)

